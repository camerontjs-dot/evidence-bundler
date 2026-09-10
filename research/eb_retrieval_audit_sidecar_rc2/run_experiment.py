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

from evidence_bundler.contracts.factual_context import _reseal
from evidence_bundler.contracts.writer import validate_bundle_tree
from research.cal_rc0_contract_b_handoff.build_handoff import (
    build_runtime_receipt,
    canonical_bytes,
)
from research.cal_rc0_contract_b_handoff.fixture_loader import load_cohort
from research.cal_rc0_contract_b_handoff.qualified_handoff import (
    build_all_contract_b_qualified,
)
from research.contract_b_evidence_package_recoverability_rc1.run_experiment import (
    _aperture_candidate_counts,
    _review_map_from_b,
    _review_map_from_runtime,
    read_contract_b_only,
)

SCHEMA = "eb-retrieval-audit-sidecar-rc2-result-v1"
SIDECAR_SCHEMA = "eb-retrieval-audit-v1"
ENVELOPE_SCHEMA = "eb-evidence-package-envelope-v1"
BASE_SHA = "f5e257904bef731b5798233ad53caa709136c810"
CONTRACT_B_AUTHORITY = "c314e53bd91c0736aa4370a364673b069aceb43e"
SIDECAR_NAME = "EB_RETRIEVAL_AUDIT.json"
ENVELOPE_NAME = "EB_EVIDENCE_PACKAGE_ENVELOPE.json"
PROHIBITED_SEMANTIC_KEYS = {
    "support",
    "refutation",
    "proposition_specific_relation",
    "semantic_validity",
    "temporal_applicability",
    "authority_applicability",
    "supplier_applicability",
    "completeness_conclusion",
    "decision_participation",
    "audit_support_verdict",
    "verdict",
    "abstention",
}
PROHIBITED_REVIEW_KEYS = {"review", "admission", "accepted", "rejected", "needs-review"}


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _text_sha256(text: str) -> str:
    return _sha256(text.encode("utf-8"))


def _canonical(value: Any) -> bytes:
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


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected mapping in {path}")
    return value


def _tree_snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): _sha256(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_walk_keys(child))
    return keys


def _candidate_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row["query_id"]), str(row["evidence_id"])


def _prop_evidence_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row["proposition_id"]), str(row["evidence_id"])


def _bundle_binding(bundle_dir: Path) -> dict[str, str]:
    manifest = _load_yaml(bundle_dir / "bundle_manifest.yaml")
    return {
        "bundle_id": str(manifest["bundle_id"]),
        "contract_b_version": str(manifest["schema_version"]),
        "bundle_hash": str(manifest["bundle"]["bundle_hash"]),
    }


def build_sidecar(
    *,
    case: dict[str, Any],
    runtime_case: dict[str, Any],
    runtime: dict[str, Any],
    bundle_dir: Path,
) -> dict[str, Any]:
    retained_keys = {_candidate_key(row) for row in runtime_case["retained"]}
    proposition_text = {
        str(runtime_case["root_proposition"]["proposition_id"]): str(
            runtime_case["root_proposition"]["text"]
        )
    }
    for child in runtime_case["declared_children"]:
        proposition_text[str(child["proposition_id"])] = str(child["text"])

    queries: dict[str, dict[str, Any]] = {}
    candidates: list[dict[str, Any]] = []
    candidate_ids: set[str] = set()
    for row in runtime_case["candidate_pool"]:
        qid = str(row["query_id"])
        proposition_id = str(row["proposition_id"])
        queries.setdefault(
            qid,
            {
                "query_id": qid,
                "proposition_id": proposition_id,
                "proposition_role": str(row["proposition_role"]),
                "retrieval_lane": str(row["retrieval_lane"]),
                "query_text": proposition_text[proposition_id],
            },
        )
        candidate_ids.add(str(row["evidence_id"]))
        candidates.append(
            {
                "query_id": qid,
                "proposition_id": proposition_id,
                "proposition_role": str(row["proposition_role"]),
                "retrieval_lane": str(row["retrieval_lane"]),
                "evidence_id": str(row["evidence_id"]),
                "source_id": str(row["source_id"]),
                "rank": int(row["rank"]),
                "score": row["score"],
                "score_kind": str(row["score_kind"]),
                "retained": _candidate_key(row) in retained_keys,
            }
        )

    passage_by_id = {str(row["evidence_id"]): row for row in case["passages"]}
    source_hash_by_id = {
        str(row["source_id"]): str(row["content_sha256"])
        for row in case["contract_a"]["sources"]
    }
    candidate_passages = []
    for evidence_id in sorted(candidate_ids):
        passage = passage_by_id[evidence_id]
        text = str(passage["text"])
        source_id = str(passage["source_id"])
        candidate_passages.append(
            {
                "evidence_id": evidence_id,
                "source_id": source_id,
                "passage_text": text,
                "passage_sha256": _text_sha256(text),
                "source_content_sha256": source_hash_by_id[source_id],
            }
        )

    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in candidates:
        values = counts[str(row["proposition_id"])]
        values[0] += 1
        if row["retained"]:
            values[1] += 1

    query_rows = []
    for qid, row in sorted(queries.items()):
        query_candidates = [candidate for candidate in candidates if candidate["query_id"] == qid]
        item = dict(row)
        item["candidate_count"] = len(query_candidates)
        item["retained_count"] = sum(bool(candidate["retained"]) for candidate in query_candidates)
        query_rows.append(item)

    return {
        "schema": SIDECAR_SCHEMA,
        "case_id": str(runtime_case["case_id"]),
        "candidate_history_complete": True,
        "contract_b_binding": _bundle_binding(bundle_dir),
        "retrieval_profile_sha256": str(runtime["profile_sha256"]),
        "queries": query_rows,
        "candidates": sorted(candidates, key=lambda row: (row["query_id"], row["rank"], row["evidence_id"])),
        "candidate_passages": candidate_passages,
        "count_checks": [
            {
                "proposition_id": proposition_id,
                "candidate": values[0],
                "retained": values[1],
            }
            for proposition_id, values in sorted(counts.items())
        ],
        "authority_boundary": {
            "retrieval_audit_only": True,
            "semantic_judgment_authority": False,
            "admission_authority": False,
        },
    }


def build_envelope(sidecar: dict[str, Any], bundle_dir: Path) -> dict[str, Any]:
    return {
        "schema": ENVELOPE_SCHEMA,
        "case_id": str(sidecar["case_id"]),
        "integrity_mode": "sha256-content-binding-only",
        "authentication_provided": False,
        "contract_b": _bundle_binding(bundle_dir),
        "retrieval_audit": {
            "schema": SIDECAR_SCHEMA,
            "sha256": _sha256(_canonical(sidecar)),
        },
    }


def write_package(package_dir: Path, source_bundle: Path, sidecar: dict[str, Any]) -> None:
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)
    bundle_dir = package_dir / "contract_b"
    shutil.copytree(source_bundle, bundle_dir)
    (package_dir / SIDECAR_NAME).write_bytes(_canonical(sidecar))
    envelope = build_envelope(sidecar, bundle_dir)
    (package_dir / ENVELOPE_NAME).write_bytes(_canonical(envelope))


def verify_package(package_dir: Path) -> list[str]:
    errors: list[str] = []
    bundle_dir = package_dir / "contract_b"
    sidecar_path = package_dir / SIDECAR_NAME
    envelope_path = package_dir / ENVELOPE_NAME

    b_errors = validate_bundle_tree(bundle_dir)
    errors.extend(f"contract B invalid: {error}" for error in b_errors)

    try:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return errors + [f"package parse failure: {exc}"]

    if sidecar_path.read_bytes() != _canonical(sidecar):
        errors.append("sidecar is not canonical JSON")
    if envelope_path.read_bytes() != _canonical(envelope):
        errors.append("envelope is not canonical JSON")
    if sidecar.get("schema") != SIDECAR_SCHEMA:
        errors.append("sidecar schema mismatch")
    if envelope.get("schema") != ENVELOPE_SCHEMA:
        errors.append("envelope schema mismatch")
    if sidecar.get("candidate_history_complete") is not True:
        errors.append("candidate history is not declared complete")

    actual_binding = _bundle_binding(bundle_dir)
    if sidecar.get("contract_b_binding") != actual_binding:
        errors.append("sidecar Contract B binding mismatch")
    if envelope.get("contract_b") != actual_binding:
        errors.append("envelope Contract B binding mismatch")
    if envelope.get("case_id") != sidecar.get("case_id"):
        errors.append("envelope case identity mismatch")
    expected_sidecar_hash = _sha256(sidecar_path.read_bytes())
    observed_sidecar_hash = envelope.get("retrieval_audit", {}).get("sha256")
    if observed_sidecar_hash != expected_sidecar_hash:
        errors.append("sidecar sha256 mismatch")
    if envelope.get("retrieval_audit", {}).get("schema") != SIDECAR_SCHEMA:
        errors.append("envelope sidecar schema mismatch")
    if envelope.get("integrity_mode") != "sha256-content-binding-only":
        errors.append("integrity mode mismatch")
    if envelope.get("authentication_provided") is not False:
        errors.append("unexpected authentication claim")

    all_keys = _walk_keys(sidecar)
    semantic_keys = sorted(all_keys.intersection(PROHIBITED_SEMANTIC_KEYS))
    if semantic_keys:
        errors.append("prohibited semantic keys in sidecar: " + ",".join(semantic_keys))
    review_keys = sorted(all_keys.intersection(PROHIBITED_REVIEW_KEYS))
    if review_keys:
        errors.append("review/admission keys duplicated into sidecar: " + ",".join(review_keys))

    candidates = sidecar.get("candidates", [])
    if not isinstance(candidates, list):
        errors.append("candidates is not an array")
        return errors
    candidate_keys = [_candidate_key(row) for row in candidates]
    if len(candidate_keys) != len(set(candidate_keys)):
        errors.append("duplicate candidate identity")

    query_by_id = {str(row["query_id"]): row for row in sidecar.get("queries", [])}
    if len(query_by_id) != len(sidecar.get("queries", [])):
        errors.append("duplicate query identity")
    for qid, query in query_by_id.items():
        rows = [row for row in candidates if str(row["query_id"]) == qid]
        ranks = sorted(int(row["rank"]) for row in rows)
        if ranks != list(range(1, len(rows) + 1)):
            errors.append(f"non-contiguous candidate ranks for {qid}")
        if int(query["candidate_count"]) != len(rows):
            errors.append(f"query candidate count mismatch for {qid}")
        if int(query["retained_count"]) != sum(bool(row["retained"]) for row in rows):
            errors.append(f"query retained count mismatch for {qid}")
    unknown_queries = sorted({str(row["query_id"]) for row in candidates} - set(query_by_id))
    if unknown_queries:
        errors.append("candidate references unknown query: " + ",".join(unknown_queries))

    passage_by_id = {
        str(row["evidence_id"]): row for row in sidecar.get("candidate_passages", [])
    }
    if len(passage_by_id) != len(sidecar.get("candidate_passages", [])):
        errors.append("duplicate candidate passage identity")
    candidate_evidence_ids = {str(row["evidence_id"]) for row in candidates}
    if set(passage_by_id) != candidate_evidence_ids:
        errors.append("candidate passage identity coverage mismatch")
    for evidence_id, passage in passage_by_id.items():
        if passage.get("passage_sha256") != _text_sha256(str(passage.get("passage_text", ""))):
            errors.append(f"candidate passage hash mismatch for {evidence_id}")
        sources = {
            str(row["source_id"])
            for row in candidates
            if str(row["evidence_id"]) == evidence_id
        }
        if sources != {str(passage.get("source_id"))}:
            errors.append(f"candidate passage source mismatch for {evidence_id}")

    derived_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in candidates:
        values = derived_counts[str(row["proposition_id"])]
        values[0] += 1
        if row["retained"]:
            values[1] += 1
    supplied_counts = {
        str(row["proposition_id"]): (int(row["candidate"]), int(row["retained"]))
        for row in sidecar.get("count_checks", [])
    }
    expected_counts = {key: tuple(value) for key, value in derived_counts.items()}
    if supplied_counts != expected_counts:
        errors.append("candidate count mismatch")

    return errors


def _sidecar_candidate_keys(sidecar: dict[str, Any]) -> set[tuple[str, str]]:
    return {_candidate_key(row) for row in sidecar["candidates"]}


def _sidecar_retained_prop_keys(sidecar: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        _prop_evidence_key(row)
        for row in sidecar["candidates"]
        if bool(row["retained"])
    }


def _runtime_prop_keys(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {_prop_evidence_key(row) for row in rows}


def _b_history_prop_keys(reader: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (str(row["claim_id"]), str(row["passage_id"]))
        for row in reader["history"]
    }


def run_mutations(package_dirs: list[Path]) -> dict[str, Any]:
    if len(package_dirs) < 2:
        raise ValueError("mutation suite requires at least two packages")
    first = package_dirs[0]
    second = package_dirs[1]
    results: dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="eb-sidecar-byte-") as td:
        mutated = Path(td) / "package"
        shutil.copytree(first, mutated)
        path = mutated / SIDECAR_NAME
        sidecar = json.loads(path.read_text(encoding="utf-8"))
        sidecar["candidate_passages"][0]["passage_text"] += " tamper"
        path.write_bytes(_canonical(sidecar))
        errors = verify_package(mutated)
        results["sidecar_byte_tamper"] = {
            "passed": "sidecar sha256 mismatch" in errors,
            "errors": errors,
        }

    with tempfile.TemporaryDirectory(prefix="eb-sidecar-omit-") as td:
        mutated = Path(td) / "package"
        shutil.copytree(first, mutated)
        path = mutated / SIDECAR_NAME
        sidecar = json.loads(path.read_text(encoding="utf-8"))
        sidecar["candidates"] = sidecar["candidates"][1:]
        path.write_bytes(_canonical(sidecar))
        errors = verify_package(mutated)
        results["candidate_omission_stale_envelope"] = {
            "passed": "sidecar sha256 mismatch" in errors,
            "errors": errors,
        }

    with tempfile.TemporaryDirectory(prefix="eb-sidecar-omit-refresh-") as td:
        mutated = Path(td) / "package"
        shutil.copytree(first, mutated)
        sidecar_path = mutated / SIDECAR_NAME
        envelope_path = mutated / ENVELOPE_NAME
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        sidecar["candidates"] = sidecar["candidates"][1:]
        sidecar_path.write_bytes(_canonical(sidecar))
        envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
        envelope["retrieval_audit"]["sha256"] = _sha256(sidecar_path.read_bytes())
        envelope_path.write_bytes(_canonical(envelope))
        errors = verify_package(mutated)
        results["candidate_omission_refreshed_envelope_stale_counts"] = {
            "passed": any("count mismatch" in error for error in errors),
            "errors": errors,
        }

    with tempfile.TemporaryDirectory(prefix="eb-sidecar-swap-") as td:
        mutated = Path(td) / "package"
        mutated.mkdir(parents=True)
        shutil.copytree(first / "contract_b", mutated / "contract_b")
        shutil.copy2(second / SIDECAR_NAME, mutated / SIDECAR_NAME)
        shutil.copy2(second / ENVELOPE_NAME, mutated / ENVELOPE_NAME)
        errors = verify_package(mutated)
        results["cross_case_swap"] = {
            "passed": any("Contract B binding mismatch" in error for error in errors),
            "errors": errors,
        }

    with tempfile.TemporaryDirectory(prefix="eb-sidecar-b-unsealed-") as td:
        mutated = Path(td) / "package"
        shutil.copytree(first, mutated)
        manifest_path = mutated / "contract_b" / "bundle_manifest.yaml"
        manifest_path.write_text(manifest_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        errors = verify_package(mutated)
        results["unsealed_contract_b_tamper"] = {
            "passed": any(error.startswith("contract B invalid:") for error in errors),
            "errors": errors,
        }

    with tempfile.TemporaryDirectory(prefix="eb-sidecar-b-resealed-") as td:
        mutated = Path(td) / "package"
        shutil.copytree(first, mutated)
        bundle_dir = mutated / "contract_b"
        manifest_path = bundle_dir / "bundle_manifest.yaml"
        manifest = _load_yaml(manifest_path)
        manifest["generated_at_utc"] = "2026-09-06T00:00:01Z"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        _reseal(bundle_dir)
        b_errors = validate_bundle_tree(bundle_dir)
        errors = verify_package(mutated)
        results["resealed_contract_b_mutation"] = {
            "passed": not b_errors and "envelope Contract B binding mismatch" in errors,
            "contract_b_validation_errors": b_errors,
            "errors": errors,
        }

    with tempfile.TemporaryDirectory(prefix="eb-sidecar-score-") as td:
        mutated = Path(td) / "package"
        shutil.copytree(first, mutated)
        before_b = _tree_snapshot(mutated / "contract_b")
        before_projection = read_contract_b_only(mutated / "contract_b")["admitted_projection"]
        sidecar_path = mutated / SIDECAR_NAME
        envelope_path = mutated / ENVELOPE_NAME
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        sidecar["candidates"][0]["score"] = float(sidecar["candidates"][0]["score"]) + 0.125
        sidecar_path.write_bytes(_canonical(sidecar))
        envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
        envelope["retrieval_audit"]["sha256"] = _sha256(sidecar_path.read_bytes())
        envelope_path.write_bytes(_canonical(envelope))
        errors = verify_package(mutated)
        after_b = _tree_snapshot(mutated / "contract_b")
        after_projection = read_contract_b_only(mutated / "contract_b")["admitted_projection"]
        results["nomination_score_only"] = {
            "passed": not errors and before_b == after_b and before_projection == after_projection,
            "errors": errors,
            "contract_b_bytes_unchanged": before_b == after_b,
            "admitted_projection_unchanged": before_projection == after_projection,
        }

    return results


def run(research_root: Path, artifact_root: Path) -> dict[str, Any]:
    fixtures = research_root / "fixtures"
    cohort = load_cohort(fixtures)
    admission = json.loads((fixtures / "admission.json").read_text(encoding="utf-8"))
    carrier = json.loads(
        (fixtures / "contract_b_compatibility_carrier.json").read_text(encoding="utf-8")
    )
    profile = json.loads((research_root / "RESEARCH_EB_PROFILE.json").read_text(encoding="utf-8"))
    runtime = build_runtime_receipt(cohort=cohort, admission=admission, profile=profile)
    case_by_id = {str(row["case_id"]): row for row in cohort["cases"]}
    runtime_by_case = {str(row["case_id"]): row for row in runtime["cases"]}

    artifact_root.mkdir(parents=True, exist_ok=True)
    packages_root = artifact_root / "packages"
    if packages_root.exists():
        shutil.rmtree(packages_root)
    packages_root.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="eb-sidecar-rc2-") as td:
        built_root = Path(td) / "qualified"
        build_all_contract_b_qualified(
            cohort=cohort,
            receipt=runtime,
            profile=profile,
            compatibility_carrier=carrier,
            out_dir=built_root,
        )

        cases: list[dict[str, Any]] = []
        package_dirs: list[Path] = []
        for case_id in sorted(runtime_by_case):
            source_bundle = built_root / "contract_b" / case_id
            source_snapshot = _tree_snapshot(source_bundle)
            b_errors = validate_bundle_tree(source_bundle)
            sidecar = build_sidecar(
                case=case_by_id[case_id],
                runtime_case=runtime_by_case[case_id],
                runtime=runtime,
                bundle_dir=source_bundle,
            )
            package_dir = packages_root / case_id
            write_package(package_dir, source_bundle, sidecar)
            package_dirs.append(package_dir)

            verify_errors = verify_package(package_dir)
            packaged_snapshot = _tree_snapshot(package_dir / "contract_b")
            b_reader = read_contract_b_only(package_dir / "contract_b")
            loaded_sidecar = json.loads((package_dir / SIDECAR_NAME).read_text(encoding="utf-8"))
            runtime_case = runtime_by_case[case_id]

            runtime_candidates = {_candidate_key(row) for row in runtime_case["candidate_pool"]}
            sidecar_candidates = _sidecar_candidate_keys(loaded_sidecar)
            runtime_retained_prop = _runtime_prop_keys(runtime_case["retained"])
            sidecar_retained_prop = _sidecar_retained_prop_keys(loaded_sidecar)
            b_history_prop = _b_history_prop_keys(b_reader)
            sidecar_passage_ids = {
                str(row["evidence_id"]) for row in loaded_sidecar["candidate_passages"]
            }
            candidate_passage_complete = sidecar_passage_ids == {
                str(row["evidence_id"]) for row in runtime_case["candidate_pool"]
            } and all(
                row["passage_sha256"] == _text_sha256(str(row["passage_text"]))
                and bool(row["source_id"])
                and bool(row["source_content_sha256"])
                for row in loaded_sidecar["candidate_passages"]
            )

            runtime_counts: dict[str, int] = defaultdict(int)
            for row in runtime_case["candidate_pool"]:
                runtime_counts[str(row["proposition_id"])] += 1
            sidecar_counts = {
                str(row["proposition_id"]): int(row["candidate"])
                for row in loaded_sidecar["count_checks"]
            }
            b_counts = _aperture_candidate_counts(b_reader["aperture"])

            cases.append(
                {
                    "case_id": case_id,
                    "canonical_contract_b_valid": not b_errors,
                    "canonical_contract_b_validation_errors": b_errors,
                    "contract_b_bytes_unchanged": source_snapshot == packaged_snapshot,
                    "package_verification_pass": not verify_errors,
                    "package_verification_errors": verify_errors,
                    "pre_retention_candidate_identity_recoverable": sidecar_candidates == runtime_candidates,
                    "candidate_passage_content_recoverable": candidate_passage_complete,
                    "sidecar_retention_matches_runtime": sidecar_retained_prop == runtime_retained_prop,
                    "contract_b_retained_matches_sidecar": b_history_prop == sidecar_retained_prop,
                    "contract_b_review_state_unchanged": _review_map_from_b(b_reader["history"])
                    == _review_map_from_runtime(runtime_case["admission"]),
                    "candidate_counts_agree": dict(runtime_counts) == sidecar_counts == b_counts,
                    "sidecar_has_no_semantic_or_review_authority_keys": not bool(
                        _walk_keys(loaded_sidecar).intersection(
                            PROHIBITED_SEMANTIC_KEYS | PROHIBITED_REVIEW_KEYS
                        )
                    ),
                    "runtime_candidate_count": len(runtime_candidates),
                    "contract_b_history_count": len(b_history_prop),
                    "envelope_sha256": _sha256((package_dir / ENVELOPE_NAME).read_bytes()),
                    "sidecar_sha256": _sha256((package_dir / SIDECAR_NAME).read_bytes()),
                    "contract_b_binding": _bundle_binding(package_dir / "contract_b"),
                }
            )

        mutations = run_mutations(package_dirs)

    criteria = {
        "canonical_contract_b_validation": all(row["canonical_contract_b_valid"] for row in cases),
        "contract_b_bytes_unchanged": all(row["contract_b_bytes_unchanged"] for row in cases),
        "package_binding_verification": all(row["package_verification_pass"] for row in cases),
        "pre_retention_candidate_identity": all(
            row["pre_retention_candidate_identity_recoverable"] for row in cases
        ),
        "candidate_passage_content": all(row["candidate_passage_content_recoverable"] for row in cases),
        "selection_trace_consistency": all(
            row["sidecar_retention_matches_runtime"] and row["contract_b_retained_matches_sidecar"]
            for row in cases
        ),
        "contract_b_review_state_unchanged": all(
            row["contract_b_review_state_unchanged"] for row in cases
        ),
        "candidate_counts_agree": all(row["candidate_counts_agree"] for row in cases),
        "sidecar_authority_boundary": all(
            row["sidecar_has_no_semantic_or_review_authority_keys"] for row in cases
        ),
        "mutation_checks": all(row["passed"] for row in mutations.values()),
    }

    if not criteria["canonical_contract_b_validation"] or not criteria["mutation_checks"]:
        disposition = "INVALID_APPARATUS"
    elif all(criteria.values()):
        disposition = "SUPPORTED_WITHIN_TESTED_APERTURE"
    else:
        disposition = "FALSIFIED_WITHIN_TESTED_APERTURE"

    result = {
        "schema": SCHEMA,
        "frozen_base_sha": BASE_SHA,
        "contract_b_authority_sha": CONTRACT_B_AUTHORITY,
        "case_count": len(cases),
        "disposition": disposition,
        "criteria": criteria,
        "mutation_checks": mutations,
        "cases": cases,
        "interpretation_boundary": {
            "contract_b_schema_changed": False,
            "contract_b_bytes_changed_by_packaging": not criteria["contract_b_bytes_unchanged"],
            "retrieval_quality_claimed": False,
            "corpus_completeness_claimed": False,
            "semantic_authority_claimed": False,
            "authentication_claimed": False,
            "integrity_binding_only": True,
            "cal_called": False,
            "production_promotion_authorized": False,
        },
    }
    (artifact_root / "RESULT.json").write_bytes(canonical_bytes(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--research-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.research_root, args.artifact_root)
    print(
        json.dumps(
            {
                "disposition": result["disposition"],
                "criteria": result["criteria"],
                "case_count": result["case_count"],
            },
            sort_keys=True,
        )
    )
    return 2 if result["disposition"] == "INVALID_APPARATUS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
