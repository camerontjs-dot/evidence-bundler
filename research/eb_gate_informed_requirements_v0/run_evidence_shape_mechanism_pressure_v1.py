from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from run_actual_gate_field_pressure import (
    NEG_RE,
    NUMBER_RE,
    POSTURE_BAD,
    UNIT_RE,
    bounded_repair,
    candidate_forms,
    field_truthy,
    flatten_strings,
    gate_result,
    load_lane_sources,
    semantic_model,
    semantic_order,
    semantic_score,
    sha256_file,
)

LOSS_CAPS = (0.0, 0.005, 0.01, 0.02, 0.05)

STRICT_MEASUREMENT_RE = re.compile(
    r"\b(?:measured|measurement|recorded|mean|median|average|rate|yield|capacity|"
    r"germination|depth|nitrate|lead|sulfur|runtime|wait time|completion|produced|"
    r"reached|retained|contained)\b",
    re.I,
)
STRICT_EVENT_RE = re.compile(r"\b(?:audit log|witness log|incident record|event record)\b", re.I)
STRICT_REGISTRY_RE = re.compile(
    r"\b(?:registry entry|registered|registrar|certificate|certified|database record)\b",
    re.I,
)
STRICT_DECLARATION_RE = re.compile(
    r"\b(?:report states|states that|declaration|policy states|code requires|"
    r"manual states|specification requires)\b",
    re.I,
)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def expected_forms(gate: dict[str, Any]) -> set[str]:
    return {
        value.strip().lower()
        for value in flatten_strings(gate["claim_profile"].get("expected_evidence_forms"))
        if value.strip() and value.strip().lower() not in {"unknown", "none", "not_applicable"}
    }


def strict_candidate_forms(text: str) -> set[str]:
    forms = {"document_text"}
    has_number_or_unit = bool(NUMBER_RE.search(text) or UNIT_RE.search(text))
    if has_number_or_unit and STRICT_MEASUREMENT_RE.search(text):
        forms.add("measurement")
    if STRICT_EVENT_RE.search(text):
        forms.add("event_record")
    if STRICT_REGISTRY_RE.search(text):
        forms.add("registry_entry")
    if STRICT_DECLARATION_RE.search(text):
        forms.add("authoritative_declaration")
    return forms


def pointwise_fraction(expected: set[str], observed: set[str]) -> float | None:
    if not expected:
        return None
    return len(expected & observed) / len(expected)


def pointwise_anyof(expected: set[str], observed: set[str]) -> float | None:
    if not expected:
        return None
    return 1.0 if expected & observed else 0.0


def generic_form_richness(observed: set[str]) -> float:
    return float(len(observed - {"document_text"}))


def score_map(
    ordered: list[dict[str, Any]],
    scorer: Callable[[dict[str, Any]], float | None],
) -> dict[str, float | None]:
    return {str(row["candidate_id"]): scorer(row) for row in ordered}


def forms_for(
    ordered: list[dict[str, Any]],
    classifier: Callable[[str], set[str]],
) -> dict[str, set[str]]:
    return {
        str(row["candidate_id"]): classifier(str(row["text"]))
        for row in ordered
    }


def semantic_loss(victim: dict[str, Any], challenger: dict[str, Any]) -> float:
    return float(victim["semantic_score"]) - float(challenger["semantic_score"])


def one_swap_set_repair(
    ordered: list[dict[str, Any]],
    *,
    objective: Callable[[list[dict[str, Any]]], float],
    loss_cap: float,
) -> list[str]:
    selected = list(ordered[:3])
    outside = list(ordered[3:])
    if not selected or not outside:
        return [str(row["candidate_id"]) for row in selected]

    current_objective = objective(selected)
    best: tuple[float, float, float, int, str, list[dict[str, Any]]] | None = None

    for victim_index, victim in enumerate(selected):
        for challenger in outside:
            loss = semantic_loss(victim, challenger)
            if loss > loss_cap + 1e-12:
                continue
            proposed = [
                challenger if index == victim_index else row
                for index, row in enumerate(selected)
            ]
            obj = objective(proposed)
            if obj <= current_objective + 1e-12:
                continue
            semantic_sum = sum(float(row["semantic_score"]) for row in proposed)
            key = (
                obj,
                semantic_sum,
                -max(loss, 0.0),
                -int(challenger["rank"]),
                str(challenger["candidate_id"]),
                proposed,
            )
            if best is None or key[:5] > best[:5]:
                best = key

    chosen = selected if best is None else best[5]
    chosen = sorted(
        chosen,
        key=lambda row: (-float(row["semantic_score"]), int(row["rank"]), str(row["candidate_id"])),
    )
    return [str(row["candidate_id"]) for row in chosen]


def gate_set_coverage_repair(
    ordered: list[dict[str, Any]],
    expected: set[str],
    form_map: dict[str, set[str]],
    loss_cap: float,
) -> list[str]:
    if not expected:
        return [str(row["candidate_id"]) for row in ordered[:3]]

    def objective(rows: list[dict[str, Any]]) -> float:
        covered: set[str] = set()
        for row in rows:
            covered |= form_map[str(row["candidate_id"])] & expected
        return len(covered) / len(expected)

    return one_swap_set_repair(ordered, objective=objective, loss_cap=loss_cap)


def generic_form_diversity_repair(
    ordered: list[dict[str, Any]],
    form_map: dict[str, set[str]],
    loss_cap: float,
) -> list[str]:
    def objective(rows: list[dict[str, Any]]) -> float:
        covered: set[str] = set()
        for row in rows:
            covered |= form_map[str(row["candidate_id"])] - {"document_text"}
        return float(len(covered))

    return one_swap_set_repair(ordered, objective=objective, loss_cap=loss_cap)


def generic_source_diversity_repair(
    ordered: list[dict[str, Any]], loss_cap: float
) -> list[str]:
    def objective(rows: list[dict[str, Any]]) -> float:
        return float(len({str(row["source_id"]) for row in rows}))

    return one_swap_set_repair(ordered, objective=objective, loss_cap=loss_cap)


def apply_after_selection(
    ordered: list[dict[str, Any]],
    selected_ids: list[str],
    compat: dict[str, float | None],
    loss_cap: float,
) -> list[str]:
    selected_set = set(selected_ids)
    by_id = {str(row["candidate_id"]): row for row in ordered}
    synthetic = [by_id[cid] for cid in selected_ids] + [
        row for row in ordered if str(row["candidate_id"]) not in selected_set
    ]
    return bounded_repair(synthetic, compat, loss_cap)


def rotate_lane_ids(lane_ids: list[str]) -> dict[str, str]:
    ordered = sorted(lane_ids)
    return {
        lane_id: ordered[(index + 1) % len(ordered)]
        for index, lane_id in enumerate(ordered)
    }


def run() -> dict[str, Any]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claims", required=True)
    parser.add_argument("--sources", required=True)
    parser.add_argument("--pools", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    claims = json.loads(Path(args.claims).read_text(encoding="utf-8"))
    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    pools = json.loads(Path(args.pools).read_text(encoding="utf-8"))

    claims_by_lane = {str(row["lane_id"]): row for row in claims["lanes"]}
    sources_by_lane = load_lane_sources(sources)
    pools_by_lane = {str(row["lane_id"]): row for row in pools["lanes"]}
    lane_ids = sorted(claims_by_lane)
    if lane_ids != sorted(sources_by_lane) or lane_ids != sorted(pools_by_lane):
        raise RuntimeError("claim/source/pool lane identities do not match")

    tokenizer, model = semantic_model()
    gates: dict[str, dict[str, Any]] = {}
    ordered_by_lane: dict[str, list[dict[str, Any]]] = {}
    diagnostics: dict[str, Any] = {}

    for lane_id in lane_ids:
        claim = str(claims_by_lane[lane_id]["claim"])
        gate = gate_result(claim, lane_id, sources_by_lane[lane_id])
        rows: list[dict[str, Any]] = []
        for candidate in pools_by_lane[lane_id]["candidates"]:
            row = dict(candidate)
            row["semantic_score"] = semantic_score(
                tokenizer, model, claim, str(candidate["text"])
            )
            rows.append(row)
        ordered = semantic_order(rows)
        gates[lane_id] = gate
        ordered_by_lane[lane_id] = ordered

        loose = forms_for(ordered, candidate_forms)
        strict = forms_for(ordered, strict_candidate_forms)
        diagnostics[lane_id] = {
            "expected_forms": sorted(expected_forms(gate)),
            "gate_negation": gate["claim_profile"].get("negation"),
            "candidates": [
                {
                    "candidate_id": str(row["candidate_id"]),
                    "rank": int(row["rank"]),
                    "source_id": str(row["source_id"]),
                    "semantic_score": float(row["semantic_score"]),
                    "loose_forms": sorted(loose[str(row["candidate_id"])]),
                    "strict_forms": sorted(strict[str(row["candidate_id"])]),
                }
                for row in ordered
            ],
        }

    rotation = rotate_lane_ids(lane_ids)
    selections: dict[str, list[dict[str, Any]]] = {}
    replacement_stats: dict[str, Counter[str]] = defaultdict(Counter)

    def add(arm: str, lane_id: str, ids: list[str], baseline: list[str]) -> None:
        selections.setdefault(arm, []).append(
            {"lane_id": lane_id, "selected_candidate_ids": ids}
        )
        replacement_stats[arm]["changed_lanes"] += int(ids != baseline)

    for lane_id in lane_ids:
        ordered = ordered_by_lane[lane_id]
        baseline = [str(row["candidate_id"]) for row in ordered[:3]]
        rank_top3 = [
            str(row["candidate_id"])
            for row in sorted(ordered, key=lambda row: int(row["rank"]))[:3]
        ]
        add("control_bm25_rank_top3_no_gates", lane_id, rank_top3, baseline)
        add("control_semantic_top3_no_gates", lane_id, baseline, baseline)
        add("control_gate_present_ignored", lane_id, baseline, baseline)

        correct_expected = expected_forms(gates[lane_id])
        shuffled_expected = expected_forms(gates[rotation[lane_id]])

        loose_map = forms_for(ordered, candidate_forms)
        strict_map = forms_for(ordered, strict_candidate_forms)

        correct_neg = field_truthy(gates[lane_id]["claim_profile"].get("negation"))
        shuffled_neg = field_truthy(
            gates[rotation[lane_id]]["claim_profile"].get("negation")
        )
        neg_correct = {
            str(row["candidate_id"]): (
                None
                if correct_neg is None
                else 1.0
                if bool(NEG_RE.search(str(row["text"]))) == correct_neg
                else 0.0
            )
            for row in ordered
        }
        neg_shuffled = {
            str(row["candidate_id"]): (
                None
                if shuffled_neg is None
                else 1.0
                if bool(NEG_RE.search(str(row["text"]))) == shuffled_neg
                else 0.0
            )
            for row in ordered
        }
        posture_scores = {
            str(row["candidate_id"]): 0.0 if POSTURE_BAD.search(str(row["text"])) else 1.0
            for row in ordered
        }

        for cap in LOSS_CAPS:
            cap_label = f"{cap:.3f}"

            gate_pointwise_specs = (
                ("gate_fraction_loose", loose_map, pointwise_fraction),
                ("gate_anyof_loose", loose_map, pointwise_anyof),
                ("gate_fraction_strict", strict_map, pointwise_fraction),
                ("gate_anyof_strict", strict_map, pointwise_anyof),
            )
            for prefix, form_map, matcher in gate_pointwise_specs:
                correct_scores = {
                    cid: matcher(correct_expected, forms) for cid, forms in form_map.items()
                }
                shuffled_scores = {
                    cid: matcher(shuffled_expected, forms) for cid, forms in form_map.items()
                }
                add(
                    f"{prefix}_correct_cap_{cap_label}",
                    lane_id,
                    bounded_repair(ordered, correct_scores, cap),
                    baseline,
                )
                add(
                    f"{prefix}_shuffled_cap_{cap_label}",
                    lane_id,
                    bounded_repair(ordered, shuffled_scores, cap),
                    baseline,
                )

            for prefix, form_map in (
                ("gate_set_coverage_loose", loose_map),
                ("gate_set_coverage_strict", strict_map),
            ):
                add(
                    f"{prefix}_correct_cap_{cap_label}",
                    lane_id,
                    gate_set_coverage_repair(
                        ordered, correct_expected, form_map, cap
                    ),
                    baseline,
                )
                add(
                    f"{prefix}_shuffled_cap_{cap_label}",
                    lane_id,
                    gate_set_coverage_repair(
                        ordered, shuffled_expected, form_map, cap
                    ),
                    baseline,
                )

            for prefix, form_map in (
                ("generic_form_richness_loose", loose_map),
                ("generic_form_richness_strict", strict_map),
            ):
                richness_scores = {
                    cid: generic_form_richness(forms) for cid, forms in form_map.items()
                }
                add(
                    f"{prefix}_cap_{cap_label}",
                    lane_id,
                    bounded_repair(ordered, richness_scores, cap),
                    baseline,
                )

            for prefix, form_map in (
                ("generic_form_diversity_loose", loose_map),
                ("generic_form_diversity_strict", strict_map),
            ):
                add(
                    f"{prefix}_cap_{cap_label}",
                    lane_id,
                    generic_form_diversity_repair(ordered, form_map, cap),
                    baseline,
                )

            add(
                f"generic_source_diversity_cap_{cap_label}",
                lane_id,
                generic_source_diversity_repair(ordered, cap),
                baseline,
            )

            current_shape = bounded_repair(
                ordered,
                {
                    cid: pointwise_fraction(correct_expected, forms)
                    for cid, forms in loose_map.items()
                },
                cap,
            )
            shuffled_shape = bounded_repair(
                ordered,
                {
                    cid: pointwise_fraction(shuffled_expected, forms)
                    for cid, forms in loose_map.items()
                },
                cap,
            )
            add(
                f"gate_fraction_loose_then_negation_correct_cap_{cap_label}",
                lane_id,
                apply_after_selection(ordered, current_shape, neg_correct, cap),
                baseline,
            )
            add(
                f"gate_fraction_loose_then_negation_shuffled_cap_{cap_label}",
                lane_id,
                apply_after_selection(ordered, shuffled_shape, neg_shuffled, cap),
                baseline,
            )
            add(
                f"gate_fraction_loose_then_posture_cap_{cap_label}",
                lane_id,
                apply_after_selection(ordered, current_shape, posture_scores, cap),
                baseline,
            )
            add(
                f"gate_fraction_loose_then_source_diversity_cap_{cap_label}",
                lane_id,
                one_swap_set_repair(
                    [
                        next(row for row in ordered if str(row["candidate_id"]) == cid)
                        for cid in current_shape
                    ]
                    + [
                        row
                        for row in ordered
                        if str(row["candidate_id"]) not in set(current_shape)
                    ],
                    objective=lambda rows: float(
                        len({str(row["source_id"]) for row in rows})
                    ),
                    loss_cap=cap,
                ),
                baseline,
            )

    if selections["control_semantic_top3_no_gates"] != selections["control_gate_present_ignored"]:
        raise AssertionError("Gate-present ignored placebo differs from semantic no-Gate control")

    expected_distribution = Counter()
    for lane in diagnostics.values():
        expected_distribution[canonical(lane["expected_forms"])] += 1

    output = {
        "schema": "eb-evidence-shape-mechanism-pressure-v1-selections",
        "classification": "EXPOSED_DEVELOPMENT_MECHANISM_PRESSURE",
        "authorities": {
            "proposition_authoring_subject": "e29a165b682d060f5dc2a0f3c7d64a7f29b172b4",
            "claims_sha256": sha256_file(Path(args.claims)),
            "sources_sha256": sha256_file(Path(args.sources)),
            "pools_sha256": sha256_file(Path(args.pools)),
            "semantic_model": "cross-encoder/ms-marco-MiniLM-L6-v2",
            "semantic_revision": "233902d25c440f23af6f7d6e94d2946bac0bee0a",
        },
        "controls": {
            "bm25": "control_bm25_rank_top3_no_gates",
            "semantic": "control_semantic_top3_no_gates",
            "placebo": "control_gate_present_ignored",
        },
        "loss_caps": list(LOSS_CAPS),
        "shuffled_lane_mapping": rotation,
        "expected_form_distribution": dict(sorted(expected_distribution.items())),
        "replacement_stats": {
            arm: dict(counter) for arm, counter in sorted(replacement_stats.items())
        },
        "diagnostics": diagnostics,
        "selections": {arm: rows for arm, rows in sorted(selections.items())},
        "nonclaims": [
            "exposed development mechanism pressure only",
            "does not qualify Gate fields or EB behavior",
            "first-stage retrieval is unchanged",
            "gold is not consumed by this selection program",
        ],
    }
    output["output_sha256"] = sha256_json(output)
    Path(args.out).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "arm_count": len(selections),
                "expected_form_distribution": output["expected_form_distribution"],
                "output_sha256": output["output_sha256"],
                "changed_lane_counts": {
                    arm: stats["changed_lanes"]
                    for arm, stats in sorted(output["replacement_stats"].items())
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return output


if __name__ == "__main__":
    run()
