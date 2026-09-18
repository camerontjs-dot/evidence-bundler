from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SUPPORTED_SPECIALTY_FORMS = frozenset(
    {"authoritative_declaration", "event_record", "registry_entry"}
)
SEMANTIC_LOSS_CAP = 0.01
BUDGET = 3

EVENT_RE = re.compile(
    r"\b(?:log|record|audit|witness|incident|event)\b",
    re.IGNORECASE,
)
REGISTRY_RE = re.compile(
    r"\b(?:registry|inventory|certificate|certified|code|registrar|database)\b",
    re.IGNORECASE,
)
DECLARATION_RE = re.compile(
    r"\b(?:report states|states that|declaration|policy|code|manual|specification)\b",
    re.IGNORECASE,
)


class SelectorInputError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def candidate_specialty_forms(text: str) -> frozenset[str]:
    forms: set[str] = set()
    if EVENT_RE.search(text):
        forms.add("event_record")
    if REGISTRY_RE.search(text):
        forms.add("registry_entry")
    if DECLARATION_RE.search(text):
        forms.add("authoritative_declaration")
    return frozenset(forms)


def expected_specialty_forms(expected_evidence_forms: list[str]) -> frozenset[str]:
    return frozenset(
        str(value).strip().lower()
        for value in expected_evidence_forms
        if str(value).strip().lower() in SUPPORTED_SPECIALTY_FORMS
    )


def _validate_candidate(candidate: dict[str, Any]) -> None:
    required = {"candidate_id", "rank", "text", "semantic_score"}
    if set(candidate) != required:
        raise SelectorInputError(
            f"candidate fields must be exactly {sorted(required)}, got "
            f"{sorted(candidate)}"
        )
    if not isinstance(candidate["candidate_id"], str) or not candidate["candidate_id"]:
        raise SelectorInputError("candidate_id must be a nonempty string")
    if not isinstance(candidate["rank"], int) or candidate["rank"] < 1:
        raise SelectorInputError("rank must be a positive integer")
    if not isinstance(candidate["text"], str):
        raise SelectorInputError("text must be a string")
    if not isinstance(candidate["semantic_score"], (int, float)):
        raise SelectorInputError("semantic_score must be numeric")


def _semantic_order(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda row: (
            -float(row["semantic_score"]),
            int(row["rank"]),
            str(row["candidate_id"]),
        ),
    )


def _match(
    candidate: dict[str, Any],
    specialties: frozenset[str],
) -> int:
    if not specialties:
        return 0
    observed = candidate_specialty_forms(str(candidate["text"]))
    return int(bool(observed & specialties))


def select(payload: dict[str, Any]) -> dict[str, Any]:
    required = {"claim_id", "expected_evidence_forms", "candidates"}
    if set(payload) != required:
        raise SelectorInputError(
            f"input fields must be exactly {sorted(required)}, got {sorted(payload)}"
        )

    claim_id = payload["claim_id"]
    expected = payload["expected_evidence_forms"]
    candidates = payload["candidates"]

    if not isinstance(claim_id, str) or not claim_id:
        raise SelectorInputError("claim_id must be a nonempty string")
    if not isinstance(expected, list) or not all(isinstance(x, str) for x in expected):
        raise SelectorInputError("expected_evidence_forms must be a list of strings")
    if not isinstance(candidates, list) or len(candidates) < BUDGET:
        raise SelectorInputError(f"candidates must contain at least {BUDGET} rows")

    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise SelectorInputError("each candidate must be an object")
        _validate_candidate(candidate)

    ids = [str(candidate["candidate_id"]) for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise SelectorInputError("candidate_id values must be unique")

    ordered = _semantic_order(candidates)
    selected = list(ordered[:BUDGET])
    outside = list(ordered[BUDGET:])
    specialties = expected_specialty_forms(expected)

    action = "NO_SPECIALTY_NOOP"
    victim_id: str | None = None
    challenger_id: str | None = None
    semantic_loss: float | None = None

    if specialties and outside:
        victim = min(
            selected,
            key=lambda row: (
                _match(row, specialties),
                float(row["semantic_score"]),
                -int(row["rank"]),
                str(row["candidate_id"]),
            ),
        )
        challenger = max(
            outside,
            key=lambda row: (
                _match(row, specialties),
                float(row["semantic_score"]),
                -int(row["rank"]),
                str(row["candidate_id"]),
            ),
        )
        victim_match = _match(victim, specialties)
        challenger_match = _match(challenger, specialties)
        semantic_loss = float(victim["semantic_score"]) - float(
            challenger["semantic_score"]
        )

        if challenger_match > victim_match and semantic_loss <= SEMANTIC_LOSS_CAP + 1e-12:
            selected = [row for row in selected if row is not victim] + [challenger]
            selected = _semantic_order(selected)
            action = "SPECIALTY_REPAIR"
            victim_id = str(victim["candidate_id"])
            challenger_id = str(challenger["candidate_id"])
        else:
            action = "SPECIALTY_NO_CHANGE"

    output = {
        "schema": "eb-gate-specialty-selector-rc0-output",
        "claim_id": claim_id,
        "budget": BUDGET,
        "semantic_loss_cap": SEMANTIC_LOSS_CAP,
        "expected_specialty_forms": sorted(specialties),
        "action": action,
        "victim_candidate_id": victim_id,
        "challenger_candidate_id": challenger_id,
        "semantic_loss": semantic_loss,
        "selected_candidate_ids": [
            str(candidate["candidate_id"]) for candidate in selected
        ],
    }
    output["output_sha256"] = _sha256_json(output)
    return output
