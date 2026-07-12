"""Review annotation YAML I/O tests."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from evidence_bundler.contracts.writer import build_retrieval_bundle
from evidence_bundler.contracts.yaml_io import dump_yaml, load_model_yaml, load_yaml
from evidence_bundler.models.cb import ClaimAuditUnit
from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.review.io import (
    ReviewAnnotationDriftError,
    load_review_annotations,
    scaffold_annotations_from_bundle,
    write_review_annotations,
)


def test_scaffold_annotations_from_hybrid_bundle_matches_claim_passage_containers(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft_bundle_dir = _build_hybrid_draft_bundle(
        mixed_scaffold_run_tmp,
        tmp_path,
        monkeypatch,
    )

    annotation_file = scaffold_annotations_from_bundle(draft_bundle_dir)
    expected = _expected_annotations_from_claim_files(draft_bundle_dir)

    assert [
        (row.claim_id, row.source_id, row.passage_id, row.evidence_role)
        for row in annotation_file.annotations
    ] == expected
    assert len(annotation_file.annotations) == len(expected)
    assert all(row.decision == "needs-review" for row in annotation_file.annotations)
    assert all(row.decided_at_utc is None for row in annotation_file.annotations)
    assert [
        (row.claim_id, row.source_id, row.passage_id)
        for row in annotation_file.annotations
    ] == sorted(
        (row.claim_id, row.source_id, row.passage_id)
        for row in annotation_file.annotations
    )


def test_load_review_annotations_detects_bundle_hash_drift(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft_bundle_dir = _build_hybrid_draft_bundle(
        mixed_scaffold_run_tmp,
        tmp_path,
        monkeypatch,
    )
    annotation_path = tmp_path / "review_annotations.yaml"
    annotations = scaffold_annotations_from_bundle(draft_bundle_dir)
    write_review_annotations(annotations, annotation_path)

    claim_path = next((draft_bundle_dir / "claims").glob("*.yaml"))
    claim_path.write_text(
        claim_path.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )

    with pytest.raises(ReviewAnnotationDriftError, match="bundle-hash mismatch"):
        load_review_annotations(annotation_path, draft_bundle_dir)


def test_load_review_annotations_detects_retrieval_config_hash_drift(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft_bundle_dir = _build_hybrid_draft_bundle(
        mixed_scaffold_run_tmp,
        tmp_path,
        monkeypatch,
    )
    annotation_path = tmp_path / "review_annotations.yaml"
    annotations = scaffold_annotations_from_bundle(draft_bundle_dir)
    write_review_annotations(annotations, annotation_path)
    data = load_yaml(annotation_path)
    data["retrieval_config_hash"] = (
        "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )
    dump_yaml(data, annotation_path)

    with pytest.raises(ReviewAnnotationDriftError, match="config-hash mismatch"):
        load_review_annotations(annotation_path, draft_bundle_dir)


def test_review_annotations_write_load_round_trip(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft_bundle_dir = _build_hybrid_draft_bundle(
        mixed_scaffold_run_tmp,
        tmp_path,
        monkeypatch,
    )
    annotation_path = tmp_path / "review_annotations.yaml"
    annotations = scaffold_annotations_from_bundle(draft_bundle_dir)

    write_review_annotations(annotations, annotation_path)
    loaded = load_review_annotations(annotation_path, draft_bundle_dir)

    assert loaded == annotations


def _build_hybrid_draft_bundle(
    scaffold_run_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    draft_bundle_dir = tmp_path / "phase-3-unit1-draft"
    build_retrieval_bundle(
        scaffold_run_dir,
        draft_bundle_dir,
        config=RetrievalConfig(
            retrieval_method="hybrid",
            top_k=5,
            rrf_candidate_pool=20,
            embedding_model="fake-semantic-model",
            contradiction_enabled=True,
            contradiction_top_k=5,
        ),
    )
    return draft_bundle_dir


def _expected_annotations_from_claim_files(
    draft_bundle_dir: Path,
) -> list[tuple[str, str, str, str]]:
    expected: list[tuple[str, str, str, str]] = []
    for claim_path in sorted((draft_bundle_dir / "claims").glob("*.yaml")):
        claim = load_model_yaml(ClaimAuditUnit, claim_path)
        expected.extend(
            (claim.claim_id, passage.source_id, passage.passage_id, "supporting")
            for passage in claim.evidence_passages
        )
        expected.extend(
            (claim.claim_id, passage.source_id, passage.passage_id, "contradicting")
            for passage in claim.counterevidence_passages
        )
    return sorted(expected, key=lambda row: (row[0], row[1], row[2]))


class FakeEmbedder:
    """Deterministic fake embedding model for review I/O tests."""

    def encode(self, texts: Sequence[str], **_kwargs: object) -> list[list[float]]:
        return [_vector_for(text) for text in texts]


def _vector_for(text: str) -> list[float]:
    lowered = text.lower()
    if "submission checklist" in lowered or "audit review" in lowered:
        return [1.0, 0.0, 0.0]
    if "line breaks" in lowered or "plain text" in lowered:
        return [0.0, 1.0, 0.0]
    if "pdf" in lowered or "extraction" in lowered:
        return [0.0, 0.0, 1.0]
    return [0.1, 0.1, 0.1]
