#!/usr/bin/env python3
"""Execute the preregistered EB V1 5/3 baseline and 10/7 retention treatment.

This process deliberately has no evaluator-gold input. It freezes runtime
candidate ordering, raw BM25 scores, package state, retention, and admission
before any gold-aware evaluation process runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from evidence_bundler.ingest import chunk_source_documents
from evidence_bundler.models.document import ChunkSpec, SourceDocument
from evidence_bundler.v1 import V1Config, build_package, primary_targets, validate_package
from evidence_bundler.v1.retrieval import query_bm25

IMPLEMENTATION_SHA = "c4e3f97ec8f0bd36180954c3aa382418925bf947"
IMPLEMENTATION_TREE = "1d254e38cb0e174635efc7687c2b0ab091aa52b3"
EB_FIXTURE_SHA = "dd4fb2b89f351fbdcd8b08e48dd9d7d1f10c2d05"
CAL_DECOY_SHA = "7a46d61585f868a2e904f870528f605fb06772ea"
CONTRACT_A_RELEASE = "529c92b49a34d5c610618551a8737f019f9fa332"
CONTRACT_A_VALIDATOR_BLOB = "42e5f5b3bf38d677445e9d01ea130ba604e53409"
PREDECESSOR_RUN = 34608721684
PREDECESSOR_ARTIFACT = 10267561504
PREDECESSOR_DIGEST = "sha256:86283d446726f4c5d430d87bfec642427a099575b9f7e1de9835f74b2060b4f9"


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


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def case_files(cases_dir: Path) -> list[Path]:
    return sorted(path for path in cases_dir.glob("*.json") if path.is_file())


def legacy_passage_map(case: dict[str, Any]) -> dict[tuple[str, str], str]:
    return {
        (str(row["source_id"]), str(row["text"])): str(row["evidence_id"])
        for row in case["passages"]
    }


def legacy_evidence_id(
    case: dict[str, Any],
    *,
    source_id: str,
    text: str,
    passage_map: dict[tuple[str, str], str],
) -> str | None:
    exact = passage_map.get((source_id, text))
    if exact is not None:
        return exact
    if (
        case["case_id"] == "RETRIEVAL_APERTURE"
        and source_id == "RET-AP-S6"
        and "Alpha exceeded Beta by 4 units." in text
    ):
        return "RET-AP-P6"
    return None


def legacy_decisions(
    admission_fixture: dict[str, Any], case_id: str
) -> dict[tuple[str, str], str]:
    decisions: dict[tuple[str, str], str] = {}
    for proposition_id, state in admission_fixture["cases"].get(case_id, {}).items():
        for decision in ("accepted", "rejected", "needs-review"):
            for evidence_id in state.get(decision, []):
                decisions[(str(proposition_id), str(evidence_id))] = decision
    return decisions


def translated_admission(
    package: dict[str, Any],
    *,
    case: dict[str, Any],
    passage_map: dict[tuple[str, str], str],
    legacy_decisions_map: dict[tuple[str, str], str],
) -> dict[tuple[str, str], str]:
    translated: dict[tuple[str, str], str] = {}
    for row in package["candidates"]:
        if row["selection_state"] != "retained":
            continue
        evidence_id = legacy_evidence_id(
            case,
            source_id=str(row["source_id"]),
            text=str(row["text"]),
            passage_map=passage_map,
        )
        if evidence_id is None:
            continue
        decision = legacy_decisions_map.get((str(row["proposition_id"]), evidence_id))
        if decision is not None:
            translated[(str(row["proposition_id"]), str(row["passage_id"]))] = decision
    return translated


def documents(contract_a: dict[str, Any]) -> list[SourceDocument]:
    out: list[SourceDocument] = []
    for source in contract_a["sources"]:
        media_type = str(source["media_type"])
        is_markdown = media_type.startswith("text/markdown")
        suffix = ".md" if is_markdown else ".txt"
        out.append(
            SourceDocument(
                source_id=str(source["source_id"]),
                content_path=Path("contract-a") / f"{source['source_id']}{suffix}",
                content_type="markdown" if is_markdown else "text",
                raw_text=str(source["content"]),
                content_hash=str(source["content_sha256"]),
                metadata={},
                passages={},
            )
        )
    return out


def raw_retrieval(
    case: dict[str, Any],
    config: V1Config,
    passage_map: dict[tuple[str, str], str],
) -> list[dict[str, Any]]:
    contract_a = case["contract_a"]
    chunks = chunk_source_documents(
        documents(contract_a),
        ChunkSpec(
            max_chars=config.chunk_max_chars,
            overlap_chars=config.chunk_overlap_chars,
        ),
    )
    rows: list[dict[str, Any]] = []
    for target in primary_targets(contract_a):
        for hit in query_bm25(target["text"], chunks, top_k=config.candidate_depth):
            rows.append(
                {
                    "proposition_id": target["proposition_id"],
                    "retrieval_lane": target["role"],
                    "rank": hit.rank,
                    "score": round(hit.score, 12),
                    "source_id": hit.chunk.source_id,
                    "char_start": hit.chunk.char_start,
                    "char_end": hit.chunk.char_end,
                    "text": hit.chunk.text,
                    "chunk_hash": hit.chunk.chunk_hash,
                    "evidence_id": legacy_evidence_id(
                        case,
                        source_id=hit.chunk.source_id,
                        text=hit.chunk.text,
                        passage_map=passage_map,
                    ),
                }
            )
    return rows


def semantic_authority_leak(package: dict[str, Any]) -> bool:
    forbidden = {
        "support",
        "supports",
        "refute",
        "refutes",
        "refutation",
        "verdict",
        "semantic_relation",
        "relation_hint",
        "evidence_role",
    }

    def walk(value: Any) -> bool:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).lower() in forbidden:
                    return True
                if walk(child):
                    return True
        elif isinstance(value, list):
            return any(walk(child) for child in value)
        return False

    return walk(package)


def run_case(
    case: dict[str, Any],
    admission_fixture: dict[str, Any],
    *,
    candidate_depth: int,
    retained_k: int,
) -> dict[str, Any]:
    config = V1Config(candidate_depth=candidate_depth, retained_k=retained_k)
    passage_map = legacy_passage_map(case)
    decisions = legacy_decisions(admission_fixture, str(case["case_id"]))

    raw = raw_retrieval(case, config, passage_map)
    first = build_package(contract_a=case["contract_a"], config=config)
    admission = translated_admission(
        first,
        case=case,
        passage_map=passage_map,
        legacy_decisions_map=decisions,
    )
    package = build_package(
        contract_a=case["contract_a"],
        config=config,
        admission=admission,
    )
    validate_package(package)

    candidate_rows: list[dict[str, Any]] = []
    raw_by_lane_rank = {
        (str(row["proposition_id"]), int(row["rank"])): row for row in raw
    }
    package_order_matches_raw = True
    for row in package["candidates"]:
        evidence_id = legacy_evidence_id(
            case,
            source_id=str(row["source_id"]),
            text=str(row["text"]),
            passage_map=passage_map,
        )
        raw_row = raw_by_lane_rank.get(
            (str(row["proposition_id"]), int(row["nomination_rank"]))
        )
        if raw_row is None:
            package_order_matches_raw = False
            score = None
        else:
            score = raw_row["score"]
            if (
                raw_row["source_id"] != row["source_id"]
                or raw_row["char_start"] != row["char_start"]
                or raw_row["char_end"] != row["char_end"]
                or raw_row["text"] != row["text"]
            ):
                package_order_matches_raw = False
        candidate_rows.append(
            {
                "proposition_id": row["proposition_id"],
                "retrieval_lane": row["retrieval_lane"],
                "query_id": row["query_id"],
                "retrieval_id": row["retrieval_id"],
                "rank": row["nomination_rank"],
                "score": score,
                "source_id": row["source_id"],
                "source_content_sha256": row["source_content_sha256"],
                "passage_id": row["passage_id"],
                "char_start": row["char_start"],
                "char_end": row["char_end"],
                "passage_sha256": row["passage_sha256"],
                "text": row["text"],
                "evidence_id": evidence_id,
                "selection_state": row["selection_state"],
                "admission_state": row["admission_state"],
            }
        )

    retained_rows = [
        row for row in candidate_rows if row["selection_state"] == "retained"
    ]
    unique_physical = {
        (str(row["source_id"]), str(row["passage_id"])) for row in retained_rows
    }
    return {
        "case_id": case["case_id"],
        "contract_a_handoff_sha256": case["contract_a"]["handoff_sha256"],
        "config": package["config"],
        "config_sha256": package["config_sha256"],
        "package_sha256": package["package_sha256"],
        "primary_targets": package["primary_targets"],
        "retrieval_plans": package["retrieval_plans"],
        "retrieval_executions": package["retrieval_executions"],
        "candidate_rows": candidate_rows,
        "raw_retrieval": raw,
        "package_order_matches_raw": package_order_matches_raw,
        "retained_relationship_count": len(retained_rows),
        "unique_physical_retained_passage_count": len(unique_physical),
        "semantic_authority_leak_observed": semantic_authority_leak(package),
        "package": package,
    }


def build_receipt(
    cases: list[dict[str, Any]],
    admissions: dict[str, dict[str, Any]],
    *,
    candidate_depth: int,
    retained_k: int,
    label: str,
    runtime_file_hashes: dict[str, str],
) -> dict[str, Any]:
    rows = [
        run_case(
            case,
            admissions[str(case["case_id"])],
            candidate_depth=candidate_depth,
            retained_k=retained_k,
        )
        for case in cases
    ]
    total_lanes = sum(len(row["primary_targets"]) for row in rows)
    total_retained = sum(int(row["retained_relationship_count"]) for row in rows)
    unique_physical = {
        (str(candidate["source_id"]), str(candidate["passage_id"]))
        for row in rows
        for candidate in row["candidate_rows"]
        if candidate["selection_state"] == "retained"
    }
    return {
        "schema": "eb-v1-k7-runtime-receipt-v1",
        "profile": label,
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
        "config": {
            "candidate_depth": candidate_depth,
            "retained_k": retained_k,
        },
        "gold_loaded": False,
        "runtime_file_hashes": runtime_file_hashes,
        "case_count": len(rows),
        "normative_lane_count": total_lanes,
        "retained_relationship_count": total_retained,
        "unique_physical_retained_passage_count": len(unique_physical),
        "all_packages_valid": True,
        "all_package_order_matches_raw": all(
            bool(row["package_order_matches_raw"]) for row in rows
        ),
        "semantic_authority_leak_observed": any(
            bool(row["semantic_authority_leak_observed"]) for row in rows
        ),
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-input-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--preregistration", type=Path, required=True)
    args = parser.parse_args()

    runtime_root = args.runtime_input_root
    eb_root = runtime_root / "eb"
    cal_root = runtime_root / "cal"
    cases_dir = eb_root / "cases"
    eight_case_paths = case_files(cases_dir)
    if len(eight_case_paths) != 8:
        raise SystemExit(f"APPARATUS_INVALID: expected 8 EB cases, observed {len(eight_case_paths)}")
    eight_cases = [read_json(path) for path in eight_case_paths]
    eight_admission = read_json(eb_root / "admission.json")
    decoy_cohort = read_json(cal_root / "cohort.json")
    if decoy_cohort.get("schema") != "research-eb-rc0-cohort-v1":
        raise SystemExit("APPARATUS_INVALID: decoy cohort schema mismatch")
    decoy_cases = decoy_cohort.get("cases", [])
    if len(decoy_cases) != 1 or decoy_cases[0].get("case_id") != "RETRIEVAL_APERTURE":
        raise SystemExit("APPARATUS_INVALID: preserved decoy identity mismatch")
    decoy_case = decoy_cases[0]
    decoy_admission = read_json(cal_root / "admission.json")

    cases = eight_cases + [decoy_case]
    admissions = {str(case["case_id"]): eight_admission for case in eight_cases}
    admissions["RETRIEVAL_APERTURE"] = decoy_admission

    runtime_files = eight_case_paths + [
        eb_root / "admission.json",
        cal_root / "cohort.json",
        cal_root / "admission.json",
    ]
    runtime_file_hashes = {
        str(path.relative_to(runtime_root)): sha256_file(path) for path in runtime_files
    }

    args.out.mkdir(parents=True, exist_ok=True)
    baseline = build_receipt(
        cases,
        admissions,
        candidate_depth=5,
        retained_k=3,
        label="5/3",
        runtime_file_hashes=runtime_file_hashes,
    )
    treatment = build_receipt(
        cases,
        admissions,
        candidate_depth=10,
        retained_k=7,
        label="10/7",
        runtime_file_hashes=runtime_file_hashes,
    )

    if baseline["case_count"] != 9 or treatment["case_count"] != 9:
        raise SystemExit("APPARATUS_INVALID: expected exactly nine cases")
    if baseline["normative_lane_count"] != 18 or treatment["normative_lane_count"] != 18:
        raise SystemExit("APPARATUS_INVALID: expected exactly 18 normative lanes")
    if baseline["retained_relationship_count"] != 54:
        raise SystemExit(
            "APPARATUS_INVALID: baseline retained relationship count must reproduce 54; "
            f"observed={baseline['retained_relationship_count']}"
        )
    if not baseline["all_package_order_matches_raw"] or not treatment["all_package_order_matches_raw"]:
        raise SystemExit("APPARATUS_INVALID: package candidate ordering differs from raw retrieval")
    if baseline["semantic_authority_leak_observed"] or treatment["semantic_authority_leak_observed"]:
        raise SystemExit("APPARATUS_INVALID: semantic authority field observed")

    (args.out / "BASELINE_5_3_RECEIPT.json").write_bytes(canonical_bytes(baseline))
    (args.out / "TREATMENT_10_7_RECEIPT.json").write_bytes(canonical_bytes(treatment))
    shutil.copyfile(args.preregistration, args.out / "PREREGISTRATION.md")

    runtime_manifest = {
        "schema": "eb-v1-k7-pre-gold-runtime-freeze-v1",
        "implementation_sha": IMPLEMENTATION_SHA,
        "baseline_receipt_sha256": sha256_file(args.out / "BASELINE_5_3_RECEIPT.json"),
        "treatment_receipt_sha256": sha256_file(args.out / "TREATMENT_10_7_RECEIPT.json"),
        "preregistration_sha256": sha256_file(args.out / "PREREGISTRATION.md"),
        "gold_loaded": False,
    }
    (args.out / "PRE_GOLD_RUNTIME_FREEZE.json").write_bytes(canonical_bytes(runtime_manifest))
    print(json.dumps(runtime_manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
