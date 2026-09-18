from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CAPS = (0.005, 0.010, 0.020)
DEFAULT_FORMS = frozenset({"document_text", "measurement"})
SUPPORTED_FORMS = frozenset(
    {"document_text", "measurement", "event_record", "registry_entry", "authoritative_declaration"}
)
SPECIALTY_FORMS = frozenset({"event_record", "registry_entry", "authoritative_declaration"})


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def score_fraction(expected: set[str], observed: set[str]) -> float | None:
    if not expected:
        return None
    return len(expected & observed) / len(expected)


def score_any(expected: set[str], observed: set[str]) -> float | None:
    if not expected:
        return None
    return 1.0 if expected & observed else 0.0


def ordered(diag: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        diag["candidates"],
        key=lambda row: (-float(row["semantic_score"]), int(row["rank"]), str(row["candidate_id"])),
    )


def bounded_repair(
    rows: list[dict[str, Any]],
    scores: dict[str, float | None],
    cap: float,
) -> list[str]:
    selected = list(rows[:3])
    outside = list(rows[3:])

    def s(row: dict[str, Any]) -> float:
        value = scores.get(str(row["candidate_id"]))
        return -1.0 if value is None else float(value)

    victim = min(selected, key=lambda row: (s(row), float(row["semantic_score"]), -int(row["rank"])))
    challenger = max(outside, key=lambda row: (s(row), float(row["semantic_score"]), -int(row["rank"])))
    if s(challenger) <= s(victim):
        return [str(row["candidate_id"]) for row in selected]
    loss = float(victim["semantic_score"]) - float(challenger["semantic_score"])
    if loss > cap + 1e-12:
        return [str(row["candidate_id"]) for row in selected]
    selected = [row for row in selected if row is not victim] + [challenger]
    selected = sorted(
        selected,
        key=lambda row: (-float(row["semantic_score"]), int(row["rank"]), str(row["candidate_id"])),
    )
    return [str(row["candidate_id"]) for row in selected]


def selection_map(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {str(row["lane_id"]): [str(x) for x in row["selected_candidate_ids"]] for row in rows}


def rotate(ids: list[str]) -> dict[str, str]:
    ordered_ids = sorted(ids)
    return {lane: ordered_ids[(i + 1) % len(ordered_ids)] for i, lane in enumerate(ordered_ids)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1-selections", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    source_path = Path(args.v1_selections)
    source = json.loads(source_path.read_text(encoding="utf-8"))
    diagnostics = source["diagnostics"]
    source_arms = source["selections"]
    semantic = selection_map(source_arms["control_semantic_top3_no_gates"])

    exceptional = sorted(
        lane for lane, diag in diagnostics.items()
        if set(diag["expected_forms"]) != DEFAULT_FORMS
    )
    default = sorted(set(diagnostics) - set(exceptional))
    if len(exceptional) != 8 or len(default) != 22:
        raise AssertionError("unexpected default/exceptional split")

    rare_rotation = rotate(exceptional)
    union_specialty: set[str] = set()
    specialty_by_lane: dict[str, set[str]] = {}
    for lane in exceptional:
        specialty = (set(diagnostics[lane]["expected_forms"]) & SUPPORTED_FORMS) - DEFAULT_FORMS
        specialty_by_lane[lane] = specialty
        union_specialty |= specialty

    selections: dict[str, list[dict[str, Any]]] = {
        "control_semantic_top3_no_gates": source_arms["control_semantic_top3_no_gates"]
    }

    def add(arm: str, lane: str, ids: list[str]) -> None:
        selections.setdefault(arm, []).append({"lane_id": lane, "selected_candidate_ids": ids})

    for lane in sorted(diagnostics):
        diag = diagnostics[lane]
        rows = ordered(diag)
        baseline = semantic[lane]
        observed = {
            str(row["candidate_id"]): set(str(x) for x in row["loose_forms"])
            for row in rows
        }
        true_full = set(str(x) for x in diag["expected_forms"]) & SUPPORTED_FORMS
        true_specialty = specialty_by_lane.get(lane, set())
        shuffled_specialty = (
            specialty_by_lane[rare_rotation[lane]] if lane in rare_rotation else set()
        )

        for cap in CAPS:
            label=f"{cap:.3f}"
            arms: dict[str, dict[str, float | None]] = {}

            arms[f"true_full_gate_cap_{label}"] = {
                cid: score_fraction(true_full, forms) for cid, forms in observed.items()
            }
            arms[f"true_specialty_fraction_cap_{label}"] = {
                cid: score_fraction(true_specialty, forms) for cid, forms in observed.items()
            }
            arms[f"true_specialty_anyof_cap_{label}"] = {
                cid: score_any(true_specialty, forms) for cid, forms in observed.items()
            }
            arms[f"rare_shuffled_specialty_fraction_cap_{label}"] = {
                cid: score_fraction(shuffled_specialty, forms) for cid, forms in observed.items()
            }
            arms[f"generic_any_specialty_cap_{label}"] = {
                cid: (1.0 if (forms & SPECIALTY_FORMS) else 0.0) for cid, forms in observed.items()
            }
            arms[f"generic_union_specialty_fraction_cap_{label}"] = {
                cid: score_fraction(union_specialty, forms) for cid, forms in observed.items()
            }

            for removed in sorted(SPECIALTY_FORMS):
                ablated = true_specialty - {removed}
                arms[f"ablate_{removed}_cap_{label}"] = {
                    cid: score_fraction(ablated, forms) for cid, forms in observed.items()
                }

            for arm, scores in arms.items():
                chosen = baseline if not any(v is not None for v in scores.values()) else bounded_repair(rows, scores, cap)
                add(arm, lane, chosen)

            original = selection_map(source_arms[f"gate_fraction_loose_correct_cap_{label}"])[lane]
            current = selections[f"true_full_gate_cap_{label}"][-1]["selected_candidate_ids"]
            if current != original:
                raise AssertionError(f"full Gate reproduction mismatch {lane} {label}")

    output = {
        "schema":"eb-gate-specialty-ablation-v3-selections",
        "classification":"EXPOSED_DEVELOPMENT_SPECIALTY_ABLATION",
        "source_v1_selection_sha256":sha256_file(source_path),
        "default_lanes":default,
        "exceptional_lanes":exceptional,
        "specialty_by_lane":{lane:sorted(values) for lane,values in specialty_by_lane.items()},
        "union_specialty":sorted(union_specialty),
        "rare_rotation":rare_rotation,
        "caps":list(CAPS),
        "selections":{arm:rows for arm,rows in sorted(selections.items())},
        "nonclaims":[
            "exposed development ablation only",
            "no gold consumed by this program",
            "no model or Gate runtime rerun",
            "no first-stage retrieval change",
        ],
    }
    output["output_sha256"]=hashlib.sha256(canonical(output).encode("utf-8")).hexdigest()
    Path(args.out).write_text(json.dumps(output,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "output_sha256":output["output_sha256"],
        "exceptional_lanes":exceptional,
        "specialty_by_lane":output["specialty_by_lane"],
        "union_specialty":output["union_specialty"],
        "arm_count":len(selections),
    },indent=2,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
