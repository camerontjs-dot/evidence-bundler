"""Review annotator library tests."""

from __future__ import annotations

from evidence_bundler.models.review import ReviewAnnotation, ReviewAnnotationFile
from evidence_bundler.review.annotator import (
    apply_decision,
    apply_decision_to_annotations,
    filter_annotations,
    summarize_review_annotations,
    update_notes,
)


def test_filter_annotations_supports_role_claim_source_and_deterministic_sample() -> None:
    annotation_file = _annotation_file()

    matches = filter_annotations(
        annotation_file.annotations,
        role="supporting",
        claim_id="clm-001",
        sample=1,
    )

    assert matches == [0]


def test_apply_decision_sets_timestamp_iff_decision_is_not_needs_review() -> None:
    annotation = _annotation_file().annotations[0]

    accepted = apply_decision(
        annotation,
        decision="accepted",
        notes="reviewed",
        decided_at_utc="2026-05-13T01:02:03Z",
    )
    reset = apply_decision(
        accepted,
        decision="needs-review",
        notes="defer for comparison",
        decided_at_utc="2026-05-13T04:05:06Z",
    )

    assert accepted.decision == "accepted"
    assert accepted.decided_at_utc == "2026-05-13T01:02:03Z"
    assert accepted.reviewer_notes == "reviewed"
    assert reset.decision == "needs-review"
    assert reset.decided_at_utc is None
    assert reset.reviewer_notes == "defer for comparison"


def test_update_notes_does_not_stamp_timestamp() -> None:
    annotation = _annotation_file().annotations[0]

    updated = update_notes(annotation, notes="deferred - compare with clm-002")

    assert updated.decision == "needs-review"
    assert updated.decided_at_utc is None
    assert updated.reviewer_notes == "deferred - compare with clm-002"


def test_apply_decision_to_annotations_returns_updated_file_and_count() -> None:
    annotation_file = _annotation_file()

    updated, count = apply_decision_to_annotations(
        annotation_file,
        decision="rejected",
        role="supporting",
        sample=1,
        decided_at_utc="2026-05-13T01:02:03Z",
    )

    assert count == 1
    assert updated.annotations[0].decision == "rejected"
    assert updated.annotations[0].decided_at_utc == "2026-05-13T01:02:03Z"
    assert updated.annotations[1].decision == "needs-review"
    assert annotation_file.annotations[0].decision == "needs-review"


def test_summarize_review_annotations_counts_decisions_and_roles() -> None:
    annotation_file, _count = apply_decision_to_annotations(
        _annotation_file(),
        decision="accepted",
        role="contradicting",
        decided_at_utc="2026-05-13T01:02:03Z",
    )

    summary = summarize_review_annotations(annotation_file)

    assert summary.total == 3
    assert summary.by_decision == {"needs-review": 2, "accepted": 1}
    assert summary.by_role == {"supporting": 2, "contradicting": 1}


def _annotation_file() -> ReviewAnnotationFile:
    return ReviewAnnotationFile(
        draft_bundle_id="bundle-001",
        draft_bundle_hash="sha256:" + "0" * 64,
        retrieval_config_hash="sha256:" + "1" * 64,
        generated_at_utc="2026-05-13T00:00:00Z",
        annotations=[
            ReviewAnnotation(
                claim_id="clm-001",
                passage_id="passage-001",
                source_id="src-001",
                evidence_role="supporting",
            ),
            ReviewAnnotation(
                claim_id="clm-001",
                passage_id="passage-002",
                source_id="src-002",
                evidence_role="supporting",
            ),
            ReviewAnnotation(
                claim_id="clm-002",
                passage_id="passage-003",
                source_id="src-003",
                evidence_role="contradicting",
            ),
        ],
    )
