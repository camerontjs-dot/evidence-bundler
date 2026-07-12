"""Report helpers for Evidence Bundler."""

from evidence_bundler.reports.coverage import (
    CoverageReport,
    CoverageReportError,
    build_coverage_report,
    render_coverage_report_markdown,
    write_coverage_report_json,
    write_coverage_report_markdown,
)
from evidence_bundler.reports.retrieval_comparison import (
    ComparisonRunResult,
    ComparisonSuiteResult,
    FixtureExpectations,
    score_claim_units,
)

__all__ = [
    "ComparisonRunResult",
    "ComparisonSuiteResult",
    "CoverageReport",
    "CoverageReportError",
    "FixtureExpectations",
    "build_coverage_report",
    "render_coverage_report_markdown",
    "score_claim_units",
    "write_coverage_report_json",
    "write_coverage_report_markdown",
]
