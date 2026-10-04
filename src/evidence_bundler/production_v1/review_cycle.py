"""Bound review record and readable context for the installed V1 command.

The admission wire stays a proposition/passage decision list. Reasons, input
bindings, and display context live beside that wire. Display context is
reconstructed from source offsets for reading. It is not admitted text and it
does not change passage spans or identifiers.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

REVIEW_RECORD_SCHEMA = "evidence-bundler-v1-review-record-v1"
BINDING_KEYS = (
    "config_sha256",
    "input_sha256",
    "package_version",
    "profile_id",
    "unreviewed_native_package_sha256",
)
DECISION_KEYS = ("decision", "passage_id", "proposition_id", "reason")
DECISIONS = frozenset({"accepted", "rejected", "needs-review"})
DISPLAY_LIMIT = 1200

GAP_NOT_RUN = "Retrieval for this target did not run."
GAP_NO_SOURCES = "This target had no sources to search."
GAP_NO_NOMINATIONS = "Retrieval searched the sources and nominated nothing."
GAP_NOT_RETAINED = "Retrieval nominated candidates and retained none."
GAP_NONE_ACCEPTED = "Retained passages were reviewed and none were accepted."

STALE_PREFIX = "refusing stale review"
COVERAGE_MESSAGE = (
    "refusing review because the decisions do not cover the retained pairs of this "
    "unreviewed package. Generate a new review record from the current run. "
    "Nothing was written."
)
REASON_MESSAGE = (
    "refusing review because a retained decision has an empty reason. Fill every "
    "reason, or generate a new review record. Nothing was written."
)
MIXED_MESSAGE = (
    "refusing mixed review inputs: pass either --admission or --review. Nothing was written."
)

_HEADING_LINE = re.compile(r"^#{1,6}[ \t]+\S[^\n]*", re.MULTILINE)
_RECORD_KEYS = frozenset({"bindings", "decisions", "schema"})


class ReviewCycleError(ValueError):
    """Raised when a V1 review record cannot be applied. No output is written."""


def file_sha256(path: Path) -> str:
    """Hash the raw file bytes, not a parsed or reformatted document."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def dump_record(value: dict[str, Any]) -> str:
    """Serialize a review record canonically."""
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def retained_rows(package: dict[str, Any]) -> list[dict[str, Any]]:
    """Return normative candidates the fixed profile retained."""
    return [row for row in package["candidates"] if row["selection_state"] == "retained"]


def retained_pairs(package: dict[str, Any]) -> set[tuple[str, str]]:
    """Return the proposition/passage pairs a review must cover exactly."""
    return {
        (str(row["proposition_id"]), str(row["passage_id"])) for row in retained_rows(package)
    }


def template_record(
    bindings: dict[str, str], retained: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build an unapplied review record. Blank reasons cannot be applied."""
    ordered = sorted(
        retained,
        key=lambda row: (
            str(row["proposition_id"]),
            int(row["nomination_rank"]),
            str(row["passage_id"]),
        ),
    )
    decisions = [
        {
            "decision": "needs-review",
            "passage_id": row["passage_id"],
            "proposition_id": row["proposition_id"],
            "reason": "",
        }
        for row in ordered
    ]
    return {
        "bindings": {key: bindings[key] for key in BINDING_KEYS},
        "decisions": decisions,
        "schema": REVIEW_RECORD_SCHEMA,
    }


def load_review_record(path: Path) -> dict[str, Any]:
    """Load one review record or reject it before any package output exists."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewCycleError(f"invalid review record: {exc}") from exc
    if not isinstance(value, dict) or set(value) != _RECORD_KEYS:
        raise ReviewCycleError(
            "invalid review record: keys must be schema, bindings, and decisions"
        )
    if value["schema"] != REVIEW_RECORD_SCHEMA:
        raise ReviewCycleError(
            f"invalid review record: schema must equal {REVIEW_RECORD_SCHEMA!r}"
        )
    bindings = value["bindings"]
    if not isinstance(bindings, dict) or set(bindings) != set(BINDING_KEYS):
        raise ReviewCycleError(
            "invalid review record: bindings must be exactly "
            + ", ".join(BINDING_KEYS)
        )
    if any(not isinstance(bindings[key], str) or not bindings[key].strip() for key in BINDING_KEYS):
        raise ReviewCycleError("invalid review record: bindings must be nonblank strings")
    decisions = value["decisions"]
    if not isinstance(decisions, list):
        raise ReviewCycleError("invalid review record: decisions must be a list")
    for index, raw in enumerate(decisions):
        label = f"decisions[{index}]"
        if not isinstance(raw, dict) or set(raw) != set(DECISION_KEYS):
            raise ReviewCycleError(f"invalid review record: {label} keys are wrong")
        if raw["decision"] not in DECISIONS:
            raise ReviewCycleError(f"invalid review record: {label}.decision is invalid")
        for field in ("proposition_id", "passage_id"):
            if not isinstance(raw[field], str) or not raw[field].strip():
                raise ReviewCycleError(f"invalid review record: {label}.{field} must be nonblank")
        if not isinstance(raw["reason"], str):
            raise ReviewCycleError(f"invalid review record: {label}.reason must be a string")
    return value


def binding_mismatches(record: dict[str, Any], expected: dict[str, str]) -> list[str]:
    """Return binding names that do not identify this input and unreviewed package."""
    bindings = record["bindings"]
    return [key for key in BINDING_KEYS if bindings.get(key) != expected[key]]


def stale_message(mismatches: list[str]) -> str:
    """Tell the operator to review the current run instead of reusing the old record."""
    rendered = ", ".join(mismatches)
    return (
        f"{STALE_PREFIX} because these bindings do not match this input file and "
        f"unreviewed package: {rendered}. Generate a new review record from the current "
        "run and review that record. Nothing was written."
    )


def covered_decisions(
    record: dict[str, Any], pairs: set[tuple[str, str]]
) -> dict[tuple[str, str], tuple[str, str]]:
    """Require the record to name each retained pair once and no other pair."""
    found: dict[tuple[str, str], tuple[str, str]] = {}
    for row in record["decisions"]:
        key = (str(row["proposition_id"]), str(row["passage_id"]))
        if key in found:
            raise ReviewCycleError(
                f"invalid review record: duplicate decision for {key[0]}/{key[1]}"
            )
        found[key] = (str(row["decision"]), str(row["reason"]))
    if set(found) != pairs:
        raise ReviewCycleError(COVERAGE_MESSAGE)
    return found


def require_reasons(covered: dict[tuple[str, str], tuple[str, str]]) -> None:
    """Refuse a template or any other record that has not been filled in."""
    for reason in (item[1] for item in covered.values()):
        if not reason.strip():
            raise ReviewCycleError(REASON_MESSAGE)


def admission_from_review(
    covered: dict[tuple[str, str], tuple[str, str]],
) -> dict[tuple[str, str], str]:
    """Drop reasons before they can reach the admission wire."""
    return {key: decision for key, (decision, _reason) in covered.items()}


def gap_sentence(package: dict[str, Any], proposition_id: str) -> str | None:
    """Explain an empty or unaccepted target without inventing a support verdict."""
    plans = [
        row
        for row in package["retrieval_plans"]
        if str(row["proposition_id"]) == proposition_id
    ]
    executions = {str(row["retrieval_id"]): row for row in package["retrieval_executions"]}
    execution = executions.get(str(plans[0]["retrieval_id"])) if plans else None
    retained = [
        row
        for row in package["candidates"]
        if str(row["proposition_id"]) == proposition_id and row["selection_state"] == "retained"
    ]
    if not retained:
        if execution is None or execution.get("status") == "not_run":
            return GAP_NOT_RUN
        searched = execution.get("searched_source_ids") or []
        sources = package["contract_a"]["sources"]
        if len(sources) == 0 or len(searched) == 0:
            return GAP_NO_SOURCES
        if int(execution.get("returned_count") or 0) == 0:
            return GAP_NO_NOMINATIONS
        return GAP_NOT_RETAINED
    if any(row.get("admission_state") == "accepted" for row in retained):
        return None
    if all(row.get("admission_state") == "needs-review" for row in retained):
        return None
    return GAP_NONE_ACCEPTED


def _preceding_heading(source: str, start: int) -> tuple[int, str] | None:
    found: tuple[int, str] | None = None
    for match in _HEADING_LINE.finditer(source[:start]):
        found = (match.start(), match.group(0))
    return found


def _preceding_table_lines(source: str, start: int, limit: int = 4) -> list[str]:
    lines: list[str] = []
    cursor = start
    while len(lines) < limit and cursor > 0:
        previous = source.rfind("\n", 0, cursor)
        line_start = 0 if previous < 0 else previous + 1
        line = source[line_start:cursor].strip("\r\n")
        if not line or not line.lstrip().startswith("|"):
            break
        lines.append(line)
        if previous < 0:
            break
        cursor = previous
    lines.reverse()
    return lines


def _truncate_bridge(text: str, heading_line: str | None) -> str:
    if len(text) <= DISPLAY_LIMIT:
        return text
    if heading_line and text.startswith(heading_line):
        marker = "\n...\n"
        budget = DISPLAY_LIMIT - len(heading_line) - len(marker)
        if budget <= 0:
            return heading_line[:DISPLAY_LIMIT]
        return heading_line + marker + text[len(heading_line) :][-budget:]
    return text[-DISPLAY_LIMIT:]


def display_bridge(source: str, start: int, end: int) -> tuple[str | None, int | None]:
    """Return readable heading or table context that the passage itself does not contain."""
    if not (0 <= start < end <= len(source)):
        return None, None
    passage = source[start:end]
    heading = _preceding_heading(source, start)
    heading_at = heading[0] if heading else None
    heading_line = heading[1] if heading else None
    parts: list[str] = []
    if heading_at is not None and heading_line is not None and heading_line not in passage:
        raw = source[heading_at:start].strip("\n")
        if raw and raw not in passage:
            parts.append(raw)
    if any(line.lstrip().startswith("|") for line in passage.splitlines()):
        existing = "\n".join(parts)
        extra = [
            line
            for line in _preceding_table_lines(source, start)
            if line not in existing and line not in passage
        ]
        if extra:
            parts.append("\n".join(extra))
    if not parts:
        return None, heading_at
    text = _truncate_bridge(parts[0] if len(parts) == 1 else "\n".join(parts), heading_line)
    if not text or text in passage:
        return None, heading_at
    return text, heading_at


def _heading_owners(
    candidates: list[dict[str, Any]],
    *,
    source_id: str,
    heading_at: int,
    passage_id: str,
) -> list[dict[str, Any]]:
    owners = []
    for row in candidates:
        if row.get("selection_state") != "retained":
            continue
        if str(row.get("source_id")) != source_id or str(row.get("passage_id")) == passage_id:
            continue
        if int(row["char_start"]) <= heading_at < int(row["char_end"]):
            owners.append(row)
    owners.sort(key=lambda row: (str(row["proposition_id"]), str(row["passage_id"])))
    return owners


def render_review_context(package: dict[str, Any], *, binding_note: str | None = None) -> str:
    """Render one Markdown context file for the package that was actually emitted."""
    lines = [
        "# Review context",
        "",
        "Display context is reconstructed for reading. It is not admitted text, and it "
        "does not change passage spans or identifiers.",
        "",
    ]
    if binding_note:
        lines.extend([binding_note, ""])
    sources = {str(row["source_id"]): row for row in package["contract_a"]["sources"]}
    for target in package["primary_targets"]:
        proposition_id = str(target["proposition_id"])
        lines.extend([f"## Target `{proposition_id}`", "", "Claim:", "", str(target["text"]), ""])
        gap = gap_sentence(package, proposition_id)
        if gap:
            lines.extend([f"Gap: {gap}", ""])
        retained = sorted(
            (
                row
                for row in package["candidates"]
                if str(row["proposition_id"]) == proposition_id
                and row["selection_state"] == "retained"
            ),
            key=lambda row: (int(row["nomination_rank"]), str(row["passage_id"])),
        )
        for row in retained:
            passage_id = str(row["passage_id"])
            lines.extend(
                [
                    f"### Passage `{passage_id}`",
                    "",
                    f"- Source: `{row['source_id']}`",
                    f"- Offsets: {row['char_start']}:{row['char_end']}",
                    f"- Admission: `{row['admission_state']}`",
                    "",
                    "Passage text:",
                    "",
                    "```",
                    str(row["text"]).rstrip("\n"),
                    "```",
                    "",
                ]
            )
            source = sources.get(str(row["source_id"]))
            if source is None:
                continue
            content = str(source["content"])
            bridge, heading_at = display_bridge(
                content, int(row["char_start"]), int(row["char_end"])
            )
            if bridge:
                lines.extend(
                    [
                        "Display context (not admitted text):",
                        "",
                        "```",
                        bridge,
                        "```",
                        "",
                    ]
                )
            if heading_at is None:
                continue
            for owner in _heading_owners(
                package["candidates"],
                source_id=str(row["source_id"]),
                heading_at=heading_at,
                passage_id=passage_id,
            ):
                lines.extend(
                    [
                        "The heading also falls inside retained passage "
                        f"`{owner['passage_id']}` for target `{owner['proposition_id']}`.",
                        "",
                    ]
                )
    return "\n".join(lines).rstrip() + "\n"
