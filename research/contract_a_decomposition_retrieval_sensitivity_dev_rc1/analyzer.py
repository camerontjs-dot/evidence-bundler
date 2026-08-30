from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

DEV_GOLD_SHA256 = "da5b06d78060897f85dc78a8ff45c9622c697a10fe43942ea74a688115c7fac3"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def paragraph_rows(benchmark_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for content_path in sorted((benchmark_root / "sources").glob("*/content.txt")):
        source_id = content_path.parent.name
        text = content_path.read_text(encoding="utf-8")
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        for index, paragraph in enumerate(paragraphs):
            rows.append(
                {
                    "source_id": source_id,
                    "paragraph_index": index,
                    "paragraph_id": f"{source_id}:paragraph:{index:03d}",
                    "text": paragraph,
                }
            )
    return rows


def map_gold_to_paragraphs(
    *,
    benchmark_root: Path,
    gold_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    paragraphs_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in paragraph_rows(benchmark_root):
        paragraphs_by_source[str(row["source_id"])].append(row)

    mapped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for gold in gold_rows:
        source_id = str(gold["source_id"])
        span = str(gold["span_text"])
        matches = [
            row
            for row in paragraphs_by_source[source_id]
            if span in str(row["text"])
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"gold span mapping must be unique: {gold['annotation_id']} -> {len(matches)}"
            )
        enriched = dict(gold)
        enriched["paragraph_id"] = matches[0]["paragraph_id"]
        mapped[str(gold["case_id"])].append(enriched)
    return mapped


def ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def _hit_ids(result: dict[str, Any]) -> set[str]:
    return {str(row["paragraph_id"]) for row in result["hits"]}


def _decisive_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("decisive") is True and row.get("in_accessible_subset") is True
    ]


def _role_subset(rows: list[dict[str, Any]], patterns: tuple[str, ...]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if any(pattern in str(row.get("relevance_class", "")).lower() for pattern in patterns)
    ]


def _first_decisive_rank(result: dict[str, Any], decisive_ids: set[str]) -> int | None:
    for rank, hit in enumerate(result["hits"], start=1):
        if str(hit["paragraph_id"]) in decisive_ids:
            return rank
    return None


def _child_query_coverage(result: dict[str, Any], decisive_ids: set[str]) -> dict[str, Any]:
    query_ids: set[str] = set()
    queries_with_decisive: set[str] = set()
    for hit in result["hits"]:
        for query_hit in hit["query_hits"]:
            query_id = str(query_hit["query_id"])
            query_ids.add(query_id)
            if str(hit["paragraph_id"]) in decisive_ids:
                queries_with_decisive.add(query_id)
    return {
        "child_query_count": len(query_ids),
        "child_queries_with_decisive_hit": len(queries_with_decisive),
        "all_child_queries_have_decisive_hit": bool(query_ids)
        and query_ids == queries_with_decisive,
    }


def evaluate_result(
    result: dict[str, Any],
    gold_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    decisive = _decisive_rows(gold_rows)
    decisive_ids = {str(row["paragraph_id"]) for row in decisive}
    decisive_sources = {str(row["source_id"]) for row in decisive}
    hit_ids = _hit_ids(result)
    hit_sources = {
        str(row["source_id"])
        for row in result["hits"]
        if str(row["paragraph_id"]) in hit_ids
    }

    counter = _role_subset(decisive, ("counter", "contradict", "refut"))
    qualifier = _role_subset(decisive, ("qualifier", "exception", "conditional"))
    counter_ids = {str(row["paragraph_id"]) for row in counter}
    qualifier_ids = {str(row["paragraph_id"]) for row in qualifier}

    joint_groups: dict[str, set[str]] = defaultdict(set)
    for row in decisive:
        group_id = row.get("joint_group_id")
        if group_id:
            joint_groups[str(group_id)].add(str(row["paragraph_id"]))
    complete_groups = sum(
        1 for members in joint_groups.values() if members and members <= hit_ids
    )

    child_coverage = _child_query_coverage(result, decisive_ids)
    return {
        "decisive_total": len(decisive_ids),
        "decisive_found": len(decisive_ids & hit_ids),
        "decisive_recall": ratio(len(decisive_ids & hit_ids), len(decisive_ids)),
        "decisive_source_total": len(decisive_sources),
        "decisive_source_found": len(decisive_sources & hit_sources),
        "decisive_source_recall": ratio(
            len(decisive_sources & hit_sources),
            len(decisive_sources),
        ),
        "counter_total": len(counter_ids),
        "counter_found": len(counter_ids & hit_ids),
        "counter_recall": ratio(len(counter_ids & hit_ids), len(counter_ids)),
        "qualifier_total": len(qualifier_ids),
        "qualifier_found": len(qualifier_ids & hit_ids),
        "qualifier_recall": ratio(len(qualifier_ids & hit_ids), len(qualifier_ids)),
        "joint_group_total": len(joint_groups),
        "joint_group_complete": complete_groups,
        "joint_group_coverage": ratio(complete_groups, len(joint_groups)),
        "case_hit": None if not decisive_ids else bool(decisive_ids & hit_ids),
        "first_decisive_rank": _first_decisive_rank(result, decisive_ids),
        "requested_candidate_positions": result["requested_candidate_positions"],
        "returned_before_dedupe": result["returned_before_dedupe"],
        "unique_candidates": result["unique_candidates"],
        "duplicate_burden": result["duplicate_burden"],
        "no_hit_queries": result["no_hit_queries"],
        **child_coverage,
    }


def set_comparison(
    composite: dict[str, Any],
    decomposed: dict[str, Any],
) -> dict[str, Any]:
    composite_ids = _hit_ids(composite)
    decomposed_ids = _hit_ids(decomposed)
    union = composite_ids | decomposed_ids
    intersection = composite_ids & decomposed_ids
    return {
        "composite_unique_count": len(composite_ids - decomposed_ids),
        "decomposed_unique_count": len(decomposed_ids - composite_ids),
        "intersection_count": len(intersection),
        "jaccard": ratio(len(intersection), len(union)),
        "composite_only_ids": sorted(composite_ids - decomposed_ids),
        "decomposed_only_ids": sorted(decomposed_ids - composite_ids),
    }


def sign_flip_pvalue(deltas: list[float]) -> float | None:
    nonzero = [value for value in deltas if not math.isclose(value, 0.0, abs_tol=1e-12)]
    if not nonzero:
        return None
    observed = abs(sum(nonzero) / len(nonzero))
    extreme = 0
    total = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(nonzero)):
        signed_sum = sum(
            sign * value
            for sign, value in zip(signs, nonzero, strict=True)
        )
        permuted = abs(signed_sum / len(nonzero))
        total += 1
        if permuted >= observed - 1e-12:
            extreme += 1
    return extreme / total


def summarize_paired(rows: list[dict[str, Any]]) -> dict[str, Any]:
    deltas = [
        float(row["decomposed_recall"]) - float(row["composite_recall"])
        for row in rows
        if row["decomposed_recall"] is not None and row["composite_recall"] is not None
    ]
    return {
        "pair_count": len(deltas),
        "improved": sum(value > 1e-12 for value in deltas),
        "worsened": sum(value < -1e-12 for value in deltas),
        "tied": sum(abs(value) <= 1e-12 for value in deltas),
        "mean_decisive_recall_delta": (
            sum(deltas) / len(deltas) if deltas else None
        ),
        "median_decisive_recall_delta": (
            sorted(deltas)[len(deltas) // 2]
            if deltas
            else None
        ),
        "exact_sign_flip_pvalue_descriptive": sign_flip_pvalue(deltas),
    }


def analyze(
    *,
    benchmark_root: Path,
    raw_path: Path,
    gold_path: Path,
) -> dict[str, Any]:
    if sha256_bytes(gold_path.read_bytes()) != DEV_GOLD_SHA256:
        raise RuntimeError("frozen dev relevance hash mismatch")

    raw = load_json(raw_path)
    gold_by_case = map_gold_to_paragraphs(
        benchmark_root=benchmark_root,
        gold_rows=load_jsonl(gold_path),
    )

    case_id_by_key = {
        (str(row["original_claim_id"]), str(row["variant_id"])): str(row["case_id"])
        for row in load_jsonl(benchmark_root / "cases" / "dev_cases.jsonl")
    }

    per_claim: list[dict[str, Any]] = []
    paired: dict[str, dict[str, list[dict[str, Any]]]] = {
        retriever: {
            "A1_equal_total": [],
            "A2_equal_total": [],
            "A1_per_query": [],
            "A2_per_query": [],
            "A3_equal_total": [],
            "A4_equal_total": [],
        }
        for retriever in ("bm25", "semantic")
    }

    for claim in raw["claims"]:
        original_claim_id = str(claim["original_claim_id"])
        claim_out: dict[str, Any] = {
            "original_claim_id": original_claim_id,
            "accessible_subset_id": claim["accessible_subset_id"],
            "k": claim["k"],
            "retrievers": {},
        }
        for retriever_name, retriever_data in claim["retrievers"].items():
            a0_case_id = case_id_by_key[(original_claim_id, "A0")]
            composite_eval = evaluate_result(
                retriever_data["composite"],
                gold_by_case[a0_case_id],
            )
            variants_out: dict[str, Any] = {}
            for variant_id, variant in retriever_data["variants"].items():
                case_id = case_id_by_key[(original_claim_id, variant_id)]
                total_eval = evaluate_result(
                    variant["equal_total_budget"],
                    gold_by_case[case_id],
                )
                per_query_eval = evaluate_result(
                    variant["equal_per_query_budget"],
                    gold_by_case[case_id],
                )
                variants_out[variant_id] = {
                    "preserves_parent_meaning": variant["preserves_parent_meaning"],
                    "over_decomposition": variant["over_decomposition"],
                    "equal_total_budget": total_eval,
                    "equal_per_query_budget": per_query_eval,
                    "equal_total_vs_composite_set": set_comparison(
                        retriever_data["composite"],
                        variant["equal_total_budget"],
                    ),
                    "per_query_vs_composite_set": set_comparison(
                        retriever_data["composite"],
                        variant["equal_per_query_budget"],
                    ),
                    "ownership_equivalence": variant["ownership_equivalence"],
                }
                for label, evaluation in (
                    (f"{variant_id}_equal_total", total_eval),
                    (f"{variant_id}_per_query", per_query_eval),
                ):
                    if label in paired[retriever_name]:
                        paired[retriever_name][label].append(
                            {
                                "original_claim_id": original_claim_id,
                                "composite_recall": composite_eval["decisive_recall"],
                                "decomposed_recall": evaluation["decisive_recall"],
                            }
                        )
            claim_out["retrievers"][retriever_name] = {
                "composite": composite_eval,
                "variants": variants_out,
            }
        per_claim.append(claim_out)

    paired_summary = {
        retriever: {
            comparison: summarize_paired(rows)
            for comparison, rows in comparisons.items()
        }
        for retriever, comparisons in paired.items()
    }

    ownership_invariants = [
        variant["ownership_equivalence"]["identical"]
        for claim in raw["claims"]
        for retriever in claim["retrievers"].values()
        for variant_id, variant in retriever["variants"].items()
        if variant_id in {"A1", "A2"}
    ]

    return {
        "schema_version": "1.0",
        "experiment": "contract-a-decomposition-retrieval-sensitivity-dev-rc1",
        "raw_sha256": sha256_bytes(raw_path.read_bytes()),
        "gold_sha256": DEV_GOLD_SHA256,
        "base_claim_count": len(per_claim),
        "ownership_equivalence": {
            "checks": len(ownership_invariants),
            "all_identical": all(ownership_invariants),
        },
        "paired_summary": paired_summary,
        "per_claim": per_claim,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(
        benchmark_root=args.benchmark_root,
        raw_path=args.raw,
        gold_path=args.gold,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ownership_equivalence": result["ownership_equivalence"],
                "paired_summary": result["paired_summary"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
