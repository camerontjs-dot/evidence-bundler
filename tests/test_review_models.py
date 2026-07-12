"""Review-state model tests."""

from __future__ import annotations

import pytest
import yaml

from evidence_bundler.contracts.yaml_io import yaml_to_string
from evidence_bundler.models.retrieval import EvidenceRole
from evidence_bundler.models.review import ReviewAnnotation, ReviewDecision

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


@pytest.mark.parametrize("decision", REVIEW_DECISIONS)
def test_review_decision_state_round_trips_through_yaml(decision: ReviewDecision) -> None:
    annotation = ReviewAnnotation(
        claim_id="clm-001",
        passage_id="pass-001",
        source_id="src-001",
        evidence_role="supporting",
        decision=decision,
    )

    serialized = yaml_to_string(annotation.model_dump(mode="json"))
    reloaded = ReviewAnnotation.model_validate(yaml.safe_load(serialized))

    assert reloaded == annotation
    assert reloaded.decision == decision


@pytest.mark.parametrize("evidence_role", EVIDENCE_ROLES)
@pytest.mark.parametrize("decision", REVIEW_DECISIONS)
def test_review_decision_is_orthogonal_to_evidence_role(
    evidence_role: EvidenceRole,
    decision: ReviewDecision,
) -> None:
    annotation = ReviewAnnotation(
        claim_id="clm-001",
        passage_id="pass-001",
        source_id="src-001",
        evidence_role=evidence_role,
        decision=decision,
    )

    assert annotation.evidence_role == evidence_role
    assert annotation.decision == decision
