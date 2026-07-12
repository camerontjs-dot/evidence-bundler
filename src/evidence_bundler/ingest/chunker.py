"""Chunk loaded Markdown and plain-text source documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from evidence_bundler.contracts.hashing import hash_text, strip_hash_prefix
from evidence_bundler.models.document import ChunkLevel, ChunkSpec, DocumentChunk, SourceDocument

HEADER_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t#]*$", re.MULTILINE)
NUMERIC_SECTION_RE = re.compile(r"^\s*((?:\d+\.)*\d+)\b")
NUMERIC_HEADING_RE = re.compile(
    r"^\s*((?:\d+\.)+\d*)(?:\s+|\r?\n)([A-Z][A-Za-z0-9 ,'\-&()]+)$",
    re.MULTILINE
)
IMRAD_TAGS = {
    "abstract": "Abstract",
    "introduction": "Introduction",
    "background": "Background",
    "methods": "Methods",
    "method": "Methods",
    "materials and methods": "Methods",
    "results": "Results",
    "discussion": "Discussion",
    "conclusion": "Conclusion",
    "conclusions": "Conclusion",
    "limitations": "Limitations",
}
SEPARATORS = ("\n\n", "\n", ". ", " ", "")
EXCERPT_CHARS = 240


@dataclass(frozen=True)
class TextSpan:
    """Absolute character span inside one SourceDocument.raw_text."""

    start: int
    end: int
    text: str


@dataclass(frozen=True)
class MarkdownSection:
    """Markdown heading block with absolute source offsets."""

    heading_level: int
    heading: str
    heading_path: list[str]
    section_tag: str | None
    start: int
    body_start: int
    end: int


@dataclass(frozen=True)
class NumericSection:
    """Numeric section heading block with absolute source offsets."""

    heading_level: int
    heading: str
    heading_path: list[str]
    section_tag: str | None
    start: int
    body_start: int
    end: int


def chunk_source_documents(
    documents: list[SourceDocument],
    spec: ChunkSpec | None = None,
) -> list[DocumentChunk]:
    """Chunk loaded documents in their existing deterministic order."""
    chunk_spec = spec or ChunkSpec()
    chunks: list[DocumentChunk] = []
    for document in documents:
        chunks.extend(chunk_source_document(document, chunk_spec))
    return chunks


def chunk_source_document(
    document: SourceDocument,
    spec: ChunkSpec | None = None,
) -> list[DocumentChunk]:
    """Chunk one SourceDocument into traceable in-memory DocumentChunk records."""
    chunk_spec = spec or ChunkSpec()
    if not document.raw_text.strip():
        return []
    if document.content_type == "markdown":
        return _chunk_markdown(document, chunk_spec)
    return _chunk_plain_text(document, chunk_spec)


def _chunk_markdown(document: SourceDocument, spec: ChunkSpec) -> list[DocumentChunk]:
    masked_text = _mask_fenced_code_blocks(document.raw_text)
    sections = _parse_markdown_sections(document.raw_text, masked_text)
    if not sections:
        return _chunk_plain_text(document, spec)

    chunks: list[DocumentChunk] = []

    # Handle preamble if present
    first_heading_start = sections[0].start
    if first_heading_start > 0:
        preamble_span = _trim_span(document.raw_text, 0, first_heading_start)
        if preamble_span is not None:
            parent_level: ChunkLevel = "section"
            parent_id = _chunk_id(document.source_id, parent_level, preamble_span, None)
            section_tag = _extract_section_tag(_first_nonblank_line(preamble_span.text))
            
            chunks.append(
                _build_chunk(
                    document=document,
                    chunk_id=parent_id,
                    level=parent_level,
                    span=preamble_span,
                    parent_chunk_id=None,
                    heading_path=[],
                    section_tag=section_tag,
                )
            )

            body_spans = _split_markdown_body(
                document.raw_text,
                start=preamble_span.start,
                end=preamble_span.end,
                spec=spec,
                masked_text=masked_text,
            )
            child_level = _child_level_for_parent(parent_level)
            for span in body_spans:
                chunks.append(
                    _build_chunk(
                        document=document,
                        chunk_id=_chunk_id(document.source_id, child_level, span, parent_id),
                        level=child_level,
                        span=span,
                        parent_chunk_id=parent_id,
                        heading_path=[],
                        section_tag=section_tag,
                    )
                )

    for section in sections:
        parent_span = _trim_span(document.raw_text, section.start, section.end)
        if parent_span is None:
            continue

        parent_level = _header_level_to_chunk_level(section.heading_level)
        parent_id = _chunk_id(document.source_id, parent_level, parent_span, None)
        chunks.append(
            _build_chunk(
                document=document,
                chunk_id=parent_id,
                level=parent_level,
                span=parent_span,
                parent_chunk_id=None,
                heading_path=section.heading_path,
                section_tag=section.section_tag,
            )
        )

        body_spans = _split_markdown_body(
            document.raw_text,
            start=section.body_start,
            end=section.end,
            spec=spec,
            masked_text=masked_text,
        )
        child_level = _child_level_for_parent(parent_level)
        for span in body_spans:
            chunks.append(
                _build_chunk(
                    document=document,
                    chunk_id=_chunk_id(document.source_id, child_level, span, parent_id),
                    level=child_level,
                    span=span,
                    parent_chunk_id=parent_id,
                    heading_path=section.heading_path,
                    section_tag=section.section_tag,
                )
            )
    return chunks


def _chunk_plain_text(document: SourceDocument, spec: ChunkSpec) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    sections = _parse_numeric_sections(document.raw_text)
    if not sections:
        for span in _recursive_split(document.raw_text, 0, len(document.raw_text), spec):
            level: ChunkLevel = "paragraph"
            chunks.append(
                _build_chunk(
                    document=document,
                    chunk_id=_chunk_id(document.source_id, level, span, None),
                    level=level,
                    span=span,
                    parent_chunk_id=None,
                    heading_path=[],
                    section_tag=_extract_section_tag(_first_nonblank_line(span.text)),
                )
            )
        return chunks

    
    # Handle preamble if present
    first_heading_start = sections[0].start
    if first_heading_start > 0:
        preamble_span = _trim_span(document.raw_text, 0, first_heading_start)
        if preamble_span is not None:
            parent_level: ChunkLevel = "section"
            parent_id = _chunk_id(document.source_id, parent_level, preamble_span, None)
            section_tag = _extract_section_tag(_first_nonblank_line(preamble_span.text))
            
            chunks.append(
                _build_chunk(
                    document=document,
                    chunk_id=parent_id,
                    level=parent_level,
                    span=preamble_span,
                    parent_chunk_id=None,
                    heading_path=[],
                    section_tag=section_tag,
                )
            )

            body_spans = _recursive_split(
                document.raw_text,
                start=preamble_span.start,
                end=preamble_span.end,
                spec=spec,
            )
            child_level = _child_level_for_parent(parent_level)
            for span in body_spans:
                chunks.append(
                    _build_chunk(
                        document=document,
                        chunk_id=_chunk_id(document.source_id, child_level, span, parent_id),
                        level=child_level,
                        span=span,
                        parent_chunk_id=parent_id,
                        heading_path=[],
                        section_tag=section_tag,
                    )
                )

    for section in sections:
        parent_span = _trim_span(document.raw_text, section.start, section.end)
        if parent_span is None:
            continue

        parent_level = _header_level_to_chunk_level(section.heading_level)
        parent_id = _chunk_id(document.source_id, parent_level, parent_span, None)
        chunks.append(
            _build_chunk(
                document=document,
                chunk_id=parent_id,
                level=parent_level,
                span=parent_span,
                parent_chunk_id=None,
                heading_path=section.heading_path,
                section_tag=section.section_tag,
            )
        )

        body_spans = _recursive_split(
            document.raw_text,
            start=section.body_start,
            end=section.end,
            spec=spec,
        )
        child_level = _child_level_for_parent(parent_level)
        for span in body_spans:
            chunks.append(
                _build_chunk(
                    document=document,
                    chunk_id=_chunk_id(document.source_id, child_level, span, parent_id),
                    level=child_level,
                    span=span,
                    parent_chunk_id=parent_id,
                    heading_path=section.heading_path,
                    section_tag=section.section_tag,
                )
            )
    return chunks


def _parse_numeric_sections(text: str) -> list[NumericSection]:
    matches = list(NUMERIC_HEADING_RE.finditer(text))
    if not matches:
        return []

    sections: list[NumericSection] = []
    heading_stack: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        prefix = match.group(1).rstrip('.')
        parts = prefix.split('.')
        level = len(parts)

        heading_title = match.group(2).strip()
        heading_str = f"{match.group(1)} {heading_title}"

        body_start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)

        heading_stack = [
            (item_level, item) for item_level, item in heading_stack if item_level < level
        ]
        heading_stack.append((level, heading_str))
        heading_path = [item for _, item in heading_stack]

        sections.append(
            NumericSection(
                heading_level=level,
                heading=heading_str,
                heading_path=heading_path,
                section_tag=_extract_section_tag(heading_str),
                start=match.start(),
                body_start=body_start,
                end=end,
            )
        )
    return sections


def _parse_markdown_sections(text: str, masked_text: str) -> list[MarkdownSection]:
    matches = list(HEADER_RE.finditer(masked_text))
    if not matches:
        return []

    sections: list[MarkdownSection] = []
    heading_stack: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        level = len(match.group(1))
        heading = match.group(2).strip()
        body_start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)

        heading_stack = [
            (item_level, item) for item_level, item in heading_stack if item_level < level
        ]
        heading_stack.append((level, heading))
        heading_path = [item for _, item in heading_stack]

        sections.append(
            MarkdownSection(
                heading_level=level,
                heading=heading,
                heading_path=heading_path,
                section_tag=_extract_section_tag(heading),
                start=match.start(),
                body_start=body_start,
                end=end,
            )
        )
    return sections


def _split_markdown_body(
    text: str,
    *,
    start: int,
    end: int,
    spec: ChunkSpec,
    masked_text: str,
) -> list[TextSpan]:
    spans: list[TextSpan] = []
    for block in _iter_markdown_blocks(text, start, end, masked_text=masked_text):
        if _is_table_block(block.text):
            spans.append(block)
        else:
            spans.extend(_recursive_split(text, block.start, block.end, spec))
    return spans


def _iter_markdown_blocks(text: str, start: int, end: int, masked_text: str) -> list[TextSpan]:
    blocks: list[TextSpan] = []
    line_start = start
    current_text_start: int | None = None
    current_table_start: int | None = None

    while line_start < end:
        line_end = text.find("\n", line_start, end)
        if line_end == -1:
            line_end = end
            next_line_start = end
        else:
            next_line_start = line_end + 1

        line_masked = masked_text[line_start:line_end]
        is_table = _is_pipe_table_line(line_masked)

        if is_table:
            if current_text_start is not None:
                _append_trimmed(blocks, text, current_text_start, line_start)
                current_text_start = None
            if current_table_start is None:
                current_table_start = line_start
        else:
            if current_table_start is not None:
                _append_trimmed(blocks, text, current_table_start, line_start)
                current_table_start = None
            if current_text_start is None and line_masked.strip():
                current_text_start = line_start

        line_start = next_line_start

    if current_table_start is not None:
        _append_trimmed(blocks, text, current_table_start, end)
    if current_text_start is not None:
        _append_trimmed(blocks, text, current_text_start, end)
    return blocks


def _recursive_split(text: str, start: int, end: int, spec: ChunkSpec) -> list[TextSpan]:
    span = _trim_span(text, start, end)
    if span is None:
        return []
    if len(span.text) <= spec.max_chars:
        return [span]
    return _split_with_separator(text, span, spec, separator_index=0)


def _split_with_separator(
    text: str,
    span: TextSpan,
    spec: ChunkSpec,
    *,
    separator_index: int,
) -> list[TextSpan]:
    if len(span.text) <= spec.max_chars:
        return [span]
    separator = SEPARATORS[separator_index]
    if separator == "":
        return _hard_split(text, span, spec)

    parts = _split_span_parts(text, span, separator)
    if len(parts) <= 1:
        return _split_with_separator(text, span, spec, separator_index=separator_index + 1)

    chunks: list[TextSpan] = []
    current_start: int | None = None
    current_end: int | None = None
    for part in parts:
        if len(part.text) > spec.max_chars:
            if current_start is not None and current_end is not None:
                _append_trimmed(chunks, text, current_start, current_end)
                current_start = None
                current_end = None
            chunks.extend(
                _split_with_separator(
                    text,
                    part,
                    spec,
                    separator_index=separator_index + 1,
                )
            )
            continue

        candidate_start = part.start if current_start is None else current_start
        candidate = _trim_span(text, candidate_start, part.end)
        if candidate is not None and len(candidate.text) <= spec.max_chars:
            current_start = candidate.start
            current_end = candidate.end
            continue

        if current_start is not None and current_end is not None:
            finalized = _trim_span(text, current_start, current_end)
            if finalized is not None:
                chunks.append(finalized)
            overlap_start = _overlap_start(finalized, part, spec) if finalized else part.start
            current_start = overlap_start
            current_end = part.end
        else:
            current_start = part.start
            current_end = part.end

    if current_start is not None and current_end is not None:
        _append_trimmed(chunks, text, current_start, current_end)
    return chunks


def _split_span_parts(text: str, span: TextSpan, separator: str) -> list[TextSpan]:
    parts: list[TextSpan] = []
    search_from = span.start
    while search_from < span.end:
        found = text.find(separator, search_from, span.end)
        if found == -1:
            _append_trimmed(parts, text, search_from, span.end)
            break
        part_end = found + 1 if separator == ". " else found
        _append_trimmed(parts, text, search_from, part_end)
        search_from = found + len(separator)
    return parts


def _hard_split(text: str, span: TextSpan, spec: ChunkSpec) -> list[TextSpan]:
    chunks: list[TextSpan] = []
    start = span.start
    while start < span.end:
        chunk_end = min(start + spec.max_chars, span.end)
        _append_trimmed(chunks, text, start, chunk_end)
        next_start = chunk_end - spec.overlap_chars
        start = chunk_end if next_start <= start else next_start
    return chunks


def _append_trimmed(spans: list[TextSpan], text: str, start: int, end: int) -> None:
    span = _trim_span(text, start, end)
    if span is not None:
        spans.append(span)


def _trim_span(text: str, start: int, end: int) -> TextSpan | None:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    if end <= start:
        return None
    return TextSpan(start=start, end=end, text=text[start:end])


def _overlap_start(previous: TextSpan, part: TextSpan, spec: ChunkSpec) -> int:
    if spec.overlap_chars == 0:
        return part.start
    start = max(previous.start, previous.end - spec.overlap_chars)
    return start if part.end - start <= spec.max_chars else part.start


def _build_chunk(
    *,
    document: SourceDocument,
    chunk_id: str,
    level: ChunkLevel,
    span: TextSpan,
    parent_chunk_id: str | None,
    heading_path: list[str],
    section_tag: str | None,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        source_id=document.source_id,
        source_path=document.content_path,
        title=document.title,
        chunk_level=level,
        parent_chunk_id=parent_chunk_id,
        heading_path=heading_path,
        section_tag=section_tag,
        char_start=span.start,
        char_end=span.end,
        chunk_hash=hash_text(span.text),
        excerpt=_excerpt(span.text),
        text=span.text,
    )


def _chunk_id(
    source_id: str,
    level: ChunkLevel,
    span: TextSpan,
    parent_chunk_id: str | None,
) -> str:
    parent_part = parent_chunk_id or "root"
    seed = f"{source_id}\0{parent_part}\0{level}\0{span.start}\0{span.end}\0{span.text}"
    digest = strip_hash_prefix(hash_text(seed))[:16]
    return f"{source_id}:{span.start}-{span.end}:{level}:{digest}"


def _header_level_to_chunk_level(header_level: int) -> ChunkLevel:
    if header_level == 0:
        return "document"
    if header_level == 1:
        return "section"
    if header_level == 2:
        return "subsection"
    return "paragraph"


def _child_level_for_parent(parent_level: ChunkLevel) -> ChunkLevel:
    if parent_level in {"document", "section", "subsection"}:
        return "paragraph"
    return "clause"


def _extract_section_tag(text: str) -> str | None:
    match = NUMERIC_SECTION_RE.match(text)
    if match:
        return match.group(1)
    lowered = re.sub(r"[^a-z ]+", " ", text.lower())
    words = " ".join(lowered.split())
    for key, value in IMRAD_TAGS.items():
        if words == key or words.startswith(f"{key} "):
            return value
    return None


def _first_nonblank_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def _is_pipe_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _is_table_block(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    return bool(lines) and all(_is_pipe_table_line(line) for line in lines)


def _excerpt(text: str) -> str:
    excerpt = " ".join(text.split())
    return excerpt[:EXCERPT_CHARS]


def _mask_fenced_code_blocks(text: str) -> str:
    """Mask fenced code blocks (```...```) to prevent matching headings/tables.

    Preserves character positions.
    """
    masked = list(text)
    in_code_block = False
    i = 0
    n = len(text)
    while i < n:
        if text[i:i+3] == "```":
            in_code_block = not in_code_block
            i += 3
        else:
            if in_code_block:
                if text[i] != "\n":
                    masked[i] = " "
            i += 1
    return "".join(masked)
