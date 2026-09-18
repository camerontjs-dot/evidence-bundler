from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from typing import Any

PAIR_RE = re.compile(r"^(?P<family>.+)_(?P<kind>correct|shuffled)_cap_(?P<cap>\d+\.\d+)$")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_frozen_evaluator(path: str | Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("frozen_rc1_evaluator", path)
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


def delta(candidate: dict[str, Any], reference: dict[str, Any]) -> dict[str, float | int]:
    return {
        "required_lane_coverage": (
            candidate["required_lane_coverage"]["covered_positive_lanes"]
            - reference["required_lane_coverage"]["covered_positive_lanes"]
        ),
        "useful_recall": (
            candidate["useful_item_recall_at_3"]["rate"]
            - reference["useful_item_recall_at_3"]["rate"]
        ),
        "unsafe_retention": (
            candidate["unsafe_misleading_retention"]["total"]
            - reference["unsafe_misleading_retention"]["total"]
        ),
        "nonuseful_burden": (
            candidate["nonuseful_burden"]["total"]
            - reference["nonuseful_burden"]["total"]
        ),
        "redundant_retention": (
            candidate["redundant_retention"] - reference["redundant_retention"]
        ),
        "deep_useful_rescue": (
            candidate["deep_useful_rescue_count"] - reference["deep_useful_rescue_count"]
        ),
    }


def compact_metrics(metric: dict[str, Any]) -> dict[str, Any]:
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
        "category10_burden": metric["category10_selected_burden"],
        "ordinary_easy_coverage": metric["ordinary_easy_lane_coverage"],
        "complementary_coverage": metric["complementary_coverage"],
    }


def selection_change_count(
    candidate_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
) -> int:
    cand = selected_map(candidate_rows)
    base = selected_map(baseline_rows)
    return sum(cand[lane_id] != base[lane_id] for lane_id in sorted(base))


def posthoc_screen(
    correct: dict[str, Any],
    shuffled: dict[str, Any],
    baseline: dict[str, Any],
) -> str:
    c = delta(correct, baseline)
    s = delta(shuffled, baseline)

    if c["required_lane_coverage"] < 0 or c["useful_recall"] < -1e-12:
        return "HARMFUL_PRIMARY"

    correct_improvement = (
        c["required_lane_coverage"] > 0
        or c["useful_recall"] > 1e-12
        or c["unsafe_retention"] < 0
        or c["nonuseful_burden"] < 0
    )
    correct_beats_wrong = (
        c["required_lane_coverage"] > s["required_lane_coverage"]
        or c["useful_recall"] > s["useful_recall"] + 1e-12
        or c["unsafe_retention"] < s["unsafe_retention"]
        or c["nonuseful_burden"] < s["nonuseful_burden"]
    )
    if correct_improvement and correct_beats_wrong:
        return "PROMISING_CORRECT_OVER_SHUFFLED"
    if correct_improvement:
        return "GENERIC_OR_NONCAUSAL_IMPROVEMENT"
    if c == s:
        return "NO_CORRECT_SIGNAL_DISCRIMINATION"
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
    evaluator = load_frozen_evaluator(args.frozen_evaluator)

    lane_by_id, _candidate_by_id = evaluator._gold_index(gold)
    arms = selections["selections"]
    metrics = {
        name: evaluator._arm_metrics(name, selected_map(rows), lane_by_id)
        for name, rows in sorted(arms.items())
    }

    baseline_name = "baseline_no_gates_semantic_top3"
    placebo_name = "placebo_gate_present_ignored"
    baseline_rows = arms[baseline_name]
    baseline = metrics[baseline_name]
    if baseline_rows != arms[placebo_name]:
        raise AssertionError("placebo selections differ from no-Gate baseline")
    baseline_compare = dict(baseline)
    placebo_compare = dict(metrics[placebo_name])
    baseline_compare.pop("arm", None)
    placebo_compare.pop("arm", None)
    if placebo_compare != baseline_compare:
        raise AssertionError("placebo metric payload differs from no-Gate baseline")

    pairs: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for name in sorted(arms):
        match = PAIR_RE.match(name)
        if match is None or match.group("kind") != "correct":
            continue
        family = match.group("family")
        cap = match.group("cap")
        shuffled_name = f"{family}_shuffled_cap_{cap}"
        correct = metrics[name]
        shuffled = metrics[shuffled_name]
        row = {
            "family": family,
            "loss_cap": float(cap),
            "correct_arm": name,
            "shuffled_arm": shuffled_name,
            "correct": compact_metrics(correct),
            "shuffled": compact_metrics(shuffled),
            "correct_vs_baseline": delta(correct, baseline),
            "shuffled_vs_baseline": delta(shuffled, baseline),
            "correct_vs_shuffled": delta(correct, shuffled),
            "correct_changed_lanes": selection_change_count(arms[name], baseline_rows),
            "shuffled_changed_lanes": selection_change_count(
                arms[shuffled_name], baseline_rows
            ),
            "posthoc_screen": posthoc_screen(correct, shuffled, baseline),
        }
        pairs.append(row)
        grouped[family].append(row)

    family_summary: dict[str, Any] = {}
    for family, rows in sorted(grouped.items()):
        correct_selection_hashes = {
            hashlib.sha256(
                json.dumps(
                    arms[row["correct_arm"]],
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            for row in rows
        }
        shuffled_selection_hashes = {
            hashlib.sha256(
                json.dumps(
                    arms[row["shuffled_arm"]],
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            for row in rows
        }
        family_summary[family] = {
            "screens": sorted({row["posthoc_screen"] for row in rows}),
            "correct_distinct_selection_sets_across_caps": len(correct_selection_hashes),
            "shuffled_distinct_selection_sets_across_caps": len(shuffled_selection_hashes),
            "best_correct_coverage": max(row["correct"]["coverage"] for row in rows),
            "best_correct_useful_recall": max(
                row["correct"]["useful_recall"] for row in rows
            ),
            "best_correct_unsafe": min(row["correct"]["unsafe"] for row in rows),
            "best_correct_nonuseful": min(row["correct"]["nonuseful"] for row in rows),
            "max_correct_changed_lanes": max(
                row["correct_changed_lanes"] for row in rows
            ),
        }

    representation = selections["representation_summary"]
    fields_by_disposition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in representation["fields"]:
        fields_by_disposition[row["representation_disposition"]].append(
            {
                "field_id": row["field_id"],
                "layer": row["layer"],
                "evidence_status": row["evidence_status"],
                "cases_present": row["cases_present"],
                "cases_known": row["cases_known"],
                "unique_known_values": row["unique_known_values"],
            }
        )

    top_arms = sorted(
        (
            {
                "arm": name,
                **compact_metrics(metric),
                "delta_vs_baseline": delta(metric, baseline),
                "changed_lanes": selection_change_count(arms[name], baseline_rows),
            }
            for name, metric in metrics.items()
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
        "schema": "eb-gate-field-pressure-dev-posthoc-audit-v0",
        "classification": "POST_HOC_EXPOSED_DEVELOPMENT_DIAGNOSTIC",
        "source_selection_sha256": sha256_file(args.selections),
        "gold_sha256": sha256_file(args.gold),
        "frozen_evaluator_sha256": sha256_file(args.frozen_evaluator),
        "baseline": {
            "arm": baseline_name,
            "metrics": compact_metrics(baseline),
        },
        "placebo_exact_equal": True,
        "representation_counts": {
            "field_count": representation["field_count"],
            "nontrivial": representation["nontrivial"],
            "constant": representation["constant"],
            "unmaterialized_or_unknown": representation[
                "unmaterialized_or_unknown"
            ],
        },
        "fields_by_representation_disposition": {
            key: sorted(value, key=lambda row: row["field_id"])
            for key, value in sorted(fields_by_disposition.items())
        },
        "family_availability": selections["family_availability"],
        "family_summary": family_summary,
        "pairs": pairs,
        "top_arms": top_arms[:30],
        "nonclaims": [
            "post-hoc exposed-development diagnostic only",
            "does not qualify Gate fields or EB behavior",
            "does not alter any frozen selection",
            "uses exact frozen RC1 evaluator semantics for metrics",
            "survivors require fresh independent qualification",
        ],
    }
    output["audit_sha256"] = hashlib.sha256(
        json.dumps(output, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    Path(args.out).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    concise = {
        "baseline": output["baseline"],
        "representation_counts": output["representation_counts"],
        "family_availability": output["family_availability"],
        "family_summary": output["family_summary"],
        "nontrivial_fields": [
            row["field_id"]
            for row in output["fields_by_representation_disposition"].get(
                "NONTRIVIAL", []
            )
        ],
        "constant_fields": [
            row["field_id"]
            for row in output["fields_by_representation_disposition"].get(
                "CONSTANT", []
            )
        ],
        "top_arms": output["top_arms"][:15],
    }
    print(json.dumps(concise, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
