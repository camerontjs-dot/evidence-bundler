from __future__ import annotations

import json
import sys
from pathlib import Path

from research.cal_rc0_contract_b_handoff.qualification_runner import main

RESEARCH_ROOT = (
    Path(__file__).resolve().parents[1] / "research" / "cal_rc0_contract_b_handoff"
)


def test_qualification_runner_emits_inspectable_bundle_tree(
    tmp_path: Path, monkeypatch
) -> None:
    out_dir = tmp_path / "qualification-output"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qualification_runner",
            "--research-root",
            str(RESEARCH_ROOT),
            "--out-dir",
            str(out_dir),
        ],
    )

    assert main() == 0

    summary = json.loads(
        (out_dir / "qualification_summary.json").read_text(encoding="utf-8")
    )
    evaluation = json.loads(
        (out_dir / "evaluation_receipt.json").read_text(encoding="utf-8")
    )

    assert summary["schema"] == "research-eb-rc0-qualification-summary-v2"
    assert summary["case_count"] == 8
    assert summary["cal_semantic_engine_called"] is False
    assert summary["actual_upstream_contract"] == "contract-a-v2.0.0"
    assert len(summary["contract_b_results"]) == 8
    assert evaluation["missing_required_evidence_by_first_stage"] == {
        "candidate_pool": 1,
        "retention": 1,
        "admission": 1,
    }

    assert (out_dir / "runtime_receipt.json").is_file()
    for result in summary["contract_b_results"]:
        bundle_dir = out_dir / "contract_b" / result["case_id"]
        assert bundle_dir.is_dir()
        assert (bundle_dir / "SHA256SUMS").is_file()
