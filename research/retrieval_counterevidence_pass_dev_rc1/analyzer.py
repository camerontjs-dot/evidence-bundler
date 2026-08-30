from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

COUNTER_CLASSES = {
    "decisive_counterevidence",
    "decisive_contradiction",
    "decisive_refutation",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _ids(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {(str(row["source_id"]), str(row["passage_id"])) for row in rows}


def ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def analyze(
    *,
    runtime_root: Path,
    gold_path: Path,
    raw_path: Path,
) -> dict[str, Any]:
    raw = load_json(raw_path)
    apertures_payload = load_json(runtime_root / "apertures.json")
    apertures = {
        str(row["subset_id"]): {str(value) for value in row["source_ids"]}
        for row in apertures_payload["subsets"]
    }
    gold: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in load_jsonl(gold_path):
        gold[str(row["case_id"])].append(row)

    arm_totals: dict[str, dict[str, int]] = {
        arm: defaultdict(int)
        for arm in ("E0_disabled", "E1_gate_on", "E2_gate_off")
    }
    family_totals: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: {
            arm: defaultdict(int)
            for arm in ("E0_disabled", "E1_gate_on", "E2_gate_off")
        }
    )
    case_rows: list[dict[str, Any]] = []

    for raw_case in raw["cases"]:
        case_id = str(raw_case["case_id"])
        family = str(raw_case["family"])
        subset = apertures[str(raw_case["accessible_subset_id"])]
        case_gold = [
            row for row in gold[case_id] if str(row["source_id"]) in subset
        ]
        decisive_counter = _ids(
            [
                row
                for row in case_gold
                if row.get("decisive") is True
                and row.get("relevance_class") in COUNTER_CLASSES
            ]
        )
        hard_negative = _ids(
            [row for row in case_gold if row.get("relevance_class") == "hard_negative"]
        )
        supporting_ids = _ids(raw_case["supporting_semantic_k"])
        metrics: dict[str, Any] = {}

        for arm, rows in raw_case["arms"].items():
            ids = _ids(rows)
            found = decisive_counter & ids
            totals = arm_totals[arm]
            family_stats = family_totals[family][arm]
            totals["counter_total"] += len(decisive_counter)
            totals["counter_found"] += len(found)
            totals["counter_cases"] += int(bool(decisive_counter))
            totals["counter_case_hits"] += int(bool(found))
            totals["admissions"] += len(ids)
            totals["hard_negative_admissions"] += len(ids & hard_negative)
            totals["support_duplicates"] += len(ids & supporting_ids)
            totals["noncounter_family_admissions"] += (
                len(ids) if not decisive_counter else 0
            )
            family_stats["counter_total"] += len(decisive_counter)
            family_stats["counter_found"] += len(found)
            family_stats["admissions"] += len(ids)
            family_stats["hard_negative_admissions"] += len(ids & hard_negative)
            metrics[arm] = {
                "counter_total": len(decisive_counter),
                "counter_found": len(found),
                "counter_recall": ratio(len(found), len(decisive_counter)),
                "admissions": len(ids),
                "hard_negative_admissions": len(ids & hard_negative),
                "support_duplicates": len(ids & supporting_ids),
                "contradicting_roles": sum(
                    1 for row in rows if row.get("evidence_role") == "contradicting"
                ),
                "conditional_roles": sum(
                    1 for row in rows if row.get("evidence_role") == "conditional"
                ),
            }

        gate_off_ids = _ids(raw_case["arms"]["E2_gate_off"])
        gate_on_ids = _ids(raw_case["arms"]["E1_gate_on"])
        gate_rejected = gate_off_ids - gate_on_ids
        false_rejected = decisive_counter & gate_rejected
        arm_totals["E1_gate_on"]["gate_rejections"] += len(gate_rejected)
        arm_totals["E1_gate_on"]["false_counter_rejections"] += len(false_rejected)
        metrics["gate_comparison"] = {
            "gate_rejected": len(gate_rejected),
            "decisive_counterevidence_rejected": len(false_rejected),
        }
        case_rows.append(
            {
                "case_id": case_id,
                "family": family,
                "metrics": metrics,
            }
        )

    summary: dict[str, Any] = {}
    for arm, totals in arm_totals.items():
        summary[arm] = {
            "counterevidence_recall": ratio(
                totals["counter_found"], totals["counter_total"]
            ),
            "counter_case_hit_rate": ratio(
                totals["counter_case_hits"], totals["counter_cases"]
            ),
            "admissions": totals["admissions"],
            "hard_negative_admissions": totals["hard_negative_admissions"],
            "support_duplicates": totals["support_duplicates"],
            "noncounter_family_admissions": totals["noncounter_family_admissions"],
            "gate_rejections": totals.get("gate_rejections", 0),
            "false_counter_rejections": totals.get("false_counter_rejections", 0),
        }

    families: dict[str, Any] = {}
    for family, by_arm in family_totals.items():
        families[family] = {}
        for arm, totals in by_arm.items():
            families[family][arm] = {
                "counterevidence_recall": ratio(
                    totals["counter_found"], totals["counter_total"]
                ),
                "admissions": totals["admissions"],
                "hard_negative_admissions": totals["hard_negative_admissions"],
            }

    return {
        "schema_version": "1.0",
        "experiment": "retrieval-counterevidence-pass-dev-rc1",
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "summary": summary,
        "families": families,
        "case_metrics": case_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(
        runtime_root=args.runtime_root,
        gold_path=args.gold,
        raw_path=args.raw,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"summary": result["summary"], "families": result["families"]},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
