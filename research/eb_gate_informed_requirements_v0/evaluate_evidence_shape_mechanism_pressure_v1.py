from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType
from typing import Any

PAIR_RE = re.compile(
    r"^(?P<family>.+)_(?P<kind>correct|shuffled)_cap_(?P<cap>\d+\.\d{3})$"
)


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_evaluator(path: str | Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("frozen_rc1_evaluator_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load frozen RC1 evaluator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def selected_map(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        str(row["lane_id"]): [str(x) for x in row["selected_candidate_ids"]]
        for row in rows
    }


def compact(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "coverage": metric["required_lane_coverage"]["covered_positive_lanes"],
        "coverage_total": metric["required_lane_coverage"]["eligible_positive_lanes"],
        "useful_recall": metric["useful_item_recall_at_3"]["rate"],
        "useful_retained": metric["useful_item_recall_at_3"]["useful_groups_retained"],
        "useful_available": metric["useful_item_recall_at_3"]["useful_groups_available"],
        "unsafe": metric["unsafe_misleading_retention"]["total"],
        "nonuseful": metric["nonuseful_burden"]["total"],
        "redundant": metric["redundant_retention"],
        "deep_useful_rescue": metric["deep_useful_rescue_count"],
        "ordinary_easy_coverage": metric["ordinary_easy_lane_coverage"],
        "complementary_coverage": metric["complementary_coverage"],
    }


def delta(candidate: dict[str, Any], reference: dict[str, Any]) -> dict[str, float | int]:
    return {
        "coverage": (
            candidate["required_lane_coverage"]["covered_positive_lanes"]
            - reference["required_lane_coverage"]["covered_positive_lanes"]
        ),
        "useful_recall": (
            candidate["useful_item_recall_at_3"]["rate"]
            - reference["useful_item_recall_at_3"]["rate"]
        ),
        "unsafe": (
            candidate["unsafe_misleading_retention"]["total"]
            - reference["unsafe_misleading_retention"]["total"]
        ),
        "nonuseful": (
            candidate["nonuseful_burden"]["total"]
            - reference["nonuseful_burden"]["total"]
        ),
        "deep_useful_rescue": (
            candidate["deep_useful_rescue_count"]
            - reference["deep_useful_rescue_count"]
        ),
    }


def changed_lanes(
    rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]
) -> int:
    candidate = selected_map(rows)
    baseline = selected_map(baseline_rows)
    return sum(candidate[lane] != baseline[lane] for lane in sorted(baseline))


def same_metric_payload(a: dict[str, Any], b: dict[str, Any]) -> bool:
    left = dict(a)
    right = dict(b)
    left.pop("arm", None)
    right.pop("arm", None)
    return left == right


def screen_pair(
    correct: dict[str, Any],
    shuffled: dict[str, Any],
    semantic: dict[str, Any],
) -> str:
    c = delta(correct, semantic)
    s = delta(shuffled, semantic)

    if c["coverage"] < 0 or c["useful_recall"] < -1e-12:
        return "HARMFUL_PRIMARY"
    improves = (
        c["coverage"] > 0
        or c["useful_recall"] > 1e-12
        or c["unsafe"] < 0
        or c["nonuseful"] < 0
    )
    beats_shuffled = (
        c["coverage"] > s["coverage"]
        or c["useful_recall"] > s["useful_recall"] + 1e-12
        or c["unsafe"] < s["unsafe"]
        or c["nonuseful"] < s["nonuseful"]
    )
    if improves and beats_shuffled:
        return "CORRECT_SIGNAL_BEATS_SHUFFLED"
    if improves:
        return "GENERIC_OR_NONCAUSAL_EFFECT"
    if c == s:
        return "NO_DISCRIMINATION"
    return "MIXED_OR_NULL"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selections", required=True)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--frozen-evaluator", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    selections = load_json(args.selections)
    gold = load_json(args.gold)
    evaluator = load_evaluator(args.frozen_evaluator)
    lane_by_id, _ = evaluator._gold_index(gold)

    arms = selections["selections"]
    metrics = {
        arm: evaluator._arm_metrics(arm, selected_map(rows), lane_by_id)
        for arm, rows in sorted(arms.items())
    }

    semantic_name = "control_semantic_top3_no_gates"
    bm25_name = "control_bm25_rank_top3_no_gates"
    placebo_name = "control_gate_present_ignored"
    semantic = metrics[semantic_name]
    bm25 = metrics[bm25_name]
    placebo = metrics[placebo_name]

    if arms[semantic_name] != arms[placebo_name]:
        raise AssertionError("Gate-present placebo selection differs from no-Gate semantic")
    if not same_metric_payload(semantic, placebo):
        raise AssertionError("Gate-present placebo metric payload differs from semantic")

    expected_semantic = {
        "coverage": 21,
        "useful_retained": 24,
        "useful_available": 41,
        "unsafe": 62,
        "nonuseful": 66,
    }
    semantic_compact = compact(semantic)
    for key, expected in expected_semantic.items():
        if semantic_compact[key] != expected:
            raise AssertionError(
                f"semantic baseline drift for {key}: {semantic_compact[key]} != {expected}"
            )

    expected_bm25 = {
        "coverage": 16,
        "useful_retained": 22,
        "useful_available": 41,
        "unsafe": 62,
        "nonuseful": 68,
    }
    bm25_compact = compact(bm25)
    for key, expected in expected_bm25.items():
        if bm25_compact[key] != expected:
            raise AssertionError(
                f"BM25 baseline drift for {key}: {bm25_compact[key]} != {expected}"
            )

    reproduction_name = "gate_fraction_loose_correct_cap_0.020"
    reproduction = compact(metrics[reproduction_name])
    expected_shape = {
        "coverage": 21,
        "useful_retained": 27,
        "unsafe": 58,
        "nonuseful": 63,
    }
    for key, expected in expected_shape.items():
        if reproduction[key] != expected:
            raise AssertionError(
                f"prior evidence-shape mechanism did not reproduce for {key}: "
                f"{reproduction[key]} != {expected}"
            )

    pair_results: list[dict[str, Any]] = []
    for arm in sorted(arms):
        match = PAIR_RE.match(arm)
        if match is None or match.group("kind") != "correct":
            continue
        family = match.group("family")
        cap = match.group("cap")
        shuffled_arm = f"{family}_shuffled_cap_{cap}"
        if shuffled_arm not in metrics:
            raise AssertionError(f"missing shuffled pair for {arm}")
        correct_metric = metrics[arm]
        shuffled_metric = metrics[shuffled_arm]
        pair_results.append(
            {
                "family": family,
                "loss_cap": float(cap),
                "correct_arm": arm,
                "shuffled_arm": shuffled_arm,
                "correct": compact(correct_metric),
                "shuffled": compact(shuffled_metric),
                "correct_vs_semantic": delta(correct_metric, semantic),
                "shuffled_vs_semantic": delta(shuffled_metric, semantic),
                "correct_vs_shuffled": delta(correct_metric, shuffled_metric),
                "correct_changed_lanes": changed_lanes(arms[arm], arms[semantic_name]),
                "shuffled_changed_lanes": changed_lanes(
                    arms[shuffled_arm], arms[semantic_name]
                ),
                "screen": screen_pair(correct_metric, shuffled_metric, semantic),
            }
        )

    generic_results: list[dict[str, Any]] = []
    for arm in sorted(arms):
        if not (
            arm.startswith("generic_")
            or arm.startswith("gate_fraction_loose_then_posture_")
            or arm.startswith("gate_fraction_loose_then_source_diversity_")
        ):
            continue
        metric = metrics[arm]
        generic_results.append(
            {
                "arm": arm,
                "metrics": compact(metric),
                "vs_semantic": delta(metric, semantic),
                "changed_lanes": changed_lanes(arms[arm], arms[semantic_name]),
            }
        )

    family_summaries: dict[str, Any] = {}
    for family in sorted({row["family"] for row in pair_results}):
        rows = [row for row in pair_results if row["family"] == family]
        family_summaries[family] = {
            "screens": sorted({row["screen"] for row in rows}),
            "best_correct_coverage": max(row["correct"]["coverage"] for row in rows),
            "best_correct_useful_recall": max(
                row["correct"]["useful_recall"] for row in rows
            ),
            "best_correct_unsafe": min(row["correct"]["unsafe"] for row in rows),
            "best_correct_nonuseful": min(
                row["correct"]["nonuseful"] for row in rows
            ),
            "best_correct_vs_shuffled_useful_recall": max(
                row["correct_vs_shuffled"]["useful_recall"] for row in rows
            ),
            "best_correct_vs_shuffled_unsafe": min(
                row["correct_vs_shuffled"]["unsafe"] for row in rows
            ),
            "max_changed_lanes": max(row["correct_changed_lanes"] for row in rows),
        }

    top_arms = sorted(
        (
            {
                "arm": arm,
                "metrics": compact(metric),
                "vs_semantic": delta(metric, semantic),
                "changed_lanes": changed_lanes(arms[arm], arms[semantic_name]),
            }
            for arm, metric in metrics.items()
        ),
        key=lambda row: (
            -row["metrics"]["coverage"],
            -row["metrics"]["useful_recall"],
            row["metrics"]["unsafe"],
            row["metrics"]["nonuseful"],
            row["arm"],
        ),
    )

    output = {
        "schema": "eb-evidence-shape-mechanism-pressure-v1-evaluation",
        "classification": "EXPOSED_DEVELOPMENT_MECHANISM_DIAGNOSTIC",
        "selection_sha256": sha256_file(args.selections),
        "gold_sha256": sha256_file(args.gold),
        "frozen_evaluator_sha256": sha256_file(args.frozen_evaluator),
        "controls": {
            "bm25_no_gates": compact(bm25),
            "semantic_no_gates": compact(semantic),
            "gate_present_ignored": compact(placebo),
            "placebo_exact_equal": True,
        },
        "prior_evidence_shape_reproduction": {
            "arm": reproduction_name,
            "metrics": reproduction,
            "pass": True,
        },
        "expected_form_distribution": selections["expected_form_distribution"],
        "pair_results": pair_results,
        "family_summaries": family_summaries,
        "generic_results": generic_results,
        "top_arms": top_arms[:40],
        "nonclaims": [
            "exposed development evidence only",
            "mechanism results do not qualify any Gate field or EB behavior",
            "first-stage retrieval is unchanged",
            "fresh independent reproduction is required for any surviving mechanism",
        ],
    }
    output["evaluation_sha256"] = hashlib.sha256(
        json.dumps(output, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    Path(args.out).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "controls": output["controls"],
                "prior_evidence_shape_reproduction": output[
                    "prior_evidence_shape_reproduction"
                ],
                "expected_form_distribution": output["expected_form_distribution"],
                "family_summaries": output["family_summaries"],
                "generic_results": output["generic_results"],
                "top_arms": output["top_arms"][:20],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
