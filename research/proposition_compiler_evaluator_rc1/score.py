#!/usr/bin/env python3
"""Post-freeze scorer. This is the only RC1 runtime utility that reads gold."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def by_case(rows: list[dict]) -> dict[str, dict]:
    return {r["case_id"]: r for r in rows}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--gold", required=True)
    p.add_argument("--raw-dir", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    gold = load_jsonl(Path(args.gold))
    rawdir = Path(args.raw_dir)
    systems = {p.stem: by_case(load_jsonl(p)) for p in sorted(rawdir.glob("*.jsonl"))}
    results: dict[str, dict] = {}
    target_falsifiers: list[dict] = []

    for system, rows in systems.items():
        exact = 0
        unsafe_accept = 0
        ambiguity_accept = 0
        family_errors: dict[str, int] = defaultdict(int)
        for g in gold:
            r = rows[g["case_id"]]
            actual = r["disposition"]
            expected = g["expected_disposition"]
            if actual == expected:
                exact += 1
            else:
                family_errors[g["family"]] += 1
            if g.get("promotion_critical") and expected == "REJECT_UNSAFE" and actual == "ACCEPTABLE_WITHIN_PROFILE":
                unsafe_accept += 1
                if system == "target_raw":
                    target_falsifiers.append({"case_id": g["case_id"], "type": "UNSAFE_ACCEPTANCE", "family": g["family"]})
            if g.get("promotion_critical") and expected == "INDETERMINATE" and actual == "ACCEPTABLE_WITHIN_PROFILE":
                ambiguity_accept += 1
                if system == "target_raw":
                    target_falsifiers.append({"case_id": g["case_id"], "type": "AMBIGUITY_FORCED_TO_ACCEPTANCE", "family": g["family"]})
        results[system] = {
            "exact": exact,
            "total": len(gold),
            "unsafe_acceptances": unsafe_accept,
            "ambiguity_acceptances": ambiguity_accept,
            "family_errors": dict(sorted(family_errors.items())),
        }

    results["C5_GOLD_ORACLE"] = {"exact": len(gold), "total": len(gold), "unsafe_acceptances": 0, "ambiguity_acceptances": 0}

    disposition = "FALSIFIED" if target_falsifiers else "UNRESOLVED_PENDING_OTHER_GATES"
    report = {"disposition_from_semantic_falsifiers": disposition, "target_falsifiers": target_falsifiers, "systems": results}
    text = json.dumps(report, sort_keys=True, indent=2) + "\n"
    Path(args.output).write_text(text, encoding="utf-8")
    print(hashlib.sha256(text.encode()).hexdigest())


if __name__ == "__main__":
    main()
