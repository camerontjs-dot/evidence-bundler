"""YAML I/O for review annotations outside sealed draft bundles."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from evidence_bundler.contracts.hashing import compute_bundle_tree_hash, hash_text
from evidence_bundler.contracts.yaml_io import (
    load_model_yaml,
    model_to_yaml_dict,
    write_model_yaml,
    yaml_to_string,
)
from evidence_bundler.models.cb import BundleManifest, ClaimAuditUnit
from evidence_bundler.models.review import ReviewAnnotation, ReviewAnnotationFile


class ReviewAnnotationDriftError(ValueError):
    """Raised when annotations no longer match their draft bundle anchors."""


def scaffold_annotations_from_bundle(draft_bundle_dir: Path) -> ReviewAnnotationFile:
    """Create default review annotations for every candidate in a draft C-B bundle."""
    manifest = _load_manifest(draft_bundle_dir)
    annotations: list[ReviewAnnotation] = []
    for claim_path in sorted((draft_bundle_dir / "claims").glob("*.yaml")):
        claim = load_model_yaml(ClaimAuditUnit, claim_path)
        for passage in claim.evidence_passages:
            annotations.append(
                ReviewAnnotation(
                    claim_id=claim.claim_id,
                    passage_id=passage.passage_id,
                    source_id=passage.source_id,
                    evidence_role="supporting",
                )
            )
        for passage in claim.counterevidence_passages:
            # C-B v1.0.0 stores counter-candidates in one container, so Unit 1 cannot
            # recover ADR-010's contradicting-vs-conditional distinction from claim YAML.
            annotations.append(
                ReviewAnnotation(
                    claim_id=claim.claim_id,
                    passage_id=passage.passage_id,
                    source_id=passage.source_id,
                    evidence_role="contradicting",
                )
            )

    return ReviewAnnotationFile(
        draft_bundle_id=manifest.bundle_id,
        draft_bundle_hash=compute_bundle_tree_hash(draft_bundle_dir),
        retrieval_config_hash=manifest.evidence_builder.config_hash,
        generated_at_utc=_utc_now(),
        annotations=sorted(
            annotations,
            key=lambda annotation: (
                annotation.claim_id,
                annotation.source_id,
                annotation.passage_id,
            ),
        ),
    )


def write_review_annotations(file: ReviewAnnotationFile, path: Path) -> None:
    """Write a review annotation artifact through deterministic model YAML."""
    write_model_yaml(file, path)


def compute_review_annotations_hash(path: Path) -> str:
    """Hash review annotations from canonical model YAML, not raw file bytes."""
    file = load_model_yaml(ReviewAnnotationFile, path)
    return hash_text(yaml_to_string(model_to_yaml_dict(file)))


def load_review_annotations(path: Path, draft_bundle_dir: Path) -> ReviewAnnotationFile:
    """Load annotations and fail closed if the draft bundle drifted."""
    file = load_model_yaml(ReviewAnnotationFile, path)
    manifest = _load_manifest(draft_bundle_dir)

    if file.draft_bundle_id != manifest.bundle_id:
        raise ReviewAnnotationDriftError(
            "draft bundle-id mismatch: "
            f"annotations={file.draft_bundle_id!r} bundle={manifest.bundle_id!r}"
        )

    actual_bundle_hash = compute_bundle_tree_hash(draft_bundle_dir)
    if file.draft_bundle_hash != actual_bundle_hash:
        raise ReviewAnnotationDriftError(
            "draft bundle-hash mismatch: "
            f"annotations={file.draft_bundle_hash!r} bundle={actual_bundle_hash!r}"
        )

    actual_config_hash = manifest.evidence_builder.config_hash
    if file.retrieval_config_hash != actual_config_hash:
        raise ReviewAnnotationDriftError(
            "retrieval config-hash mismatch: "
            f"annotations={file.retrieval_config_hash!r} bundle={actual_config_hash!r}"
        )

    return file


def _load_manifest(draft_bundle_dir: Path) -> BundleManifest:
    return load_model_yaml(BundleManifest, draft_bundle_dir / "bundle_manifest.yaml")


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
