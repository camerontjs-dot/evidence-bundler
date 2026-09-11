#!/usr/bin/env python3
"""Evaluate frozen EB V1 K=7 runtime receipts after the gold firewall opens."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

IMPLEMENTATION_SHA = "c4e3f97ec8f0bd36180954c3aa382418925bf947"
IMPLEMENTATION_TREE = "1d254e38cb0e174635efc7687c2b0ab091aa52b3"
EB_FIXTURE_SHA = "dd4fb2b89f351fbdcd8b08e48dd9d7d1f10c2d05"
CAL_DECOY_SHA = "7a46d61585f868a2e904f870528f605fb06772ea"
CONTRACT_A_RELEASE = "529c92b49a34d5c610618551a8737f019f9fa332"
CONTRACT_A_VALIDATOR_BLOB = "42e5f5b3bf38d677445e9d01ea130ba604e53409"
PREDECESSOR_RUN = 34608721684
PREDECESSOR_ARTIFACT = 10267561504
PREDECESSOR_DIGEST = "sha256:86283d446726f4c5d430d87bfec642427a099575b9f7e1de9835f74b2060b4f9"
EXPECTED_BASELINE_MISSING = {
    "C03-P2": "candidate_pool",
    "C06-P1": "retention",
    "C08-P2": "admission",
    "RET-AP-P6": "candidate_pool",
}
STAGE_ORDINAL = {"candidate_pool": 0, "retention": 1, "admission": 2, None: 3}
TERMINAL = {
    "K7_NOT_FALSIFIED_AS_SMALLEST_BOUNDED_REMEDY",
    "FIXED_K_WIDENING_REJECTED_ON_QUALIFICATION_SET",
    "K7_RETENTION_REMEDY_FALSIFIED",
    "INCONCLUSIVE_GOLD_COVERAGE",
    "APPARATUS_INVALID",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_bytes(value))


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def cases_by_id(receipt: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["case_id"]): row for row in receipt["cases"]}


def candidate_sets(case: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    candidate: set[str] = set()
    retained: set[str] = set()
    admitted: set[str] = set()
    for row in case["candidate_rows"]:
        evidence_id = row.get("evidence_id")
        if evidence_id is None:
            continue
        evidence_id = str(evidence_id)
        candidate.add(evidence_id)
        if row["selection_state"] == "retained":
            retained.add(evidence_id)
        if row["admission_state"] == "accepted":
            admitted.add(evidence_id)
    return candidate, retained, admitted


def missing_stage(case: dict[str, Any], evidence_id: str) -> str | None:
    candidate, retained, admitted = candidate_sets(case)
    if evidence_id not in candidate:
        return "candidate_pool"
    if evidence_id not in retained:
        return "retention"
    if evidence_id not in admitted:
        return "admission"
    return None


def build_required_map(
    evaluator_gold: dict[str, Any], runtime_admission: dict[str, Any]
) -> tuple[dict[str, set[str]], dict[str, dict[str, str]]]:
    per_case_required: dict[str, set[str]] = {}
    per_case_prop: dict[str, dict[str, str]] = {}
    for case_id, gold in evaluator_gold["cases"].items():
        required = {str(item) for item in gold["required"]}
        per_case_required[case_id] = required
        prop_mapping: dict[str, str] = {}
        admission_case = runtime_admission["cases"].get(case_id, {})
        assigned: set[str] = set()
        propositions_without_required: list[str] = []
        for proposition_id, state in admission_case.items():
            matches = [
                str(evidence_id)
                for decision in ("accepted", "needs-review")
                for evidence_id in state.get(decision, [])
                if str(evidence_id) in required
            ]
            if matches:
                for evidence_id in matches:
                    prop_mapping[f"{proposition_id}|{evidence_id}"] = "explicit_runtime_admission"
                    assigned.add(evidence_id)
            else:
                propositions_without_required.append(str(proposition_id))
        unassigned = sorted(required - assigned)
        if len(unassigned) == 1 and len(propositions_without_required) == 1:
            prop_mapping[f"{propositions_without_required[0]}|{unassigned[0]}"] = (
                "unique_missing_required_fixture_pair"
            )
        per_case_prop[case_id] = prop_mapping
    return per_case_required, per_case_prop


def duplicate_nonrequired(gold_case: dict[str, Any]) -> set[str]:
    required = {str(item) for item in gold_case["required"]}
    out: set[str] = set()
    for group in gold_case.get("duplicates", []):
        for evidence_id in group:
            evidence_id = str(evidence_id)
            if evidence_id not in required:
                out.add(evidence_id)
    return out


def classify_relationship(
    *,
    case_id: str,
    proposition_id: str,
    evidence_id: str | None,
    evaluator_gold: dict[str, Any],
    required_prop_map: dict[str, dict[str, str]],
) -> tuple[str, str]:
    if evidence_id is None:
        return "unresolved_not_safely_classifiable", "no_legacy_evidence_identity"

    if case_id == "RETRIEVAL_APERTURE":
        if proposition_id == "RETRIEVAL_APERTURE:child:1":
            if evidence_id == "RET-AP-P6":
                return "required", "frozen_decoy_required_true_support"
            if evidence_id in {
                "RET-AP-P1",
                "RET-AP-P2",
                "RET-AP-P3",
                "RET-AP-P4",
                "RET-AP-P5",
            }:
                return (
                    "known_non_required_or_distractor",
                    "frozen_campaign_five_lexical_decoys",
                )
            return (
                "unresolved_not_safely_classifiable",
                "decoy_control_relation_not_explicitly_adjudicated",
            )
        if proposition_id == "RETRIEVAL_APERTURE:child:2" and evidence_id == "RET-AP-P7":
            return "required", "frozen_decoy_control_required"
        return (
            "unresolved_not_safely_classifiable",
            "decoy_cross_lane_relation_not_explicitly_adjudicated",
        )

    gold_case = evaluator_gold["cases"][case_id]
    relation_key = f"{proposition_id}|{evidence_id}"
    if relation_key in required_prop_map[case_id]:
        return "required", required_prop_map[case_id][relation_key]
    if evidence_id in {str(item) for item in gold_case.get("hard_negative", [])}:
        return "known_non_required_or_distractor", "frozen_gold_hard_negative"
    if evidence_id in duplicate_nonrequired(gold_case):
        return "known_non_required_or_distractor", "frozen_gold_nonrequired_duplicate"
    return (
        "unresolved_not_safely_classifiable",
        "sparse_gold_does_not_authorize_relation_judgment",
    )


def lane_key(case_id: str, proposition_id: str) -> str:
    return f"{case_id}|{proposition_id}"


def retained_by_lane(receipt: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for case in receipt["cases"]:
        case_id = str(case["case_id"])
        for row in case["candidate_rows"]:
            if row["selection_state"] != "retained":
                continue
            key = lane_key(case_id, str(row["proposition_id"]))
            out.setdefault(key, []).append(row)
    for rows in out.values():
        rows.sort(key=lambda row: int(row["rank"]))
    return out


def all_lanes(receipt: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for case in receipt["cases"]:
        for target in case["primary_targets"]:
            keys.append(lane_key(str(case["case_id"]), str(target["proposition_id"])))
    return sorted(keys)


def ordering_comparison(
    baseline: dict[str, Any],
    treatment: dict[str, Any],
    predecessor: dict[str, Any],
) -> dict[str, Any]:
    base_cases = cases_by_id(baseline)
    treatment_cases = cases_by_id(treatment)
    lanes: list[dict[str, Any]] = []
    all_ok = True
    for case_id in sorted(base_cases):
        braw = base_cases[case_id]["raw_retrieval"]
        traw = treatment_cases[case_id]["raw_retrieval"]
        propositions = sorted(
            {str(row["proposition_id"]) for row in braw}
            | {str(row["proposition_id"]) for row in traw}
        )
        for proposition_id in propositions:
            b = [row for row in braw if row["proposition_id"] == proposition_id]
            t = [row for row in traw if row["proposition_id"] == proposition_id]
            prefix = t[: len(b)]
            fields = (
                "rank",
                "score",
                "source_id",
                "char_start",
                "char_end",
                "text",
                "evidence_id",
            )
            prefix_equal = len(prefix) == len(b) and all(
                all(left[field] == right[field] for field in fields)
                for left, right in zip(b, prefix, strict=True)
            )
            all_ok = all_ok and prefix_equal
            lanes.append(
                {
                    "case_id": case_id,
                    "proposition_id": proposition_id,
                    "baseline_count": len(b),
                    "treatment_count": len(t),
                    "baseline_is_exact_treatment_prefix": prefix_equal,
                    "baseline": b,
                    "treatment": t,
                }
            )

    package_match = all(
        bool(case["package_order_matches_raw"]) for case in treatment["cases"]
    )

    def decoy_score_rows(receipt: dict[str, Any]) -> list[dict[str, Any]]:
        case = cases_by_id(receipt)["RETRIEVAL_APERTURE"]
        return [
            {
                "proposition_id": row["proposition_id"],
                "source_id": row["source_id"],
                "evidence_id": row["evidence_id"],
                "rank": row["rank"],
                "score": row["score"],
            }
            for row in case["raw_retrieval"]
        ]

    baseline_decoy_matches_predecessor = (
        decoy_score_rows(baseline)
        == predecessor["profiles"]["5/3"]["decoy"]["score_diagnostics"]
    )
    treatment_decoy_matches_predecessor_depth10 = (
        decoy_score_rows(treatment)
        == predecessor["profiles"]["10/6"]["decoy"]["score_diagnostics"]
    )
    return {
        "schema": "eb-v1-k7-candidate-ordering-comparison-v1",
        "baseline_prefix_matches_treatment": all_ok,
        "treatment_package_order_matches_same_depth10_raw_retrieval": package_match,
        "baseline_decoy_order_and_scores_match_frozen_predecessor_5_3": (
            baseline_decoy_matches_predecessor
        ),
        "treatment_decoy_order_and_scores_match_frozen_predecessor_depth10": (
            treatment_decoy_matches_predecessor_depth10
        ),
        "scores_preserved_diagnostically_only": True,
        "bm25_score_added_to_package_contract": False,
        "lanes": lanes,
    }


def required_stage_comparison(
    baseline: dict[str, Any], treatment: dict[str, Any], evaluator_gold: dict[str, Any]
) -> dict[str, Any]:
    bcases = cases_by_id(baseline)
    tcases = cases_by_id(treatment)
    required: list[tuple[str, str]] = []
    for case_id, gold in sorted(evaluator_gold["cases"].items()):
        for evidence_id in gold["required"]:
            required.append((case_id, str(evidence_id)))
    required.extend(
        [
            ("RETRIEVAL_APERTURE", "RET-AP-P6"),
            ("RETRIEVAL_APERTURE", "RET-AP-P7"),
        ]
    )
    rows: list[dict[str, Any]] = []
    regressions: list[dict[str, Any]] = []
    for case_id, evidence_id in required:
        before = missing_stage(bcases[case_id], evidence_id)
        after = missing_stage(tcases[case_id], evidence_id)
        regression = STAGE_ORDINAL[after] < STAGE_ORDINAL[before]
        row = {
            "case_id": case_id,
            "evidence_id": evidence_id,
            "baseline_first_missing_stage": before,
            "treatment_first_missing_stage": after,
            "regression": regression,
        }
        rows.append(row)
        if regression:
            regressions.append(row)
    baseline_missing = {
        row["evidence_id"]: row["baseline_first_missing_stage"]
        for row in rows
        if row["baseline_first_missing_stage"] is not None
    }
    baseline_reproduced = baseline_missing == EXPECTED_BASELINE_MISSING
    return {
        "schema": "eb-v1-k7-required-stage-comparison-v1",
        "baseline_missing_expected": EXPECTED_BASELINE_MISSING,
        "baseline_missing_observed": baseline_missing,
        "baseline_stage_reproduction_pass": baseline_reproduced,
        "required_evidence_regressions": regressions,
        "no_required_evidence_regression": not regressions,
        "rows": rows,
    }


def burden_outputs(
    baseline: dict[str, Any],
    treatment: dict[str, Any],
    evaluator_gold: dict[str, Any],
    runtime_admission: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    _, prop_required_map = build_required_map(evaluator_gold, runtime_admission)
    blanes = retained_by_lane(baseline)
    tlanes = retained_by_lane(treatment)
    lanes = all_lanes(treatment)

    lane_metrics: list[dict[str, Any]] = []
    deltas: list[int] = []
    saturated = 0
    classification_rows: list[dict[str, Any]] = []
    fully_adjudicable = 0
    dominated = 0

    for key in lanes:
        case_id, proposition_id = key.split("|", 1)
        b = blanes.get(key, [])
        t = tlanes.get(key, [])
        delta = len(t) - len(b)
        deltas.append(delta)
        seven = len(t) == 7
        saturated += int(seven)
        lane_metrics.append(
            {
                "case_id": case_id,
                "proposition_id": proposition_id,
                "baseline_retained_count": len(b),
                "treatment_retained_count": len(t),
                "delta": delta,
                "all_seven_positions_occupied": seven,
            }
        )

        classified: list[dict[str, Any]] = []
        for row in t:
            cls, authority = classify_relationship(
                case_id=case_id,
                proposition_id=proposition_id,
                evidence_id=(
                    str(row["evidence_id"])
                    if row.get("evidence_id") is not None
                    else None
                ),
                evaluator_gold=evaluator_gold,
                required_prop_map=prop_required_map,
            )
            classified.append(
                {
                    "rank": row["rank"],
                    "evidence_id": row.get("evidence_id"),
                    "source_id": row["source_id"],
                    "passage_id": row["passage_id"],
                    "classification": cls,
                    "classification_authority": authority,
                }
            )
        unresolved = sum(
            row["classification"] == "unresolved_not_safely_classifiable"
            for row in classified
        )
        known_distractor = sum(
            row["classification"] == "known_non_required_or_distractor"
            for row in classified
        )
        required_count = sum(row["classification"] == "required" for row in classified)
        adjudicable = bool(classified) and unresolved == 0
        ratio = known_distractor / len(classified) if classified else None
        is_dominated = bool(adjudicable and ratio is not None and ratio >= 0.8)
        fully_adjudicable += int(adjudicable)
        dominated += int(is_dominated)
        classification_rows.append(
            {
                "case_id": case_id,
                "proposition_id": proposition_id,
                "retained_relationship_count": len(classified),
                "required_count": required_count,
                "known_non_required_or_distractor_count": known_distractor,
                "unresolved_count": unresolved,
                "classification_coverage": (
                    (len(classified) - unresolved) / len(classified) if classified else None
                ),
                "fully_adjudicable": adjudicable,
                "known_distractor_ratio": ratio,
                "known_distractor_dominated": is_dominated,
                "relationships": classified,
            }
        )

    total_baseline = int(baseline["retained_relationship_count"])
    total_treatment = int(treatment["retained_relationship_count"])
    hard_ceiling_pass = total_treatment <= 108

    def physical(receipt: dict[str, Any]) -> tuple[int, dict[str, int]]:
        global_ids: set[str] = set()
        per_case: dict[str, int] = {}
        for case in receipt["cases"]:
            ids = {
                str(row["passage_id"])
                for row in case["candidate_rows"]
                if row["selection_state"] == "retained"
            }
            per_case[str(case["case_id"])] = len(ids)
            global_ids.update(ids)
        return len(global_ids), per_case

    bphysical, bpercase = physical(baseline)
    tphysical, tpercase = physical(treatment)

    baseline_known_distractor = 0
    for key in lanes:
        case_id, proposition_id = key.split("|", 1)
        for row in blanes.get(key, []):
            cls, _ = classify_relationship(
                case_id=case_id,
                proposition_id=proposition_id,
                evidence_id=(
                    str(row["evidence_id"])
                    if row.get("evidence_id") is not None
                    else None
                ),
                evaluator_gold=evaluator_gold,
                required_prop_map=prop_required_map,
            )
            baseline_known_distractor += int(
                cls == "known_non_required_or_distractor"
            )
    treatment_known_distractor = sum(
        row["known_non_required_or_distractor_count"] for row in classification_rows
    )

    newly_retained_required: list[dict[str, str]] = []
    for key in lanes:
        case_id, proposition_id = key.split("|", 1)
        b_ids = {
            str(row["evidence_id"])
            for row in blanes.get(key, [])
            if row.get("evidence_id") is not None
        }
        t_ids = {
            str(row["evidence_id"])
            for row in tlanes.get(key, [])
            if row.get("evidence_id") is not None
        }
        for evidence_id in sorted(t_ids - b_ids):
            cls, authority = classify_relationship(
                case_id=case_id,
                proposition_id=proposition_id,
                evidence_id=evidence_id,
                evaluator_gold=evaluator_gold,
                required_prop_map=prop_required_map,
            )
            if cls == "required":
                newly_retained_required.append(
                    {
                        "case_id": case_id,
                        "proposition_id": proposition_id,
                        "evidence_id": evidence_id,
                        "authority": authority,
                    }
                )

    added = total_treatment - total_baseline
    recovered_count = len(newly_retained_required)
    burden = {
        "schema": "eb-v1-k7-review-burden-v1",
        "baseline_normative_lane_count": baseline["normative_lane_count"],
        "baseline_retained_relationship_count": total_baseline,
        "baseline_expected_retained_relationship_count": 54,
        "baseline_count_pass": (
            total_baseline == 54 and baseline["normative_lane_count"] == 18
        ),
        "hard_total_retention_ceiling": 108,
        "treatment_retained_relationship_count": total_treatment,
        "hard_total_retention_ceiling_pass": hard_ceiling_pass,
        "lane_metrics": lane_metrics,
        "mean_delta": statistics.fmean(deltas) if deltas else 0.0,
        "median_delta": statistics.median(deltas) if deltas else 0.0,
        "maximum_delta": max(deltas, default=0),
        "saturated_at_seven_count": saturated,
        "saturated_at_seven_proportion": saturated / len(lanes) if lanes else 0.0,
        "physical_passage_burden": {
            "baseline_unique_physical_retained_passages": bphysical,
            "treatment_unique_physical_retained_passages": tphysical,
            "baseline_per_case_unique_physical_passages": bpercase,
            "treatment_per_case_unique_physical_passages": tpercase,
            "baseline_relationship_minus_physical": total_baseline - bphysical,
            "treatment_relationship_minus_physical": total_treatment - tphysical,
        },
        "efficiency_diagnostic": {
            "additional_retained_relationships": added,
            "baseline_known_non_required_or_distractor_relationships": (
                baseline_known_distractor
            ),
            "treatment_known_non_required_or_distractor_relationships": (
                treatment_known_distractor
            ),
            "additional_known_non_required_or_distractor_relationships": (
                treatment_known_distractor - baseline_known_distractor
            ),
            "newly_recovered_required_relationships": newly_retained_required,
            "newly_recovered_required_relationship_count": recovered_count,
            "added_relationships_per_newly_recovered_required_relationship": (
                added / recovered_count if recovered_count else None
            ),
            "universal_efficiency_threshold_applied": False,
        },
    }

    dominance_ratio = dominated / fully_adjudicable if fully_adjudicable else None
    distractor = {
        "schema": "eb-v1-k7-known-distractor-burden-v1",
        "classification_policy": {
            "absence_from_sparse_gold_implies_distractor": False,
            "required_mapping": (
                "explicit admission + unique one-to-one missing-required fixture mapping"
            ),
            "known_distractor_sources": [
                "frozen evaluator_gold hard_negative",
                "frozen evaluator_gold non-required duplicate",
                "frozen CAL campaign's five lexical decoys for RETRIEVAL_APERTURE child:1",
            ],
            "decoy_cross_lane_unknowns_remain_unresolved": True,
        },
        "fully_adjudicable_lane_count": fully_adjudicable,
        "known_distractor_dominated_lane_count": dominated,
        "known_distractor_dominated_proportion_of_fully_adjudicable_lanes": (
            dominance_ratio
        ),
        "dominance_threshold": 0.8,
        "failure_threshold_more_than_fully_adjudicable_proportion": 0.5,
        "gold_coverage_sufficient_for_gate": fully_adjudicable > 0,
        "dominance_gate_pass": (
            fully_adjudicable > 0
            and dominance_ratio is not None
            and dominance_ratio <= 0.5
        ),
        "lanes": classification_rows,
    }
    return burden, distractor


def structural_invariants(
    baseline: dict[str, Any],
    treatment: dict[str, Any],
    ordering: dict[str, Any],
) -> dict[str, Any]:
    bcases = cases_by_id(baseline)
    tcases = cases_by_id(treatment)
    case_rows: list[dict[str, Any]] = []
    all_contract_a = True
    all_targets = True
    shared_admission = True
    root_policy = True
    score_absent = True
    authority_pins = True
    for case_id in sorted(bcases):
        b = bcases[case_id]
        t = tcases[case_id]
        contract_equal = b["package"]["contract_a"] == t["package"]["contract_a"]
        targets_equal = b["primary_targets"] == t["primary_targets"]
        all_contract_a = all_contract_a and contract_equal
        all_targets = all_targets and targets_equal
        bp = b["package"]
        tp = t["package"]
        root_ok = (
            bp["config"]["root_diagnostic"] is False
            and tp["config"]["root_diagnostic"] is False
            and bp["diagnostics"]["root_retrieval"] is None
            and tp["diagnostics"]["root_retrieval"] is None
        )
        root_policy = root_policy and root_ok
        score_ok = (
            '"score"' not in json.dumps(bp, sort_keys=True)
            and '"score"' not in json.dumps(tp, sort_keys=True)
        )
        score_absent = score_absent and score_ok
        expected_authority = {
            "contract_version": "2.0.0",
            "release_commit": CONTRACT_A_RELEASE,
            "validator_blob": CONTRACT_A_VALIDATOR_BLOB,
        }
        pin_ok = (
            bp["contract_a_authority"] == expected_authority
            and tp["contract_a_authority"] == expected_authority
        )
        authority_pins = authority_pins and pin_ok

        baseline_shared = {
            (
                str(row["proposition_id"]),
                int(row["rank"]),
                str(row["source_id"]),
                str(row["text"]),
            ): row
            for row in b["candidate_rows"]
            if row["selection_state"] == "retained"
        }
        for row in t["candidate_rows"]:
            key = (
                str(row["proposition_id"]),
                int(row["rank"]),
                str(row["source_id"]),
                str(row["text"]),
            )
            if key in baseline_shared and row["rank"] <= 3:
                if row["admission_state"] != baseline_shared[key]["admission_state"]:
                    shared_admission = False
        case_rows.append(
            {
                "case_id": case_id,
                "contract_a_identical": contract_equal,
                "primary_targets_identical": targets_equal,
                "root_diagnostic_policy_preserved": root_ok,
                "bm25_score_absent_from_packages": score_ok,
                "contract_a_authority_pins_exact": pin_ok,
            }
        )

    checks = {
        "implementation_sha_exact": (
            baseline["authority"]["implementation_sha"] == IMPLEMENTATION_SHA
            and treatment["authority"]["implementation_sha"] == IMPLEMENTATION_SHA
        ),
        "implementation_tree_exact": (
            baseline["authority"]["implementation_tree"] == IMPLEMENTATION_TREE
            and treatment["authority"]["implementation_tree"] == IMPLEMENTATION_TREE
        ),
        "contract_a_authority_and_source_world_identical": all_contract_a,
        "root_child_lane_identity_preserved": all_targets,
        "candidate_ordering_shared_prefix_unchanged": ordering[
            "baseline_prefix_matches_treatment"
        ],
        "treatment_order_matches_same_depth10_raw_retrieval": ordering[
            "treatment_package_order_matches_same_depth10_raw_retrieval"
        ],
        "raw_scores_preserved_in_receipt_not_package": score_absent,
        "frozen_admission_semantics_unchanged_for_shared_top3": shared_admission,
        "semantic_authority_prohibition": (
            not baseline["semantic_authority_leak_observed"]
            and not treatment["semantic_authority_leak_observed"]
        ),
        "root_diagnostic_policy_preserved": root_policy,
        "contract_a_authority_pins_exact": authority_pins,
        "all_frozen_packages_valid": (
            baseline["all_packages_valid"] and treatment["all_packages_valid"]
        ),
    }
    return {
        "schema": "eb-v1-k7-structural-invariants-v1",
        "checks": checks,
        "all_invariants_hold": all(bool(value) for value in checks.values()),
        "cases": case_rows,
        "intended_difference": {
            "baseline": {"candidate_depth": 5, "retained_k": 3},
            "treatment": {"candidate_depth": 10, "retained_k": 7},
            "experiment_focus": (
                "retention boundary; candidate-depth 10 is predecessor-established aperture "
                "needed to expose rank 7"
            ),
        },
    }


def p6_observation(treatment: dict[str, Any]) -> dict[str, Any]:
    decoy = cases_by_id(treatment)["RETRIEVAL_APERTURE"]
    matches = [
        row
        for row in decoy["candidate_rows"]
        if row["proposition_id"] == "RETRIEVAL_APERTURE:child:1"
        and row.get("evidence_id") == "RET-AP-P6"
    ]
    if len(matches) != 1:
        return {
            "found_exactly_once": False,
            "candidate_pool": False,
            "retained": False,
            "natural_rank": None,
            "score": None,
            "admission_state": None,
        }
    row = matches[0]
    return {
        "found_exactly_once": True,
        "candidate_pool": True,
        "retained": row["selection_state"] == "retained",
        "natural_rank": row["rank"],
        "score": row["score"],
        "admission_state": row["admission_state"],
        "source_id": row["source_id"],
        "passage_id": row["passage_id"],
    }


def results_markdown(result: dict[str, Any]) -> str:
    p6 = result["preserved_defect"]
    burden = result["review_burden_summary"]
    distractor = result["known_distractor_summary"]
    stages = result["required_evidence_summary"]
    inv = result["structural_invariants_summary"]
    return f"""# Evidence Bundler V1 — K=7 Retention-Boundary Result

## Terminal disposition

`{result['terminal_disposition']}`

## Exact scope

Frozen V1 implementation: `{IMPLEMENTATION_SHA}`. The only successor treatment was `candidate_depth=10`, `retained_k=7`; `5/3` was reproduced only as the preregistered baseline consistency control. No other K or retrieval/selection mechanism was run.

## Preserved rank-7 defect

`RET-AP-P6` remained at natural rank `{p6['natural_rank']}` with raw BM25 score `{p6['score']}` and retained state `{p6['retained']}`. Its frozen admission state after retention was `{p6['admission_state']}`; no admission repair was performed.

## Required-evidence regression

Baseline stage reproduction: `{stages['baseline_stage_reproduction_pass']}`. Required-evidence regressions: `{stages['regression_count']}`.

## Review burden

- baseline retained relationships: `{burden['baseline_retained_relationship_count']}`
- treatment retained relationships: `{burden['treatment_retained_relationship_count']}`
- hard ceiling: `{burden['hard_total_retention_ceiling']}`
- hard ceiling pass: `{burden['hard_total_retention_ceiling_pass']}`
- mean lane delta: `{burden['mean_delta']}`
- median lane delta: `{burden['median_delta']}`
- maximum lane delta: `{burden['maximum_delta']}`
- lanes saturated at seven: `{burden['saturated_at_seven_count']}` / 18
- unique physical retained passages under treatment: `{burden['treatment_unique_physical_retained_passages']}`

## Known-distractor burden

- fully adjudicable lanes: `{distractor['fully_adjudicable_lane_count']}`
- known-distractor-dominated lanes: `{distractor['known_distractor_dominated_lane_count']}`
- dominated proportion among fully adjudicable lanes: `{distractor['dominated_proportion']}`
- dominance gate pass: `{distractor['dominance_gate_pass']}`

Unknown relationships were kept unresolved rather than converted to distractors merely because sparse gold omitted them.

## Structural invariants

All preregistered structural invariants hold: `{inv['all_invariants_hold']}`. Raw BM25 score remains diagnostic in the research receipts and was not added to the V1 package contract.

## Interpretation boundary

This result is bounded to the frozen nine-case, eighteen-lane qualification set. A passing result means only that `10/7` was not falsified as the smallest fixed-K retention remedy on this set. It does not qualify a production V1 default, does not amend PR #60, and does not authorize merge, release, tag, promotion, K=8, or selector redesign.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--runtime-admission", type=Path, required=True)
    parser.add_argument("--predecessor", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    baseline_path = args.runtime_dir / "BASELINE_5_3_RECEIPT.json"
    treatment_path = args.runtime_dir / "TREATMENT_10_7_RECEIPT.json"
    pregold_path = args.runtime_dir / "PRE_GOLD_RUNTIME_FREEZE.json"
    prereg_path = args.runtime_dir / "PREREGISTRATION.md"
    baseline = read_json(baseline_path)
    treatment = read_json(treatment_path)
    pregold = read_json(pregold_path)

    evaluator_gold = read_json(args.gold)
    runtime_admission = read_json(args.runtime_admission)
    predecessor = read_json(args.predecessor)
    gold_hash = sha256_file(args.gold)

    apparatus_failures: list[str] = []
    if baseline["authority"]["implementation_sha"] != IMPLEMENTATION_SHA:
        apparatus_failures.append("baseline implementation SHA mismatch")
    if treatment["authority"]["implementation_sha"] != IMPLEMENTATION_SHA:
        apparatus_failures.append("treatment implementation SHA mismatch")
    if pregold.get("gold_loaded") is not False:
        apparatus_failures.append("pre-gold runtime freeze does not record gold_loaded=false")
    if baseline.get("gold_loaded") is not False or treatment.get("gold_loaded") is not False:
        apparatus_failures.append("runtime receipt indicates gold exposure")
    if baseline["case_count"] != 9 or treatment["case_count"] != 9:
        apparatus_failures.append("cohort case count mismatch")
    if baseline["normative_lane_count"] != 18 or treatment["normative_lane_count"] != 18:
        apparatus_failures.append("normative lane count mismatch")
    if baseline["retained_relationship_count"] != 54:
        apparatus_failures.append("baseline retained relationship count mismatch")

    ordering = ordering_comparison(baseline, treatment, predecessor)
    stages = required_stage_comparison(baseline, treatment, evaluator_gold)
    burden, distractor = burden_outputs(
        baseline, treatment, evaluator_gold, runtime_admission
    )
    invariants = structural_invariants(baseline, treatment, ordering)
    p6 = p6_observation(treatment)

    if not stages["baseline_stage_reproduction_pass"]:
        apparatus_failures.append("frozen baseline required-stage pattern failed to reproduce")
    if not invariants["all_invariants_hold"]:
        apparatus_failures.append("one or more structural invariants failed")
    if not ordering["baseline_prefix_matches_treatment"]:
        apparatus_failures.append("candidate ordering/score shared prefix changed")
    if not ordering["treatment_package_order_matches_same_depth10_raw_retrieval"]:
        apparatus_failures.append(
            "treatment package ordering differs from same-depth raw retrieval"
        )
    if not ordering["baseline_decoy_order_and_scores_match_frozen_predecessor_5_3"]:
        apparatus_failures.append(
            "baseline decoy ordering/scores differ from frozen predecessor"
        )
    if not ordering["treatment_decoy_order_and_scores_match_frozen_predecessor_depth10"]:
        apparatus_failures.append(
            "treatment decoy ordering/scores differ from frozen predecessor depth-10 retrieval"
        )

    if apparatus_failures:
        disposition = "APPARATUS_INVALID"
    elif not p6["candidate_pool"] or not p6["retained"] or p6["natural_rank"] != 7:
        disposition = "K7_RETENTION_REMEDY_FALSIFIED"
    elif not stages["no_required_evidence_regression"]:
        disposition = "FIXED_K_WIDENING_REJECTED_ON_QUALIFICATION_SET"
    elif not burden["hard_total_retention_ceiling_pass"]:
        disposition = "FIXED_K_WIDENING_REJECTED_ON_QUALIFICATION_SET"
    elif not distractor["gold_coverage_sufficient_for_gate"]:
        disposition = "INCONCLUSIVE_GOLD_COVERAGE"
    elif not distractor["dominance_gate_pass"]:
        disposition = "FIXED_K_WIDENING_REJECTED_ON_QUALIFICATION_SET"
    else:
        disposition = "K7_NOT_FALSIFIED_AS_SMALLEST_BOUNDED_REMEDY"
    if disposition not in TERMINAL:
        raise AssertionError("invalid terminal disposition")

    args.out.mkdir(parents=True, exist_ok=True)
    write_json(args.out / "CANDIDATE_ORDERING_COMPARISON.json", ordering)
    write_json(args.out / "REQUIRED_EVIDENCE_STAGE_COMPARISON.json", stages)
    write_json(args.out / "REVIEW_BURDEN.json", burden)
    write_json(args.out / "KNOWN_DISTRACTOR_BURDEN.json", distractor)
    write_json(args.out / "STRUCTURAL_INVARIANTS.json", invariants)

    result = {
        "schema": "eb-v1-k7-retention-boundary-result-v1",
        "terminal_disposition": disposition,
        "authority": {
            "implementation_sha": IMPLEMENTATION_SHA,
            "implementation_tree": IMPLEMENTATION_TREE,
            "eb_fixture_sha": EB_FIXTURE_SHA,
            "cal_decoy_sha": CAL_DECOY_SHA,
            "contract_a_release_commit": CONTRACT_A_RELEASE,
            "contract_a_validator_blob": CONTRACT_A_VALIDATOR_BLOB,
            "predecessor_run": PREDECESSOR_RUN,
            "predecessor_artifact": PREDECESSOR_ARTIFACT,
            "predecessor_artifact_digest": PREDECESSOR_DIGEST,
        },
        "cohort_identity": {
            "case_count": treatment["case_count"],
            "normative_lane_count": treatment["normative_lane_count"],
            "runtime_file_hashes": treatment["runtime_file_hashes"],
            "evaluator_gold_sha256": gold_hash,
            "predecessor_receipt_sha256": sha256_file(args.predecessor),
        },
        "baseline_configuration": {"candidate_depth": 5, "retained_k": 3},
        "treatment_configuration": {"candidate_depth": 10, "retained_k": 7},
        "gold_firewall": {
            "runtime_receipts_frozen_before_gold": True,
            "pre_gold_runtime_freeze_sha256": sha256_file(pregold_path),
            "baseline_receipt_sha256": sha256_file(baseline_path),
            "treatment_receipt_sha256": sha256_file(treatment_path),
            "gold_loaded_by_runtime": False,
            "gold_opened_only_in_evaluation_process": True,
        },
        "preserved_defect": p6,
        "candidate_ordering": ordering,
        "required_evidence_stage_localization": stages,
        "review_burden": burden,
        "gold_classification_coverage": distractor,
        "structural_invariants": invariants,
        "apparatus_failures": apparatus_failures,
        "semantic_authority_leak_observed": (
            baseline["semantic_authority_leak_observed"]
            or treatment["semantic_authority_leak_observed"]
        ),
        "production_v1_default_qualified": False,
        "merge_release_tag_promotion_authorized": False,
        "automatic_successor_authorized": False,
    }
    write_json(args.out / "RETENTION_BOUNDARY_RESULT.json", result)

    compact_result = {
        "terminal_disposition": disposition,
        "preserved_defect": p6,
        "required_evidence_summary": {
            "baseline_stage_reproduction_pass": stages[
                "baseline_stage_reproduction_pass"
            ],
            "regression_count": len(stages["required_evidence_regressions"]),
        },
        "review_burden_summary": {
            "baseline_retained_relationship_count": burden[
                "baseline_retained_relationship_count"
            ],
            "treatment_retained_relationship_count": burden[
                "treatment_retained_relationship_count"
            ],
            "hard_total_retention_ceiling": burden["hard_total_retention_ceiling"],
            "hard_total_retention_ceiling_pass": burden[
                "hard_total_retention_ceiling_pass"
            ],
            "mean_delta": burden["mean_delta"],
            "median_delta": burden["median_delta"],
            "maximum_delta": burden["maximum_delta"],
            "saturated_at_seven_count": burden["saturated_at_seven_count"],
            "treatment_unique_physical_retained_passages": burden[
                "physical_passage_burden"
            ]["treatment_unique_physical_retained_passages"],
        },
        "known_distractor_summary": {
            "fully_adjudicable_lane_count": distractor[
                "fully_adjudicable_lane_count"
            ],
            "known_distractor_dominated_lane_count": distractor[
                "known_distractor_dominated_lane_count"
            ],
            "dominated_proportion": distractor[
                "known_distractor_dominated_proportion_of_fully_adjudicable_lanes"
            ],
            "dominance_gate_pass": distractor["dominance_gate_pass"],
        },
        "structural_invariants_summary": {
            "all_invariants_hold": invariants["all_invariants_hold"]
        },
    }
    (args.out / "RESULTS.md").write_text(
        results_markdown(compact_result), encoding="utf-8"
    )

    for source in (prereg_path, baseline_path, treatment_path, pregold_path):
        target = args.out / source.name
        if source.resolve() != target.resolve():
            target.write_bytes(source.read_bytes())

    sum_names = [
        "PREREGISTRATION.md",
        "PRE_GOLD_RUNTIME_FREEZE.json",
        "BASELINE_5_3_RECEIPT.json",
        "TREATMENT_10_7_RECEIPT.json",
        "CANDIDATE_ORDERING_COMPARISON.json",
        "REQUIRED_EVIDENCE_STAGE_COMPARISON.json",
        "REVIEW_BURDEN.json",
        "KNOWN_DISTRACTOR_BURDEN.json",
        "STRUCTURAL_INVARIANTS.json",
        "RETENTION_BOUNDARY_RESULT.json",
        "RESULTS.md",
    ]
    lines = []
    for name in sum_names:
        digest = hashlib.sha256((args.out / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (args.out / "SHA256SUMS").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "terminal_disposition": disposition,
                "apparatus_failures": apparatus_failures,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
