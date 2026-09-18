from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

CORRECT_RE = re.compile(r"^(?P<family>.+)_correct_cap_(?P<cap>\d+\.\d+)$")
SHUFFLED_RE = re.compile(r"^(?P<family>.+)_shuffled_cap_(?P<cap>\d+\.\d+)$")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lane_gold_index(gold: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(lane["lane_id"]): lane for lane in gold["lanes"]}


def selected_map(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        str(row["lane_id"]): [str(x) for x in row["selected_candidate_ids"]]
        for row in rows
    }


def metrics_for_arm(
    rows: list[dict[str, Any]],
    gold_by_lane: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    selected = selected_map(rows)

    positive_lanes = 0
    covered_positive_lanes = 0
    useful_total = 0
    useful_selected = 0
    class_counts: Counter[str] = Counter()
    selected_class_counts: Counter[str] = Counter()
    selected_reason_counts: Counter[str] = Counter()
    no_clear_unsafe = 0
    total_slots = 0

    lane_details: list[dict[str, Any]] = []

    for lane_id in sorted(gold_by_lane):
        lane = gold_by_lane[lane_id]
        by_id = {str(c["candidate_id"]): c for c in lane["candidates"]}
        chosen = selected[lane_id]
        total_slots += len(chosen)

        for candidate in lane["candidates"]:
            cls = str(candidate["gold_class"])
            class_counts[cls] += 1
            if cls in {"REQUIRED", "USEFUL_DISTINCT"}:
                useful_total += 1

        required_groups = {
            str(group)
            for candidate in lane["candidates"]
            if str(candidate["gold_class"]) == "REQUIRED"
            for group in candidate.get("required_group_ids", [])
        }
        selected_groups = {
            str(group)
            for candidate_id in chosen
            for group in by_id[candidate_id].get("required_group_ids", [])
        }

        lane_positive = str(lane.get("lane_type")) == "positive"
        if lane_positive:
            positive_lanes += 1
            covered = bool(required_groups) and required_groups <= selected_groups
            covered_positive_lanes += int(covered)
        else:
            covered = None

        lane_useful = 0
        lane_unsafe = 0
        lane_nonuseful = 0
        for candidate_id in chosen:
            candidate = by_id[candidate_id]
            cls = str(candidate["gold_class"])
            selected_class_counts[cls] += 1
            selected_reason_counts[str(candidate.get("reason_code"))] += 1
            if cls in {"REQUIRED", "USEFUL_DISTINCT"}:
                useful_selected += 1
                lane_useful += 1
            if cls == "UNSAFE_OR_MISLEADING":
                lane_unsafe += 1
            if cls in {"UNSAFE_OR_MISLEADING", "DISTRACTOR"}:
                lane_nonuseful += 1

        if not lane_positive:
            no_clear_unsafe += lane_unsafe

        lane_details.append(
            {
                "lane_id": lane_id,
                "positive": lane_positive,
                "required_group_count": len(required_groups),
                "selected_required_group_count": len(required_groups & selected_groups),
                "required_coverage_complete": covered,
                "selected_useful": lane_useful,
                "selected_unsafe": lane_unsafe,
                "selected_nonuseful": lane_nonuseful,
            }
        )

    unsafe = selected_class_counts["UNSAFE_OR_MISLEADING"]
    distractor = selected_class_counts["DISTRACTOR"]
    redundant = selected_class_counts["REDUNDANT"]
    return {
        "required_lane_coverage": {
            "covered_positive_lanes": covered_positive_lanes,
            "eligible_positive_lanes": positive_lanes,
            "rate": covered_positive_lanes / positive_lanes if positive_lanes else 0.0,
        },
        "useful_candidate_recall_at_3": {
            "selected": useful_selected,
            "total": useful_total,
            "rate": useful_selected / useful_total if useful_total else 0.0,
        },
        "unsafe_retained": unsafe,
        "distractor_retained": distractor,
        "redundant_retained": redundant,
        "nonuseful_burden": unsafe + distractor,
        "no_clear_lane_unsafe": no_clear_unsafe,
        "selected_class_counts": dict(sorted(selected_class_counts.items())),
        "selected_reason_counts": dict(sorted(selected_reason_counts.items())),
        "total_slots": total_slots,
        "lane_details": lane_details,
    }


def delta(candidate: dict[str, Any], reference: dict[str, Any]) -> dict[str, float | int]:
    return {
        "required_lane_coverage": (
            candidate["required_lane_coverage"]["covered_positive_lanes"]
            - reference["required_lane_coverage"]["covered_positive_lanes"]
        ),
        "useful_recall": (
            candidate["useful_candidate_recall_at_3"]["rate"]
            - reference["useful_candidate_recall_at_3"]["rate"]
        ),
        "unsafe_retained": candidate["unsafe_retained"] - reference["unsafe_retained"],
        "nonuseful_burden": candidate["nonuseful_burden"] - reference["nonuseful_burden"],
        "no_clear_lane_unsafe": (
            candidate["no_clear_lane_unsafe"] - reference["no_clear_lane_unsafe"]
        ),
    }


def causal_screen(
    correct: dict[str, Any],
    shuffled: dict[str, Any],
    baseline: dict[str, Any],
) -> str:
    corr_delta = delta(correct, baseline)
    shuffle_delta = delta(shuffled, baseline)

    correct_better_than_shuffled = (
        corr_delta["required_lane_coverage"] > shuffle_delta["required_lane_coverage"]
        or corr_delta["useful_recall"] > shuffle_delta["useful_recall"] + 1e-12
        or corr_delta["unsafe_retained"] < shuffle_delta["unsafe_retained"]
        or corr_delta["nonuseful_burden"] < shuffle_delta["nonuseful_burden"]
    )
    correct_harms_primary = (
        corr_delta["required_lane_coverage"] < 0
        or corr_delta["useful_recall"] < -1e-12
    )
    correct_improves_any = (
        corr_delta["required_lane_coverage"] > 0
        or corr_delta["useful_recall"] > 1e-12
        or corr_delta["unsafe_retained"] < 0
        or corr_delta["nonuseful_burden"] < 0
    )

    if correct_harms_primary:
        return "HARMFUL_ON_EXPOSED_DEVELOPMENT_COHORT"
    if correct_improves_any and correct_better_than_shuffled:
        return "PROMISING_CORRECT_SIGNAL_DISCRIMINATION"
    if correct_improves_any and not correct_better_than_shuffled:
        return "NONCAUSAL_OR_GENERIC_EFFECT_WRONG_SIGNAL_SIMILAR"
    if delta(correct, baseline) == delta(shuffled, baseline):
        return "NO_CORRECT_SIGNAL_DISCRIMINATION"
    return "MIXED_OR_INCONCLUSIVE_DEVELOPMENT_SIGNAL"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selections", required=True)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    selection_path = Path(args.selections)
    gold_path = Path(args.gold)
    selections = json.loads(selection_path.read_text(encoding="utf-8"))
    gold = json.loads(gold_path.read_text(encoding="utf-8"))

    arms = selections["selections"]
    gold_by_lane = lane_gold_index(gold)

    arm_metrics = {
        name: metrics_for_arm(rows, gold_by_lane)
        for name, rows in sorted(arms.items())
    }
    baseline_name = "baseline_no_gates_semantic_top3"
    placebo_name = "placebo_gate_present_ignored"
    baseline = arm_metrics[baseline_name]

    if arms[baseline_name] != arms[placebo_name]:
        raise AssertionError("Gate-present placebo differs from no-Gate baseline")
    if arm_metrics[baseline_name] != arm_metrics[placebo_name]:
        raise AssertionError("Gate-present placebo metrics differ from no-Gate baseline")

    pair_results: list[dict[str, Any]] = []
    for name in sorted(arms):
        match = CORRECT_RE.match(name)
        if not match:
            continue
        family = match.group("family")
        cap = match.group("cap")
        shuffled_name = f"{family}_shuffled_cap_{cap}"
        if shuffled_name not in arm_metrics:
            raise AssertionError(f"missing shuffled control for {name}")
        correct = arm_metrics[name]
        shuffled = arm_metrics[shuffled_name]
        pair_results.append(
            {
                "family": family,
                "loss_cap": float(cap),
                "correct_arm": name,
                "shuffled_arm": shuffled_name,
                "correct_vs_baseline": delta(correct, baseline),
                "shuffled_vs_baseline": delta(shuffled, baseline),
                "correct_vs_shuffled": delta(correct, shuffled),
                "development_screen": causal_screen(correct, shuffled, baseline),
            }
        )

    by_family: dict[str, Counter[str]] = {}
    for row in pair_results:
        by_family.setdefault(row["family"], Counter())[row["development_screen"]] += 1

    best_by_coverage = sorted(
        (
            {
                "arm": name,
                "coverage": metric["required_lane_coverage"]["covered_positive_lanes"],
                "useful_recall": metric["useful_candidate_recall_at_3"]["rate"],
                "unsafe": metric["unsafe_retained"],
                "nonuseful": metric["nonuseful_burden"],
            }
            for name, metric in arm_metrics.items()
        ),
        key=lambda row: (
            -row["coverage"],
            -row["useful_recall"],
            row["unsafe"],
            row["nonuseful"],
            row["arm"],
        ),
    )

    output = {
        "schema": "eb-gate-field-pressure-dev-evaluation-v0",
        "classification": "EXPOSED_DEVELOPMENT_DIAGNOSTIC_ONLY",
        "selection_sha256": sha256_file(selection_path),
        "gold_sha256": sha256_file(gold_path),
        "baseline": {
            "arm": baseline_name,
            "metrics": baseline,
        },
        "placebo_control": {
            "arm": placebo_name,
            "exact_selection_equal": True,
            "exact_metrics_equal": True,
        },
        "representation_summary": selections["representation_summary"],
        "family_availability": selections["family_availability"],
        "pair_results": pair_results,
        "family_screen_counts": {
            family: dict(sorted(counter.items()))
            for family, counter in sorted(by_family.items())
        },
        "top_arms_by_primary_order": best_by_coverage[:20],
        "arm_metrics": arm_metrics,
        "nonclaims": [
            "this is exposed development evidence only",
            "a promising screen does not authorize EB hint use",
            "a negative screen can identify fields or mechanisms to prune or repair",
            "first-stage retrieval remains unchanged",
        ],
    }
    output["evaluation_sha256"] = hashlib.sha256(
        json.dumps(output, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    Path(args.out).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    concise = {
        "baseline": {
            "coverage": baseline["required_lane_coverage"],
            "useful_recall": baseline["useful_candidate_recall_at_3"],
            "unsafe": baseline["unsafe_retained"],
            "nonuseful": baseline["nonuseful_burden"],
        },
        "representation": {
            k: selections["representation_summary"][k]
            for k in ("field_count", "nontrivial", "constant", "unmaterialized_or_unknown")
        },
        "family_screen_counts": output["family_screen_counts"],
        "top_arms": output["top_arms_by_primary_order"][:10],
    }
    print(json.dumps(concise, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
