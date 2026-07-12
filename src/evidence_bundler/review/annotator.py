"""Review annotation update helpers for the annotator CLI."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import NamedTuple

from evidence_bundler.models.retrieval import EvidenceRole
from evidence_bundler.models.review import ReviewAnnotation, ReviewAnnotationFile, ReviewDecision


class ReviewAnnotationKey(NamedTuple):
    """Stable identity for one candidate annotation row."""

    claim_id: str
    source_id: str
    passage_id: str


@dataclass(frozen=True)
class ReviewAnnotationSummary:
    """Compact counts for CLI feedback."""

    total: int
    by_decision: dict[str, int]
    by_role: dict[str, int]


def annotation_key(annotation: ReviewAnnotation) -> ReviewAnnotationKey:
    """Return the immutable identity tuple for an annotation row."""
    return ReviewAnnotationKey(
        claim_id=annotation.claim_id,
        source_id=annotation.source_id,
        passage_id=annotation.passage_id,
    )


def filter_annotations(
    annotations: list[ReviewAnnotation],
    *,
    role: EvidenceRole | None = None,
    claim_id: str | None = None,
    source_id: str | None = None,
    sample: int | None = None,
) -> list[int]:
    """Return matching annotation indexes with deterministic sample truncation."""
    matches = [
        index
        for index, annotation in enumerate(annotations)
        if (role is None or annotation.evidence_role == role)
        and (claim_id is None or annotation.claim_id == claim_id)
        and (source_id is None or annotation.source_id == source_id)
    ]
    if sample is None:
        return matches
    return matches[:sample]


def apply_decision(
    annotation: ReviewAnnotation,
    *,
    decision: ReviewDecision,
    notes: str | None = None,
    decided_at_utc: str | None = None,
) -> ReviewAnnotation:
    """Return an updated annotation while preserving the timestamp invariant."""
    timestamp = None if decision == "needs-review" else decided_at_utc or _utc_now()
    updates: dict[str, object] = {
        "decision": decision,
        "decided_at_utc": timestamp,
    }
    if notes is not None:
        updates["reviewer_notes"] = notes or None
    return annotation.model_copy(update=updates)


def apply_decision_to_annotations(
    file: ReviewAnnotationFile,
    *,
    decision: ReviewDecision,
    role: EvidenceRole | None = None,
    claim_id: str | None = None,
    source_id: str | None = None,
    sample: int | None = None,
    notes: str | None = None,
    decided_at_utc: str | None = None,
) -> tuple[ReviewAnnotationFile, int]:
    """Apply one decision to filtered rows and return an updated file plus count."""
    indexes = filter_annotations(
        file.annotations,
        role=role,
        claim_id=claim_id,
        source_id=source_id,
        sample=sample,
    )
    annotations = list(file.annotations)
    for index in indexes:
        annotations[index] = apply_decision(
            annotations[index],
            decision=decision,
            notes=notes,
            decided_at_utc=decided_at_utc,
        )
    return file.model_copy(update={"annotations": annotations}), len(indexes)


def update_notes(
    annotation: ReviewAnnotation,
    *,
    notes: str,
) -> ReviewAnnotation:
    """Return an annotation with notes changed and timestamp left untouched."""
    return annotation.model_copy(update={"reviewer_notes": notes or None})


def summarize_review_annotations(file: ReviewAnnotationFile) -> ReviewAnnotationSummary:
    """Summarize annotation counts for command output."""
    return ReviewAnnotationSummary(
        total=len(file.annotations),
        by_decision=dict(Counter(annotation.decision for annotation in file.annotations)),
        by_role=dict(Counter(annotation.evidence_role for annotation in file.annotations)),
    )


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
