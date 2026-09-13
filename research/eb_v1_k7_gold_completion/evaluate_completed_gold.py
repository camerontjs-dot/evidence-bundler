#!/usr/bin/env python3
"""Evaluate blind gold-completion judgments against frozen PR #63 burden data.

This script never reruns retrieval. It consumes the exact PR #63 artifact directory
plus two independently frozen reviewer outputs and, only if needed, a third-review
output for disagreement/unresolved items.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PACKET_CANONICAL_SHA256 = "4f50b1e385c48b6b15fc223f4700f0c104ce1633742887ced388fe6342420e9c"
EXPECTED_RUN = 34649326414
EXPECTED_ARTIFACT_ID = 10282804289
EXPECTED_ARTIFACT_DIGEST = "sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d"
LABELS = {
    "MATERIAL_OR_POTENTIALLY_USEFUL_FOR_PROPOSITION",
    "KNOWN_NON_REQUIRED_OR_DISTRACTOR",
    "UNRESOLVED",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_sha256(obj: Any) -> str:
    payload = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256_bytes(payload)


def verify_sha256sums(root: Path) -> None:
    manifest = root / "SHA256SUMS"
    if not manifest.is_file():
        raise ValueError("missing frozen SHA256SUMS")
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        digest, rel = raw.split(maxsplit=1)
        rel = rel.lstrip("*")
        p = root / rel
        if not p.is_file():
            raise ValueError(f"missing artifact file in SHA256SUMS: {rel}")
        observed = sha256_bytes(p.read_bytes())
        if observed != digest:
            raise ValueError(f"SHA256SUMS mismatch for {rel}: {observed} != {digest}")


def build_frozen_mapping(root: Path) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, Any]]]:
    burden = load_json(root / "KNOWN_DISTRACTOR_BURDEN.json")
    treatment = load_json(root / "TREATMENT_10_7_RECEIPT.json")

    if treatment.get("case_count") != 9 or treatment.get("normative_lane_count") != 18:
        raise ValueError("frozen cohort mismatch")
    if treatment.get("retained_relationship_count") != 96:
        raise ValueError("frozen treatment relationship count mismatch")
    cfg = treatment.get("config", {})
    if cfg.get("candidate_depth") != 10 or cfg.get("retained_k") != 7:
        raise ValueError("wrong frozen treatment config")

    prop_text: dict[str, str] = {}
    candidate_text: dict[tuple[str, str], str] = {}
    for case in treatment["cases"]:
        for target in case["primary_targets"]:
            prop_text[target["proposition_id"]] = target["text"]
        for row in case["candidate_rows"]:
            candidate_text[(row["proposition_id"], row["evidence_id"])] = row["text"]

    mapping: dict[str, dict[str, str]] = {}
    lanes: dict[str, dict[str, Any]] = {}
    unresolved = 0

    for lane in burden["lanes"]:
        pid = lane["proposition_id"]
        lanes[pid] = {
            "case_id": lane["case_id"],
            "proposition_id": pid,
            "retained_relationship_count": lane["retained_relationship_count"],
            "preexisting_known_distractor_count": lane["known_non_required_or_distractor_count"],
            "preexisting_required_count": lane["required_count"],
            "unresolved_item_ids": [],
        }
        for rel in lane["relationships"]:
            if rel["classification"] != "unresolved_not_safely_classifiable":
                continue
            unresolved += 1
            eid = rel["evidence_id"]
            raw = f"eb-v1-k7-adjudication-v1|{pid}|{eid}"
            item_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
            mapping[item_id] = {
                "case_id": lane["case_id"],
                "proposition_id": pid,
                "evidence_id": eid,
                "proposition_text": prop_text[pid],
                "passage_text": candidate_text[(pid, eid)],
            }
            lanes[pid]["unresolved_item_ids"].append(item_id)

    if unresolved != 27 or len(mapping) != 27:
        raise ValueError(f"expected 27 unresolved relationships, got {unresolved}/{len(mapping)}")

    return mapping, lanes


def verify_packet(packet_path: Path, mapping: dict[str, dict[str, str]]) -> None:
    packet = load_json(packet_path)
    if canonical_json_sha256(packet) != PACKET_CANONICAL_SHA256:
        raise ValueError("blind packet canonical JSON SHA-256 mismatch")
    if packet.get("item_count") != 27:
        raise ValueError("packet item count mismatch")
    ids = {x["item_id"] for x in packet["items"]}
    if ids != set(mapping):
        raise ValueError("packet opaque item set mismatch")
    for item in packet["items"]:
        expected = mapping[item["item_id"]]
        if item["proposition_text"] != expected["proposition_text"]:
            raise ValueError(f"packet proposition text mismatch for {item['item_id']}")
        if item["passage_text"] != expected["passage_text"]:
            raise ValueError(f"packet passage text mismatch for {item['item_id']}")
        forbidden = {
            "case_id", "proposition_id", "evidence_id", "source_id", "rank", "score",
            "admission_state", "classification", "known_distractor_ratio",
        }
        if forbidden.intersection(item):
            raise ValueError(f"packet leaks forbidden fields for {item['item_id']}")


def parse_review(path: Path, allowed_ids: set[str], exact_ids: set[str] | None = None) -> dict[str, str]:
    obj = load_json(path)
    if obj.get("schema") != "eb-v1-k7-blind-adjudication-result-v1":
        raise ValueError(f"{path}: wrong review schema")
    reviewer = obj.get("reviewer", {})
    if reviewer.get("packet_canonical_sha256") != PACKET_CANONICAL_SHA256:
        raise ValueError(f"{path}: packet hash mismatch")
    if reviewer.get("independent_of_other_reviewers") is not True:
        raise ValueError(f"{path}: independence not asserted")

    result: dict[str, str] = {}
    for j in obj.get("judgments", []):
        item_id = j.get("item_id")
        label = j.get("label")
        if item_id in result:
            raise ValueError(f"{path}: duplicate item {item_id}")
        if item_id not in allowed_ids:
            raise ValueError(f"{path}: unknown item {item_id}")
        if label not in LABELS:
            raise ValueError(f"{path}: invalid label {label}")
        result[item_id] = label

    required = exact_ids if exact_ids is not None else allowed_ids
    if set(result) != required:
        missing = sorted(required - set(result))
        extra = sorted(set(result) - required)
        raise ValueError(f"{path}: item set mismatch missing={missing} extra={extra}")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-dir", required=True, type=Path)
    ap.add_argument("--packet", required=True, type=Path)
    ap.add_argument("--review-a", required=True, type=Path)
    ap.add_argument("--review-b", required=True, type=Path)
    ap.add_argument("--review-c", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    verify_sha256sums(args.artifact_dir)
    frozen_result = load_json(args.artifact_dir / "RETENTION_BOUNDARY_RESULT.json")
    if frozen_result.get("terminal_disposition") != "INCONCLUSIVE_GOLD_COVERAGE":
        raise ValueError("predecessor terminal disposition mismatch")

    mapping, lanes = build_frozen_mapping(args.artifact_dir)
    verify_packet(args.packet, mapping)
    ids = set(mapping)

    a = parse_review(args.review_a, ids)
    b = parse_review(args.review_b, ids)

    need_third = {
        i for i in ids if a[i] != b[i] or a[i] == "UNRESOLVED" or b[i] == "UNRESOLVED"
    }
    c: dict[str, str] = {}
    if need_third:
        if args.review_c is None:
            disposition = "INCONCLUSIVE"
            experiment = "ADJUDICATION_REQUIRES_THIRD_REVIEW"
            resolved: dict[str, str] = {}
        else:
            c = parse_review(args.review_c, ids, exact_ids=need_third)
            resolved = {}
            for i in ids:
                if i not in need_third:
                    resolved[i] = a[i]
                else:
                    resolved[i] = c[i]
            if any(v == "UNRESOLVED" for v in resolved.values()):
                disposition = "INCONCLUSIVE"
                experiment = "ADJUDICATION_REMAINS_UNRESOLVED"
            else:
                disposition = ""
                experiment = ""
    else:
        resolved = dict(a)
        disposition = ""
        experiment = ""

    lane_results = []
    dominated_count = None
    if not disposition:
        dominated_count = 0
        for pid, lane in sorted(lanes.items()):
            added_distractors = sum(
                1 for item_id in lane["unresolved_item_ids"]
                if resolved[item_id] == "KNOWN_NON_REQUIRED_OR_DISTRACTOR"
            )
            material_count = sum(
                1 for item_id in lane["unresolved_item_ids"]
                if resolved[item_id] == "MATERIAL_OR_POTENTIALLY_USEFUL_FOR_PROPOSITION"
            )
            distractors = lane["preexisting_known_distractor_count"] + added_distractors
            total = lane["retained_relationship_count"]
            ratio = distractors / total
            dominated = ratio >= 0.8
            dominated_count += int(dominated)
            lane_results.append({
                **lane,
                "completed_known_non_required_or_distractor_count": distractors,
                "completed_material_or_potentially_useful_count": material_count,
                "known_distractor_ratio": ratio,
                "known_distractor_dominated": dominated,
            })

        if dominated_count > 9:
            disposition = "FALSIFIED"
            experiment = "FIXED_K_WIDENING_REJECTED_ON_COMPLETED_QUALIFICATION_GOLD"
        else:
            disposition = "SUPPORTED FOR PROMOTION"
            experiment = "K7_NOT_FALSIFIED_AS_SMALLEST_BOUNDED_REMEDY_AFTER_GOLD_COMPLETION"

    out = {
        "schema": "eb-v1-k7-gold-completion-result-v1",
        "predecessor": {
            "run": EXPECTED_RUN,
            "artifact_id": EXPECTED_ARTIFACT_ID,
            "artifact_digest": EXPECTED_ARTIFACT_DIGEST,
            "terminal_disposition": "INCONCLUSIVE_GOLD_COVERAGE",
        },
        "packet_canonical_sha256": PACKET_CANONICAL_SHA256,
        "reviewer_a": str(args.review_a),
        "reviewer_b": str(args.review_b),
        "reviewer_c": str(args.review_c) if args.review_c else None,
        "third_review_item_count": len(need_third),
        "resolved_item_count": len(resolved),
        "known_distractor_dominated_lane_count": dominated_count,
        "normative_lane_count": 18,
        "burden_failure_rule": "known_distractor_dominated_lane_count > 9",
        "primary_disposition": disposition,
        "experiment_specific_conclusion": experiment,
        "lane_results": lane_results,
        "stop_boundary": True,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "primary_disposition": disposition,
        "experiment_specific_conclusion": experiment,
        "third_review_item_count": len(need_third),
        "dominated_lane_count": dominated_count,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
