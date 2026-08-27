"""Hashing and contract-pin tests."""

from __future__ import annotations

from pathlib import Path

from evidence_bundler.contracts.hashing import compute_corpus_hash, verify_sha256sums
from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.ca import ScaffoldRunManifest


def test_fixture_sha256sums_verify(fixture_scaffold_run_dir: Path) -> None:
    assert verify_sha256sums(fixture_scaffold_run_dir) == []


def test_fixture_corpus_hash_matches_manifest(fixture_scaffold_run_dir: Path) -> None:
    manifest = load_model_yaml(ScaffoldRunManifest, fixture_scaffold_run_dir / "scaffold_run.yaml")
    assert compute_corpus_hash(fixture_scaffold_run_dir / "corpus") == manifest.corpus.corpus_hash


def test_embedded_contract_version_pin() -> None:
    asset_root = Path(__file__).resolve().parents[1]
    version_pin = (asset_root / "schema" / ".contract-version").read_text(encoding="utf-8")
    assert version_pin.strip() == "1.2.0"


def test_embedded_vocabulary_is_byte_identical() -> None:
    import pytest

    from evidence_bundler.contracts.discovery import resolve_apparatus_contracts_root

    asset_root = Path(__file__).resolve().parents[1]
    embedded = asset_root / "schema" / "vocabulary.yaml"

    try:
        canonical_root = resolve_apparatus_contracts_root()
        candidates = [
            canonical_root / "workbench" / "schema" / "vocabulary.yaml",
            canonical_root / "schema" / "vocabulary.yaml",
        ]
        canonical = None
        for cand in candidates:
            if cand.exists():
                canonical = cand
                break
        if canonical is None:
            pytest.skip(f"Canonical vocabulary file not found in resolved root: {canonical_root}")
    except FileNotFoundError as exc:
        pytest.skip(str(exc))

    assert embedded.read_bytes() == canonical.read_bytes()


def test_deviations_tamper_detection(tmp_path: Path) -> None:
    # Create a dummy structure
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()

    src_dir = corpus_dir / "src-001"
    src_dir.mkdir()

    content_file = src_dir / "content.txt"
    content_file.write_text("some content", encoding="utf-8")

    # Root level deviations directory (should be ignored by iter_handoff_files)
    root_dev = tmp_path / "deviations"
    root_dev.mkdir()
    dev_file = root_dev / "deviation.txt"
    dev_file.write_text("deviation info", encoding="utf-8")

    # Nested deviations directory (should NOT be ignored)
    nested_dev = src_dir / "deviations"
    nested_dev.mkdir()
    nested_file = nested_dev / "nested_deviation.txt"
    nested_file.write_text("nested deviation info", encoding="utf-8")

    from evidence_bundler.contracts.hashing import iter_handoff_files

    files = iter_handoff_files(tmp_path)
    rel_files = {p.relative_to(tmp_path).as_posix() for p in files}
    assert "corpus/src-001/content.txt" in rel_files
    assert "corpus/src-001/deviations/nested_deviation.txt" in rel_files
    assert "deviations/deviation.txt" not in rel_files
