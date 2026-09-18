from __future__ import annotations

import argparse
import ast
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

from shadow_carrier import (
    FORBIDDEN_INSTRUCTION_KEYS,
    ShadowCarrierError,
    build_shadow_carrier,
    registry_field_ids,
    rotated_wrong_substitutions,
    sha256_json,
    validate_registry,
    verify_shadow_carrier,
)

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "SHADOW-FIELD-REGISTRY.json"
CARRIER_PATH = ROOT / "shadow_carrier.py"


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def record(case_id: str, field_id: str) -> dict[str, Any]:
    return {
        "state": "known",
        "value": {
            "case_id": case_id,
            "field_id": field_id,
            "observation": f"{case_id}:{field_id}",
        },
        "basis": {
            "kind": "generated_pressure_fixture",
            "case_id": case_id,
            "field_id": field_id,
        },
    }


def packet(case_id: str, field_ids: tuple[str, ...]) -> dict[str, Any]:
    return {
        "schema": "eb-gate-shadow-observation-packet-v0",
        "case_id": case_id,
        "upstream_identity": {
            "producer": "generated-pressure-apparatus",
            "implementation_identity": "shadow-carrier-pressure-v0",
            "artifact_sha256": "sha256:" + sha256_json({"case_id": case_id}),
        },
        "fields": {field_id: record(case_id, field_id) for field_id in field_ids},
    }


def expect_error(callable_: Any, contains: str) -> None:
    try:
        callable_()
    except ShadowCarrierError as exc:
        if contains not in str(exc):
            raise AssertionError(
                f"expected error containing {contains!r}, got {str(exc)!r}"
            ) from exc
    else:
        raise AssertionError(f"expected ShadowCarrierError containing {contains!r}")


def assert_no_product_imports() -> list[str]:
    tree = ast.parse(CARRIER_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    prohibited = sorted(name for name in imported if name.startswith("evidence_bundler"))
    if prohibited:
        raise AssertionError(f"shadow carrier imports EB product/runtime modules: {prohibited}")
    return sorted(imported)


def run_pressure() -> dict[str, Any]:
    registry = load_registry()
    normalized_registry = validate_registry(registry)
    field_ids = registry_field_ids(registry)
    if len(field_ids) != 92:
        raise AssertionError(f"expected 92 registered fields, found {len(field_ids)}")

    case_ids = ("CASE-A", "CASE-B", "CASE-C", "CASE-D", "CASE-E")
    packets = [packet(case_id, field_ids) for case_id in case_ids]

    assertion_counts: Counter[str] = Counter()
    details: dict[str, Any] = {}

    # 1. Exact replay and requested-field order invariance.
    for source in packets:
        first = build_shadow_carrier(
            registry=registry,
            packet=source,
            requested_fields=field_ids,
        )
        second = build_shadow_carrier(
            registry=registry,
            packet=source,
            requested_fields=tuple(reversed(field_ids)),
        )
        if first != second:
            raise AssertionError(f"{source['case_id']}: exact replay/mask-order mismatch")
        verify_shadow_carrier(first)
        assertion_counts["exact_replay_and_mask_order"] += 1

    # 2. Registry entry order must not change the normalized registry identity or output.
    reversed_registry = copy.deepcopy(registry)
    reversed_registry["entries"] = list(reversed(reversed_registry["entries"]))
    if sha256_json(validate_registry(registry)) != sha256_json(
        validate_registry(reversed_registry)
    ):
        raise AssertionError("registry entry ordering changed normalized registry identity")
    base = build_shadow_carrier(
        registry=registry,
        packet=packets[0],
        requested_fields=field_ids,
    )
    reordered_registry_output = build_shadow_carrier(
        registry=reversed_registry,
        packet=packets[0],
        requested_fields=field_ids,
    )
    if base != reordered_registry_output:
        raise AssertionError("registry entry ordering changed carrier output")
    assertion_counts["registry_order_invariance"] += 1

    # 3. Packet field order must not matter.
    for source in packets:
        reordered = copy.deepcopy(source)
        reordered["fields"] = dict(reversed(list(reordered["fields"].items())))
        first = build_shadow_carrier(
            registry=registry,
            packet=source,
            requested_fields=field_ids,
        )
        second = build_shadow_carrier(
            registry=registry,
            packet=reordered,
            requested_fields=field_ids,
        )
        if first != second:
            raise AssertionError(f"{source['case_id']}: packet order changed output")
        assertion_counts["packet_order_invariance"] += 1

    # 4. Every field must survive an isolated single-field mask for every case.
    for source in packets:
        for field_id in field_ids:
            output = build_shadow_carrier(
                registry=registry,
                packet=source,
                requested_fields=[field_id],
            )
            verify_shadow_carrier(output)
            if list(output["observations"]) != [field_id]:
                raise AssertionError(
                    f"{source['case_id']}/{field_id}: single-field mask leaked observations"
                )
            if output["observations"][field_id] != source["fields"][field_id]:
                raise AssertionError(
                    f"{source['case_id']}/{field_id}: single-field value changed"
                )
            assertion_counts["single_field_masks"] += 1

    # 5. Every layer must be maskable without cross-layer leakage.
    layers: dict[str, list[str]] = {}
    for entry in normalized_registry["entries"]:
        layers.setdefault(entry["layer"], []).append(entry["field_id"])
    for layer, layer_fields in sorted(layers.items()):
        for source in packets:
            output = build_shadow_carrier(
                registry=registry,
                packet=source,
                requested_fields=layer_fields,
            )
            if set(output["observations"]) != set(layer_fields):
                raise AssertionError(f"{source['case_id']}/{layer}: layer mask leaked")
            verify_shadow_carrier(output)
            assertion_counts["layer_masks"] += 1
    details["layer_field_counts"] = {
        layer: len(fields) for layer, fields in sorted(layers.items())
    }

    # 6. Masked-out mutations may change raw input identity but not visible observations.
    target_case = packets[0]
    requested = list(field_ids[:8])
    masked_field = field_ids[-1]
    mutated = copy.deepcopy(target_case)
    mutated["fields"][masked_field]["value"]["observation"] = "masked-mutation"
    before = build_shadow_carrier(
        registry=registry,
        packet=target_case,
        requested_fields=requested,
    )
    after = build_shadow_carrier(
        registry=registry,
        packet=mutated,
        requested_fields=requested,
    )
    if before["observations_sha256"] != after["observations_sha256"]:
        raise AssertionError("masked field mutation changed visible observations")
    if before["input_packet_sha256"] == after["input_packet_sha256"]:
        raise AssertionError("masked field mutation did not change raw packet identity")
    assertion_counts["masked_mutation_isolation"] += 1

    # 7. Upstream metadata changes are receipt-visible but cannot alter observations.
    upstream_mutated = copy.deepcopy(target_case)
    upstream_mutated["upstream_identity"]["irrelevant_note"] = "changed"
    after_upstream = build_shadow_carrier(
        registry=registry,
        packet=upstream_mutated,
        requested_fields=requested,
    )
    if before["observations_sha256"] != after_upstream["observations_sha256"]:
        raise AssertionError("upstream metadata mutation changed visible observations")
    if before["input_packet_sha256"] == after_upstream["input_packet_sha256"]:
        raise AssertionError("upstream metadata mutation did not change packet identity")
    assertion_counts["upstream_metadata_isolation"] += 1

    # 8. Unknown must remain unknown for every registered field.
    unknown_packet = {
        "schema": "eb-gate-shadow-observation-packet-v0",
        "case_id": "CASE-UNKNOWN",
        "upstream_identity": {"producer": "pressure", "state": "unknown_fixture"},
        "fields": {
            field_id: {
                "state": "unknown",
                "value": None,
                "basis": {"kind": "generated_unknown_fixture"},
            }
            for field_id in field_ids
        },
    }
    unknown_output = build_shadow_carrier(
        registry=registry,
        packet=unknown_packet,
        requested_fields=field_ids,
    )
    for field_id, observed in unknown_output["observations"].items():
        if observed["state"] != "unknown" or observed["value"] is not None:
            raise AssertionError(f"{field_id}: unknown state was altered or invented")
        assertion_counts["unknown_preservation"] += 1

    # 9. Missing requested fields remain missing; the carrier invents nothing.
    empty_packet = {
        "schema": "eb-gate-shadow-observation-packet-v0",
        "case_id": "CASE-MISSING",
        "upstream_identity": {"producer": "pressure", "state": "missing_fixture"},
        "fields": {},
    }
    missing_output = build_shadow_carrier(
        registry=registry,
        packet=empty_packet,
        requested_fields=field_ids,
    )
    if missing_output["observations"]:
        raise AssertionError("carrier invented observations for missing fields")
    if set(missing_output["mask"]["missing_requested_fields"]) != set(field_ids):
        raise AssertionError("missing-requested receipt does not cover all fields")
    assertion_counts["no_invention_for_missing_fields"] += len(field_ids)

    # 10. Wrong/shuffled controls: every registered field, every case.
    permutations = rotated_wrong_substitutions(
        registry=registry,
        packets=packets,
        field_ids=field_ids,
    )
    reverse_permutations = rotated_wrong_substitutions(
        registry=registry,
        packets=list(reversed(packets)),
        field_ids=list(reversed(field_ids)),
    )
    if permutations != reverse_permutations:
        raise AssertionError("wrong-hint permutation depends on input ordering")

    packets_by_case = {source["case_id"]: source for source in packets}
    ordered_cases = sorted(packets_by_case)
    for index, target_case_id in enumerate(ordered_cases):
        source_case_id = ordered_cases[(index + 1) % len(ordered_cases)]
        output = build_shadow_carrier(
            registry=registry,
            packet=packets_by_case[target_case_id],
            requested_fields=field_ids,
            substitutions=permutations[target_case_id],
        )
        verify_shadow_carrier(output)
        if len(output["substitutions"]) != len(field_ids):
            raise AssertionError(f"{target_case_id}: incomplete substitution receipt")
        for field_id in field_ids:
            expected = packets_by_case[source_case_id]["fields"][field_id]
            if output["observations"][field_id] != expected:
                raise AssertionError(
                    f"{target_case_id}/{field_id}: wrong-hint value not sourced correctly"
                )
            assertion_counts["wrong_hint_substitutions"] += 1

    # 11. Instruction-bearing keys must fail closed.
    instruction_field = field_ids[0]
    for forbidden_key in sorted(FORBIDDEN_INSTRUCTION_KEYS):
        bad = packet("CASE-FORBIDDEN", (instruction_field,))
        bad["fields"][instruction_field]["value"] = {
            "descriptive": True,
            forbidden_key: "instruction",
        }
        expect_error(
            lambda bad=bad: build_shadow_carrier(
                registry=registry,
                packet=bad,
                requested_fields=[instruction_field],
            ),
            "forbidden causal instruction",
        )
        assertion_counts["causal_smuggling_rejections"] += 1

    # 12. An unregistered field must fail closed.
    unregistered = packet("CASE-UNREGISTERED", (field_ids[0],))
    unregistered["fields"]["claim.unregistered_pressure_field"] = record(
        "CASE-UNREGISTERED", "claim.unregistered_pressure_field"
    )
    expect_error(
        lambda: build_shadow_carrier(
            registry=registry,
            packet=unregistered,
            requested_fields=[field_ids[0]],
        ),
        "unregistered field",
    )
    assertion_counts["unregistered_field_rejection"] += 1

    # 13. Duplicate mask entries must fail closed.
    expect_error(
        lambda: build_shadow_carrier(
            registry=registry,
            packet=packets[0],
            requested_fields=[field_ids[0], field_ids[0]],
        ),
        "duplicates",
    )
    assertion_counts["duplicate_mask_rejection"] += 1

    # 14. Causal registry authority must fail closed.
    causal_registry = copy.deepcopy(registry)
    causal_registry["entries"][0]["eb_consumption_state"] = "QUALIFIED_EB_HINT"
    expect_error(lambda: validate_registry(causal_registry), "causal or unsupported")
    assertion_counts["causal_registry_rejection"] += 1

    # 15. A substitution cannot target a masked-out field.
    expect_error(
        lambda: build_shadow_carrier(
            registry=registry,
            packet=packets[0],
            requested_fields=[],
            substitutions=[
                {
                    "field_id": field_ids[0],
                    "source_case_id": "CASE-B",
                    "record": packets[1]["fields"][field_ids[0]],
                }
            ],
        ),
        "non-requested field",
    )
    assertion_counts["masked_substitution_rejection"] += 1

    # 16. Bound output hash must detect tampering.
    valid = build_shadow_carrier(
        registry=registry,
        packet=packets[0],
        requested_fields=field_ids,
    )
    verify_shadow_carrier(valid)
    for key, value in (
        ("causal_effects_authorized", True),
        ("retrieval_behavior_changed", True),
        ("selection_behavior_changed", True),
        ("admission_behavior_changed", True),
    ):
        tampered = copy.deepcopy(valid)
        tampered[key] = value
        expect_error(lambda tampered=tampered: verify_shadow_carrier(tampered), "hash mismatch")
        assertion_counts["bound_hash_tamper_rejection"] += 1

    # 17. The carrier module may not import Evidence Bundler product/runtime code.
    imports = assert_no_product_imports()
    assertion_counts["no_product_runtime_imports"] += 1
    details["carrier_imports"] = imports

    total_assertions = sum(assertion_counts.values())
    result = {
        "schema": "eb-gate-shadow-carrier-pressure-result-v0",
        "status": "SUPPORTED_SHADOW_CARRIER_APPARATUS",
        "scope": "carrier_apparatus_only_not_field_semantics",
        "registry": {
            "field_count": len(field_ids),
            "registry_sha256": sha256_json(normalized_registry),
            "layers": details["layer_field_counts"],
        },
        "pressure_cases": list(case_ids),
        "assertion_counts": dict(sorted(assertion_counts.items())),
        "total_assertions": total_assertions,
        "boundary_results": {
            "exact_replay": "PASS",
            "input_order_invariance": "PASS",
            "mask_order_invariance": "PASS",
            "registry_order_invariance": "PASS",
            "single_field_isolation_all_92": "PASS",
            "layer_isolation": "PASS",
            "masked_mutation_isolation": "PASS",
            "unknown_preservation_all_92": "PASS",
            "missing_field_no_invention_all_92": "PASS",
            "wrong_hint_rotation_all_92_x_5_cases": "PASS",
            "causal_instruction_smuggling_rejected": "PASS",
            "causal_registry_state_rejected": "PASS",
            "tamper_detection": "PASS",
            "product_runtime_imports_absent": "PASS",
        },
        "nonclaims": [
            "does not qualify any of the 92 fields as semantically correct",
            "does not authorize any field for causal Evidence Bundler use",
            "does not test retrieval, ranking, retention, admission, CAL, Decision, or Authorization",
            "does not supersede Proposition Authoring pressure results",
        ],
        "next_authorized_step": (
            "pressure actual field representations through the shadow carrier while all "
            "retrieval and selection behavior remains frozen"
        ),
    }
    result["result_sha256"] = sha256_json(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    result = run_pressure()
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
