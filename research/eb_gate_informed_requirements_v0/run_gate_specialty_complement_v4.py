from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CAPS = (0.005, 0.010, 0.020)
DEFAULT_FORMS = frozenset({"document_text", "measurement"})
SPECIALTY_FORMS = frozenset(
    {"authoritative_declaration", "event_record", "registry_entry"}
)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ordered(diag: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        diag["candidates"],
        key=lambda row: (
            -float(row["semantic_score"]),
            int(row["rank"]),
            str(row["candidate_id"]),
        ),
    )


def score_fraction(expected: set[str], observed: set[str]) -> float | None:
    if not expected:
        return None
    return len(expected & observed) / len(expected)


def score_any(expected: set[str], observed: set[str]) -> float | None:
    if not expected:
        return None
    return 1.0 if expected & observed else 0.0


def bounded_repair(
    rows: list[dict[str, Any]],
    scores: dict[str, float | None],
    cap: float,
) -> list[str]:
    selected = list(rows[:3])
    outside = list(rows[3:])

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
    if loss > cap + 1e-12:
        return [str(row["candidate_id"]) for row in selected]

    chosen = [row for row in selected if row is not victim] + [challenger]
    chosen = sorted(
        chosen,
        key=lambda row: (
            -float(row["semantic_score"]),
            int(row["rank"]),
            str(row["candidate_id"]),
        ),
    )
    return [str(row["candidate_id"]) for row in chosen]


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
    semantic = selected_map(source_arms["control_semantic_top3_no_gates"])

    exceptional = sorted(
        lane_id
        for lane_id, diag in diagnostics.items()
        if set(diag["expected_forms"]) != DEFAULT_FORMS
    )
    if len(exceptional) != 8:
        raise AssertionError(f"expected 8 exceptional lanes, got {len(exceptional)}")

    true_specialty_by_lane: dict[str, set[str]] = {}
    complement_by_lane: dict[str, set[str]] = {}
    wrong_only_by_lane: dict[str, set[str]] = {}

    for lane_id in exceptional:
        true_specialty = set(diagnostics[lane_id]["expected_forms"]) & SPECIALTY_FORMS
        if not true_specialty:
            raise AssertionError(f"{lane_id}: exceptional lane has no supported specialty")
        complement = set(SPECIALTY_FORMS) - true_specialty
        if not complement:
            raise AssertionError(f"{lane_id}: no non-true specialty remains")
        true_specialty_by_lane[lane_id] = true_specialty
        complement_by_lane[lane_id] = complement
        wrong_only_by_lane[lane_id] = {sorted(complement)[0]}

    selections: dict[str, list[dict[str, Any]]] = {
        "control_semantic_top3_no_gates": source_arms[
            "control_semantic_top3_no_gates"
        ]
    }

    def add(arm: str, lane_id: str, chosen: list[str]) -> None:
        selections.setdefault(arm, []).append(
            {"lane_id": lane_id, "selected_candidate_ids": chosen}
        )

    for lane_id in sorted(diagnostics):
        diag = diagnostics[lane_id]
        rows = ordered(diag)
        baseline = semantic[lane_id]
        observed = {
            str(row["candidate_id"]): set(str(value) for value in row["loose_forms"])
            for row in rows
        }

        true_specialty = true_specialty_by_lane.get(lane_id, set())
        complement = complement_by_lane.get(lane_id, set())
        wrong_only = wrong_only_by_lane.get(lane_id, set())

        for cap in CAPS:
            label = f"{cap:.3f}"
            expected_sets = {
                f"true_specialty_fraction_cap_{label}": true_specialty,
                f"true_specialty_anyof_cap_{label}": true_specialty,
                f"complement_fraction_cap_{label}": complement,
                f"complement_anyof_cap_{label}": complement,
                f"wrong_only_cap_{label}": wrong_only,
                f"generic_union_fraction_cap_{label}": set(SPECIALTY_FORMS),
                f"generic_union_anyof_cap_{label}": set(SPECIALTY_FORMS),
                f"authoritative_only_cap_{label}": {"authoritative_declaration"},
                f"event_only_cap_{label}": {"event_record"},
                f"registry_only_cap_{label}": {"registry_entry"},
            }

            for arm, expected in expected_sets.items():
                if lane_id not in exceptional and arm not in {
                    f"authoritative_only_cap_{label}",
                    f"event_only_cap_{label}",
                    f"registry_only_cap_{label}",
                    f"generic_union_fraction_cap_{label}",
                    f"generic_union_anyof_cap_{label}",
                }:
                    add(arm, lane_id, baseline)
                    continue

                matcher = (
                    score_any
                    if "anyof" in arm or arm.startswith("wrong_only")
                    or arm.endswith("_only_cap_" + label)
                    else score_fraction
                )
                scores = {
                    candidate_id: matcher(expected, forms)
                    for candidate_id, forms in observed.items()
                }
                if not expected:
                    chosen = baseline
                else:
                    chosen = bounded_repair(rows, scores, cap)
                add(arm, lane_id, chosen)

            original = selected_map(
                source_arms[f"gate_fraction_loose_correct_cap_{label}"]
            )[lane_id]
            current = selections[f"true_specialty_fraction_cap_{label}"][-1][
                "selected_candidate_ids"
            ]
            if lane_id in exceptional and current != original:
                raise AssertionError(
                    f"true specialty reproduction mismatch {lane_id} {label}"
                )

    output = {
        "schema": "eb-gate-specialty-complement-v4-selections",
        "classification": "EXPOSED_DEVELOPMENT_COMPLEMENT_FALSIFIER",
        "source_v1_selection_sha256": sha256_file(source_path),
        "caps": list(CAPS),
        "exceptional_lanes": exceptional,
        "true_specialty_by_lane": {
            lane_id: sorted(values)
            for lane_id, values in sorted(true_specialty_by_lane.items())
        },
        "complement_by_lane": {
            lane_id: sorted(values)
            for lane_id, values in sorted(complement_by_lane.items())
        },
        "wrong_only_by_lane": {
            lane_id: sorted(values)
            for lane_id, values in sorted(wrong_only_by_lane.items())
        },
        "selections": {arm: rows for arm, rows in sorted(selections.items())},
        "nonclaims": [
            "exposed development complement falsifier only",
            "no gold consumed by this selector program",
            "no model or Gate runtime rerun",
            "no first-stage retrieval change",
            "no Gate field or EB behavior qualified",
        ],
    }
    output["output_sha256"] = hashlib.sha256(
        canonical(output).encode("utf-8")
    ).hexdigest()
    Path(args.out).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output_sha256": output["output_sha256"],
                "exceptional_lanes": exceptional,
                "true_specialty_by_lane": output["true_specialty_by_lane"],
                "complement_by_lane": output["complement_by_lane"],
                "wrong_only_by_lane": output["wrong_only_by_lane"],
                "arm_count": len(selections),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
