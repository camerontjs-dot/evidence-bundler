"""Deviation records emitted when contract intake fails closed."""

from __future__ import annotations

from evidence_bundler.models.common import DeviationType, NonBlankStr, StrictBaseModel


class DeviationRecord(StrictBaseModel):
    """Formal deviation record for a failed handoff integrity check."""

    deviation_id: NonBlankStr
    deviation_type: DeviationType
    artifact_id: NonBlankStr
    detected_at_utc: NonBlankStr
    detected_by: NonBlankStr
    description: NonBlankStr
    impact_assessment: NonBlankStr
    resolution: NonBlankStr = "pending"
    capa_notes: str = ""

