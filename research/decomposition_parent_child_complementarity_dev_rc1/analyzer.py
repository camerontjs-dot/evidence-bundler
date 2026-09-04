from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.contract_a_decomposition_retrieval_sensitivity_dev_rc1.analyzer import (
    DEV_GOLD_SHA256,
    map_gold_to_paragraphs,
)

STRATEGY_ORDER = ("D1", "D2", "D3", "D4", "D5a", "D5b", "D6")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def ratio(a: int, b: int) -> float | None:
    return None if b == 0 else a / b


def _ids(result: dict[str, Any] | None) -> set[str]:
    if result is None:
        return set()
    return {str(hit["paragraph_id"]) for hit in result["hits"]}


def _role(rows: list[dict[str, Any]], term: str) -> set[str]:
    return {
        str(row["paragraph_id"])
        for row in rows
        if term in str(row.get("relevance_class", "")).lower()
        and row.get("decisive") is True
        and row.get("in_accessible_subset") is True
    }


def _evaluate(result: dict[str, Any] | None, gold_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if result is None:
        return None
    hit_ids = _ids(result)
    decisive_rows = [
        row
        for row in gold_rows
        if row.get("decisive") is True and row.get("in_accessible_subset") is True
    ]
    decisive_ids = {str(row["paragraph_id"]) for row in decisive_rows}
    qualifier_ids = _role(decisive_rows, "qualifier")
    exception_ids = _role(decisive_rows, "exception")
    counter_ids = {
        str(row["paragraph_id"])
        for row in decisive_rows
        if any(
            token in str(row.get("relevance_class", "")).lower()
            for token in ("counter", "contradict", "refut")
        )
    }
    hard_negative_ids = {
        str(row["paragraph_id"])
        for row in gold_rows
        if str(row.get("relevance_class")) == "hard_negative"
        and row.get("in_accessible_subset") is True
    }
    joint_groups: dict[str, set[str]] = defaultdict(set)
    for row in decisive_rows:
        if row.get("joint_group_id"):
            joint_groups[str(row["joint_group_id"])].add(str(row["paragraph_id"]))
    joint_complete = sum(1 for members in joint_groups.values() if members <= hit_ids)
    return {
        "decisive_total": len(decisive_ids),
        "decisive_found": len(decisive_ids & hit_ids),
        "decisive_recall": ratio(len(decisive_ids & hit_ids), len(decisive_ids)),
        "qualifier_total": len(qualifier_ids),
        "qualifier_found": len(qualifier_ids & hit_ids),
        "qualifier_recall": ratio(len(qualifier_ids & hit_ids), len(qualifier_ids)),
        "exception_total": len(exception_ids),
        "exception_found": len(exception_ids & hit_ids),
        "exception_recall": ratio(len(exception_ids & hit_ids), len(exception_ids)),
        "counterevidence_total": len(counter_ids),
        "counterevidence_found": len(counter_ids & hit_ids),
        "counterevidence_recall": (
            "NOT_ESTIMABLE_IN_COHORT"
            if not counter_ids
            else ratio(len(counter_ids & hit_ids), len(counter_ids))
        ),
        "joint_group_total": len(joint_groups),
        "joint_group_complete": joint_complete,
        "joint_group_coverage": ratio(joint_complete, len(joint_groups)),
        "hard_negative_found": len(hard_negative_ids & hit_ids),
        "hard_negative_burden": ratio(len(hard_negative_ids & hit_ids), len(hit_ids)),
        "unique_candidates": int(result["unique_candidates"]),
        "duplicate_burden": int(result["duplicate_burden"]),
        "source_diversity": int(result["source_diversity"]),
        "requested_candidate_positions": int(result["requested_candidate_positions"]),
        "returned_before_dedupe": int(result["returned_before_dedupe"]),
    }


def _marginal(
    *, r0: dict[str, Any], r1: dict[str, Any], r2: dict[str, Any], gold_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    decisive = {
        str(row["paragraph_id"])
        for row in gold_rows
        if row.get("decisive") is True and row.get("in_accessible_subset") is True
    }
    hard = {
        str(row["paragraph_id"])
        for row in gold_rows
        if str(row.get("relevance_class")) == "hard_negative"
        and row.get("in_accessible_subset") is True
    }
    r0_ids, r1_ids, r2_ids = _ids(r0), _ids(r1), _ids(r2)
    return {
        "r2_decisive_only_over_r1": sorted((r2_ids - r1_ids) & decisive),
        "r2_decisive_only_over_r0": sorted((r2_ids - r0_ids) & decisive),
        "r2_new_hard_negatives_over_r1": sorted((r2_ids - r1_ids) & hard),
        "r2_new_physical_passages_over_r1": sorted(r2_ids - r1_ids),
        "r2_new_physical_passages_over_r0": sorted(r2_ids - r0_ids),
        "r2_root_only_passages": list(r2["root_only_passage_ids"]),
        "r2_child_only_passages": list(r2["child_only_passage_ids"]),
        "r2_both_passages": list(r2["both_passage_ids"]),
    }


def analyze(
    *,
    benchmark_root: Path,
    raw_path: Path,
    gold_path: Path,
    expected_raw_sha256: str,
    output: Path,
) -> dict[str, Any]:
    actual_raw_sha = sha256_bytes(raw_path.read_bytes())
    if actual_raw_sha != expected_raw_sha256:
        raise RuntimeError("raw retrieval changed before posthoc analysis")
    if sha256_bytes(gold_path.read_bytes()) != DEV_GOLD_SHA256:
        raise RuntimeError("frozen dev relevance hash mismatch")

    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    gold_by_case = map_gold_to_paragraphs(
        benchmark_root=benchmark_root,
        gold_rows=load_jsonl(gold_path),
    )
    cases = load_jsonl(benchmark_root / "cases" / "dev_cases.jsonl")
    a0_by_claim = {
        str(row["original_claim_id"]): row
        for row in cases
        if str(row["variant_id"]) == "A0"
    }

    per_case: list[dict[str, Any]] = []
    aggregate: dict[str, Any] = {
        retriever: {
            budget: {
                strategy: {
                    "declared_cases": 0,
                    "r2_decisive_gain_over_r1_cases": 0,
                    "r2_decisive_gain_over_r0_cases": 0,
                    "root_adds_hard_negative_without_decisive_gain_cases": 0,
                    "decomposition_hurts_vs_root_cases": 0,
                    "r2_r3_physical_identity_failures": 0,
                    "r2_relationships_removed_by_flattening": 0,
                }
                for strategy in STRATEGY_ORDER
            }
            for budget in ("equal_total", "equal_per_query")
        }
        for retriever in ("bm25", "semantic")
    }

    for case in raw["cases"]:
        claim_id = str(case["original_claim_id"])
        a0 = a0_by_claim[claim_id]
        gold_rows = gold_by_case[str(a0["case_id"])]
        case_out: dict[str, Any] = {
            "original_claim_id": claim_id,
            "challenge_family": a0.get("challenge_family"),
            "accessible_subset_id": a0["accessible_subset_id"],
            "strategies": {},
        }
        for strategy, strategy_data in case["strategies"].items():
            strategy_out: dict[str, Any] = {
                "decomposition_state": strategy_data["decomposition_state"],
                "child_count": strategy_data["child_count"],
                "retrievers": {},
            }
            for retriever, retriever_data in strategy_data["retrievers"].items():
                retriever_out: dict[str, Any] = {}
                for budget, arms in retriever_data.items():
                    r0_eval = _evaluate(arms["R0"], gold_rows)
                    r1_eval = _evaluate(arms["R1"], gold_rows)
                    r2_eval = _evaluate(arms["R2"], gold_rows)
                    row_out: dict[str, Any] = {
                        "R0": r0_eval,
                        "R1": r1_eval,
                        "R2": r2_eval,
                        "R3": _evaluate(arms["R3"], gold_rows),
                        "marginal": None,
                        "flattening_control": None,
                    }
                    if arms["R2"] is not None:
                        marginal = _marginal(
                            r0=arms["R0"], r1=arms["R1"], r2=arms["R2"], gold_rows=gold_rows
                        )
                        same_physical = _ids(arms["R2"]) == _ids(arms["R3"])
                        relationship_count = sum(
                            len(hit["relationships"]) for hit in arms["R2"]["hits"]
                        )
                        row_out["marginal"] = marginal
                        row_out["flattening_control"] = {
                            "r2_r3_identical_physical_passage_set": same_physical,
                            "r2_relationship_count": relationship_count,
                            "r3_relationship_count": 0,
                            "attribution_information_removed": relationship_count > 0,
                        }
                        agg = aggregate[retriever][budget][strategy]
                        agg["declared_cases"] += 1
                        gain_r1 = bool(marginal["r2_decisive_only_over_r1"])
                        gain_r0 = bool(marginal["r2_decisive_only_over_r0"])
                        if gain_r1:
                            agg["r2_decisive_gain_over_r1_cases"] += 1
                        if gain_r0:
                            agg["r2_decisive_gain_over_r0_cases"] += 1
                        if marginal["r2_new_hard_negatives_over_r1"] and not gain_r1:
                            agg["root_adds_hard_negative_without_decisive_gain_cases"] += 1
                        if (
                            r0_eval is not None
                            and r1_eval is not None
                            and r0_eval["decisive_recall"] is not None
                            and r1_eval["decisive_recall"] is not None
                            and float(r1_eval["decisive_recall"]) < float(r0_eval["decisive_recall"])
                        ):
                            agg["decomposition_hurts_vs_root_cases"] += 1
                        if not same_physical:
                            agg["r2_r3_physical_identity_failures"] += 1
                        agg["r2_relationships_removed_by_flattening"] += relationship_count
                    retriever_out[budget] = row_out
                strategy_out["retrievers"][retriever] = retriever_out
            strategy_out["retrievers"] = strategy_out["retrievers"]
            case_out["strategies"][strategy] = strategy_out
        per_case.append(case_out)

    result = {
        "schema_version": "1.0",
        "experiment": raw["experiment"],
        "apparatus_sha": raw["apparatus_sha"],
        "raw_sha256_verified": actual_raw_sha,
        "gold_sha256": DEV_GOLD_SHA256,
        "case_count": len(per_case),
        "aggregate": aggregate,
        "per_case": per_case,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "case_count": len(per_case),
        "raw_sha256_verified": actual_raw_sha,
        "analysis_sha256": sha256_bytes(output.read_bytes()),
        "aggregate": aggregate,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--expected-raw-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = analyze(
        benchmark_root=args.benchmark_root,
        raw_path=args.raw,
        gold_path=args.gold,
        expected_raw_sha256=args.expected_raw_sha256,
        output=args.output,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
