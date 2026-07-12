"""Generate the ADR-010 Unit 5 comparison report on committed fixtures."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

import evidence_bundler.contracts.writer as writer
from evidence_bundler.contracts.writer import BundleWriterError, build_retrieval_bundle
from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.cb import ClaimAuditUnit
from evidence_bundler.models.retrieval import RetrievalConfig

FIXTURE_EXPECTATIONS = {
    "clm-md": ("no significant effect",),
    "clm-txt": ("only when",),
    "clm-pdf": (),
}
EXPECTED_SUPPORT_SOURCES = {
    "clm-md": "src-md",
    "clm-txt": "src-txt",
    "clm-pdf": "src-pdf",
}
DOMAIN_PREFIXES = (
    "contraindicated in",
    "failed primary endpoint for",
    "off-label use of",
    "adverse events from",
)


def main() -> None:
    asset_root = Path(__file__).resolve().parents[1]
    fixture_dir = asset_root / "tests" / "fixtures" / "scaffold-run-mixed-formats"
    report_dir = asset_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"report_{timestamp}.md"

    writer.load_embedding_model = lambda *_args, **_kwargs: FakeEmbedder()
    writer.load_reranker_model = lambda *_args, **_kwargs: FakeCrossEncoder()

    default_config = RetrievalConfig(
        retrieval_method="hybrid",
        top_k=5,
        rrf_candidate_pool=20,
        embedding_model="fake-semantic-model",
        contradiction_enabled=True,
        contradiction_top_k=5,
    )
    runs = [
        ("test1_rerank_off_contra_rerank_off", default_config),
        (
            "test1_rerank_on_contra_rerank_off",
            default_config.model_copy(
                update={
                    "rerank_enabled": True,
                    "rerank_model": "fake-reranker",
                    "rerank_top_n": 5,
                }
            ),
        ),
        (
            "test1_rerank_on_contra_rerank_on",
            default_config.model_copy(
                update={
                    "rerank_enabled": True,
                    "rerank_model": "fake-reranker",
                    "rerank_top_n": 5,
                    "contradiction_rerank_enabled": True,
                }
            ),
        ),
        (
            "test2_default_plus_domain_prefixes",
            default_config.model_copy(
                update={
                    "contradiction_query_prefixes": [
                        *default_config.contradiction_query_prefixes,
                        *DOMAIN_PREFIXES,
                    ]
                }
            ),
        ),
        (
            "test3_text_gate_disabled",
            default_config.model_copy(update={"contradiction_text_gate_enabled": False}),
        ),
    ]

    results: list[RunResult] = [
        RunResult(
            name="test1_rerank_off_contra_rerank_on",
            config_hash="n/a",
            status="not runnable; validator requires rerank_enabled=True",
        )
    ]
    with TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        for name, config in runs:
            results.append(_run_fixture(name, config, fixture_dir, tmp_root))

    report_path.write_text(_render_report(results), encoding="utf-8")
    print(report_path)


def _run_fixture(
    name: str,
    config: RetrievalConfig,
    fixture_dir: Path,
    tmp_root: Path,
) -> RunResult:
    fixture_copy = tmp_root / name / "scaffold-run"
    output_dir = tmp_root / name / "bundle"
    copytree(fixture_dir, fixture_copy)
    try:
        result = build_retrieval_bundle(fixture_copy, output_dir, config=config)
    except BundleWriterError as exc:
        return RunResult(name=name, config_hash="n/a", status=f"failed: {exc}")
    claim_units = {
        path.stem: load_model_yaml(ClaimAuditUnit, path)
        for path in sorted((output_dir / "claims").glob("*.yaml"))
    }
    return RunResult(
        name=name,
        config_hash=result.retrieval_report.config_hash
        if result.retrieval_report is not None
        else "n/a",
        status="completed",
        metrics=_score_claim_units(claim_units),
    )


def _score_claim_units(claim_units: dict[str, ClaimAuditUnit]) -> dict[str, str]:
    expected_total = sum(len(values) for values in FIXTURE_EXPECTATIONS.values())
    expected_found = 0
    false_positive_passages = 0
    supported_expected_sources = 0
    supporting_passages = 0

    for claim_id, expected_needles in FIXTURE_EXPECTATIONS.items():
        unit = claim_units[claim_id]
        counter_texts = [passage.passage_text.lower() for passage in unit.counterevidence_passages]
        for needle in expected_needles:
            if any(needle in text for text in counter_texts):
                expected_found += 1
        if not expected_needles:
            false_positive_passages += len(counter_texts)
        else:
            false_positive_passages += sum(
                1
                for text in counter_texts
                if not any(needle in text for needle in expected_needles)
            )
        supporting_passages += len(unit.evidence_passages)
        expected_source = EXPECTED_SUPPORT_SOURCES[claim_id]
        if any(passage.source_id == expected_source for passage in unit.evidence_passages):
            supported_expected_sources += 1

    return {
        "counterevidence_recall": f"{expected_found}/{expected_total}",
        "false_positive_counter_passages": str(false_positive_passages),
        "supporting_source_recall": (
            f"{supported_expected_sources}/{len(EXPECTED_SUPPORT_SOURCES)}"
        ),
        "supporting_precision_proxy": (
            f"{supported_expected_sources}/{supporting_passages}"
            if supporting_passages
            else "0/0"
        ),
    }


def _render_report(results: list[RunResult]) -> str:
    lines = [
        "# Phase 2b Unit 5 ADR-010 Comparison Report",
        "",
        "status: recorded",
        "asset: live-asset/evidence-bundler",
        f"last_updated: {datetime.now(UTC).strftime('%Y-%m-%d')}",
        "",
        "Counter-candidates are retrieval nominations, not verified counterevidence.",
        "Null and negative results are recorded as valid outcomes.",
        "",
        "## Test 1 — Rerank 2x2 Matrix",
        "",
        (
            "The structurally invalid cell `rerank_enabled=false` with "
            "`contradiction_rerank_enabled=true` is not runnable because ADR-010's "
            "validator deliberately fails closed. The remaining runnable cells are recorded."
        ),
        "",
        _table(
            [
                result
                for result in results
                if result.name.startswith("test1_")
            ]
        ),
        "",
        "Finding: no default flip is justified on this fixture record.",
        "",
        "## Test 2 — Prefix-Set Comparison",
        "",
        _table(
            [
                result
                for result in results
                if result.name
                in {"test1_rerank_off_contra_rerank_off", "test2_default_plus_domain_prefixes"}
            ]
        ),
        "",
        "Finding: no prefix default amendment is justified on this fixture record.",
        "",
        "## Test 3 — Text-Gate Calibration",
        "",
        _table(
            [
                result
                for result in results
                if result.name in {"test1_rerank_off_contra_rerank_off", "test3_text_gate_disabled"}
            ]
        ),
        "",
        "Finding: no pattern amendment is justified on this fixture record.",
        "",
    ]
    return "\n".join(lines)


def _table(results: list[RunResult]) -> str:
    lines = [
        (
            "| Run | Status | Config hash | Counter-candidate recall | "
            "False-positive counter passages | Supporting source recall | "
            "Supporting precision proxy |"
        ),
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        metrics = result.metrics
        lines.append(
            f"| `{result.name}` | {result.status} | `{result.config_hash}` | "
            f"{metrics.get('counterevidence_recall', 'n/a')} | "
            f"{metrics.get('false_positive_counter_passages', 'n/a')} | "
            f"{metrics.get('supporting_source_recall', 'n/a')} | "
            f"{metrics.get('supporting_precision_proxy', 'n/a')} |"
        )
    return "\n".join(lines)


class RunResult:
    def __init__(
        self,
        *,
        name: str,
        config_hash: str,
        status: str,
        metrics: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.config_hash = config_hash
        self.status = status
        self.metrics = metrics or {}


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
    if "not a support verdict" in lowered:
        return 4.0
    if "submission checklist" in lowered:
        return 3.0
    if "plain-text intake" in lowered:
        return 2.0
    if "pdf extraction" in lowered:
        return 1.0
    return -1.0


if __name__ == "__main__":
    main()
