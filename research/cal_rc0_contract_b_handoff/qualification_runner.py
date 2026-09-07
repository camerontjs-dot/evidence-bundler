from __future__ import annotations

import argparse
import json
from pathlib import Path

from .build_handoff import build_runtime_receipt, canonical_bytes, sha256_bytes
from .evaluate_receipt import evaluate
from .fixture_loader import load_cohort
from .qualified_handoff import build_all_contract_b_qualified


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--research-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    root = args.research_root
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    cohort = load_cohort(root / "fixtures")
    admission = json.loads((root / "fixtures" / "admission.json").read_text(encoding="utf-8"))
    compatibility_carrier = json.loads(
        (root / "fixtures" / "contract_b_compatibility_carrier.json").read_text(
            encoding="utf-8"
        )
    )
    evaluator_gold = json.loads(
        (root / "fixtures" / "evaluator_gold.json").read_text(encoding="utf-8")
    )
    profile = json.loads((root / "RESEARCH_EB_PROFILE.json").read_text(encoding="utf-8"))

    receipt = build_runtime_receipt(cohort=cohort, admission=admission, profile=profile)
    receipt_path = out_dir / "runtime_receipt.json"
    receipt_path.write_bytes(canonical_bytes(receipt))
    contract_b_results = build_all_contract_b_qualified(
        cohort=cohort,
        receipt=receipt,
        profile=profile,
        compatibility_carrier=compatibility_carrier,
        out_dir=out_dir,
    )
    evaluation = evaluate(runtime=receipt, gold=evaluator_gold)
    evaluation_path = out_dir / "evaluation_receipt.json"
    evaluation_path.write_bytes(canonical_bytes(evaluation))

    summary = {
        "schema": "research-eb-rc0-qualification-summary-v2",
        "case_count": len(receipt["cases"]),
        "runtime_receipt_sha256": sha256_bytes(receipt_path.read_bytes()),
        "evaluation_receipt_sha256": sha256_bytes(evaluation_path.read_bytes()),
        "contract_b_results": contract_b_results,
        "compatibility_carrier_schema": compatibility_carrier["schema"],
        "actual_upstream_contract": compatibility_carrier["authority"][
            "actual_upstream_contract"
        ],
        "cal_semantic_engine_called": False,
    }
    (out_dir / "qualification_summary.json").write_bytes(canonical_bytes(summary))
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
