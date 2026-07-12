"""Phase 2b Unit 6 retrieval comparison report tests."""

from __future__ import annotations

from collections.abc import Sequence
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

import pytest

from evidence_bundler.contracts.writer import build_retrieval_bundle
from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.cb import ClaimAuditUnit
from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.reports.retrieval_comparison import (
    load_fixture_expectations,
    render_comparison_report,
    run_comparison_suite,
    score_claim_units,
)


def test_load_fixture_expectations() -> None:
    expectations = load_fixture_expectations(_expectations_path())

    assert expectations.schema_version == "internal-phase-2b-unit6"
    assert expectations.fixture == "scaffold-run-mixed-formats"
    assert expectations.by_claim_id["clm-md"].expected_supporting_source_ids == ("src-md",)
    assert expectations.by_claim_id["clm-md"].expected_countercandidate_needles == (
        "no significant effect",
    )
    assert expectations.by_claim_id["clm-pdf"].expected_countercandidate_role == "none"


def test_score_claim_units_defines_supporting_precision_and_counter_metrics(
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
    bundle_dir = tmp_path / "bundle"
    build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(
            retrieval_method="hybrid",
            top_k=5,
            rrf_candidate_pool=20,
            embedding_model="fake-semantic-model",
            rerank_enabled=True,
            rerank_model="fake-reranker",
            rerank_top_n=5,
            contradiction_enabled=True,
            contradiction_top_k=5,
        ),
    )
    claim_units = _load_claim_units(bundle_dir)

    metrics, claim_results = score_claim_units(
        claim_units=claim_units,
        expectations=load_fixture_expectations(_expectations_path()),
        contradiction_enabled=True,
    )

    assert metrics.supporting_source_recall.endswith("/3")
    assert 0.0 <= float(metrics.supporting_precision_proxy) <= 1.0
    assert metrics.counter_candidate_recall == "2/2"
    assert metrics.false_positive_counter_candidate_count.isdigit()
    md_result = next(result for result in claim_results if result.claim_id == "clm-md")
    assert md_result.matched_countercandidate_needles == ("no significant effect",)


def test_score_claim_units_marks_counter_metrics_na_when_contradiction_disabled(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    bundle_dir = tmp_path / "bundle"
    build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        bundle_dir,
        config=RetrievalConfig(retrieval_method="bm25", top_k=5, child_top_k=20),
    )

    metrics, claim_results = score_claim_units(
        claim_units=_load_claim_units(bundle_dir),
        expectations=load_fixture_expectations(_expectations_path()),
        contradiction_enabled=False,
    )

    assert metrics.counter_candidate_recall == "n/a"
    assert metrics.false_positive_counter_candidate_count == "n/a"
    assert all(result.matched_countercandidate_needles is None for result in claim_results)
    assert all(result.false_positive_counter_passages is None for result in claim_results)


def test_run_comparison_suite_extracts_deltas_and_checklist(
    mixed_scaffold_run_dir: Path,
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

    result = run_comparison_suite(
        fixture_dir=mixed_scaffold_run_dir,
        expectations=load_fixture_expectations(_expectations_path()),
        run_configs=_run_configs(),
        work_dir=tmp_path,
        generated_at_utc="2026-05-12T18:00:00Z",
    )

    assert [run.name for run in result.runs] == [
        "lexical_bm25",
        "hybrid_rerank_only",
        "hybrid_rerank_contradiction",
    ]
    assert all(run.completed for run in result.runs)
    assert len(result.deltas) == 2
    assert any("Config hashes recorded" in item for item in result.checklist)


def test_render_comparison_report_uses_calibrated_language_and_na_counter_metrics(
    mixed_scaffold_run_dir: Path,
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
    result = run_comparison_suite(
        fixture_dir=mixed_scaffold_run_dir,
        expectations=load_fixture_expectations(_expectations_path()),
        run_configs=_run_configs(),
        work_dir=tmp_path,
        generated_at_utc="2026-05-12T18:00:00Z",
    )

    report = render_comparison_report(result)

    assert "Candidate passages are retrieval nominations, not verified evidence." in report
    assert "review required" in report
    assert "C-A/C-B contract status: `v1.0.0 unchanged`" in report
    assert "Pre-Merge Checklist" in report
    assert "| `lexical_bm25`" in report
    assert "| `hybrid_rerank_only`" in report
    assert "n/a | n/a |" in report
    assert "verified support" not in report.lower()


def test_unit6_script_smoke_writes_report(
    tmp_path: Path,
) -> None:
    script = _load_unit6_script()
    report_path = script.generate_report(Path(__file__).resolve().parents[1], report_dir=tmp_path)

    report = report_path.read_text(encoding="utf-8")
    assert report_path.name.startswith("phase_2b_unit6_comparison_")
    assert "# Phase 2b Unit 6 Lexical-vs-Hybrid Comparison Report" in report
    assert "lexical_bm25" in report
    assert "hybrid_rerank_contradiction" in report


def _load_claim_units(bundle_dir: Path) -> dict[str, ClaimAuditUnit]:
    return {
        path.stem: load_model_yaml(ClaimAuditUnit, path)
        for path in sorted((bundle_dir / "claims").glob("*.yaml"))
    }


def _expectations_path() -> Path:
    return Path(__file__).parent / "fixtures" / "phase-2b-unit6-expectations.yaml"


def _run_configs() -> dict[str, RetrievalConfig]:
    return {
        "lexical_bm25": RetrievalConfig(retrieval_method="bm25", top_k=5, child_top_k=20),
        "hybrid_rerank_only": RetrievalConfig(
            retrieval_method="hybrid",
            top_k=5,
            rrf_candidate_pool=20,
            embedding_model="fake-semantic-model",
            rerank_enabled=True,
            rerank_model="fake-reranker",
            rerank_top_n=5,
        ),
        "hybrid_rerank_contradiction": RetrievalConfig(
            retrieval_method="hybrid",
            top_k=5,
            rrf_candidate_pool=20,
            embedding_model="fake-semantic-model",
            rerank_enabled=True,
            rerank_model="fake-reranker",
            rerank_top_n=5,
            contradiction_enabled=True,
            contradiction_top_k=5,
        ),
    }


def _load_unit6_script() -> Any:
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "run_phase_2b_unit6_comparison.py"
    )
    spec = spec_from_file_location("run_phase_2b_unit6_comparison", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeEmbedder:
    """Deterministic fake embedding model for comparison tests."""

    def encode(self, texts: Sequence[str], **_kwargs: object) -> list[list[float]]:
        return [_vector_for(text) for text in texts]


class FakeCrossEncoder:
    """Deterministic fake reranker for comparison tests."""

    def predict(self, pairs: Sequence[tuple[str, str]], **_kwargs: object) -> list[float]:
        return [_rerank_score(parent_text) for _claim_text, parent_text in pairs]


def _vector_for(text: str) -> list[float]:
    lowered = text.lower()
    if "submission checklist" in lowered or "audit review" in lowered:
        return [1.0, 0.0, 0.0]
    if "line breaks" in lowered or "plain text" in lowered:
        return [0.0, 1.0, 0.0]
    if "pdf" in lowered or "extraction" in lowered:
        return [0.0, 0.0, 1.0]
    return [0.1, 0.1, 0.1]


def _rerank_score(parent_text: str) -> float:
    lowered = parent_text.lower()
    if "no significant effect" in lowered:
        return 6.0
    if "only when" in lowered:
        return 5.0
    if "submission checklist" in lowered:
        return 4.0
    if "plain-text intake" in lowered:
        return 3.0
    if "pdf extraction" in lowered:
        return 2.0
    return -1.0
