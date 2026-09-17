#!/usr/bin/env python3
"""Target-agnostic evaluator for EB typed-selector RC1.

The evaluator knows only opaque ARM_A..ARM_D keys until a post-freeze role
binding is supplied. It never executes a selector and never reads gold before
the caller explicitly invokes it after arm-output freeze.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any

ARM_KEYS = ("ARM_A", "ARM_B", "ARM_C", "ARM_D")
USEFUL_CLASSES = {"REQUIRED", "USEFUL_DISTINCT"}
NONUSEFUL_CLASSES = {"DISTRACTOR", "REDUNDANT", "UNSAFE_OR_MISLEADING"}
ALL_CLASSES = USEFUL_CLASSES | NONUSEFUL_CLASSES | {"UNRESOLVED"}

REQUIRED_EXTERNAL_GATES = (
    "candidate_input_order_permutation_pass",
    "irrelevant_metadata_mutation_pass",
    "runner_sealed_gold_dependency_absent",
    "post_reveal_adapter_source_hashes_recorded",
    "prereveal_contamination_absent",
    "postfreeze_scientific_change_absent",
    "frozen_gold_evaluator_unchanged_after_reveal",
    "gold_opened_only_after_arm_output_freeze",
    "adapter_case_specific_logic_absent",
    "exact_target_scorer_identity_verified",
    "execution_complete",
    "candidate_forbidden_access_absent",
    "target_owned_deterministic_system_property_pass",
)

class EvaluationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationError(message)


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        value = json.load(f)
    _require(isinstance(value, dict), f"{path}: top-level JSON must be an object")
    return value


def _gold_index(gold: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    lanes = gold.get("lanes")
    _require(isinstance(lanes, list), "gold.lanes must be a list")
    _require(len(lanes) == 30, "gold must contain exactly 30 lanes")
    lane_by_id: dict[str, Any] = {}
    candidate_by_id: dict[str, dict[str, Any]] = {}
    category_counts: dict[int, int] = {}
    for lane in lanes:
        _require(isinstance(lane, dict), "gold lane must be an object")
        lane_id = lane.get("lane_id")
        category = lane.get("category")
        candidates = lane.get("candidates")
        _require(isinstance(lane_id, str) and lane_id, "gold lane_id must be nonempty")
        _require(lane_id not in lane_by_id, f"duplicate gold lane_id: {lane_id}")
        _require(isinstance(category, int) and 1 <= category <= 10, f"{lane_id}: invalid category")
        _require(isinstance(candidates, list) and len(candidates) == 10, f"{lane_id}: expected 10 candidates")
        category_counts[category] = category_counts.get(category, 0) + 1
        seen_ids: set[str] = set()
        for cand in candidates:
            _require(isinstance(cand, dict), f"{lane_id}: candidate must be object")
            cid = cand.get("candidate_id")
            cls = cand.get("gold_class")
            rank = cand.get("rank")
            req_groups = cand.get("required_group_ids")
            red_group = cand.get("redundancy_group_id")
            _require(isinstance(cid, str) and cid, f"{lane_id}: candidate_id missing")
            _require(cid not in seen_ids, f"{lane_id}: duplicate candidate_id {cid}")
            _require(cid not in candidate_by_id, f"candidate_id reused across lanes: {cid}")
            _require(cls in ALL_CLASSES, f"{lane_id}/{cid}: invalid gold_class {cls!r}")
            _require(isinstance(rank, int) and 1 <= rank <= 10, f"{lane_id}/{cid}: invalid rank")
            _require(isinstance(req_groups, list), f"{lane_id}/{cid}: required_group_ids must be list")
            _require(all(isinstance(g, str) and g for g in req_groups), f"{lane_id}/{cid}: invalid required group")
            _require(red_group is None or (isinstance(red_group, str) and red_group), f"{lane_id}/{cid}: invalid redundancy group")
            if cls == "REQUIRED":
                _require(req_groups, f"{lane_id}/{cid}: REQUIRED needs at least one required_group_id")
            seen_ids.add(cid)
            candidate_by_id[cid] = {"lane_id": lane_id, **cand}
        lane_by_id[lane_id] = lane
    _require(set(category_counts) == set(range(1, 11)), "gold must contain categories 1..10")
    _require(all(category_counts[c] == 3 for c in range(1, 11)), "gold must contain exactly 3 lanes per category")
    return lane_by_id, candidate_by_id


def _parse_replay(
    replay: dict[str, Any],
    gold: dict[str, Any],
    lane_by_id: dict[str, Any],
    candidate_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, list[str]]]:
    _require(replay.get("candidate_pools_raw_sha256") == gold.get("candidate_pools_raw_sha256"),
             "candidate-pool hash mismatch")
    arms = replay.get("arms")
    _require(isinstance(arms, dict), "replay.arms must be an object")
    _require(set(arms) == set(ARM_KEYS), f"replay arms must be exactly {ARM_KEYS}")
    parsed: dict[str, dict[str, list[str]]] = {}
    expected_lanes = set(lane_by_id)
    for arm in ARM_KEYS:
        rows = arms[arm]
        _require(isinstance(rows, list), f"{arm}: lanes must be a list")
        by_lane: dict[str, list[str]] = {}
        for row in rows:
            _require(isinstance(row, dict), f"{arm}: lane output must be object")
            _require(set(row) == {"lane_id", "selected_candidate_ids"},
                     f"{arm}: output rows may contain only lane_id and selected_candidate_ids")
            lane_id = row["lane_id"]
            selected = row["selected_candidate_ids"]
            _require(isinstance(lane_id, str) and lane_id in lane_by_id, f"{arm}: unknown lane_id {lane_id!r}")
            _require(lane_id not in by_lane, f"{arm}: duplicate lane output {lane_id}")
            _require(isinstance(selected, list), f"{arm}/{lane_id}: selected_candidate_ids must be a list")
            _require(len(selected) <= 3, f"{arm}/{lane_id}: more than 3 selections")
            _require(all(isinstance(x, str) for x in selected), f"{arm}/{lane_id}: candidate IDs must be strings")
            _require(len(selected) == len(set(selected)), f"{arm}/{lane_id}: duplicate selected candidate IDs")
            pool_ids = {c["candidate_id"] for c in lane_by_id[lane_id]["candidates"]}
            _require(set(selected) <= pool_ids, f"{arm}/{lane_id}: selection outside frozen top-10 pool")
            by_lane[lane_id] = list(selected)
        _require(set(by_lane) == expected_lanes, f"{arm}: output must cover all 30 lanes exactly once")
        parsed[arm] = by_lane
    return parsed


def _required_groups(lane: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for cand in lane["candidates"]:
        if cand["gold_class"] == "REQUIRED":
            out.update(cand["required_group_ids"])
    return out


def _selected_required_groups(lane: dict[str, Any], selected: list[str]) -> set[str]:
    chosen = set(selected)
    out: set[str] = set()
    for cand in lane["candidates"]:
        if cand["candidate_id"] in chosen and cand["gold_class"] == "REQUIRED":
            out.update(cand["required_group_ids"])
    return out


def _useful_group_keys(lane: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for cand in lane["candidates"]:
        if cand["gold_class"] == "REQUIRED":
            for group in cand["required_group_ids"]:
                keys.add(f"required:{group}")
        elif cand["gold_class"] == "USEFUL_DISTINCT":
            keys.add(f"useful:{cand['candidate_id']}")
    return keys


def _selected_useful_group_keys(lane: dict[str, Any], selected: list[str]) -> set[str]:
    chosen = set(selected)
    keys: set[str] = set()
    for cand in lane["candidates"]:
        if cand["candidate_id"] not in chosen:
            continue
        if cand["gold_class"] == "REQUIRED":
            for group in cand["required_group_ids"]:
                keys.add(f"required:{group}")
        elif cand["gold_class"] == "USEFUL_DISTINCT":
            keys.add(f"useful:{cand['candidate_id']}")
    return keys


def _arm_metrics(
    arm: str,
    selections: dict[str, list[str]],
    lane_by_id: dict[str, Any],
) -> dict[str, Any]:
    positive_lanes = [l for l in lane_by_id.values() if l["lane_type"] == "positive"]
    positive_ids = {l["lane_id"] for l in positive_lanes}
    covered_ids: set[str] = set()
    useful_available = 0
    useful_retained = 0
    unsafe_total = 0
    unsafe_lanes: set[str] = set()
    nonuseful_total = 0
    useful_distinct_retained = 0
    redundant_retained = 0
    category10_burden = 0
    selected_useful_ranks: list[int] = []
    deep_useful_rescue = 0
    per_category: dict[str, dict[str, Any]] = {}
    complementary_total = 0
    complementary_covered = 0

    for lane_id, lane in lane_by_id.items():
        selected = selections[lane_id]
        chosen = set(selected)
        req = _required_groups(lane)
        got_req = _selected_required_groups(lane, selected)
        covered = bool(req) and req <= got_req
        if lane_id in positive_ids and covered:
            covered_ids.add(lane_id)
        if len(req) >= 2:
            complementary_total += 1
            if covered:
                complementary_covered += 1

        available_keys = _useful_group_keys(lane)
        selected_keys = _selected_useful_group_keys(lane, selected)
        useful_available += len(available_keys)
        useful_retained += len(selected_keys & available_keys)

        cat = str(lane["category"])
        pc = per_category.setdefault(cat, {
            "positive_lanes": 0, "covered_positive_lanes": 0,
            "unsafe_retained": 0, "nonuseful_retained": 0,
            "useful_groups_available": 0, "useful_groups_retained": 0,
        })
        if lane_id in positive_ids:
            pc["positive_lanes"] += 1
            if covered:
                pc["covered_positive_lanes"] += 1
        pc["useful_groups_available"] += len(available_keys)
        pc["useful_groups_retained"] += len(selected_keys & available_keys)

        for cand in lane["candidates"]:
            if cand["candidate_id"] not in chosen:
                continue
            cls = cand["gold_class"]
            if cls == "UNSAFE_OR_MISLEADING":
                unsafe_total += 1
                unsafe_lanes.add(lane_id)
                pc["unsafe_retained"] += 1
            if cls in NONUSEFUL_CLASSES:
                nonuseful_total += 1
                pc["nonuseful_retained"] += 1
            if cls == "USEFUL_DISTINCT":
                useful_distinct_retained += 1
            if cls == "REDUNDANT":
                redundant_retained += 1
            if lane["category"] == 10:
                category10_burden += 1
            if cls in USEFUL_CLASSES:
                selected_useful_ranks.append(cand["rank"])
                if cand["rank"] >= 4:
                    deep_useful_rescue += 1

    for pc in per_category.values():
        denom = pc["useful_groups_available"]
        pc["useful_recall_at_3"] = pc["useful_groups_retained"] / denom if denom else None

    ordinary_ids = {l["lane_id"] for l in lane_by_id.values() if l["category"] == 9}
    ordinary_coverage = sum(1 for lid in ordinary_ids if lid in covered_ids)
    recall = useful_retained / useful_available if useful_available else 0.0
    return {
        "arm": arm,
        "required_lane_coverage": {
            "covered_positive_lanes": len(covered_ids),
            "eligible_positive_lanes": len(positive_ids),
            "rate": len(covered_ids) / len(positive_ids) if positive_ids else 0.0,
        },
        "useful_item_recall_at_3": {
            "useful_groups_retained": useful_retained,
            "useful_groups_available": useful_available,
            "rate": recall,
        },
        "unsafe_misleading_retention": {
            "total": unsafe_total,
            "lanes_affected": len(unsafe_lanes),
        },
        "nonuseful_burden": {
            "total": nonuseful_total,
            "per_lane_mean": nonuseful_total / len(lane_by_id),
        },
        "useful_distinct_retention": useful_distinct_retained,
        "redundant_retention": redundant_retained,
        "category10_selected_burden": category10_burden,
        "mean_original_rank_of_selected_useful": (
            sum(selected_useful_ranks) / len(selected_useful_ranks) if selected_useful_ranks else None
        ),
        "deep_useful_rescue_count": deep_useful_rescue,
        "ordinary_easy_lane_coverage": ordinary_coverage,
        "complementary_coverage": {
            "covered": complementary_covered,
            "total": complementary_total,
        },
        "per_category": per_category,
    }


def _pairwise_deltas(metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for a, b in itertools.combinations(ARM_KEYS, 2):
        ma, mb = metrics[a], metrics[b]
        out[f"{a}_vs_{b}"] = {
            "required_lane_coverage_delta": (
                ma["required_lane_coverage"]["covered_positive_lanes"]
                - mb["required_lane_coverage"]["covered_positive_lanes"]
            ),
            "useful_recall_delta": (
                ma["useful_item_recall_at_3"]["rate"]
                - mb["useful_item_recall_at_3"]["rate"]
            ),
            "unsafe_retention_delta": (
                ma["unsafe_misleading_retention"]["total"]
                - mb["unsafe_misleading_retention"]["total"]
            ),
            "nonuseful_burden_delta": (
                ma["nonuseful_burden"]["total"] - mb["nonuseful_burden"]["total"]
            ),
        }
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _selection_overlap(selections: dict[str, dict[str, list[str]]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for a, b in itertools.combinations(ARM_KEYS, 2):
        vals = []
        for lane_id in selections[a]:
            vals.append(_jaccard(set(selections[a][lane_id]), set(selections[b][lane_id])))
        out[f"{a}_vs_{b}"] = sum(vals) / len(vals)
    return out


def evaluate_replays(
    gold: dict[str, Any],
    replay_1: dict[str, Any],
    replay_2: dict[str, Any],
) -> dict[str, Any]:
    lane_by_id, candidate_by_id = _gold_index(gold)
    p1 = _parse_replay(replay_1, gold, lane_by_id, candidate_by_id)
    p2 = _parse_replay(replay_2, gold, lane_by_id, candidate_by_id)
    replay_identity = {
        arm: all(p1[arm][lid] == p2[arm][lid] for lid in lane_by_id)
        for arm in ARM_KEYS
    }
    metrics = {arm: _arm_metrics(arm, p1[arm], lane_by_id) for arm in ARM_KEYS}
    return {
        "schema": "eb-typed-selector-rc1-evaluation-v1",
        "exact_replay_identity": {
            "per_arm": replay_identity,
            "all_arms": all(replay_identity.values()),
        },
        "arm_metrics": metrics,
        "pairwise_deltas": _pairwise_deltas(metrics),
        "selection_overlap_jaccard": _selection_overlap(p1),
    }


def _validate_binding(binding: dict[str, Any]) -> dict[str, str]:
    expected_roles = {"rank_only", "semantic", "candidate", "weak"}
    _require(set(binding) == expected_roles, f"binding roles must be exactly {sorted(expected_roles)}")
    _require(set(binding.values()) == set(ARM_KEYS), "binding values must be a permutation of ARM_A..ARM_D")
    return {k: str(v) for k, v in binding.items()}


def _validate_system_gates(gates: dict[str, Any]) -> None:
    _require(set(REQUIRED_EXTERNAL_GATES) <= set(gates), "system-gates file is missing required preregistered keys")
    for key in REQUIRED_EXTERNAL_GATES:
        _require(isinstance(gates[key], bool), f"system gate {key} must be boolean")


def assign_disposition(
    evaluation: dict[str, Any],
    binding: dict[str, Any],
    system_gates: dict[str, Any],
) -> dict[str, Any]:
    roles = _validate_binding(binding)
    _validate_system_gates(system_gates)
    metrics = evaluation["arm_metrics"]
    candidate = metrics[roles["candidate"]]
    semantic = metrics[roles["semantic"]]
    rank = metrics[roles["rank_only"]]
    weak = metrics[roles["weak"]]

    replay = evaluation["exact_replay_identity"]["per_arm"]
    candidate_replay_failed = not replay[roles["candidate"]]
    noncandidate_replay_failed = any(not replay[roles[r]] for r in ("rank_only", "semantic", "weak"))

    apparatus_failures = []
    if not system_gates["frozen_gold_evaluator_unchanged_after_reveal"]:
        apparatus_failures.append("gold_or_evaluator_changed_after_reveal")
    if not system_gates["gold_opened_only_after_arm_output_freeze"]:
        apparatus_failures.append("gold_opened_before_arm_output_freeze")
    if not system_gates["adapter_case_specific_logic_absent"]:
        apparatus_failures.append("post_reveal_adapter_contains_case_specific_or_gold_dependent_logic")
    if not system_gates["exact_target_scorer_identity_verified"]:
        apparatus_failures.append("target_or_scorer_identity_unverified")
    if not system_gates["execution_complete"]:
        apparatus_failures.append("execution_incomplete")
    if noncandidate_replay_failed:
        apparatus_failures.append("noncandidate_exact_replay_failure")
    if candidate_replay_failed and system_gates["target_owned_deterministic_system_property_pass"]:
        apparatus_failures.append("candidate_replay_failed_without_preregistered_target_owned_failure")
    if apparatus_failures:
        return {"disposition": "BLOCKED_APPARATUS", "reasons": apparatus_failures}

    cand_cov = candidate["required_lane_coverage"]["covered_positive_lanes"]
    sem_cov = semantic["required_lane_coverage"]["covered_positive_lanes"]
    weak_cov = weak["required_lane_coverage"]["covered_positive_lanes"]
    cand_rec = candidate["useful_item_recall_at_3"]["rate"]
    sem_rec = semantic["useful_item_recall_at_3"]["rate"]
    weak_rec = weak["useful_item_recall_at_3"]["rate"]
    cand_unsafe = candidate["unsafe_misleading_retention"]["total"]
    sem_unsafe = semantic["unsafe_misleading_retention"]["total"]
    cand_nonuseful = candidate["nonuseful_burden"]["total"]
    sem_nonuseful = semantic["nonuseful_burden"]["total"]
    cand_ord = candidate["ordinary_easy_lane_coverage"]
    sem_ord = semantic["ordinary_easy_lane_coverage"]
    rank_ord = rank["ordinary_easy_lane_coverage"]

    falsification_reasons = []
    if sem_cov - cand_cov >= 3:
        falsification_reasons.append("required_lane_coverage_worse_by_at_least_3")
    if sem_rec - cand_rec >= 0.08 - 1e-12:
        falsification_reasons.append("useful_recall_worse_by_at_least_0.08")
    if cand_unsafe - sem_unsafe > 2:
        falsification_reasons.append("more_than_2_additional_unsafe_items")
    if cand_ord == 0 and max(rank_ord, sem_ord) >= 2:
        falsification_reasons.append("lost_all_ordinary_lanes_while_control_covers_at_least_2")
    if not system_gates["target_owned_deterministic_system_property_pass"]:
        falsification_reasons.append("target_owned_deterministic_or_system_property_failed")
    if not system_gates["candidate_forbidden_access_absent"]:
        falsification_reasons.append("candidate_requires_forbidden_access")
    if falsification_reasons:
        return {"disposition": "FALSIFIED", "reasons": falsification_reasons}

    all_system_pass = (
        evaluation["exact_replay_identity"]["all_arms"]
        and system_gates["candidate_input_order_permutation_pass"]
        and system_gates["irrelevant_metadata_mutation_pass"]
        and system_gates["runner_sealed_gold_dependency_absent"]
        and system_gates["post_reveal_adapter_source_hashes_recorded"]
        and system_gates["prereveal_contamination_absent"]
        and system_gates["postfreeze_scientific_change_absent"]
        and system_gates["candidate_forbidden_access_absent"]
        and system_gates["target_owned_deterministic_system_property_pass"]
    )
    support_checks = {
        "coverage_delta_at_least_3": cand_cov - sem_cov >= 3,
        "useful_recall_delta_at_least_0_08": cand_rec - sem_rec >= 0.08 - 1e-12,
        "unsafe_no_worse": cand_unsafe <= sem_unsafe,
        "nonuseful_burden_within_3": cand_nonuseful <= sem_nonuseful + 3,
        "ordinary_coverage_within_1_of_better_control": cand_ord >= max(rank_ord, sem_ord) - 1,
        "weak_discrimination": (cand_cov - weak_cov >= 2) or (cand_rec - weak_rec >= 0.05 - 1e-12),
        "all_deterministic_and_system_gates_pass": all_system_pass,
        "no_prereveal_contamination": system_gates["prereveal_contamination_absent"],
        "no_material_postfreeze_scientific_change": system_gates["postfreeze_scientific_change_absent"],
    }
    if all(support_checks.values()):
        return {"disposition": "SUPPORTED FOR PROMOTION", "support_checks": support_checks, "reasons": []}
    return {"disposition": "INCONCLUSIVE", "support_checks": support_checks, "reasons": []}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--gold", required=True)
    p.add_argument("--replay-1", required=True)
    p.add_argument("--replay-2", required=True)
    p.add_argument("--binding")
    p.add_argument("--system-gates")
    p.add_argument("--out")
    args = p.parse_args(argv)
    try:
        gold = _load_json(args.gold)
        r1 = _load_json(args.replay_1)
        r2 = _load_json(args.replay_2)
        result = evaluate_replays(gold, r1, r2)
        if args.binding or args.system_gates:
            _require(args.binding and args.system_gates, "--binding and --system-gates must be supplied together")
            binding = _load_json(args.binding)
            gates = _load_json(args.system_gates)
            result["research_disposition"] = assign_disposition(result, binding, gates)
        else:
            result["research_disposition"] = None
            result["disposition_note"] = "No role binding supplied; prereveal metrics only."
    except EvaluationError as exc:
        result = {
            "schema": "eb-typed-selector-rc1-evaluation-v1",
            "research_disposition": {
                "disposition": "BLOCKED_APPARATUS",
                "reasons": [str(exc)],
            },
        }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
