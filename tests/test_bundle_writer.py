"""C-B fixture bundle writer tests."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from conftest import assert_no_python_yaml_tags

from evidence_bundler.contracts.hashing import (
    compute_bundle_tree_hash,
    compute_corpus_hash,
    hash_file,
    verify_sha256sums,
    write_sha256sums,
)
from evidence_bundler.contracts.writer import (
    build_fixture_bundle,
    build_retrieval_bundle,
    validate_bundle_tree,
)
from evidence_bundler.contracts.yaml_io import dump_yaml, load_model_yaml, load_yaml
from evidence_bundler.models.cb import AuditConfig, BundleManifest, ClaimAuditUnit, PassageRecord
from evidence_bundler.models.retrieval import RetrievalConfig


def test_build_fixture_bundle_emits_complete_cb_tree(
    scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    bundle_dir = tmp_path / "evidence-bundle-fixture"
    result = build_fixture_bundle(scaffold_run_tmp, bundle_dir)

    expected_files = {
        "bundle_manifest.yaml",
        "claims/clm-001.yaml",
        "evidence/src-001/passages/pass-001.yaml",
        "evidence/src-001/source_profile.yaml",
        "audit_config.yaml",
        "validation_set_ref.yaml",
        "CONTRACT_VERSION",
        "SHA256SUMS",
    }
    actual_files = {
        path.relative_to(bundle_dir).as_posix() for path in bundle_dir.rglob("*") if path.is_file()
    }

    assert result.bundle_dir == bundle_dir
    assert expected_files <= actual_files
    assert "claims/seed-001.yaml" not in actual_files
    assert validate_bundle_tree(bundle_dir) == []
    assert verify_sha256sums(bundle_dir) == []


def test_bundle_manifest_hash_matches_normalized_tree(
    scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    bundle_dir = tmp_path / "evidence-bundle-fixture"
    build_fixture_bundle(scaffold_run_tmp, bundle_dir)

    manifest = load_model_yaml(BundleManifest, bundle_dir / "bundle_manifest.yaml")
    assert manifest.bundle.bundle_hash == compute_bundle_tree_hash(bundle_dir)


def test_claim_audit_fields_are_null_at_handoff(scaffold_run_tmp: Path, tmp_path: Path) -> None:
    bundle_dir = tmp_path / "evidence-bundle-fixture"
    build_fixture_bundle(scaffold_run_tmp, bundle_dir)

    claim_unit = load_model_yaml(ClaimAuditUnit, bundle_dir / "claims" / "clm-001.yaml")
    audit_data = claim_unit.audit.model_dump(mode="json")

    assert audit_data
    assert all(value is None for value in audit_data.values())


def test_generated_yaml_has_no_python_tags(scaffold_run_tmp: Path, tmp_path: Path) -> None:
    bundle_dir = tmp_path / "evidence-bundle-fixture"
    build_fixture_bundle(scaffold_run_tmp, bundle_dir)
    assert_no_python_yaml_tags(bundle_dir)


def test_build_retrieval_bundle_emits_valid_cb_tree(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    bundle_dir = tmp_path / "evidence-bundle-retrieval"
    report_path = tmp_path / "retrieval-report.md"

    result = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(top_k=1, child_top_k=5),
        report_out=report_path,
    )

    assert result.bundle_dir == bundle_dir
    assert result.retrieval_report is not None
    assert report_path.exists()
    assert validate_bundle_tree(bundle_dir) == []
    assert verify_sha256sums(bundle_dir) == []
    assert_no_python_yaml_tags(bundle_dir)

    claim_unit = load_model_yaml(ClaimAuditUnit, bundle_dir / "claims" / "clm-md.yaml")
    assert claim_unit.evidence_passages
    assert all(value is None for value in claim_unit.audit.model_dump(mode="json").values())


def test_retrieval_bundle_uses_auto_retrieved_passages(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    bundle_dir = tmp_path / "evidence-bundle-retrieval"
    build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(top_k=1, child_top_k=5),
    )

    passage_paths = sorted((bundle_dir / "evidence").glob("*/passages/*.yaml"))
    assert passage_paths
    passages = [load_model_yaml(PassageRecord, path) for path in passage_paths]
    assert {passage.extraction_method for passage in passages} == {"auto_retrieved"}


def test_retrieval_bundle_keeps_no_candidate_claims_and_reports_them(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    claims_path = mixed_scaffold_run_tmp / "claims.yaml"
    claims_data = load_yaml(claims_path)
    claims_data["claims"].append(
        {
            "claim_id": "clm-none",
            "claim_type": "extracted_claim",
            "claim_text": "zzzz qqqq xxxx unmatched lexical tokens",
            "support_status": "uncertain",
            "claim_strength": 0.5,
            "extraction_fidelity": 0.5,
            "source_refs": [],
            "counterevidence_checked": True,
            "counterevidence_found": False,
            "downgraded": False,
            "downgrade_reason": None,
            "scaffold_notes": "Synthetic no-candidate claim for Phase 2a reporting.",
        }
    )
    dump_yaml(claims_data, claims_path)
    write_sha256sums(mixed_scaffold_run_tmp)

    bundle_dir = tmp_path / "evidence-bundle-retrieval"
    report_path = tmp_path / "retrieval-report.md"
    result = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(top_k=1, child_top_k=5),
        report_out=report_path,
    )

    claim_unit = load_model_yaml(ClaimAuditUnit, bundle_dir / "claims" / "clm-none.yaml")
    manifest = load_model_yaml(BundleManifest, bundle_dir / "bundle_manifest.yaml")

    assert claim_unit.evidence_passages == []
    assert result.retrieval_report is not None
    assert result.retrieval_report.no_candidate_claim_ids == ["clm-none"]
    assert "`clm-none`" in report_path.read_text(encoding="utf-8")
    assert manifest.quality_gates.every_claim_has_at_least_one_passage is False


def test_build_retrieval_bundle_hybrid_emits_valid_cb_tree(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    bundle_dir = tmp_path / "evidence-bundle-hybrid"
    report_path = tmp_path / "hybrid-report.md"

    result = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(
            retrieval_method="hybrid",
            top_k=1,
            rrf_candidate_pool=5,
            embedding_model="fake-semantic-model",
        ),
        report_out=report_path,
    )

    assert result.retrieval_report is not None
    assert result.retrieval_report.retrieval_config.retrieval_method == "hybrid"
    assert validate_bundle_tree(bundle_dir) == []
    assert verify_sha256sums(bundle_dir) == []
    report = report_path.read_text(encoding="utf-8")
    assert "- Retrieval method: `hybrid`" in report
    assert "- RRF k constant: `60`" in report
    assert "- Rerank enabled: `False`" in report
    assert "Lexical-only" in report
    assert "Semantic-only" in report
    assert "Top fusion score" in report
    assert "no rerank score" in report

    claim_unit = load_model_yaml(ClaimAuditUnit, bundle_dir / "claims" / "clm-md.yaml")
    assert claim_unit.evidence_passages


def test_build_retrieval_bundle_hybrid_rerank_reports_scores(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_reranker_model",
        lambda *_args, **_kwargs: FakeCrossEncoder(),
    )
    bundle_dir = tmp_path / "evidence-bundle-hybrid-rerank"
    report_path = tmp_path / "hybrid-rerank-report.md"

    result = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(
            retrieval_method="hybrid",
            top_k=1,
            rrf_candidate_pool=5,
            embedding_model="fake-semantic-model",
            rerank_enabled=True,
            rerank_model="fake-reranker",
            rerank_top_n=3,
        ),
        report_out=report_path,
    )

    assert result.retrieval_report is not None
    assert result.retrieval_report.retrieval_config.rerank_enabled is True
    assert validate_bundle_tree(bundle_dir) == []
    assert verify_sha256sums(bundle_dir) == []
    report = report_path.read_text(encoding="utf-8")
    assert "- Rerank enabled: `True`" in report
    assert "- Rerank model: `fake-reranker`" in report
    assert "- Rerank candidate limit: `3`" in report
    assert "Top rerank score" in report
    assert any(
        summary.top_rerank_score is not None
        for summary in result.retrieval_report.claim_summaries
        if not summary.no_candidate
    )

    claim_unit = load_model_yaml(ClaimAuditUnit, bundle_dir / "claims" / "clm-md.yaml")
    audit_config = load_model_yaml(AuditConfig, bundle_dir / "audit_config.yaml")
    assert claim_unit.evidence_passages
    assert all(value is None for value in claim_unit.audit.model_dump(mode="json").values())
    assert all("reranking" not in limitation for limitation in audit_config.known_limitations)


def test_hybrid_bundle_can_nominate_semantic_only_candidate(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    bundle_dir = tmp_path / "evidence-bundle-hybrid-semantic-only"

    result = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(
            retrieval_method="hybrid",
            top_k=1,
            rrf_candidate_pool=5,
            lexical_score_floor=999.0,
            embedding_model="fake-semantic-model",
        ),
    )

    assert result.retrieval_report is not None
    md_summary = next(
        summary
        for summary in result.retrieval_report.claim_summaries
        if summary.claim_id == "clm-md"
    )
    assert md_summary.selected_candidates == 1
    assert md_summary.lexical_only_child_hits == 0
    assert md_summary.semantic_only_child_hits is not None
    assert md_summary.semantic_only_child_hits > 0
    assert md_summary.overlap_child_hits == 0
    assert md_summary.top_lexical_score is None
    assert md_summary.top_semantic_score is not None
    assert md_summary.top_fusion_score is not None


def test_contradiction_bundle_routes_counter_candidates(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    bundle_dir = tmp_path / "evidence-bundle-contradiction"
    report_path = tmp_path / "contradiction-report.md"

    result = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(
            retrieval_method="hybrid",
            top_k=5,
            rrf_candidate_pool=20,
            embedding_model="fake-semantic-model",
            contradiction_enabled=True,
            contradiction_top_k=5,
        ),
        report_out=report_path,
    )

    claim_unit = load_model_yaml(ClaimAuditUnit, bundle_dir / "claims" / "clm-md.yaml")
    counter_texts = [passage.passage_text for passage in claim_unit.counterevidence_passages]
    evidence_texts = [passage.passage_text for passage in claim_unit.evidence_passages]

    assert result.retrieval_report is not None
    assert any("no significant effect" in text for text in counter_texts)
    assert all("no significant effect" not in text for text in evidence_texts)
    assert any(
        summary.contradicting_hits > 0
        for summary in result.retrieval_report.claim_summaries
    )
    report = report_path.read_text(encoding="utf-8")
    assert "- Contradiction retrieval enabled: `True`" in report
    assert "No counter-candidate claims" in report
    assert "Contradicting" in report


def test_contradiction_bundle_reports_no_countercandidate_without_no_candidate(
    scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _rewrite_minimal_fixture_without_gate_patterns(scaffold_run_tmp)
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    bundle_dir = tmp_path / "evidence-bundle-no-countercandidate"

    result = build_retrieval_bundle(
        scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(
            retrieval_method="hybrid",
            top_k=2,
            rrf_candidate_pool=5,
            embedding_model="fake-semantic-model",
            contradiction_enabled=True,
            contradiction_top_k=2,
        ),
    )

    claim_unit = load_model_yaml(ClaimAuditUnit, bundle_dir / "claims" / "clm-001.yaml")

    assert claim_unit.evidence_passages
    assert claim_unit.counterevidence_passages == []
    assert result.retrieval_report is not None
    assert result.retrieval_report.no_candidate_claim_ids == []
    assert result.retrieval_report.no_countercandidate_claim_ids == ["clm-001"]


def test_build_retrieval_bundle_semantic_emits_valid_cb_tree(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    bundle_dir = tmp_path / "evidence-bundle-semantic"
    report_path = tmp_path / "semantic-report.md"

    result = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(
            retrieval_method="semantic",
            top_k=2,
            semantic_child_top_k=5,
            embedding_model="fake-semantic-model",
        ),
        report_out=report_path,
    )

    assert result.retrieval_report is not None
    assert result.retrieval_report.retrieval_config.retrieval_method == "semantic"
    assert validate_bundle_tree(bundle_dir) == []
    assert verify_sha256sums(bundle_dir) == []
    assert any(
        summary.top_semantic_score is not None
        for summary in result.retrieval_report.claim_summaries
        if not summary.no_candidate
    )
    assert all(
        summary.top_lexical_score is None
        for summary in result.retrieval_report.claim_summaries
    )
    report = report_path.read_text(encoding="utf-8")
    assert "- Retrieval method: `semantic`" in report
    assert "- Semantic child top-k: `5`" in report


class FakeEmbedder:
    """Deterministic fake embedding model for writer-level hybrid tests."""

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


class FakeCrossEncoder:
    """Deterministic fake reranker for writer-level hybrid+rerank tests."""

    def predict(self, pairs: Sequence[tuple[str, str]], **_kwargs: object) -> list[float]:
        return [_rerank_score(parent_text) for _claim_text, parent_text in pairs]


def _rerank_score(parent_text: str) -> float:
    lowered = parent_text.lower()
    if "plain-text intake" in lowered:
        return 5.0
    if "submission checklist" in lowered:
        return 2.0
    if "pdf extraction" in lowered:
        return 1.0
    return -1.0


def _rewrite_minimal_fixture_without_gate_patterns(scaffold_run_dir: Path) -> None:
    content_path = scaffold_run_dir / "corpus" / "src-001" / "content.md"
    content_path.write_text(
        "# Synthetic Regulatory Guidance\n\n"
        "Accelerated approval applications should include 30-day accelerated stability "
        "data in the submission package.\n\n"
        "The submission package keeps stability records available for review.\n",
        encoding="utf-8",
    )
    metadata_path = scaffold_run_dir / "corpus" / "src-001" / "metadata.yaml"
    metadata = load_yaml(metadata_path)
    metadata["content_hash"] = hash_file(content_path)
    dump_yaml(metadata, metadata_path)

    scaffold_run_path = scaffold_run_dir / "scaffold_run.yaml"
    scaffold_run = load_yaml(scaffold_run_path)
    scaffold_run["corpus"]["corpus_hash"] = compute_corpus_hash(scaffold_run_dir / "corpus")
    dump_yaml(scaffold_run, scaffold_run_path)
    write_sha256sums(scaffold_run_dir)
