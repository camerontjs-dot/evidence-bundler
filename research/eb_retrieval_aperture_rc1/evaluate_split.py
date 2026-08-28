from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

EXPECTED_EVALUATOR_SHA = "acfa232c0a6d1708f249b71606cbdc96755bc4d9"
EXPECTED_BENCHMARK_SHA = "22b227ec2c34a085efc79267bc007ff78607aeed"


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TypeError(f"{path}: JSONL row must be object")
            rows.append(value)
    return rows


def mean(values: Iterable[float]) -> float | None:
    values = list(values)
    return None if not values else sum(values) / len(values)


def ratio(num: int, den: int) -> float | None:
    return None if den == 0 else num / den


def configure_frozen_evaluator(evaluator_root: Path):
    sys.path.insert(0, str(evaluator_root))
    import corrected_runner as corrected  # type: ignore
    import evaluator as core  # type: ignore

    corrected.install_correction()
    return core, corrected


def evaluate_split(
    *,
    core: Any,
    benchmark_root: Path,
    split: str,
    results: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    core.verify_freeze_receipt(benchmark_root)
    cases_all = core.load_cases(benchmark_root)
    gold_all = core.load_gold(benchmark_root)
    core.validate_gold_interpretation(cases_all, gold_all)
    subsets = core.load_subsets(benchmark_root)
    passage_index, _ = core.load_passages(benchmark_root)
    anchor_reverse = core.load_anchor_reverse_mapping(benchmark_root)

    case_ids = sorted(
        case_id for case_id, case in cases_all.items() if case.get("split") == split
    )
    result_by_case = {str(row.get("case_id")): row for row in results}
    if set(result_by_case) != set(case_ids):
        raise core.EvaluatorError(
            f"{split} result case set mismatch "
            f"missing={sorted(set(case_ids) - set(result_by_case))} "
            f"extra={sorted(set(result_by_case) - set(case_ids))}"
        )

    case_metrics = [
        core.evaluate_case(
            cases_all[case_id],
            gold_all[case_id],
            result_by_case[case_id],
            subsets,
            passage_index,
            anchor_reverse,
        )
        for case_id in case_ids
    ]
    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_metrics:
        families[row["family"]].append(row)
    family_summary = {
        family_id: core._aggregate_case_metrics(rows)
        for family_id, rows in sorted(families.items())
    }
    expected_families = {f"F{n:02d}" for n in range(1, 13)}
    summary = {
        "schema_version": "1.0",
        "evaluator_id": "eb-retrieval-evaluator-assurance-rc1",
        "evaluator_commit": EXPECTED_EVALUATOR_SHA,
        "benchmark_commit": EXPECTED_BENCHMARK_SHA,
        "split": split,
        "thresholds": dict(core.THRESHOLDS),
        "overall": core._aggregate_case_metrics(case_metrics),
        "families": family_summary,
        "family_reporting_complete": set(family_summary) == expected_families,
        "case_metrics": case_metrics,
    }
    qualified, failures = core.qualify_summary(summary)
    summary["qualified_retrieval_assurance_pass"] = qualified
    summary["qualification_failures"] = failures
    return summary, cases_all, gold_all


def canonical_identities(
    core: Any,
    benchmark_root: Path,
    results: list[dict[str, Any]],
) -> dict[str, list[tuple[str, str] | None]]:
    passage_index, _ = core.load_passages(benchmark_root)
    anchor_reverse = core.load_anchor_reverse_mapping(benchmark_root)
    output: dict[str, list[tuple[str, str] | None]] = {}
    for result in results:
        output[result["case_id"]] = [
            core.canonical_hit_identity(hit, passage_index, anchor_reverse)
            for hit in result["hits"]
        ]
    return output


def auxiliary_metrics(
    *,
    core: Any,
    benchmark_root: Path,
    split: str,
    results: list[dict[str, Any]],
    summary: dict[str, Any],
    cases_all: dict[str, dict[str, Any]],
    gold_all: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    ids_by_case = canonical_identities(core, benchmark_root, results)
    result_by_case = {row["case_id"]: row for row in results}

    scored_passage_num = 0
    scored_passage_den = 0
    source_num = 0
    source_den = 0
    per_case_source_recall: dict[str, float | None] = {}
    per_case_scored_passage_recall: dict[str, float | None] = {}

    aperture_case_ids: dict[str, list[str]] = defaultdict(list)
    for case_id, case in cases_all.items():
        if case.get("split") == split:
            aperture_case_ids[case["accessible_subset_id"]].append(case_id)

    for case_id in sorted(result_by_case):
        case = cases_all[case_id]
        k = int(case["runtime_config"]["maximum_passages"])
        bounded_ids = {value for value in ids_by_case[case_id][:k] if value is not None}
        rows = gold_all[case_id]
        scored_rows = [
            row
            for row in rows
            if row.get("in_accessible_subset") is True
            and (row.get("decisive") is True or core._is_material_context(row))
        ]
        scored_passages = {(row["source_id"], row["passage_id"]) for row in scored_rows}
        scored_sources = {row["source_id"] for row in scored_rows}
        hit_sources = {source_id for source_id, _ in bounded_ids}

        scored_passage_num += len(scored_passages & bounded_ids)
        scored_passage_den += len(scored_passages)
        source_num += len(scored_sources & hit_sources)
        source_den += len(scored_sources)
        per_case_scored_passage_recall[case_id] = ratio(
            len(scored_passages & bounded_ids), len(scored_passages)
        )
        per_case_source_recall[case_id] = ratio(
            len(scored_sources & hit_sources), len(scored_sources)
        )

    apertures: dict[str, Any] = {}
    metrics_by_case = {row["case_id"]: row for row in summary["case_metrics"]}
    for subset_id, case_ids in sorted(aperture_case_ids.items()):
        rows = [metrics_by_case[case_id] for case_id in sorted(case_ids)]
        apertures[subset_id] = core._aggregate_case_metrics(rows)
        source_values = [
            per_case_source_recall[case_id]
            for case_id in case_ids
            if per_case_source_recall[case_id] is not None
        ]
        passage_values = [
            per_case_scored_passage_recall[case_id]
            for case_id in case_ids
            if per_case_scored_passage_recall[case_id] is not None
        ]
        apertures[subset_id]["mean_case_source_recall_at_k"] = (
            None if not source_values else sum(source_values) / len(source_values)
        )
        apertures[subset_id]["mean_case_scored_passage_recall_at_k"] = (
            None if not passage_values else sum(passage_values) / len(passage_values)
        )

    no_answer_ids = sorted(
        case_id
        for case_id, case in cases_all.items()
        if case.get("split") == split
        and metrics_by_case.get(case_id, {}).get("family") == "F11"
    )
    no_answer_hit_counts = [len(result_by_case[case_id]["hits"]) for case_id in no_answer_ids]
    no_answer_statuses = Counter(
        result_by_case[case_id]["completeness_claim"]["status"] for case_id in no_answer_ids
    )
    no_answer = {
        "case_count": len(no_answer_ids),
        "returned_hit_count_total": sum(no_answer_hit_counts),
        "returned_hit_count_mean": mean(float(value) for value in no_answer_hit_counts),
        "hard_negative_count_at_k_total": sum(
            metrics_by_case[case_id]["hard_negative_count_at_k"] for case_id in no_answer_ids
        ),
        "false_completeness_claim_count": sum(
            1 for case_id in no_answer_ids if metrics_by_case[case_id]["false_completeness_claim"]
        ),
        "completeness_status_counts": dict(sorted(no_answer_statuses.items())),
        "note": (
            "Returned entries are retrieval nominations only. The c818 SUT does not "
            "label them proposition-level relevant or complete."
        ),
    }

    return {
        "passage_recall_at_k_scored_gold_pooled": ratio(
            scored_passage_num, scored_passage_den
        ),
        "passage_recall_at_k_scored_gold_numerator": scored_passage_num,
        "passage_recall_at_k_scored_gold_denominator": scored_passage_den,
        "source_recall_at_k_scored_gold_pooled": ratio(source_num, source_den),
        "source_recall_at_k_scored_gold_numerator": source_num,
        "source_recall_at_k_scored_gold_denominator": source_den,
        "decisive_passage_recall_at_k_pooled": summary["overall"][
            "decisive_annotation_recall_at_k"
        ],
        "first_relevant_mean_reciprocal_rank": summary["overall"][
            "first_decisive_mean_reciprocal_rank"
        ],
        "hard_negative_before_first_decisive_total": summary["overall"][
            "hard_negative_before_first_decisive_total"
        ],
        "hard_negative_proportion_at_k": summary["overall"][
            "hard_negative_proportion_at_k"
        ],
        "apertures": apertures,
        "no_answer": no_answer,
    }


def normalized_behavior(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": result["case_id"],
        "hits": [
            {
                "source_id": hit["source_id"],
                "passage_id": hit.get("passage_id"),
                "anchor": hit.get("anchor"),
                "rank": hit["rank"],
                "score": hit.get("score"),
                "text": hit.get("text"),
            }
            for hit in result["hits"]
        ],
        "search_scope": result["search_scope"],
        "completeness_claim": result["completeness_claim"],
    }


def compare_behavior(
    canonical_results: list[dict[str, Any]],
    alternate_results: list[dict[str, Any]],
) -> dict[str, Any]:
    alternate_by_case = {row["case_id"]: row for row in alternate_results}
    changed: list[str] = []
    for result in canonical_results:
        case_id = result["case_id"]
        if normalized_behavior(result) != normalized_behavior(alternate_by_case[case_id]):
            changed.append(case_id)
    return {
        "case_count": len(canonical_results),
        "changed_case_count": len(changed),
        "changed_case_ids": changed,
        "invariant": len(changed) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--evaluator-root", type=Path, required=True)
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--replay-results", type=Path)
    parser.add_argument("--reverse-results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    core, _corrected = configure_frozen_evaluator(args.evaluator_root)
    results = load_jsonl(args.results)
    summary, cases_all, gold_all = evaluate_split(
        core=core,
        benchmark_root=args.benchmark_root,
        split=args.split,
        results=results,
    )
    auxiliary = auxiliary_metrics(
        core=core,
        benchmark_root=args.benchmark_root,
        split=args.split,
        results=results,
        summary=summary,
        cases_all=cases_all,
        gold_all=gold_all,
    )

    control_comparison: dict[str, Any] = {}
    for control_id in ("C2", "C3"):
        all_control = core.make_control_results(args.benchmark_root, control_id)
        split_control = [
            row for row in all_control if cases_all[row["case_id"]].get("split") == args.split
        ]
        control_summary, _, _ = evaluate_split(
            core=core,
            benchmark_root=args.benchmark_root,
            split=args.split,
            results=split_control,
        )
        control_comparison[control_id] = {
            "overall": control_summary["overall"],
            "qualified_retrieval_assurance_pass": control_summary[
                "qualified_retrieval_assurance_pass"
            ],
            "qualification_failures": control_summary["qualification_failures"],
        }

    reproducibility: dict[str, Any] = {}
    if args.replay_results is not None:
        reproducibility["exact_replay"] = {
            "canonical_sha256": sha256_bytes(args.results.read_bytes()),
            "replay_sha256": sha256_bytes(args.replay_results.read_bytes()),
            "byte_identical": args.results.read_bytes() == args.replay_results.read_bytes(),
        }
    if args.reverse_results is not None:
        reverse = load_jsonl(args.reverse_results)
        reproducibility["source_order_invariance"] = compare_behavior(results, reverse)

    record = {
        "schema_version": "1.0",
        "split": args.split,
        "frozen_evaluator_summary": summary,
        "auxiliary_non_threshold_metrics": auxiliary,
        "weak_control_comparison": control_comparison,
        "reproducibility": reproducibility,
        "raw_results_sha256": sha256_bytes(args.results.read_bytes()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(record))
    print(
        json.dumps(
            {
                "output": str(args.output),
                "sha256": sha256_bytes(args.output.read_bytes()),
                "split": args.split,
                "qualified_retrieval_assurance_pass": summary[
                    "qualified_retrieval_assurance_pass"
                ],
                "qualification_failures": summary["qualification_failures"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
