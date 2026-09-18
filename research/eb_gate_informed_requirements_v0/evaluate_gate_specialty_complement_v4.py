from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

CAP_LABELS = ("0.005", "0.010", "0.020")
USEFUL = {"REQUIRED", "USEFUL_DISTINCT"}


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_evaluator(path: str | Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("frozen_eval_v4", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen RC1 evaluator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def selected_map(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        str(row["lane_id"]): [str(value) for value in row["selected_candidate_ids"]]
        for row in rows
    }


def compact(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "coverage": metric["required_lane_coverage"]["covered_positive_lanes"],
        "coverage_total": metric["required_lane_coverage"]["eligible_positive_lanes"],
        "useful_retained": metric["useful_item_recall_at_3"]["useful_groups_retained"],
        "useful_available": metric["useful_item_recall_at_3"]["useful_groups_available"],
        "useful_recall": metric["useful_item_recall_at_3"]["rate"],
        "unsafe": metric["unsafe_misleading_retention"]["total"],
        "nonuseful": metric["nonuseful_burden"]["total"],
        "deep_useful_rescue": metric["deep_useful_rescue_count"],
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


def subset_metrics(
    evaluator: ModuleType,
    arm: str,
    selections: dict[str, list[str]],
    lane_by_id: dict[str, Any],
    lane_ids: list[str],
) -> dict[str, Any]:
    return evaluator._arm_metrics(
        arm,
        {lane_id: selections[lane_id] for lane_id in lane_ids},
        {lane_id: lane_by_id[lane_id] for lane_id in lane_ids},
    )


def lane_outcomes(
    selections: dict[str, list[str]],
    lane_by_id: dict[str, Any],
    lane_ids: list[str],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for lane_id in lane_ids:
        lane = lane_by_id[lane_id]
        by_id = {
            str(candidate["candidate_id"]): candidate
            for candidate in lane["candidates"]
        }
        chosen = selections[lane_id]
        selected = [by_id[candidate_id] for candidate_id in chosen]
        out[lane_id] = {
            "selected_candidate_ids": chosen,
            "selected_classes": [
                str(candidate["gold_class"]) for candidate in selected
            ],
            "selected_ranks": [int(candidate["rank"]) for candidate in selected],
            "useful_selected": sum(
                str(candidate["gold_class"]) in USEFUL for candidate in selected
            ),
            "unsafe_selected": sum(
                str(candidate["gold_class"]) == "UNSAFE_OR_MISLEADING"
                for candidate in selected
            ),
            "nonuseful_selected": sum(
                str(candidate["gold_class"])
                in {"DISTRACTOR", "REDUNDANT", "UNSAFE_OR_MISLEADING"}
                for candidate in selected
            ),
        }
    return out


def changed(
    candidate: dict[str, list[str]],
    reference: dict[str, list[str]],
    lane_ids: list[str],
) -> list[str]:
    return [
        lane_id
        for lane_id in lane_ids
        if candidate[lane_id] != reference[lane_id]
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selections", required=True)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--frozen-evaluator", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    payload = load_json(args.selections)
    gold = load_json(args.gold)
    evaluator = load_evaluator(args.frozen_evaluator)
    lane_by_id, _ = evaluator._gold_index(gold)
    arms = {
        arm: selected_map(rows)
        for arm, rows in payload["selections"].items()
    }
    exceptional = list(payload["exceptional_lanes"])
    baseline_name = "control_semantic_top3_no_gates"
    baseline = evaluator._arm_metrics(
        baseline_name, arms[baseline_name], lane_by_id
    )
    baseline_exceptional = subset_metrics(
        evaluator,
        baseline_name,
        arms[baseline_name],
        lane_by_id,
        exceptional,
    )

    comparisons: list[dict[str, Any]] = []
    for label in CAP_LABELS:
        names = {
            "true": f"true_specialty_fraction_cap_{label}",
            "true_anyof": f"true_specialty_anyof_cap_{label}",
            "complement": f"complement_fraction_cap_{label}",
            "complement_anyof": f"complement_anyof_cap_{label}",
            "wrong_only": f"wrong_only_cap_{label}",
            "generic_union": f"generic_union_fraction_cap_{label}",
            "generic_union_anyof": f"generic_union_anyof_cap_{label}",
            "authoritative_only": f"authoritative_only_cap_{label}",
            "event_only": f"event_only_cap_{label}",
            "registry_only": f"registry_only_cap_{label}",
        }

        all_metrics = {
            key: evaluator._arm_metrics(arm, arms[arm], lane_by_id)
            for key, arm in names.items()
        }
        exceptional_metrics = {
            key: subset_metrics(
                evaluator, arm, arms[arm], lane_by_id, exceptional
            )
            for key, arm in names.items()
        }
        true_map = arms[names["true"]]

        comparisons.append(
            {
                "loss_cap": float(label),
                "overall": {
                    key: compact(metric)
                    for key, metric in all_metrics.items()
                },
                "overall_vs_semantic": {
                    key: delta(metric, baseline)
                    for key, metric in all_metrics.items()
                },
                "exceptional_8": {
                    key: compact(metric)
                    for key, metric in exceptional_metrics.items()
                },
                "exceptional_vs_semantic": {
                    key: delta(metric, baseline_exceptional)
                    for key, metric in exceptional_metrics.items()
                },
                "exceptional_vs_true": {
                    key: delta(metric, exceptional_metrics["true"])
                    for key, metric in exceptional_metrics.items()
                    if key != "true"
                },
                "changed_lanes_vs_true": {
                    key: changed(arms[arm], true_map, exceptional)
                    for key, arm in names.items()
                    if key != "true"
                },
                "lane_outcomes": {
                    key: lane_outcomes(arms[arm], lane_by_id, exceptional)
                    for key, arm in names.items()
                    if key
                    in {
                        "true",
                        "complement",
                        "wrong_only",
                        "generic_union",
                    }
                },
            }
        )

    output = {
        "schema": "eb-gate-specialty-complement-v4-evaluation",
        "classification": "EXPOSED_DEVELOPMENT_COMPLEMENT_DIAGNOSTIC",
        "selection_sha256": sha256_file(args.selections),
        "gold_sha256": sha256_file(args.gold),
        "frozen_evaluator_sha256": sha256_file(args.frozen_evaluator),
        "exceptional_lanes": exceptional,
        "true_specialty_by_lane": payload["true_specialty_by_lane"],
        "complement_by_lane": payload["complement_by_lane"],
        "wrong_only_by_lane": payload["wrong_only_by_lane"],
        "baseline_exceptional": compact(baseline_exceptional),
        "comparisons": comparisons,
        "nonclaims": [
            "exposed development complement diagnostic only",
            "no Gate field or EB behavior qualified",
            "no model or Gate runtime rerun",
            "fresh independent reproduction remains required",
        ],
    }
    output["evaluation_sha256"] = hashlib.sha256(
        json.dumps(output, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    Path(args.out).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "true_specialty_by_lane": output["true_specialty_by_lane"],
                "complement_by_lane": output["complement_by_lane"],
                "wrong_only_by_lane": output["wrong_only_by_lane"],
                "baseline_exceptional": output["baseline_exceptional"],
                "comparisons": comparisons,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
