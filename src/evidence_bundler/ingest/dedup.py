"""Incremental ingest orchestration and report rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from evidence_bundler.ingest.chunker import chunk_source_document
from evidence_bundler.ingest.loader import load_source_documents
from evidence_bundler.models.document import IngestDocumentStatus, IngestReport, SourceDocument

STATE_VERSION = 1
DEFAULT_INGEST_STATE_PATH = Path.home() / ".cache" / "evidence-bundler" / "ingest-state.json"


class IngestStateError(Exception):
    """Raised when the incremental ingest state file cannot be used."""


def run_ingest(
    scaffold_run_dir: Path,
    *,
    state_path: Path | None = None,
    dry_run: bool = True,
    report_out: Path | None = None,
) -> IngestReport:
    """Load, deduplicate, and chunk a verified scaffold-run directory."""
    resolved_scaffold_run_dir = scaffold_run_dir.resolve()
    resolved_state_path = _resolve_state_path(state_path)
    documents = load_source_documents(resolved_scaffold_run_dir)
    previous_runs = _load_runs(resolved_state_path)
    run_key = _run_key(resolved_scaffold_run_dir)
    previous_sources = previous_runs.get(run_key, {})

    statuses = _build_statuses(documents, previous_sources)
    report = IngestReport(
        scaffold_run_dir=resolved_scaffold_run_dir,
        documents_loaded=len(documents),
        documents_chunked=sum(1 for status in statuses if status.status in {"new", "changed"}),
        documents_skipped=sum(1 for status in statuses if status.status == "unchanged"),
        documents_removed=sum(1 for status in statuses if status.status == "removed"),
        chunks_emitted=sum(status.chunks_emitted for status in statuses),
        dry_run=dry_run,
        state_path=resolved_state_path,
        statuses=statuses,
    )

    if not dry_run:
        previous_runs[run_key] = {
            document.source_id: document.content_hash for document in sorted_documents(documents)
        }
        _write_runs(resolved_state_path, previous_runs)

    if report_out is not None:
        write_ingest_report_markdown(report, report_out)

    return report


def write_ingest_report_markdown(report: IngestReport, path: Path) -> None:
    """Write a human-readable Markdown ingest report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_ingest_report_markdown(report), encoding="utf-8")


def render_ingest_report_markdown(report: IngestReport) -> str:
    """Render an ingest report without implying reviewed evidence status."""
    state_path = report.state_path.as_posix() if report.state_path is not None else "none"
    lines = [
        "# Ingest Report",
        "",
        f"- Scaffold run: `{report.scaffold_run_dir.as_posix()}`",
        f"- Dry run: `{str(report.dry_run).lower()}`",
        f"- State path: `{state_path}`",
        f"- Documents loaded: `{report.documents_loaded}`",
        f"- Documents chunked: `{report.documents_chunked}`",
        f"- Documents skipped: `{report.documents_skipped}`",
        f"- Documents removed: `{report.documents_removed}`",
        f"- Chunks emitted: `{report.chunks_emitted}`",
        "",
        "## Source Outcomes",
        "",
        "| Source | Status | Chunks | Coverage | Uncovered | Content hash | Previous hash |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for status in sorted(report.statuses, key=lambda item: (item.source_id, item.status)):
        previous = status.previous_content_hash or ""
        total = (status.coverage_chars or 0) + (status.uncovered_chars or 0)
        pct = (
            100.0 * status.coverage_chars / total
            if status.coverage_chars is not None and total > 0
            else 0.0
        )
        cov_str = (
            f"{status.coverage_chars} ({pct:.1f}%)"
            if status.coverage_chars is not None
            else "n/a"
        )
        unc_str = str(status.uncovered_chars) if status.uncovered_chars is not None else "n/a"
        lines.append(
            "| "
            f"`{status.source_id}` | `{status.status}` | {status.chunks_emitted} | "
            f"{cov_str} | {unc_str} | `{status.content_hash}` | `{previous}` |"
        )
    lines.append("")

    uncovered_warnings = []
    for status in sorted(report.statuses, key=lambda item: item.source_id):
        if status.uncovered_chars is not None and status.uncovered_chars > 0:
            uncovered_warnings.append(
                f"- Source `{status.source_id}` has "
                f"`{status.uncovered_chars}` uncovered characters."
            )
    if uncovered_warnings:
        lines.extend([
            "## Coverage Residue Warnings",
            "",
            *uncovered_warnings,
            ""
        ])

    return "\n".join(lines)


def sorted_documents(documents: list[SourceDocument]) -> list[SourceDocument]:
    """Return documents sorted by source id for stable state writes."""
    return sorted(documents, key=lambda document: document.source_id)


def _build_statuses(
    documents: list[SourceDocument],
    previous_sources: dict[str, str],
) -> list[IngestDocumentStatus]:
    statuses: list[IngestDocumentStatus] = []
    current_sources = {document.source_id: document for document in sorted_documents(documents)}

    for source_id, document in current_sources.items():
        previous_hash = previous_sources.get(source_id)

        # Always chunk to calculate coverage invariants
        chunks = chunk_source_document(document)
        parent_chunks = [c for c in chunks if c.parent_chunk_id is None]
        total_len = len(document.raw_text)
        coverage = 0
        if parent_chunks:
            intervals = sorted((c.char_start, c.char_end) for c in parent_chunks)
            merged = []
            current_start, current_end = intervals[0]
            for start, end in intervals[1:]:
                if start <= current_end:
                    current_end = max(current_end, end)
                else:
                    merged.append((current_start, current_end))
                    current_start, current_end = start, end
            merged.append((current_start, current_end))
            coverage = sum(end - start for start, end in merged)
        uncovered = total_len - coverage

        if previous_hash == document.content_hash:
            statuses.append(
                IngestDocumentStatus(
                    source_id=source_id,
                    content_hash=document.content_hash,
                    status="unchanged",
                    chunks_emitted=0,
                    previous_content_hash=previous_hash,
                    coverage_chars=coverage,
                    uncovered_chars=uncovered,
                )
            )
            continue

        statuses.append(
            IngestDocumentStatus(
                source_id=source_id,
                content_hash=document.content_hash,
                status="new" if previous_hash is None else "changed",
                chunks_emitted=len(chunks),
                previous_content_hash=previous_hash,
                coverage_chars=coverage,
                uncovered_chars=uncovered,
            )
        )

    for source_id in sorted(set(previous_sources) - set(current_sources)):
        previous_hash = previous_sources[source_id]
        statuses.append(
            IngestDocumentStatus(
                source_id=source_id,
                content_hash=previous_hash,
                status="removed",
                chunks_emitted=0,
                previous_content_hash=previous_hash,
            )
        )

    return statuses


def _resolve_state_path(state_path: Path | None) -> Path:
    if state_path is not None:
        return state_path.expanduser().resolve()
    return DEFAULT_INGEST_STATE_PATH.expanduser().resolve()


def _load_runs(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IngestStateError(f"Cannot parse ingest state JSON: {path}") from exc

    if not isinstance(raw, dict):
        raise IngestStateError(f"Ingest state must be a JSON object: {path}")
    if raw.get("version") != STATE_VERSION:
        raise IngestStateError(f"Unsupported ingest state version in {path}")
    runs = raw.get("runs")
    if not isinstance(runs, dict):
        raise IngestStateError(f"Ingest state missing runs mapping: {path}")

    return _validate_runs(runs, path)


def _write_runs(path: Path, runs: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": STATE_VERSION,
        "runs": {
            run_key: {"sources": dict(sorted(sources.items()))}
            for run_key, sources in sorted(runs.items())
        },
    }
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _validate_runs(raw_runs: dict[str, Any], path: Path) -> dict[str, dict[str, str]]:
    runs: dict[str, dict[str, str]] = {}
    for run_key, raw_run in raw_runs.items():
        if not isinstance(run_key, str) or not isinstance(raw_run, dict):
            raise IngestStateError(f"Invalid run entry in ingest state: {path}")
        raw_sources = raw_run.get("sources")
        if not isinstance(raw_sources, dict):
            raise IngestStateError(f"Invalid sources entry for {run_key!r}: {path}")
        sources: dict[str, str] = {}
        for source_id, content_hash in raw_sources.items():
            try:
                status = IngestDocumentStatus(
                    source_id=source_id,
                    content_hash=content_hash,
                    status="unchanged",
                    chunks_emitted=0,
                )
            except ValidationError as exc:
                raise IngestStateError(f"Invalid source state for {source_id!r}: {path}") from exc
            sources[status.source_id] = status.content_hash
        runs[run_key] = sources
    return runs


def _run_key(scaffold_run_dir: Path) -> str:
    return scaffold_run_dir.as_posix()
