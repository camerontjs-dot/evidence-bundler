"""Shared contract model primitives."""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

ContractVersion: TypeAlias = Literal["1.0.0", "1.1.0"]
CONTRACT_VERSION: ContractVersion = "1.1.0"
SUPPORTED_CONTRACT_VERSIONS: frozenset[str] = frozenset({"1.0.0", "1.1.0"})
PENDING_HASH = "sha256:pending"

NonBlankStr: TypeAlias = Annotated[str, Field(min_length=1)]
HashValue: TypeAlias = Annotated[
    str,
    Field(pattern=r"^sha256:([a-f0-9]{64}|pending)$"),
]

WorkflowCondition: TypeAlias = Literal[
    "baseline",
    "format_only",
    "provenance_scaffold",
    "full_scaffold",
]
ClaimType: TypeAlias = Literal["retrieval_seed", "extracted_claim"]
SupportStatus: TypeAlias = Literal["sourced", "inferred", "uncertain", "unsupported"]
AuditSupportVerdict: TypeAlias = Literal[
    "supported",
    "partially_supported",
    "unsupported",
    "overstated",
    "needs_source",
    "not_checkable",
]
SourceType: TypeAlias = Literal[
    "journal_article",
    "regulatory_guidance",
    "preprint",
    "web_page",
    "book",
    "other",
]
TrustLevel: TypeAlias = Literal["primary", "secondary", "background"]
ExtractionMethod: TypeAlias = Literal["scaffold_cited", "scaffold_inferred", "auto_retrieved"]
DeviationType: TypeAlias = Literal[
    "intake_hash_mismatch",
    "schema_validation_failure",
    "vocabulary_drift",
    "missing_required_field",
    "other",
]


class StrictBaseModel(BaseModel):
    """Base model that rejects schema drift and normalizes surrounding whitespace."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

