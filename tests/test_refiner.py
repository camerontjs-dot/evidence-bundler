"""Narrow excerpt-refinement tests for Phase 3 Unit 3."""

from __future__ import annotations

from pathlib import Path

import pytest

from evidence_bundler.contracts.hashing import compute_bundle_tree_hash, hash_text
from evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml
from evidence_bundler.models.cb import (
    AuditFields,
    BundleManifest,
    BundleStats,
    ClaimAuditUnit,
    ClaimEvidencePassage,
    EvidenceBuilderInfo,
    QualityGates,
    ReviewerSignOff,
)
from evidence_bundler.models.retrieval import EvidenceRole
from evidence_bundler.models.review import ReviewAnnotation, ReviewAnnotationFile, ReviewDecision
from evidence_bundler.output.refiner import (
    ExcerptRefinerDriftError,
    load_excerpt_refinement,
    refine_excerpts,
    write_excerpt_refinement,
)
from evidence_bundler.review import (
    apply_decision_to_annotations,
    compute_review_annotations_hash,
    write_review_annotations,
)


def test_refiner_clusters_same_passage_and_preserves_decision_conflict(
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _draft_with_annotations(
        tmp_path,
        {
            "clm-001": [
                _passage("pass-001", 0, 100, "Shared excerpt text."),
            ]
        },
        [
            _annotation("clm-001", "pass-001", decision="accepted"),
            _annotation("clm-001", "pass-001", decision="rejected"),
        ],
    )

    refinement, summary = refine_excerpts(
        draft_bundle_dir,
        annotation_path,
        generated_at_utc="2026-05-13T00:00:00Z",
    )

    cluster = refinement.clusters[0]
    assert summary.candidates == 2
    assert summary.clusters == 1
    assert summary.members == 2
    assert summary.collapsed_members == 1
    assert summary.decision_conflicts == 1
    assert cluster.decision_conflict is True
    assert cluster.member_decisions == ["accepted", "rejected"]
    assert cluster.representative.decision == "accepted"
    assert {member.decision for member in cluster.members} == {"accepted", "rejected"}


def test_refiner_clusters_overlapping_spans_and_containment(tmp_path: Path) -> None:
    draft_bundle_dir, annotation_path = _draft_with_annotations(
        tmp_path,
        {
            "clm-001": [
                _passage("pass-wide", 0, 100, "The wide candidate excerpt covers all text."),
                _passage("pass-overlap", 10, 105, "The overlapping candidate excerpt covers text."),
                _passage("pass-contained", 20, 80, "The contained candidate excerpt."),
            ]
        },
        [
            _annotation("clm-001", "pass-wide", decision="needs-review"),
            _annotation("clm-001", "pass-overlap", decision="needs-review"),
            _annotation("clm-001", "pass-contained", decision="needs-review"),
        ],
    )

    refinement, _summary = refine_excerpts(draft_bundle_dir, annotation_path)

    assert len(refinement.clusters) == 1
    assert [member.passage_id for member in refinement.clusters[0].members] == [
        "pass-contained",
        "pass-overlap",
        "pass-wide",
    ]


def test_refiner_clusters_near_identical_normalized_text(tmp_path: Path) -> None:
    draft_bundle_dir, annotation_path = _draft_with_annotations(
        tmp_path,
        {
            "clm-001": [
                _passage("pass-a", 0, 50, "Submission checklist requires QA review."),
                _passage("pass-b", 200, 250, "submission   checklist requires qa review"),
            ]
        },
        [
            _annotation("clm-001", "pass-a"),
            _annotation("clm-001", "pass-b"),
        ],
    )

    refinement, _summary = refine_excerpts(draft_bundle_dir, annotation_path)

    assert len(refinement.clusters) == 1
    assert refinement.clusters[0].decision_conflict is False


def test_refiner_does_not_cluster_below_threshold_cross_role_or_cross_claim(
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _draft_with_annotations(
        tmp_path,
        {
            "clm-001": [
                _passage("pass-a", 0, 40, "Alpha beta gamma delta."),
                _passage("pass-b", 300, 340, "Completely different excerpt."),
                _passage("pass-counter", 0, 40, "Alpha beta gamma delta."),
            ],
            "clm-002": [
                _passage("pass-c", 0, 40, "Alpha beta gamma delta."),
            ],
        },
        [
            _annotation("clm-001", "pass-a", role="supporting"),
            _annotation("clm-001", "pass-b", role="supporting"),
            _annotation("clm-001", "pass-counter", role="contradicting"),
            _annotation("clm-002", "pass-c", role="supporting"),
        ],
    )

    refinement, summary = refine_excerpts(draft_bundle_dir, annotation_path)

    assert refinement.clusters == []
    assert summary.clusters == 0
    assert summary.collapsed_members == 0


def test_refiner_representative_priority_and_all_rejected_cluster(
    tmp_path: Path,
) -> None:
    draft_bundle_dir, annotation_path = _draft_with_annotations(
        tmp_path,
        {
            "clm-001": [
                _passage("pass-accepted", 10, 80, "Same near duplicate text."),
                _passage("pass-needs-review", 0, 100, "Same near duplicate text."),
            ],
            "clm-002": [
                _passage("pass-rejected-a", 0, 100, "Rejected duplicate text."),
                _passage("pass-rejected-b", 10, 90, "Rejected duplicate text."),
            ],
        },
        [
            _annotation("clm-001", "pass-accepted", decision="accepted"),
            _annotation("clm-001", "pass-needs-review", decision="needs-review"),
            _annotation("clm-002", "pass-rejected-a", decision="rejected"),
            _annotation("clm-002", "pass-rejected-b", decision="rejected"),
        ],
    )

    refinement, _summary = refine_excerpts(draft_bundle_dir, annotation_path)

    assert len(refinement.clusters) == 2
    assert refinement.clusters[0].representative.passage_id == "pass-accepted"
    assert refinement.clusters[0].member_decisions == ["accepted", "needs-review"]
    assert refinement.clusters[1].member_decisions == ["rejected"]
    assert refinement.clusters[1].decision_conflict is False


def test_review_annotation_hash_uses_canonical_yaml(tmp_path: Path) -> None:
    draft_bundle_dir, annotation_path = _draft_with_annotations(
        tmp_path,
        {"clm-001": [_passage("pass-001", 0, 100, "Shared excerpt text.")]},
        [_annotation("clm-001", "pass-001")],
    )
    del draft_bundle_dir
    original_hash = compute_review_annotations_hash(annotation_path)
    original = annotation_path.read_text(encoding="utf-8")
    annotation_path.write_text(f"# harmless formatting comment\n{original}", encoding="utf-8")

    assert compute_review_annotations_hash(annotation_path) == original_hash


def test_refinement_loader_detects_annotation_hash_drift(tmp_path: Path) -> None:
    draft_bundle_dir, annotation_path = _draft_with_annotations(
        tmp_path,
        {"clm-001": [_passage("pass-001", 0, 100, "Shared excerpt text.")]},
        [_annotation("clm-001", "pass-001")],
    )
    refinement, _summary = refine_excerpts(draft_bundle_dir, annotation_path)
    refinement_path = tmp_path / "excerpt_refinement.yaml"
    write_excerpt_refinement(refinement, refinement_path)
    annotations = load_model_yaml(ReviewAnnotationFile, annotation_path)
    updated, _count = apply_decision_to_annotations(
        annotations,
        decision="accepted",
        sample=1,
        decided_at_utc="2026-05-13T01:02:03Z",
    )
    write_review_annotations(updated, annotation_path)

    with pytest.raises(ExcerptRefinerDriftError, match="review annotations-hash mismatch"):
        load_excerpt_refinement(refinement_path, draft_bundle_dir, annotation_path)


def test_refinement_output_is_byte_identical_with_fixed_timestamp(tmp_path: Path) -> None:
    draft_bundle_dir, annotation_path = _draft_with_annotations(
        tmp_path,
        {
            "clm-001": [
                _passage("pass-a", 0, 50, "Submission checklist requires QA review."),
                _passage("pass-b", 200, 250, "submission checklist requires qa review"),
            ]
        },
        [_annotation("clm-001", "pass-a"), _annotation("clm-001", "pass-b")],
    )
    first, _summary = refine_excerpts(
        draft_bundle_dir,
        annotation_path,
        generated_at_utc="2026-05-13T00:00:00Z",
    )
    second, _summary = refine_excerpts(
        draft_bundle_dir,
        annotation_path,
        generated_at_utc="2026-05-13T00:00:00Z",
    )
    first_path = tmp_path / "first.yaml"
    second_path = tmp_path / "second.yaml"

    write_excerpt_refinement(first, first_path)
    write_excerpt_refinement(second, second_path)

    assert first_path.read_bytes() == second_path.read_bytes()


def _draft_with_annotations(
    tmp_path: Path,
    claims: dict[str, list[ClaimEvidencePassage]],
    annotations: list[ReviewAnnotation],
) -> tuple[Path, Path]:
    draft_bundle_dir = tmp_path / "draft-bundle"
    (draft_bundle_dir / "claims").mkdir(parents=True)
    bundle_id = "bundle-test-001"
    for claim_id, passages in claims.items():
        unit = ClaimAuditUnit(
            claim_id=claim_id,
            bundle_id=bundle_id,
            schema_version="1.0.0",
            claim_text=f"Claim text for {claim_id}",
            claim_type="extracted_claim",
            workflow_condition="baseline",
            task_id="task-001",
            scaffold_support_status="sourced",
            scaffold_claim_strength=0.8,
            scaffold_extraction_fidelity=0.9,
            scaffold_counterevidence_found=False,
            scaffold_downgraded=False,
            evidence_passages=[
                passage
                for passage in passages
                if not passage.passage_id.startswith("pass-counter")
            ],
            counterevidence_passages=[
                passage for passage in passages if passage.passage_id.startswith("pass-counter")
            ],
            audit=AuditFields(),
        )
        write_model_yaml(unit, draft_bundle_dir / "claims" / f"{claim_id}.yaml")

    manifest = _manifest(bundle_id=bundle_id, total_claims=len(claims))
    manifest_path = draft_bundle_dir / "bundle_manifest.yaml"
    write_model_yaml(manifest, manifest_path)
    bundle_hash = compute_bundle_tree_hash(draft_bundle_dir)
    manifest = manifest.model_copy(
        update={"bundle": manifest.bundle.model_copy(update={"bundle_hash": bundle_hash})}
    )
    write_model_yaml(manifest, manifest_path)

    annotation_path = tmp_path / "review_annotations.yaml"
    annotation_file = ReviewAnnotationFile(
        draft_bundle_id=bundle_id,
        draft_bundle_hash=compute_bundle_tree_hash(draft_bundle_dir),
        retrieval_config_hash=manifest.evidence_builder.config_hash,
        generated_at_utc="2026-05-13T00:00:00Z",
        annotations=annotations,
    )
    write_review_annotations(annotation_file, annotation_path)
    return draft_bundle_dir, annotation_path


def _manifest(*, bundle_id: str, total_claims: int) -> BundleManifest:
    return BundleManifest(
        bundle_id=bundle_id,
        schema_version="1.0.0",
        generated_at_utc="2026-05-13T00:00:00Z",
        source_run_id="run-001",
        source_contract_version="1.0.0",
        source_corpus_hash="sha256:" + "2" * 64,
        evidence_builder=EvidenceBuilderInfo(
            version="0.1.0",
            config_hash="sha256:" + "3" * 64,
            operator="unit-test",
            build_timestamp_utc="2026-05-13T00:00:00Z",
        ),
        bundle=BundleStats(
            total_claims_in_source=total_claims,
            claims_included=total_claims,
            claims_excluded=0,
            exclusion_rationale="Unit test draft bundle.",
            total_evidence_passages=0,
            bundle_hash="sha256:pending",
        ),
        quality_gates=QualityGates(
            every_claim_has_at_least_one_passage=True,
            every_passage_links_to_source_profile=True,
            source_hashes_verified=True,
            bundle_integrity_verified=True,
        ),
        audit_config_version="test-audit-config",
        audit_config_hash="sha256:" + "4" * 64,
        validation_set_version="test-validation-set",
        validation_set_hash="sha256:" + "5" * 64,
        reviewer_sign_off=ReviewerSignOff(required=False),
    )


def _annotation(
    claim_id: str,
    passage_id: str,
    *,
    source_id: str = "src-001",
    role: EvidenceRole = "supporting",
    decision: ReviewDecision = "needs-review",
) -> ReviewAnnotation:
    return ReviewAnnotation(
        claim_id=claim_id,
        passage_id=passage_id,
        source_id=source_id,
        evidence_role=role,
        decision=decision,
    )


def _passage(
    passage_id: str,
    start: int,
    end: int,
    text: str,
    *,
    source_id: str = "src-001",
) -> ClaimEvidencePassage:
    return ClaimEvidencePassage(
        passage_id=passage_id,
        source_id=source_id,
        passage_text=text,
        section=None,
        char_start=start,
        char_end=end,
        source_trust_level="primary",
        passage_hash=hash_text(text),
    )
