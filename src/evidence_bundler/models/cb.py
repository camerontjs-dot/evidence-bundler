"""Pydantic models for C-B evidence-bundle artifacts."""

from __future__ import annotations

from pydantic import Field

from evidence_bundler.models.ca import SourceBibliographic
from evidence_bundler.models.common import (
    AuditSupportVerdict,
    ClaimType,
    ContractVersion,
    ExtractionMethod,
    HashValue,
    NonBlankStr,
    StrictBaseModel,
    SupportStatus,
    TrustLevel,
    WorkflowCondition,
)


class EvidenceBuilderInfo(StrictBaseModel):
    """Bundler runtime state recorded in bundle_manifest.yaml."""

    version: NonBlankStr
    config_hash: HashValue
    operator: NonBlankStr
    build_timestamp_utc: NonBlankStr


class BundleStats(StrictBaseModel):
    """Bundle claim and passage counts."""

    total_claims_in_source: int = Field(ge=0)
    claims_included: int = Field(ge=0)
    claims_excluded: int = Field(ge=0)
    exclusion_rationale: str
    total_evidence_passages: int = Field(ge=0)
    bundle_hash: HashValue


class TransformationRecord(StrictBaseModel):
    """Transformation applied while preparing the C-B bundle."""

    type: NonBlankStr
    description: NonBlankStr
    claims_affected: list[NonBlankStr] = Field(default_factory=list)


class QualityGates(StrictBaseModel):
    """Seal-time quality gate outcomes."""

    every_claim_has_at_least_one_passage: bool
    every_passage_links_to_source_profile: bool
    source_hashes_verified: bool
    bundle_integrity_verified: bool


class ReviewerSignOff(StrictBaseModel):
    """Deferred 21 CFR Part 11 sign-off surface."""

    required: bool = False
    signed_by: NonBlankStr | None = None
    signature_timestamp_utc: NonBlankStr | None = None
    signature_notes: str | None = None


class BundleManifest(StrictBaseModel):
    """C-B bundle_manifest.yaml certificate of analysis."""

    bundle_id: NonBlankStr
    schema_version: ContractVersion
    generated_at_utc: NonBlankStr
    source_run_id: NonBlankStr
    source_contract_version: ContractVersion
    source_corpus_hash: HashValue
    evidence_builder: EvidenceBuilderInfo
    bundle: BundleStats
    transformations: list[TransformationRecord] = Field(default_factory=list)
    quality_gates: QualityGates
    audit_config_version: NonBlankStr
    audit_config_hash: HashValue
    validation_set_version: NonBlankStr
    validation_set_hash: HashValue
    reviewer_sign_off: ReviewerSignOff


class ClaimEvidencePassage(StrictBaseModel):
    """Passage embedded into a self-contained claim audit unit."""

    passage_id: NonBlankStr
    source_id: NonBlankStr
    passage_text: NonBlankStr
    section: NonBlankStr | None = None
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    source_trust_level: TrustLevel
    passage_hash: HashValue


class AuditFields(StrictBaseModel):
    """Claim Audit Lab target fields; all null at Evidence Bundler handoff."""

    audit_run_id: NonBlankStr | None = None
    audited_at_utc: NonBlankStr | None = None
    audit_support_verdict: AuditSupportVerdict | None = None
    audit_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    audit_notes: str | None = None
    false_caution_flag: bool | None = None
    deviation_flag: bool | None = None
    deviation_notes: str | None = None


class ClaimAuditUnit(StrictBaseModel):
    """C-B claims/{claim_id}.yaml self-contained audit unit."""

    claim_id: NonBlankStr
    bundle_id: NonBlankStr
    schema_version: ContractVersion
    claim_text: NonBlankStr
    claim_type: ClaimType
    workflow_condition: WorkflowCondition
    task_id: NonBlankStr
    scaffold_support_status: SupportStatus
    scaffold_claim_strength: float = Field(ge=0.0, le=1.0)
    scaffold_extraction_fidelity: float = Field(ge=0.0, le=1.0)
    scaffold_counterevidence_found: bool
    scaffold_downgraded: bool
    evidence_passages: list[ClaimEvidencePassage] = Field(default_factory=list)
    counterevidence_passages: list[ClaimEvidencePassage] = Field(default_factory=list)
    audit: AuditFields = Field(default_factory=AuditFields)


class PassageProvenance(StrictBaseModel):
    """Full C-A to C-B lineage for a passage record."""

    source_url: NonBlankStr
    source_access_date_utc: NonBlankStr
    source_content_hash: HashValue
    scaffold_run_id: NonBlankStr
    evidence_builder_version: NonBlankStr
    bundle_created_at_utc: NonBlankStr


class PassageRecord(StrictBaseModel):
    """C-B evidence/{source_id}/passages/{passage_id}.yaml."""

    passage_id: NonBlankStr
    source_id: NonBlankStr
    bundle_id: NonBlankStr
    schema_version: ContractVersion
    passage_text: NonBlankStr
    section: NonBlankStr | None = None
    paragraph_index: int = Field(ge=0)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    passage_hash: HashValue
    cited_by_claims: list[NonBlankStr] = Field(default_factory=list)
    extraction_method: ExtractionMethod
    provenance: PassageProvenance


class SourceProfile(StrictBaseModel):
    """Abbreviated source identity copied into C-B without raw source content."""

    source_id: NonBlankStr
    schema_version: ContractVersion
    bibliographic: SourceBibliographic
    trust_level: TrustLevel
    content_hash: HashValue
    retrieved_for: list[NonBlankStr] = Field(default_factory=list)
    retrieval_query: NonBlankStr
    retrieval_rank: int = Field(ge=1)
    notes: str = ""


class AuditScoringConfig(StrictBaseModel):
    """Frozen audit scoring thresholds."""

    support_threshold_sourced: float = Field(ge=0.0, le=1.0)
    support_threshold_partial: float = Field(ge=0.0, le=1.0)
    counterevidence_weight: float = Field(ge=0.0, le=1.0)


class AuditRulePolicies(StrictBaseModel):
    """Frozen audit rule switches."""

    require_passage_level_match: bool
    flag_unsupported_threshold: float = Field(ge=0.0, le=1.0)
    false_caution_detection: bool
    false_caution_threshold: float = Field(ge=0.0, le=1.0)
    overstated_detection: bool
    needs_source_detection: bool


class AuditConfigChange(StrictBaseModel):
    """Audit config change-log entry."""

    version: NonBlankStr
    date: NonBlankStr
    changes: NonBlankStr
    rationale: NonBlankStr


class AuditConfig(StrictBaseModel):
    """C-B audit_config.yaml frozen audit rules."""

    config_id: NonBlankStr
    config_hash: HashValue
    schema_version: ContractVersion
    frozen_at_utc: NonBlankStr
    scoring: AuditScoringConfig
    rule_policies: AuditRulePolicies
    known_limitations: list[NonBlankStr] = Field(default_factory=list)
    change_log: list[AuditConfigChange] = Field(default_factory=list)


class ValidationSetRef(StrictBaseModel):
    """C-B validation_set_ref.yaml pointer."""

    schema_version: ContractVersion
    validation_set_version: NonBlankStr
    validation_set_hash: HashValue
    frozen_at_utc: NonBlankStr
    description: NonBlankStr
    notes: str = ""

