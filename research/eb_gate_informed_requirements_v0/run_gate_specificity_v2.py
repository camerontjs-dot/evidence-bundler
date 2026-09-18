from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CAPS = (0.005, 0.010, 0.020)
DEFAULT_EXPECTED = frozenset({"document_text", "measurement"})
SUPPORTED_FORMS = frozenset(
    {
        "document_text",
        "measurement",
        "event_record",
        "registry_entry",
        "authoritative_declaration",
    }
)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ordered_candidates(diag: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        list(diag["candidates"]),
        key=lambda row: (
            -float(row["semantic_score"]),
            int(row["rank"]),
            str(row["candidate_id"]),
        ),
    )


def fractional_score(expected: set[str], observed: set[str]) -> float | None:
    if not expected:
        return None
    return len(expected & observed) / len(expected)


def bounded_repair(
    ordered: list[dict[str, Any]],
    scores: dict[str, float | None],
    loss_cap: float,
) -> list[str]:
    selected = list(ordered[:3])
    outside = list(ordered[3:])
    if not selected or not outside:
        return [str(row["candidate_id"]) for row in selected]

    def score(row: dict[str, Any]) -> float:
        value = scores.get(str(row["candidate_id"]))
        return -1.0 if value is None else float(value)

    victim = min(
        selected,
        key=lambda row: (
            score(row),
            float(row["semantic_score"]),
            -int(row["rank"]),
            str(row["candidate_id"]),
        ),
    )
    challenger = max(
        outside,
        key=lambda row: (
            score(row),
            float(row["semantic_score"]),
            -int(row["rank"]),
            str(row["candidate_id"]),
        ),
    )
    if score(challenger) <= score(victim):
        return [str(row["candidate_id"]) for row in selected]

    loss = float(victim["semantic_score"]) - float(challenger["semantic_score"])
    if loss > loss_cap + 1e-12:
        return [str(row["candidate_id"]) for row in selected]

    replaced = [row for row in selected if row is not victim] + [challenger]
    replaced = sorted(
        replaced,
        key=lambda row: (
            -float(row["semantic_score"]),
            int(row["rank"]),
            str(row["candidate_id"]),
        ),
    )
    return [str(row["candidate_id"]) for row in replaced]


def score_candidates(
    ordered: list[dict[str, Any]], expected: set[str]
) -> dict[str, float | None]:
    return {
        str(row["candidate_id"]): fractional_score(
            expected, set(str(value) for value in row["loose_forms"])
        )
        for row in ordered
    }


def rotate_subset(ids: list[str]) -> dict[str, str]:
    ordered = sorted(ids)
    return {
        lane_id: ordered[(index + 1) % len(ordered)]
        for index, lane_id in enumerate(ordered)
    }


def selected_map(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        str(row["lane_id"]): [str(value) for value in row["selected_candidate_ids"]]
        for row in rows
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1-selections", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    source_path = Path(args.v1_selections)
    source = json.loads(source_path.read_text(encoding="utf-8"))
    diagnostics = source["diagnostics"]
    source_arms = source["selections"]

    semantic_rows = source_arms["control_semantic_top3_no_gates"]
    semantic = selected_map(semantic_rows)

    default_lanes = sorted(
        lane_id
        for lane_id, diag in diagnostics.items()
        if set(diag["expected_forms"]) == DEFAULT_EXPECTED
    )
    exceptional_lanes = sorted(set(diagnostics) - set(default_lanes))
    if len(default_lanes) != 22 or len(exceptional_lanes) != 8:
        raise AssertionError(
            f"expected 22 default and 8 exceptional lanes, got "
            f"{len(default_lanes)} and {len(exceptional_lanes)}"
        )

    rare_rotation = rotate_subset(exceptional_lanes)
    unsupported_by_lane = {
        lane_id: sorted(set(diag["expected_forms"]) - SUPPORTED_FORMS)
        for lane_id, diag in diagnostics.items()
    }

    selections: dict[str, list[dict[str, Any]]] = {
        "control_semantic_top3_no_gates": semantic_rows,
    }

    def add(arm: str, lane_id: str, selected: list[str]) -> None:
        selections.setdefault(arm, []).append(
            {"lane_id": lane_id, "selected_candidate_ids": selected}
        )

    for lane_id in sorted(diagnostics):
        diag = diagnostics[lane_id]
        ordered = ordered_candidates(diag)
        baseline = semantic[lane_id]
        true_expected = set(str(value) for value in diag["expected_forms"])
        clipped_expected = true_expected & SUPPORTED_FORMS
        shuffled_expected = (
            set(diagnostics[rare_rotation[lane_id]]["expected_forms"])
            if lane_id in rare_rotation
            else set(DEFAULT_EXPECTED)
        )
        shuffled_clipped = shuffled_expected & SUPPORTED_FORMS

        for cap in CAPS:
            label = f"{cap:.3f}"
            arms = {
                f"true_gate_fraction_cap_{label}": true_expected,
                f"constant_default_fraction_cap_{label}": set(DEFAULT_EXPECTED),
                f"true_gate_supported_only_cap_{label}": clipped_expected,
                f"rare_shuffled_gate_fraction_cap_{label}": shuffled_expected,
                f"rare_shuffled_supported_only_cap_{label}": shuffled_clipped,
                f"measurement_only_prior_cap_{label}": {"measurement"},
                f"document_only_prior_cap_{label}": {"document_text"},
            }
            for arm, expected in arms.items():
                chosen = bounded_repair(
                    ordered,
                    score_candidates(ordered, expected),
                    cap,
                )
                add(arm, lane_id, chosen)

            original_arm = source_arms[f"gate_fraction_loose_correct_cap_{label}"]
            original_selected = selected_map(original_arm)[lane_id]
            if selections[f"true_gate_fraction_cap_{label}"][-1][
                "selected_candidate_ids"
            ] != original_selected:
                raise AssertionError(
                    f"true Gate reproduction mismatch in {lane_id} at cap {label}"
                )

        if baseline != [str(row["candidate_id"]) for row in ordered[:3]]:
            raise AssertionError(f"semantic baseline mismatch in {lane_id}")

    default_true_equals_constant = {}
    for cap in CAPS:
        label = f"{cap:.3f}"
        true_map = selected_map(selections[f"true_gate_fraction_cap_{label}"])
        constant_map = selected_map(
            selections[f"constant_default_fraction_cap_{label}"]
        )
        default_true_equals_constant[label] = all(
            true_map[lane_id] == constant_map[lane_id]
            for lane_id in default_lanes
        )
        if not default_true_equals_constant[label]:
            raise AssertionError(
                f"default-lane true/constant selections diverged at cap {label}"
            )

    output = {
        "schema": "eb-gate-specificity-v2-selections",
        "classification": "EXPOSED_DEVELOPMENT_SPECIFICITY_FALSIFIER",
        "source_v1_selection_sha256": sha256_file(source_path),
        "source_authorities": source["authorities"],
        "caps": list(CAPS),
        "default_expected_forms": sorted(DEFAULT_EXPECTED),
        "supported_form_vocabulary": sorted(SUPPORTED_FORMS),
        "default_lanes": default_lanes,
        "exceptional_lanes": exceptional_lanes,
        "exceptional_lane_rotation": rare_rotation,
        "unsupported_expected_forms_by_lane": unsupported_by_lane,
        "default_true_equals_constant": default_true_equals_constant,
        "selections": {
            arm: rows for arm, rows in sorted(selections.items())
        },
        "nonclaims": [
            "exposed development specificity test only",
            "no gold is consumed by this program",
            "no model or Gate runtime is rerun",
            "no first-stage retrieval change",
            "no Gate field or EB behavior is qualified",
        ],
    }
    output["output_sha256"] = sha256_json(output)
    Path(args.out).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output_sha256": output["output_sha256"],
                "default_lane_count": len(default_lanes),
                "exceptional_lane_count": len(exceptional_lanes),
                "default_true_equals_constant": default_true_equals_constant,
                "unsupported_expected_forms_by_lane": {
                    lane: values
                    for lane, values in unsupported_by_lane.items()
                    if values
                },
                "arm_count": len(selections),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
