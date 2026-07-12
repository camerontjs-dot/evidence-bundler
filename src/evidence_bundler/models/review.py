"""Review annotation models for draft evidence bundles."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from evidence_bundler.models.common import (
    CONTRACT_VERSION,
    ContractVersion,
    HashValue,
    NonBlankStr,
    StrictBaseModel,
)
from evidence_bundler.models.retrieval import EvidenceRole

ReviewDecision = Literal["accepted", "rejected", "needs-review", "insufficient-excerpt"]


class ReviewAnnotation(StrictBaseModel):
    """One reviewer decision row for a draft-bundle candidate passage."""

    claim_id: NonBlankStr
    passage_id: NonBlankStr
    source_id: NonBlankStr
    evidence_role: EvidenceRole
    decision: ReviewDecision = "needs-review"
    reviewer_notes: str | None = None
    decided_at_utc: NonBlankStr | None = None


class ReviewAnnotationFile(StrictBaseModel):
    """Sidecar review annotation artifact bound to a draft bundle by hashes."""

    schema_version: ContractVersion = CONTRACT_VERSION

    draft_bundle_id: NonBlankStr
    draft_bundle_hash: HashValue
    retrieval_config_hash: HashValue
    generated_at_utc: NonBlankStr
    reviewer: NonBlankStr | None = None
    annotations: list[ReviewAnnotation] = Field(default_factory=list)
