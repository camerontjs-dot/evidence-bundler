"""In-memory document models for ingest."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from evidence_bundler.models.common import HashValue, NonBlankStr

ChunkLevel = Literal["document", "section", "subsection", "paragraph", "clause"]
IngestStatus = Literal["new", "changed", "unchanged", "removed"]


class SourceDocument(BaseModel):
    """Raw loaded source content from a C-A scaffold-run corpus."""

    model_config = ConfigDict(extra="forbid")

    source_id: NonBlankStr
    content_path: Path
    content_type: Literal["markdown", "text", "pdf"]
    raw_text: str
    content_hash: HashValue
    metadata: dict[str, Any]
    passages: dict[str, Any]
    title: str | None = None


class ChunkSpec(BaseModel):
    """Configuration for deterministic Markdown/text chunking."""

    model_config = ConfigDict(extra="forbid")

    max_chars: int = Field(default=1800, gt=0)
    overlap_chars: int = Field(default=80, ge=0)

    @model_validator(mode="after")
    def validate_overlap(self) -> ChunkSpec:
        """Keep recursive splitting from stalling."""
        if self.overlap_chars >= self.max_chars:
            raise ValueError("overlap_chars must be smaller than max_chars")
        return self


class DocumentChunk(BaseModel):
    """Traceable text segment produced from a loaded SourceDocument."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: NonBlankStr
    source_id: NonBlankStr
    source_path: Path
    title: str | None = None
    chunk_level: ChunkLevel
    parent_chunk_id: str | None = None
    heading_path: list[str] = Field(default_factory=list)
    section_tag: str | None = None
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    chunk_hash: HashValue
    excerpt: str
    text: str

    @model_validator(mode="after")
    def validate_offsets_and_text(self) -> DocumentChunk:
        """Reject empty chunks and inverted source spans."""
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        if not self.text.strip():
            raise ValueError("DocumentChunk text must not be empty")
        return self


class IngestDocumentStatus(BaseModel):
    """Per-source outcome from one incremental ingest run."""

    model_config = ConfigDict(extra="forbid")

    source_id: NonBlankStr
    content_hash: HashValue
    status: IngestStatus
    chunks_emitted: int = Field(ge=0)
    previous_content_hash: HashValue | None = None
    coverage_chars: int | None = None
    uncovered_chars: int | None = None


class IngestReport(BaseModel):
    """Summary of a single loader/chunker ingest run."""

    model_config = ConfigDict(extra="forbid")

    scaffold_run_dir: Path
    documents_loaded: int = Field(ge=0)
    documents_chunked: int = Field(ge=0)
    documents_skipped: int = Field(ge=0)
    documents_removed: int = Field(ge=0)
    chunks_emitted: int = Field(ge=0)
    dry_run: bool
    state_path: Path | None = None
    statuses: list[IngestDocumentStatus] = Field(default_factory=list)
