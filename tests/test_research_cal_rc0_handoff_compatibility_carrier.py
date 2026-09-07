from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

import pytest

from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.cb import ClaimAuditUnit, PassageRecord, SourceProfile
from research.cal_rc0_contract_b_handoff.build_handoff import build_runtime_receipt
from research.cal_rc0_contract_b_handoff.fixture_loader import load_cohort
from research.cal_rc0_contract_b_handoff.qualified_handoff import (
    build_all_contract_b_qualified,
    validate_compatibility_carrier,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT / "research" / "cal_rc0_contract_b_handoff"
FIXTURES = RESEARCH_ROOT / "fixtures"


def load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def load_inputs() -> tuple[dict, dict, dict, dict]:
    cohort = load_cohort(FIXTURES)
    admission = load_json("admission.json")
    profile = json.loads(
        (RESEARCH_ROOT / "RESEARCH_EB_PROFILE.json").read_text(encoding="utf-8")
    )
    carrier = load_json("contract_b_compatibility_carrier.json")
    return cohort, admission, profile, carrier


def test_missing_or_weakened_compatibility_carrier_fails_closed() -> None:
    _, _, _, carrier = load_inputs()
    with pytest.raises(ValueError):
        validate_compatibility_carrier({})

    weakened = copy.deepcopy(carrier)
    weakened["authority"]["semantic_use_authorized"] = True
    with pytest.raises(ValueError, match="authority boundary"):
        validate_compatibility_carrier(weakened)

    incomplete = copy.deepcopy(carrier)
    del incomplete["legacy_claim_fields"]["scaffold_extraction_fidelity"]
    with pytest.raises(ValueError, match="claim compatibility field set"):
        validate_compatibility_carrier(incomplete)


def test_carrier_cannot_influence_retrieval_or_admission_receipt() -> None:
    cohort, admission, profile, carrier = load_inputs()
    assert "compatibility_carrier" not in inspect.signature(build_runtime_receipt).parameters

    before = build_runtime_receipt(cohort=cohort, admission=admission, profile=profile)
    mutated = copy.deepcopy(carrier)
    mutated["legacy_claim_fields"]["scaffold_support_status"] = "unsupported"
    mutated["source_profile"]["trust_level"] = "primary"
    after = build_runtime_receipt(cohort=cohort, admission=admission, profile=profile)
    assert before == after


def test_final_b_uses_explicit_carrier_and_exact_a2_source_binding(tmp_path: Path) -> None:
    cohort, admission, profile, carrier = load_inputs()
    receipt = build_runtime_receipt(cohort=cohort, admission=admission, profile=profile)
    build_all_contract_b_qualified(
        cohort=cohort,
        receipt=receipt,
        profile=profile,
        compatibility_carrier=carrier,
        out_dir=tmp_path,
    )

    case = cohort["cases"][0]
    contract_a = case["contract_a"]
    bundle = tmp_path / "contract_b" / case["case_id"]
    child_id = contract_a["decomposition"]["children"][0]["proposition_id"]
    claim = load_model_yaml(ClaimAuditUnit, bundle / "claims" / f"{child_id}.yaml")

    legacy = carrier["legacy_claim_fields"]
    assert claim.claim_type == legacy["claim_type"]
    assert claim.workflow_condition == legacy["workflow_condition"]
    assert claim.task_id == contract_a["work"]["work_id"]
    assert claim.scaffold_support_status == legacy["scaffold_support_status"]
    assert claim.scaffold_claim_strength == legacy["scaffold_claim_strength"]
    assert claim.scaffold_extraction_fidelity == legacy["scaffold_extraction_fidelity"]
    assert all(
        row.source_trust_level == carrier["source_profile"]["trust_level"]
        for row in claim.evidence_passages
    )

    evidence = claim.evidence_passages[0]
    source = next(
        row for row in contract_a["sources"] if row["source_id"] == evidence.source_id
    )
    source_profile = load_model_yaml(
        SourceProfile, bundle / "evidence" / evidence.source_id / "source_profile.yaml"
    )
    assert source_profile.bibliographic.source_type == "other"
    assert source_profile.trust_level == "background"
    assert source_profile.content_hash == source["content_sha256"]
    assert source_profile.bibliographic.publication_date is None

    passage = load_model_yaml(
        PassageRecord,
        bundle
        / "evidence"
        / evidence.source_id
        / "passages"
        / f"{evidence.passage_id}.yaml",
    )
    assert passage.extraction_method == carrier["passage_record"]["extraction_method"]
    assert passage.provenance.source_content_hash == source["content_sha256"]
    assert source["content"][passage.char_start : passage.char_end] == passage.passage_text
