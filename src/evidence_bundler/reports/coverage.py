"""Read-only coverage reporting for reviewed bundle finalization."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field

from evidence_bundler.contracts.hashing import compute_bundle_tree_hash
from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.cb import BundleManifest, ClaimAuditUnit, PassageRecord
from evidence_bundler.models.common import HashValue, NonBlankStr, StrictBaseModel
from evidence_bundler.models.refinement import ExcerptCluster, ExcerptRefinementMember
from evidence_bundler.models.retrieval import EvidenceRole
from evidence_bundler.models.review import ReviewAnnotation, ReviewDecision
from evidence_bundler.output.finalizer import (
    FinalizeProvenanceFile,
    compute_excerpt_refinement_hash,
)
from evidence_bundler.output.refiner import load_excerpt_refinement
from evidence_bundler.review.io import (
    compute_review_annotations_hash,
    load_review_annotations,
)

REVIEW_DECISIONS: tuple[ReviewDecision, ...] = (
    "accepted",
    "rejected",
    "needs-review",
    "insufficient-excerpt",
)
EVIDENCE_ROLES: tuple[EvidenceRole, ...] = (
    "supporting",
    "contradicting",
    "conditional",
    "insufficient",
)

CoverageSeverity = Literal["warning", "error"]


class CoverageReportError(ValueError):
    """Raised when coverage reporting cannot safely read its input anchors."""


class CoverageInconsistency(StrictBaseModel):
    """Structured report finding for downstream parsing."""

    code: NonBlankStr
    severity: CoverageSeverity
    message: NonBlankStr
    refs: list[NonBlankStr] = Field(default_factory=list)


class CoverageAnchors(StrictBaseModel):
    """Hash chain tying a coverage report to exact input artifacts."""

    draft_bundle_id: NonBlankStr
    draft_bundle_hash: HashValue
    review_annotations_hash: HashValue
    excerpt_refinement_hash: HashValue
    final_bundle_id: NonBlankStr
    final_bundle_hash: HashValue


class DecisionCoverageRow(StrictBaseModel):
    """Coverage counts for one review decision."""

    decision: NonBlankStr
    total: int = Field(ge=0)
    by_role: dict[NonBlankStr, int] = Field(default_factory=dict)


class NominationGapCoverage(StrictBaseModel):
    """Claim-level nomination gap categories observed in the draft bundle."""

    no_candidate_claim_ids: list[NonBlankStr] = Field(default_factory=list)
    no_supporting_candidate_claim_ids: list[NonBlankStr] = Field(default_factory=list)
    no_counterevidence_candidate_claim_ids: list[NonBlankStr] = Field(default_factory=list)
    skipped_claim_count: int = Field(ge=0)
    skipped_claim_ids_available: bool = False
    exclusion_rationale: str


class RefinementConflictCluster(StrictBaseModel):
    """Mixed-decision near-duplicate cluster surfaced for review traceability."""

    cluster_id: NonBlankStr
    claim_id: NonBlankStr
    source_id: NonBlankStr
    evidence_role: NonBlankStr
    representative: NonBlankStr
    member_decisions: list[NonBlankStr] = Field(default_factory=list)
    members: list[NonBlankStr] = Field(default_factory=list)


class RefinementCoverage(StrictBaseModel):
    """Coverage details from excerpt refinement."""

    cluster_count: int = Field(ge=0)
    suppressed_non_representative_count: int = Field(ge=0)
    cluster_size_distribution: dict[NonBlankStr, int] = Field(default_factory=dict)
    conflict_clusters: list[RefinementConflictCluster] = Field(default_factory=list)


class FinalBundleCoverage(StrictBaseModel):
    """Observed final reviewed C-B bundle counts."""

    claim_file_count: int = Field(ge=0)
    evidence_passage_refs: int = Field(ge=0)
    counterevidence_passage_refs: int = Field(ge=0)
    unique_passage_records: int = Field(ge=0)
    manifest_total_evidence_passages: int = Field(ge=0)
    reviewer_sign_off_required: bool


class CoverageReport(StrictBaseModel):
    """Single source model for Markdown and JSON coverage reports."""

    schema_version: NonBlankStr = "coverage-report-v1"
    report_generated_at_utc: NonBlankStr
    anchors: CoverageAnchors
    decision_coverage: list[DecisionCoverageRow] = Field(default_factory=list)
    nomination_gaps: NominationGapCoverage
    refinement: RefinementCoverage
    final_bundle: FinalBundleCoverage
    inconsistencies: list[CoverageInconsistency] = Field(default_factory=list)


def build_coverage_report(
    draft_bundle_dir: Path,
    annotation_path: Path,
    refinement_path: Path,
    final_bundle_dir: Path,
    provenance_path: Path,
    *,
    generated_at_utc: str | None = None,
) -> CoverageReport:
    """Build a read-only coverage report from finalized review artifacts."""
    draft_bundle_dir = draft_bundle_dir.resolve()
    annotation_path = annotation_path.resolve()
    refinement_path = refinement_path.resolve()
    final_bundle_dir = final_bundle_dir.resolve()
    provenance_path = provenance_path.resolve()

    draft_manifest = _load_manifest(draft_bundle_dir)
    final_manifest = _load_manifest(final_bundle_dir)
    annotations = load_review_annotations(annotation_path, draft_bundle_dir)
    refinement = load_excerpt_refinement(refinement_path, draft_bundle_dir, annotation_path)
    provenance = load_model_yaml(FinalizeProvenanceFile, provenance_path)

    draft_hash = compute_bundle_tree_hash(draft_bundle_dir)
    annotation_hash = compute_review_annotations_hash(annotation_path)
    refinement_hash = compute_excerpt_refinement_hash(refinement_path)
    final_hash = compute_bundle_tree_hash(final_bundle_dir)
    _validate_provenance_chain(
        provenance=provenance,
        draft_manifest=draft_manifest,
        final_manifest=final_manifest,
        draft_hash=draft_hash,
        annotation_hash=annotation_hash,
        refinement_hash=refinement_hash,
        final_hash=final_hash,
    )

    draft_claims = _load_claims(draft_bundle_dir)
    final_claims = _load_claims(final_bundle_dir)
    final_passage_records = _load_passage_records(final_bundle_dir)
    inconsistencies = _collect_inconsistencies(
        annotations=annotations.annotations,
        refinement_clusters=refinement.clusters,
        draft_claims=draft_claims,
        final_claims=final_claims,
        final_passage_records=final_passage_records,
        final_manifest=final_manifest,
        final_hash=final_hash,
    )

    return CoverageReport(
        report_generated_at_utc=generated_at_utc or _utc_now(),
        anchors=CoverageAnchors(
            draft_bundle_id=draft_manifest.bundle_id,
            draft_bundle_hash=draft_hash,
            review_annotations_hash=annotation_hash,
            excerpt_refinement_hash=refinement_hash,
            final_bundle_id=final_manifest.bundle_id,
            final_bundle_hash=final_hash,
        ),
        decision_coverage=_decision_coverage(annotations.annotations),
        nomination_gaps=_nomination_gaps(draft_manifest, draft_claims),
        refinement=_refinement_coverage(refinement.clusters),
        final_bundle=_final_bundle_coverage(
            final_manifest=final_manifest,
            final_claims=final_claims,
            final_passage_records=final_passage_records,
        ),
        inconsistencies=inconsistencies,
    )


def write_coverage_report_markdown(report: CoverageReport, path: Path) -> None:
    """Write a Markdown coverage report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_coverage_report_markdown(report), encoding="utf-8")


def write_coverage_report_json(report: CoverageReport, path: Path) -> None:
    """Write a JSON coverage report from the same report model as Markdown."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")


def render_coverage_report_markdown(report: CoverageReport) -> str:
    """Render a calibrated Markdown review coverage report."""
    lines = [
        "# Review Coverage Report",
        "",
        "Candidate passages are review nominations, not support determinations. "
        "This report summarizes review coverage and final-bundle observations only.",
        "",
        "## Anchors",
        "",
        f"- Generated at: `{report.report_generated_at_utc}`",
        f"- Draft bundle id: `{report.anchors.draft_bundle_id}`",
        f"- Draft bundle hash: `{report.anchors.draft_bundle_hash}`",
        f"- Review annotations hash: `{report.anchors.review_annotations_hash}`",
        f"- Excerpt refinement hash: `{report.anchors.excerpt_refinement_hash}`",
        f"- Final bundle id: `{report.anchors.final_bundle_id}`",
        f"- Final bundle hash: `{report.anchors.final_bundle_hash}`",
        "",
        "## Review Decisions",
        "",
        "| Decision | Total | Supporting | Contradicting | Conditional | Insufficient role |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report.decision_coverage:
        lines.append(
            f"| `{row.decision}` | {row.total} | "
            f"{row.by_role.get('supporting', 0)} | "
            f"{row.by_role.get('contradicting', 0)} | "
            f"{row.by_role.get('conditional', 0)} | "
            f"{row.by_role.get('insufficient', 0)} |"
        )

    gaps = report.nomination_gaps
    lines.extend(
        [
            "",
            "## Nomination Gaps",
            "",
            f"- No candidate claims: {_ids_cell(gaps.no_candidate_claim_ids)}",
            f"- No supporting-candidate claims: "
            f"{_ids_cell(gaps.no_supporting_candidate_claim_ids)}",
            f"- No counterevidence-candidate claims: "
            f"{_ids_cell(gaps.no_counterevidence_candidate_claim_ids)}",
            f"- Skipped claims count: `{gaps.skipped_claim_count}`",
            f"- Skipped claim IDs available: `{gaps.skipped_claim_ids_available}`",
            f"- Exclusion rationale: `{gaps.exclusion_rationale}`",
            "",
            "## Refinement",
            "",
            f"- Clusters: `{report.refinement.cluster_count}`",
            "- Suppressed non-representatives: "
            f"`{report.refinement.suppressed_non_representative_count}`",
            "- Cluster size distribution: "
            f"`{_dict_cell(report.refinement.cluster_size_distribution)}`",
            f"- Conflict clusters: `{len(report.refinement.conflict_clusters)}`",
        ]
    )
    if report.refinement.conflict_clusters:
        lines.extend(
            [
                "",
                "| Cluster | Claim | Source | Role | Representative | Decisions | Members |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for cluster in report.refinement.conflict_clusters:
            lines.append(
                f"| `{cluster.cluster_id}` | `{cluster.claim_id}` | "
                f"`{cluster.source_id}` | `{cluster.evidence_role}` | "
                f"`{cluster.representative}` | {_ids_cell(cluster.member_decisions)} | "
                f"{_ids_cell(cluster.members)} |"
            )

    final = report.final_bundle
    lines.extend(
        [
            "",
            "## Final Bundle Observations",
            "",
            f"- Claim files: `{final.claim_file_count}`",
            f"- Evidence passage references: `{final.evidence_passage_refs}`",
            f"- Counterevidence passage references: `{final.counterevidence_passage_refs}`",
            f"- Unique passage records: `{final.unique_passage_records}`",
            "- Manifest total evidence passages: "
            f"`{final.manifest_total_evidence_passages}`",
            f"- Reviewer sign-off required: `{final.reviewer_sign_off_required}`",
            "",
            "## Inconsistencies",
            "",
        ]
    )
    if not report.inconsistencies:
        lines.append("none")
    else:
        lines.extend(["| Severity | Code | Message | Refs |", "| --- | --- | --- | --- |"])
        for finding in report.inconsistencies:
            lines.append(
                f"| `{finding.severity}` | `{finding.code}` | "
                f"{finding.message} | {_ids_cell(finding.refs)} |"
            )
    lines.append("")
    return "\n".join(lines)


def _validate_provenance_chain(
    *,
    provenance: FinalizeProvenanceFile,
    draft_manifest: BundleManifest,
    final_manifest: BundleManifest,
    draft_hash: str,
    annotation_hash: str,
    refinement_hash: str,
    final_hash: str,
) -> None:
    checks = [
        ("draft bundle id", provenance.draft_bundle_id, draft_manifest.bundle_id),
        ("draft bundle hash", provenance.draft_bundle_hash, draft_hash),
        ("review annotations hash", provenance.annotation_hash, annotation_hash),
        ("excerpt refinement hash", provenance.refinement_hash, refinement_hash),
        ("final bundle id", provenance.final_bundle_id, final_manifest.bundle_id),
        ("final bundle hash", provenance.final_bundle_hash, final_hash),
        ("final manifest bundle hash", final_manifest.bundle.bundle_hash, final_hash),
    ]
    for label, recorded, actual in checks:
        if recorded != actual:
            raise CoverageReportError(
                f"{label} mismatch: provenance={recorded!r} actual={actual!r}"
            )


def _decision_coverage(annotations: list[ReviewAnnotation]) -> list[DecisionCoverageRow]:
    by_decision = Counter(annotation.decision for annotation in annotations)
    by_decision_role = Counter(
        (annotation.decision, annotation.evidence_role) for annotation in annotations
    )
    rows = []
    for decision in REVIEW_DECISIONS:
        rows.append(
            DecisionCoverageRow(
                decision=decision,
                total=by_decision.get(decision, 0),
                by_role={
                    role: by_decision_role.get((decision, role), 0)
                    for role in EVIDENCE_ROLES
                },
            )
        )
    return rows


def _nomination_gaps(
    draft_manifest: BundleManifest,
    draft_claims: dict[str, ClaimAuditUnit],
) -> NominationGapCoverage:
    return NominationGapCoverage(
        no_candidate_claim_ids=[
            claim_id
            for claim_id, claim in sorted(draft_claims.items())
            if not claim.evidence_passages and not claim.counterevidence_passages
        ],
        no_supporting_candidate_claim_ids=[
            claim_id
            for claim_id, claim in sorted(draft_claims.items())
            if not claim.evidence_passages
        ],
        no_counterevidence_candidate_claim_ids=[
            claim_id
            for claim_id, claim in sorted(draft_claims.items())
            if not claim.counterevidence_passages
        ],
        skipped_claim_count=draft_manifest.bundle.claims_excluded,
        exclusion_rationale=draft_manifest.bundle.exclusion_rationale,
    )


def _refinement_coverage(clusters: list[ExcerptCluster]) -> RefinementCoverage:
    sizes = Counter(len(cluster.members) for cluster in clusters)
    return RefinementCoverage(
        cluster_count=len(clusters),
        suppressed_non_representative_count=sum(
            max(len(cluster.members) - 1, 0) for cluster in clusters
        ),
        cluster_size_distribution={
            str(size): sizes[size] for size in sorted(sizes)
        },
        conflict_clusters=[
            RefinementConflictCluster(
                cluster_id=cluster.cluster_id,
                claim_id=cluster.claim_id,
                source_id=cluster.source_id,
                evidence_role=cluster.evidence_role,
                representative=_member_ref(cluster.representative),
                member_decisions=list(cluster.member_decisions),
                members=[_member_ref(member) for member in cluster.members],
            )
            for cluster in clusters
            if cluster.decision_conflict
        ],
    )


def _final_bundle_coverage(
    *,
    final_manifest: BundleManifest,
    final_claims: dict[str, ClaimAuditUnit],
    final_passage_records: dict[tuple[str, str], PassageRecord],
) -> FinalBundleCoverage:
    return FinalBundleCoverage(
        claim_file_count=len(final_claims),
        evidence_passage_refs=sum(len(claim.evidence_passages) for claim in final_claims.values()),
        counterevidence_passage_refs=sum(
            len(claim.counterevidence_passages) for claim in final_claims.values()
        ),
        unique_passage_records=len(final_passage_records),
        manifest_total_evidence_passages=final_manifest.bundle.total_evidence_passages,
        reviewer_sign_off_required=final_manifest.reviewer_sign_off.required,
    )


def _collect_inconsistencies(
    *,
    annotations: list[ReviewAnnotation],
    refinement_clusters: list[ExcerptCluster],
    draft_claims: dict[str, ClaimAuditUnit],
    final_claims: dict[str, ClaimAuditUnit],
    final_passage_records: dict[tuple[str, str], PassageRecord],
    final_manifest: BundleManifest,
    final_hash: str,
) -> list[CoverageInconsistency]:
    findings: list[CoverageInconsistency] = []
    insufficient_role_count = sum(
        1 for annotation in annotations if annotation.evidence_role == "insufficient"
    )
    if insufficient_role_count:
        findings.append(
            CoverageInconsistency(
                code="insufficient-role-annotations",
                severity="warning",
                message=(
                    "Review annotations include evidence_role='insufficient', which is "
                    "schema-valid but not expected from C-B claim files."
                ),
                refs=[str(insufficient_role_count)],
            )
        )
    conflict_ids = [
        cluster.cluster_id for cluster in refinement_clusters if cluster.decision_conflict
    ]
    if conflict_ids:
        findings.append(
            CoverageInconsistency(
                code="refinement-decision-conflicts",
                severity="warning",
                message="Near-identical excerpt clusters contain mixed review decisions.",
                refs=conflict_ids,
            )
        )

    draft_ids = set(draft_claims)
    final_ids = set(final_claims)
    missing_final = sorted(draft_ids - final_ids)
    extra_final = sorted(final_ids - draft_ids)
    if missing_final or extra_final:
        findings.append(
            CoverageInconsistency(
                code="final-claim-set-mismatch",
                severity="error",
                message="Final claim files do not match draft claim files.",
                refs=[*missing_final, *extra_final],
            )
        )
    if final_manifest.bundle.total_evidence_passages != len(final_passage_records):
        findings.append(
            CoverageInconsistency(
                code="final-passage-count-mismatch",
                severity="error",
                message=(
                    "Final manifest total_evidence_passages does not match observed "
                    "passage record files."
                ),
                refs=[
                    str(final_manifest.bundle.total_evidence_passages),
                    str(len(final_passage_records)),
                ],
            )
        )
    if final_manifest.bundle.bundle_hash != final_hash:
        findings.append(
            CoverageInconsistency(
                code="final-manifest-hash-mismatch",
                severity="error",
                message="Final manifest bundle hash does not match recomputed final bundle hash.",
                refs=[final_manifest.bundle.bundle_hash, final_hash],
            )
        )
    return findings


def _load_manifest(bundle_dir: Path) -> BundleManifest:
    return load_model_yaml(BundleManifest, bundle_dir / "bundle_manifest.yaml")


def _load_claims(bundle_dir: Path) -> dict[str, ClaimAuditUnit]:
    claims: dict[str, ClaimAuditUnit] = {}
    for path in sorted((bundle_dir / "claims").glob("*.yaml")):
        claim = load_model_yaml(ClaimAuditUnit, path)
        claims[claim.claim_id] = claim
    return claims


def _load_passage_records(bundle_dir: Path) -> dict[tuple[str, str], PassageRecord]:
    records = {}
    for path in sorted((bundle_dir / "evidence").glob("*/passages/*.yaml")):
        record = load_model_yaml(PassageRecord, path)
        records[(record.source_id, record.passage_id)] = record
    return records


def _member_ref(member: ExcerptRefinementMember) -> str:
    return f"{member.claim_id}/{member.source_id}/{member.passage_id}"


def _ids_cell(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) or "none"


def _dict_cell(values: dict[str, int]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{key}: {values[key]}" for key in sorted(values))


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
