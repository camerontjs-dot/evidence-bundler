"""Aggregate child retrieval hits to parent evidence contexts."""

from __future__ import annotations

from evidence_bundler.models.ca import ScaffoldClaim
from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.models.retrieval import CandidateEvidence, RetrievalConfig
from evidence_bundler.retrieval.hits import ChunkSearchHit


def aggregate_parent_candidates(
    *,
    claim: ScaffoldClaim,
    hits: list[ChunkSearchHit],
    chunks_by_id: dict[str, DocumentChunk],
    config: RetrievalConfig,
    limit: int | None = None,
) -> list[CandidateEvidence]:
    """Collapse child hits to parent chunks using the configured aggregation rule."""
    if config.parent_aggregation != "max":
        raise ValueError(f"Unsupported parent aggregation: {config.parent_aggregation}")
    candidate_limit = limit if limit is not None else config.top_k
    if candidate_limit <= 0:
        raise ValueError("Parent candidate limit must be greater than zero")

    best_by_parent: dict[str, ChunkSearchHit] = {}
    for hit in hits:
        parent_id = hit.chunk.parent_chunk_id or hit.chunk.chunk_id
        current = best_by_parent.get(parent_id)
        if current is None or _is_better_child_hit(hit, current):
            best_by_parent[parent_id] = hit

    ranked_parent_ids = sorted(
        best_by_parent,
        key=lambda parent_id: (
            -best_by_parent[parent_id].score,
            best_by_parent[parent_id].rank,
            _parent_chunk(parent_id, best_by_parent[parent_id], chunks_by_id).char_start,
            parent_id,
        ),
    )

    candidates: list[CandidateEvidence] = []
    for parent_id in ranked_parent_ids[:candidate_limit]:
        hit = best_by_parent[parent_id]
        parent = _parent_chunk(parent_id, hit, chunks_by_id)
        candidates.append(
            CandidateEvidence(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                parent_chunk=parent,
                matched_child_chunk=hit.chunk,
                child_rank=hit.rank,
                lexical_score=_lexical_score(hit, config),
                semantic_score=hit.semantic_score,
                fusion_score=hit.fusion_score,
                retrieval_method=config.retrieval_method,
                evidence_role="supporting",
            )
        )
    return candidates


def _lexical_score(hit: ChunkSearchHit, config: RetrievalConfig) -> float | None:
    if hit.lexical_score is not None:
        return hit.lexical_score
    if config.retrieval_method == "bm25":
        return hit.score
    return None


def _is_better_child_hit(
    candidate: ChunkSearchHit,
    current: ChunkSearchHit,
) -> bool:
    if candidate.score != current.score:
        return candidate.score > current.score
    if candidate.rank != current.rank:
        return candidate.rank < current.rank
    if candidate.chunk.char_start != current.chunk.char_start:
        return candidate.chunk.char_start < current.chunk.char_start
    return candidate.chunk.chunk_id < current.chunk.chunk_id


def _parent_chunk(
    parent_id: str,
    hit: ChunkSearchHit,
    chunks_by_id: dict[str, DocumentChunk],
) -> DocumentChunk:
    return chunks_by_id.get(parent_id, hit.chunk)
