from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

EXPECTED_LABEL_COUNTS = {
    "KEEP_DISTINCT": 19,
    "DROP_REDUNDANT": 3,
    "DROP_DISTRACTOR": 73,
    "UNRESOLVED": 1,
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_labels(binding: dict[str, Any], relation_map: dict[str, Any]) -> dict[str, str]:
    all_keys = {
        str(row["semantic_key"])
        for row in relation_map["matched_relationships"]
    }
    all_keys.update(
        str(row["semantic_key"])
        for row in relation_map["larger_arm_only_relationships"]
    )
    labels = {key: str(binding["default_for_other_cobalt_relationships"]) for key in all_keys}
    for row in binding["non_drop_bindings"]:
        key = str(row["semantic_key"])
        if key not in labels:
            raise RuntimeError(f"binding key outside cobalt universe: {key}")
        labels[key] = str(row["label"])
    observed_counts = defaultdict(int)
    for label in labels.values():
        observed_counts[label] += 1
    if dict(observed_counts) != EXPECTED_LABEL_COUNTS:
        raise RuntimeError(
            f"operational label count mismatch: {dict(observed_counts)} != {EXPECTED_LABEL_COUNTS}"
        )
    return labels


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", required=True)
    parser.add_argument("--binding", required=True)
    parser.add_argument("--relation-map", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    selection_path = Path(args.selection)
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    binding = json.loads(Path(args.binding).read_text(encoding="utf-8"))
    relation_map = json.loads(Path(args.relation_map).read_text(encoding="utf-8"))
    labels = build_labels(binding, relation_map)

    keeps_by_lane: dict[str, set[str]] = defaultdict(set)
    for semantic_key, label in labels.items():
        proposition_id, evidence_id = semantic_key.split("|", 1)
        if label == "KEEP_DISTINCT":
            keeps_by_lane[proposition_id].add(evidence_id)

    arm_names = sorted(selection["lanes"][0]["arms"])
    evaluation: dict[str, Any] = {}
    for arm in arm_names:
        selected_keys: list[str] = []
        lane_coverage = 0
        for lane in selection["lanes"]:
            proposition_id = str(lane["proposition_id"])
            selected = [str(x) for x in lane["arms"][arm]]
            selected_keys.extend(f"{proposition_id}|{evidence_id}" for evidence_id in selected)
            expected_keeps = keeps_by_lane.get(proposition_id, set())
            if expected_keeps.issubset(set(selected)):
                lane_coverage += 1

        counts = defaultdict(int)
        for key in selected_keys:
            counts[labels[key]] += 1
        keep_count = counts["KEEP_DISTINCT"]
        nonkeep = len(selected_keys) - keep_count
        evaluation[arm] = {
            "selected_relationships": len(selected_keys),
            "label_counts": {label: counts[label] for label in EXPECTED_LABEL_COUNTS},
            "keep_distinct_retained": keep_count,
            "keep_distinct_total": EXPECTED_LABEL_COUNTS["KEEP_DISTINCT"],
            "all_keep_lanes_covered": lane_coverage,
            "lane_total": len(selection["lanes"]),
            "non_keep_selected": nonkeep,
        }

    result = {
        "schema": "eb-typed-selector-rc0-operational-pool-evaluation-v1",
        "classification": "RETROSPECTIVE_DEVELOPMENT_DIAGNOSTIC_ONLY",
        "selection_sha256": sha256_file(selection_path),
        "operational_authority": binding["authority"],
        "evaluation": evaluation,
        "nonclaims": [
            "The operational labels are opened only after selection output exists.",
            "This is retrospective development evidence, not fresh qualification and not a promotion disposition.",
            "The 96-relationship operational universe is the frozen 10/7 review world, not the complete depth-10 universe.",
        ],
    }
    text = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    Path(args.output).write_text(text, encoding="utf-8")
    print(hashlib.sha256(text.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
