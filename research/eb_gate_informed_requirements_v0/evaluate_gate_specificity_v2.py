from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

CAP_LABELS = ("0.005", "0.010", "0.020")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_evaluator(path: str | Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("frozen_rc1_evaluator_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load frozen RC1 evaluator")
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


def subset_metrics(
    evaluator: ModuleType,
    arm: str,
    selections: dict[str, list[str]],
    lane_by_id: dict[str, Any],
    lane_ids: list[str],
) -> dict[str, Any]:
    subset_lane_by_id = {lane_id: lane_by_id[lane_id] for lane_id in lane_ids}
    subset_selections = {lane_id: selections[lane_id] for lane_id in lane_ids}
    return evaluator._arm_metrics(arm, subset_selections, subset_lane_by_id)


def changed_lanes(
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

    selections_payload = load_json(args.selections)
    gold = load_json(args.gold)
    evaluator = load_evaluator(args.frozen_evaluator)
    lane_by_id, _ = evaluator._gold_index(gold)

    arms = {
        arm: selected_map(rows)
        for arm, rows in selections_payload["selections"].items()
    }
    all_lanes = sorted(lane_by_id)
    default_lanes = list(selections_payload["default_lanes"])
    exceptional_lanes = list(selections_payload["exceptional_lanes"])

    metrics: dict[str, dict[str, Any]] = {}
    default_metrics: dict[str, dict[str, Any]] = {}
    exceptional_metrics: dict[str, dict[str, Any]] = {}
    for arm, selection in sorted(arms.items()):
        metrics[arm] = evaluator._arm_metrics(arm, selection, lane_by_id)
        default_metrics[arm] = subset_metrics(
            evaluator, arm, selection, lane_by_id, default_lanes
        )
        exceptional_metrics[arm] = subset_metrics(
            evaluator, arm, selection, lane_by_id, exceptional_lanes
        )

    semantic_name = "control_semantic_top3_no_gates"
    semantic = metrics[semantic_name]
    semantic_compact = compact(semantic)
    expected_semantic = {
        "coverage": 21,
        "useful_retained": 24,
        "useful_available": 41,
        "unsafe": 62,
        "nonuseful": 66,
    }
    for key, expected in expected_semantic.items():
        if semantic_compact[key] != expected:
            raise AssertionError(
                f"semantic control drift for {key}: "
                f"{semantic_compact[key]} != {expected}"
            )

    comparisons: list[dict[str, Any]] = []
    for label in CAP_LABELS:
        true_name = f"true_gate_fraction_cap_{label}"
        constant_name = f"constant_default_fraction_cap_{label}"
        clipped_name = f"true_gate_supported_only_cap_{label}"
        shuffled_name = f"rare_shuffled_gate_fraction_cap_{label}"
        shuffled_clipped_name = f"rare_shuffled_supported_only_cap_{label}"
        measurement_name = f"measurement_only_prior_cap_{label}"
        document_name = f"document_only_prior_cap_{label}"

        true = metrics[true_name]
        constant = metrics[constant_name]
        clipped = metrics[clipped_name]
        shuffled = metrics[shuffled_name]
        shuffled_clipped = metrics[shuffled_clipped_name]
        measurement = metrics[measurement_name]
        document = metrics[document_name]

        true_map = arms[true_name]
        constant_map = arms[constant_name]
        clipped_map = arms[clipped_name]
        shuffled_map = arms[shuffled_name]
        measurement_map = arms[measurement_name]
        document_map = arms[document_name]
        semantic_map = arms[semantic_name]

        default_true_constant_changes = changed_lanes(
            true_map, constant_map, default_lanes
        )
        if default_true_constant_changes:
            raise AssertionError(
                f"true and constant differ on default lanes at cap {label}: "
                f"{default_true_constant_changes}"
            )

        comparisons.append(
            {
                "loss_cap": float(label),
                "overall": {
                    "semantic": compact(semantic),
                    "true_gate": compact(true),
                    "constant_default": compact(constant),
                    "true_supported_only": compact(clipped),
                    "rare_shuffled_gate": compact(shuffled),
                    "rare_shuffled_supported_only": compact(shuffled_clipped),
                    "measurement_only": compact(measurement),
                    "document_only": compact(document),
                    "true_vs_constant": delta(true, constant),
                    "true_vs_semantic": delta(true, semantic),
                    "constant_vs_semantic": delta(constant, semantic),
                    "true_supported_vs_true": delta(clipped, true),
                    "true_vs_rare_shuffled": delta(true, shuffled),
                    "measurement_vs_constant": delta(measurement, constant),
                    "document_vs_semantic": delta(document, semantic),
                },
                "default_22_lanes": {
                    "semantic": compact(default_metrics[semantic_name]),
                    "true_gate": compact(default_metrics[true_name]),
                    "constant_default": compact(default_metrics[constant_name]),
                    "true_vs_constant": delta(
                        default_metrics[true_name],
                        default_metrics[constant_name],
                    ),
                },
                "exceptional_8_lanes": {
                    "semantic": compact(exceptional_metrics[semantic_name]),
                    "true_gate": compact(exceptional_metrics[true_name]),
                    "constant_default": compact(exceptional_metrics[constant_name]),
                    "true_supported_only": compact(
                        exceptional_metrics[clipped_name]
                    ),
                    "rare_shuffled_gate": compact(
                        exceptional_metrics[shuffled_name]
                    ),
                    "rare_shuffled_supported_only": compact(
                        exceptional_metrics[shuffled_clipped_name]
                    ),
                    "measurement_only": compact(
                        exceptional_metrics[measurement_name]
                    ),
                    "true_vs_constant": delta(
                        exceptional_metrics[true_name],
                        exceptional_metrics[constant_name],
                    ),
                    "true_vs_rare_shuffled": delta(
                        exceptional_metrics[true_name],
                        exceptional_metrics[shuffled_name],
                    ),
                    "supported_vs_true": delta(
                        exceptional_metrics[clipped_name],
                        exceptional_metrics[true_name],
                    ),
                },
                "changed_lanes": {
                    "true_vs_semantic": changed_lanes(
                        true_map, semantic_map, all_lanes
                    ),
                    "constant_vs_semantic": changed_lanes(
                        constant_map, semantic_map, all_lanes
                    ),
                    "true_vs_constant": changed_lanes(
                        true_map, constant_map, all_lanes
                    ),
                    "true_vs_constant_exceptional": changed_lanes(
                        true_map, constant_map, exceptional_lanes
                    ),
                    "true_supported_vs_true": changed_lanes(
                        clipped_map, true_map, all_lanes
                    ),
                    "true_vs_rare_shuffled_exceptional": changed_lanes(
                        true_map, shuffled_map, exceptional_lanes
                    ),
                    "measurement_vs_constant": changed_lanes(
                        measurement_map, constant_map, all_lanes
                    ),
                    "document_vs_semantic": changed_lanes(
                        document_map, semantic_map, all_lanes
                    ),
                },
            }
        )

    output = {
        "schema": "eb-gate-specificity-v2-evaluation",
        "classification": "EXPOSED_DEVELOPMENT_SPECIFICITY_DIAGNOSTIC",
        "selection_sha256": sha256_file(args.selections),
        "gold_sha256": sha256_file(args.gold),
        "frozen_evaluator_sha256": sha256_file(args.frozen_evaluator),
        "default_expected_forms": selections_payload["default_expected_forms"],
        "default_lanes": default_lanes,
        "exceptional_lanes": exceptional_lanes,
        "unsupported_expected_forms_by_lane": selections_payload[
            "unsupported_expected_forms_by_lane"
        ],
        "comparisons": comparisons,
        "nonclaims": [
            "exposed development specificity diagnostic only",
            "no Gate field or EB behavior is qualified",
            "no model or Gate runtime was rerun",
            "no first-stage retrieval change",
            "fresh independent evidence remains required for any successor",
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
                "default_expected_forms": output["default_expected_forms"],
                "default_lane_count": len(default_lanes),
                "exceptional_lane_count": len(exceptional_lanes),
                "unsupported_expected_forms_by_lane": {
                    lane_id: values
                    for lane_id, values in output[
                        "unsupported_expected_forms_by_lane"
                    ].items()
                    if values
                },
                "comparisons": comparisons,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
