from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from research.cal_rc0_contract_b_handoff import (
    build_handoff,
    evaluate_receipt,
    fixture_loader,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "cal_rc0_contract_b_handoff"
FIXTURES = RESEARCH / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture()
def inputs() -> tuple[dict, dict, dict, dict]:
    return (
        fixture_loader.load_cohort(FIXTURES),
        load("admission.json"),
        load("evaluator_gold.json"),
        json.loads((RESEARCH / "RESEARCH_EB_PROFILE.json").read_text(encoding="utf-8")),
    )


def test_contract_a_declared_child_identity_and_lane_survive(inputs) -> None:
    cohort, admission, _, profile = inputs
    receipt = build_handoff.build_runtime_receipt(
        cohort=cohort, admission=admission, profile=profile
    )
    by_case = {row["case_id"]: row for row in receipt["cases"]}
    for case in cohort["cases"]:
        actual = by_case[case["case_id"]]
        expected_children = case["contract_a"]["decomposition"]["children"]
        assert actual["declared_children"] == expected_children
        assert {
            row["retrieval_lane"] for row in actual["candidate_pool"]
        } <= {build_handoff.DECLARED_CHILD_LANE}
        assert {
            row["proposition_id"] for row in actual["candidate_pool"]
        } <= {row["proposition_id"] for row in expected_children}


def test_nomination_does_not_silently_become_admission(inputs) -> None:
    cohort, admission, _, profile = inputs
    receipt = build_handoff.build_runtime_receipt(
        cohort=cohort, admission=admission, profile=profile
    )
    assert any(
        len(case["candidate_pool"]) > len(case["admission"])
        for case in receipt["cases"]
    )
    assert all(
        len(case["admission"]) == len(case["retained"])
        for case in receipt["cases"]
    )
    assert any(
        row["decision"] == "needs-review"
        for case in receipt["cases"]
        for row in case["admission"]
    )


def test_rc0_handoff_never_flattens_parent_child_relationships(inputs) -> None:
    cohort, admission, _, profile = inputs
    receipt = build_handoff.build_runtime_receipt(
        cohort=cohort, admission=admission, profile=profile
    )
    assert profile["retrieval"]["parent_child_flattening"] is False
    assert all(case["flattened_parent_child"] is False for case in receipt["cases"])
    for case in receipt["cases"]:
        for row in case["candidate_pool"]:
            assert row["root_proposition_id"]
            assert row["proposition_id"]
            assert row["retrieval_lane"]


def test_optional_root_diagnostic_is_separate_and_labeled(inputs) -> None:
    cohort, admission, _, profile = inputs
    default = build_handoff.build_runtime_receipt(
        cohort=cohort, admission=admission, profile=profile
    )
    diagnostic = build_handoff.build_runtime_receipt(
        cohort=cohort,
        admission=admission,
        profile=profile,
        diagnostic_root_rescue=True,
    )
    assert not any(
        row["retrieval_lane"] == build_handoff.DIAGNOSTIC_ROOT_LANE
        for case in default["cases"]
        for row in case["candidate_pool"]
    )
    for case in diagnostic["cases"]:
        root_id = case["root_proposition"]["proposition_id"]
        root_rows = [
            row
            for row in case["candidate_pool"]
            if row["retrieval_lane"] == build_handoff.DIAGNOSTIC_ROOT_LANE
        ]
        assert root_rows
        assert {row["proposition_id"] for row in root_rows} == {root_id}


def test_duplicate_physical_evidence_preserves_identity_and_provenance(inputs) -> None:
    cohort, admission, _, profile = inputs
    receipt = build_handoff.build_runtime_receipt(
        cohort=cohort, admission=admission, profile=profile
    )
    case = next(row for row in receipt["cases"] if row["case_id"] == "C07_DUPLICATE")
    rows = {
        row["evidence_id"]: row
        for row in case["candidate_pool"]
        if row["evidence_id"] in {"C07-P1", "C07-P1T"}
    }
    assert set(rows) == {"C07-P1", "C07-P1T"}
    assert rows["C07-P1"]["source_id"] != rows["C07-P1T"]["source_id"]


def test_output_is_deterministic_for_pinned_inputs(inputs) -> None:
    cohort, admission, _, profile = inputs
    one = build_handoff.build_runtime_receipt(
        cohort=cohort, admission=admission, profile=profile
    )
    two = build_handoff.build_runtime_receipt(
        cohort=cohort, admission=admission, profile=profile
    )
    assert build_handoff.canonical_bytes(one) == build_handoff.canonical_bytes(two)


def test_evaluator_localizes_missing_required_evidence_by_stage(inputs) -> None:
    cohort, admission, gold, profile = inputs
    runtime = build_handoff.build_runtime_receipt(
        cohort=cohort, admission=admission, profile=profile
    )
    result = evaluate_receipt.evaluate(runtime, gold)
    assert result["missing_required_evidence_by_first_stage"] == {
        "candidate_pool": 1,
        "retention": 1,
        "admission": 1,
    }


def test_runtime_source_has_no_gold_or_cal_semantic_dependency() -> None:
    source = inspect.getsource(build_handoff)
    assert "claim_audit_lab" not in source
    assert "audit_claims" not in source
    assert "evaluator_gold" not in source


def test_research_receipt_does_not_invent_semantic_fields(inputs) -> None:
    cohort, admission, _, profile = inputs
    receipt = build_handoff.build_runtime_receipt(
        cohort=cohort, admission=admission, profile=profile
    )
    prohibited = {
        "support",
        "refutation",
        "proposition_specific_relation",
        "semantic_validity",
        "temporal_applicability",
        "authority_applicability",
        "supplier_applicability",
        "completeness_conclusion",
        "decision_participation",
        "audit_support_verdict",
        "verdict",
        "abstention",
        "warrant",
    }

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert key not in prohibited
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(receipt)


def test_contract_b_12_bundle_and_extension_validate_exactly(inputs, tmp_path) -> None:
    cohort, admission, _, profile = inputs
    receipt = build_handoff.build_runtime_receipt(
        cohort=cohort, admission=admission, profile=profile
    )
    results = build_handoff.build_all_contract_b(
        cohort=cohort,
        receipt=receipt,
        profile=profile,
        out_dir=tmp_path,
    )
    assert len(results) == len(cohort["cases"])
    assert all(result["contract_b_version"] == "1.2.0" for result in results)
    assert all(result["tree_validation"] == "PASS" for result in results)

    from evidence_bundler.contracts.factual_context import (
        ContractBFactualContext,
        canonical_bytes,
        validate_for_bundle,
    )
    from evidence_bundler.contracts.writer import validate_bundle_tree

    for result in results:
        bundle = tmp_path / "contract_b" / result["case_id"]
        assert validate_bundle_tree(bundle) == []
        extension_path = bundle / "extensions" / "contract-b-factual-context-v1.json"
        extension = ContractBFactualContext.model_validate_json(
            extension_path.read_text(encoding="utf-8")
        )
        assert canonical_bytes(extension) == extension_path.read_bytes()
        assert validate_for_bundle(bundle, extension) == []
