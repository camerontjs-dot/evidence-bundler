from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

COUNTER_CLASSES = {
    "decisive_counterevidence",
    "decisive_contradiction",
    "decisive_refutation",
}
QUALIFIER_CLASSES = {
    "decisive_qualifier",
    "decisive_exception",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def _ids(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {(str(row["source_id"]), str(row["passage_id"])) for row in rows}


def _pool_ids(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {(str(row["source_id"]), str(row["passage_id"])) for row in rows}


def _union_rows(
    lexical: list[dict[str, Any]],
    semantic: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, Any]] = []
    for row in [*lexical, *semantic]:
        identity = (str(row["source_id"]), str(row["passage_id"]))
        if identity in seen:
            continue
        seen.add(identity)
        output.append(row)
    return output


def analyze_case(
    *,
    case: dict[str, Any],
    gold_rows: list[dict[str, Any]],
    subset_sources: set[str],
    pool_record: dict[str, Any],
) -> dict[str, Any]:
    accessible_decisive = [
        row
        for row in gold_rows
        if row.get("decisive") is True and str(row["source_id"]) in subset_sources
    ]
    decisive_ids = _ids(accessible_decisive)
    counter_ids = _ids(
        [row for row in accessible_decisive if row.get("relevance_class") in COUNTER_CLASSES]
    )
    qualifier_ids = _ids(
        [row for row in accessible_decisive if row.get("relevance_class") in QUALIFIER_CLASSES]
    )
    hard_ids = _ids(
        [
            row
            for row in gold_rows
            if row.get("relevance_class") == "hard_negative"
            and str(row["source_id"]) in subset_sources
        ]
    )
    groups: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in accessible_decisive:
        group_id = row.get("joint_group_id")
        if group_id:
            groups[str(group_id)].add((str(row["source_id"]), str(row["passage_id"])))

    metrics: dict[str, Any] = {}
    for pool_name, pool_rows in (
        ("lexical", pool_record["lexical"]),
        ("semantic", pool_record["semantic"]),
        ("union", _union_rows(pool_record["lexical"], pool_record["semantic"])),
    ):
        pool_ids = _pool_ids(pool_rows)
        complete_groups = sum(
            1 for members in groups.values() if members and members <= pool_ids
        )
        metrics[pool_name] = {
            "requested_per_retriever": int(pool_record["requested_per_retriever"]),
            "actual_pool_size": len(pool_ids),
            "applicable_decisive": len(decisive_ids),
            "found_decisive": len(decisive_ids & pool_ids),
            "case_hit": None if not decisive_ids else int(bool(decisive_ids & pool_ids)),
            "counter_total": len(counter_ids),
            "counter_found": len(counter_ids & pool_ids),
            "qualifier_total": len(qualifier_ids),
            "qualifier_found": len(qualifier_ids & pool_ids),
            "joint_groups": len(groups),
            "complete_joint_groups": complete_groups,
            "hard_negative_count": len(hard_ids & pool_ids),
        }
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "metrics": metrics,
    }


def aggregate(case_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_pool: dict[str, Any] = {}
    for pool_name in ("lexical", "semantic", "union"):
        applicable = sum(row["metrics"][pool_name]["applicable_decisive"] for row in case_rows)
        found = sum(row["metrics"][pool_name]["found_decisive"] for row in case_rows)
        hit_den = sum(
            1 for row in case_rows if row["metrics"][pool_name]["case_hit"] is not None
        )
        hit_num = sum(
            int(row["metrics"][pool_name]["case_hit"] or 0)
            for row in case_rows
            if row["metrics"][pool_name]["case_hit"] is not None
        )
        counter_total = sum(row["metrics"][pool_name]["counter_total"] for row in case_rows)
        counter_found = sum(row["metrics"][pool_name]["counter_found"] for row in case_rows)
        qualifier_total = sum(
            row["metrics"][pool_name]["qualifier_total"] for row in case_rows
        )
        qualifier_found = sum(
            row["metrics"][pool_name]["qualifier_found"] for row in case_rows
        )
        groups = sum(row["metrics"][pool_name]["joint_groups"] for row in case_rows)
        complete_groups = sum(
            row["metrics"][pool_name]["complete_joint_groups"] for row in case_rows
        )
        by_pool[pool_name] = {
            "case_hit_rate": ratio(hit_num, hit_den),
            "decisive_pool_recall": ratio(found, applicable),
            "counterevidence_pool_recall": ratio(counter_found, counter_total),
            "qualifier_exception_pool_recall": ratio(qualifier_found, qualifier_total),
            "complete_joint_group_pool_coverage": ratio(complete_groups, groups),
            "actual_candidate_count": sum(
                row["metrics"][pool_name]["actual_pool_size"] for row in case_rows
            ),
            "hard_negative_count": sum(
                row["metrics"][pool_name]["hard_negative_count"] for row in case_rows
            ),
        }
    families: dict[str, Any] = {}
    family_names = sorted({str(row["family"]) for row in case_rows})
    for family in family_names:
        family_rows = [row for row in case_rows if row["family"] == family]
        families[family] = aggregate_without_families(family_rows)
    return {
        "pools": by_pool,
        "families": families,
    }


def aggregate_without_families(case_rows: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for pool_name in ("lexical", "semantic", "union"):
        applicable = sum(row["metrics"][pool_name]["applicable_decisive"] for row in case_rows)
        found = sum(row["metrics"][pool_name]["found_decisive"] for row in case_rows)
        hit_rows = [
            row["metrics"][pool_name]["case_hit"]
            for row in case_rows
            if row["metrics"][pool_name]["case_hit"] is not None
        ]
        output[pool_name] = {
            "case_hit_rate": ratio(sum(int(value or 0) for value in hit_rows), len(hit_rows)),
            "decisive_pool_recall": ratio(found, applicable),
        }
    return output


def analyze(
    *,
    runtime_root: Path,
    gold_path: Path,
    candidate_path: Path,
) -> dict[str, Any]:
    candidate_record = load_json(candidate_path)
    cases = {str(row["case_id"]): row for row in load_jsonl(runtime_root / "dev_cases.jsonl")}
    subsets_payload = load_json(runtime_root / "apertures.json")
    subsets = {
        str(row["subset_id"]): {str(value) for value in row["source_ids"]}
        for row in subsets_payload["subsets"]
    }
    gold: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in load_jsonl(gold_path):
        gold[str(row["case_id"])].append(row)

    by_multiplier: dict[str, Any] = {}
    for multiplier in candidate_record["multipliers"]:
        case_rows = []
        for pool_case in candidate_record["cases"]:
            case_id = str(pool_case["case_id"])
            case = cases[case_id]
            case_rows.append(
                analyze_case(
                    case=case,
                    gold_rows=gold[case_id],
                    subset_sources=subsets[str(case["accessible_subset_id"])],
                    pool_record=pool_case["multipliers"][str(multiplier)],
                )
            )
        by_multiplier[str(multiplier)] = {
            "aggregate": aggregate(case_rows),
            "case_metrics": case_rows,
        }

    return {
        "schema_version": "1.0",
        "experiment": "retrieval-candidate-pool-aperture-dev-rc1",
        "candidate_record_sha256": __import__("hashlib").sha256(
            candidate_path.read_bytes()
        ).hexdigest(),
        "multipliers": by_multiplier,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(
        runtime_root=args.runtime_root,
        gold_path=args.gold,
        candidate_path=args.candidates,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["multipliers"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
