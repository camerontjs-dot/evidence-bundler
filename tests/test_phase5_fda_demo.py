"""Phase 5 FDA guidance real-corpus demo tests."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType

import yaml

from evidence_bundler.contracts.hashing import hash_file
from evidence_bundler.contracts.intake import verify_intake
from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.ca import ClaimsRegistry

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "scripts" / "run_phase_5_fda_guidance_demo.py"
PHASE5_DRAFT = REPO_ROOT / "examples" / "phase-5-draft"


def test_phase5_claims_registry_validates() -> None:
    registry = load_model_yaml(ClaimsRegistry, PHASE5_DRAFT / "claims.yaml")

    assert {claim.claim_id for claim in registry.claims} == {
        "clm-qms-coverage",
        "clm-validation-exemption",
        "clm-apr-scope",
        "clm-capa-risk",
        "clm-equipment-requalification",
        "clm-clinical-endpoint",
        "clm-supplier-qualification",
        "clm-stability-extension",
    }


def test_phase5_source_manifest_is_pinned() -> None:
    manifest = yaml.safe_load((PHASE5_DRAFT / "source-manifest.yaml").read_text())

    sources = manifest["sources"]
    assert len(sources) == 1
    assert sources[0]["source_id"] == "src-cgmp-quality-systems"
    assert sources[0]["retrieval_date"] == "2026-05-13"
    assert sources[0]["expected_sha256"] == (
        "69fa9da511ea1d5b59f780700a3ee2c5e949e9add538781cdf1aaaa7d613a32a"
    )


def test_phase5_scaffold_builder_writes_valid_ca_artifact(tmp_path: Path) -> None:
    runner = _load_runner()
    source_pdf = (
        REPO_ROOT
        / "tests"
        / "fixtures"
        / "scaffold-run-mixed-formats"
        / "corpus"
        / "src-pdf"
        / "content.pdf"
    )
    staged_pdf = tmp_path / "src-cgmp-quality-systems.pdf"
    shutil.copy2(source_pdf, staged_pdf)
    manifest = yaml.safe_load((PHASE5_DRAFT / "source-manifest.yaml").read_text())
    manifest["sources"][0]["expected_sha256"] = hash_file(staged_pdf).removeprefix("sha256:")
    source = runner.DownloadedSource(
        source_id="src-cgmp-quality-systems",
        path=staged_pdf,
        sha256=manifest["sources"][0]["expected_sha256"],
        source_manifest=manifest["sources"][0],
    )

    scaffold_dir = tmp_path / "scaffold-run-fda-guidance"
    runner._build_scaffold(scaffold_dir, [source], manifest)
    result = verify_intake(scaffold_dir)

    assert result.valid, result.errors
    assert (scaffold_dir / "SHA256SUMS").exists()


def test_phase5_output_dir_refuses_nonempty_without_force(tmp_path: Path) -> None:
    runner = _load_runner()
    output_dir = tmp_path / "demo-output"
    output_dir.mkdir()
    (output_dir / "existing.txt").write_text("already here", encoding="utf-8")

    try:
        runner._prepare_output_dir(output_dir, force=False)
    except SystemExit as exc:
        message = str(exc)
    else:  # pragma: no cover - defensive clarity for assertion failures.
        raise AssertionError("Expected SystemExit for non-empty output without --force")

    assert "Output directory is not empty" in message


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("phase5_runner", RUNNER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
