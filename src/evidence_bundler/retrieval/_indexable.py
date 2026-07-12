"""Shared chunk selection for retrieval indexes."""

from __future__ import annotations

from evidence_bundler.models.document import DocumentChunk


def select_indexable_chunks(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    """Return child/leaf chunks indexed by retrieval methods.

    Parent chunks provide audit-facing context, while child/leaf chunks provide
    retrieval precision. Flat chunks without children are indexed as their own
    context.
    """
    parent_ids = {chunk.parent_chunk_id for chunk in chunks if chunk.parent_chunk_id is not None}
    return [
        chunk
        for chunk in chunks
        if chunk.parent_chunk_id is not None or chunk.chunk_id not in parent_ids
    ]
