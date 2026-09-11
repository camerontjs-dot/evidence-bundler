"""Contract A 2.0 intake for the Evidence Bundler V1 candidate.

The released Contract A validator remains the authority.  This module is a
small maintained consumer implementation that mirrors the released wire rules
and is cross-checked against the canonical validator in V1 qualification.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal, TypedDict

CONTRACT_A_VERSION = "2.0.0"
WIRE_SCHEMA_TOKEN = "contract-a-wire-candidate-rc2"
CONTRACT_A_RELEASE_COMMIT = "529c92b49a34d5c610618551a8737f019f9fa332"
CONTRACT_A_VALIDATOR_BLOB = "42e5f5b3bf38d677445e9d01ea130ba604e53409"
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
MEDIA_TYPES = {"text/plain; charset=utf-8", "text/markdown; charset=utf-8"}
DECOMPOSITION_STATES = {"not_decomposed", "failed", "unknown", "declared"}


class ContractAValidationError(ValueError):
    """Raised when Contract A bytes do not satisfy the released wire rules."""


class PrimaryTarget(TypedDict):
    """One exact upstream-declared proposition that receives a normative lane."""

    proposition_id: str
    text: str
    text_sha256: str
    role: Literal["root", "declared_child"]
    sequence: int | None


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_payload_bytes(value: dict[str, Any]) -> bytes:
    payload = dict(value)
    payload.pop("handoff_sha256", None)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def compute_handoff_sha256(value: dict[str, Any]) -> str:
    """Compute the released Contract A whole-object binding."""
    return "sha256:" + hashlib.sha256(_canonical_payload_bytes(value)).hexdigest()


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractAValidationError(f"{path} must be an object")
    return value


def _array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractAValidationError(f"{path} must be an array")
    return value


def _exact_keys(value: dict[str, Any], allowed: set[str], required: set[str], path: str) -> None:
    extras = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if extras:
        raise ContractAValidationError(
            f"{path} has forbidden/unknown fields: {', '.join(extras)}"
        )
    if missing:
        raise ContractAValidationError(f"{path} is missing required fields: {', '.join(missing)}")


def _nonblank(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractAValidationError(f"{path} must be a non-blank string")
    return value


def _hash(value: Any, path: str) -> str:
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise ContractAValidationError(f"{path} must be lowercase sha256:<64 hex>")
    return value


def _validate_proposition(value: Any, path: str) -> dict[str, Any]:
    row = _object(value, path)
    keys = {"proposition_id", "text", "text_sha256"}
    _exact_keys(row, keys, keys, path)
    _nonblank(row["proposition_id"], f"{path}.proposition_id")
    text = _nonblank(row["text"], f"{path}.text")
    supplied = _hash(row["text_sha256"], f"{path}.text_sha256")
    expected = _sha256_text(text)
    if supplied != expected:
        raise ContractAValidationError(
            f"{path}.text_sha256 mismatch: supplied={supplied}, expected={expected}"
        )
    return row


def _validate_decomposition(value: Any, root_id: str) -> None:
    row = _object(value, "$.decomposition")
    state = row.get("state")
    if state not in DECOMPOSITION_STATES:
        raise ContractAValidationError(
            "$.decomposition.state must be one of declared, failed, not_decomposed, unknown"
        )
    if state != "declared":
        _exact_keys(row, {"state"}, {"state"}, "$.decomposition")
        return

    allowed = {"state", "decomposition_id", "operator", "children"}
    _exact_keys(row, allowed, allowed, "$.decomposition")
    _nonblank(row["decomposition_id"], "$.decomposition.decomposition_id")
    if row["operator"] != "all_of":
        raise ContractAValidationError("$.decomposition.operator must equal 'all_of'")
    children = _array(row["children"], "$.decomposition.children")
    if len(children) < 2:
        raise ContractAValidationError(
            "declared all_of decomposition requires at least two children"
        )

    ids: list[str] = []
    texts: list[str] = []
    sequences: list[int] = []
    for index, child_value in enumerate(children):
        path = f"$.decomposition.children[{index}]"
        child = _object(child_value, path)
        keys = {"proposition_id", "text", "text_sha256", "sequence"}
        _exact_keys(child, keys, keys, path)
        _validate_proposition(
            {
                "proposition_id": child["proposition_id"],
                "text": child["text"],
                "text_sha256": child["text_sha256"],
            },
            path,
        )
        sequence = child["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            raise ContractAValidationError(f"{path}.sequence must be an integer >= 1")
        ids.append(str(child["proposition_id"]))
        texts.append(str(child["text"]))
        sequences.append(sequence)

    if root_id in ids:
        raise ContractAValidationError(
            "a declared child proposition_id cannot equal the root proposition_id"
        )
    if len(ids) != len(set(ids)):
        raise ContractAValidationError("declared child proposition_id values must be unique")
    if len(texts) != len(set(texts)):
        raise ContractAValidationError("declared child text values must be unique")
    if len(sequences) != len(set(sequences)):
        raise ContractAValidationError("declared child sequence values must be unique")
    expected_sequences = list(range(1, len(children) + 1))
    if sequences != expected_sequences:
        raise ContractAValidationError(
            f"declared children must be ordered by contiguous sequence 1..N; got {sequences}"
        )


def _validate_sources(value: Any) -> None:
    rows = _array(value, "$.sources")
    source_ids: list[str] = []
    for index, source_value in enumerate(rows):
        path = f"$.sources[{index}]"
        source = _object(source_value, path)
        keys = {"source_id", "media_type", "content", "content_sha256"}
        _exact_keys(source, keys, keys, path)
        source_id = _nonblank(source["source_id"], f"{path}.source_id")
        media_type = source["media_type"]
        if media_type not in MEDIA_TYPES:
            raise ContractAValidationError(
                f"{path}.media_type must be one of {sorted(MEDIA_TYPES)!r}"
            )
        content = source["content"]
        if not isinstance(content, str):
            raise ContractAValidationError(f"{path}.content must be a string")
        supplied = _hash(source["content_sha256"], f"{path}.content_sha256")
        expected = _sha256_text(content)
        if supplied != expected:
            raise ContractAValidationError(
                f"{path}.content_sha256 mismatch: supplied={supplied}, expected={expected}"
            )
        source_ids.append(source_id)
    if len(source_ids) != len(set(source_ids)):
        raise ContractAValidationError("source_id values must be unique")


def validate_contract_a(value: Any) -> dict[str, Any]:
    """Validate one parsed Contract A 2.0 wire object and return it unchanged."""
    root = _object(value, "$")
    top = {
        "schema",
        "handoff_id",
        "producer",
        "work",
        "root_proposition",
        "decomposition",
        "sources",
        "handoff_sha256",
    }
    _exact_keys(root, top, top, "$")
    if root["schema"] != WIRE_SCHEMA_TOKEN:
        raise ContractAValidationError(f"$.schema must equal {WIRE_SCHEMA_TOKEN!r}")
    _nonblank(root["handoff_id"], "$.handoff_id")

    producer = _object(root["producer"], "$.producer")
    producer_keys = {"producer_id", "producer_version"}
    _exact_keys(producer, producer_keys, producer_keys, "$.producer")
    _nonblank(producer["producer_id"], "$.producer.producer_id")
    _nonblank(producer["producer_version"], "$.producer.producer_version")

    work = _object(root["work"], "$.work")
    _exact_keys(work, {"work_id"}, {"work_id"}, "$.work")
    _nonblank(work["work_id"], "$.work.work_id")

    proposition = _validate_proposition(root["root_proposition"], "$.root_proposition")
    _validate_decomposition(root["decomposition"], str(proposition["proposition_id"]))
    _validate_sources(root["sources"])

    supplied = _hash(root["handoff_sha256"], "$.handoff_sha256")
    expected = compute_handoff_sha256(root)
    if supplied != expected:
        raise ContractAValidationError(
            f"$.handoff_sha256 mismatch: supplied={supplied}, expected={expected}"
        )
    return root


def load_contract_a(path: Path) -> dict[str, Any]:
    """Load strict UTF-8 JSON and validate against the maintained A2 consumer."""
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=lambda token: (_ for _ in ()).throw(
                ContractAValidationError(f"non-finite JSON value is forbidden: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractAValidationError(f"invalid UTF-8 JSON: {exc}") from exc
    return validate_contract_a(value)


def primary_targets(value: dict[str, Any]) -> list[PrimaryTarget]:
    """Return only exact upstream-authoritative normative retrieval targets.

    A declared all_of decomposition yields one lane per exact declared child.
    A positively declared ``not_decomposed`` object yields one root lane.
    ``unknown`` and ``failed`` are deliberately not reinterpreted as
    ``not_decomposed`` and therefore fail closed.
    """
    validate_contract_a(value)
    decomposition = value["decomposition"]
    state = decomposition["state"]
    if state == "declared":
        return [
            PrimaryTarget(
                proposition_id=str(child["proposition_id"]),
                text=str(child["text"]),
                text_sha256=str(child["text_sha256"]),
                role="declared_child",
                sequence=int(child["sequence"]),
            )
            for child in decomposition["children"]
        ]
    if state == "not_decomposed":
        root = value["root_proposition"]
        return [
            PrimaryTarget(
                proposition_id=str(root["proposition_id"]),
                text=str(root["text"]),
                text_sha256=str(root["text_sha256"]),
                role="root",
                sequence=None,
            )
        ]
    raise ContractAValidationError(
        f"Contract A decomposition state {state!r} supplies no normative EB V1 target; "
        "EB will not infer not_decomposed"
    )
