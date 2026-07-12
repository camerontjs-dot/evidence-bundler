"""Hybrid retrieval fusion over child/leaf rankings."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf


@dataclass(frozen=True)
class FusedChunkRank:
    """A child/leaf chunk rank after Reciprocal Rank Fusion."""

    chunk_id: str
    fusion_score: float
    rank: int
    source_ranks: tuple[int | None, ...]

    @property
    def lexical_rank(self) -> int | None:
        """Rank from the first ranking list, conventionally BM25."""
        return self.source_ranks[0] if self.source_ranks else None

    @property
    def semantic_rank(self) -> int | None:
        """Rank from the second ranking list, conventionally semantic retrieval."""
        return self.source_ranks[1] if len(self.source_ranks) > 1 else None


def reciprocal_rank_fusion(
    rankings: list[list[str]],
    *,
    k: int = 60,
) -> list[FusedChunkRank]:
    """Fuse ranked child/leaf chunk ids without normalizing retriever scores."""
    if k <= 0:
        raise ValueError("RRF k constant must be greater than zero")

    scores: dict[str, float] = {}
    ranks_by_chunk: dict[str, list[int | None]] = {}
    source_count = len(rankings)

    for source_index, ranked_chunk_ids in enumerate(rankings):
        seen_in_source: set[str] = set()
        for source_rank, chunk_id in enumerate(ranked_chunk_ids, start=1):
            if chunk_id in seen_in_source:
                continue
            seen_in_source.add(chunk_id)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + source_rank)
            ranks = ranks_by_chunk.setdefault(chunk_id, [None] * source_count)
            ranks[source_index] = source_rank

    sorted_chunk_ids = sorted(
        scores,
        key=lambda chunk_id: (
            -scores[chunk_id],
            tuple(_rank_sort_value(rank) for rank in ranks_by_chunk[chunk_id]),
            chunk_id,
        ),
    )
    return [
        FusedChunkRank(
            chunk_id=chunk_id,
            fusion_score=scores[chunk_id],
            rank=rank,
            source_ranks=tuple(ranks_by_chunk[chunk_id]),
        )
        for rank, chunk_id in enumerate(sorted_chunk_ids, start=1)
    ]


def _rank_sort_value(rank: int | None) -> float:
    return inf if rank is None else float(rank)
