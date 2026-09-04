from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from research.retrieval_characterization_block_b_dev_rc1.runtime_runner import (
    canonical_json_bytes,
    load_jsonl,
)

DEPTH_MULTIPLIERS = (1, 2, 4)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _min_rank(rows: list[dict[str, Any]], passage_id: str) -> int | None:
    ranks = [int(row["rank"]) for row in rows if str(row["passage_id"]) == passage_id]
    return min(ranks) if ranks else None


def _first_prefix_hit(
    depth_records: list[dict[str, Any]],
    passage_id: str,
    channel: str,
) -> dict[str, Any] | None:
    for depth in depth_records:
        for prefix in depth["prefix_rankings"]:
            rank = _min_rank(prefix[channel], passage_id)
            if rank is not None:
                return {
                    "depth_multiplier": int(depth["depth_multiplier"]),
                    "child_depth": int(depth["child_depth"]),
                    "prefix_index": int(prefix["prefix_index"]),
                    "prefix": str(prefix["prefix"]),
                    "rank": rank,
                }
    return None


def _labels_by_passage(gold_rows: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    labels: dict[str, dict[str, str]] = {}
    for row in gold_rows:
        labels.setdefault(str(row["case_id"]), {})[str(row["passage_id"])] = str(
            row["relevance_class"]
        )
    return labels


def _burden(
    case: dict[str, Any],
    depth: dict[str, Any],
    labels: dict[str, dict[str, str]],
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    k = int(case["k"])
    final_ids = [str(value) for value in depth["final_k_passage_ids"]]
    top_depth_ids = [
        str(row["passage_id"])
        for row in depth["parent_candidate_order"][: int(depth["child_depth"])]
    ]
    case_labels = labels.get(case_id, {})

    def count_class(ids: list[str], target: str) -> int:
        return sum(1 for passage_id in ids if case_labels.get(passage_id) == target)

    def count_non_counter(ids: list[str]) -> int:
        return sum(
            1
            for passage_id in ids
            if case_labels.get(passage_id) != "decisive_counterevidence"
        )

    duplicates = int(depth["support_channel_duplicate_count"])
    return {
        "k": k,
        "final_k_count": len(final_ids),
        "final_k_hard_negative_count": count_class(final_ids, "hard_negative"),
        "final_k_non_counterevidence_count": count_non_counter(final_ids),
        "final_k_support_duplicate_count": duplicates,
        "final_k_support_duplicate_rate": (duplicates / len(final_ids) if final_ids else 0.0),
        "top_child_depth_parent_count": len(top_depth_ids),
        "top_child_depth_hard_negative_count": count_class(top_depth_ids, "hard_negative"),
        "top_child_depth_non_counterevidence_count": count_non_counter(top_depth_ids),
    }


def _classify_passage(
    *,
    case: dict[str, Any],
    depth_details: list[dict[str, Any]],
    burdens: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    k = int(case["k"])
    semantic_seen = any(row["best_semantic_rank"] is not None for row in depth_details)
    retained = [row for row in depth_details if row["final_k_retained"]]
    parent_ranks = [
        int(row["parent_candidate_rank"])
        for row in depth_details
        if row["parent_candidate_rank"] is not None
    ]
    child_ranks = [
        min(
            rank
            for rank in (row["best_lexical_rank"], row["best_semantic_rank"])
            if rank is not None
        )
        for row in depth_details
        if row["best_lexical_rank"] is not None or row["best_semantic_rank"] is not None
    ]

    if not semantic_seen:
        return {
            "primary": "PREFIX_QUERY_SUPPRESSION",
            "submechanisms": [],
            "reason": "Absent from every semantic contradiction child ranking through 4K.",
        }

    submechanisms: list[str] = []
    if retained and int(retained[0]["depth_multiplier"]) > 1:
        submechanisms.append("CHILD_DEPTH_APERTURE")
    if child_ranks and min(child_ranks) <= k and parent_ranks and min(parent_ranks) > k:
        submechanisms.append("CROSS_PREFIX_RRF_GEOMETRY")
    if parent_ranks and any(k < rank <= 2 * k for rank in parent_ranks):
        submechanisms.append("OUTPUT_TRUNCATION_PRESSURE")

    if retained:
        first_retained = retained[0]
        multiplier = int(first_retained["depth_multiplier"])
        burden = burdens[str(multiplier)]
        severe_noise = (
            burden["final_k_non_counterevidence_count"] >= max(1, k // 2)
            or burden["final_k_support_duplicate_rate"] >= 0.75
        )
        if multiplier == 4 and severe_noise:
            return {
                "primary": "WIDE_NOISY_RECOVERY",
                "submechanisms": submechanisms,
                "reason": (
                    "Recovered only at 4K and the retained candidate set remains heavily "
                    "non-counterevidence or support-duplicative."
                ),
            }
        return {
            "primary": "MIXED_OR_OTHER",
            "submechanisms": submechanisms,
            "reason": (
                "Recovered after widening; the preregistered failure taxonomy does not "
                "label a clean child-depth-only recovery as fusion or output truncation."
            ),
        }

    if "CROSS_PREFIX_RRF_GEOMETRY" in submechanisms:
        return {
            "primary": "CROSS_PREFIX_RRF_GEOMETRY",
            "submechanisms": submechanisms,
            "reason": (
                "At least one contradiction child channel ranks the passage within K, "
                "but cross-prefix fusion/parent ordering leaves it outside final K."
            ),
        }
    if "OUTPUT_TRUNCATION_PRESSURE" in submechanisms:
        return {
            "primary": "OUTPUT_TRUNCATION",
            "submechanisms": submechanisms,
            "reason": (
                "The passage reaches the fused/parent aperture near the output boundary "
                "but remains outside final K."
            ),
        }
    return {
        "primary": "MIXED_OR_OTHER",
        "submechanisms": submechanisms,
        "reason": (
            "The passage is present in contradiction children but does not fit the "
            "preregistered exclusive mechanisms cleanly."
        ),
    }


def analyze(
    *,
    raw_path: Path,
    gold_path: Path,
    expected_raw_sha256: str,
    output: Path,
) -> dict[str, Any]:
    raw_bytes = raw_path.read_bytes()
    actual_raw_sha256 = sha256_bytes(raw_bytes)
    if actual_raw_sha256 != expected_raw_sha256:
        raise ValueError("Raw retrieval artifact digest changed before analysis")
    raw = json.loads(raw_bytes)
    gold_rows = load_jsonl(gold_path)
    labels = _labels_by_passage(gold_rows)
    by_case = {str(row["case_id"]): row for row in raw["cases"]}

    decisive_rows = [
        row
        for row in gold_rows
        if bool(row.get("decisive"))
        and str(row["relevance_class"]) == "decisive_counterevidence"
    ]
    passage_results: list[dict[str, Any]] = []
    for gold in sorted(
        decisive_rows,
        key=lambda row: (str(row["case_id"]), str(row["passage_id"])),
    ):
        case_id = str(gold["case_id"])
        passage_id = str(gold["passage_id"])
        case = by_case[case_id]
        depth_records = sorted(
            case["depths"], key=lambda row: int(row["depth_multiplier"])
        )
        depth_details: list[dict[str, Any]] = []
        burdens: dict[str, dict[str, Any]] = {}
        for depth in depth_records:
            lexical_ranks: list[int] = []
            semantic_ranks: list[int] = []
            for prefix in depth["prefix_rankings"]:
                lexical_rank = _min_rank(prefix["lexical"], passage_id)
                semantic_rank = _min_rank(prefix["semantic"], passage_id)
                if lexical_rank is not None:
                    lexical_ranks.append(lexical_rank)
                if semantic_rank is not None:
                    semantic_ranks.append(semantic_rank)
            fused_rank = _min_rank(depth["fused_rrf_order"], passage_id)
            parent_rank = _min_rank(depth["parent_candidate_order"], passage_id)
            multiplier = int(depth["depth_multiplier"])
            depth_details.append(
                {
                    "depth_multiplier": multiplier,
                    "child_depth": int(depth["child_depth"]),
                    "best_lexical_rank": min(lexical_ranks) if lexical_ranks else None,
                    "best_semantic_rank": min(semantic_ranks) if semantic_ranks else None,
                    "fused_rank": fused_rank,
                    "parent_candidate_rank": parent_rank,
                    "final_k_retained": passage_id in depth["final_k_passage_ids"],
                    "support_channel_duplicate": passage_id
                    in depth["support_channel_duplicate_passage_ids"],
                }
            )
            burdens[str(multiplier)] = _burden(case, depth, labels)

        classification = _classify_passage(
            case=case,
            depth_details=depth_details,
            burdens=burdens,
        )
        passage_results.append(
            {
                "case_id": case_id,
                "family": case["family"],
                "passage_id": passage_id,
                "source_id": gold["source_id"],
                "k": int(case["k"]),
                "first_lexical_hit": _first_prefix_hit(
                    depth_records, passage_id, "lexical"
                ),
                "first_semantic_hit": _first_prefix_hit(
                    depth_records, passage_id, "semantic"
                ),
                "depths": depth_details,
                "burdens": burdens,
                "classification": classification,
            }
        )

    r02 = [row for row in passage_results if str(row["family"]).startswith("R02")]
    primary_counts: dict[str, int] = {}
    for row in passage_results:
        primary = str(row["classification"]["primary"])
        primary_counts[primary] = primary_counts.get(primary, 0) + 1

    no_counter_families: dict[str, dict[str, int]] = {}
    decisive_cases = {str(row["case_id"]) for row in decisive_rows}
    for case in raw["cases"]:
        if str(case["case_id"]) in decisive_cases:
            continue
        family = str(case["family"])
        stats = no_counter_families.setdefault(
            family,
            {
                "cases": 0,
                "final_k_candidates_at_4k": 0,
                "support_duplicates_at_4k": 0,
            },
        )
        stats["cases"] += 1
        depth4 = next(
            row for row in case["depths"] if int(row["depth_multiplier"]) == 4
        )
        stats["final_k_candidates_at_4k"] += len(depth4["final_k_passage_ids"])
        stats["support_duplicates_at_4k"] += int(
            depth4["support_channel_duplicate_count"]
        )

    result = {
        "schema_version": "1.0",
        "experiment": raw["experiment"],
        "apparatus_sha": raw["apparatus_sha"],
        "raw_sha256_verified": actual_raw_sha256,
        "gold_path": str(gold_path),
        "decisive_counterevidence_count": len(passage_results),
        "classification_counts": primary_counts,
        "r02": r02,
        "all_decisive_counterevidence": passage_results,
        "no_decisive_counterevidence_family_spillover": no_counter_families,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    return {
        "apparatus_sha": raw["apparatus_sha"],
        "raw_sha256_verified": actual_raw_sha256,
        "analysis_sha256": sha256_bytes(output.read_bytes()),
        "decisive_counterevidence_count": len(passage_results),
        "classification_counts": primary_counts,
        "r02": r02,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--expected-raw-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = analyze(
        raw_path=args.raw,
        gold_path=args.gold,
        expected_raw_sha256=args.expected_raw_sha256,
        output=args.output,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
