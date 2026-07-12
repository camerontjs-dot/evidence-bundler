"""Generate the Phase 2b Unit 6 lexical-vs-hybrid comparison report."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import evidence_bundler.contracts.writer as writer
from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.reports.retrieval_comparison import (
    load_fixture_expectations,
    run_comparison_suite,
    write_comparison_report,
)


def main() -> None:
    asset_root = Path(__file__).resolve().parents[1]
    report_path = generate_report(asset_root)
    print(report_path)


def generate_report(asset_root: Path, report_dir: Path | None = None) -> Path:
    """Generate the Unit 6 report and return its path."""
    fixture_dir = asset_root / "tests" / "fixtures" / "scaffold-run-mixed-formats"
    expectations_path = asset_root / "tests" / "fixtures" / "phase-2b-unit6-expectations.yaml"
    report_dir = report_dir or asset_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"phase_2b_unit6_comparison_{timestamp}.md"

    writer.load_embedding_model = lambda *_args, **_kwargs: FakeEmbedder()
    writer.load_reranker_model = lambda *_args, **_kwargs: FakeCrossEncoder()

    expectations = load_fixture_expectations(expectations_path)
    with TemporaryDirectory() as tmp:
        result = run_comparison_suite(
            fixture_dir=fixture_dir,
            expectations=expectations,
            run_configs=_run_configs(),
            work_dir=Path(tmp),
        )
    write_comparison_report(result, report_path)
    return report_path


def _run_configs() -> dict[str, RetrievalConfig]:
    return {
        "lexical_bm25": RetrievalConfig(
            retrieval_method="bm25",
            top_k=5,
            child_top_k=20,
        ),
        "hybrid_rerank_only": RetrievalConfig(
            retrieval_method="hybrid",
            top_k=5,
            rrf_candidate_pool=20,
            embedding_model="fake-semantic-model",
            rerank_enabled=True,
            rerank_model="fake-reranker",
            rerank_top_n=5,
            contradiction_enabled=False,
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
            contradiction_rerank_enabled=False,
        ),
    }


class FakeEmbedder:
    """Deterministic fake embedding model for fixture comparison runs."""

    def encode(self, texts: Sequence[str], **_kwargs: object) -> list[list[float]]:
        return [_vector_for(text) for text in texts]


class FakeCrossEncoder:
    """Deterministic fake reranker for fixture comparison runs."""

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


if __name__ == "__main__":
    main()
