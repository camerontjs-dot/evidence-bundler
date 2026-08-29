"""Fixture-only C-B evidence-bundle writer for Phase 0."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from evidence_bundler import __version__
from evidence_bundler.contracts.hashing import (
    compute_bundle_tree_hash,
    hash_audit_config_file,
    hash_text,
    verify_sha256sums,
    write_sha256sums,
)
from evidence_bundler.contracts.intake import (
    ScaffoldRunArtifact,
    SourceArtifact,
    verify_intake,
)
from evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml, yaml_to_string
from evidence_bundler.ingest.chunker import chunk_source_documents
from evidence_bundler.ingest.loader import load_source_documents
from evidence_bundler.models.ca import ScaffoldClaim, ScaffoldPassage
from evidence_bundler.models.cb import (
    AuditConfig,
    AuditConfigChange,
    AuditRulePolicies,
    AuditScoringConfig,
    BundleManifest,
    BundleStats,
    ClaimAuditUnit,
    ClaimEvidencePassage,
    EvidenceBuilderInfo,
    PassageProvenance,
    PassageRecord,
    QualityGates,
    ReviewerSignOff,
    SourceProfile,
    TransformationRecord,
    ValidationSetRef,
)
from evidence_bundler.models.common import CONTRACT_VERSION, PENDING_HASH
from evidence_bundler.models.document import ChunkSpec, DocumentChunk
from evidence_bundler.models.retrieval import (
    CandidateEvidence,
    RetrievalClaimSummary,
    RetrievalConfig,
    RetrievalRunReport,
)
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
from evidence_bundler.retrieval.contradiction import retrieve_contradicting
from evidence_bundler.retrieval.embedding_retriever import (
    SemanticIndex,
    SemanticIndexError,
    SemanticIndexManifestMismatch,
    SemanticSearchHit,
    compute_semantic_chunk_set_hash,
    load_embedding_model,
)
from evidence_bundler.retrieval.hits import ChunkSearchHit
from evidence_bundler.retrieval.hybrid import FusedChunkRank, reciprocal_rank_fusion
from evidence_bundler.retrieval.parent_aggregator import aggregate_parent_candidates
from evidence_bundler.retrieval.reranker import (
    ParentReranker,
    RerankerError,
    load_reranker_model,
)

AUDIT_CONFIG_VERSION = "cal-rules-v1.2.0"
VALIDATION_SET_VERSION = "valset-phase-0-fixture"
RETRIEVAL_VALIDATION_SET_VERSION = "valset-phase-2a-lexical"
SEMANTIC_VALIDATION_SET_VERSION = "valset-phase-2b-semantic"
HYBRID_VALIDATION_SET_VERSION = "valset-phase-2b-hybrid"


class BundleWriterError(Exception):
    """Raised when a fixture bundle cannot be built safely."""


@dataclass(frozen=True)
class BundleBuildResult:
    """Result returned after building a C-B fixture bundle."""

    bundle_dir: Path
    manifest: BundleManifest
    retrieval_report: RetrievalRunReport | None = None


def build_fixture_bundle(scaffold_run_dir: Path, output_dir: Path) -> BundleBuildResult:
    """Build a minimal C-B tree from a valid synthetic C-A fixture.

    This is a Phase 0 contract fixture writer. It copies scaffold-cited passages
    through to the C-B shape and does not perform retrieval or support auditing.
    """
    output_dir = output_dir.resolve()
    _prepare_output_dir(output_dir)

    intake = verify_intake(scaffold_run_dir)
    if not intake.valid or intake.artifact is None:
        raise BundleWriterError("; ".join(intake.errors))
    artifact = intake.artifact

    bundle_id = str(uuid5(NAMESPACE_URL, f"evidence-bundler:{artifact.manifest.run_id}"))
    generated_at = _utc_now()

    included_claims = [
        claim for claim in artifact.claims.claims if claim.claim_type == "extracted_claim"
    ]
    unique_passage_records = _collect_passage_records(
        artifact=artifact,
        claims=included_claims,
        bundle_id=bundle_id,
        bundle_created_at=generated_at,
    )

    _write_contract_version(output_dir)
    _write_validation_set_ref(output_dir, generated_at)

    audit_config = _make_audit_config(generated_at)
    audit_config_path = output_dir / "audit_config.yaml"
    write_model_yaml(audit_config, audit_config_path)
    audit_config = audit_config.model_copy(
        update={"config_hash": hash_audit_config_file(audit_config_path)}
    )
    write_model_yaml(audit_config, audit_config_path)

    _write_source_profiles(output_dir, artifact, unique_passage_records)
    _write_passage_records(output_dir, unique_passage_records)
    _write_claim_units(output_dir, artifact, included_claims, unique_passage_records, bundle_id)

    manifest = _make_manifest(
        artifact=artifact,
        bundle_id=bundle_id,
        generated_at=generated_at,
        audit_config_hash=audit_config.config_hash,
        total_claims_included=len(included_claims),
        total_evidence_passages=len(unique_passage_records),
    )
    manifest_path = output_dir / "bundle_manifest.yaml"
    write_model_yaml(manifest, manifest_path)
    manifest = manifest.model_copy(
        update={
            "bundle": manifest.bundle.model_copy(
                update={"bundle_hash": compute_bundle_tree_hash(output_dir)}
            )
        }
    )
    write_model_yaml(manifest, manifest_path)

    write_sha256sums(output_dir)
    errors = validate_bundle_tree(output_dir)
    if errors:
        raise BundleWriterError("; ".join(errors))

    return BundleBuildResult(bundle_dir=output_dir, manifest=manifest)


def build_retrieval_bundle(
    scaffold_run_dir: Path,
    output_dir: Path,
    *,
    config: RetrievalConfig | None = None,
    report_out: Path | None = None,
) -> BundleBuildResult:
    """Build a C-B bundle by nominating candidate passages with BM25 retrieval."""
    retrieval_config = config or RetrievalConfig()
    output_dir = output_dir.resolve()
    if report_out is not None and _is_relative_to(report_out.resolve(), output_dir):
        raise BundleWriterError(
            "Retrieval report must be written outside the sealed bundle directory"
        )
    if retrieval_config.semantic_index_path is not None and _is_relative_to(
        retrieval_config.semantic_index_path.resolve(),
        output_dir,
    ):
        raise BundleWriterError("Semantic index path must be outside the sealed bundle directory")
    _prepare_output_dir(output_dir)

    intake = verify_intake(scaffold_run_dir)
    if not intake.valid or intake.artifact is None:
        raise BundleWriterError("; ".join(intake.errors))
    artifact = intake.artifact
    config_hash = _retrieval_config_hash(retrieval_config)

    documents = load_source_documents(artifact)
    chunk_spec = ChunkSpec(
        max_chars=retrieval_config.chunk_max_chars,
        overlap_chars=retrieval_config.chunk_overlap_chars,
    )
    chunks = chunk_source_documents(documents, chunk_spec)
    retriever = BM25Retriever(chunks)
    semantic_index = _load_semantic_index_if_needed(retrieval_config, chunks, artifact)
    reranker = _load_reranker_if_needed(retrieval_config)
    included_claims = [
        claim for claim in artifact.claims.claims if claim.claim_type == "extracted_claim"
    ]

    candidates_by_claim: dict[str, list[CandidateEvidence]] = {}
    claim_summaries: list[RetrievalClaimSummary] = []
    no_candidate_claim_ids: list[str] = []
    no_countercandidate_claim_ids: list[str] = []
    for claim in included_claims:
        supporting_candidates, summary = _retrieve_claim_candidates(
            claim=claim,
            retriever=retriever,
            semantic_index=semantic_index,
            reranker=reranker,
            chunks_by_id=retriever.chunks_by_id,
            config=retrieval_config,
        )
        contradiction_candidates: list[CandidateEvidence] = []
        if retrieval_config.contradiction_enabled:
            if semantic_index is None:
                raise BundleWriterError("Contradiction retrieval requires a semantic index")
            try:
                contradiction_candidates = retrieve_contradicting(
                    claim=claim,
                    bm25_index=retriever,
                    semantic_index=semantic_index,
                    reranker=reranker,
                    chunks_by_id=retriever.chunks_by_id,
                    config=retrieval_config,
                )
            except (RerankerError, ValueError) as exc:
                raise BundleWriterError(str(exc)) from exc
            if not _counter_candidates(contradiction_candidates):
                no_countercandidate_claim_ids.append(claim.claim_id)
        candidates = _merge_supporting_and_counter_candidates(
            supporting_candidates=supporting_candidates,
            contradiction_candidates=contradiction_candidates,
        )
        candidates_by_claim[claim.claim_id] = candidates
        if not candidates:
            no_candidate_claim_ids.append(claim.claim_id)
        claim_summaries.append(
            _with_role_counts(
                summary,
                bundle_candidates=candidates,
                contradiction_candidates=contradiction_candidates,
            )
        )

    generated_at = _utc_now()
    bundle_id = str(
        uuid5(NAMESPACE_URL, f"evidence-bundler-retrieval:{artifact.manifest.run_id}:{config_hash}")
    )
    passage_records = _collect_retrieved_passage_records(
        artifact=artifact,
        candidates_by_claim=candidates_by_claim,
        bundle_id=bundle_id,
        bundle_created_at=generated_at,
    )

    _write_contract_version(output_dir)
    _write_retrieval_validation_set_ref(output_dir, generated_at, retrieval_config)

    audit_config = _make_retrieval_audit_config(generated_at, retrieval_config)
    audit_config_path = output_dir / "audit_config.yaml"
    write_model_yaml(audit_config, audit_config_path)
    audit_config = audit_config.model_copy(
        update={"config_hash": hash_audit_config_file(audit_config_path)}
    )
    write_model_yaml(audit_config, audit_config_path)

    _write_source_profiles(output_dir, artifact, passage_records)
    _write_passage_records(output_dir, passage_records)
    _write_retrieval_claim_units(
        output_dir,
        artifact,
        included_claims,
        candidates_by_claim,
        passage_records,
        bundle_id,
    )

    manifest = _make_retrieval_manifest(
        artifact=artifact,
        claims=included_claims,
        candidates_by_claim=candidates_by_claim,
        bundle_id=bundle_id,
        generated_at=generated_at,
        audit_config_hash=audit_config.config_hash,
        config_hash=config_hash,
        retrieval_config=retrieval_config,
        total_evidence_passages=len(passage_records),
    )
    manifest_path = output_dir / "bundle_manifest.yaml"
    write_model_yaml(manifest, manifest_path)
    manifest = manifest.model_copy(
        update={
            "bundle": manifest.bundle.model_copy(
                update={"bundle_hash": compute_bundle_tree_hash(output_dir)}
            )
        }
    )
    write_model_yaml(manifest, manifest_path)

    write_sha256sums(output_dir)
    errors = validate_bundle_tree(output_dir)
    if errors:
        raise BundleWriterError("; ".join(errors))

    report = RetrievalRunReport(
        scaffold_run_dir=artifact.root,
        bundle_dir=output_dir,
        run_id=artifact.manifest.run_id,
        generated_at_utc=generated_at,
        retrieval_config=retrieval_config,
        config_hash=config_hash,
        source_documents=len(documents),
        total_chunks=len(chunks),
        indexed_child_chunks=len(retriever.indexed_chunks),
        claims_in_source=len(artifact.claims.claims),
        claims_included=len(included_claims),
        no_candidate_claim_ids=no_candidate_claim_ids,
        no_countercandidate_claim_ids=no_countercandidate_claim_ids,
        claim_summaries=claim_summaries,
    )
    if report_out is not None:
        write_retrieval_report_markdown(report, report_out)

    return BundleBuildResult(bundle_dir=output_dir, manifest=manifest, retrieval_report=report)


def validate_bundle_tree(bundle_dir: Path) -> list[str]:
    """Validate local C-B tree shape, schemas, hashes, and SHA256SUMS."""
    errors: list[str] = []

    contract_path = bundle_dir / "CONTRACT_VERSION"
    if not contract_path.exists():
        errors.append("CONTRACT_VERSION file missing")
    elif contract_path.read_text(encoding="utf-8").strip() != CONTRACT_VERSION:
        errors.append("CONTRACT_VERSION mismatch")

    try:
        manifest = load_model_yaml(BundleManifest, bundle_dir / "bundle_manifest.yaml")
        audit_config = load_model_yaml(AuditConfig, bundle_dir / "audit_config.yaml")
        load_model_yaml(ValidationSetRef, bundle_dir / "validation_set_ref.yaml")
    except Exception as exc:  # noqa: BLE001 - report validation failures as tree errors.
        return [str(exc)]

    actual_audit_hash = hash_audit_config_file(bundle_dir / "audit_config.yaml")
    if audit_config.config_hash != actual_audit_hash:
        errors.append("audit_config.config_hash does not match normalized audit_config.yaml")
    if manifest.audit_config_hash != audit_config.config_hash:
        errors.append("bundle_manifest.audit_config_hash does not match audit_config.config_hash")

    actual_bundle_hash = compute_bundle_tree_hash(bundle_dir)
    if manifest.bundle.bundle_hash != actual_bundle_hash:
        errors.append("bundle.bundle_hash does not match recomputed bundle tree hash")

    for claim_path in sorted((bundle_dir / "claims").glob("*.yaml")):
        load_model_yaml(ClaimAuditUnit, claim_path)
    for source_profile_path in sorted((bundle_dir / "evidence").glob("*/source_profile.yaml")):
        load_model_yaml(SourceProfile, source_profile_path)
    for passage_path in sorted((bundle_dir / "evidence").glob("*/passages/*.yaml")):
        load_model_yaml(PassageRecord, passage_path)

    errors.extend(verify_sha256sums(bundle_dir))
    return errors


def write_retrieval_report_markdown(report: RetrievalRunReport, path: Path) -> None:
    """Write a Markdown report for a retrieval nomination run."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_retrieval_report_markdown(report), encoding="utf-8")


def render_retrieval_report_markdown(report: RetrievalRunReport) -> str:
    """Render retrieval run details without implying support verification."""
    bundle_dir = report.bundle_dir.as_posix() if report.bundle_dir is not None else "none"
    no_candidate = (
        ", ".join(f"`{claim_id}`" for claim_id in report.no_candidate_claim_ids) or "none"
    )
    no_countercandidate = (
        ", ".join(f"`{claim_id}`" for claim_id in report.no_countercandidate_claim_ids)
        or "none"
    )
    lines = [
        "# Retrieval Run Report",
        "",
        "Candidate passages are retrieval nominees and require review/audit.",
        "",
        f"- Scaffold run: `{report.scaffold_run_dir.as_posix()}`",
        f"- Bundle dir: `{bundle_dir}`",
        f"- Run id: `{report.run_id}`",
        f"- Generated at: `{report.generated_at_utc}`",
        f"- Retrieval method: `{report.retrieval_config.retrieval_method}`",
        f"- Config hash: `{report.config_hash}`",
        f"- Parent aggregation: `{report.retrieval_config.parent_aggregation}`",
        f"- Parent top-k: `{report.retrieval_config.top_k}`",
        f"- Child top-k: `{report.retrieval_config.child_top_k}`",
        f"- Lexical score floor: `{report.retrieval_config.lexical_score_floor}`",
        f"- Chunk max chars: `{report.retrieval_config.chunk_max_chars}`",
        f"- Chunk overlap chars: `{report.retrieval_config.chunk_overlap_chars}`",
        f"- Semantic model: `{report.retrieval_config.embedding_model}`",
        (
            "- Semantic model revision: "
            f"`{report.retrieval_config.embedding_model_revision or 'unpinned'}`"
        ),
        (
            "- Immutable model revisions required: "
            f"`{report.retrieval_config.require_immutable_model_revisions}`"
        ),
        f"- Semantic index path: `{_semantic_index_path_label(report.retrieval_config)}`",
        f"- Semantic child top-k: `{report.retrieval_config.semantic_child_top_k}`",
        f"- Hybrid lexical candidate pool: `{report.retrieval_config.rrf_candidate_pool}`",
        f"- RRF k constant: `{report.retrieval_config.rrf_k_constant}`",
        f"- Rerank enabled: `{report.retrieval_config.rerank_enabled}`",
        f"- Rerank model: `{report.retrieval_config.rerank_model}`",
        f"- Rerank model revision: `{report.retrieval_config.rerank_model_revision or 'unpinned'}`",
        f"- Rerank candidate limit: `{report.retrieval_config.rerank_top_n}`",
        f"- Contradiction retrieval enabled: `{report.retrieval_config.contradiction_enabled}`",
        f"- Contradiction top-k: `{report.retrieval_config.contradiction_top_k}`",
        (
            "- Contradiction query prefixes: "
            f"`{_contradiction_prefixes_label(report.retrieval_config)}`"
        ),
        f"- Contradiction rerank enabled: `{report.retrieval_config.contradiction_rerank_enabled}`",
        (
            "- Contradiction text gate enabled: "
            f"`{report.retrieval_config.contradiction_text_gate_enabled}`"
        ),
        f"- Source documents: `{report.source_documents}`",
        f"- Total chunks: `{report.total_chunks}`",
        f"- Indexed child/leaf chunks: `{report.indexed_child_chunks}`",
        f"- Claims in source: `{report.claims_in_source}`",
        f"- Claims included: `{report.claims_included}`",
        f"- No-candidate claims: {no_candidate}",
        f"- No counter-candidate claims: {no_countercandidate}",
        "",
        "## Claim Summaries",
        "",
        (
            "| Claim | Child hits | Lexical-only | Semantic-only | Overlap | Total fused | "
            "Unique parents | Selected candidates | Supporting | Contradicting | Conditional | "
            "Insufficient | Top lexical score | Top semantic score | Top fusion score | "
            "Top rerank score | Top child excerpt |"
        ),
        (
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
            "---: | --- | --- | --- | --- | --- |"
        ),
    ]
    for summary in report.claim_summaries:
        top_lexical_score = _score_cell(summary.top_lexical_score, "lexical")
        top_semantic_score = _score_cell(summary.top_semantic_score, "semantic")
        top_fusion_score = _score_cell(summary.top_fusion_score, "fusion")
        top_rerank_score = _score_cell(summary.top_rerank_score, "rerank")
        top_excerpt = _markdown_table_cell(summary.top_child_excerpt or "")
        lines.append(
            f"| `{summary.claim_id}` | {summary.child_hits} | "
            f"{_count_cell(summary.lexical_only_child_hits)} | "
            f"{_count_cell(summary.semantic_only_child_hits)} | "
            f"{_count_cell(summary.overlap_child_hits)} | "
            f"{_count_cell(summary.total_fused_child_hits)} | "
            f"{summary.unique_parent_hits} | {summary.selected_candidates} | "
            f"{summary.supporting_hits} | {summary.contradicting_hits} | "
            f"{summary.conditional_hits} | {summary.insufficient_hits} | "
            f"{top_lexical_score} | {top_semantic_score} | {top_fusion_score} | "
            f"{top_rerank_score} | {top_excerpt} |"
        )
    lines.append("")
    return "\n".join(lines)


def _prepare_output_dir(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise BundleWriterError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def _write_contract_version(output_dir: Path) -> None:
    (output_dir / "CONTRACT_VERSION").write_text(f"{CONTRACT_VERSION}\n", encoding="utf-8")


def _write_validation_set_ref(output_dir: Path, generated_at: str) -> ValidationSetRef:
    validation_ref = ValidationSetRef(
        schema_version=CONTRACT_VERSION,
        validation_set_version=VALIDATION_SET_VERSION,
        validation_set_hash=hash_text("phase-0-validation-set-placeholder-v1"),
        frozen_at_utc=generated_at,
        description="Phase 0 synthetic fixture validation-set pointer.",
        notes="Local C-B shape validation only; Claim Audit Lab C-B ingestion remains blocked.",
    )
    write_model_yaml(validation_ref, output_dir / "validation_set_ref.yaml")
    return validation_ref


def _write_retrieval_validation_set_ref(
    output_dir: Path,
    generated_at: str,
    config: RetrievalConfig,
) -> ValidationSetRef:
    version = _retrieval_validation_set_version(config)
    validation_ref = ValidationSetRef(
        schema_version=CONTRACT_VERSION,
        validation_set_version=version,
        validation_set_hash=_retrieval_validation_set_hash(config),
        frozen_at_utc=generated_at,
        description=f"{_retrieval_method_label(config)} retrieval validation-set pointer.",
        notes=(
            f"{_retrieval_method_label(config)} retrieval nominates candidate passages only; "
            "Claim Audit Lab remains "
            "responsible for support audit verdicts."
        ),
    )
    write_model_yaml(validation_ref, output_dir / "validation_set_ref.yaml")
    return validation_ref


def _make_audit_config(generated_at: str) -> AuditConfig:
    return AuditConfig(
        config_id=AUDIT_CONFIG_VERSION,
        config_hash=PENDING_HASH,
        schema_version=CONTRACT_VERSION,
        frozen_at_utc=generated_at,
        scoring=AuditScoringConfig(
            support_threshold_sourced=0.80,
            support_threshold_partial=0.55,
            counterevidence_weight=0.30,
        ),
        rule_policies=AuditRulePolicies(
            require_passage_level_match=True,
            flag_unsupported_threshold=0.40,
            false_caution_detection=True,
            false_caution_threshold=0.85,
            overstated_detection=True,
            needs_source_detection=True,
        ),
        known_limitations=[
            "Phase 0 does not run Claim Audit Lab.",
            "Phase 0 does not assign support verdicts or retrieval scores.",
        ],
        change_log=[
            AuditConfigChange(
                version="1.2.0",
                date="2026-05-01",
                changes=(
                    "Added false_caution_detection, overstated_detection, and "
                    "needs_source_detection rules."
                ),
                rationale="Fixture mirrors the locked C-B v1.0.0 audit-config shape.",
            )
        ],
    )


def _make_retrieval_audit_config(
    generated_at: str,
    retrieval_config: RetrievalConfig,
) -> AuditConfig:
    method_label = _retrieval_method_label(retrieval_config)
    omitted_steps = ["support review"]
    if not retrieval_config.rerank_enabled:
        omitted_steps.append("reranking")
    if not retrieval_config.contradiction_enabled:
        omitted_steps.append("contradiction retrieval")
    return AuditConfig(
        config_id=AUDIT_CONFIG_VERSION,
        config_hash=PENDING_HASH,
        schema_version=CONTRACT_VERSION,
        frozen_at_utc=generated_at,
        scoring=AuditScoringConfig(
            support_threshold_sourced=0.80,
            support_threshold_partial=0.55,
            counterevidence_weight=0.30,
        ),
        rule_policies=AuditRulePolicies(
            require_passage_level_match=True,
            flag_unsupported_threshold=0.40,
            false_caution_detection=True,
            false_caution_threshold=0.85,
            overstated_detection=True,
            needs_source_detection=True,
        ),
        known_limitations=[
            f"{method_label} retrieval nominates candidates and does not assign support verdicts.",
            f"This retrieval bundle does not run {_join_steps(omitted_steps)}.",
        ],
        change_log=[
            AuditConfigChange(
                version="1.2.0",
                date="2026-05-01",
                changes=(
                    "Added false_caution_detection, overstated_detection, and "
                    "needs_source_detection rules."
                ),
                rationale="Retrieval bundles preserve the locked C-B v1.0.0 audit-config shape.",
            )
        ],
    )


def _make_manifest(
    *,
    artifact: ScaffoldRunArtifact,
    bundle_id: str,
    generated_at: str,
    audit_config_hash: str,
    total_claims_included: int,
    total_evidence_passages: int,
) -> BundleManifest:
    total_claims = len(artifact.claims.claims)
    excluded = total_claims - total_claims_included
    return BundleManifest(
        bundle_id=bundle_id,
        schema_version=CONTRACT_VERSION,
        generated_at_utc=generated_at,
        source_run_id=artifact.manifest.run_id,
        source_contract_version=CONTRACT_VERSION,
        source_corpus_hash=artifact.manifest.corpus.corpus_hash,
        evidence_builder=EvidenceBuilderInfo(
            version=__version__,
            config_hash=hash_text("phase-0-fixture-bundle-config-v1"),
            operator=artifact.manifest.run_metadata.operator,
            build_timestamp_utc=generated_at,
        ),
        bundle=BundleStats(
            total_claims_in_source=total_claims,
            claims_included=total_claims_included,
            claims_excluded=excluded,
            exclusion_rationale=(
                f"{excluded} retrieval_seed claim(s) excluded; Phase 0 fixture output "
                "includes extracted_claim instances only."
            ),
            total_evidence_passages=total_evidence_passages,
            bundle_hash=PENDING_HASH,
        ),
        transformations=[
            TransformationRecord(
                type="fixture_pass_through",
                description=(
                    "Synthetic Phase 0 fixture copied scaffold-cited passages into C-B "
                    "without retrieval or support-verdict assignment."
                ),
                claims_affected=[claim.claim_id for claim in artifact.claims.claims],
            )
        ],
        quality_gates=QualityGates(
            every_claim_has_at_least_one_passage=True,
            every_passage_links_to_source_profile=True,
            source_hashes_verified=True,
            bundle_integrity_verified=True,
        ),
        audit_config_version=AUDIT_CONFIG_VERSION,
        audit_config_hash=audit_config_hash,
        validation_set_version=VALIDATION_SET_VERSION,
        validation_set_hash=hash_text("phase-0-validation-set-placeholder-v1"),
        reviewer_sign_off=ReviewerSignOff(required=False),
    )


def _make_retrieval_manifest(
    *,
    artifact: ScaffoldRunArtifact,
    claims: list[ScaffoldClaim],
    candidates_by_claim: dict[str, list[CandidateEvidence]],
    bundle_id: str,
    generated_at: str,
    audit_config_hash: str,
    config_hash: str,
    retrieval_config: RetrievalConfig,
    total_evidence_passages: int,
) -> BundleManifest:
    total_claims = len(artifact.claims.claims)
    excluded = total_claims - len(claims)
    claims_without_candidates = [
        claim.claim_id for claim in claims if not candidates_by_claim.get(claim.claim_id)
    ]
    method_label = _retrieval_method_label(retrieval_config)
    transformation_description = (
        f"{method_label} retrieval nominated parent-context candidate passages from "
        "child/leaf chunk matches; support verdicts remain unassigned."
    )
    if retrieval_config.rerank_enabled:
        transformation_description = (
            f"{method_label} retrieval nominated parent-context candidate passages from "
            "child/leaf chunk matches, then reranked parent candidates with the configured "
            "cross-encoder; support verdicts remain unassigned."
        )
    if retrieval_config.contradiction_enabled:
        transformation_description = (
            f"{transformation_description} A separate text-gated contradiction pass nominated "
            "counter-candidates where disconfirming or limiting language was found."
        )
    return BundleManifest(
        bundle_id=bundle_id,
        schema_version=CONTRACT_VERSION,
        generated_at_utc=generated_at,
        source_run_id=artifact.manifest.run_id,
        source_contract_version=CONTRACT_VERSION,
        source_corpus_hash=artifact.manifest.corpus.corpus_hash,
        evidence_builder=EvidenceBuilderInfo(
            version=__version__,
            config_hash=config_hash,
            operator=artifact.manifest.run_metadata.operator,
            build_timestamp_utc=generated_at,
        ),
        bundle=BundleStats(
            total_claims_in_source=total_claims,
            claims_included=len(claims),
            claims_excluded=excluded,
            exclusion_rationale=(
                f"{excluded} retrieval_seed claim(s) excluded; {method_label} retrieval "
                "includes extracted_claim instances only."
            ),
            total_evidence_passages=total_evidence_passages,
            bundle_hash=PENDING_HASH,
        ),
        transformations=[
            TransformationRecord(
                type=f"{retrieval_config.retrieval_method}_candidate_retrieval",
                description=transformation_description,
                claims_affected=[claim.claim_id for claim in claims],
            )
        ],
        quality_gates=QualityGates(
            every_claim_has_at_least_one_passage=not claims_without_candidates,
            every_passage_links_to_source_profile=True,
            source_hashes_verified=True,
            bundle_integrity_verified=True,
        ),
        audit_config_version=AUDIT_CONFIG_VERSION,
        audit_config_hash=audit_config_hash,
        validation_set_version=_retrieval_validation_set_version(retrieval_config),
        validation_set_hash=_retrieval_validation_set_hash(retrieval_config),
        reviewer_sign_off=ReviewerSignOff(required=False),
    )


def _collect_passage_records(
    *,
    artifact: ScaffoldRunArtifact,
    claims: list[ScaffoldClaim],
    bundle_id: str,
    bundle_created_at: str,
) -> dict[tuple[str, str], PassageRecord]:
    records: dict[tuple[str, str], PassageRecord] = {}
    for claim in claims:
        for source_ref in claim.source_refs:
            source = artifact.sources[source_ref.source_id]
            scaffold_passage = _find_passage(source, source_ref.passage_id)
            key = (source_ref.source_id, source_ref.passage_id)
            passage_text = _extract_passage_text(source.content_path, scaffold_passage)
            if key not in records:
                records[key] = PassageRecord(
                    passage_id=scaffold_passage.passage_id,
                    source_id=source.source_id,
                    bundle_id=bundle_id,
                    schema_version=CONTRACT_VERSION,
                    passage_text=passage_text,
                    section=scaffold_passage.section,
                    paragraph_index=scaffold_passage.paragraph_index,
                    char_start=scaffold_passage.char_start,
                    char_end=scaffold_passage.char_end,
                    passage_hash=hash_text(passage_text),
                    cited_by_claims=[],
                    extraction_method=scaffold_passage.extraction_method,
                    provenance=PassageProvenance(
                        source_url=source.metadata.bibliographic.url,
                        source_access_date_utc=source.metadata.bibliographic.access_date_utc,
                        source_content_hash=source.metadata.content_hash,
                        scaffold_run_id=artifact.manifest.run_id,
                        evidence_builder_version=__version__,
                        bundle_created_at_utc=bundle_created_at,
                    ),
                )
            cited = list(records[key].cited_by_claims)
            if claim.claim_id not in cited:
                cited.append(claim.claim_id)
                records[key] = records[key].model_copy(update={"cited_by_claims": cited})
    return records


def _collect_retrieved_passage_records(
    *,
    artifact: ScaffoldRunArtifact,
    candidates_by_claim: dict[str, list[CandidateEvidence]],
    bundle_id: str,
    bundle_created_at: str,
) -> dict[tuple[str, str], PassageRecord]:
    selected: dict[tuple[str, str], tuple[DocumentChunk, set[str]]] = {}
    for claim_id, candidates in candidates_by_claim.items():
        for candidate in candidates:
            parent = candidate.parent_chunk
            key = (parent.source_id, parent.chunk_id)
            if key not in selected:
                selected[key] = (parent, set())
            selected[key][1].add(claim_id)

    records: dict[tuple[str, str], PassageRecord] = {}
    paragraph_indices: dict[str, int] = {}
    for source_id, parent_chunk_id in sorted(
        selected,
        key=lambda key: (
            key[0],
            selected[key][0].char_start,
            selected[key][0].char_end,
            selected[key][0].chunk_id,
        ),
    ):
        parent, cited_by = selected[(source_id, parent_chunk_id)]
        source = artifact.sources[source_id]
        passage_id = _retrieved_passage_id(parent)
        paragraph_index = paragraph_indices.get(source_id, 0)
        paragraph_indices[source_id] = paragraph_index + 1
        records[(source_id, passage_id)] = PassageRecord(
            passage_id=passage_id,
            source_id=source_id,
            bundle_id=bundle_id,
            schema_version=CONTRACT_VERSION,
            passage_text=parent.text,
            section=_section_from_chunk(parent),
            paragraph_index=paragraph_index,
            char_start=parent.char_start,
            char_end=parent.char_end,
            passage_hash=hash_text(parent.text),
            cited_by_claims=sorted(cited_by),
            extraction_method="auto_retrieved",
            provenance=PassageProvenance(
                source_url=source.metadata.bibliographic.url,
                source_access_date_utc=source.metadata.bibliographic.access_date_utc,
                source_content_hash=source.metadata.content_hash,
                scaffold_run_id=artifact.manifest.run_id,
                evidence_builder_version=__version__,
                bundle_created_at_utc=bundle_created_at,
            ),
        )
    return records


def _write_source_profiles(
    output_dir: Path,
    artifact: ScaffoldRunArtifact,
    passage_records: dict[tuple[str, str], PassageRecord],
) -> None:
    source_ids = sorted({source_id for source_id, _ in passage_records})
    for source_id in source_ids:
        source = artifact.sources[source_id]
        profile = SourceProfile(
            source_id=source.source_id,
            schema_version=CONTRACT_VERSION,
            bibliographic=source.metadata.bibliographic,
            trust_level=source.metadata.trust_level,
            content_hash=source.metadata.content_hash,
            retrieved_for=source.metadata.retrieval.retrieved_for,
            retrieval_query=source.metadata.retrieval.retrieval_query,
            retrieval_rank=source.metadata.retrieval.retrieval_rank,
            notes=source.metadata.notes,
        )
        write_model_yaml(profile, output_dir / "evidence" / source_id / "source_profile.yaml")


def _write_passage_records(
    output_dir: Path,
    passage_records: dict[tuple[str, str], PassageRecord],
) -> None:
    for (source_id, passage_id), record in sorted(passage_records.items()):
        write_model_yaml(
            record,
            output_dir / "evidence" / source_id / "passages" / f"{passage_id}.yaml",
        )


def _write_claim_units(
    output_dir: Path,
    artifact: ScaffoldRunArtifact,
    claims: list[ScaffoldClaim],
    passage_records: dict[tuple[str, str], PassageRecord],
    bundle_id: str,
) -> None:
    for claim in claims:
        evidence_passages = []
        for source_ref in claim.source_refs:
            record = passage_records[(source_ref.source_id, source_ref.passage_id)]
            source = artifact.sources[source_ref.source_id]
            evidence_passages.append(
                ClaimEvidencePassage(
                    passage_id=record.passage_id,
                    source_id=record.source_id,
                    passage_text=record.passage_text,
                    section=record.section,
                    char_start=record.char_start,
                    char_end=record.char_end,
                    source_trust_level=source.metadata.trust_level,
                    passage_hash=record.passage_hash,
                )
            )

        unit = ClaimAuditUnit(
            claim_id=claim.claim_id,
            bundle_id=bundle_id,
            schema_version=CONTRACT_VERSION,
            claim_text=claim.claim_text,
            claim_type=claim.claim_type,
            workflow_condition=artifact.manifest.workflow_condition,
            task_id=artifact.manifest.task_id,
            scaffold_support_status=claim.support_status,
            scaffold_claim_strength=claim.claim_strength,
            scaffold_extraction_fidelity=claim.extraction_fidelity,
            scaffold_counterevidence_found=claim.counterevidence_found,
            scaffold_downgraded=claim.downgraded,
            evidence_passages=evidence_passages,
            counterevidence_passages=[],
        )
        write_model_yaml(unit, output_dir / "claims" / f"{claim.claim_id}.yaml")


def _write_retrieval_claim_units(
    output_dir: Path,
    artifact: ScaffoldRunArtifact,
    claims: list[ScaffoldClaim],
    candidates_by_claim: dict[str, list[CandidateEvidence]],
    passage_records: dict[tuple[str, str], PassageRecord],
    bundle_id: str,
) -> None:
    for claim in claims:
        evidence_passages = []
        counterevidence_passages = []
        for candidate in candidates_by_claim.get(claim.claim_id, []):
            parent = candidate.parent_chunk
            passage_id = _retrieved_passage_id(parent)
            record = passage_records[(parent.source_id, passage_id)]
            passage = _claim_evidence_passage(artifact, record)
            if candidate.evidence_role == "supporting":
                evidence_passages.append(passage)
            elif candidate.evidence_role in {"contradicting", "conditional"}:
                counterevidence_passages.append(passage)

        unit = ClaimAuditUnit(
            claim_id=claim.claim_id,
            bundle_id=bundle_id,
            schema_version=CONTRACT_VERSION,
            claim_text=claim.claim_text,
            claim_type=claim.claim_type,
            workflow_condition=artifact.manifest.workflow_condition,
            task_id=artifact.manifest.task_id,
            scaffold_support_status=claim.support_status,
            scaffold_claim_strength=claim.claim_strength,
            scaffold_extraction_fidelity=claim.extraction_fidelity,
            scaffold_counterevidence_found=claim.counterevidence_found,
            scaffold_downgraded=claim.downgraded,
            evidence_passages=evidence_passages,
            counterevidence_passages=counterevidence_passages,
        )
        write_model_yaml(unit, output_dir / "claims" / f"{claim.claim_id}.yaml")


def _claim_evidence_passage(
    artifact: ScaffoldRunArtifact,
    record: PassageRecord,
) -> ClaimEvidencePassage:
    source = artifact.sources[record.source_id]
    return ClaimEvidencePassage(
        passage_id=record.passage_id,
        source_id=record.source_id,
        passage_text=record.passage_text,
        section=record.section,
        char_start=record.char_start,
        char_end=record.char_end,
        source_trust_level=source.metadata.trust_level,
        passage_hash=record.passage_hash,
    )


def _merge_supporting_and_counter_candidates(
    *,
    supporting_candidates: list[CandidateEvidence],
    contradiction_candidates: list[CandidateEvidence],
) -> list[CandidateEvidence]:
    counter_candidates = _counter_candidates(contradiction_candidates)
    counter_keys = {_candidate_parent_key(candidate) for candidate in counter_candidates}
    supporting_kept = [
        candidate
        for candidate in supporting_candidates
        if _candidate_parent_key(candidate) not in counter_keys
    ]
    return supporting_kept + counter_candidates


def _counter_candidates(candidates: list[CandidateEvidence]) -> list[CandidateEvidence]:
    return [
        candidate
        for candidate in candidates
        if candidate.evidence_role in {"contradicting", "conditional"}
    ]


def _candidate_parent_key(candidate: CandidateEvidence) -> tuple[str, str]:
    parent = candidate.parent_chunk
    return (parent.source_id, parent.chunk_id)


def _with_role_counts(
    summary: RetrievalClaimSummary,
    *,
    bundle_candidates: list[CandidateEvidence],
    contradiction_candidates: list[CandidateEvidence],
) -> RetrievalClaimSummary:
    return summary.model_copy(
        update={
            "supporting_hits": _role_count(bundle_candidates, "supporting"),
            "contradicting_hits": _role_count(contradiction_candidates, "contradicting"),
            "conditional_hits": _role_count(contradiction_candidates, "conditional"),
            "insufficient_hits": _role_count(contradiction_candidates, "insufficient"),
            "selected_candidates": len(bundle_candidates),
            "no_candidate": not bundle_candidates,
        }
    )


def _role_count(candidates: list[CandidateEvidence], role: str) -> int:
    return sum(1 for candidate in candidates if candidate.evidence_role == role)


def _load_semantic_index_if_needed(
    config: RetrievalConfig,
    chunks: list[DocumentChunk],
    artifact: ScaffoldRunArtifact,
) -> SemanticIndex | None:
    if config.retrieval_method not in {"semantic", "hybrid"}:
        return None

    try:
        embedder = load_embedding_model(
            str(config.embedding_model),
            cache_dir=config.embedding_model_cache_dir,
            revision=(
                str(config.embedding_model_revision)
                if config.embedding_model_revision is not None
                else None
            ),
        )
        index_path = config.semantic_index_path
        if index_path is not None:
            if index_path.exists() and not index_path.is_dir():
                raise BundleWriterError(f"Semantic index path is not a directory: {index_path}")
            if index_path.exists():
                try:
                    return SemanticIndex.load(
                        index_path,
                        embedder=embedder,
                        corpus_hash=artifact.manifest.corpus.corpus_hash,
                        embedding_model=str(config.embedding_model),
                        embedding_model_revision=(
                            str(config.embedding_model_revision)
                            if config.embedding_model_revision is not None
                            else None
                        ),
                        chunk_set_hash=compute_semantic_chunk_set_hash(chunks),
                        semantic_query_prefix=str(config.semantic_query_prefix)
                        if config.semantic_query_prefix is not None
                        else None,
                    )
                except (FileNotFoundError, SemanticIndexManifestMismatch):
                    pass

        index = SemanticIndex.build(
            chunks,
            embedder=embedder,
            corpus_hash=artifact.manifest.corpus.corpus_hash,
            embedding_model=str(config.embedding_model),
            embedding_model_revision=(
                str(config.embedding_model_revision)
                if config.embedding_model_revision is not None
                else None
            ),
            semantic_query_prefix=str(config.semantic_query_prefix)
            if config.semantic_query_prefix is not None
            else None,
            show_progress_bar=False,
        )
        if index_path is not None:
            index.save(index_path)
        return index
    except SemanticIndexError as exc:
        raise BundleWriterError(str(exc)) from exc


def _load_reranker_if_needed(config: RetrievalConfig) -> ParentReranker | None:
    if not config.rerank_enabled:
        return None
    try:
        return ParentReranker(
            load_reranker_model(
                str(config.rerank_model),
                revision=(
                    str(config.rerank_model_revision)
                    if config.rerank_model_revision is not None
                    else None
                ),
            )
        )
    except RerankerError as exc:
        raise BundleWriterError(str(exc)) from exc


def _retrieve_claim_candidates(
    *,
    claim: ScaffoldClaim,
    retriever: BM25Retriever,
    semantic_index: SemanticIndex | None,
    reranker: ParentReranker | None,
    chunks_by_id: dict[str, DocumentChunk],
    config: RetrievalConfig,
) -> tuple[list[CandidateEvidence], RetrievalClaimSummary]:
    if config.retrieval_method == "hybrid":
        if semantic_index is None:
            raise BundleWriterError("Hybrid retrieval requires a semantic index")
        return _retrieve_hybrid_claim(
            claim=claim,
            retriever=retriever,
            semantic_index=semantic_index,
            reranker=reranker,
            chunks_by_id=chunks_by_id,
            config=config,
        )
    if config.retrieval_method == "semantic":
        if semantic_index is None:
            raise BundleWriterError("Semantic retrieval requires a semantic index")
        return _retrieve_semantic_claim(
            claim=claim,
            semantic_index=semantic_index,
            chunks_by_id=chunks_by_id,
            config=config,
        )

    hits = retriever.query(
        claim.claim_text,
        top_k=config.child_top_k,
        score_floor=config.lexical_score_floor,
    )
    candidates = aggregate_parent_candidates(
        claim=claim,
        hits=hits,
        chunks_by_id=chunks_by_id,
        config=config,
    )
    return candidates, _make_claim_summary(
        claim=claim,
        candidates=candidates,
        hits=hits,
        lexical_only_child_hits=len(hits),
        semantic_only_child_hits=0,
        overlap_child_hits=0,
        total_fused_child_hits=len(hits),
    )


def _retrieve_semantic_claim(
    *,
    claim: ScaffoldClaim,
    semantic_index: SemanticIndex,
    chunks_by_id: dict[str, DocumentChunk],
    config: RetrievalConfig,
) -> tuple[list[CandidateEvidence], RetrievalClaimSummary]:
    semantic_hits = semantic_index.query(
        claim.claim_text,
        top_k=config.semantic_child_top_k,
    )
    hits = [
        ChunkSearchHit(
            chunk=hit.chunk,
            score=hit.semantic_score,
            rank=hit.rank,
            semantic_score=hit.semantic_score,
            semantic_rank=hit.rank,
        )
        for hit in semantic_hits
    ]
    candidates = aggregate_parent_candidates(
        claim=claim,
        hits=hits,
        chunks_by_id=chunks_by_id,
        config=config,
    )
    return candidates, _make_claim_summary(
        claim=claim,
        candidates=candidates,
        hits=hits,
        lexical_only_child_hits=0,
        semantic_only_child_hits=len(hits),
        overlap_child_hits=0,
        total_fused_child_hits=len(hits),
    )


def _retrieve_hybrid_claim(
    *,
    claim: ScaffoldClaim,
    retriever: BM25Retriever,
    semantic_index: SemanticIndex,
    reranker: ParentReranker | None,
    chunks_by_id: dict[str, DocumentChunk],
    config: RetrievalConfig,
) -> tuple[list[CandidateEvidence], RetrievalClaimSummary]:
    lexical_hits = retriever.query(
        claim.claim_text,
        top_k=config.rrf_candidate_pool,
        score_floor=config.lexical_score_floor,
    )
    semantic_hits = semantic_index.query(claim.claim_text, top_k=config.semantic_child_top_k)
    lexical_ids = [hit.chunk.chunk_id for hit in lexical_hits]
    semantic_ids = [hit.chunk.chunk_id for hit in semantic_hits]
    fused_ranks = reciprocal_rank_fusion(
        [lexical_ids, semantic_ids],
        k=config.rrf_k_constant,
    )
    lexical_by_id = {hit.chunk.chunk_id: hit for hit in lexical_hits}
    semantic_by_id = {hit.chunk.chunk_id: hit for hit in semantic_hits}
    fused_hits = [
        _make_fused_hit(
            fused_rank=fused_rank,
            chunks_by_id=chunks_by_id,
            lexical_by_id=lexical_by_id,
            semantic_by_id=semantic_by_id,
        )
        for fused_rank in fused_ranks
    ]
    parent_pool_limit = max(config.top_k, config.rerank_top_n) if config.rerank_enabled else None
    candidates = aggregate_parent_candidates(
        claim=claim,
        hits=fused_hits,
        chunks_by_id=chunks_by_id,
        config=config,
        limit=parent_pool_limit,
    )
    if config.rerank_enabled:
        if reranker is None:
            raise BundleWriterError("Hybrid reranking requires a reranker model")
        candidates = _rerank_parent_candidates(
            claim=claim,
            candidates=candidates,
            reranker=reranker,
            config=config,
        )
    lexical_set = set(lexical_ids)
    semantic_set = set(semantic_ids)
    overlap = lexical_set & semantic_set
    return candidates, _make_claim_summary(
        claim=claim,
        candidates=candidates,
        hits=fused_hits,
        lexical_only_child_hits=len(lexical_set - semantic_set),
        semantic_only_child_hits=len(semantic_set - lexical_set),
        overlap_child_hits=len(overlap),
        total_fused_child_hits=len(lexical_set | semantic_set),
    )


def _rerank_parent_candidates(
    *,
    claim: ScaffoldClaim,
    candidates: list[CandidateEvidence],
    reranker: ParentReranker,
    config: RetrievalConfig,
) -> list[CandidateEvidence]:
    rerankable = candidates[: config.rerank_top_n]
    tail = candidates[config.rerank_top_n :]
    try:
        reranked = reranker.rerank(claim.claim_text, rerankable)
    except RerankerError as exc:
        raise BundleWriterError(str(exc)) from exc
    return (reranked + tail)[: config.top_k]


def _make_fused_hit(
    *,
    fused_rank: FusedChunkRank,
    chunks_by_id: dict[str, DocumentChunk],
    lexical_by_id: dict[str, ChunkSearchHit],
    semantic_by_id: dict[str, SemanticSearchHit],
) -> ChunkSearchHit:
    chunk = chunks_by_id.get(fused_rank.chunk_id)
    if chunk is None:
        raise BundleWriterError(
            f"Hybrid retrieval returned unknown chunk id: {fused_rank.chunk_id}"
        )
    lexical_hit = lexical_by_id.get(fused_rank.chunk_id)
    semantic_hit = semantic_by_id.get(fused_rank.chunk_id)
    return ChunkSearchHit(
        chunk=chunk,
        score=fused_rank.fusion_score,
        rank=fused_rank.rank,
        lexical_score=lexical_hit.score if lexical_hit is not None else None,
        semantic_score=semantic_hit.semantic_score if semantic_hit is not None else None,
        fusion_score=fused_rank.fusion_score,
        lexical_rank=fused_rank.lexical_rank,
        semantic_rank=fused_rank.semantic_rank,
    )


def _make_claim_summary(
    *,
    claim: ScaffoldClaim,
    candidates: list[CandidateEvidence],
    hits: list[ChunkSearchHit],
    lexical_only_child_hits: int,
    semantic_only_child_hits: int,
    overlap_child_hits: int,
    total_fused_child_hits: int,
) -> RetrievalClaimSummary:
    return RetrievalClaimSummary(
        claim_id=claim.claim_id,
        claim_text=claim.claim_text,
        child_hits=len(hits),
        lexical_only_child_hits=lexical_only_child_hits,
        semantic_only_child_hits=semantic_only_child_hits,
        overlap_child_hits=overlap_child_hits,
        total_fused_child_hits=total_fused_child_hits,
        unique_parent_hits=len({hit.chunk.parent_chunk_id or hit.chunk.chunk_id for hit in hits}),
        selected_candidates=len(candidates),
        no_candidate=not candidates,
        supporting_hits=len(candidates),
        top_lexical_score=_max_candidate_score(candidates, "lexical_score"),
        top_semantic_score=_max_candidate_score(candidates, "semantic_score"),
        top_fusion_score=_max_candidate_score(candidates, "fusion_score"),
        top_rerank_score=_max_candidate_score(candidates, "rerank_score"),
        top_child_excerpt=candidates[0].matched_child_chunk.excerpt if candidates else None,
    )


def _max_candidate_score(
    candidates: list[CandidateEvidence],
    field_name: str,
) -> float | None:
    values = [
        value
        for value in (getattr(candidate, field_name) for candidate in candidates)
        if value is not None
    ]
    return max(values) if values else None


def _find_passage(source: SourceArtifact, passage_id: str) -> ScaffoldPassage:
    for passage in source.passages.passages:
        if passage.passage_id == passage_id:
            return passage
    raise BundleWriterError(f"Source {source.source_id} missing passage {passage_id}")


def _extract_passage_text(content_path: Path, passage: ScaffoldPassage) -> str:
    if content_path.suffix == ".pdf":
        raise BundleWriterError("Phase 0 fixture writer does not extract PDF passages")
    content = content_path.read_text(encoding="utf-8")
    try:
        passage_text = content[passage.char_start : passage.char_end]
    except IndexError as exc:
        raise BundleWriterError(f"Invalid passage offsets for {passage.passage_id}") from exc
    if not passage_text.strip():
        raise BundleWriterError(f"Empty passage text for {passage.passage_id}")
    return passage_text


def _retrieval_config_hash(config: RetrievalConfig) -> str:
    dumped = config.model_dump(mode="json")
    dumped.pop("embedding_model_cache_dir", None)
    dumped.pop("semantic_index_path", None)
    return hash_text(yaml_to_string(dumped))


def _retrieval_validation_set_version(config: RetrievalConfig) -> str:
    if config.retrieval_method == "hybrid":
        return HYBRID_VALIDATION_SET_VERSION
    if config.retrieval_method == "semantic":
        return SEMANTIC_VALIDATION_SET_VERSION
    return RETRIEVAL_VALIDATION_SET_VERSION


def _retrieval_validation_set_hash(config: RetrievalConfig) -> str:
    if config.retrieval_method == "hybrid":
        return hash_text("phase-2b-hybrid-validation-set-placeholder-v1")
    if config.retrieval_method == "semantic":
        return hash_text("phase-2b-semantic-validation-set-placeholder-v1")
    return hash_text("phase-2a-lexical-validation-set-placeholder-v1")


def _retrieval_method_label(config: RetrievalConfig) -> str:
    if config.retrieval_method == "hybrid":
        return "Hybrid BM25 + semantic"
    if config.retrieval_method == "semantic":
        return "Semantic"
    return "BM25 lexical"


def _retrieved_passage_id(chunk: DocumentChunk) -> str:
    digest = hash_text(
        f"{chunk.chunk_id}\0{chunk.chunk_hash}\0{chunk.char_start}\0{chunk.char_end}"
    )
    return f"auto-{chunk.source_id}-{digest.removeprefix('sha256:')[:12]}"


def _section_from_chunk(chunk: DocumentChunk) -> str | None:
    if chunk.heading_path:
        return " > ".join(chunk.heading_path)
    return chunk.section_tag


def _markdown_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _score_cell(value: float | None, label: str) -> str:
    if value is None:
        return f"no {label} score"
    return f"{value:.6f}"


def _count_cell(value: int | None) -> str:
    return "n/a" if value is None else str(value)


def _join_steps(steps: list[str]) -> str:
    if len(steps) == 1:
        return steps[0]
    if len(steps) == 2:
        return f"{steps[0]} or {steps[1]}"
    return f"{', '.join(steps[:-1])}, or {steps[-1]}"


def _semantic_index_path_label(config: RetrievalConfig) -> str:
    if config.semantic_index_path is not None:
        return config.semantic_index_path.as_posix()
    if config.retrieval_method in {"semantic", "hybrid"}:
        return "none (transient)"
    return "none"


def _contradiction_prefixes_label(config: RetrievalConfig) -> str:
    return ", ".join(str(prefix) for prefix in config.contradiction_query_prefixes)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
