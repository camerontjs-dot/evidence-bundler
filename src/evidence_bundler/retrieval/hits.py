"""Shared retrieval hit objects."""

from __future__ import annotations

from dataclasses import dataclass

from evidence_bundler.models.document import DocumentChunk


@dataclass(frozen=True)
class ChunkSearchHit:
    """A ranked child/leaf chunk returned by a retrieval method."""

    chunk: DocumentChunk
    score: float
    rank: int
    lexical_score: float | None = None
    semantic_score: float | None = None
    fusion_score: float | None = None
    lexical_rank: int | None = None
    semantic_rank: int | None = None
