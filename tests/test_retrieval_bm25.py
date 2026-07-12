"""BM25 retrieval tests for Phase 2a."""

from __future__ import annotations

from pathlib import Path

from evidence_bundler.contracts.hashing import hash_text
from evidence_bundler.ingest.chunker import chunk_source_document, chunk_source_documents
from evidence_bundler.ingest.loader import load_source_documents
from evidence_bundler.models.document import DocumentChunk, SourceDocument
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever, tokenize


def test_tokenizer_is_lowercase_and_deterministic() -> None:
    assert tokenize("ICH Q10, Batch-Release!") == ["ich", "q10", "batch", "release"]
    assert tokenize("ICH Q10, Batch-Release!") == tokenize("ich q10 batch release")


def test_bm25_indexes_child_chunks_not_markdown_parents(mixed_scaffold_run_tmp: Path) -> None:
    chunks = chunk_source_documents(load_source_documents(mixed_scaffold_run_tmp))
    retriever = BM25Retriever(chunks)
    indexed_ids = {chunk.chunk_id for chunk in retriever.indexed_chunks}
    parent_ids = {chunk.parent_chunk_id for chunk in chunks if chunk.parent_chunk_id is not None}

    assert retriever.indexed_chunks
    assert indexed_ids.isdisjoint(parent_ids)
    assert any(chunk.parent_chunk_id is not None for chunk in retriever.indexed_chunks)


def test_flat_text_chunks_are_indexed_as_their_own_context(mixed_scaffold_run_tmp: Path) -> None:
    chunks = chunk_source_documents(load_source_documents(mixed_scaffold_run_tmp))
    
    # A plain text file without numeric section headings
    raw_text = (
        "First paragraph has unique-needle-word downstream chunking.\n\n"
        "Second paragraph remains flat."
    )
    flat_document = SourceDocument(
        source_id="flat-txt",
        content_path=Path("flat.txt"),
        content_type="text",
        raw_text=raw_text,
        content_hash=hash_text(raw_text),
        metadata={},
        passages={},
        title="Flat Text Fixture",
    )
    flat_chunks = chunk_source_document(flat_document)
    all_chunks = chunks + flat_chunks
    retriever = BM25Retriever(all_chunks)

    hits = retriever.query("unique-needle-word downstream chunking", top_k=5)

    assert hits
    assert hits[0].chunk.source_id == "flat-txt"
    assert hits[0].chunk.parent_chunk_id is None


def test_bm25_ranking_is_deterministic(mixed_scaffold_run_tmp: Path) -> None:
    chunks = chunk_source_documents(load_source_documents(mixed_scaffold_run_tmp))
    retriever = BM25Retriever(chunks)

    first = retriever.query("submission checklist final audit review", top_k=5)
    second = retriever.query("submission checklist final audit review", top_k=5)

    assert [(hit.chunk.chunk_id, hit.score) for hit in first] == [
        (hit.chunk.chunk_id, hit.score) for hit in second
    ]


def test_empty_and_zero_overlap_queries_return_no_candidates() -> None:
    retriever = BM25Retriever(
        [
            _chunk(
                chunk_id="flat-001",
                text="Submission checklist and audit packet controls.",
                start=0,
                end=47,
            )
        ]
    )

    assert retriever.query("") == []
    assert retriever.query("zzzz qqqq xxxx") == []


def _chunk(
    *,
    chunk_id: str,
    text: str,
    start: int,
    end: int,
    parent_chunk_id: str | None = None,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        source_id="src-test",
        source_path=Path("content.md"),
        title="Test",
        chunk_level="paragraph",
        parent_chunk_id=parent_chunk_id,
        heading_path=[],
        section_tag=None,
        char_start=start,
        char_end=end,
        chunk_hash=hash_text(text),
        excerpt=text,
        text=text,
    )
