#!/usr/bin/env python3
"""Run the bounded Evidence Bundler V1 convergence qualification.

This apparatus does not tune retrieval. It compares only the preregistered
5/3 -> 10/3 -> 10/6 sequence against frozen prior fixtures and records raw
BM25 scores diagnostically outside the V1 package contract.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from evidence_bundler.ingest import chunk_source_documents
from evidence_bundler.models.document import ChunkSpec, SourceDocument
from evidence_bundler.v1 import V1Config, build_package, validate_contract_a
from evidence_bundler.v1.contract_a import compute_handoff_sha256, primary_targets
from evidence_bundler.v1.retrieval import query_bm25

EXPECTED_BASELINE_LOSSES = {
    "C03-P2": "candidate_pool",
    "C06-P1": "retention",
    "C08-P2": "admission",
}
STAGE_ORDINAL = {
    "candidate_pool": 0,
    "retention": 1,
    "admission": 2,
    None: 3,
}
PROFILES = ((5, 3), (10, 3), (10, 6))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_bytes(value: Any) -> bytes:
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


def _case_files(cases_dir: Path) -> list[Path]:
    return sorted(path for path in cases_dir.glob("*.json") if path.is_file())


def _legacy_passage_map(case: dict[str, Any]) -> dict[tuple[str, str], str]:
    return {
        (str(row["source_id"]), str(row["text"])): str(row["evidence_id"])
        for row in case["passages"]
    }


def _legacy_decisions(
    admission_fixture: dict[str, Any], case_id: str
) -> dict[tuple[str, str], str]:
    decisions: dict[tuple[str, str], str] = {}
    for proposition_id, state in admission_fixture["cases"].get(case_id, {}).items():
        for decision in ("accepted", "rejected", "needs-review"):
            for evidence_id in state.get(decision, []):
                decisions[(str(proposition_id), str(evidence_id))] = decision
    return decisions


def _translated_admission(
    package: dict[str, Any],
    *,
    passage_map: dict[tuple[str, str], str],
    legacy_decisions: dict[tuple[str, str], str],
) -> dict[tuple[str, str], str]:
    translated: dict[tuple[str, str], str] = {}
    for row in package["candidates"]:
        if row["selection_state"] != "retained":
            continue
        evidence_id = passage_map.get((str(row["source_id"]), str(row["text"])))
        if evidence_id is None:
            continue
        decision = legacy_decisions.get((str(row["proposition_id"]), evidence_id))
        if decision is not None:
            translated[(str(row["proposition_id"]), str(row["passage_id"]))] = decision
    return translated


def _documents(contract_a: dict[str, Any]) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for source in contract_a["sources"]:
        media_type = str(source["media_type"])
        is_markdown = media_type.startswith("text/markdown")
        suffix = ".md" if is_markdown else ".txt"
        documents.append(
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
    return documents


def _score_diagnostics(
    contract_a: dict[str, Any],
    config: V1Config,
    passage_map: dict[tuple[str, str], str],
) -> list[dict[str, Any]]:
    chunks = chunk_source_documents(
        _documents(contract_a),
        ChunkSpec(
            max_chars=config.chunk_max_chars,
            overlap_chars=config.chunk_overlap_chars,
        ),
    )
    rows: list[dict[str, Any]] = []
    for target in primary_targets(contract_a):
        hits = query_bm25(target["text"], chunks, top_k=config.candidate_depth)
        for hit in hits:
            rows.append(
                {
                    "proposition_id": target["proposition_id"],
                    "source_id": hit.chunk.source_id,
                    "evidence_id": passage_map.get(
                        (hit.chunk.source_id, hit.chunk.text)
                    ),
                    "rank": hit.rank,
                    "score": round(hit.score, 12),
                }
            )
    return rows


def _run_case(
    case: dict[str, Any],
    admission_fixture: dict[str, Any],
    *,
    candidate_depth: int,
    retained_k: int,
) -> dict[str, Any]:
    config = V1Config(candidate_depth=candidate_depth, retained_k=retained_k)
    passage_map = _legacy_passage_map(case)
    decisions = _legacy_decisions(admission_fixture, str(case["case_id"]))
    initial = build_package(contract_a=case["contract_a"], config=config)
    translated = _translated_admission(
        initial,
        passage_map=passage_map,
        legacy_decisions=decisions,
    )
    package = build_package(
        contract_a=case["contract_a"],
        config=config,
        admission=translated,
    )

    candidate_ids: set[str] = set()
    retained_ids: set[str] = set()
    admitted_ids: set[str] = set()
    candidate_rows: list[dict[str, Any]] = []
    for row in package["candidates"]:
        evidence_id = passage_map.get((str(row["source_id"]), str(row["text"])))
        if evidence_id is None:
            continue
        candidate_ids.add(evidence_id)
        if row["selection_state"] == "retained":
            retained_ids.add(evidence_id)
        if row["admission_state"] == "accepted":
            admitted_ids.add(evidence_id)
        candidate_rows.append(
            {
                "proposition_id": row["proposition_id"],
                "retrieval_lane": row["retrieval_lane"],
                "evidence_id": evidence_id,
                "rank": row["nomination_rank"],
                "selection_state": row["selection_state"],
                "admission_state": row["admission_state"],
            }
        )

    return {
        "case_id": case["case_id"],
        "package_sha256": package["package_sha256"],
        "candidate_ids": sorted(candidate_ids),
        "retained_ids": sorted(retained_ids),
        "admitted_ids": sorted(admitted_ids),
        "candidate_rows": candidate_rows,
        "score_diagnostics": _score_diagnostics(case["contract_a"], config, passage_map),
        "retained_count": len(
            [row for row in package["candidates"] if row["selection_state"] == "retained"]
        ),
        "normative_lane_count": len(package["retrieval_plans"]),
        "semantic_fields_present": any(
            token in json.dumps(package, sort_keys=True)
            for token in ("SUPPORTS", "REFUTES", '"verdict"')
        ),
    }


def _missing_stage(case_result: dict[str, Any], evidence_id: str) -> str | None:
    if evidence_id not in case_result["candidate_ids"]:
        return "candidate_pool"
    if evidence_id not in case_result["retained_ids"]:
        return "retention"
    if evidence_id not in case_result["admitted_ids"]:
        return "admission"
    return None


def _evaluate_eight(
    results: list[dict[str, Any]], gold: dict[str, Any]
) -> dict[str, Any]:
    by_case = {str(row["case_id"]): row for row in results}
    required: dict[str, dict[str, Any]] = {}
    for case_id, case_gold in sorted(gold["cases"].items()):
        for evidence_id in case_gold["required"]:
            stage = _missing_stage(by_case[case_id], str(evidence_id))
            required[str(evidence_id)] = {
                "case_id": case_id,
                "first_missing_stage": stage,
            }
    stage_counts = {"candidate_pool": 0, "retention": 0, "admission": 0}
    for row in required.values():
        stage = row["first_missing_stage"]
        if stage is not None:
            stage_counts[stage] += 1
    return {"required": required, "stage_counts": stage_counts}


def _baseline_reproduced(evaluation: dict[str, Any]) -> bool:
    observed_losses = {
        evidence_id: row["first_missing_stage"]
        for evidence_id, row in evaluation["required"].items()
        if row["first_missing_stage"] is not None
    }
    return observed_losses == EXPECTED_BASELINE_LOSSES


def _no_required_regression(
    baseline: dict[str, Any], successor: dict[str, Any]
) -> tuple[bool, list[dict[str, Any]]]:
    regressions: list[dict[str, Any]] = []
    for evidence_id, baseline_row in baseline["required"].items():
        before = baseline_row["first_missing_stage"]
        after = successor["required"][evidence_id]["first_missing_stage"]
        if STAGE_ORDINAL[after] < STAGE_ORDINAL[before]:
            regressions.append(
                {"evidence_id": evidence_id, "baseline": before, "successor": after}
            )
    return not regressions, regressions


def _profile_summary(
    case_results: list[dict[str, Any]], evaluation: dict[str, Any]
) -> dict[str, Any]:
    retained = sum(int(row["retained_count"]) for row in case_results)
    lanes = sum(int(row["normative_lane_count"]) for row in case_results)
    return {
        "qualification_case_count": len(case_results),
        "normative_lane_count": lanes,
        "retained_relationship_count": retained,
        "max_retained_per_lane": max(
            (
                len(
                    [
                        item
                        for item in row["candidate_rows"]
                        if item["proposition_id"] == proposition_id
                        and item["selection_state"] == "retained"
                    ]
                )
                for row in case_results
                for proposition_id in {
                    str(item["proposition_id"]) for item in row["candidate_rows"]
                }
            ),
            default=0,
        ),
        "missing_required_evidence_by_first_stage": evaluation["stage_counts"],
        "semantic_fields_present": any(
            bool(row["semantic_fields_present"]) for row in case_results
        ),
    }


def _validator_conformance(
    apparatus_root: Path, valid_contracts: list[dict[str, Any]]
) -> dict[str, Any]:
    sys.path.insert(0, str(apparatus_root))
    try:
        canonical = importlib.import_module("validators.contract_a")
    finally:
        sys.path.pop(0)

    def ours_accepts(value: dict[str, Any]) -> bool:
        try:
            validate_contract_a(deepcopy(value))
        except ValueError:
            return False
        return True

    def canonical_accepts(value: dict[str, Any]) -> bool:
        try:
            canonical.validate_candidate(deepcopy(value))
        except ValueError:
            return False
        return True

    rows: list[dict[str, Any]] = []
    for index, value in enumerate(valid_contracts):
        rows.append(
            {
                "case": f"valid-{index + 1}",
                "ours": ours_accepts(value),
                "canonical": canonical_accepts(value),
                "hash_equal": compute_handoff_sha256(value)
                == canonical.compute_handoff_sha256(value),
            }
        )

    base = deepcopy(valid_contracts[0])
    mutations: dict[str, dict[str, Any]] = {}

    mutated = deepcopy(base)
    mutated["root_proposition"]["text"] += " mutated"
    mutations["root_text_stale_hash"] = mutated

    mutated = deepcopy(base)
    mutated["decomposition"]["children"][1]["sequence"] = 3
    mutated["handoff_sha256"] = compute_handoff_sha256(mutated)
    mutations["noncontiguous_child_sequence"] = mutated

    mutated = deepcopy(base)
    mutated["sources"][1]["source_id"] = mutated["sources"][0]["source_id"]
    mutated["handoff_sha256"] = compute_handoff_sha256(mutated)
    mutations["duplicate_source_id"] = mutated

    mutated = deepcopy(base)
    mutated["unexpected"] = "field"
    mutated["handoff_sha256"] = compute_handoff_sha256(mutated)
    mutations["unknown_top_level_field"] = mutated

    mutated = deepcopy(base)
    mutated["sources"][0]["content"] += " changed"
    mutated["handoff_sha256"] = compute_handoff_sha256(mutated)
    mutations["source_content_stale_hash"] = mutated

    mutated = deepcopy(base)
    mutated["handoff_sha256"] = "sha256:" + "0" * 64
    mutations["stale_handoff_hash"] = mutated

    for name, value in mutations.items():
        rows.append(
            {
                "case": name,
                "ours": ours_accepts(value),
                "canonical": canonical_accepts(value),
                "hash_equal": compute_handoff_sha256(value)
                == canonical.compute_handoff_sha256(value),
            }
        )

    agreement = all(
        row["ours"] == row["canonical"] and bool(row["hash_equal"])
        for row in rows
    )
    return {"agreement": agreement, "cases": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eb-research-root", type=Path, required=True)
    parser.add_argument("--cal-research-root", type=Path, required=True)
    parser.add_argument("--apparatus-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    fixture_root = args.eb_research_root / "research/cal_rc0_contract_b_handoff/fixtures"
    eight_cases = [_read_json(path) for path in _case_files(fixture_root / "cases")]
    eight_admission = _read_json(fixture_root / "admission.json")
    gold = _read_json(fixture_root / "evaluator_gold.json")

    decoy_root = args.cal_research_root / "pipeline/cal_rc0/data_campaign/retrieval_aperture"
    decoy_cohort = _read_json(decoy_root / "cohort.json")
    decoy_case = decoy_cohort["cases"][0]
    decoy_admission = _read_json(decoy_root / "admission.json")

    valid_contracts = [case["contract_a"] for case in eight_cases] + [
        decoy_case["contract_a"]
    ]
    conformance = _validator_conformance(args.apparatus_root, valid_contracts)

    profile_results: dict[str, Any] = {}
    baseline_cases = [
        _run_case(case, eight_admission, candidate_depth=5, retained_k=3)
        for case in eight_cases
    ]
    baseline_eval = _evaluate_eight(baseline_cases, gold)
    baseline_decoy = _run_case(
        decoy_case,
        decoy_admission,
        candidate_depth=5,
        retained_k=3,
    )
    p6_baseline_stage = _missing_stage(baseline_decoy, "RET-AP-P6")
    profile_results["5/3"] = {
        "eight_case_evaluation": baseline_eval,
        "summary": _profile_summary(baseline_cases + [baseline_decoy], baseline_eval),
        "decoy_true_evidence_stage": p6_baseline_stage,
        "decoy": baseline_decoy,
    }

    ten_three_cases = [
        _run_case(case, eight_admission, candidate_depth=10, retained_k=3)
        for case in eight_cases
    ]
    ten_three_eval = _evaluate_eight(ten_three_cases, gold)
    no_regression_10_3, regressions_10_3 = _no_required_regression(
        baseline_eval, ten_three_eval
    )
    ten_three_decoy = _run_case(
        decoy_case,
        decoy_admission,
        candidate_depth=10,
        retained_k=3,
    )
    p6_10_3_stage = _missing_stage(ten_three_decoy, "RET-AP-P6")
    profile_results["10/3"] = {
        "eight_case_evaluation": ten_three_eval,
        "summary": _profile_summary(ten_three_cases + [ten_three_decoy], ten_three_eval),
        "decoy_true_evidence_stage": p6_10_3_stage,
        "required_evidence_regressions": regressions_10_3,
        "no_required_evidence_regression": no_regression_10_3,
        "decoy": ten_three_decoy,
    }

    chosen_profile: str | None = None
    discriminator_state: str
    ran_10_6 = False
    if p6_10_3_stage is None and no_regression_10_3:
        chosen_profile = "10/3"
        discriminator_state = "CLOSED_AT_10_3"
    elif p6_10_3_stage == "retention" and no_regression_10_3:
        ran_10_6 = True
        ten_six_cases = [
            _run_case(case, eight_admission, candidate_depth=10, retained_k=6)
            for case in eight_cases
        ]
        ten_six_eval = _evaluate_eight(ten_six_cases, gold)
        no_regression_10_6, regressions_10_6 = _no_required_regression(
            baseline_eval, ten_six_eval
        )
        ten_six_decoy = _run_case(
            decoy_case,
            decoy_admission,
            candidate_depth=10,
            retained_k=6,
        )
        p6_10_6_stage = _missing_stage(ten_six_decoy, "RET-AP-P6")
        profile_results["10/6"] = {
            "eight_case_evaluation": ten_six_eval,
            "summary": _profile_summary(ten_six_cases + [ten_six_decoy], ten_six_eval),
            "decoy_true_evidence_stage": p6_10_6_stage,
            "required_evidence_regressions": regressions_10_6,
            "no_required_evidence_regression": no_regression_10_6,
            "decoy": ten_six_decoy,
        }
        if p6_10_6_stage is None and no_regression_10_6:
            chosen_profile = "10/6"
            discriminator_state = "CLOSED_AT_10_6"
        else:
            discriminator_state = "UNRESOLVED_AT_AUTHORIZED_BOUND"
    else:
        discriminator_state = "UNRESOLVED_AT_10_3"

    baseline_reproduced = _baseline_reproduced(baseline_eval)
    preserved_defect_reproduced = p6_baseline_stage == "candidate_pool"
    semantic_leak = any(
        bool(profile["summary"]["semantic_fields_present"])
        for profile in profile_results.values()
    )
    qualification_pass = (
        conformance["agreement"]
        and baseline_reproduced
        and preserved_defect_reproduced
        and chosen_profile is not None
        and not semantic_leak
    )

    receipt = {
        "schema": "evidence-bundler-v1-convergence-qualification-v1",
        "authority": {
            "eb_research_head": "dd4fb2b89f351fbdcd8b08e48dd9d7d1f10c2d05",
            "cal_decoy_head": "7a46d61585f868a2e904f870528f605fb06772ea",
            "contract_a_release_commit": "529c92b49a34d5c610618551a8737f019f9fa332",
            "contract_a_validator_blob": "42e5f5b3bf38d677445e9d01ea130ba604e53409",
        },
        "contract_a_conformance": conformance,
        "baseline_eight_case_reproduced": baseline_reproduced,
        "preserved_decoy_defect_reproduced": preserved_defect_reproduced,
        "profile_sequence": ["5/3", "10/3"] + (["10/6"] if ran_10_6 else []),
        "profiles": profile_results,
        "selected_profile": chosen_profile,
        "discriminator_state": discriminator_state,
        "package_score_policy": {
            "bm25_score_in_v1_package": False,
            "raw_scores_preserved_in_qualification_receipt": True,
        },
        "semantic_authority_leak_observed": semantic_leak,
        "qualification_pass": qualification_pass,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(_canonical_bytes(receipt))
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if qualification_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
