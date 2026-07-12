"""Models for deterministic excerpt refinement sidecars."""

from __future__ import annotations

from pydantic import Field

from evidence_bundler.models.common import (
    CONTRACT_VERSION,
    ContractVersion,
    HashValue,
    NonBlankStr,
    StrictBaseModel,
)
from evidence_bundler.models.retrieval import EvidenceRole
from evidence_bundler.models.review import ReviewDecision


class ExcerptRefinementConfig(StrictBaseModel):
    """Deterministic thresholds used by the narrow excerpt refiner."""

    span_jaccard_threshold: float = Field(default=0.80, ge=0.0, le=1.0)
    span_containment_threshold: float = Field(default=0.90, ge=0.0, le=1.0)
    text_similarity_threshold: float = Field(default=0.95, ge=0.0, le=1.0)


class ExcerptRefinementMember(StrictBaseModel):
    """One original reviewed candidate preserved in a refinement cluster."""

    claim_id: NonBlankStr
    source_id: NonBlankStr
    passage_id: NonBlankStr
    evidence_role: EvidenceRole
    decision: ReviewDecision
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    passage_hash: HashValue


class ExcerptCluster(StrictBaseModel):
    """Near-identical reviewed candidates represented as one deterministic cluster."""

    cluster_id: NonBlankStr
    claim_id: NonBlankStr
    source_id: NonBlankStr
    evidence_role: EvidenceRole
    representative: ExcerptRefinementMember
    members: list[ExcerptRefinementMember] = Field(default_factory=list)
    decision_conflict: bool
    member_decisions: list[ReviewDecision] = Field(default_factory=list)


class ExcerptRefinementFile(StrictBaseModel):
    """Sidecar transformation log for Phase 3 Unit 3 excerpt refinement."""

    schema_version: ContractVersion = CONTRACT_VERSION

    draft_bundle_id: NonBlankStr
    draft_bundle_hash: HashValue
    retrieval_config_hash: HashValue
    review_annotations_hash: HashValue
    refiner_config_hash: HashValue
    generated_at_utc: NonBlankStr
    clusters: list[ExcerptCluster] = Field(default_factory=list)
