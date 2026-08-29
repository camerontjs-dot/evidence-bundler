"""Internal retrieval models for lexical candidate nomination."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from evidence_bundler.models.common import HashValue, NonBlankStr, StrictBaseModel
from evidence_bundler.models.document import DocumentChunk

RetrievalMethod = Literal["bm25", "semantic", "hybrid"]
ParentAggregation = Literal["max"]
EvidenceRole = Literal["supporting", "contradicting", "conditional", "insufficient"]
IMMUTABLE_MODEL_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")

DEFAULT_CONTRADICTION_QUERY_PREFIXES = (
    "evidence against",
    "limitations of",
    "contradicts the claim that",
    "does not support",
    "fails to demonstrate",
)


class RetrievalConfig(StrictBaseModel):
    """Config snapshot for a deterministic retrieval run."""

    retrieval_method: RetrievalMethod = "bm25"
    top_k: int = Field(default=5, gt=0)
    parent_candidate_top_k: int | None = Field(default=None, gt=0)
    child_top_k: int = Field(default=20, gt=0)
    parent_aggregation: ParentAggregation = "max"
    lexical_score_floor: float = Field(default=0.0, ge=0.0)
    chunk_max_chars: int = Field(default=1800, gt=0)
    chunk_overlap_chars: int = Field(default=80, ge=0)
    embedding_model: NonBlankStr = "BAAI/bge-small-en-v1.5"
    embedding_model_revision: NonBlankStr | None = None
    embedding_model_cache_dir: Path | None = None
    semantic_index_path: Path | None = None
    semantic_child_top_k: int = Field(default=50, gt=0)
    semantic_query_prefix: NonBlankStr | None = (
        "Represent this sentence for searching relevant passages: "
    )
    rrf_candidate_pool: int = Field(default=50, gt=0)
    rrf_k_constant: int = Field(default=60, gt=0)
    rerank_enabled: bool = False
    rerank_model: NonBlankStr = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_model_revision: NonBlankStr | None = None
    require_immutable_model_revisions: bool = False
    rerank_top_n: int = Field(default=30, gt=0)
    contradiction_enabled: bool = False
    contradiction_top_k: int = Field(default=20, gt=0)
    counterevidence_lexical_child_top_k: int | None = Field(default=None, gt=0)
    counterevidence_semantic_child_top_k: int | None = Field(default=None, gt=0)
    contradiction_query_prefixes: list[NonBlankStr] = Field(
        default_factory=lambda: list(DEFAULT_CONTRADICTION_QUERY_PREFIXES),
        min_length=1,
    )
    contradiction_rerank_enabled: bool = False
    contradiction_text_gate_enabled: bool = True

    @model_validator(mode="after")
    def validate_retrieval_feature_dependencies(self) -> Self:
        """Validate feature knobs that depend on the hybrid retrieval stack."""
        if self.chunk_overlap_chars >= self.chunk_max_chars:
            raise ValueError("chunk_overlap_chars must be smaller than chunk_max_chars")
        if self.parent_candidate_top_k is not None and self.parent_candidate_top_k < self.top_k:
            raise ValueError("parent_candidate_top_k must be greater than or equal to top_k")
        for field_name, revision in (
            ("embedding_model_revision", self.embedding_model_revision),
            ("rerank_model_revision", self.rerank_model_revision),
        ):
            if revision is not None and not IMMUTABLE_MODEL_REVISION_RE.fullmatch(str(revision)):
                raise ValueError(f"{field_name} must be a full 40-hex commit SHA")
        if (
            self.require_immutable_model_revisions
            and self.retrieval_method in {"semantic", "hybrid"}
        ):
            if self.embedding_model_revision is None:
                raise ValueError(
                    "immutable semantic execution requires embedding_model_revision"
                )
        if self.require_immutable_model_revisions and self.rerank_enabled:
            if self.rerank_model_revision is None:
                raise ValueError("immutable reranking requires rerank_model_revision")
        if self.rerank_enabled and self.retrieval_method != "hybrid":
            raise ValueError("rerank_enabled requires retrieval_method='hybrid'")
        if self.contradiction_enabled and self.retrieval_method != "hybrid":
            raise ValueError("contradiction_enabled requires retrieval_method='hybrid'")
        if self.contradiction_rerank_enabled and not self.contradiction_enabled:
            raise ValueError("contradiction_rerank_enabled requires contradiction_enabled=True")
        if self.contradiction_rerank_enabled and not self.rerank_enabled:
            raise ValueError("contradiction_rerank_enabled requires rerank_enabled=True")
        return self


class CandidateEvidence(StrictBaseModel):
    """A retrieval nominee; not a reviewed evidence judgment."""

    claim_id: NonBlankStr
    claim_text: NonBlankStr
    parent_chunk: DocumentChunk
    matched_child_chunk: DocumentChunk
    child_rank: int = Field(ge=1)
    lexical_score: float | None = Field(default=None, ge=0.0)
    semantic_score: float | None = Field(default=None)
    fusion_score: float | None = Field(default=None, ge=0.0)
    rerank_score: float | None = None
    retrieval_method: RetrievalMethod = "bm25"
    llm_assisted: bool = False
    evidence_role: EvidenceRole


class RetrievalClaimSummary(StrictBaseModel):
    """Per-claim retrieval report row."""

    claim_id: NonBlankStr
    claim_text: NonBlankStr
    child_hits: int = Field(ge=0)
    lexical_only_child_hits: int | None = Field(default=None, ge=0)
    semantic_only_child_hits: int | None = Field(default=None, ge=0)
    overlap_child_hits: int | None = Field(default=None, ge=0)
    total_fused_child_hits: int | None = Field(default=None, ge=0)
    unique_parent_hits: int = Field(ge=0)
    selected_candidates: int = Field(ge=0)
    no_candidate: bool
    supporting_hits: int = Field(default=0, ge=0)
    contradicting_hits: int = Field(default=0, ge=0)
    conditional_hits: int = Field(default=0, ge=0)
    insufficient_hits: int = Field(default=0, ge=0)
    top_lexical_score: float | None = Field(default=None, ge=0.0)
    top_semantic_score: float | None = Field(default=None)
    top_fusion_score: float | None = Field(default=None, ge=0.0)
    top_rerank_score: float | None = None
    top_child_excerpt: str | None = None


class RetrievalRunReport(StrictBaseModel):
    """Summary of one BM25 retrieval run."""

    scaffold_run_dir: Path
    bundle_dir: Path | None = None
    run_id: NonBlankStr
    generated_at_utc: NonBlankStr
    retrieval_config: RetrievalConfig
    config_hash: HashValue
    source_documents: int = Field(ge=0)
    total_chunks: int = Field(ge=0)
    indexed_child_chunks: int = Field(ge=0)
    claims_in_source: int = Field(ge=0)
    claims_included: int = Field(ge=0)
    no_candidate_claim_ids: list[NonBlankStr] = Field(default_factory=list)
    no_countercandidate_claim_ids: list[NonBlankStr] = Field(default_factory=list)
    claim_summaries: list[RetrievalClaimSummary] = Field(default_factory=list)
