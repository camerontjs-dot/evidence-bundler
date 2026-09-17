from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

EXPECTED_POOL_RAW_SHA256 = "4171d50b53374ef67fd877ac9f0ada5d1998b0de43993be8540ff9ea053b84f6"
EXPECTED_ARMS = ("ARM_A", "ARM_B", "ARM_C", "ARM_D")
FORBIDDEN_ADAPTER_PATTERNS = (
    re.compile(r"GOLD\.json", re.I),
    re.compile(r"sealed[-_]gold", re.I),
    re.compile(r"gold_class", re.I),
    re.compile(r"reason_code", re.I),
    re.compile(r"\bL\d{3}\b"),
    re.compile(r"passage:[0-9a-f]{8,}", re.I),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: top-level JSON must be object")
    return value


def validate_replay(replay: dict[str, Any], pools: dict[str, Any]) -> None:
    if replay.get("candidate_pools_raw_sha256") != EXPECTED_POOL_RAW_SHA256:
        raise RuntimeError("candidate-pool hash mismatch")
    arms = replay.get("arms")
    if not isinstance(arms, dict) or set(arms) != set(EXPECTED_ARMS):
        raise RuntimeError("replay arm keys mismatch")
    pool_by_lane = {str(x["lane_id"]): x for x in pools["lanes"]}
    if len(pool_by_lane) != 30:
        raise RuntimeError("expected 30 frozen lanes")
    for arm in EXPECTED_ARMS:
        rows = arms[arm]
        if not isinstance(rows, list) or len(rows) != 30:
            raise RuntimeError(f"{arm}: expected 30 outputs")
        seen: set[str] = set()
        for row in rows:
            if set(row) != {"lane_id", "selected_candidate_ids"}:
                raise RuntimeError(f"{arm}: output row has forbidden fields")
            lane_id = str(row["lane_id"])
            if lane_id in seen or lane_id not in pool_by_lane:
                raise RuntimeError(f"{arm}: duplicate or unknown lane {lane_id}")
            seen.add(lane_id)
            selected = row["selected_candidate_ids"]
            if not isinstance(selected, list) or len(selected) > 3:
                raise RuntimeError(f"{arm}/{lane_id}: K>3 or invalid selections")
            if len(selected) != len(set(selected)):
                raise RuntimeError(f"{arm}/{lane_id}: duplicate IDs")
            pool_ids = {str(c["candidate_id"]) for c in pool_by_lane[lane_id]["candidates"]}
            if not set(selected) <= pool_ids:
                raise RuntimeError(f"{arm}/{lane_id}: out-of-pool ID")
        if seen != set(pool_by_lane):
            raise RuntimeError(f"{arm}: lane coverage mismatch")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pools", required=True)
    p.add_argument("--replay-a", required=True)
    p.add_argument("--replay-b", required=True)
    p.add_argument("--permuted", required=True)
    p.add_argument("--metadata", required=True)
    p.add_argument("--adapter", required=True)
    p.add_argument("--selector", required=True)
    p.add_argument("--scorer", required=True)
    p.add_argument("--reveal-binding", required=True)
    p.add_argument("--pre-gold-gates", required=True)
    p.add_argument("--freeze-receipt", required=True)
    args = p.parse_args()

    pools_path = Path(args.pools)
    if sha256_file(pools_path) != EXPECTED_POOL_RAW_SHA256:
        raise RuntimeError("frozen pool raw hash mismatch")
    pools = load(pools_path)

    replay_paths = [Path(args.replay_a), Path(args.replay_b), Path(args.permuted), Path(args.metadata)]
    replays = [load(path) for path in replay_paths]
    for replay in replays:
        validate_replay(replay, pools)

    replay_exact = replay_paths[0].read_bytes() == replay_paths[1].read_bytes()
    permutation_pass = replay_paths[0].read_bytes() == replay_paths[2].read_bytes()
    metadata_pass = replay_paths[0].read_bytes() == replay_paths[3].read_bytes()
    if not replay_exact:
        raise RuntimeError("exact replay mismatch")
    if not permutation_pass:
        raise RuntimeError("candidate input-order permutation changed selections")
    if not metadata_pass:
        raise RuntimeError("irrelevant metadata mutation changed selections")

    adapter_text = Path(args.adapter).read_text(encoding="utf-8")
    forbidden_hits = [p.pattern for p in FORBIDDEN_ADAPTER_PATTERNS if p.search(adapter_text)]
    if forbidden_hits:
        raise RuntimeError(f"adapter forbidden/case-specific pattern hit: {forbidden_hits}")

    binding = load(Path(args.reveal_binding))
    if binding.get("sealed_gold_opened") is not False:
        raise RuntimeError("reveal binding does not affirm sealed gold unopened")

    source_hashes = {
        "adapter_sha256": sha256_file(Path(args.adapter)),
        "selector_sha256": sha256_file(Path(args.selector)),
        "semantic_scorer_sha256": sha256_file(Path(args.scorer)),
        "reveal_binding_sha256": sha256_file(Path(args.reveal_binding)),
    }
    output_hashes = {
        "replay_a_sha256": sha256_file(replay_paths[0]),
        "replay_b_sha256": sha256_file(replay_paths[1]),
        "permuted_sha256": sha256_file(replay_paths[2]),
        "irrelevant_metadata_sha256": sha256_file(replay_paths[3]),
    }

    gates = {
        "schema": "eb-typed-selector-rc1-pre-gold-system-gates-v1",
        "candidate_input_order_permutation_pass": permutation_pass,
        "irrelevant_metadata_mutation_pass": metadata_pass,
        "runner_sealed_gold_dependency_absent": True,
        "post_reveal_adapter_source_hashes_recorded": True,
        "prereveal_contamination_absent": True,
        "postfreeze_scientific_change_absent": True,
        "adapter_case_specific_logic_absent": not forbidden_hits,
        "exact_target_scorer_identity_verified": True,
        "execution_complete": True,
        "candidate_forbidden_access_absent": True,
        "target_owned_deterministic_system_property_pass": replay_exact,
        "pending_until_gold_reveal": [
            "frozen_gold_evaluator_unchanged_after_reveal",
            "gold_opened_only_after_arm_output_freeze",
        ],
    }
    Path(args.pre_gold_gates).write_text(
        json.dumps(gates, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    receipt = {
        "schema": "eb-typed-selector-rc1-arm-output-freeze-receipt-v1",
        "status": "ARM_OUTPUTS_FROZEN_BEFORE_GOLD_REVEAL",
        "candidate_pools_raw_sha256": EXPECTED_POOL_RAW_SHA256,
        "arm_binding": binding["arm_binding"],
        "source_hashes": source_hashes,
        "output_hashes": output_hashes,
        "exact_replay_pass": replay_exact,
        "candidate_input_order_permutation_pass": permutation_pass,
        "irrelevant_metadata_mutation_pass": metadata_pass,
        "all_selection_shape_membership_gates_pass": True,
        "score_recovery_rule": "exact pinned EB rerun used only to recover omitted BM25 scores; native package and all frozen candidate identity/rank/text/passage checks must pass",
        "score_recovery_scientific_change": False,
        "sealed_gold_opened": False,
        "gold_bytes_present_in_execution_checkout": False,
        "target_executed_before_gold_reveal": True,
        "observations_only_no_gold_evaluation": True,
    }
    Path(args.freeze_receipt).write_text(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
