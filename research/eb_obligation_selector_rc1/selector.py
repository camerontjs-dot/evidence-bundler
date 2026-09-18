from __future__ import annotations

import hashlib
import json
import re
from typing import Any

BUDGET = 3
SEMANTIC_LOSS_CAP = 0.01

SUPPORTED_FORMS = frozenset(
    {
        "authoritative_declaration",
        "event_record",
        "registry_entry",
        "measurement",
    }
)

EVENT_RE = re.compile(
    r"\b(?:event log|log entry|audit trail|witness record|inspection record|"
    r"run record|batch record|incident record|event record|recorded|logged|"
    r"observed|witnessed)\b",
    re.IGNORECASE,
)
REGISTRY_RE = re.compile(
    r"\b(?:registry|register|registered|database|inventory|certificate|"
    r"certified|listing|listed)\b",
    re.IGNORECASE,
)
DECLARATION_RE = re.compile(
    r"\b(?:policy|manual|procedure|specification|declaration|states that|"
    r"requires|requirement|shall|must)\b",
    re.IGNORECASE,
)
MEASUREMENT_RE = re.compile(
    r"\b(?:measurement|measured|reading|gauge|sensor reading|test value|"
    r"temperature|pressure|concentration|duration)\b",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
UNIT_RE = re.compile(
    r"\b(?:bar|psi|kpa|mpa|degrees?\s*c|°c|percent|%|minutes?|hours?|"
    r"seconds?)\b",
    re.IGNORECASE,
)


class SelectorInputError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def candidate_forms(text: str) -> frozenset[str]:
    forms: set[str] = set()
    if EVENT_RE.search(text):
        forms.add("event_record")
    if REGISTRY_RE.search(text):
        forms.add("registry_entry")
    if DECLARATION_RE.search(text):
        forms.add("authoritative_declaration")
    if MEASUREMENT_RE.search(text) or (
        NUMBER_RE.search(text) and UNIT_RE.search(text)
    ):
        forms.add("measurement")
    return frozenset(forms)


def _normalize_subject(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SelectorInputError("subject must be a string or null")
    value = " ".join(value.split())
    return value or None


def _validate(payload: dict[str, Any]) -> None:
    required = {"parent_id", "children", "candidates"}
    if set(payload) != required:
        raise SelectorInputError(
            f"input fields must be exactly {sorted(required)}"
        )
    if not isinstance(payload["parent_id"], str) or not payload["parent_id"]:
        raise SelectorInputError("parent_id must be a nonempty string")
    children = payload["children"]
    candidates = payload["candidates"]
    if not isinstance(children, list) or len(children) < 2:
        raise SelectorInputError("children must contain at least two rows")
    if not isinstance(candidates, list) or len(candidates) < BUDGET:
        raise SelectorInputError(
            f"candidates must contain at least {BUDGET} rows"
        )

    child_ids: list[str] = []
    for row in children:
        if not isinstance(row, dict):
            raise SelectorInputError("each child must be an object")
        if set(row) != {
            "child_id",
            "subject",
            "expected_evidence_forms",
        }:
            raise SelectorInputError("unexpected child fields")
        child_id = row["child_id"]
        if not isinstance(child_id, str) or not child_id:
            raise SelectorInputError("child_id must be a nonempty string")
        child_ids.append(child_id)
        _normalize_subject(row["subject"])
        forms = row["expected_evidence_forms"]
        if not isinstance(forms, list) or not all(
            isinstance(value, str) for value in forms
        ):
            raise SelectorInputError(
                "expected_evidence_forms must be a list of strings"
            )
    if len(child_ids) != len(set(child_ids)):
        raise SelectorInputError("child_id values must be unique")

    candidate_ids: list[str] = []
    for row in candidates:
        if not isinstance(row, dict):
            raise SelectorInputError("each candidate must be an object")
        if set(row) != {
            "candidate_id",
            "text",
            "semantic_scores",
        }:
            raise SelectorInputError("unexpected candidate fields")
        candidate_id = row["candidate_id"]
        if not isinstance(candidate_id, str) or not candidate_id:
            raise SelectorInputError(
                "candidate_id must be a nonempty string"
            )
        candidate_ids.append(candidate_id)
        if not isinstance(row["text"], str):
            raise SelectorInputError("candidate text must be a string")
        scores = row["semantic_scores"]
        if not isinstance(scores, dict) or set(scores) != set(child_ids):
            raise SelectorInputError(
                "semantic_scores keys must exactly match child IDs"
            )
        if not all(
            isinstance(value, (int, float))
            for value in scores.values()
        ):
            raise SelectorInputError("semantic scores must be numeric")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise SelectorInputError("candidate_id values must be unique")


def _decorate(
    payload: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    children = {
        str(row["child_id"]): {
            "child_id": str(row["child_id"]),
            "subject": _normalize_subject(row["subject"]),
            "expected_forms": frozenset(
                str(value).strip().lower()
                for value in row["expected_evidence_forms"]
                if str(value).strip().lower() in SUPPORTED_FORMS
            ),
        }
        for row in payload["children"]
    }

    rows: list[dict[str, Any]] = []
    for candidate in payload["candidates"]:
        scores = {
            str(key): float(value)
            for key, value in candidate["semantic_scores"].items()
        }
        best_child = max(
            scores,
            key=lambda child_id: (
                scores[child_id],
                child_id,
            ),
        )
        rows.append(
            {
                "candidate_id": str(candidate["candidate_id"]),
                "text": str(candidate["text"]),
                "semantic_scores": scores,
                "best_child": best_child,
                "best_score": scores[best_child],
                "candidate_forms": candidate_forms(
                    str(candidate["text"])
                ),
            }
        )
    return rows, children


def _semantic_order(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            -float(row["best_score"]),
            str(row["candidate_id"]),
        ),
    )


def _coverage_repair(
    rows: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    child_ids: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    current = list(selected)
    receipts: list[dict[str, Any]] = []

    for missing_child in child_ids:
        counts = {
            child_id: sum(
                row["best_child"] == child_id for row in current
            )
            for child_id in child_ids
        }
        if counts[missing_child] > 0:
            continue

        outside = [
            row
            for row in rows
            if row not in current
            and row["best_child"] == missing_child
        ]
        victims = [
            row
            for row in current
            if counts[row["best_child"]] > 1
        ]
        if not outside or not victims:
            receipts.append(
                {
                    "child_id": missing_child,
                    "action": "NO_ELIGIBLE_SWAP",
                }
            )
            continue

        challenger = max(
            outside,
            key=lambda row: (
                float(row["best_score"]),
                str(row["candidate_id"]),
            ),
        )
        victim = min(
            victims,
            key=lambda row: (
                float(row["best_score"]),
                str(row["candidate_id"]),
            ),
        )
        loss = (
            float(victim["best_score"])
            - float(challenger["best_score"])
        )

        if loss <= SEMANTIC_LOSS_CAP + 1e-12:
            current = [
                row for row in current if row is not victim
            ] + [challenger]
            current = _semantic_order(current)
            receipts.append(
                {
                    "child_id": missing_child,
                    "action": "SWAP",
                    "victim": victim["candidate_id"],
                    "challenger": challenger["candidate_id"],
                    "semantic_loss": loss,
                }
            )
        else:
            receipts.append(
                {
                    "child_id": missing_child,
                    "action": "LOSS_CAP_BLOCK",
                    "semantic_loss": loss,
                }
            )

    return _semantic_order(current), receipts


def _form_match(
    row: dict[str, Any],
    child: dict[str, Any],
) -> int:
    expected = child["expected_forms"]
    if not expected:
        return 0
    return int(bool(row["candidate_forms"] & expected))


def _subject_match(
    row: dict[str, Any],
    child: dict[str, Any],
) -> int:
    subject = child["subject"]
    if not subject:
        return 0
    return int(subject.lower() in str(row["text"]).lower())


def _repair_stage(
    *,
    rows: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    children: dict[str, dict[str, Any]],
    stage: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    current = list(selected)
    receipts: list[dict[str, Any]] = []

    if stage == "form":
        scorer = _form_match
    elif stage == "subject":
        scorer = _subject_match
    else:
        raise ValueError(stage)

    for child_id in children:
        child = children[child_id]
        owned = [
            row for row in current
            if row["best_child"] == child_id
        ]
        outside = [
            row
            for row in rows
            if row not in current
            and row["best_child"] == child_id
        ]
        if not owned or not outside:
            receipts.append(
                {
                    "child_id": child_id,
                    "action": "NO_ELIGIBLE_SWAP",
                }
            )
            continue

        victim = min(
            owned,
            key=lambda row: (
                scorer(row, child),
                float(row["best_score"]),
                str(row["candidate_id"]),
            ),
        )
        challenger = max(
            outside,
            key=lambda row: (
                scorer(row, child),
                float(row["best_score"]),
                str(row["candidate_id"]),
            ),
        )
        victim_score = scorer(victim, child)
        challenger_score = scorer(challenger, child)

        if challenger_score <= victim_score:
            receipts.append(
                {
                    "child_id": child_id,
                    "action": "NO_MATCH_IMPROVEMENT",
                }
            )
            continue

        loss = (
            float(victim["best_score"])
            - float(challenger["best_score"])
        )
        if loss > SEMANTIC_LOSS_CAP + 1e-12:
            receipts.append(
                {
                    "child_id": child_id,
                    "action": "LOSS_CAP_BLOCK",
                    "semantic_loss": loss,
                }
            )
            continue

        trial = [
            row for row in current if row is not victim
        ] + [challenger]
        represented = {
            row["best_child"] for row in trial
        }
        if not set(children) <= represented:
            receipts.append(
                {
                    "child_id": child_id,
                    "action": "COMPOSITION_BLOCK",
                }
            )
            continue

        current = _semantic_order(trial)
        receipts.append(
            {
                "child_id": child_id,
                "action": "SWAP",
                "victim": victim["candidate_id"],
                "challenger": challenger["candidate_id"],
                "semantic_loss": loss,
                "victim_match": victim_score,
                "challenger_match": challenger_score,
            }
        )

    return _semantic_order(current), receipts


def select(payload: dict[str, Any]) -> dict[str, Any]:
    _validate(payload)
    rows, children = _decorate(payload)
    ordered = _semantic_order(rows)
    selected = ordered[:BUDGET]
    child_ids = list(children)

    semantic_ids = [
        row["candidate_id"] for row in selected
    ]

    selected, coverage_receipt = _coverage_repair(
        ordered,
        selected,
        child_ids,
    )
    coverage_ids = [
        row["candidate_id"] for row in selected
    ]

    selected, form_receipt = _repair_stage(
        rows=ordered,
        selected=selected,
        children=children,
        stage="form",
    )
    form_ids = [
        row["candidate_id"] for row in selected
    ]

    selected, subject_receipt = _repair_stage(
        rows=ordered,
        selected=selected,
        children=children,
        stage="subject",
    )
    final_ids = [
        row["candidate_id"] for row in selected
    ]

    output = {
        "schema": "eb-obligation-selector-rc1-output",
        "parent_id": payload["parent_id"],
        "budget": BUDGET,
        "semantic_loss_cap": SEMANTIC_LOSS_CAP,
        "stage_order": [
            "semantic_topk",
            "child_coverage",
            "expected_evidence_form",
            "subject_identity",
        ],
        "semantic_topk_ids": semantic_ids,
        "after_child_coverage_ids": coverage_ids,
        "after_expected_form_ids": form_ids,
        "selected_candidate_ids": final_ids,
        "coverage_receipt": coverage_receipt,
        "form_receipt": form_receipt,
        "subject_receipt": subject_receipt,
    }
    output["output_sha256"] = _sha256_json(output)
    return output
