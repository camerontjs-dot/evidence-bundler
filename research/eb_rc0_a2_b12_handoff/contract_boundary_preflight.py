#!/usr/bin/env python3
"""Executable A2 -> B1.2 compatibility stop-condition preflight.

This is research infrastructure only. It does not retrieve evidence, call CAL,
or produce a Contract B candidate. A confirmed mismatch is a valid negative
result and must not be patched around inside this RC0.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from evidence_bundler.models.cb import ClaimAuditUnit

A_FIXTURE = Path("fixtures/contract-a/2.0.0/valid-all-of.json")
A_VALIDATOR = Path("validators/contract_a.py")
A_ENGINE = Path("validators/contract_a_rc2.py")
A_SPEC = Path("contract-a-v2.0.0.md")
B_SPEC = Path("handoff-contract-v1.0.0.md")
B_EXTENSION_SPEC = Path("contract-b-factual-context-extension-v1.2.0.md")

LEGACY_B_CORE_FIELDS = (
    "claim_type",
    "workflow_condition",
    "task_id",
    "scaffold_support_status",
    "scaffold_claim_strength",
    "scaffold_extraction_fidelity",
    "scaffold_counterevidence_found",
    "scaffold_downgraded",
)

FORBIDDEN_SEMANTIC_TEST_FIELD = "scaffold_support_status"


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apparatus-a", required=True, type=Path)
    parser.add_argument("--apparatus-b", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    a_root = args.apparatus_a.resolve()
    b_root = args.apparatus_b.resolve()
    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    # Use the released canonical A validator exactly from the pinned A checkout.
    sys.path.insert(0, str(a_root))
    from validators.contract_a import ContractAValidationError, load_candidate, validate_candidate  # type: ignore  # noqa: E402

    fixture_path = a_root / A_FIXTURE
    handoff = load_candidate(fixture_path)
    declared = handoff["decomposition"]
    assert declared["state"] == "declared"
    child = declared["children"][0]

    # Contract A 2.0 fails closed if a legacy semantic-looking scaffold field is added.
    hostile = copy.deepcopy(handoff)
    hostile[FORBIDDEN_SEMANTIC_TEST_FIELD] = "sourced"
    hostile_rejected = False
    hostile_error = ""
    try:
        validate_candidate(hostile)
    except ContractAValidationError as exc:
        hostile_rejected = True
        hostile_error = str(exc)
    if not hostile_rejected:
        raise AssertionError("canonical Contract A validator accepted hostile legacy field")

    # The canonical EB producer model for the locked Contract B core requires these fields.
    required = {
        name for name, field in ClaimAuditUnit.model_fields.items() if field.is_required()
    }
    missing_required_contract_b_fields = [
        name for name in LEGACY_B_CORE_FIELDS if name in required and name not in child
    ]
    if missing_required_contract_b_fields != list(LEGACY_B_CORE_FIELDS):
        raise AssertionError(
            "unexpected Contract B producer field set: "
            + canonical_json(missing_required_contract_b_fields)
        )

    # Attempt the smallest child claim construction using only mechanical B fields
    # plus A2-authoritative child identity. It must fail rather than invent legacy state.
    b_claim_rejected = False
    b_claim_errors: list[dict[str, Any]] = []
    try:
        ClaimAuditUnit(
            claim_id=child["proposition_id"],
            bundle_id="research-preflight-not-a-real-bundle",
            schema_version="1.2.0",
            claim_text=child["text"],
        )
    except ValidationError as exc:
        b_claim_rejected = True
        b_claim_errors = exc.errors(include_url=False)
    if not b_claim_rejected:
        raise AssertionError("Contract B core claim unexpectedly constructible from A2 identity alone")

    error_fields = {str(row["loc"][0]) for row in b_claim_errors if row.get("loc")}
    absent_from_error = [name for name in LEGACY_B_CORE_FIELDS if name not in error_fields]
    if absent_from_error:
        raise AssertionError(f"expected required B fields not reported missing: {absent_from_error}")

    a_spec = (a_root / A_SPEC).read_text(encoding="utf-8")
    b_spec = (b_root / B_SPEC).read_text(encoding="utf-8")
    b_ext_spec = (b_root / B_EXTENSION_SPEC).read_text(encoding="utf-8")

    textual_controls = {
        "a2_unknown_fields_fail_closed": "Unknown Contract-A-owned fields fail closed." in a_spec,
        "a2_nonauthority_excludes_upstream_support_labels":
            "upstream support/unsupported labels, confidence, claim strength, or extraction fidelity"
            in a_spec,
        "b_core_labels_from_ca_immutable":
            "Scaffold-assigned labels (from C-A; immutable in C-B)" in b_spec,
        "b12_additive_not_core_rewrite":
            "It does not rewrite the v1.0.0 contract body." in b_ext_spec,
        "b12_existing_core_records_canonical":
            "The existing Contract B claim/source/passage files remain canonical" in b_ext_spec,
    }
    if not all(textual_controls.values()):
        raise AssertionError(f"frozen textual control missing: {textual_controls}")

    report = {
        "schema": "research-eb-a2-b12-boundary-counterexample-v1",
        "result": "COUNTEREXAMPLE_CONFIRMED",
        "claim": (
            "A canonical Contract A 2.0 declared child cannot be emitted as a canonical "
            "Contract B 1.2 core claim without inventing legacy Contract-A-derived fields "
            "that Contract A 2.0 neither carries nor authorizes."
        ),
        "contract_a": {
            "version": "2.0.0",
            "fixture": str(A_FIXTURE),
            "fixture_sha256": sha256_file(fixture_path),
            "validator_sha256": sha256_file(a_root / A_VALIDATOR),
            "engine_sha256": sha256_file(a_root / A_ENGINE),
            "spec_sha256": sha256_file(a_root / A_SPEC),
            "handoff_id": handoff["handoff_id"],
            "root_proposition_id": handoff["root_proposition"]["proposition_id"],
            "decomposition_id": declared["decomposition_id"],
            "operator": declared["operator"],
            "first_child": {
                "proposition_id": child["proposition_id"],
                "text_sha256": child["text_sha256"],
                "sequence": child["sequence"],
            },
            "hostile_legacy_field_rejected": hostile_rejected,
            "hostile_legacy_field_error": hostile_error,
        },
        "contract_b": {
            "version": "1.2.0",
            "core_spec_sha256": sha256_file(b_root / B_SPEC),
            "extension_spec_sha256": sha256_file(b_root / B_EXTENSION_SPEC),
            "required_legacy_core_fields_absent_from_a2": missing_required_contract_b_fields,
            "a2_identity_only_claim_construction_rejected": b_claim_rejected,
            "missing_field_errors": sorted(error_fields),
            "extension_can_preserve_lineage_but_cannot_replace_core_claim": True,
        },
        "textual_controls": textual_controls,
        "stop_condition": "Contract B cannot preserve required root/child identity without semantic misuse.",
        "forbidden_workarounds": [
            "invent legacy scaffold semantic fields",
            "relabel retrieval metadata as semantic authority",
            "weaken canonical validation",
            "silently widen Contract B",
            "call CAL",
        ],
        "bounded_inference": (
            "RC0 cannot lawfully materialize the requested A2 -> B1.2 vertical under the frozen "
            "authorities. This is an interface-authority mismatch, not a retrieval-quality result."
        ),
    }
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("COUNTEREXAMPLE_CONFIRMED")
    print(f"receipt={out}")
    print("no retrieval, CAL, merge, release, tag, promotion, or production-default mutation performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
