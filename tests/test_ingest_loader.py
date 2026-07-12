"""SourceDocument loader tests for Phase 1 Unit 1."""

from __future__ import annotations

from pathlib import Path

import pytest

from evidence_bundler.contracts.hashing import compute_corpus_hash, hash_file, write_sha256sums
from evidence_bundler.contracts.intake import verify_intake
from evidence_bundler.contracts.yaml_io import dump_yaml, load_yaml
from evidence_bundler.ingest.loader import (
    SourceDocumentIntakeError,
    load_source_documents,
)
from evidence_bundler.models.document import SourceDocument


def test_markdown_source_loads_with_expected_fields(mixed_scaffold_run_tmp: Path) -> None:
    documents = load_source_documents(mixed_scaffold_run_tmp)
    by_id = _by_source_id(documents)

    markdown = by_id["src-md"]
    content_path = mixed_scaffold_run_tmp / "corpus" / "src-md" / "content.md"

    assert [document.source_id for document in documents] == [
        "src-empty",
        "src-md",
        "src-pdf",
        "src-txt",
    ]
    assert markdown.content_type == "markdown"
    assert markdown.content_path == content_path.resolve()
    assert markdown.raw_text == content_path.read_text(encoding="utf-8")
    assert markdown.content_hash == hash_file(content_path)
    assert markdown.title == "Markdown Loader Fixture"


def test_plain_text_source_loads_with_expected_fields(mixed_scaffold_run_tmp: Path) -> None:
    by_id = _by_source_id(load_source_documents(mixed_scaffold_run_tmp))

    text = by_id["src-txt"]
    content_path = mixed_scaffold_run_tmp / "corpus" / "src-txt" / "content.txt"

    assert text.content_type == "text"
    assert text.content_path == content_path.resolve()
    assert text.raw_text == content_path.read_text(encoding="utf-8")
    assert text.content_hash == hash_file(content_path)
    assert text.title == "Plain Text Loader Fixture"


def test_sidecar_metadata_and_passages_round_trip_into_document(
    mixed_scaffold_run_tmp: Path,
) -> None:
    by_id = _by_source_id(load_source_documents(mixed_scaffold_run_tmp))
    source_dir = mixed_scaffold_run_tmp / "corpus" / "src-md"

    assert by_id["src-md"].metadata == load_yaml(source_dir / "metadata.yaml")
    assert by_id["src-md"].passages == load_yaml(source_dir / "passages.yaml")
    assert by_id["src-md"].metadata["retrieval"]["retrieved_for"] == ["clm-md"]
    assert by_id["src-md"].passages["passages"][0]["used_for_claims"] == ["clm-md"]


def test_content_hash_is_deterministic_across_loads(mixed_scaffold_run_tmp: Path) -> None:
    first = load_source_documents(mixed_scaffold_run_tmp)
    second = load_source_documents(mixed_scaffold_run_tmp)

    assert [(document.source_id, document.content_hash) for document in first] == [
        (document.source_id, document.content_hash) for document in second
    ]


def test_loader_refuses_unverified_scaffold_run(mixed_scaffold_run_tmp: Path) -> None:
    content_path = mixed_scaffold_run_tmp / "corpus" / "src-md" / "content.md"
    content_path.write_text(
        content_path.read_text(encoding="utf-8") + "\nMutation after handoff.\n",
        encoding="utf-8",
    )

    with pytest.raises(SourceDocumentIntakeError) as exc_info:
        load_source_documents(mixed_scaffold_run_tmp)

    assert "corpus_hash" in str(exc_info.value)
    assert exc_info.value.result.deviation_path is not None
    assert exc_info.value.result.deviation_path.exists()


def test_loader_refuses_unrecognized_content_extension_during_intake(
    mixed_scaffold_run_tmp: Path,
) -> None:
    source_dir = mixed_scaffold_run_tmp / "corpus" / "src-md"
    markdown_path = source_dir / "content.md"
    html_path = source_dir / "content.html"
    html_path.write_bytes(markdown_path.read_bytes())
    markdown_path.unlink()

    metadata_path = source_dir / "metadata.yaml"
    metadata = load_yaml(metadata_path)
    metadata["content_hash"] = hash_file(html_path)
    dump_yaml(metadata, metadata_path)

    manifest_path = mixed_scaffold_run_tmp / "scaffold_run.yaml"
    manifest = load_yaml(manifest_path)
    manifest["corpus"]["corpus_hash"] = compute_corpus_hash(mixed_scaffold_run_tmp / "corpus")
    dump_yaml(manifest, manifest_path)
    write_sha256sums(mixed_scaffold_run_tmp)

    intake = verify_intake(mixed_scaffold_run_tmp)
    assert not intake.valid
    with pytest.raises(SourceDocumentIntakeError) as exc_info:
        load_source_documents(mixed_scaffold_run_tmp)

    assert "Expected one content.{md,txt,pdf}" in str(exc_info.value)


def _by_source_id(documents: list[SourceDocument]) -> dict[str, SourceDocument]:
    return {document.source_id: document for document in documents}
