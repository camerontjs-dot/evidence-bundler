from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

LABELS = {"KEEP_DISTINCT", "DROP_REDUNDANT", "DROP_DISTRACTOR", "UNRESOLVED"}
ACTION = {
    "KEEP_DISTINCT": "KEEP",
    "DROP_REDUNDANT": "DROP",
    "DROP_DISTRACTOR": "DROP",
    "UNRESOLVED": "UNRESOLVED",
}
REVIEW_SCHEMA = "eb-v1-operational-burden-rc1-review-v2"


class DuplicateKeyError(ValueError):
    pass


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise DuplicateKeyError(f"duplicate JSON object key: {key}")
        out[key] = value
    return out


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_no_duplicates(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_pairs)


def load_no_duplicates_text(text: str) -> Any:
    return json.loads(text, object_pairs_hook=reject_duplicate_pairs)


def canonical_hash(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def packet_relation_ids(packet: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for lane in packet.get("lanes", []):
        for passage in lane.get("passages", []):
            rid = passage.get("relation_id")
            if not isinstance(rid, str):
                raise ValueError("packet relation_id missing")
            ids.append(rid)
    if len(set(ids)) != len(ids):
        raise ValueError("packet duplicate relation_id")
    return ids


def output_schema(packet: dict[str, Any], phase: str, reviewer_id: str) -> dict[str, Any]:
    if phase not in {"reference", "test"}:
        raise ValueError("invalid review phase")
    ids = packet_relation_ids(packet)
    packet_hash = canonical_hash(packet)
    label_properties = {
        rid: {"type": "string", "enum": sorted(LABELS)} for rid in ids
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["schema", "reviewer", "labels"],
        "properties": {
            "schema": {"type": "string", "enum": [REVIEW_SCHEMA]},
            "reviewer": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "reviewer_id",
                    "review_phase",
                    "model_or_human",
                    "execution_context",
                    "packet_canonical_sha256",
                    "independent_of_other_reviewers",
                    "saw_other_set",
                    "saw_prior_reference",
                ],
                "properties": {
                    "reviewer_id": {"type": "string", "enum": [reviewer_id]},
                    "review_phase": {"type": "string", "enum": [phase]},
                    "model_or_human": {"type": "string", "minLength": 1},
                    "execution_context": {"type": "string", "minLength": 1},
                    "packet_canonical_sha256": {"type": "string", "enum": [packet_hash]},
                    "independent_of_other_reviewers": {"type": "boolean", "enum": [True]},
                    "saw_other_set": {"type": "boolean", "enum": [False]},
                    "saw_prior_reference": {"type": "boolean", "enum": [False]},
                },
            },
            "labels": {
                "type": "object",
                "additionalProperties": False,
                "required": ids,
                "properties": label_properties,
            },
        },
    }


def _validate_review_obj(
    review: Any,
    packet: dict[str, Any],
    expected_phase: str,
    expected_reviewer_id: str | None = None,
    used_reviewer_ids: set[str] | None = None,
) -> tuple[dict[str, str], str]:
    expected_hash = canonical_hash(packet)
    allowed_ids = set(packet_relation_ids(packet))
    if not isinstance(review, dict):
        raise ValueError("review must be an object")
    if set(review) != {"schema", "reviewer", "labels"}:
        raise ValueError("review top-level fields mismatch")
    if review.get("schema") != REVIEW_SCHEMA:
        raise ValueError("review schema mismatch")
    meta = review.get("reviewer")
    if not isinstance(meta, dict):
        raise ValueError("reviewer metadata missing")
    expected_meta = {
        "reviewer_id", "review_phase", "model_or_human", "execution_context",
        "packet_canonical_sha256", "independent_of_other_reviewers",
        "saw_other_set", "saw_prior_reference",
    }
    if set(meta) != expected_meta:
        raise ValueError("reviewer metadata fields mismatch")
    reviewer_id = meta.get("reviewer_id")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise ValueError("reviewer_id missing")
    if expected_reviewer_id is not None and reviewer_id != expected_reviewer_id:
        raise ValueError("reviewer_id mismatch")
    if used_reviewer_ids is not None:
        if reviewer_id in used_reviewer_ids:
            raise ValueError(f"duplicate reviewer_id {reviewer_id}")
        used_reviewer_ids.add(reviewer_id)
    if meta.get("review_phase") != expected_phase:
        raise ValueError("review_phase mismatch")
    if not isinstance(meta.get("model_or_human"), str) or not meta["model_or_human"].strip():
        raise ValueError("model_or_human missing")
    if not isinstance(meta.get("execution_context"), str) or not meta["execution_context"].strip():
        raise ValueError("execution_context missing")
    if meta.get("packet_canonical_sha256") != expected_hash:
        raise ValueError("packet hash mismatch")
    if meta.get("independent_of_other_reviewers") is not True:
        raise ValueError("independence assertion missing")
    if meta.get("saw_other_set") is not False:
        raise ValueError("other-set exposure")
    if meta.get("saw_prior_reference") is not False:
        raise ValueError("prior-reference exposure")
    labels = review.get("labels")
    if not isinstance(labels, dict):
        raise ValueError("labels missing")
    if set(labels) != allowed_ids:
        raise ValueError("relation set mismatch")
    for rid, label in labels.items():
        if label not in LABELS:
            raise ValueError(f"invalid label {label} for {rid}")
    return dict(labels), reviewer_id


def validate_review_text(
    text: str,
    packet: dict[str, Any],
    expected_phase: str,
    expected_reviewer_id: str | None = None,
    used_reviewer_ids: set[str] | None = None,
) -> tuple[dict[str, str], str]:
    return _validate_review_obj(
        load_no_duplicates_text(text), packet, expected_phase, expected_reviewer_id, used_reviewer_ids
    )


def validate_review(
    review_path: Path,
    packet_path: Path,
    expected_phase: str,
    used_reviewer_ids: set[str] | None = None,
    expected_reviewer_id: str | None = None,
) -> tuple[dict[str, str], str]:
    packet = load(packet_path)
    return _validate_review_obj(
        load_no_duplicates(review_path), packet, expected_phase, expected_reviewer_id, used_reviewer_ids
    )


def is_result_shaped_message(text: str) -> bool:
    try:
        obj = load_no_duplicates_text(text)
    except (json.JSONDecodeError, DuplicateKeyError):
        return False
    return isinstance(obj, dict) and (
        obj.get("schema") == REVIEW_SCHEMA or bool({"reviewer", "labels"} & set(obj))
    )
