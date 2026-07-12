"""Read-only coverage report tests for Phase 3 Unit 5."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_finalizer import (
    _annotation,
    _draft_bundle,
    _member,
    _passage,
    _write_annotations,
    _write_refinement,
)

from evidence_bundler.contracts.hashing import compute_bundle_tree_hash, hash_text
from evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml
from evidence_bundler.models.cb import BundleManifest
from evidence_bundler.models.refinement import ExcerptCluster, ExcerptRefinementFile
from evidence_bundler.models.review import ReviewAnnotationFile
from evidence_bundler.output.finalizer import (
    FinalizeProvenanceFile,
    compute_excerpt_refinement_hash,
    finalize_bundle,
)
from evidence_bundler.reports.coverage import (
    CoverageReportError,
    build_coverage_report,
    render_coverage_report_markdown,
    write_coverage_report_json,
    write_coverage_report_markdown,
)
from evidence_bundler.review import compute_review_annotations_hash, write_review_annotations


def test_coverage_report_summarizes_states_gaps_roles_and_conflicts(tmp_path: Path) -> None:
    draft_bundle_dir, annotation_path, refinement_path, final_bundle_dir, provenance_path = (
        _finalized_coverage_case(tmp_path)
    )

    report = build_coverage_report(
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        final_bundle_dir,
        provenance_path,
        generated_at_utc="2026-05-13T03:00:00Z",
    )
    markdown = render_coverage_report_markdown(report)

    by_decision = {row.decision: row for row in report.decision_coverage}
    assert report.anchors.draft_bundle_hash == compute_bundle_tree_hash(draft_bundle_dir)
    assert report.report_generated_at_utc == "2026-05-13T03:00:00Z"
    assert by_decision["accepted"].total == 1
    assert by_decision["accepted"].by_role["supporting"] == 1
    assert by_decision["rejected"].total == 1
    assert by_decision["needs-review"].total == 1
    assert by_decision["needs-review"].by_role["contradicting"] == 1
    assert by_decision["insufficient-excerpt"].total == 1
    assert by_decision["insufficient-excerpt"].by_role["conditional"] == 1
    assert by_decision["accepted"].by_role["insufficient"] == 0
    assert report.nomination_gaps.no_candidate_claim_ids == ["clm-none"]
    assert report.nomination_gaps.no_supporting_candidate_claim_ids == [
        "clm-counter-only",
        "clm-none",
    ]
    assert report.nomination_gaps.no_counterevidence_candidate_claim_ids == [
        "clm-none",
        "clm-support-only",
    ]
    assert report.nomination_gaps.skipped_claim_count == 2
    assert report.nomination_gaps.skipped_claim_ids_available is False
    assert report.nomination_gaps.exclusion_rationale == "Skipped by unit test fixture."
    assert report.refinement.cluster_count == 1
    assert report.refinement.suppressed_non_representative_count == 1
    assert report.refinement.cluster_size_distribution == {"2": 1}
    assert [cluster.cluster_id for cluster in report.refinement.conflict_clusters] == [
        "excerpt-cluster-0001"
    ]
    assert report.final_bundle.reviewer_sign_off_required is True
    assert [finding.code for finding in report.inconsistencies] == [
        "refinement-decision-conflicts"
    ]
    assert "No counterevidence-candidate claims" in markdown
    assert "`Skipped by unit test fixture.`" in markdown
    assert "refinement-decision-conflicts" in markdown


def test_coverage_report_flags_schema_valid_insufficient_role(tmp_path: Path) -> None:
    draft_bundle_dir, annotation_path, refinement_path, final_bundle_dir, provenance_path = (
        _finalized_coverage_case(tmp_path)
    )
    _mutate_sidecars_to_include_insufficient_role(
        annotation_path,
        refinement_path,
        provenance_path,
    )

    report = build_coverage_report(
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        final_bundle_dir,
        provenance_path,
        generated_at_utc="2026-05-13T03:00:00Z",
    )

    by_decision = {row.decision: row for row in report.decision_coverage}
    assert by_decision["rejected"].by_role["insufficient"] == 1
    assert "insufficient-role-annotations" in {
        finding.code for finding in report.inconsistencies
    }


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("draft_bundle_hash", hash_text("wrong-draft"), "draft bundle hash mismatch"),
        ("annotation_hash", hash_text("wrong-annotation"), "review annotations hash mismatch"),
        ("refinement_hash", hash_text("wrong-refinement"), "excerpt refinement hash mismatch"),
        ("final_bundle_id", "wrong-final-id", "final bundle id mismatch"),
        ("final_bundle_hash", hash_text("wrong-final"), "final bundle hash mismatch"),
    ],
)
def test_coverage_report_fails_closed_on_provenance_mismatch(
    tmp_path: Path,
    field: str,
    replacement: str,
    message: str,
) -> None:
    draft_bundle_dir, annotation_path, refinement_path, final_bundle_dir, provenance_path = (
        _finalized_coverage_case(tmp_path)
    )
    provenance = load_model_yaml(FinalizeProvenanceFile, provenance_path)
    write_model_yaml(provenance.model_copy(update={field: replacement}), provenance_path)

    with pytest.raises(CoverageReportError, match=message):
        build_coverage_report(
            draft_bundle_dir,
            annotation_path,
            refinement_path,
            final_bundle_dir,
            provenance_path,
            generated_at_utc="2026-05-13T03:00:00Z",
        )


def test_coverage_report_is_read_only_and_deterministic(tmp_path: Path) -> None:
    draft_bundle_dir, annotation_path, refinement_path, final_bundle_dir, provenance_path = (
        _finalized_coverage_case(tmp_path)
    )
    before = {
        "draft": compute_bundle_tree_hash(draft_bundle_dir),
        "final": compute_bundle_tree_hash(final_bundle_dir),
        "annotations": annotation_path.read_bytes(),
        "refinement": refinement_path.read_bytes(),
        "provenance": provenance_path.read_bytes(),
    }

    first = build_coverage_report(
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        final_bundle_dir,
        provenance_path,
        generated_at_utc="2026-05-13T03:00:00Z",
    )
    second = build_coverage_report(
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        final_bundle_dir,
        provenance_path,
        generated_at_utc="2026-05-13T03:00:00Z",
    )
    first_md = tmp_path / "first.md"
    first_json = tmp_path / "first.json"
    second_md = tmp_path / "second.md"
    second_json = tmp_path / "second.json"
    write_coverage_report_markdown(first, first_md)
    write_coverage_report_json(first, first_json)
    write_coverage_report_markdown(second, second_md)
    write_coverage_report_json(second, second_json)

    assert first_md.read_bytes() == second_md.read_bytes()
    assert first_json.read_bytes() == second_json.read_bytes()
    assert json.loads(first_json.read_text(encoding="utf-8"))["anchors"]["final_bundle_id"]
    assert compute_bundle_tree_hash(draft_bundle_dir) == before["draft"]
    assert compute_bundle_tree_hash(final_bundle_dir) == before["final"]
    assert annotation_path.read_bytes() == before["annotations"]
    assert refinement_path.read_bytes() == before["refinement"]
    assert provenance_path.read_bytes() == before["provenance"]


def _finalized_coverage_case(
    tmp_path: Path,
) -> tuple[Path, Path, Path, Path, Path]:
    draft_bundle_dir = _draft_bundle(
        tmp_path,
        {
            "clm-support-only": {
                "evidence": [
                    _passage("pass-accepted", 0, 20, "Accepted support."),
                    _passage("pass-rejected", 20, 40, "Rejected support."),
                ],
            },
            "clm-counter-only": {
                "counter": [
                    _passage("pass-needs-review", 40, 60, "Needs review counter."),
                    _passage("pass-insufficient-excerpt", 60, 80, "Too narrow counter."),
                ],
            },
            "clm-none": {},
        },
    )
    _record_skipped_claims(draft_bundle_dir, count=2)
    annotations = [
        _annotation("clm-support-only", "pass-accepted", decision="accepted"),
        _annotation("clm-support-only", "pass-rejected", decision="rejected"),
        _annotation(
            "clm-counter-only",
            "pass-needs-review",
            role="contradicting",
            decision="needs-review",
        ),
        _annotation(
            "clm-counter-only",
            "pass-insufficient-excerpt",
            role="conditional",
            decision="insufficient-excerpt",
        ),
    ]
    annotation_path = _write_annotations(tmp_path, draft_bundle_dir, annotations)
    cluster = ExcerptCluster(
        cluster_id="excerpt-cluster-0001",
        claim_id="clm-support-only",
        source_id="src-001",
        evidence_role="supporting",
        representative=_member(
            "clm-support-only",
            "pass-accepted",
            decision="accepted",
            start=0,
            end=20,
        ),
        members=[
            _member(
                "clm-support-only",
                "pass-accepted",
                decision="accepted",
                start=0,
                end=20,
            ),
            _member(
                "clm-support-only",
                "pass-rejected",
                decision="rejected",
                start=20,
                end=40,
            ),
        ],
        decision_conflict=True,
        member_decisions=["accepted", "rejected"],
    )
    refinement_path = _write_refinement(tmp_path, draft_bundle_dir, annotation_path, [cluster])
    final_bundle_dir = tmp_path / "final-bundle"
    result = finalize_bundle(
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        final_bundle_dir,
        generated_at_utc="2026-05-13T02:00:00Z",
    )
    return (
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        final_bundle_dir,
        result.provenance_path,
    )


def _record_skipped_claims(draft_bundle_dir: Path, *, count: int) -> None:
    manifest_path = draft_bundle_dir / "bundle_manifest.yaml"
    manifest = load_model_yaml(BundleManifest, manifest_path)
    pending = manifest.model_copy(
        update={
            "bundle": manifest.bundle.model_copy(
                update={
                    "claims_excluded": count,
                    "exclusion_rationale": "Skipped by unit test fixture.",
                    "bundle_hash": "sha256:pending",
                }
            )
        }
    )
    write_model_yaml(pending, manifest_path)
    write_model_yaml(
        pending.model_copy(
            update={
                "bundle": pending.bundle.model_copy(
                    update={"bundle_hash": compute_bundle_tree_hash(draft_bundle_dir)}
                )
            }
        ),
        manifest_path,
    )


def _mutate_sidecars_to_include_insufficient_role(
    annotation_path: Path,
    refinement_path: Path,
    provenance_path: Path,
) -> None:
    annotation_file = load_model_yaml(ReviewAnnotationFile, annotation_path)
    updated_annotations = list(annotation_file.annotations)
    updated_annotations[1] = updated_annotations[1].model_copy(
        update={"evidence_role": "insufficient"}
    )
    write_review_annotations(
        annotation_file.model_copy(update={"annotations": updated_annotations}),
        annotation_path,
    )
    refinement = load_model_yaml(ExcerptRefinementFile, refinement_path)
    write_model_yaml(
        refinement.model_copy(
            update={"review_annotations_hash": compute_review_annotations_hash(annotation_path)}
        ),
        refinement_path,
    )
    provenance = load_model_yaml(FinalizeProvenanceFile, provenance_path)
    write_model_yaml(
        provenance.model_copy(
            update={
                "annotation_hash": compute_review_annotations_hash(annotation_path),
                "refinement_hash": compute_excerpt_refinement_hash(refinement_path),
            }
        ),
        provenance_path,
    )
