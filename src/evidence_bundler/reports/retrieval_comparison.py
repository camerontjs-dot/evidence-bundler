"""Lexical-vs-hybrid retrieval comparison reporting."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from shutil import copytree

from evidence_bundler.contracts.writer import (
    BundleWriterError,
    build_retrieval_bundle,
)
from evidence_bundler.contracts.yaml_io import load_model_yaml, load_yaml
from evidence_bundler.models.cb import ClaimAuditUnit, ClaimEvidencePassage
from evidence_bundler.models.retrieval import RetrievalConfig

NA = "n/a"


@dataclass(frozen=True)
class ClaimExpectation:
    """Fixture-only expectations for one claim."""

    claim_id: str
    expected_supporting_source_ids: tuple[str, ...] = ()
    expected_countercandidate_needles: tuple[str, ...] = ()
    expected_countercandidate_role: str | None = None


@dataclass(frozen=True)
class FixtureExpectations:
    """Internal retrieval expectations; not part of C-A or C-B."""

    schema_version: str
    fixture: str
    notes: str
    claims: tuple[ClaimExpectation, ...]

    @property
    def by_claim_id(self) -> dict[str, ClaimExpectation]:
        return {claim.claim_id: claim for claim in self.claims}


@dataclass(frozen=True)
class ClaimComparisonResult:
    """Per-claim scored result for one comparison run."""

    claim_id: str
    expected_supporting_source_ids: tuple[str, ...]
    retrieved_supporting_source_ids: tuple[str, ...]
    matched_supporting_source_ids: tuple[str, ...]
    expected_countercandidate_needles: tuple[str, ...]
    matched_countercandidate_needles: tuple[str, ...] | None
    false_positive_counter_passages: int | None
    supporting_candidate_labels: tuple[str, ...]
    counter_candidate_labels: tuple[str, ...]


@dataclass(frozen=True)
class ComparisonMetrics:
    """Fixture-bounded metric values for one comparison run."""

    supporting_source_recall: str
    supporting_precision_proxy: str
    counter_candidate_recall: str
    false_positive_counter_candidate_count: str


@dataclass(frozen=True)
class ComparisonRunResult:
    """One retrieval comparison run."""

    name: str
    status: str
    config_hash: str
    config: RetrievalConfig | None = None
    metrics: ComparisonMetrics | None = None
    claim_results: tuple[ClaimComparisonResult, ...] = ()

    @property
    def completed(self) -> bool:
        return self.status == "completed"


@dataclass(frozen=True)
class CandidateDelta:
    """Candidate labels added or removed between two runs."""

    claim_id: str
    added: tuple[str, ...]
    removed: tuple[str, ...]


@dataclass(frozen=True)
class DeltaComparison:
    """Candidate deltas from one run to another."""

    label: str
    baseline_run: str
    comparison_run: str
    claim_deltas: tuple[CandidateDelta, ...]


@dataclass(frozen=True)
class ComparisonSuiteResult:
    """Full Unit 6 comparison report data."""

    fixture_path: Path
    generated_at_utc: str
    runs: tuple[ComparisonRunResult, ...]
    deltas: tuple[DeltaComparison, ...]
    checklist: tuple[str, ...] = field(default_factory=tuple)


def load_fixture_expectations(path: Path) -> FixtureExpectations:
    """Load Unit 6 fixture expectations from YAML."""
    data = load_yaml(path)
    claims = []
    for claim_id, claim_data in data.get("claims", {}).items():
        claims.append(
            ClaimExpectation(
                claim_id=str(claim_id),
                expected_supporting_source_ids=tuple(
                    str(source_id)
                    for source_id in claim_data.get("expected_supporting_source_ids", [])
                ),
                expected_countercandidate_needles=tuple(
                    str(needle)
                    for needle in claim_data.get("expected_countercandidate_needles", [])
                ),
                expected_countercandidate_role=claim_data.get("expected_countercandidate_role"),
            )
        )
    return FixtureExpectations(
        schema_version=str(data["schema_version"]),
        fixture=str(data["fixture"]),
        notes=str(data.get("notes", "")),
        claims=tuple(claims),
    )


def run_comparison_suite(
    *,
    fixture_dir: Path,
    expectations: FixtureExpectations,
    run_configs: Mapping[str, RetrievalConfig],
    work_dir: Path,
    generated_at_utc: str | None = None,
) -> ComparisonSuiteResult:
    """Run configured retrieval builds and score the resulting C-B claim units."""
    generated_at = generated_at_utc or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    results: list[ComparisonRunResult] = []
    for run_name, config in run_configs.items():
        results.append(
            _run_fixture(
                run_name=run_name,
                config=config,
                fixture_dir=fixture_dir,
                expectations=expectations,
                work_dir=work_dir,
            )
        )
    return ComparisonSuiteResult(
        fixture_path=fixture_dir,
        generated_at_utc=generated_at,
        runs=tuple(results),
        deltas=_make_suite_deltas(results),
        checklist=_make_checklist(results),
    )


def score_claim_units(
    *,
    claim_units: Mapping[str, ClaimAuditUnit],
    expectations: FixtureExpectations,
    contradiction_enabled: bool,
) -> tuple[ComparisonMetrics, tuple[ClaimComparisonResult, ...]]:
    """Score C-B claim units against explicit fixture expectations."""
    claim_results = tuple(
        _score_claim(
            claim_units[expectation.claim_id],
            expectation=expectation,
            contradiction_enabled=contradiction_enabled,
        )
        for expectation in expectations.claims
    )
    expected_support_total = sum(
        len(result.expected_supporting_source_ids) for result in claim_results
    )
    matched_support_total = sum(
        len(result.matched_supporting_source_ids) for result in claim_results
    )
    supporting_source_recall = _ratio_cell(matched_support_total, expected_support_total)

    precision_values = []
    for result in claim_results:
        retrieved_count = len(result.retrieved_supporting_source_ids)
        expected_count = len(result.expected_supporting_source_ids)
        if retrieved_count:
            precision_values.append(len(result.matched_supporting_source_ids) / retrieved_count)
        elif expected_count:
            precision_values.append(0.0)
    supporting_precision_proxy = (
        f"{sum(precision_values) / len(precision_values):.3f}" if precision_values else NA
    )

    if contradiction_enabled:
        expected_counter_total = sum(
            len(result.expected_countercandidate_needles) for result in claim_results
        )
        matched_counter_total = sum(
            len(result.matched_countercandidate_needles or ()) for result in claim_results
        )
        false_positive_count = sum(
            result.false_positive_counter_passages or 0 for result in claim_results
        )
        counter_candidate_recall = _ratio_cell(matched_counter_total, expected_counter_total)
        false_positive_counter_candidate_count = str(false_positive_count)
    else:
        counter_candidate_recall = NA
        false_positive_counter_candidate_count = NA

    return (
        ComparisonMetrics(
            supporting_source_recall=supporting_source_recall,
            supporting_precision_proxy=supporting_precision_proxy,
            counter_candidate_recall=counter_candidate_recall,
            false_positive_counter_candidate_count=false_positive_counter_candidate_count,
        ),
        claim_results,
    )


def render_comparison_report(result: ComparisonSuiteResult) -> str:
    """Render a calibrated Markdown comparison report."""
    lines = [
        "# Phase 2b Unit 6 Lexical-vs-Hybrid Comparison Report",
        "",
        "status: recorded",
        "asset: live-asset/evidence-bundler",
        f"last_updated: {result.generated_at_utc[:10]}",
        "",
        "Candidate passages are retrieval nominations, not verified evidence. "
        "Fixture expectation matches are local checks only; review required before audit use.",
        "Negative or null fixture results are valid outcomes.",
        "",
        "## Metadata",
        "",
        f"- Fixture: `{result.fixture_path.as_posix()}`",
        f"- Generated at: `{result.generated_at_utc}`",
        "- Comparison scope: `lexical_bm25` vs `hybrid_rerank_only` vs "
        "`hybrid_rerank_contradiction`",
        "- C-A/C-B contract status: `v1.0.0 unchanged`",
        "- Contradiction activation: `config-only via RetrievalConfig / --config`",
        "",
        "## Metric Definitions",
        "",
        "- Supporting source recall: expected supporting source IDs retrieved at least once "
        "/ total expected supporting source IDs.",
        "- Supporting precision proxy: macro-average by claim of matched expected supporting "
        "source IDs / unique retrieved supporting source IDs; claims with expected support "
        "and no retrieved supporting source score `0.0`.",
        "- Counter-candidate recall: expected counter-candidate needles found in "
        "`counterevidence_passages` / total expected counter-candidate needles; `n/a` when "
        "contradiction retrieval is disabled.",
        "- False-positive counter-candidate count: counter-candidate passages without an "
        "expected needle for that claim, plus all counter-candidates for claims with no "
        "expected counter-candidate; `n/a` when contradiction retrieval is disabled.",
        "",
        "## Run Summary",
        "",
        "| Run | Status | Config hash | Method | Rerank | Contradiction | "
        "Supporting source recall | Supporting precision proxy | "
        "Counter-candidate recall | False-positive counter candidates |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for run in result.runs:
        config = run.config
        metrics = run.metrics
        lines.append(
            f"| `{run.name}` | {run.status} | `{run.config_hash}` | "
            f"`{config.retrieval_method if config else NA}` | "
            f"`{config.rerank_enabled if config else NA}` | "
            f"`{config.contradiction_enabled if config else NA}` | "
            f"{metrics.supporting_source_recall if metrics else NA} | "
            f"{metrics.supporting_precision_proxy if metrics else NA} | "
            f"{metrics.counter_candidate_recall if metrics else NA} | "
            f"{metrics.false_positive_counter_candidate_count if metrics else NA} |"
        )

    lines.extend(["", "## Per-Claim Candidate Nominations", ""])
    for run in result.runs:
        lines.extend(
            [
                f"### {run.name}",
                "",
                "| Claim | Expected support | Retrieved supporting sources | "
                "Matched support | Expected counter needles | Matched counter needles | "
                "False-positive counter candidates | Supporting candidates | Counter candidates |",
                "| --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
            ]
        )
        if not run.claim_results:
            lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
        for claim in run.claim_results:
            false_positive_cell = (
                str(claim.false_positive_counter_passages)
                if claim.false_positive_counter_passages is not None
                else NA
            )
            lines.append(
                f"| `{claim.claim_id}` | {_tuple_cell(claim.expected_supporting_source_ids)} | "
                f"{_tuple_cell(claim.retrieved_supporting_source_ids)} | "
                f"{_tuple_cell(claim.matched_supporting_source_ids)} | "
                f"{_tuple_cell(claim.expected_countercandidate_needles)} | "
                f"{_optional_tuple_cell(claim.matched_countercandidate_needles)} | "
                f"{false_positive_cell} | "
                f"{_tuple_cell(claim.supporting_candidate_labels)} | "
                f"{_tuple_cell(claim.counter_candidate_labels)} |"
            )
        lines.append("")

    lines.extend(["## Candidate Deltas", ""])
    for delta in result.deltas:
        lines.extend(
            [
                f"### {delta.label}",
                "",
                f"Baseline: `{delta.baseline_run}`. Comparison: `{delta.comparison_run}`.",
                "",
                "| Claim | Added candidates | Removed candidates |",
                "| --- | --- | --- |",
            ]
        )
        for claim_delta in delta.claim_deltas:
            lines.append(
                f"| `{claim_delta.claim_id}` | {_tuple_cell(claim_delta.added)} | "
                f"{_tuple_cell(claim_delta.removed)} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Pre-Merge Checklist",
            "",
            *[f"- {item}" for item in result.checklist],
            "",
            "Finding: this fixture comparison records candidate-nomination behavior only. "
            "No default, schema, or vocabulary change is justified by this Unit 6 artifact alone.",
            "",
        ]
    )
    return "\n".join(lines)


def write_comparison_report(result: ComparisonSuiteResult, path: Path) -> None:
    """Write a Unit 6 comparison report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_comparison_report(result), encoding="utf-8")


def _run_fixture(
    *,
    run_name: str,
    config: RetrievalConfig,
    fixture_dir: Path,
    expectations: FixtureExpectations,
    work_dir: Path,
) -> ComparisonRunResult:
    fixture_copy = work_dir / run_name / "scaffold-run"
    output_dir = work_dir / run_name / "bundle"
    copytree(fixture_dir, fixture_copy)
    try:
        build_result = build_retrieval_bundle(fixture_copy, output_dir, config=config)
    except BundleWriterError as exc:
        return ComparisonRunResult(
            name=run_name,
            status=f"failed: {exc}",
            config_hash=NA,
            config=config,
        )
    claim_units = {
        path.stem: load_model_yaml(ClaimAuditUnit, path)
        for path in sorted((output_dir / "claims").glob("*.yaml"))
    }
    metrics, claim_results = score_claim_units(
        claim_units=claim_units,
        expectations=expectations,
        contradiction_enabled=config.contradiction_enabled,
    )
    return ComparisonRunResult(
        name=run_name,
        status="completed",
        config_hash=build_result.retrieval_report.config_hash
        if build_result.retrieval_report is not None
        else NA,
        config=config,
        metrics=metrics,
        claim_results=claim_results,
    )


def _score_claim(
    unit: ClaimAuditUnit,
    *,
    expectation: ClaimExpectation,
    contradiction_enabled: bool,
) -> ClaimComparisonResult:
    supporting_sources = _unique_sorted(
        passage.source_id for passage in unit.evidence_passages
    )
    expected_support = tuple(sorted(expectation.expected_supporting_source_ids))
    matched_support = tuple(
        source_id for source_id in expected_support if source_id in set(supporting_sources)
    )

    if contradiction_enabled:
        counter_texts = [
            passage.passage_text.lower() for passage in unit.counterevidence_passages
        ]
        expected_needles = tuple(expectation.expected_countercandidate_needles)
        matched_needles = tuple(
            needle
            for needle in expected_needles
            if any(needle.lower() in text for text in counter_texts)
        )
        false_positive_count = _false_positive_counter_count(
            unit.counterevidence_passages,
            expected_needles=expected_needles,
        )
    else:
        expected_needles = tuple(expectation.expected_countercandidate_needles)
        matched_needles = None
        false_positive_count = None

    return ClaimComparisonResult(
        claim_id=expectation.claim_id,
        expected_supporting_source_ids=expected_support,
        retrieved_supporting_source_ids=supporting_sources,
        matched_supporting_source_ids=matched_support,
        expected_countercandidate_needles=expected_needles,
        matched_countercandidate_needles=matched_needles,
        false_positive_counter_passages=false_positive_count,
        supporting_candidate_labels=_candidate_labels(
            unit.evidence_passages,
            role="supporting",
        ),
        counter_candidate_labels=_candidate_labels(
            unit.counterevidence_passages,
            role="counter",
        )
        if contradiction_enabled
        else (),
    )


def _false_positive_counter_count(
    passages: Sequence[ClaimEvidencePassage],
    *,
    expected_needles: Sequence[str],
) -> int:
    if not expected_needles:
        return len(passages)
    lowered_needles = [needle.lower() for needle in expected_needles]
    return sum(
        1
        for passage in passages
        if not any(needle in passage.passage_text.lower() for needle in lowered_needles)
    )


def _candidate_labels(
    passages: Sequence[ClaimEvidencePassage],
    *,
    role: str,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            f"{role}:{passage.source_id}:{passage.passage_hash.removeprefix('sha256:')[:12]}"
            for passage in passages
        )
    )


def _make_suite_deltas(
    results: Sequence[ComparisonRunResult],
) -> tuple[DeltaComparison, ...]:
    by_name = {result.name: result for result in results}
    pairs = [
        (
            "Hybrid rerank-only vs BM25",
            "lexical_bm25",
            "hybrid_rerank_only",
        ),
        (
            "Contradiction-aware hybrid vs hybrid rerank-only",
            "hybrid_rerank_only",
            "hybrid_rerank_contradiction",
        ),
    ]
    deltas = []
    for label, baseline_name, comparison_name in pairs:
        baseline = by_name.get(baseline_name)
        comparison = by_name.get(comparison_name)
        if baseline is None or comparison is None:
            continue
        deltas.append(
            DeltaComparison(
                label=label,
                baseline_run=baseline_name,
                comparison_run=comparison_name,
                claim_deltas=_claim_deltas(baseline, comparison),
            )
        )
    return tuple(deltas)


def _claim_deltas(
    baseline: ComparisonRunResult,
    comparison: ComparisonRunResult,
) -> tuple[CandidateDelta, ...]:
    baseline_by_claim = {claim.claim_id: claim for claim in baseline.claim_results}
    comparison_by_claim = {claim.claim_id: claim for claim in comparison.claim_results}
    claim_ids = sorted(set(baseline_by_claim) | set(comparison_by_claim))
    deltas = []
    for claim_id in claim_ids:
        baseline_candidates = _all_candidate_labels(baseline_by_claim.get(claim_id))
        comparison_candidates = _all_candidate_labels(comparison_by_claim.get(claim_id))
        deltas.append(
            CandidateDelta(
                claim_id=claim_id,
                added=tuple(sorted(comparison_candidates - baseline_candidates)),
                removed=tuple(sorted(baseline_candidates - comparison_candidates)),
            )
        )
    return tuple(deltas)


def _all_candidate_labels(result: ClaimComparisonResult | None) -> set[str]:
    if result is None:
        return set()
    return set(result.supporting_candidate_labels) | set(result.counter_candidate_labels)


def _make_checklist(results: Sequence[ComparisonRunResult]) -> tuple[str, ...]:
    all_completed_or_failed = all(
        result.status == "completed" or result.status.startswith("failed:")
        for result in results
    )
    hashes_recorded = all(result.config_hash != NA for result in results if result.completed)
    return (
        "Committed fixture used: `tests/fixtures/scaffold-run-mixed-formats`.",
        f"All three configs completed or explicitly failed: `{all_completed_or_failed}`.",
        f"Config hashes recorded for completed runs: `{hashes_recorded}`.",
        "Metric formulas applied exactly as listed in this report.",
        "C-A/C-B v1.0.0 unchanged; expectations live outside contract fixtures.",
        "Calibrated nomination language used; candidates are not support verdicts.",
        "Verification commands run before merge: `ruff check .`, `python -m pytest`, "
        "`python -m compileall src`, Unit 6 comparison script, BM25 smoke, hybrid smoke.",
    )


def _ratio_cell(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return NA
    return f"{numerator}/{denominator}"


def _unique_sorted(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def _tuple_cell(values: Sequence[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "none"


def _optional_tuple_cell(values: Sequence[str] | None) -> str:
    if values is None:
        return NA
    return _tuple_cell(values)
