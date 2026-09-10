from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from evidence_bundler.contracts.factual_context import (
    ContractBFactualContext,
    canonical_bytes as extension_canonical_bytes,
    validate_for_bundle,
)
from evidence_bundler.contracts.writer import validate_bundle_tree
from research.cal_rc0_contract_b_handoff.build_handoff import (
    build_runtime_receipt,
    canonical_bytes,
)
from research.cal_rc0_contract_b_handoff.fixture_loader import load_cohort
from research.cal_rc0_contract_b_handoff.qualified_handoff import (
    build_all_contract_b_qualified,
)

SCHEMA = "contract-b-evidence-package-recoverability-rc1-result-v1"
BASE_SHA = "dd4fb2b89f351fbdcd8b08e48dd9d7d1f10c2d05"
CONTRACT_B_AUTHORITY = "c314e53bd91c0736aa4370a364673b069aceb43e"
EXTENSION_REL = Path("extensions/contract-b-factual-context-v1.json")


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected mapping in {path}")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_contract_b_only(bundle_dir: Path) -> dict[str, Any]:
    """Independent structural reader whose only input is a Contract B bundle tree."""
    claims: list[dict[str, Any]] = []
    for path in sorted((bundle_dir / "claims").glob("*.yaml")):
        row = _load_yaml(path)
        claims.append(
            {
                "claim_id": row["claim_id"],
                "claim_text": row["claim_text"],
                "schema_version": row["schema_version"],
            }
        )

    sources: list[dict[str, Any]] = []
    passages: list[dict[str, Any]] = []
    passage_source: dict[str, str] = {}
    evidence_root = bundle_dir / "evidence"
    for source_dir in sorted(path for path in evidence_root.iterdir() if path.is_dir()):
        source = _load_yaml(source_dir / "source_profile.yaml")
        sources.append(
            {
                "source_id": source["source_id"],
                "content_hash": source["content_hash"],
                "bibliographic": source["bibliographic"],
                "trust_level": source["trust_level"],
            }
        )
        for path in sorted((source_dir / "passages").glob("*.yaml")):
            passage = _load_yaml(path)
            passage_source[str(passage["passage_id"])] = str(passage["source_id"])
            passages.append(
                {
                    "passage_id": passage["passage_id"],
                    "source_id": passage["source_id"],
                    "passage_text": passage["passage_text"],
                    "passage_hash": passage["passage_hash"],
                    "char_start": passage["char_start"],
                    "char_end": passage["char_end"],
                    "provenance": passage["provenance"],
                }
            )

    extension = json.loads((bundle_dir / EXTENSION_REL).read_text(encoding="utf-8"))
    history = extension["history"]
    admitted_projection = sorted(
        {
            (
                str(row["claim_id"]),
                str(row["passage_id"]),
                passage_source[str(row["passage_id"])],
            )
            for row in history
            if row["review"]["decision"] == "accepted"
        }
    )
    return {
        "claims": claims,
        "sources": sources,
        "passages": passages,
        "lineage": extension["claims"],
        "history_complete": extension["history_complete"],
        "history": history,
        "history_count_checks": extension["history_count_checks"],
        "aperture": extension["aperture"],
        "admitted_projection": [list(row) for row in admitted_projection],
        "extension_sha256": _sha256((bundle_dir / EXTENSION_REL).read_bytes()),
    }


def _keys(rows: list[dict[str, Any]]) -> list[list[str]]:
    return sorted(
        [str(row["proposition_id"]), str(row["evidence_id"])] for row in rows
    )


def _history_keys(history: list[dict[str, Any]]) -> list[list[str]]:
    return sorted([str(row["claim_id"]), str(row["passage_id"])] for row in history)


def _review_map_from_runtime(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {
        f"{row['proposition_id']}\0{row['evidence_id']}": str(row["decision"])
        for row in rows
    }


def _review_map_from_b(history: list[dict[str, Any]]) -> dict[str, str]:
    return {
        f"{row['claim_id']}\0{row['passage_id']}": str(row["review"]["decision"])
        for row in history
    }


def _aperture_candidate_counts(aperture: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in aperture:
        outcome = row["outcome"]
        if outcome["state"] != "known":
            continue
        value = outcome["value"]
        if isinstance(value, dict) and isinstance(value.get("candidate_count"), int):
            counts[str(row["claim_id"])] = int(value["candidate_count"])
    return counts


def _runtime_candidate_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row["proposition_id"])] += 1
    return dict(counts)


def _admitted_projection_from_extension_dict(
    extension: dict[str, Any], passage_source: dict[str, str]
) -> list[list[str]]:
    return sorted(
        [
            str(row["claim_id"]),
            str(row["passage_id"]),
            passage_source[str(row["passage_id"])],
        ]
        for row in extension["history"]
        if row["review"]["decision"] == "accepted"
    )


def run_mutations(bundle_dir: Path, reader: dict[str, Any]) -> dict[str, Any]:
    extension_path = bundle_dir / EXTENSION_REL
    original = json.loads(extension_path.read_text(encoding="utf-8"))
    passage_source = {str(row["passage_id"]): str(row["source_id"]) for row in reader["passages"]}
    results: dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="eb-b-unsealed-") as td:
        mutated_bundle = Path(td) / "bundle"
        shutil.copytree(bundle_dir, mutated_bundle)
        mutated = copy.deepcopy(original)
        mutated["history"][0]["nomination"]["score"] = float(
            mutated["history"][0]["nomination"].get("score", 0.0)
        ) + 0.125
        (mutated_bundle / EXTENSION_REL).write_text(
            json.dumps(mutated, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
        errors = validate_bundle_tree(mutated_bundle)
        results["unsealed_extension_mutation"] = {
            "passed": bool(errors),
            "error_count": len(errors),
            "errors": errors,
        }

    removed = copy.deepcopy(original)
    removed["history"] = removed["history"][1:]
    removed_model = ContractBFactualContext.model_validate(removed)
    removed_errors = validate_for_bundle(bundle_dir, removed_model)
    results["history_removed_with_stale_counts"] = {
        "passed": any("history count mismatch" in error for error in removed_errors),
        "errors": removed_errors,
    }

    duplicated = copy.deepcopy(original)
    duplicated["history"].append(copy.deepcopy(duplicated["history"][0]))
    duplicated_model = ContractBFactualContext.model_validate(duplicated)
    duplicate_errors = validate_for_bundle(bundle_dir, duplicated_model)
    results["duplicate_history_identity"] = {
        "passed": any("duplicate link_id" in error for error in duplicate_errors),
        "errors": duplicate_errors,
    }

    prohibited = copy.deepcopy(original)
    prohibited["history"][0]["nomination"]["support"] = True
    prohibited_model = ContractBFactualContext.model_validate(prohibited)
    prohibited_errors = validate_for_bundle(bundle_dir, prohibited_model)
    results["prohibited_semantic_field"] = {
        "passed": any("prohibited proposition-specific field" in error for error in prohibited_errors),
        "errors": prohibited_errors,
    }

    bad_unknown = copy.deepcopy(original)
    bad_unknown["claims"][0]["atomicity"] = {"state": "unknown", "value": "invented-default"}
    try:
        ContractBFactualContext.model_validate(bad_unknown)
    except ValidationError as exc:
        results["unknown_with_non_null_value"] = {
            "passed": True,
            "error_count": len(exc.errors()),
        }
    else:
        results["unknown_with_non_null_value"] = {"passed": False, "error_count": 0}

    score_mutation = copy.deepcopy(original)
    score_mutation["history"][0]["nomination"]["score"] = float(
        score_mutation["history"][0]["nomination"].get("score", 0.0)
    ) + 0.125
    score_model = ContractBFactualContext.model_validate(score_mutation)
    score_errors = validate_for_bundle(bundle_dir, score_model)
    before_projection = _admitted_projection_from_extension_dict(original, passage_source)
    after_projection = _admitted_projection_from_extension_dict(score_mutation, passage_source)
    original_model = ContractBFactualContext.model_validate(original)
    results["nomination_score_separation"] = {
        "passed": (
            not score_errors
            and _sha256(extension_canonical_bytes(original_model))
            != _sha256(extension_canonical_bytes(score_model))
            and before_projection == after_projection
        ),
        "validation_errors": score_errors,
        "audit_record_changed": _sha256(extension_canonical_bytes(original_model))
        != _sha256(extension_canonical_bytes(score_model)),
        "admitted_projection_unchanged": before_projection == after_projection,
    }
    return results


def run(research_root: Path) -> dict[str, Any]:
    fixtures = research_root / "fixtures"
    cohort = load_cohort(fixtures)
    admission = json.loads((fixtures / "admission.json").read_text(encoding="utf-8"))
    carrier = json.loads(
        (fixtures / "contract_b_compatibility_carrier.json").read_text(encoding="utf-8")
    )
    profile = json.loads((research_root / "RESEARCH_EB_PROFILE.json").read_text(encoding="utf-8"))
    runtime = build_runtime_receipt(cohort=cohort, admission=admission, profile=profile)

    with tempfile.TemporaryDirectory(prefix="eb-b-recoverability-") as td:
        out_dir = Path(td) / "qualified"
        build_all_contract_b_qualified(
            cohort=cohort,
            receipt=runtime,
            profile=profile,
            compatibility_carrier=carrier,
            out_dir=out_dir,
        )

        runtime_by_case = {str(row["case_id"]): row for row in runtime["cases"]}
        cases: list[dict[str, Any]] = []
        first_bundle: Path | None = None
        first_reader: dict[str, Any] | None = None

        for case_id in sorted(runtime_by_case):
            bundle_dir = out_dir / "contract_b" / case_id
            if first_bundle is None:
                first_bundle = bundle_dir
            validation_errors = validate_bundle_tree(bundle_dir)
            reader = read_contract_b_only(bundle_dir)
            if first_reader is None:
                first_reader = reader
            runtime_case = runtime_by_case[case_id]

            runtime_candidates = _keys(runtime_case["candidate_pool"])
            runtime_retained = _keys(runtime_case["retained"])
            b_history = _history_keys(reader["history"])
            candidate_counts_runtime = _runtime_candidate_counts(runtime_case["candidate_pool"])
            candidate_counts_b = _aperture_candidate_counts(reader["aperture"])

            cases.append(
                {
                    "case_id": case_id,
                    "bundle_validation_pass": not validation_errors,
                    "bundle_validation_errors": validation_errors,
                    "retained_identity_recoverable": b_history == runtime_retained,
                    "review_state_recoverable": _review_map_from_b(reader["history"])
                    == _review_map_from_runtime(runtime_case["admission"]),
                    "candidate_counts_recoverable": candidate_counts_b == candidate_counts_runtime,
                    "pre_retention_candidate_identity_recoverable": b_history == runtime_candidates,
                    "runtime_candidate_count": len(runtime_candidates),
                    "runtime_retained_count": len(runtime_retained),
                    "contract_b_history_count": len(b_history),
                    "candidate_identities_missing_from_b": sorted(
                        row for row in runtime_candidates if row not in b_history
                    ),
                    "reader": reader,
                }
            )

        if first_bundle is None or first_reader is None:
            raise ValueError("qualification cohort produced no Contract B bundles")
        mutations = run_mutations(first_bundle, first_reader)

    criteria = {
        "canonical_bundle_validation": all(row["bundle_validation_pass"] for row in cases),
        "retained_nomination_identity": all(row["retained_identity_recoverable"] for row in cases),
        "retained_review_admission_state": all(row["review_state_recoverable"] for row in cases),
        "candidate_counts": all(row["candidate_counts_recoverable"] for row in cases),
        "pre_retention_candidate_identity": all(
            row["pre_retention_candidate_identity_recoverable"] for row in cases
        ),
        "mutation_checks": all(row["passed"] for row in mutations.values()),
    }

    if not criteria["canonical_bundle_validation"] or not criteria["mutation_checks"]:
        disposition = "INVALID_APPARATUS"
    elif all(criteria.values()):
        disposition = "SUPPORTED_WITHIN_TESTED_APERTURE"
    else:
        disposition = "PARTIAL_RECOVERABILITY"

    missing = [
        {
            "case_id": row["case_id"],
            "missing": row["candidate_identities_missing_from_b"],
        }
        for row in cases
        if row["candidate_identities_missing_from_b"]
    ]
    return {
        "schema": SCHEMA,
        "frozen_base_sha": BASE_SHA,
        "contract_b_authority_sha": CONTRACT_B_AUTHORITY,
        "case_count": len(cases),
        "disposition": disposition,
        "criteria": criteria,
        "mutation_checks": mutations,
        "pre_retention_identity_gaps": missing,
        "cases": cases,
        "interpretation_boundary": {
            "contract_b_schema_violation_claimed": False,
            "retrieval_quality_claimed": False,
            "cal_called": False,
            "production_promotion_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--research-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.research_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(canonical_bytes(result))
    print(json.dumps({
        "disposition": result["disposition"],
        "criteria": result["criteria"],
        "pre_retention_identity_gap_cases": len(result["pre_retention_identity_gaps"]),
    }, sort_keys=True))
    return 2 if result["disposition"] == "INVALID_APPARATUS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
