"""Deterministic lexical retrieval used by the Evidence Bundler V1 candidate."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.retrieval._indexable import select_indexable_chunks

TOKEN_RE = re.compile(r"\w+")
ENGINE_ID = "evidence_bundler_okapi_bm25_v1"
TOKENIZER_ID = "lowercase_word_v1"
BM25_K1 = 1.5
BM25_B = 0.75


@dataclass(frozen=True)
class RankedChunk:
    """One deterministic nomination from the V1 retriever."""

    chunk: DocumentChunk
    score: float
    rank: int


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def query_bm25(
    query: str,
    chunks: list[DocumentChunk],
    *,
    top_k: int,
) -> list[RankedChunk]:
    """Rank positive-score child/leaf chunks with pinned Okapi BM25 math.

    Scores are used only to order nominations.  They are intentionally not
    emitted in the V1 evidence package, where rank and stage transitions are
    the durable evidence-world facts.
    """
    if top_k < 1:
        raise ValueError("top_k must be >= 1")
    indexed = select_indexable_chunks(chunks)
    documents = [tokenize(chunk.text) for chunk in indexed]
    if not documents:
        return []
    query_terms = tokenize(query)
    if not query_terms:
        return []

    document_count = len(documents)
    average_length = sum(len(document) for document in documents) / document_count
    document_frequency: Counter[str] = Counter()
    for document in documents:
        document_frequency.update(set(document))

    scored: list[tuple[float, DocumentChunk]] = []
    for document, chunk in zip(documents, indexed, strict=True):
        term_frequency = Counter(document)
        document_length = len(document)
        score = 0.0
        for term in query_terms:
            frequency = term_frequency.get(term, 0)
            if frequency == 0:
                continue
            df = document_frequency[term]
            idf = math.log(1.0 + (document_count - df + 0.5) / (df + 0.5))
            denominator = frequency + BM25_K1 * (
                1.0 - BM25_B + BM25_B * document_length / average_length
            )
            score += idf * frequency * (BM25_K1 + 1.0) / denominator
        if score > 0.0:
            scored.append((score, chunk))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1].source_id,
            item[1].char_start,
            item[1].chunk_id,
        )
    )
    return [
        RankedChunk(chunk=chunk, score=score, rank=index)
        for index, (score, chunk) in enumerate(scored[:top_k], start=1)
    ]
