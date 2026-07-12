"""BM25 lexical retrieval over child/leaf chunks."""

import heapq
import re

from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]

from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.retrieval._indexable import select_indexable_chunks
from evidence_bundler.retrieval.hits import ChunkSearchHit

TOKEN_RE = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokenizer. Fast, deterministic, and dependency-light."""
    return TOKEN_RE.findall(text.lower())


class BM25Retriever:
    """Thin deterministic wrapper around BM25Okapi."""

    def __init__(self, chunks: list[DocumentChunk]) -> None:
        self.chunks = list(chunks)
        self.chunks_by_id = {chunk.chunk_id: chunk for chunk in self.chunks}
        self.indexed_chunks = select_indexable_chunks(self.chunks)
        self._corpus_tokens = [tokenize(chunk.text) for chunk in self.indexed_chunks]
        self._bm25 = BM25Okapi(self._corpus_tokens) if self.indexed_chunks else None

    def query(
        self,
        query_text: str,
        *,
        top_k: int = 20,
        score_floor: float = 0.0,
    ) -> list[ChunkSearchHit]:
        """Return positive-score child/leaf hits sorted by descending BM25 score."""
        query_tokens = tokenize(query_text)
        if not query_tokens or self._bm25 is None:
            return []

        scores = self._bm25.get_scores(query_tokens)
        candidate_indices = [
            i for i, score in enumerate(scores) if float(score) > score_floor
        ]
        best_indices = heapq.nsmallest(
            top_k,
            candidate_indices,
            key=lambda index: (
                -float(scores[index]),
                self.indexed_chunks[index].char_start,
                self.indexed_chunks[index].chunk_id,
            ),
        )

        hits: list[ChunkSearchHit] = []
        for index in best_indices:
            score = float(scores[index])
            hits.append(
                ChunkSearchHit(
                    chunk=self.indexed_chunks[index],
                    score=score,
                    rank=len(hits) + 1,
                    lexical_score=score,
                    lexical_rank=len(hits) + 1,
                )
            )
        return hits
