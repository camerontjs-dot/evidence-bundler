"""Final reviewed bundle writer tests for Phase 3 Unit 4."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import assert_no_python_yaml_tags

from evidence_bundler.contracts.hashing import (
    compute_bundle_tree_hash,
    hash_audit_config_file,
    hash_text,
    verify_sha256sums,
)
from evidence_bundler.contracts.writer import validate_bundle_tree
from evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml
from evidence_bundler.models.ca import SourceBibliographic
from evidence_bundler.models.cb import (
    AuditConfig,
    AuditFields,
    AuditRulePolicies,
    AuditScoringConfig,
    BundleManifest,
    BundleStats,
    ClaimAuditUnit,
    ClaimEvidencePassage,
    EvidenceBuilderInfo,
    PassageProvenance,
    PassageRecord,
    QualityGates,
    ReviewerSignOff,
    SourceProfile,
    ValidationSetRef,
)
from evidence_bundler.models.refinement import (
    ExcerptCluster,
    ExcerptRefinementFile,
    ExcerptRefinementMember,
)
from evidence_bundler.models.retrieval import EvidenceRole
from evidence_bundler.models.review import ReviewAnnotation, ReviewAnnotationFile, ReviewDecision
from evidence_bundler.output.finalizer import (
    FinalizeBundleError,
    FinalizeProvenanceFile,
    compute_excerpt_refinement_hash,
    finalize_bundle,
)
from evidence_bundler.review import compute_review_annotations_hash, write_review_annotations


def test_finalize_bundle_applies_adr011_decisions_and_routes_roles(tmp_path: Path) -> None:
    draft_bundle_dir = _draft_bundle(
        tmp_path,
        {
            "clm-001": {
                "evidence": [
                    _passage("pass-accepted", 0, 20, "Accepted support."),
                    _passage("pass-rejected", 20, 40, "Rejected support."),
                    _passage("pass-needs-review", 40, 60, "Needs review support."),
                    _passage("pass-insufficient", 60, 80, "Too narrow support."),
                ],
                "counter": [
                    _passage("pass-counter", 80, 100, "Contradicting candidate."),
                ],
            }
        },
    )
    annotation_path = _write_annotations(
        tmp_path,
        draft_bundle_dir,
        [
            _annotation("clm-001", "pass-accepted", decision="accepted"),
            _annotation("clm-001", "pass-rejected", decision="rejected"),
            _annotation("clm-001", "pass-needs-review", decision="needs-review"),
            _annotation("clm-001", "pass-insufficient", decision="insufficient-excerpt"),
            _annotation(
                "clm-001",
                "pass-counter",
                decision="accepted",
                role="contradicting",
            ),
        ],
    )
    refinement_path = _write_refinement(tmp_path, draft_bundle_dir, annotation_path, [])

    result = finalize_bundle(
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        tmp_path / "final-bundle",
        generated_at_utc="2026-05-13T02:00:00Z",
    )

    claim = load_model_yaml(ClaimAuditUnit, result.bundle_dir / "claims" / "clm-001.yaml")
    manifest = load_model_yaml(BundleManifest, result.bundle_dir / "bundle_manifest.yaml")
    provenance = load_model_yaml(FinalizeProvenanceFile, result.provenance_path)
    assert [passage.passage_id for passage in claim.evidence_passages] == [
        "pass-accepted",
        "pass-needs-review",
    ]
    assert [passage.passage_id for passage in claim.counterevidence_passages] == [
        "pass-counter"
    ]
    assert manifest.reviewer_sign_off.required is True
    assert manifest.reviewer_sign_off.signed_by is None
    assert manifest.reviewer_sign_off.signature_timestamp_utc is None
    assert manifest.reviewer_sign_off.signature_notes is None
    assert manifest.evidence_builder.config_hash == _manifest_hash("retrieval-config")
    assert manifest.evidence_builder.operator == "draft-operator"
    assert manifest.evidence_builder.build_timestamp_utc == "2026-05-13T02:00:00Z"
    assert manifest.source_run_id == "run-001"
    assert manifest.source_contract_version == "1.0.0"
    assert manifest.source_corpus_hash == _manifest_hash("corpus")
    assert validate_bundle_tree(result.bundle_dir) == []
    assert verify_sha256sums(result.bundle_dir) == []
    assert_no_python_yaml_tags(result.bundle_dir)
    assert provenance.final_bundle_id == manifest.bundle_id
    assert provenance.final_bundle_hash == manifest.bundle.bundle_hash


def test_finalize_bundle_signoff_false_without_shipped_needs_review(
    tmp_path: Path,
) -> None:
    draft_bundle_dir = _draft_bundle(
        tmp_path,
        {"clm-001": {"evidence": [_passage("pass-accepted", 0, 20, "Accepted support.")]}},
    )
    annotation_path = _write_annotations(
        tmp_path,
        draft_bundle_dir,
        [_annotation("clm-001", "pass-accepted", decision="accepted")],
    )
    refinement_path = _write_refinement(tmp_path, draft_bundle_dir, annotation_path, [])

    result = finalize_bundle(
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        tmp_path / "final-bundle",
        generated_at_utc="2026-05-13T02:00:00Z",
    )

    manifest = load_model_yaml(BundleManifest, result.bundle_dir / "bundle_manifest.yaml")
    assert manifest.reviewer_sign_off.required is False


def test_finalize_bundle_refiner_representative_carries_union_cited_claims(
    tmp_path: Path,
) -> None:
    draft_bundle_dir = _draft_bundle(
        tmp_path,
        {
            "clm-001": {"evidence": [_passage("pass-a", 0, 40, "Shared support.")]},
            "clm-002": {"evidence": [_passage("pass-b", 5, 45, "Shared support.")]},
        },
    )
    annotation_path = _write_annotations(
        tmp_path,
        draft_bundle_dir,
        [
            _annotation("clm-001", "pass-a", decision="accepted"),
            _annotation("clm-002", "pass-b", decision="accepted"),
        ],
    )
    cluster = ExcerptCluster(
        cluster_id="excerpt-cluster-0001",
        claim_id="clm-001",
        source_id="src-001",
        evidence_role="supporting",
        representative=_member("clm-001", "pass-a", decision="accepted", start=0, end=40),
        members=[
            _member("clm-001", "pass-a", decision="accepted", start=0, end=40),
            _member("clm-002", "pass-b", decision="accepted", start=5, end=45),
        ],
        decision_conflict=False,
        member_decisions=["accepted"],
    )
    refinement_path = _write_refinement(tmp_path, draft_bundle_dir, annotation_path, [cluster])

    result = finalize_bundle(
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        tmp_path / "final-bundle",
        generated_at_utc="2026-05-13T02:00:00Z",
    )

    claim_1 = load_model_yaml(ClaimAuditUnit, result.bundle_dir / "claims" / "clm-001.yaml")
    claim_2 = load_model_yaml(ClaimAuditUnit, result.bundle_dir / "claims" / "clm-002.yaml")
    passage_record = load_model_yaml(
        PassageRecord,
        result.bundle_dir / "evidence" / "src-001" / "passages" / "pass-a.yaml",
    )
    assert [passage.passage_id for passage in claim_1.evidence_passages] == ["pass-a"]
    assert [passage.passage_id for passage in claim_2.evidence_passages] == ["pass-a"]
    assert not (result.bundle_dir / "evidence" / "src-001" / "passages" / "pass-b.yaml").exists()
    assert passage_record.cited_by_claims == ["clm-001", "clm-002"]


def test_finalize_bundle_fails_closed_for_missing_extra_duplicate_and_insufficient(
    tmp_path: Path,
) -> None:
    draft_bundle_dir = _draft_bundle(
        tmp_path,
        {"clm-001": {"evidence": [_passage("pass-a", 0, 40, "Support.")]}}
    )
    refinement_path: Path

    missing_path = _write_annotations(tmp_path, draft_bundle_dir, [])
    refinement_path = _write_refinement(tmp_path, draft_bundle_dir, missing_path, [])
    with pytest.raises(FinalizeBundleError, match="missing draft candidate"):
        finalize_bundle(draft_bundle_dir, missing_path, refinement_path, tmp_path / "missing")

    extra_path = _write_annotations(
        tmp_path,
        draft_bundle_dir,
        [
            _annotation("clm-001", "pass-a", decision="accepted"),
            _annotation("clm-001", "pass-extra", decision="accepted"),
        ],
        name="extra_annotations.yaml",
    )
    refinement_path = _write_refinement(
        tmp_path,
        draft_bundle_dir,
        extra_path,
        [],
        name="extra_refinement.yaml",
    )
    with pytest.raises(FinalizeBundleError, match="unknown draft candidate"):
        finalize_bundle(draft_bundle_dir, extra_path, refinement_path, tmp_path / "extra")

    duplicate_path = _write_annotations(
        tmp_path,
        draft_bundle_dir,
        [
            _annotation("clm-001", "pass-a", decision="accepted"),
            _annotation("clm-001", "pass-a", decision="rejected"),
        ],
        name="duplicate_annotations.yaml",
    )
    refinement_path = _write_refinement(
        tmp_path,
        draft_bundle_dir,
        duplicate_path,
        [],
        name="duplicate_refinement.yaml",
    )
    with pytest.raises(FinalizeBundleError, match="Duplicate review annotation"):
        finalize_bundle(draft_bundle_dir, duplicate_path, refinement_path, tmp_path / "duplicate")

    insufficient_path = _write_annotations(
        tmp_path,
        draft_bundle_dir,
        [_annotation("clm-001", "pass-a", role="insufficient", decision="accepted")],
        name="insufficient_annotations.yaml",
    )
    refinement_path = _write_refinement(
        tmp_path,
        draft_bundle_dir,
        insufficient_path,
        [],
        name="insufficient_refinement.yaml",
    )
    with pytest.raises(FinalizeBundleError, match="role does not match draft evidence"):
        finalize_bundle(
            draft_bundle_dir,
            insufficient_path,
            refinement_path,
            tmp_path / "insufficient",
        )


def test_finalize_bundle_detects_refinement_annotation_hash_drift(tmp_path: Path) -> None:
    draft_bundle_dir = _draft_bundle(
        tmp_path,
        {"clm-001": {"evidence": [_passage("pass-a", 0, 40, "Support.")]}}
    )
    annotation_path = _write_annotations(
        tmp_path,
        draft_bundle_dir,
        [_annotation("clm-001", "pass-a", decision="accepted")],
    )
    refinement_path = _write_refinement(tmp_path, draft_bundle_dir, annotation_path, [])
    annotation_file = load_model_yaml(ReviewAnnotationFile, annotation_path)
    updated_annotations = [
        annotation.model_copy(update={"decision": "rejected"})
        for annotation in annotation_file.annotations
    ]
    write_review_annotations(
        annotation_file.model_copy(update={"annotations": updated_annotations}),
        annotation_path,
    )

    with pytest.raises(ValueError, match="review annotations-hash mismatch"):
        finalize_bundle(draft_bundle_dir, annotation_path, refinement_path, tmp_path / "final")

    assert not (tmp_path / "final").exists()


def test_finalize_bundle_is_deterministic_with_fixed_timestamp(tmp_path: Path) -> None:
    draft_bundle_dir = _draft_bundle(
        tmp_path,
        {"clm-001": {"evidence": [_passage("pass-a", 0, 40, "Support.")]}}
    )
    annotation_path = _write_annotations(
        tmp_path,
        draft_bundle_dir,
        [_annotation("clm-001", "pass-a", decision="accepted")],
    )
    refinement_path = _write_refinement(tmp_path, draft_bundle_dir, annotation_path, [])

    first = finalize_bundle(
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        tmp_path / "final-one",
        provenance_path=tmp_path / "first_provenance.yaml",
        generated_at_utc="2026-05-13T02:00:00Z",
    )
    second = finalize_bundle(
        draft_bundle_dir,
        annotation_path,
        refinement_path,
        tmp_path / "final-two",
        provenance_path=tmp_path / "second_provenance.yaml",
        generated_at_utc="2026-05-13T02:00:00Z",
    )

    assert _tree_bytes(first.bundle_dir) == _tree_bytes(second.bundle_dir)


def _draft_bundle(
    tmp_path: Path,
    claims: dict[str, dict[str, list[ClaimEvidencePassage]]],
) -> Path:
    draft_bundle_dir = tmp_path / "draft-bundle"
    draft_bundle_dir.mkdir()
    (draft_bundle_dir / "CONTRACT_VERSION").write_text("1.0.0\n", encoding="utf-8")
    audit_config_hash = _write_audit_config(draft_bundle_dir)
    _write_validation_ref(draft_bundle_dir)
    all_passages = {
        (passage.source_id, passage.passage_id): passage
        for claim in claims.values()
        for passages in claim.values()
        for passage in passages
    }
    _write_source_profiles(draft_bundle_dir, {source_id for source_id, _ in all_passages})
    _write_passage_records(draft_bundle_dir, all_passages, claims)
    for claim_id, grouped in claims.items():
        unit = ClaimAuditUnit(
            claim_id=claim_id,
            bundle_id="draft-bundle-001",
            schema_version="1.0.0",
            claim_text=f"Claim text for {claim_id}",
            claim_type="extracted_claim",
            workflow_condition="baseline",
            task_id="task-001",
            scaffold_support_status="sourced",
            scaffold_claim_strength=0.8,
            scaffold_extraction_fidelity=0.9,
            scaffold_counterevidence_found=bool(grouped.get("counter")),
            scaffold_downgraded=False,
            evidence_passages=grouped.get("evidence", []),
            counterevidence_passages=grouped.get("counter", []),
            audit=AuditFields(),
        )
        write_model_yaml(unit, draft_bundle_dir / "claims" / f"{claim_id}.yaml")

    manifest = _manifest(
        total_claims=len(claims),
        total_passages=len(all_passages),
        audit_config_hash=audit_config_hash,
    )
    manifest_path = draft_bundle_dir / "bundle_manifest.yaml"
    write_model_yaml(manifest, manifest_path)
    manifest = manifest.model_copy(
        update={
            "bundle": manifest.bundle.model_copy(
                update={"bundle_hash": compute_bundle_tree_hash(draft_bundle_dir)}
            )
        }
    )
    write_model_yaml(manifest, manifest_path)
    return draft_bundle_dir


def _write_annotations(
    tmp_path: Path,
    draft_bundle_dir: Path,
    annotations: list[ReviewAnnotation],
    *,
    name: str = "review_annotations.yaml",
) -> Path:
    manifest = load_model_yaml(BundleManifest, draft_bundle_dir / "bundle_manifest.yaml")
    annotation_path = tmp_path / name
    write_review_annotations(
        ReviewAnnotationFile(
            draft_bundle_id=manifest.bundle_id,
            draft_bundle_hash=compute_bundle_tree_hash(draft_bundle_dir),
            retrieval_config_hash=manifest.evidence_builder.config_hash,
            generated_at_utc="2026-05-13T01:00:00Z",
            annotations=annotations,
        ),
        annotation_path,
    )
    return annotation_path


def _write_refinement(
    tmp_path: Path,
    draft_bundle_dir: Path,
    annotation_path: Path,
    clusters: list[ExcerptCluster],
    *,
    name: str = "excerpt_refinement.yaml",
) -> Path:
    manifest = load_model_yaml(BundleManifest, draft_bundle_dir / "bundle_manifest.yaml")
    refinement_path = tmp_path / name
    write_model_yaml(
        ExcerptRefinementFile(
            draft_bundle_id=manifest.bundle_id,
            draft_bundle_hash=compute_bundle_tree_hash(draft_bundle_dir),
            retrieval_config_hash=manifest.evidence_builder.config_hash,
            review_annotations_hash=compute_review_annotations_hash(annotation_path),
            refiner_config_hash=hash_text("unit-test-refiner-config"),
            generated_at_utc="2026-05-13T01:30:00Z",
            clusters=clusters,
        ),
        refinement_path,
    )
    assert compute_excerpt_refinement_hash(refinement_path)
    return refinement_path


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


def _member(
    claim_id: str,
    passage_id: str,
    *,
    source_id: str = "src-001",
    role: EvidenceRole = "supporting",
    decision: ReviewDecision = "accepted",
    start: int = 0,
    end: int = 40,
) -> ExcerptRefinementMember:
    return ExcerptRefinementMember(
        claim_id=claim_id,
        passage_id=passage_id,
        source_id=source_id,
        evidence_role=role,
        decision=decision,
        char_start=start,
        char_end=end,
        passage_hash=hash_text(_passage_text(passage_id)),
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


def _write_audit_config(draft_bundle_dir: Path) -> str:
    audit_config_path = draft_bundle_dir / "audit_config.yaml"
    audit_config = AuditConfig(
        config_id="test-audit-config",
        config_hash="sha256:pending",
        schema_version="1.0.0",
        frozen_at_utc="2026-05-13T00:00:00Z",
        scoring=AuditScoringConfig(
            support_threshold_sourced=0.8,
            support_threshold_partial=0.55,
            counterevidence_weight=0.3,
        ),
        rule_policies=AuditRulePolicies(
            require_passage_level_match=True,
            flag_unsupported_threshold=0.4,
            false_caution_detection=True,
            false_caution_threshold=0.85,
            overstated_detection=True,
            needs_source_detection=True,
        ),
        known_limitations=["Unit test audit config."],
    )
    write_model_yaml(audit_config, audit_config_path)
    config_hash = hash_audit_config_file(audit_config_path)
    write_model_yaml(
        audit_config.model_copy(update={"config_hash": config_hash}),
        audit_config_path,
    )
    return config_hash


def _write_validation_ref(draft_bundle_dir: Path) -> None:
    write_model_yaml(
        ValidationSetRef(
            schema_version="1.0.0",
            validation_set_version="test-validation-set",
            validation_set_hash=_manifest_hash("validation"),
            frozen_at_utc="2026-05-13T00:00:00Z",
            description="Unit test validation set.",
        ),
        draft_bundle_dir / "validation_set_ref.yaml",
    )


def _write_source_profiles(draft_bundle_dir: Path, source_ids: set[str]) -> None:
    for index, source_id in enumerate(sorted(source_ids), start=1):
        write_model_yaml(
            SourceProfile(
                source_id=source_id,
                schema_version="1.0.0",
                bibliographic=SourceBibliographic(
                    source_type="journal_article",
                    title=f"Source {source_id}",
                    authors=["Unit Tester"],
                    url=f"https://example.test/{source_id}",
                    access_date_utc="2026-05-13T00:00:00Z",
                ),
                trust_level="primary",
                content_hash=_manifest_hash(f"content-{source_id}"),
                retrieved_for=["clm-001"],
                retrieval_query="unit test query",
                retrieval_rank=index,
            ),
            draft_bundle_dir / "evidence" / source_id / "source_profile.yaml",
        )


def _write_passage_records(
    draft_bundle_dir: Path,
    passages: dict[tuple[str, str], ClaimEvidencePassage],
    claims: dict[str, dict[str, list[ClaimEvidencePassage]]],
) -> None:
    for (source_id, passage_id), passage in sorted(passages.items()):
        cited_by_claims = sorted(
            claim_id
            for claim_id, grouped in claims.items()
            for grouped_passages in grouped.values()
            for grouped_passage in grouped_passages
            if grouped_passage.source_id == source_id
            and grouped_passage.passage_id == passage_id
        )
        write_model_yaml(
            PassageRecord(
                passage_id=passage_id,
                source_id=source_id,
                bundle_id="draft-bundle-001",
                schema_version="1.0.0",
                passage_text=passage.passage_text,
                section=passage.section,
                paragraph_index=0,
                char_start=passage.char_start,
                char_end=passage.char_end,
                passage_hash=passage.passage_hash,
                cited_by_claims=cited_by_claims,
                extraction_method="auto_retrieved",
                provenance=PassageProvenance(
                    source_url=f"https://example.test/{source_id}",
                    source_access_date_utc="2026-05-13T00:00:00Z",
                    source_content_hash=_manifest_hash(f"content-{source_id}"),
                    scaffold_run_id="run-001",
                    evidence_builder_version="0.1.0",
                    bundle_created_at_utc="2026-05-13T00:00:00Z",
                ),
            ),
            draft_bundle_dir / "evidence" / source_id / "passages" / f"{passage_id}.yaml",
        )


def _manifest(
    *,
    total_claims: int,
    total_passages: int,
    audit_config_hash: str,
) -> BundleManifest:
    return BundleManifest(
        bundle_id="draft-bundle-001",
        schema_version="1.0.0",
        generated_at_utc="2026-05-13T00:00:00Z",
        source_run_id="run-001",
        source_contract_version="1.0.0",
        source_corpus_hash=_manifest_hash("corpus"),
        evidence_builder=EvidenceBuilderInfo(
            version="0.1.0",
            config_hash=_manifest_hash("retrieval-config"),
            operator="draft-operator",
            build_timestamp_utc="2026-05-13T00:00:00Z",
        ),
        bundle=BundleStats(
            total_claims_in_source=total_claims,
            claims_included=total_claims,
            claims_excluded=0,
            exclusion_rationale="Unit test draft bundle.",
            total_evidence_passages=total_passages,
            bundle_hash="sha256:pending",
        ),
        quality_gates=QualityGates(
            every_claim_has_at_least_one_passage=total_passages > 0,
            every_passage_links_to_source_profile=True,
            source_hashes_verified=True,
            bundle_integrity_verified=True,
        ),
        audit_config_version="test-audit-config",
        audit_config_hash=audit_config_hash,
        validation_set_version="test-validation-set",
        validation_set_hash=_manifest_hash("validation"),
        reviewer_sign_off=ReviewerSignOff(required=False),
    )

def _manifest_hash(seed: str) -> str:
    return hash_text(seed)


def _passage_text(passage_id: str) -> str:
    return {
        "pass-a": "Shared support.",
        "pass-b": "Shared support.",
    }.get(passage_id, f"Text for {passage_id}.")


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
