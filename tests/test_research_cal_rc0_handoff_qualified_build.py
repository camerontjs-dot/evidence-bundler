from __future__ import annotations

import json
from pathlib import Path

from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.cb import BundleManifest

from research.cal_rc0_contract_b_handoff.build_handoff import build_runtime_receipt
from research.cal_rc0_contract_b_handoff.fixture_loader import load_cohort
from research.cal_rc0_contract_b_handoff.qualified_handoff import build_all_contract_b_qualified


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT / "research" / "cal_rc0_contract_b_handoff"


def test_qualified_build_reports_final_resealed_hashes(tmp_path: Path) -> None:
    cohort = load_cohort(RESEARCH_ROOT / "fixtures" / "cases")
    admission = json.loads(
        (RESEARCH_ROOT / "fixtures" / "admission.json").read_text(encoding="utf-8")
    )
    profile = json.loads(
        (RESEARCH_ROOT / "RESEARCH_EB_PROFILE.json").read_text(encoding="utf-8")
    )
    receipt = build_runtime_receipt(cohort=cohort, admission=admission, profile=profile)
    results = build_all_contract_b_qualified(
        cohort=cohort,
        receipt=receipt,
        profile=profile,
        out_dir=tmp_path,
    )
    assert len(results) == 8
    for row in results:
        manifest = load_model_yaml(
            BundleManifest,
            tmp_path / "contract_b" / row["case_id"] / "bundle_manifest.yaml",
        )
        assert row["bundle_hash"] == manifest.bundle.bundle_hash
        assert row["tree_validation"] == "PASS"
