"""Contradiction and conditional candidate retrieval."""

from __future__ import annotations

import re
from collections.abc import Iterable

from evidence_bundler.models.ca import ScaffoldClaim
from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.models.retrieval import CandidateEvidence, EvidenceRole, RetrievalConfig
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
from evidence_bundler.retrieval.embedding_retriever import SemanticIndex, SemanticSearchHit
from evidence_bundler.retrieval.hits import ChunkSearchHit
from evidence_bundler.retrieval.hybrid import FusedChunkRank, reciprocal_rank_fusion
from evidence_bundler.retrieval.parent_aggregator import aggregate_parent_candidates
from evidence_bundler.retrieval.reranker import ParentReranker, RerankerError

DISCONFIRMING_PATTERNS = (
    "did not",
    "does not",
    "failed",
    "failure",
    "never",
    "contrary to",
    "contradicts",
    "refutes",
    "disproves",
    "no significant effect",
    "no effect",
    "ineffective",
    "not effective",
)
LIMITING_PATTERNS = (
    "only when",
    "only if",
    "except",
    "limited to",
    "restricted to",
    "provided that",
    "subject to",
    "contraindicated",
    "not applicable to",
    "not indicated",
)
LIMITING_REGEX_PATTERNS = (
    r"\bin patients (?:over|under|with)\b",
    (
        r"\bfor "
        r"(?:patients|adults|children|subjects|participants|women|men|people|subgroups?|cohorts?)\b"
    ),
)


def build_contradiction_queries(claim_text: str, prefixes: list[str]) -> list[str]:
    """Return deterministic fixed-prefix contradiction queries."""
    stripped = claim_text.strip()
    return [f"{prefix} {stripped}" for prefix in prefixes]


def retrieve_contradicting(
    *,
    claim: ScaffoldClaim,
    bm25_index: BM25Retriever,
    semantic_index: SemanticIndex,
    reranker: ParentReranker | None,
    chunks_by_id: dict[str, DocumentChunk],
    config: RetrievalConfig,
) -> list[CandidateEvidence]:
    """Run the ADR-010 contradiction pass over the existing hybrid stack."""
    queries = build_contradiction_queries(
        claim.claim_text,
        [str(prefix) for prefix in config.contradiction_query_prefixes],
    )
    rankings: list[list[str]] = []
    lexical_by_id: dict[str, ChunkSearchHit] = {}
    semantic_by_id: dict[str, SemanticSearchHit] = {}

    for query in queries:
        lexical_hits = bm25_index.query(
            query,
            top_k=(config.counterevidence_lexical_child_top_k or config.rrf_candidate_pool),
            score_floor=config.lexical_score_floor,
        )
        semantic_hits = semantic_index.query(
            query,
            top_k=(config.counterevidence_semantic_child_top_k or config.rrf_candidate_pool),
        )
        rankings.append([hit.chunk.chunk_id for hit in lexical_hits])
        rankings.append([hit.chunk.chunk_id for hit in semantic_hits])
        _keep_best_lexical_hits(lexical_by_id, lexical_hits)
        _keep_best_semantic_hits(semantic_by_id, semantic_hits)

    fused_ranks = reciprocal_rank_fusion(rankings, k=config.rrf_k_constant)
    fused_hits = [
        _make_fused_hit(
            fused_rank=fused_rank,
            chunks_by_id=chunks_by_id,
            lexical_by_id=lexical_by_id,
            semantic_by_id=semantic_by_id,
        )
        for fused_rank in fused_ranks
    ]
    parent_pool_limit = (
        max(config.contradiction_top_k, config.rerank_top_n)
        if config.contradiction_rerank_enabled
        else config.contradiction_top_k
    )
    candidates = aggregate_parent_candidates(
        claim=claim,
        hits=fused_hits,
        chunks_by_id=chunks_by_id,
        config=config,
        limit=parent_pool_limit,
    )
    candidates = [
        candidate.model_copy(
            update={
                "evidence_role": classify_role(candidate.parent_chunk.text, config),
            }
        )
        for candidate in candidates
    ]
    candidates = [c for c in candidates if c.evidence_role != "insufficient"]
    if config.contradiction_rerank_enabled:
        if reranker is None:
            raise RerankerError("Contradiction reranking requires a reranker model")
        candidates = reranker.rerank(claim.claim_text, candidates)
    return candidates[: config.contradiction_top_k]


def classify_role(passage_text: str, config: RetrievalConfig) -> EvidenceRole:
    """Classify a contradiction-pass hit with the ADR-010 text-pattern gate."""
    if not config.contradiction_text_gate_enabled:
        return "contradicting"
    if _matches_any(passage_text, _literal_patterns(DISCONFIRMING_PATTERNS)):
        return "contradicting"
    limiting_patterns = [*_literal_patterns(LIMITING_PATTERNS), *LIMITING_REGEX_PATTERNS]
    if _matches_any(passage_text, limiting_patterns):
        return "conditional"
    return "insufficient"


def _literal_patterns(patterns: Iterable[str]) -> list[str]:
    return [rf"(?<!\w){re.escape(pattern)}(?!\w)" for pattern in patterns]


def _matches_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _keep_best_lexical_hits(
    best_by_id: dict[str, ChunkSearchHit],
    hits: list[ChunkSearchHit],
) -> None:
    for hit in hits:
        current = best_by_id.get(hit.chunk.chunk_id)
        if current is None or _is_better_chunk_hit(hit, current):
            best_by_id[hit.chunk.chunk_id] = hit


def _keep_best_semantic_hits(
    best_by_id: dict[str, SemanticSearchHit],
    hits: list[SemanticSearchHit],
) -> None:
    for hit in hits:
        current = best_by_id.get(hit.chunk.chunk_id)
        if current is None or _is_better_semantic_hit(hit, current):
            best_by_id[hit.chunk.chunk_id] = hit


def _is_better_chunk_hit(candidate: ChunkSearchHit, current: ChunkSearchHit) -> bool:
    if candidate.score != current.score:
        return candidate.score > current.score
    if candidate.rank != current.rank:
        return candidate.rank < current.rank
    return candidate.chunk.chunk_id < current.chunk.chunk_id


def _is_better_semantic_hit(
    candidate: SemanticSearchHit,
    current: SemanticSearchHit,
) -> bool:
    if candidate.semantic_score != current.semantic_score:
        return candidate.semantic_score > current.semantic_score
    if candidate.rank != current.rank:
        return candidate.rank < current.rank
    return candidate.chunk.chunk_id < current.chunk.chunk_id


def _make_fused_hit(
    *,
    fused_rank: FusedChunkRank,
    chunks_by_id: dict[str, DocumentChunk],
    lexical_by_id: dict[str, ChunkSearchHit],
    semantic_by_id: dict[str, SemanticSearchHit],
) -> ChunkSearchHit:
    chunk = chunks_by_id.get(fused_rank.chunk_id)
    if chunk is None:
        raise ValueError(
            f"Contradiction retrieval returned unknown chunk id: {fused_rank.chunk_id}"
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
        lexical_rank=lexical_hit.rank if lexical_hit is not None else None,
        semantic_rank=semantic_hit.rank if semantic_hit is not None else None,
    )
