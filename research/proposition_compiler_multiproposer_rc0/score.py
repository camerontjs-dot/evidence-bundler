from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

SYSTEMS = ("S1_P1", "S2_P2", "S3_P3", "S4_POOL")


def norm_text(text: str) -> str:
    return " ".join(text.lower().strip().rstrip(".").split())


def child_set(children: list[str]) -> tuple[str, ...]:
    return tuple(sorted(norm_text(x) for x in children))


def candidate_safe(eval_row: dict, gold: dict) -> bool:
    allowed = {
        tuple(sorted(norm_text(x) for x in option))
        for option in gold.get("allowed_child_sets", [])
    }
    return child_set(eval_row["children"]) in allowed


def score_system(raw_row: dict, gold: dict) -> dict:
    expected = gold["expected"]
    if raw_row["state"] != "RESOLVED":
        return {
            "state": raw_row["state"],
            "safe_resolution": False,
            "unsafe_resolution": False,
            "correct_fail_closed": expected == "FAIL_CLOSED",
        }

    surviving = [
        x
        for x in raw_row["evaluations"]
        if x.get("semantic_cluster") == raw_row["semantic_cluster"]
    ]
    safe_members = [x for x in surviving if candidate_safe(x, gold)]
    unsafe = expected == "FAIL_CLOSED" or not safe_members
    return {
        "state": "RESOLVED",
        "safe_resolution": expected == "RESOLVED" and bool(safe_members) and not unsafe,
        "unsafe_resolution": unsafe,
        "correct_fail_closed": False,
        "safe_member_ids": sorted(x["candidate_id"] for x in safe_members),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True)
    p.add_argument("--gold", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()

    raw = {
        x["root_id"]: x
        for x in map(json.loads, Path(a.raw).read_text(encoding="utf-8").splitlines())
        if x
    }
    gold = {
        x["root_id"]: x
        for x in map(json.loads, Path(a.gold).read_text(encoding="utf-8").splitlines())
        if x
    }

    summary = {
        s: {
            "safe_resolved": 0,
            "unsafe_resolved": 0,
            "correct_fail_closed": 0,
            "by_family": defaultdict(int),
        }
        for s in SYSTEMS
    }
    details = []
    for root_id, g in gold.items():
        r = raw[root_id]
        row = {
            "root_id": root_id,
            "family": g["family"],
            "expected": g["expected"],
            "systems": {},
        }
        for s in SYSTEMS:
            sc = score_system(r["systems"][s], g)
            row["systems"][s] = sc
            if sc["safe_resolution"]:
                summary[s]["safe_resolved"] += 1
                summary[s]["by_family"][g["family"]] += 1
            if sc["unsafe_resolution"]:
                summary[s]["unsafe_resolved"] += 1
            if sc["correct_fail_closed"]:
                summary[s]["correct_fail_closed"] += 1
        details.append(row)

    clean_summary = {}
    for s, v in summary.items():
        clean_summary[s] = {
            "safe_resolved": v["safe_resolved"],
            "unsafe_resolved": v["unsafe_resolved"],
            "correct_fail_closed": v["correct_fail_closed"],
            "by_family": dict(sorted(v["by_family"].items())),
        }

    best_single = max(clean_summary[s]["safe_resolved"] for s in SYSTEMS[:3])
    pool = clean_summary["S4_POOL"]["safe_resolved"]
    gain = pool - best_single
    families = sorted({g["family"] for g in gold.values()})
    family_gains = {}
    for fam in families:
        best = max(clean_summary[s]["by_family"].get(fam, 0) for s in SYSTEMS[:3])
        pooled = clean_summary["S4_POOL"]["by_family"].get(fam, 0)
        family_gains[fam] = pooled - best
    gain_families = [family for family, value in family_gains.items() if value > 0]

    result = {
        "summary": clean_summary,
        "best_single_safe_resolved": best_single,
        "pooled_safe_resolved": pool,
        "pooled_gain": gain,
        "family_gains": family_gains,
        "gain_family_count": len(gain_families),
        "gain_families": gain_families,
        "details": details,
    }
    text = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    Path(a.output).write_text(text, encoding="utf-8")
    print(hashlib.sha256(text.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
