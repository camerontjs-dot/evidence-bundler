"""DocumentChunk tests for Phase 1 Unit 2."""

from __future__ import annotations

from pathlib import Path

from evidence_bundler.contracts.hashing import hash_text
from evidence_bundler.ingest.chunker import chunk_source_document, chunk_source_documents
from evidence_bundler.ingest.loader import load_source_documents
from evidence_bundler.models.document import ChunkSpec, DocumentChunk, SourceDocument


def test_chunker_emits_no_empty_chunks(mixed_scaffold_run_tmp: Path) -> None:
    documents = _documents_by_source(mixed_scaffold_run_tmp)
    chunks = _chunks_from_fixture(mixed_scaffold_run_tmp)

    assert chunks
    assert all(chunk.text.strip() for chunk in chunks)
    assert all(
        chunk.text == documents[chunk.source_id].raw_text[chunk.char_start : chunk.char_end]
        for chunk in chunks
    )
    assert {chunk.source_id for chunk in chunks} == {"src-md", "src-pdf", "src-txt"}


def test_chunk_ids_and_hashes_are_deterministic(mixed_scaffold_run_tmp: Path) -> None:
    documents = load_source_documents(mixed_scaffold_run_tmp)

    first = chunk_source_documents(documents)
    second = chunk_source_documents(documents)

    assert [(chunk.chunk_id, chunk.chunk_hash) for chunk in first] == [
        (chunk.chunk_id, chunk.chunk_hash) for chunk in second
    ]
    assert all(chunk.chunk_hash == hash_text(chunk.text) for chunk in first)


def test_parent_child_integrity_has_no_dangling_parent_ids(
    mixed_scaffold_run_tmp: Path,
) -> None:
    chunks = _chunks_from_fixture(mixed_scaffold_run_tmp)
    chunk_ids = {chunk.chunk_id for chunk in chunks}

    assert all(
        chunk.parent_chunk_id is None or chunk.parent_chunk_id in chunk_ids for chunk in chunks
    )


def test_chunk_levels_are_valid(mixed_scaffold_run_tmp: Path) -> None:
    valid_levels = {"document", "section", "subsection", "paragraph", "clause"}

    chunk_levels = {chunk.chunk_level for chunk in _chunks_from_fixture(mixed_scaffold_run_tmp)}

    assert chunk_levels <= valid_levels


def test_markdown_heading_path_is_preserved(mixed_scaffold_run_tmp: Path) -> None:
    markdown_chunks = _chunks_by_source(mixed_scaffold_run_tmp)["src-md"]

    sponsor_chunk = _find_chunk(markdown_chunks, "The sponsor should retain")
    batch_chunk = _find_chunk(markdown_chunks, "Batch release records should preserve")

    assert sponsor_chunk.heading_path == ["Markdown Source", "Methods"]
    assert batch_chunk.heading_path == [
        "Markdown Source",
        "Results",
        "4.2.1 Batch Release Records",
    ]


def test_section_tags_cover_numeric_and_imrad_headings(mixed_scaffold_run_tmp: Path) -> None:
    by_source = _chunks_by_source(mixed_scaffold_run_tmp)

    method_parent = _find_chunk(by_source["src-md"], "## Methods")
    numeric_parent = _find_chunk(by_source["src-md"], "### 4.2.1 Batch Release Records")
    text_chunk = _find_chunk(by_source["src-txt"], "4.2.1 Plain Text Controls")

    assert method_parent.section_tag == "Methods"
    assert numeric_parent.section_tag == "4.2.1"
    assert text_chunk.section_tag == "4.2.1"


def test_markdown_pipe_table_stays_intact(mixed_scaffold_run_tmp: Path) -> None:
    markdown_chunks = _chunks_by_source(mixed_scaffold_run_tmp)["src-md"]

    table_chunk = _find_chunk(
        [chunk for chunk in markdown_chunks if chunk.parent_chunk_id is not None],
        "| Step | Owner | Record |",
    )

    assert table_chunk.parent_chunk_id is not None
    assert table_chunk.text == (
        "| Step | Owner | Record |\n"
        "| --- | --- | --- |\n"
        "| Intake | QA | Submission checklist |\n"
        "| Audit review | QA lead | Final memo |"
    )


def test_plain_text_uses_flat_fallback() -> None:
    # A plain text file without any numeric headings should fall back to flat chunking
    raw_text = (
        "This is paragraph one.\n\n"
        "This is paragraph two."
    )
    document = SourceDocument(
        source_id="flat-txt",
        content_path=Path("flat.txt"),
        content_type="text",
        raw_text=raw_text,
        content_hash=hash_text(raw_text),
        metadata={},
        passages={},
        title="Flat Plain Text",
    )
    chunks = chunk_source_document(document)
    assert chunks
    assert all(chunk.parent_chunk_id is None for chunk in chunks)
    assert all(chunk.heading_path == [] for chunk in chunks)


def test_plain_text_with_numeric_headings_creates_hierarchy(mixed_scaffold_run_tmp: Path) -> None:
    text_chunks = _chunks_by_source(mixed_scaffold_run_tmp)["src-txt"]

    assert text_chunks
    # Since src-txt has "4.2.1 Plain Text Controls", it should have parent and child chunks!
    parents = [c for c in text_chunks if c.parent_chunk_id is None]
    children = [c for c in text_chunks if c.parent_chunk_id is not None]

    assert len(parents) == 1
    assert len(children) >= 1
    assert parents[0].chunk_level == "paragraph"  # level 3 -> paragraph
    assert parents[0].heading_path == ["4.2.1 Plain Text Controls"]
    assert parents[0].section_tag == "4.2.1"
    
    assert all(child.parent_chunk_id == parents[0].chunk_id for child in children)
    assert all(child.heading_path == ["4.2.1 Plain Text Controls"] for child in children)
    assert all(child.section_tag == "4.2.1" for child in children)


def test_empty_source_returns_no_chunks(mixed_scaffold_run_tmp: Path) -> None:
    documents = _documents_by_source(mixed_scaffold_run_tmp)

    assert chunk_source_document(documents["src-empty"]) == []


def test_recursive_fallback_preserves_source_spans() -> None:
    raw_text = (
        "First paragraph records the claim boundary.\n\n"
        "Second paragraph is deliberately long enough to force the recursive splitter "
        "to emit more than one chunk when the test uses a small chunk size.\n\n"
        "Third paragraph stays traceable to the original raw text."
    )
    document = SourceDocument(
        source_id="synthetic-text",
        content_path=Path("synthetic.txt"),
        content_type="text",
        raw_text=raw_text,
        content_hash=hash_text(raw_text),
        metadata={},
        passages={},
        title="Synthetic Recursive Split Fixture",
    )

    chunks = chunk_source_document(document, ChunkSpec(max_chars=90, overlap_chars=10))

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.text == raw_text[chunk.char_start : chunk.char_end]


def _documents_by_source(scaffold_run_dir: Path) -> dict[str, SourceDocument]:
    return {document.source_id: document for document in load_source_documents(scaffold_run_dir)}


def _chunks_from_fixture(scaffold_run_dir: Path) -> list[DocumentChunk]:
    return chunk_source_documents(load_source_documents(scaffold_run_dir))


def _chunks_by_source(scaffold_run_dir: Path) -> dict[str, list[DocumentChunk]]:
    chunks_by_source: dict[str, list[DocumentChunk]] = {}
    for chunk in _chunks_from_fixture(scaffold_run_dir):
        chunks_by_source.setdefault(chunk.source_id, []).append(chunk)
    return chunks_by_source


def test_markdown_preamble_coverage() -> None:
    raw_text = (
        "This is preamble text that is stating a fact about the sponsor.\n"
        "It has two paragraphs.\n\n"
        "And another paragraph.\n"
        "# Markdown Source\n\n"
        "## Methods\n\n"
        "The sponsor should retain the checklist."
    )
    document = SourceDocument(
        source_id="synthetic-preamble",
        content_path=Path("synthetic_preamble.md"),
        content_type="markdown",
        raw_text=raw_text,
        content_hash=hash_text(raw_text),
        metadata={},
        passages={},
        title="Preamble Title",
    )
    chunks = chunk_source_document(document)

    # We should have a parent chunk for the preamble!
    preamble_parents = [c for c in chunks if c.parent_chunk_id is None and c.heading_path == []]
    assert len(preamble_parents) == 1
    preamble_parent = preamble_parents[0]
    assert preamble_parent.chunk_level == "section"
    assert "This is preamble text" in preamble_parent.text

    # We should have child chunks under this parent!
    preamble_children = [c for c in chunks if c.parent_chunk_id == preamble_parent.chunk_id]
    assert len(preamble_children) >= 1
    assert any("It has two paragraphs" in c.text for c in preamble_children)


def test_markdown_fenced_code_blocks_masked() -> None:
    raw_text = (
        "# Main Heading\n\n"
        "```python\n"
        "# This is a comment inside code block\n"
        "print('hello')\n"
        "```\n\n"
        "## Real Subheading\n"
        "Normal text."
    )
    document = SourceDocument(
        source_id="synthetic-code",
        content_path=Path("synthetic_code.md"),
        content_type="markdown",
        raw_text=raw_text,
        content_hash=hash_text(raw_text),
        metadata={},
        passages={},
        title="Code Title",
    )
    chunks = chunk_source_document(document)

    # Headings (in heading_path) should NOT contain the comment
    assert not any("comment" in part for c in chunks for part in c.heading_path)


def _find_chunk(chunks: list[DocumentChunk], text: str) -> DocumentChunk:
    return next(chunk for chunk in chunks if text in chunk.text)
