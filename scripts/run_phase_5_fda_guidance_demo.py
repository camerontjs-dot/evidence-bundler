"""Run the Phase 5 FDA guidance real-corpus demo through installed CLIs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pdfminer.high_level import extract_text

from evidence_bundler.contracts.hashing import (
    compute_bundle_tree_hash,
    compute_corpus_hash,
    hash_file,
    hash_text,
    write_sha256sums,
)
from evidence_bundler.models.common import CONTRACT_VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]
MAINFRAME_PROJECTS_ROOT = REPO_ROOT.parents[1]


PHASE5_ROOT = REPO_ROOT / "examples" / "phase-5-draft"
SOURCE_MANIFEST_PATH = PHASE5_ROOT / "source-manifest.yaml"
CLAIMS_PATH = PHASE5_ROOT / "claims.yaml"
DRAFT_NOTE_PATH = PHASE5_ROOT / "fictional-compliance-review-note.md"
OUTPUT_DIR = REPO_ROOT / "build" / "phase-5-fda-guidance-demo"

EVIDENCE_BUNDLER_CLI = REPO_ROOT / ".venv" / "bin" / "evidence-bundler"

SUPPORTED_CLAIMS = {
    "clm-qms-coverage",
    "clm-capa-risk",
    "clm-supplier-qualification",
}
CONTRADICTED_CLAIMS = {
    "clm-validation-exemption",
    "clm-stability-extension",
}
CONDITIONAL_CLAIMS = {"clm-apr-scope"}
NEEDS_REVIEW_CLAIMS = {"clm-equipment-requalification"}
INSUFFICIENT_CLAIMS = {"clm-clinical-endpoint"}
EXPECTED_COUNTER_CLAIMS = CONTRADICTED_CLAIMS | CONDITIONAL_CLAIMS
EXPECTED_NO_CANDIDATE_CLAIMS = INSUFFICIENT_CLAIMS

PHARMA_PREFIXES = [
    "evidence against",
    "limitations of",
    "contradicts the claim that",
    "does not support",
    "fails to demonstrate",
    "contraindicated in",
    "failed primary endpoint for",
    "off-label use of",
    "adverse events from",
]

PASSAGE_TARGETS = {
    "pass-qms-framework": {
        "section": "Quality Systems Model",
        "needle": "Implementation of a comprehensive quality systems model",
    },
    "pass-process-validation": {
        "section": "Process Validation",
        "needle": "process validation is not a one-time event",
    },
    "pass-annual-review": {
        "section": "Evaluation Activities",
        "needle": "Annual Review",
    },
    "pass-capa-system": {
        "section": "CAPA",
        "needle": "CAPA is a well-known CGMP regulatory concept",
    },
    "pass-equipment-qualification": {
        "section": "Facilities and Equipment",
        "needle": "The CGMP regulations place as much emphasis on process equipment",
    },
    "pass-supplier-controls": {
        "section": "Control Outsourced Operations",
        "needle": "periodic auditing of suppliers based on risk assessment",
    },
    "pass-stability-requirements": {
        "section": "Manufacturing",
        "needle": "additional stability studies",
    },
}


@dataclass(frozen=True)
class DemoPaths:
    """Runtime paths for the Phase 5 demo."""

    root: Path
    downloads: Path
    scaffold: Path
    draft: Path
    retrieval_config: Path
    retrieval_report: Path
    review_annotations: Path
    excerpt_refinement: Path
    final: Path
    finalize_provenance: Path
    coverage_md: Path
    coverage_json: Path
    run_metadata: Path
    summary_md: Path
    summary_json: Path
    adr010_dir: Path
    adr010_json: Path
    adr010_md: Path
    adr011_json: Path
    adr011_md: Path
    resolved_source_manifest: Path

    @classmethod
    def from_output_dir(cls, root: Path) -> DemoPaths:
        return cls(
            root=root,
            downloads=root / "downloads",
            scaffold=root / "scaffold-run-fda-guidance",
            draft=root / "draft-bundle",
            retrieval_config=root / "retrieval-config.yaml",
            retrieval_report=root / "retrieval-report.md",
            review_annotations=root / "review_annotations.yaml",
            excerpt_refinement=root / "excerpt_refinement.yaml",
            final=root / "final-bundle",
            finalize_provenance=root / "final-bundle_finalize_provenance.yaml",
            coverage_md=root / "coverage-report.md",
            coverage_json=root / "coverage-report.json",
            run_metadata=root / "run-metadata.json",
            summary_md=root / "phase5_summary.md",
            summary_json=root / "phase5_summary.json",
            adr010_dir=root / "adr010-measurements",
            adr010_json=root / "adr010_measurements.json",
            adr010_md=root / "adr010_measurements.md",
            adr011_json=root / "adr011_review_measurements.json",
            adr011_md=root / "adr011_review_measurements.md",
            resolved_source_manifest=root / "resolved-source-manifest.yaml",
        )


@dataclass(frozen=True)
class DownloadedSource:
    """One pinned source downloaded for the real-corpus demo."""

    source_id: str
    path: Path
    sha256: str
    source_manifest: dict[str, Any]


def main() -> None:
    args = _parse_args()
    _prepare_output_dir(OUTPUT_DIR, force=args.force)
    _assert_cli(EVIDENCE_BUNDLER_CLI)

    paths = DemoPaths.from_output_dir(OUTPUT_DIR)
    run_started = _utc_now()
    timings: dict[str, float] = {}

    manifest = _load_yaml(SOURCE_MANIFEST_PATH)
    started = time.monotonic()
    sources = _download_sources(manifest, paths.downloads)
    timings["download_sources_seconds"] = _elapsed(started)
    _write_yaml(manifest, paths.resolved_source_manifest)

    started = time.monotonic()
    _build_scaffold(paths.scaffold, sources, manifest)
    timings["build_scaffold_seconds"] = _elapsed(started)

    started = time.monotonic()
    _run_pipeline(paths)
    timings["pipeline_seconds"] = _elapsed(started)

    started = time.monotonic()
    adr010 = _run_adr010_measurements(paths)
    timings["adr010_seconds"] = _elapsed(started)
    _write_adr010_measurements(adr010, paths)

    adr011 = _build_adr011_measurements(paths)
    _write_adr011_measurements(adr011, paths)

    summary = _build_summary(paths, adr010, adr011)
    _assert_summary(summary)
    _write_summary(summary, paths)
    _write_run_metadata(
        paths,
        {
            "schema_version": "phase-5-run-metadata-v1",
            "run_started_at_utc": run_started,
            "run_completed_at_utc": _utc_now(),
            "timings": timings,
            "source_count": len(sources),
            "output_dir": _rel(paths.root),
        },
    )
    print(f"Phase 5 summary written: {paths.summary_md}")
    print(f"Phase 5 summary JSON written: {paths.summary_json}")
    print(f"ADR-010 measurements written: {paths.adr010_md}")
    print(f"ADR-011 measurements written: {paths.adr011_md}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and recreate build/phase-5-fda-guidance-demo.",
    )
    return parser.parse_args()


def _prepare_output_dir(path: Path, *, force: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not force:
            raise SystemExit(
                f"Output directory is not empty: {path}. Re-run with --force to replace it."
            )
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _assert_cli(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Required CLI not found: {path}")


def _download_sources(manifest: dict[str, Any], download_dir: Path) -> list[DownloadedSource]:
    download_dir.mkdir(parents=True, exist_ok=True)
    sources: list[DownloadedSource] = []
    for source in manifest.get("sources", []):
        source_id = str(source["source_id"])
        expected_sha256 = source.get("expected_sha256")
        if not expected_sha256:
            raise SystemExit(
                f"{SOURCE_MANIFEST_PATH} is not pinned for {source_id}: expected_sha256 missing"
            )
        url = str(source["bibliographic"]["url"])
        destination = download_dir / f"{source_id}.pdf"
        _download_file(url, destination)
        actual_sha256 = _sha256_file(destination)
        if actual_sha256 != expected_sha256:
            raise SystemExit(
                f"sha256 mismatch for {source_id}: {actual_sha256} != {expected_sha256}"
            )
        sources.append(
            DownloadedSource(
                source_id=source_id,
                path=destination,
                sha256=actual_sha256,
                source_manifest=source,
            )
        )
    return sources


def _download_file(url: str, destination: Path) -> None:
    print(f"Downloading {url}")
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            destination.write_bytes(response.read())
    except urllib.error.URLError as exc:
        raise SystemExit(f"Download failed for {url}: {exc}") from exc


def _build_scaffold(
    scaffold_dir: Path,
    sources: list[DownloadedSource],
    manifest: dict[str, Any],
) -> None:
    if scaffold_dir.exists():
        shutil.rmtree(scaffold_dir)
    corpus_dir = scaffold_dir / "corpus"
    corpus_dir.mkdir(parents=True)

    claims = _load_yaml(CLAIMS_PATH)
    shutil.copy2(CLAIMS_PATH, scaffold_dir / "claims.yaml")
    (scaffold_dir / "CONTRACT_VERSION").write_text(f"{CONTRACT_VERSION}\n", encoding="utf-8")

    for rank, source in enumerate(sources, start=1):
        source_dir = corpus_dir / source.source_id
        source_dir.mkdir(parents=True)
        content_path = source_dir / "content.pdf"
        shutil.copy2(source.path, content_path)

        source_text = extract_text(content_path)
        used_claims = _claims_retrieved_for_source(claims, source.source_id)
        metadata = _source_metadata(source, content_path, used_claims, rank)
        _write_yaml(metadata, source_dir / "metadata.yaml")
        _write_yaml(
            _source_passages(source.source_id, source_text, claims),
            source_dir / "passages.yaml",
        )

    scaffold_run = _scaffold_run_manifest(scaffold_dir, claims, manifest)
    _write_yaml(scaffold_run, scaffold_dir / "scaffold_run.yaml")
    write_sha256sums(scaffold_dir)


def _source_metadata(
    source: DownloadedSource,
    content_path: Path,
    used_claims: list[str],
    rank: int,
) -> dict[str, Any]:
    manifest = source.source_manifest
    bibliographic = dict(manifest["bibliographic"])
    retrieval_date = str(manifest["retrieval_date"])
    access_date = retrieval_date if "T" in retrieval_date else f"{retrieval_date}T00:00:00Z"
    bibliographic["access_date_utc"] = access_date
    return {
        "source_id": source.source_id,
        "schema_version": CONTRACT_VERSION,
        "bibliographic": bibliographic,
        "trust_level": manifest["trust_level"],
        "content_hash": hash_file(content_path),
        "retrieval": {
            "retrieved_for": used_claims,
            "retrieval_query": "FDA CGMP quality systems guidance for Phase 5 demo claims",
            "retrieval_rank": rank,
        },
        "notes": manifest.get("notes", ""),
    }


def _source_passages(source_id: str, source_text: str, claims: dict[str, Any]) -> dict[str, Any]:
    cited_passage_ids = {
        ref["passage_id"]
        for claim in claims.get("claims", [])
        for ref in claim.get("source_refs", [])
        if ref["source_id"] == source_id
    }
    passages: list[dict[str, Any]] = []
    for index, passage_id in enumerate(sorted(cited_passage_ids), start=1):
        target = PASSAGE_TARGETS.get(passage_id, {})
        excerpt = _find_excerpt(source_text, str(target.get("needle", "")))
        used_for_claims = [
            claim["claim_id"]
            for claim in claims.get("claims", [])
            if any(
                ref["source_id"] == source_id and ref["passage_id"] == passage_id
                for ref in claim.get("source_refs", [])
            )
        ]
        passages.append(
            {
                "passage_id": passage_id,
                "section": target.get("section"),
                "paragraph_index": index,
                "char_start": excerpt["char_start"],
                "char_end": excerpt["char_end"],
                "text_preview": excerpt["text_preview"],
                "used_for_claims": used_for_claims,
                "extraction_method": "scaffold_cited",
            }
        )
    return {
        "source_id": source_id,
        "schema_version": CONTRACT_VERSION,
        "passages": passages,
    }


def _find_excerpt(source_text: str, needle: str) -> dict[str, Any]:
    normalized = " ".join(source_text.split())
    lowered = normalized.lower()
    needle_lower = needle.lower()
    index = lowered.find(needle_lower) if needle else -1
    if index < 0:
        index = 0
    start = max(0, index - 180)
    end = min(len(normalized), index + 620)
    while start > 0 and normalized[start] not in ".;:":
        start -= 1
    if start > 0:
        start += 1
    while end < len(normalized) and normalized[end - 1] not in ".;:":
        end += 1
    excerpt = normalized[start:end].strip()
    if len(excerpt) > 900:
        excerpt = excerpt[:897].rstrip() + "..."
        end = start + len(excerpt)
    if not excerpt:
        excerpt = normalized[:300].strip() or "No extractable text found in PDF."
        start = 0
        end = len(excerpt)
    return {
        "char_start": start,
        "char_end": max(end, start + 1),
        "text_preview": excerpt,
    }


def _scaffold_run_manifest(
    scaffold_dir: Path,
    claims: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    retrieval_dates = [
        str(source["retrieval_date"])
        for source in manifest.get("sources", [])
        if source.get("retrieval_date")
    ]
    retrieval_timestamp = (
        f"{max(retrieval_dates)}T00:00:00Z" if retrieval_dates else _utc_now()
    )
    return {
        "run_id": claims["run_id"],
        "task_id": "phase-5-fda-guidance-demo",
        "workflow_condition": "full_scaffold",
        "timestamp_utc": claims["generated_at_utc"],
        "scaffold": {
            "version": "phase-5-manual-draft-v1",
            "prompt_template_id": "manual-fictional-compliance-review-note",
            "prompt_template_hash": hash_text(DRAFT_NOTE_PATH.read_text(encoding="utf-8")),
            "config_hash": hash_text(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")),
        },
        "model": {
            "model_id": "manual-authoring",
            "model_version": "phase-5",
            "api_endpoint": "local-manual-draft",
            "temperature": 0.0,
            "max_tokens": 1,
        },
        "task": {
            "research_question": (
                "Can Evidence Bundler nominate candidate passages from pinned FDA CGMP "
                "guidance for a fictional compliance review memo?"
            ),
            "domain": "pharma_regulatory",
            "expert_checkable": True,
            "ground_truth_ref": "examples/phase-5-draft/README.md",
        },
        "corpus": {
            "total_sources": len(manifest.get("sources", [])),
            "corpus_hash": compute_corpus_hash(scaffold_dir / "corpus"),
            "retrieval_strategy": "pinned_fda_guidance_manifest",
            "retrieval_timestamp_utc": retrieval_timestamp,
        },
        "intermediates_present": False,
        "run_metadata": {
            "operator": "cameron",
            "environment": "local-dev",
            "notes": (
                "Phase 5 manually authored fictional draft; Research Scaffold Harness "
                "not ready. Generated from committed Phase 5 draft artifacts."
            ),
        },
    }


def _claims_retrieved_for_source(claims: dict[str, Any], source_id: str) -> list[str]:
    return [
        claim["claim_id"]
        for claim in claims.get("claims", [])
        if any(ref["source_id"] == source_id for ref in claim.get("source_refs", []))
    ]


def _run_pipeline(paths: DemoPaths) -> None:
    config = _main_retrieval_config(paths, paths.root / "semantic-index")
    _write_yaml(config, paths.retrieval_config)
    _run([EVIDENCE_BUNDLER_CLI, "verify-intake", paths.scaffold], cwd=REPO_ROOT)
    _run_build_bundle(
        paths.scaffold,
        paths.draft,
        paths.retrieval_config,
        paths.retrieval_report,
    )
    _run(
        [
            EVIDENCE_BUNDLER_CLI,
            "review",
            "init",
            paths.draft,
            "--output",
            paths.review_annotations,
            "--reviewer",
            "phase-5-fda-guidance-deterministic-reviewer",
        ],
        cwd=REPO_ROOT,
    )
    _apply_review_sequence(paths)
    _run(
        [
            EVIDENCE_BUNDLER_CLI,
            "refine-excerpts",
            paths.draft,
            "--annotations",
            paths.review_annotations,
            "--output",
            paths.excerpt_refinement,
        ],
        cwd=REPO_ROOT,
    )
    _run(
        [
            EVIDENCE_BUNDLER_CLI,
            "finalize-bundle",
            paths.draft,
            "--annotations",
            paths.review_annotations,
            "--refinement",
            paths.excerpt_refinement,
            "--output",
            paths.final,
            "--provenance-output",
            paths.finalize_provenance,
        ],
        cwd=REPO_ROOT,
    )
    _run(
        [
            EVIDENCE_BUNDLER_CLI,
            "coverage-report",
            paths.draft,
            "--annotations",
            paths.review_annotations,
            "--refinement",
            paths.excerpt_refinement,
            "--final-bundle",
            paths.final,
            "--provenance",
            paths.finalize_provenance,
            "--markdown-out",
            paths.coverage_md,
            "--json-out",
            paths.coverage_json,
        ],
        cwd=REPO_ROOT,
    )


def _apply_review_sequence(paths: DemoPaths) -> None:
    _review_batch(paths, "rejected", notes="Phase 5 conservative default before claim-role passes.")
    for claim_id in sorted(SUPPORTED_CLAIMS):
        _review_batch(
            paths,
            "accepted",
            claim_id=claim_id,
            role="supporting",
            notes="Phase 5 deterministic review: supporting nomination accepted for demo.",
        )
    for claim_id in sorted(CONTRADICTED_CLAIMS):
        _review_batch(
            paths,
            "accepted",
            claim_id=claim_id,
            role="contradicting",
            notes="Phase 5 deterministic review: counter-candidate accepted for demo.",
        )
    for claim_id in sorted(CONDITIONAL_CLAIMS):
        _review_batch(
            paths,
            "accepted",
            claim_id=claim_id,
            role="conditional",
            notes="Phase 5 deterministic review: conditional counter-candidate accepted for demo.",
        )
    for claim_id in sorted(NEEDS_REVIEW_CLAIMS):
        _review_batch(
            paths,
            "needs-review",
            claim_id=claim_id,
            notes="Phase 5 deterministic review: ambiguous equipment interval claim.",
        )
    for claim_id in sorted(INSUFFICIENT_CLAIMS):
        _review_batch(
            paths,
            "insufficient-excerpt",
            claim_id=claim_id,
            notes="Phase 5 deterministic review: outside CGMP source scope.",
        )


def _review_batch(
    paths: DemoPaths,
    decision: str,
    *,
    claim_id: str | None = None,
    role: str | None = None,
    notes: str | None = None,
) -> None:
    command: list[object] = [
        EVIDENCE_BUNDLER_CLI,
        "review",
        "batch",
        paths.draft,
        "--annotations",
        paths.review_annotations,
        "--decision",
        decision,
    ]
    if claim_id is not None:
        command.extend(["--claim-id", claim_id])
    if role is not None:
        command.extend(["--role", role])
    if notes is not None:
        command.extend(["--notes", notes])
    _run(command, cwd=REPO_ROOT)


def _run_adr010_measurements(paths: DemoPaths) -> dict[str, Any]:
    paths.adr010_dir.mkdir(parents=True, exist_ok=True)
    run_specs = {
        "matrix_rerank_off_contradiction_rerank_off": _main_retrieval_config(
            paths,
            paths.root / "semantic-index",
            rerank_enabled=False,
            contradiction_rerank_enabled=False,
        ),
        "matrix_rerank_on_contradiction_rerank_off": _main_retrieval_config(
            paths,
            paths.root / "semantic-index",
            rerank_enabled=True,
            contradiction_rerank_enabled=False,
        ),
        "matrix_rerank_off_contradiction_rerank_on": _main_retrieval_config(
            paths,
            paths.root / "semantic-index",
            rerank_enabled=False,
            contradiction_rerank_enabled=True,
        ),
        "matrix_rerank_on_contradiction_rerank_on": _main_retrieval_config(
            paths,
            paths.root / "semantic-index",
            rerank_enabled=True,
            contradiction_rerank_enabled=True,
        ),
        "prefix_default": _main_retrieval_config(
            paths,
            paths.root / "semantic-index",
            rerank_enabled=True,
            contradiction_rerank_enabled=False,
        ),
        "prefix_default_plus_pharma": _main_retrieval_config(
            paths,
            paths.root / "semantic-index",
            rerank_enabled=True,
            contradiction_rerank_enabled=False,
            contradiction_query_prefixes=PHARMA_PREFIXES,
        ),
        "text_gate_on": _main_retrieval_config(
            paths,
            paths.root / "semantic-index",
            rerank_enabled=True,
            contradiction_text_gate_enabled=True,
        ),
        "text_gate_off": _main_retrieval_config(
            paths,
            paths.root / "semantic-index",
            rerank_enabled=True,
            contradiction_text_gate_enabled=False,
        ),
    }
    runs: dict[str, Any] = {}
    for run_name, config in run_specs.items():
        run_dir = paths.adr010_dir / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        config_path = run_dir / "retrieval-config.yaml"
        report_path = run_dir / "retrieval-report.md"
        bundle_dir = run_dir / "draft-bundle"
        _write_yaml(config, config_path)
        result = _run_build_bundle(
            paths.scaffold,
            bundle_dir,
            config_path,
            report_path,
            allow_failure=True,
        )
        runs[run_name] = _score_adr010_run(
            run_name=run_name,
            bundle_dir=bundle_dir,
            config=config,
            status="completed" if result == 0 else "failed",
            returncode=result,
        )

    return {
        "schema_version": "phase-5-adr010-measurements-v1",
        "generated_at_utc": _utc_now(),
        "scope": "FDA guidance real-corpus demo; candidate nominations only.",
        "expected_counter_claim_ids": sorted(EXPECTED_COUNTER_CLAIMS),
        "expected_no_candidate_claim_ids": sorted(EXPECTED_NO_CANDIDATE_CLAIMS),
        "runs": runs,
        "decisions": _adr010_decisions(runs),
    }


def _score_adr010_run(
    *,
    run_name: str,
    bundle_dir: Path,
    config: dict[str, Any],
    status: str,
    returncode: int,
) -> dict[str, Any]:
    if status != "completed":
        return {
            "status": "not_runnable_config_dependency"
            if run_name == "matrix_rerank_off_contradiction_rerank_on"
            else "failed",
            "returncode": returncode,
            "config": config,
            "metrics": None,
            "claim_results": {},
        }

    claim_units = _load_claims(bundle_dir)
    claim_results: dict[str, Any] = {}
    expected_counter_found = 0
    false_positive_counter = 0
    no_candidate_matches = 0
    for claim_id, claim in sorted(claim_units.items()):
        evidence = claim.get("evidence_passages", [])
        counterevidence = claim.get("counterevidence_passages", [])
        has_counter = bool(counterevidence)
        if claim_id in EXPECTED_COUNTER_CLAIMS and has_counter:
            expected_counter_found += 1
        if claim_id not in EXPECTED_COUNTER_CLAIMS:
            false_positive_counter += len(counterevidence)
        if claim_id in EXPECTED_NO_CANDIDATE_CLAIMS and not evidence and not counterevidence:
            no_candidate_matches += 1
        claim_results[claim_id] = {
            "evidence_passage_count": len(evidence),
            "counterevidence_passage_count": len(counterevidence),
            "counterevidence_excerpt_needles": _counter_excerpt_needles(counterevidence),
        }

    expected_counter_total = len(EXPECTED_COUNTER_CLAIMS)
    return {
        "status": status,
        "returncode": returncode,
        "config": config,
        "metrics": {
            "counterevidence_claim_recall": (
                f"{expected_counter_found}/{expected_counter_total}"
            ),
            "false_positive_counter_candidate_count": false_positive_counter,
            "no_candidate_expected_matches": (
                f"{no_candidate_matches}/{len(EXPECTED_NO_CANDIDATE_CLAIMS)}"
            ),
        },
        "claim_results": claim_results,
    }


def _counter_excerpt_needles(counterevidence: list[dict[str, Any]]) -> list[str]:
    needles = []
    for passage in counterevidence:
        text = str(passage.get("passage_text", "")).lower()
        matched = [
            needle
            for needle in (
                "not",
                "not required",
                "no effect",
                "only",
                "subject to",
                "additional stability",
                "validation is not a one-time event",
            )
            if needle in text
        ]
        needles.append(", ".join(matched) if matched else "none")
    return needles


def _adr010_decisions(runs: dict[str, Any]) -> dict[str, Any]:
    completed = [name for name, run in runs.items() if run["status"] == "completed"]
    failed = [name for name, run in runs.items() if run["status"] != "completed"]
    return {
        "completed_runs": completed,
        "non_completed_runs": failed,
        "amendment_required": False,
        "decision": (
            "No default or pattern amendment is promoted automatically by this runner. "
            "Review the real-corpus measurements before changing ADR-010 defaults."
        ),
    }


def _build_adr011_measurements(paths: DemoPaths) -> dict[str, Any]:
    annotations = _load_yaml(paths.review_annotations).get("annotations", [])
    total = len(annotations)
    role_disagreement_rows = []
    batch_accept_count = 0
    accepted_count = 0
    for annotation in annotations:
        decision = annotation.get("decision")
        claim_id = str(annotation.get("claim_id"))
        role = str(annotation.get("evidence_role"))
        notes = str(annotation.get("reviewer_notes") or "")
        if decision == "accepted":
            accepted_count += 1
            if "deterministic review" in notes:
                batch_accept_count += 1
        expected_roles = _expected_roles_for_claim(claim_id)
        if (
            expected_roles
            and role not in expected_roles
            and decision in {"rejected", "needs-review"}
        ):
            role_disagreement_rows.append(
                {
                    "claim_id": claim_id,
                    "source_id": annotation.get("source_id"),
                    "passage_id": annotation.get("passage_id"),
                    "retriever_role": role,
                    "expected_roles": sorted(expected_roles),
                    "decision": decision,
                    "notes": notes,
                }
            )
    disagreement_count = len(role_disagreement_rows)
    return {
        "schema_version": "phase-5-adr011-measurements-v1",
        "generated_at_utc": _utc_now(),
        "scope": "Deterministic Phase 5 review sequence over FDA guidance nominations.",
        "total_annotations": total,
        "role_disagreement_count": disagreement_count,
        "role_disagreement_fraction": _ratio(disagreement_count, total),
        "role_disagreement_rows": role_disagreement_rows,
        "accepted_count": accepted_count,
        "batch_accept_count": batch_accept_count,
        "batch_accept_fraction_of_accepted": _ratio(batch_accept_count, accepted_count),
        "amendment_required": False,
        "decision": (
            "No ADR-011 amendment is promoted automatically by this runner. The measurement "
            "records whether reviewer-vs-retriever role disagreement or batch acceptance is "
            "large enough to justify a follow-up decision."
        ),
    }


def _expected_roles_for_claim(claim_id: str) -> set[str]:
    if claim_id in SUPPORTED_CLAIMS:
        return {"supporting"}
    if claim_id in CONTRADICTED_CLAIMS:
        return {"contradicting"}
    if claim_id in CONDITIONAL_CLAIMS:
        return {"conditional", "contradicting"}
    if claim_id in NEEDS_REVIEW_CLAIMS:
        return {"supporting", "conditional", "contradicting"}
    if claim_id in INSUFFICIENT_CLAIMS:
        return set()
    return set()


def _main_retrieval_config(
    paths: DemoPaths,
    semantic_index_path: Path,
    *,
    rerank_enabled: bool = True,
    contradiction_rerank_enabled: bool = False,
    contradiction_text_gate_enabled: bool = True,
    contradiction_query_prefixes: list[str] | None = None,
) -> dict[str, Any]:
    config: dict[str, Any] = {
        "retrieval_method": "hybrid",
        "top_k": 5,
        "child_top_k": 30,
        "semantic_child_top_k": 30,
        "rrf_candidate_pool": 30,
        "semantic_index_path": str(semantic_index_path),
        "embedding_model": "BAAI/bge-small-en-v1.5",
        "rerank_enabled": rerank_enabled,
        "rerank_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "rerank_top_n": 10,
        "contradiction_enabled": True,
        "contradiction_top_k": 5,
        "contradiction_rerank_enabled": contradiction_rerank_enabled,
        "contradiction_text_gate_enabled": contradiction_text_gate_enabled,
    }
    if contradiction_query_prefixes is not None:
        config["contradiction_query_prefixes"] = contradiction_query_prefixes
    return config


def _run_build_bundle(
    scaffold_dir: Path,
    output_dir: Path,
    config_path: Path,
    report_out: Path,
    *,
    allow_failure: bool = False,
) -> int:
    command = [
        EVIDENCE_BUNDLER_CLI,
        "build-bundle",
        scaffold_dir,
        "--output",
        output_dir,
        "--config",
        config_path,
        "--report-out",
        report_out,
    ]
    return _run(command, cwd=REPO_ROOT, allow_failure=allow_failure)


def _run(command: list[object], *, cwd: Path, allow_failure: bool = False) -> int:
    printable = " ".join(str(part) for part in command)
    print(f"$ {printable}")
    result = subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.returncode != 0 and not allow_failure:
        raise SystemExit(result.returncode)
    return result.returncode


def _build_summary(
    paths: DemoPaths,
    adr010: dict[str, Any],
    adr011: dict[str, Any],
) -> dict[str, Any]:
    final_manifest = _load_yaml(paths.final / "bundle_manifest.yaml")
    coverage = _load_json(paths.coverage_json)
    draft_claims = _load_claims(paths.draft)
    final_claims = _load_claims(paths.final)
    return {
        "schema_version": "phase-5-fda-guidance-summary-v1",
        "report_generated_at_utc": _utc_now(),
        "paths": {
            "phase5_draft": _rel(DRAFT_NOTE_PATH),
            "source_manifest": _rel(SOURCE_MANIFEST_PATH),
            "scaffold_run_dir": _rel(paths.scaffold),
            "draft_bundle": _rel(paths.draft),
            "final_bundle": _rel(paths.final),
            "coverage_markdown": _rel(paths.coverage_md),
            "coverage_json": _rel(paths.coverage_json),
            "adr010_measurements": _rel(paths.adr010_json),
            "adr011_measurements": _rel(paths.adr011_json),
        },
        "final_bundle": {
            "bundle_id": final_manifest["bundle_id"],
            "bundle_hash": final_manifest["bundle"]["bundle_hash"],
            "reviewer_sign_off_required": final_manifest["reviewer_sign_off"]["required"],
            "claims_included": final_manifest["bundle"]["claims_included"],
            "claims_excluded": final_manifest["bundle"]["claims_excluded"],
            "total_evidence_passages": final_manifest["bundle"]["total_evidence_passages"],
        },
        "coverage": {
            "inconsistency_count": len(coverage.get("inconsistencies", [])),
            "decision_coverage": coverage.get("decision_coverage", []),
            "nomination_gaps": coverage.get("nomination_gaps", {}),
        },
        "claim_observations": _claim_observations(draft_claims, final_claims),
        "adr010": {
            "completed_runs": adr010["decisions"]["completed_runs"],
            "non_completed_runs": adr010["decisions"]["non_completed_runs"],
            "amendment_required": adr010["decisions"]["amendment_required"],
        },
        "adr011": {
            "role_disagreement_count": adr011["role_disagreement_count"],
            "role_disagreement_fraction": adr011["role_disagreement_fraction"],
            "batch_accept_fraction_of_accepted": adr011["batch_accept_fraction_of_accepted"],
            "amendment_required": adr011["amendment_required"],
        },
        "anchor_hash_chain": {
            "draft_bundle_hash": compute_bundle_tree_hash(paths.draft),
            "review_annotations_hash": _sha256_file(paths.review_annotations),
            "excerpt_refinement_hash": _sha256_file(paths.excerpt_refinement),
            "final_bundle_hash": final_manifest["bundle"]["bundle_hash"],
        },
    }


def _claim_observations(
    draft_claims: dict[str, dict[str, Any]],
    final_claims: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    observations = {}
    for claim_id, claim in sorted(draft_claims.items()):
        final_claim = final_claims.get(claim_id)
        observations[claim_id] = {
            "draft_evidence_passages": len(claim.get("evidence_passages", [])),
            "draft_counterevidence_passages": len(claim.get("counterevidence_passages", [])),
            "final_included": final_claim is not None,
            "final_evidence_passages": len(final_claim.get("evidence_passages", []))
            if final_claim
            else 0,
            "final_counterevidence_passages": len(final_claim.get("counterevidence_passages", []))
            if final_claim
            else 0,
        }
    return observations


def _assert_summary(summary: dict[str, Any]) -> None:
    errors = []
    if summary["coverage"]["inconsistency_count"] != 0:
        errors.append("coverage inconsistencies must be zero")
    expected_claim_ids = (
        SUPPORTED_CLAIMS
        | CONTRADICTED_CLAIMS
        | CONDITIONAL_CLAIMS
        | NEEDS_REVIEW_CLAIMS
        | INSUFFICIENT_CLAIMS
    )
    if set(summary["claim_observations"]) != expected_claim_ids:
        errors.append("claim observations must cover all Phase 5 claim IDs")
    if not summary["adr010"]["completed_runs"]:
        errors.append("at least one ADR-010 measurement run must complete")
    if summary["adr011"]["role_disagreement_fraction"] == "n/a":
        errors.append("ADR-011 role-disagreement fraction must be computable")
    if errors:
        raise SystemExit("Phase 5 demo assertions failed:\n- " + "\n- ".join(errors))


def _write_summary(summary: dict[str, Any], paths: DemoPaths) -> None:
    paths.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    paths.summary_md.write_text(_render_summary_markdown(summary), encoding="utf-8")


def _render_summary_markdown(summary: dict[str, Any]) -> str:
    claim_lines = []
    for claim_id, observation in summary["claim_observations"].items():
        claim_lines.append(
            f"| `{claim_id}` | {observation['draft_evidence_passages']} | "
            f"{observation['draft_counterevidence_passages']} | "
            f"{observation['final_included']} | {observation['final_evidence_passages']} | "
            f"{observation['final_counterevidence_passages']} |"
        )
    return "\n".join(
        [
            "# Phase 5 FDA Guidance Demo Summary",
            "",
            "This real-corpus demo records candidate nominations and review coverage. "
            "It does not verify regulatory claims or replace methodological validation.",
            "",
            "## Final Bundle",
            "",
            f"- Bundle id: `{summary['final_bundle']['bundle_id']}`",
            f"- Bundle hash: `{summary['final_bundle']['bundle_hash']}`",
            (
                "- Reviewer sign-off required: "
                f"`{summary['final_bundle']['reviewer_sign_off_required']}`"
            ),
            f"- Coverage inconsistency count: `{summary['coverage']['inconsistency_count']}`",
            "",
            "## Claim Observations",
            "",
            (
                "| Claim | Draft support | Draft counter | Final included | Final support | "
                "Final counter |"
            ),
            "| --- | ---: | ---: | --- | ---: | ---: |",
            *claim_lines,
            "",
            "## ADR Measurements",
            "",
            (
                "- ADR-010 completed runs: "
                f"`{', '.join(summary['adr010']['completed_runs'])}`"
            ),
            (
                "- ADR-010 non-completed runs: "
                f"`{', '.join(summary['adr010']['non_completed_runs']) or 'none'}`"
            ),
            (
                "- ADR-011 role disagreement: "
                f"`{summary['adr011']['role_disagreement_count']}` "
                f"({summary['adr011']['role_disagreement_fraction']})"
            ),
            (
                "- ADR-011 batch-accept fraction of accepted rows: "
                f"`{summary['adr011']['batch_accept_fraction_of_accepted']}`"
            ),
            "",
            "## Anchor Hash Chain",
            "",
            *[
                f"- `{key}`: `{value}`"
                for key, value in summary["anchor_hash_chain"].items()
            ],
            "",
        ]
    )


def _write_adr010_measurements(measurements: dict[str, Any], paths: DemoPaths) -> None:
    paths.adr010_json.write_text(json.dumps(measurements, indent=2, sort_keys=True) + "\n")
    lines = [
        "# ADR-010 Phase 5 Real-Corpus Measurements",
        "",
        "Candidate passages are retrieval nominations, not support determinations.",
        "",
        "## Run Summary",
        "",
        (
            "| Run | Status | Counter-candidate recall | False-positive counter candidates | "
            "No-candidate expected matches |"
        ),
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for run_name, run in sorted(measurements["runs"].items()):
        metrics = run.get("metrics") or {}
        lines.append(
            f"| `{run_name}` | `{run['status']}` | "
            f"{metrics.get('counterevidence_claim_recall', 'n/a')} | "
            f"{metrics.get('false_positive_counter_candidate_count', 'n/a')} | "
            f"{metrics.get('no_candidate_expected_matches', 'n/a')} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            measurements["decisions"]["decision"],
            "",
        ]
    )
    paths.adr010_md.write_text("\n".join(lines), encoding="utf-8")


def _write_adr011_measurements(measurements: dict[str, Any], paths: DemoPaths) -> None:
    paths.adr011_json.write_text(json.dumps(measurements, indent=2, sort_keys=True) + "\n")
    lines = [
        "# ADR-011 Phase 5 Review-State Measurements",
        "",
        "The deterministic review sequence records review-state behavior on real FDA text.",
        "",
        f"- Total annotation rows: `{measurements['total_annotations']}`",
        f"- Role disagreement count: `{measurements['role_disagreement_count']}`",
        f"- Role disagreement fraction: `{measurements['role_disagreement_fraction']}`",
        f"- Accepted rows: `{measurements['accepted_count']}`",
        f"- Batch-accepted rows: `{measurements['batch_accept_count']}`",
        (
            "- Batch-accept fraction of accepted rows: "
            f"`{measurements['batch_accept_fraction_of_accepted']}`"
        ),
        "",
        "## Decision",
        "",
        measurements["decision"],
        "",
    ]
    if measurements["role_disagreement_rows"]:
        lines.extend(["## Role Disagreement Rows", ""])
        for row in measurements["role_disagreement_rows"]:
            lines.append(
                f"- `{row['claim_id']}` / `{row['passage_id']}`: "
                f"{row['retriever_role']} vs {', '.join(row['expected_roles'])}"
            )
        lines.append("")
    paths.adr011_md.write_text("\n".join(lines), encoding="utf-8")


def _write_run_metadata(paths: DemoPaths, metadata: dict[str, Any]) -> None:
    paths.run_metadata.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")


def _load_claims(bundle_dir: Path) -> dict[str, dict[str, Any]]:
    claims: dict[str, dict[str, Any]] = {}
    claims_dir = bundle_dir / "claims"
    if not claims_dir.exists():
        return claims
    for path in sorted(claims_dir.glob("*.yaml")):
        data = _load_yaml(path)
        claims[str(data["claim_id"])] = data
    return claims


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON mapping: {path}")
    return data


def _write_yaml(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ratio(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator / denominator:.3f}"


def _elapsed(started: float) -> float:
    return round(time.monotonic() - started, 3)


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(MAINFRAME_PROJECTS_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())



def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
