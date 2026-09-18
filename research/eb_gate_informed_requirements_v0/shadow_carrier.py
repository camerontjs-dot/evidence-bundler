"""Shadow-only Gate observation carrier for Evidence Bundler research.

This module is research infrastructure. It deliberately has no retrieval, ranking,
selection, admission, CAL, Decision, or Authorization behavior.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

REGISTRY_SCHEMA = "eb-gate-informed-shadow-field-registry-v0"
PACKET_SCHEMA = "eb-gate-shadow-observation-packet-v0"
CARRIER_SCHEMA = "eb-gate-shadow-carrier-output-v0"

NON_CAUSAL_CONSUMPTION_STATES = frozenset(
    {
        "VISIBLE_SHADOW",
        "PRESSURE_TEST_ELIGIBLE",
    }
)

OBSERVATION_STATES = frozenset(
    {
        "known",
        "unknown",
        "not_applicable",
        "declared_none",
        "declared_some",
    }
)

# These are instruction-bearing payload keys, not descriptive evidence fields.
# Legitimate observations such as source_id, evidence_form, or proposition_id are allowed.
FORBIDDEN_INSTRUCTION_KEYS = frozenset(
    {
        "query",
        "query_string",
        "query_terms",
        "query_rewrite",
        "source_route",
        "source_routes",
        "source_ids_to_search",
        "preferred_source_id",
        "preferred_domain",
        "passage_id_to_keep",
        "passage_ids_to_keep",
        "rank_weight",
        "rank_weights",
        "retained_k",
        "admission",
        "admission_decision",
        "supports_refutes",
        "semantic_verdict",
        "decision",
        "authorization",
        "automatic_action",
    }
)

_ALLOWED_RECORD_KEYS = frozenset({"state", "value", "basis"})


class ShadowCarrierError(ValueError):
    """Raised when shadow-carrier input violates the research boundary."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes or fail on non-JSON values."""

    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ShadowCarrierError(f"value is not canonical JSON: {exc}") from exc
    return text.encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _scan_forbidden_instruction_keys(value: Any, *, path: str) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            if key.casefold() in FORBIDDEN_INSTRUCTION_KEYS:
                raise ShadowCarrierError(
                    f"forbidden causal instruction key at {path}.{key}: {key}"
                )
            _scan_forbidden_instruction_keys(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden_instruction_keys(child, path=f"{path}[{index}]")


def _normalized_registry(registry: Mapping[str, Any]) -> dict[str, Any]:
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise ShadowCarrierError("unsupported shadow registry schema")
    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ShadowCarrierError("registry.entries must be a non-empty list")

    normalized_entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(entries):
        if not isinstance(raw, Mapping):
            raise ShadowCarrierError(f"registry entry {index} must be an object")
        field_id = raw.get("field_id")
        if not isinstance(field_id, str) or not field_id:
            raise ShadowCarrierError(f"registry entry {index} has invalid field_id")
        if field_id in seen:
            raise ShadowCarrierError(f"duplicate registry field_id: {field_id}")
        seen.add(field_id)

        state = raw.get("eb_consumption_state")
        if state not in NON_CAUSAL_CONSUMPTION_STATES:
            raise ShadowCarrierError(
                f"field {field_id} has causal or unsupported EB consumption state: {state!r}"
            )
        normalized_entries.append(dict(raw))

    normalized = dict(registry)
    normalized["entries"] = sorted(normalized_entries, key=lambda row: row["field_id"])
    return normalized


def validate_registry(registry: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and canonicalize a shadow registry.

    Only non-causal EB consumption states are accepted.
    """

    normalized = _normalized_registry(registry)
    canonical_json_bytes(normalized)
    return normalized


def registry_field_ids(registry: Mapping[str, Any]) -> tuple[str, ...]:
    normalized = validate_registry(registry)
    return tuple(row["field_id"] for row in normalized["entries"])


def _validate_record(field_id: str, record: Any) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ShadowCarrierError(f"{field_id}: observation record must be an object")
    unknown_keys = set(record) - _ALLOWED_RECORD_KEYS
    if unknown_keys:
        raise ShadowCarrierError(
            f"{field_id}: unsupported observation keys: {sorted(unknown_keys)}"
        )
    missing = _ALLOWED_RECORD_KEYS - set(record)
    if missing:
        raise ShadowCarrierError(f"{field_id}: missing observation keys: {sorted(missing)}")

    state = record.get("state")
    if state not in OBSERVATION_STATES:
        raise ShadowCarrierError(f"{field_id}: unsupported observation state {state!r}")

    value = record.get("value")
    if state in {"unknown", "not_applicable"} and value is not None:
        raise ShadowCarrierError(f"{field_id}: {state} observation must have value=null")

    basis = record.get("basis")
    if not isinstance(basis, Mapping):
        raise ShadowCarrierError(f"{field_id}: basis must be an object")

    normalized = {
        "state": state,
        "value": copy.deepcopy(value),
        "basis": copy.deepcopy(dict(basis)),
    }
    _scan_forbidden_instruction_keys(normalized, path=f"fields.{field_id}")
    canonical_json_bytes(normalized)
    return normalized


def validate_packet(
    registry: Mapping[str, Any], packet: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate one normalized shadow-observation packet."""

    normalized_registry = validate_registry(registry)
    allowed_fields = {row["field_id"] for row in normalized_registry["entries"]}

    if packet.get("schema") != PACKET_SCHEMA:
        raise ShadowCarrierError("unsupported observation packet schema")
    case_id = packet.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        raise ShadowCarrierError("packet.case_id must be a non-empty string")

    upstream_identity = packet.get("upstream_identity")
    if not isinstance(upstream_identity, Mapping):
        raise ShadowCarrierError("packet.upstream_identity must be an object")
    canonical_json_bytes(upstream_identity)

    fields = packet.get("fields")
    if not isinstance(fields, Mapping):
        raise ShadowCarrierError("packet.fields must be an object")

    normalized_fields: dict[str, dict[str, Any]] = {}
    for field_id, record in fields.items():
        if not isinstance(field_id, str):
            raise ShadowCarrierError("packet field IDs must be strings")
        if field_id not in allowed_fields:
            raise ShadowCarrierError(f"packet contains unregistered field: {field_id}")
        normalized_fields[field_id] = _validate_record(field_id, record)

    return {
        "schema": PACKET_SCHEMA,
        "case_id": case_id,
        "upstream_identity": copy.deepcopy(dict(upstream_identity)),
        "fields": dict(sorted(normalized_fields.items())),
    }


def _validate_requested_fields(
    registry: Mapping[str, Any], requested_fields: Sequence[str]
) -> tuple[str, ...]:
    allowed = set(registry_field_ids(registry))
    if not isinstance(requested_fields, Sequence) or isinstance(requested_fields, (str, bytes)):
        raise ShadowCarrierError("requested_fields must be a sequence of field IDs")

    requested = list(requested_fields)
    if any(not isinstance(field_id, str) or not field_id for field_id in requested):
        raise ShadowCarrierError("requested_fields contains an invalid field ID")
    if len(requested) != len(set(requested)):
        raise ShadowCarrierError("requested_fields must not contain duplicates")

    unknown = sorted(set(requested) - allowed)
    if unknown:
        raise ShadowCarrierError(f"requested_fields contains unregistered fields: {unknown}")
    return tuple(sorted(requested))


def build_shadow_carrier(
    *,
    registry: Mapping[str, Any],
    packet: Mapping[str, Any],
    requested_fields: Sequence[str],
    substitutions: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Build a deterministic, non-causal shadow observation carrier.

    A substitution is an explicit experimental replacement for the *same* field ID:
    {"field_id": ..., "source_case_id": ..., "record": {...}}.

    This is how wrong/shuffled-hint controls can be materialized without adding any
    retrieval or selection behavior to the carrier itself.
    """

    normalized_registry = validate_registry(registry)
    normalized_packet = validate_packet(normalized_registry, packet)
    requested = _validate_requested_fields(normalized_registry, requested_fields)

    observations = {
        field_id: copy.deepcopy(normalized_packet["fields"][field_id])
        for field_id in requested
        if field_id in normalized_packet["fields"]
    }

    substitution_receipts: list[dict[str, Any]] = []
    seen_substitution_fields: set[str] = set()
    for index, raw_substitution in enumerate(substitutions):
        if not isinstance(raw_substitution, Mapping):
            raise ShadowCarrierError(f"substitution {index} must be an object")
        if set(raw_substitution) != {"field_id", "source_case_id", "record"}:
            raise ShadowCarrierError(
                f"substitution {index} must contain exactly field_id, source_case_id, record"
            )
        field_id = raw_substitution["field_id"]
        source_case_id = raw_substitution["source_case_id"]
        if field_id not in requested:
            raise ShadowCarrierError(
                f"substitution {index} targets non-requested field: {field_id}"
            )
        if field_id in seen_substitution_fields:
            raise ShadowCarrierError(f"duplicate substitution for field: {field_id}")
        if not isinstance(source_case_id, str) or not source_case_id:
            raise ShadowCarrierError(f"substitution {index} has invalid source_case_id")
        record = _validate_record(field_id, raw_substitution["record"])
        observations[field_id] = record
        seen_substitution_fields.add(field_id)
        substitution_receipts.append(
            {
                "field_id": field_id,
                "source_case_id": source_case_id,
                "record_sha256": sha256_json(record),
            }
        )

    present = tuple(sorted(observations))
    missing_requested = tuple(sorted(set(requested) - set(present)))
    masked_out = tuple(
        sorted(set(normalized_packet["fields"]) - set(requested))
    )

    registry_sha = sha256_json(normalized_registry)
    packet_sha = sha256_json(normalized_packet)
    mask_object = {
        "requested_fields": list(requested),
        "present_fields": list(present),
        "missing_requested_fields": list(missing_requested),
        "masked_out_fields": list(masked_out),
    }
    observations_sha = sha256_json(observations)

    output: dict[str, Any] = {
        "schema": CARRIER_SCHEMA,
        "case_id": normalized_packet["case_id"],
        "registry_sha256": registry_sha,
        "input_packet_sha256": packet_sha,
        "mask": mask_object,
        "mask_sha256": sha256_json(mask_object),
        "observations": dict(sorted(observations.items())),
        "observations_sha256": observations_sha,
        "substitutions": sorted(
            substitution_receipts, key=lambda row: (row["field_id"], row["source_case_id"])
        ),
        "causal_effects_authorized": False,
        "retrieval_behavior_changed": False,
        "selection_behavior_changed": False,
        "admission_behavior_changed": False,
        "nonclaims": [
            "shadow visibility is not EB hint authority",
            "the carrier does not prescribe queries, sources, passages, ranks, K, or admission",
            "the carrier does not judge support, refutation, truth, sufficiency, or authorization",
        ],
    }
    output["output_sha256"] = sha256_json(output)
    return output


def verify_shadow_carrier(output: Mapping[str, Any]) -> None:
    """Fail if a serialized carrier is malformed or its bound hash is stale."""

    if output.get("schema") != CARRIER_SCHEMA:
        raise ShadowCarrierError("unsupported carrier output schema")
    expected = output.get("output_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ShadowCarrierError("carrier output_sha256 must be a 64-character SHA-256")
    unsigned = dict(output)
    unsigned.pop("output_sha256", None)
    actual = sha256_json(unsigned)
    if actual != expected:
        raise ShadowCarrierError(
            f"carrier output hash mismatch: expected {expected}, recomputed {actual}"
        )

    for field in (
        "causal_effects_authorized",
        "retrieval_behavior_changed",
        "selection_behavior_changed",
        "admission_behavior_changed",
    ):
        if output.get(field) is not False:
            raise ShadowCarrierError(f"carrier boundary flag must remain false: {field}")

    _scan_forbidden_instruction_keys(output.get("observations", {}), path="observations")


def rotated_wrong_substitutions(
    *,
    registry: Mapping[str, Any],
    packets: Sequence[Mapping[str, Any]],
    field_ids: Sequence[str],
) -> dict[str, list[dict[str, Any]]]:
    """Build a deterministic cyclic wrong-hint control.

    Cases are sorted by case_id. Each target case receives the requested field
    records from the next case, wrapping at the end. No random state is used.
    """

    if len(packets) < 2:
        raise ShadowCarrierError("wrong-hint permutation requires at least two cases")

    normalized = [validate_packet(registry, packet) for packet in packets]
    by_case = {packet["case_id"]: packet for packet in normalized}
    if len(by_case) != len(normalized):
        raise ShadowCarrierError("wrong-hint permutation requires unique case_id values")

    requested = _validate_requested_fields(registry, field_ids)
    ordered_ids = sorted(by_case)
    result: dict[str, list[dict[str, Any]]] = {}

    for index, target_case in enumerate(ordered_ids):
        source_case = ordered_ids[(index + 1) % len(ordered_ids)]
        source_fields = by_case[source_case]["fields"]
        substitutions: list[dict[str, Any]] = []
        for field_id in requested:
            if field_id not in source_fields:
                continue
            substitutions.append(
                {
                    "field_id": field_id,
                    "source_case_id": source_case,
                    "record": copy.deepcopy(source_fields[field_id]),
                }
            )
        result[target_case] = substitutions

    return result


def carrier_source_boundary_tokens() -> tuple[str, ...]:
    """Tokens that a source-level pressure test should forbid in this module."""

    return (
        "evidence_bundler.retrieval",
        "query_bm25",
        "semantic_select",
        "typed_select",
        "admission_state",
        "contract_b",
        "claim_audit",
        "decision_engine",
    )
