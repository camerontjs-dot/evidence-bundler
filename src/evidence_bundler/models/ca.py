"""Pydantic models for C-A scaffold-run artifacts."""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from evidence_bundler.models.common import (
    ClaimType,
    ContractVersion,
    ExtractionMethod,
    HashValue,
    NonBlankStr,
    SourceType,
    StrictBaseModel,
    SupportStatus,
    TrustLevel,
    WorkflowCondition,
)


class ScaffoldConfigInfo(StrictBaseModel):
    """Scaffold version and frozen prompt/config identity."""

    version: NonBlankStr
    prompt_template_id: NonBlankStr
    prompt_template_hash: HashValue
    config_hash: HashValue


class ScaffoldModelInfo(StrictBaseModel):
    """Model runtime state captured by the scaffold run."""

    model_id: NonBlankStr
    model_version: NonBlankStr
    api_endpoint: NonBlankStr
    temperature: float = Field(ge=0.0)
    max_tokens: int = Field(gt=0)


class ScaffoldTaskInfo(StrictBaseModel):
    """Task identity and checkability state for a scaffold run."""

    research_question: NonBlankStr
    domain: NonBlankStr
    expert_checkable: bool
    ground_truth_ref: NonBlankStr | None = None


class ScaffoldCorpusInfo(StrictBaseModel):
    """Corpus retrieval summary and integrity hash."""

    total_sources: int = Field(ge=0)
    corpus_hash: HashValue
    retrieval_strategy: NonBlankStr
    retrieval_timestamp_utc: NonBlankStr


class ScaffoldRunMetadata(StrictBaseModel):
    """Operator and environment metadata for a scaffold run."""

    operator: NonBlankStr
    environment: NonBlankStr
    notes: str = ""


class ScaffoldRunManifest(StrictBaseModel):
    """C-A scaffold_run.yaml frozen state manifest."""

    run_id: NonBlankStr
    task_id: NonBlankStr
    workflow_condition: WorkflowCondition
    timestamp_utc: NonBlankStr
    scaffold: ScaffoldConfigInfo
    model: ScaffoldModelInfo
    task: ScaffoldTaskInfo
    corpus: ScaffoldCorpusInfo
    intermediates_present: bool
    run_metadata: ScaffoldRunMetadata


class SourceRef(StrictBaseModel):
    """Reference from a scaffold claim to a source passage."""

    source_id: NonBlankStr
    passage_id: NonBlankStr


class ScaffoldClaim(StrictBaseModel):
    """Claim object from C-A claims.yaml."""

    claim_id: NonBlankStr
    claim_type: ClaimType
    claim_text: NonBlankStr
    support_status: SupportStatus
    claim_strength: float = Field(ge=0.0, le=1.0)
    extraction_fidelity: float = Field(ge=0.0, le=1.0)
    source_refs: list[SourceRef] = Field(default_factory=list)
    counterevidence_checked: bool
    counterevidence_found: bool
    downgraded: bool
    downgrade_reason: str | None = None
    scaffold_notes: str = ""


class ClaimsRegistry(StrictBaseModel):
    """C-A claims.yaml registry."""

    schema_version: ContractVersion
    run_id: NonBlankStr
    generated_at_utc: NonBlankStr
    claims: list[ScaffoldClaim] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_claim_ids(self) -> Self:
        """Reject duplicate claim IDs in the C-A registry."""
        seen: set[str] = set()
        for claim in self.claims:
            if claim.claim_id in seen:
                raise ValueError(f"Duplicate claim_id: {claim.claim_id}")
            seen.add(claim.claim_id)
        return self


class SourceBibliographic(StrictBaseModel):
    """Bibliographic identity for a C-A source."""

    source_type: SourceType
    title: NonBlankStr
    authors: list[NonBlankStr] = Field(default_factory=list)
    publication_date: NonBlankStr | None = None
    pmid: NonBlankStr | None = None
    doi: NonBlankStr | None = None
    url: NonBlankStr
    access_date_utc: NonBlankStr


class SourceRetrieval(StrictBaseModel):
    """Retrieval linkage from a source back to target claims."""

    retrieved_for: list[NonBlankStr] = Field(default_factory=list)
    retrieval_query: NonBlankStr
    retrieval_rank: int = Field(ge=1)


class SourceMetadata(StrictBaseModel):
    """C-A corpus/{source_id}/metadata.yaml."""

    source_id: NonBlankStr
    schema_version: ContractVersion
    bibliographic: SourceBibliographic
    trust_level: TrustLevel
    content_hash: HashValue
    retrieval: SourceRetrieval
    notes: str = ""


class ScaffoldPassage(StrictBaseModel):
    """Passage used by the scaffold from a source."""

    passage_id: NonBlankStr
    section: NonBlankStr | None = None
    paragraph_index: int = Field(ge=0)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    text_preview: NonBlankStr
    used_for_claims: list[NonBlankStr] = Field(default_factory=list)
    extraction_method: ExtractionMethod

    @model_validator(mode="after")
    def validate_offsets(self) -> Self:
        """Reject inverted character offsets."""
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self


class SourcePassages(StrictBaseModel):
    """C-A corpus/{source_id}/passages.yaml."""

    source_id: NonBlankStr
    schema_version: ContractVersion
    passages: list[ScaffoldPassage] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_passage_ids(self) -> Self:
        """Reject duplicate passage IDs within a source."""
        seen: set[str] = set()
        for passage in self.passages:
            if passage.passage_id in seen:
                raise ValueError(f"Duplicate passage_id: {passage.passage_id}")
            seen.add(passage.passage_id)
        return self

