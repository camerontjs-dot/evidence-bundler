"""C-A intake verification tests."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest

from evidence_bundler.contracts.hashing import write_sha256sums
from evidence_bundler.contracts.intake import verify_intake
from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.deviation import DeviationRecord

DeviationType = Literal[
    "intake_hash_mismatch",
    "schema_validation_failure",
    "vocabulary_drift",
    "missing_required_field",
]


def test_valid_synthetic_ca_passes_intake(scaffold_run_tmp: Path) -> None:
    result = verify_intake(scaffold_run_tmp)
    assert result.valid
    assert result.errors == ()
    assert result.artifact is not None
    assert result.artifact.manifest.run_id == "550e8400-e29b-41d4-a716-446655440000"


def test_tampered_synthetic_ca_fails_and_writes_deviation(scaffold_run_tmp: Path) -> None:
    content_path = scaffold_run_tmp / "corpus" / "src-001" / "content.md"
    tampered_content = content_path.read_text(encoding="utf-8") + "\nTampered.\n"
    content_path.write_text(tampered_content, encoding="utf-8")

    result = verify_intake(scaffold_run_tmp)

    assert not result.valid
    assert result.deviation_path is not None
    assert result.deviation_path.exists()
    assert result.deviation_path.name == "intake-550e8400-e29b-41d4-a716-446655440000.yaml"

    deviation = load_model_yaml(DeviationRecord, result.deviation_path)
    assert deviation.deviation_type == "intake_hash_mismatch"
    assert "corpus_hash" in deviation.description


@pytest.mark.parametrize(
    ("mutator_name", "expected_type"),
    [
        ("missing_contract_version", "missing_required_field"),
        ("wrong_contract_version", "vocabulary_drift"),
        ("missing_sha256sums", "missing_required_field"),
        ("malformed_claims_yaml", "schema_validation_failure"),
        ("invalid_workflow_condition", "schema_validation_failure"),
        ("missing_source_content", "missing_required_field"),
        ("missing_claim_passage_reference", "schema_validation_failure"),
    ],
)
def test_invalid_ca_inputs_fail_closed_with_typed_deviations(
    scaffold_run_tmp: Path,
    mutator_name: str,
    expected_type: DeviationType,
) -> None:
    """Representative bad C-A artifacts halt intake and record why."""
    _MUTATORS[mutator_name](scaffold_run_tmp)

    result = verify_intake(scaffold_run_tmp)

    assert not result.valid
    assert result.artifact is None or result.errors
    assert result.deviation_path is not None
    assert result.deviation_path.exists()

    deviation = load_model_yaml(DeviationRecord, result.deviation_path)
    assert deviation.deviation_type == expected_type
    assert deviation.resolution == "pending"


def _missing_contract_version(root: Path) -> None:
    (root / "CONTRACT_VERSION").unlink()


def _wrong_contract_version(root: Path) -> None:
    (root / "CONTRACT_VERSION").write_text("0.9.0\n", encoding="utf-8")


def _missing_sha256sums(root: Path) -> None:
    (root / "SHA256SUMS").unlink()


def _malformed_claims_yaml(root: Path) -> None:
    (root / "claims.yaml").write_text("claims: [\n", encoding="utf-8")


def _invalid_workflow_condition(root: Path) -> None:
    manifest_path = root / "scaffold_run.yaml"
    manifest = manifest_path.read_text(encoding="utf-8")
    manifest_path.write_text(
        manifest.replace('workflow_condition: "full_scaffold"', 'workflow_condition: "drifted"'),
        encoding="utf-8",
    )


def _missing_source_content(root: Path) -> None:
    (root / "corpus" / "src-001" / "content.md").unlink()


def _missing_claim_passage_reference(root: Path) -> None:
    claims_path = root / "claims.yaml"
    claims = claims_path.read_text(encoding="utf-8")
    claims_path.write_text(
        claims.replace('passage_id: "pass-001"', 'passage_id: "missing"'),
        encoding="utf-8",
    )
    write_sha256sums(root)


_MUTATORS = {
    "missing_contract_version": _missing_contract_version,
    "wrong_contract_version": _wrong_contract_version,
    "missing_sha256sums": _missing_sha256sums,
    "malformed_claims_yaml": _malformed_claims_yaml,
    "invalid_workflow_condition": _invalid_workflow_condition,
    "missing_source_content": _missing_source_content,
    "missing_claim_passage_reference": _missing_claim_passage_reference,
}
