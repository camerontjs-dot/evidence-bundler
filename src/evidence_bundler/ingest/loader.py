"""Load raw source documents from a verified C-A scaffold-run."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

from evidence_bundler.contracts.hashing import hash_file
from evidence_bundler.contracts.intake import (
    IntakeResult,
    ScaffoldRunArtifact,
    SourceArtifact,
    verify_intake,
)
from evidence_bundler.contracts.yaml_io import load_yaml
from evidence_bundler.ingest.pdf_extractor import PDFExtractionError, PDFExtractor
from evidence_bundler.models.document import SourceDocument

CONTENT_TYPES = {
    ".md": "markdown",
    ".txt": "text",
    ".pdf": "pdf",
}


class SourceDocumentLoadError(Exception):
    """Base error raised when source documents cannot be loaded."""


class SourceDocumentIntakeError(SourceDocumentLoadError):
    """Raised when C-A intake verification fails before loading."""

    def __init__(self, result: IntakeResult) -> None:
        self.result = result
        message = "; ".join(result.errors) or "C-A intake verification failed"
        super().__init__(message)


class UnsupportedContentTypeError(SourceDocumentLoadError):
    """Raised when a C-A source uses a format outside this unit's loader scope."""

    def __init__(self, source_id: str, content_path: Path) -> None:
        self.source_id = source_id
        self.content_path = content_path
        super().__init__(
            f"Unsupported content file for {source_id}: {content_path.name}. "
            "Phase 1 ingest supports content.md, content.txt, and content.pdf."
        )


def load_source_documents(
    scaffold_run_dir_or_artifact: Path | ScaffoldRunArtifact,
    *,
    pdf_extractor: PDFExtractor | None = None,
) -> list[SourceDocument]:
    """Return deterministic SourceDocument records for supported C-A source files."""
    if isinstance(scaffold_run_dir_or_artifact, ScaffoldRunArtifact):
        artifact = scaffold_run_dir_or_artifact
    else:
        intake = verify_intake(scaffold_run_dir_or_artifact)
        if not intake.valid or intake.artifact is None:
            raise SourceDocumentIntakeError(intake)
        artifact = intake.artifact

    documents: list[SourceDocument] = []
    extractor = pdf_extractor or PDFExtractor()
    for source_id in sorted(artifact.sources):
        source = artifact.sources[source_id]
        documents.append(_load_source_document(source, pdf_extractor=extractor))
    return documents


def _load_source_document(
    source: SourceArtifact,
    *,
    pdf_extractor: PDFExtractor,
) -> SourceDocument:
    content_type = CONTENT_TYPES.get(source.content_path.suffix)
    if content_type is None:
        raise UnsupportedContentTypeError(source.source_id, source.content_path)

    if content_type == "pdf":
        try:
            raw_text = pdf_extractor.extract(source.content_path)
        except PDFExtractionError as exc:
            raise SourceDocumentLoadError(
                f"Source {source.source_id} PDF extraction failed: {exc.reason}"
            ) from exc
    else:
        raw_bytes = source.content_path.read_bytes()
        try:
            raw_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourceDocumentLoadError(
                f"Source {source.source_id} is not valid UTF-8 text: {source.content_path}"
            ) from exc

    metadata = load_yaml(source.source_dir / "metadata.yaml")
    passages = load_yaml(source.source_dir / "passages.yaml")

    return SourceDocument(
        source_id=source.source_id,
        content_path=source.content_path,
        content_type=cast(Literal["markdown", "text", "pdf"], content_type),
        raw_text=raw_text,
        content_hash=hash_file(source.content_path),
        metadata=metadata,
        passages=passages,
        title=_title_from_metadata(metadata),
    )


def _title_from_metadata(metadata: dict[str, Any]) -> str | None:
    bibliographic = metadata.get("bibliographic")
    if not isinstance(bibliographic, dict):
        return None
    title = bibliographic.get("title")
    return title if isinstance(title, str) else None
