"""PDF extraction tests for Phase 1 Unit 3."""

from __future__ import annotations

from pathlib import Path

import pytest

from evidence_bundler.contracts.hashing import hash_file
from evidence_bundler.ingest.chunker import chunk_source_document
from evidence_bundler.ingest.loader import SourceDocumentLoadError, load_source_documents
from evidence_bundler.ingest.pdf_extractor import PDFExtractionError, PDFExtractor
from evidence_bundler.models.document import SourceDocument


def test_pdfminer_extracts_synthetic_pdf_text(mixed_scaffold_run_dir: Path) -> None:
    pdf_path = mixed_scaffold_run_dir / "corpus" / "src-pdf" / "content.pdf"

    text = PDFExtractor(backend="pdfminer").extract(pdf_path)

    assert "4.3 PDF Extraction Controls" in text
    assert "PDF extraction should preserve source text for downstream chunking." in text


def test_auto_backend_falls_back_to_pypdf_when_pdfminer_returns_empty(
    mixed_scaffold_run_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = mixed_scaffold_run_dir / "corpus" / "src-pdf" / "content.pdf"
    extractor = PDFExtractor()

    monkeypatch.setattr(extractor, "_extract_pdfminer", lambda path: "")
    monkeypatch.setattr(extractor, "_extract_pypdf", lambda path: "fallback text")

    assert extractor.extract(pdf_path) == "fallback text"


def test_pdf_extractor_classifies_empty_text_failure(
    mixed_scaffold_run_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = mixed_scaffold_run_dir / "corpus" / "src-pdf" / "content.pdf"
    extractor = PDFExtractor()

    monkeypatch.setattr(extractor, "_extract_pdfminer", lambda path: "")
    monkeypatch.setattr(extractor, "_extract_pypdf", lambda path: "")

    with pytest.raises(PDFExtractionError) as exc_info:
        extractor.extract(pdf_path)

    assert exc_info.value.reason == "empty_text"
    assert [(attempt.backend, attempt.status) for attempt in exc_info.value.attempts] == [
        ("pdfminer", "empty"),
        ("pypdf", "empty"),
    ]


def test_pdf_extractor_classifies_backend_error(
    mixed_scaffold_run_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = mixed_scaffold_run_dir / "corpus" / "src-pdf" / "content.pdf"
    extractor = PDFExtractor()

    def fail(_path: Path) -> str:
        raise ValueError("synthetic parser failure")

    monkeypatch.setattr(extractor, "_extract_pdfminer", fail)
    monkeypatch.setattr(extractor, "_extract_pypdf", fail)

    with pytest.raises(PDFExtractionError) as exc_info:
        extractor.extract(pdf_path)

    assert exc_info.value.reason == "extractor_error"
    assert [attempt.status for attempt in exc_info.value.attempts] == ["error", "error"]


def test_loader_emits_pdf_source_document(mixed_scaffold_run_tmp: Path) -> None:
    documents = _documents_by_source(mixed_scaffold_run_tmp)
    pdf = documents["src-pdf"]
    content_path = mixed_scaffold_run_tmp / "corpus" / "src-pdf" / "content.pdf"

    assert pdf.content_type == "pdf"
    assert pdf.content_path == content_path.resolve()
    assert pdf.content_hash == hash_file(content_path)
    assert pdf.title == "Synthetic PDF Extraction Fixture"
    assert "PDF extraction should preserve source text for downstream chunking." in pdf.raw_text


def test_loader_wraps_pdf_extraction_failure(
    mixed_scaffold_run_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extractor = PDFExtractor()
    monkeypatch.setattr(extractor, "_extract_pdfminer", lambda path: "")
    monkeypatch.setattr(extractor, "_extract_pypdf", lambda path: "")

    with pytest.raises(SourceDocumentLoadError) as exc_info:
        load_source_documents(mixed_scaffold_run_tmp, pdf_extractor=extractor)

    assert "src-pdf PDF extraction failed: empty_text" in str(exc_info.value)


def test_pdf_source_chunks_hierarchically(mixed_scaffold_run_tmp: Path) -> None:
    pdf = _documents_by_source(mixed_scaffold_run_tmp)["src-pdf"]

    chunks = chunk_source_document(pdf)

    assert chunks
    parents = [c for c in chunks if c.parent_chunk_id is None]
    children = [c for c in chunks if c.parent_chunk_id is not None]

    assert len(parents) == 1
    assert len(children) >= 1
    assert parents[0].chunk_level == "subsection"  # 4.3 -> level 2 -> subsection
    assert parents[0].heading_path == ["4.3 PDF Extraction Controls"]
    assert parents[0].section_tag == "4.3"

    assert all(child.parent_chunk_id == parents[0].chunk_id for child in children)
    assert all(child.heading_path == ["4.3 PDF Extraction Controls"] for child in children)
    assert all(child.section_tag == "4.3" for child in children)
    assert any(
        "PDF extraction should preserve source text for downstream chunking." in chunk.text
        for chunk in children
    )


def _documents_by_source(scaffold_run_dir: Path) -> dict[str, SourceDocument]:
    return {document.source_id: document for document in load_source_documents(scaffold_run_dir)}
