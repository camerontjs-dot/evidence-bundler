from __future__ import annotations

from evidence_bundler.models.ca import SourceBibliographic
from evidence_bundler.models.cb import (
    BundleManifest,
    ClaimAuditUnit,
    ClaimEvidencePassage,
    SourceProfile,
)
from evidence_bundler.models.common import StrictBaseModel


def test_canonical_models_reject_undeclared_context_fields() -> None:
    assert StrictBaseModel.model_config["extra"] == "forbid"


def test_current_claim_unit_is_apparatus_bound_and_cal_shaped() -> None:
    fields = set(ClaimAuditUnit.model_fields)

    assert {
        "workflow_condition",
        "task_id",
        "scaffold_support_status",
        "scaffold_claim_strength",
        "scaffold_extraction_fidelity",
        "scaffold_counterevidence_found",
        "scaffold_downgraded",
    } <= fields
    assert "audit" in fields


def test_current_claim_unit_has_no_general_origin_atomicity_or_coverage_surface() -> None:
    fields = set(ClaimAuditUnit.model_fields)

    assert "origin" not in fields
    assert "atomicity" not in fields
    assert "coverage" not in fields
    assert "admission" not in fields
    assert "nomination" not in fields


def test_current_source_surface_cannot_encode_annex22_style_status_context() -> None:
    source_fields = set(SourceProfile.model_fields)
    bibliographic_fields = set(SourceBibliographic.model_fields)
    combined = source_fields | bibliographic_fields

    assert "document_status" not in combined
    assert "jurisdiction" not in combined
    assert "version_label" not in combined
    assert "effective_date" not in combined
    assert "context_facts" not in combined


def test_current_passage_surface_has_offsets_but_no_representation_bound_typed_anchors() -> None:
    fields = set(ClaimEvidencePassage.model_fields)

    assert {"section", "char_start", "char_end"} <= fields
    assert "anchors" not in fields
    assert "representation_id" not in fields
    assert "representation_hash" not in fields


def test_current_manifest_pins_downstream_cal_configuration() -> None:
    fields = set(BundleManifest.model_fields)

    assert {
        "audit_config_version",
        "audit_config_hash",
        "validation_set_version",
        "validation_set_hash",
    } <= fields


def test_current_semantic_lane_split_is_part_of_claim_unit_shape() -> None:
    fields = set(ClaimAuditUnit.model_fields)

    assert "evidence_passages" in fields
    assert "counterevidence_passages" in fields
