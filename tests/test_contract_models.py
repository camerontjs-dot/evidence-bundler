"""Schema model round-trip tests."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from evidence_bundler.contracts.writer import build_fixture_bundle
from evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml
from evidence_bundler.models.ca import (
    ClaimsRegistry,
    ScaffoldRunManifest,
    SourceMetadata,
    SourcePassages,
)
from evidence_bundler.models.cb import BundleManifest, ClaimAuditUnit


def roundtrip_model(model: BaseModel, model_type: type[BaseModel], tmp_path: Path) -> BaseModel:
    """Write and reload a model through safe YAML."""
    out = tmp_path / f"{model_type.__name__}.yaml"
    write_model_yaml(model, out)
    return load_model_yaml(model_type, out)


def test_ca_models_roundtrip(fixture_scaffold_run_dir: Path, tmp_path: Path) -> None:
    manifest = load_model_yaml(ScaffoldRunManifest, fixture_scaffold_run_dir / "scaffold_run.yaml")
    claims = load_model_yaml(ClaimsRegistry, fixture_scaffold_run_dir / "claims.yaml")
    metadata = load_model_yaml(
        SourceMetadata,
        fixture_scaffold_run_dir / "corpus" / "src-001" / "metadata.yaml",
    )
    passages = load_model_yaml(
        SourcePassages,
        fixture_scaffold_run_dir / "corpus" / "src-001" / "passages.yaml",
    )

    assert roundtrip_model(manifest, ScaffoldRunManifest, tmp_path) == manifest
    assert roundtrip_model(claims, ClaimsRegistry, tmp_path) == claims
    assert roundtrip_model(metadata, SourceMetadata, tmp_path) == metadata
    assert roundtrip_model(passages, SourcePassages, tmp_path) == passages


def test_cb_models_roundtrip(scaffold_run_tmp: Path, tmp_path: Path) -> None:
    bundle_dir = tmp_path / "evidence-bundle-fixture"
    build_fixture_bundle(scaffold_run_tmp, bundle_dir)

    manifest = load_model_yaml(BundleManifest, bundle_dir / "bundle_manifest.yaml")
    claim_unit = load_model_yaml(ClaimAuditUnit, bundle_dir / "claims" / "clm-001.yaml")

    assert roundtrip_model(manifest, BundleManifest, tmp_path) == manifest
    assert roundtrip_model(claim_unit, ClaimAuditUnit, tmp_path) == claim_unit
