"""Incremental ingest tests for Phase 1 Unit 4."""

from __future__ import annotations

from pathlib import Path
from shutil import rmtree

from evidence_bundler.contracts.hashing import compute_corpus_hash, hash_file, write_sha256sums
from evidence_bundler.contracts.yaml_io import dump_yaml, load_yaml
from evidence_bundler.ingest.dedup import run_ingest


def test_first_run_chunks_sources_and_second_run_skips_unchanged(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "ingest-state.json"

    first = run_ingest(mixed_scaffold_run_tmp, state_path=state_path, dry_run=False)
    second = run_ingest(mixed_scaffold_run_tmp, state_path=state_path, dry_run=False)

    assert state_path.exists()
    assert first.documents_loaded == 4
    assert first.documents_chunked == 4
    assert first.documents_skipped == 0
    assert first.chunks_emitted > 0
    assert _statuses(first) == {
        "src-empty": "new",
        "src-md": "new",
        "src-pdf": "new",
        "src-txt": "new",
    }
    assert _status_by_source(first)["src-empty"].chunks_emitted == 0

    assert second.documents_loaded == 4
    assert second.documents_chunked == 0
    assert second.documents_skipped == 4
    assert second.chunks_emitted == 0
    assert set(_statuses(second).values()) == {"unchanged"}


def test_dry_run_does_not_write_state(mixed_scaffold_run_tmp: Path, tmp_path: Path) -> None:
    state_path = tmp_path / "ingest-state.json"

    first = run_ingest(mixed_scaffold_run_tmp, state_path=state_path, dry_run=True)
    second = run_ingest(mixed_scaffold_run_tmp, state_path=state_path, dry_run=True)

    assert not state_path.exists()
    assert _statuses(first) == _statuses(second)
    assert set(_statuses(second).values()) == {"new"}


def test_modified_source_invalidates_only_that_source(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "ingest-state.json"
    run_ingest(mixed_scaffold_run_tmp, state_path=state_path, dry_run=False)
    _append_valid_source_text(mixed_scaffold_run_tmp, "src-md", "\nMutation for Unit 4.\n")

    report = run_ingest(mixed_scaffold_run_tmp, state_path=state_path, dry_run=False)

    assert _statuses(report) == {
        "src-empty": "unchanged",
        "src-md": "changed",
        "src-pdf": "unchanged",
        "src-txt": "unchanged",
    }
    assert report.documents_chunked == 1
    assert report.documents_skipped == 3
    assert report.chunks_emitted == _status_by_source(report)["src-md"].chunks_emitted
    assert _status_by_source(report)["src-md"].previous_content_hash is not None


def test_deleted_source_is_reported_as_removed(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "ingest-state.json"
    run_ingest(mixed_scaffold_run_tmp, state_path=state_path, dry_run=False)
    rmtree(mixed_scaffold_run_tmp / "corpus" / "src-empty")
    _refresh_manifest_and_sums(mixed_scaffold_run_tmp)

    report = run_ingest(mixed_scaffold_run_tmp, state_path=state_path, dry_run=False)

    assert report.documents_loaded == 3
    assert report.documents_removed == 1
    assert _statuses(report) == {
        "src-empty": "removed",
        "src-md": "unchanged",
        "src-pdf": "unchanged",
        "src-txt": "unchanged",
    }
    assert _status_by_source(report)["src-empty"].chunks_emitted == 0


def test_report_out_writes_markdown_report(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "ingest-report.md"

    report = run_ingest(
        mixed_scaffold_run_tmp,
        state_path=tmp_path / "ingest-state.json",
        dry_run=True,
        report_out=report_path,
    )

    text = report_path.read_text(encoding="utf-8")
    assert report.chunks_emitted > 0
    assert "# Ingest Report" in text
    assert "## Source Outcomes" in text
    assert "`src-md`" in text
    assert "!!python" not in text


def _append_valid_source_text(scaffold_run_dir: Path, source_id: str, text: str) -> None:
    content_path = scaffold_run_dir / "corpus" / source_id / "content.md"
    content_path.write_text(content_path.read_text(encoding="utf-8") + text, encoding="utf-8")

    metadata_path = scaffold_run_dir / "corpus" / source_id / "metadata.yaml"
    metadata = load_yaml(metadata_path)
    metadata["content_hash"] = hash_file(content_path)
    dump_yaml(metadata, metadata_path)

    _refresh_manifest_and_sums(scaffold_run_dir)


def _refresh_manifest_and_sums(scaffold_run_dir: Path) -> None:
    manifest_path = scaffold_run_dir / "scaffold_run.yaml"
    manifest = load_yaml(manifest_path)
    corpus_dir = scaffold_run_dir / "corpus"
    source_dirs = [path for path in corpus_dir.iterdir() if path.is_dir()]
    manifest["corpus"]["total_sources"] = len(source_dirs)
    manifest["corpus"]["corpus_hash"] = compute_corpus_hash(corpus_dir)
    dump_yaml(manifest, manifest_path)
    write_sha256sums(scaffold_run_dir)


def _statuses(report) -> dict[str, str]:
    return {status.source_id: status.status for status in report.statuses}


def _status_by_source(report):
    return {status.source_id: status for status in report.statuses}
