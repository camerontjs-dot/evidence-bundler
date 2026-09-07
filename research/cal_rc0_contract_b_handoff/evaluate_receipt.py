from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EVALUATOR_SCHEMA = "research-eb-rc0-evaluator-gold-v1"
RESULT_SCHEMA = "research-eb-rc0-evaluator-receipt-v1"


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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _physical_ids(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row["evidence_id"]) for row in rows}


def evaluate(runtime: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    if gold.get("schema") != EVALUATOR_SCHEMA:
        raise ValueError("evaluator gold schema mismatch")

    runtime_by_case = {row["case_id"]: row for row in runtime["cases"]}
    case_results: list[dict[str, Any]] = []
    for case_id, case_gold in sorted(gold["cases"].items()):
        row = runtime_by_case[case_id]
        candidate_ids = _physical_ids(row["candidate_pool"])
        retained_ids = _physical_ids(row["retained"])
        admitted_ids = {
            str(item["evidence_id"])
            for item in row["admission"]
            if item["decision"] == "accepted"
        }

        required_rows: list[dict[str, Any]] = []
        for evidence_id in case_gold["required"]:
            in_candidate = evidence_id in candidate_ids
            in_retained = evidence_id in retained_ids
            admitted = evidence_id in admitted_ids
            missing_stage = None
            if not in_candidate:
                missing_stage = "candidate_pool"
            elif not in_retained:
                missing_stage = "retention"
            elif not admitted:
                missing_stage = "admission"
            required_rows.append(
                {
                    "evidence_id": evidence_id,
                    "candidate_pool_present": in_candidate,
                    "retained": in_retained,
                    "admitted": admitted,
                    "first_missing_stage": missing_stage,
                    "candidate_locations": [
                        {
                            "proposition_id": item["proposition_id"],
                            "retrieval_lane": item["retrieval_lane"],
                            "rank": item["rank"],
                            "score": item["score"],
                        }
                        for item in row["candidate_pool"]
                        if item["evidence_id"] == evidence_id
                    ],
                }
            )

        retained_relations = row["retained"]
        hard_negative = set(case_gold["hard_negative"])
        duplicate_members = {
            value
            for group in case_gold["duplicates"]
            for value in group[1:]
        }
        hard_negative_relations = sum(
            item["evidence_id"] in hard_negative for item in retained_relations
        )
        duplicate_relations = sum(
            item["evidence_id"] in duplicate_members for item in retained_relations
        )
        denominator = max(1, len(retained_relations))

        def missing(category: str) -> list[str]:
            return sorted(
                evidence_id
                for evidence_id in case_gold[category]
                if evidence_id not in admitted_ids
            )

        joint_checks = [
            {
                "evidence_ids": group,
                "all_admitted": all(evidence_id in admitted_ids for evidence_id in group),
                "missing_ids": sorted(
                    evidence_id for evidence_id in group if evidence_id not in admitted_ids
                ),
            }
            for group in case_gold["joint"]
        ]

        case_results.append(
            {
                "case_id": case_id,
                "required_evidence": required_rows,
                "all_required_evidence_admitted": all(
                    item["admitted"] for item in required_rows
                ),
                "missing_qualifier_ids": missing("qualifier"),
                "missing_exception_ids": missing("exception"),
                "missing_counterevidence_ids": missing("counterevidence"),
                "jointly_necessary_groups": joint_checks,
                "hard_negative_burden": {
                    "retained_relationship_count": hard_negative_relations,
                    "retained_relationship_fraction": round(
                        hard_negative_relations / denominator, 6
                    ),
                },
                "duplicate_burden": {
                    "retained_duplicate_relationship_count": duplicate_relations,
                    "retained_duplicate_relationship_fraction": round(
                        duplicate_relations / denominator, 6
                    ),
                    "duplicate_groups": case_gold["duplicates"],
                },
            }
        )

    stage_counts = {"candidate_pool": 0, "retention": 0, "admission": 0}
    for case in case_results:
        for item in case["required_evidence"]:
            stage = item["first_missing_stage"]
            if stage is not None:
                stage_counts[stage] += 1

    return {
        "schema": RESULT_SCHEMA,
        "runtime_receipt_sha256": "sha256:" + sha256_bytes(canonical_bytes(runtime)),
        "evaluator_gold_sha256": "sha256:" + sha256_bytes(canonical_bytes(gold)),
        "case_count": len(case_results),
        "missing_required_evidence_by_first_stage": stage_counts,
        "cases": case_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-receipt", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    runtime = json.loads(args.runtime_receipt.read_text(encoding="utf-8"))
    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    result = evaluate(runtime, gold)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(canonical_bytes(result))
    print(json.dumps({
        "evaluator_receipt_sha256": sha256_bytes(args.out.read_bytes()),
        "case_count": result["case_count"],
        "missing_required_evidence_by_first_stage": result[
            "missing_required_evidence_by_first_stage"
        ],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
