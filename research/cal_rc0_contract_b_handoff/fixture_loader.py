from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research.cal_rc0_contract_b_handoff.build_handoff import canonical_bytes

CASE_IDS = (
    "C01_DIRECT",
    "C02_COUNTER",
    "C03_POOL_MISS",
    "C04_QUALIFIER",
    "C05_JOINT",
    "C06_HARD_NEG",
    "C07_DUPLICATE",
    "C08_ADMISSION",
)


def load_cohort(fixtures_dir: Path) -> dict[str, Any]:
    cases_dir = fixtures_dir / "cases"
    cases = [
        json.loads((cases_dir / f"{case_id}.json").read_text(encoding="utf-8"))
        for case_id in CASE_IDS
    ]
    observed = tuple(str(case["case_id"]) for case in cases)
    if observed != CASE_IDS:
        raise ValueError(f"qualification case identity/order mismatch: {observed!r}")
    return {"schema": "research-eb-rc0-cohort-v1", "cases": cases}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cohort = load_cohort(args.fixtures_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(canonical_bytes(cohort))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
