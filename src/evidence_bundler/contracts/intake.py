"""C-A scaffold-run intake verification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml
from pydantic import ValidationError

from evidence_bundler import __version__
from evidence_bundler.contracts.hashing import (
    compute_corpus_hash,
    hash_file,
    verify_sha256sums,
)
from evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml
from evidence_bundler.models.ca import (
    ClaimsRegistry,
    ScaffoldRunManifest,
    SourceMetadata,
    SourcePassages,
)
from evidence_bundler.models.common import (
    CONTRACT_VERSION,
    SUPPORTED_CONTRACT_VERSIONS,
    DeviationType,
)
from evidence_bundler.models.deviation import DeviationRecord

CONTENT_SUFFIXES = {".md", ".txt", ".pdf"}


@dataclass(frozen=True)
class SourceArtifact:
    """Validated C-A source directory contents."""

    source_id: str
    source_dir: Path
    content_path: Path
    metadata: SourceMetadata
    passages: SourcePassages


@dataclass(frozen=True)
class ScaffoldRunArtifact:
    """Validated C-A scaffold-run artifact."""

    root: Path
    manifest: ScaffoldRunManifest
    claims: ClaimsRegistry
    sources: dict[str, SourceArtifact]


@dataclass(frozen=True)
class IntakeResult:
    """Result of fail-closed C-A intake verification."""

    valid: bool
    artifact: ScaffoldRunArtifact | None
    errors: tuple[str, ...]
    deviation_path: Path | None = None


class IntakeVerificationError(Exception):
    """Raised when C-A intake fails."""


def verify_intake(scaffold_run_dir: Path, *, deviation_dir: Path | None = None) -> IntakeResult:
    """Verify a C-A scaffold-run artifact before any bundle work begins."""
    scaffold_run_dir = scaffold_run_dir.resolve()
    artifact_id = scaffold_run_dir.name
    deviation_type: DeviationType = "intake_hash_mismatch"
    try:
        artifact = load_scaffold_run(scaffold_run_dir)
        artifact_id = artifact.manifest.run_id
        errors = list(_validate_artifact_integrity(artifact))
        deviation_type = _classify_integrity_errors(errors)
    except FileNotFoundError as exc:
        artifact = None
        errors = [str(exc)]
        deviation_type = "missing_required_field"
    except (ValidationError, yaml.YAMLError) as exc:
        artifact = None
        errors = [str(exc)]
        deviation_type = "schema_validation_failure"
    except ValueError as exc:
        artifact = None
        errors = [str(exc)]
        deviation_type = _classify_value_error(str(exc))

    if errors:
        deviation_path = write_intake_deviation(
            artifact_id=artifact_id,
            deviation_type=deviation_type,
            description="; ".join(errors),
            scaffold_run_dir=scaffold_run_dir,
            deviation_dir=deviation_dir,
        )
        return IntakeResult(
            valid=False,
            artifact=artifact,
            errors=tuple(errors),
            deviation_path=deviation_path,
        )

    return IntakeResult(valid=True, artifact=artifact, errors=())


def load_scaffold_run(scaffold_run_dir: Path) -> ScaffoldRunArtifact:
    """Load and schema-validate core C-A files."""
    if not scaffold_run_dir.is_dir():
        raise FileNotFoundError(f"Scaffold-run directory not found: {scaffold_run_dir}")

    manifest = load_model_yaml(ScaffoldRunManifest, scaffold_run_dir / "scaffold_run.yaml")
    claims = load_model_yaml(ClaimsRegistry, scaffold_run_dir / "claims.yaml")
    if claims.run_id != manifest.run_id:
        raise ValueError("claims.yaml run_id does not match scaffold_run.yaml run_id")

    corpus_dir = scaffold_run_dir / "corpus"
    if not corpus_dir.is_dir():
        raise FileNotFoundError("C-A corpus/ directory is missing")

    sources: dict[str, SourceArtifact] = {}
    for source_dir in sorted(path for path in corpus_dir.iterdir() if path.is_dir()):
        source_id = source_dir.name
        metadata = load_model_yaml(SourceMetadata, source_dir / "metadata.yaml")
        passages = load_model_yaml(SourcePassages, source_dir / "passages.yaml")
        content_path = _find_content_file(source_dir)

        if metadata.source_id != source_id:
            raise ValueError(f"metadata.yaml source_id mismatch for {source_id}")
        if passages.source_id != source_id:
            raise ValueError(f"passages.yaml source_id mismatch for {source_id}")

        sources[source_id] = SourceArtifact(
            source_id=source_id,
            source_dir=source_dir,
            content_path=content_path,
            metadata=metadata,
            passages=passages,
        )

    return ScaffoldRunArtifact(
        root=scaffold_run_dir,
        manifest=manifest,
        claims=claims,
        sources=sources,
    )


def write_intake_deviation(
    *,
    artifact_id: str,
    deviation_type: DeviationType,
    description: str,
    scaffold_run_dir: Path,
    deviation_dir: Path | None = None,
) -> Path:
    """Write a formal deviation record for failed intake."""
    destination = deviation_dir if deviation_dir is not None else scaffold_run_dir / "deviations"
    safe_artifact_id = artifact_id.replace("/", "-")
    deviation = DeviationRecord(
        deviation_id=f"dev-{safe_artifact_id}",
        deviation_type=deviation_type,
        artifact_id=artifact_id,
        detected_at_utc=_utc_now(),
        detected_by=f"evidence_bundler_v{__version__}",
        description=description,
        impact_assessment="Cannot proceed; bundle production halted.",
    )
    path = destination / f"intake-{safe_artifact_id}.yaml"
    write_model_yaml(deviation, path)
    return path


def _validate_artifact_integrity(artifact: ScaffoldRunArtifact) -> tuple[str, ...]:
    errors: list[str] = []

    contract_version_path = artifact.root / "CONTRACT_VERSION"
    if not contract_version_path.exists():
        errors.append("CONTRACT_VERSION file missing")
    else:
        version = contract_version_path.read_text(encoding="utf-8").strip()
        if version not in SUPPORTED_CONTRACT_VERSIONS:
            errors.append(
                f"CONTRACT_VERSION is {version!r}, "
                f"expected one of {sorted(SUPPORTED_CONTRACT_VERSIONS)!r} "
                f"(current emit version: {CONTRACT_VERSION!r})"
            )

    expected_corpus_hash = artifact.manifest.corpus.corpus_hash
    actual_corpus_hash = compute_corpus_hash(artifact.root / "corpus")
    if actual_corpus_hash != expected_corpus_hash:
        errors.append(
            "corpus_hash in scaffold_run.yaml does not match recomputed corpus/ hash "
            f"({expected_corpus_hash} != {actual_corpus_hash})"
        )

    if artifact.manifest.corpus.total_sources != len(artifact.sources):
        errors.append(
            "corpus.total_sources does not match source directories "
            f"({artifact.manifest.corpus.total_sources} != {len(artifact.sources)})"
        )

    for source in artifact.sources.values():
        actual_content_hash = hash_file(source.content_path)
        if actual_content_hash != source.metadata.content_hash:
            errors.append(
                f"content_hash mismatch for {source.source_id} "
                f"({source.metadata.content_hash} != {actual_content_hash})"
            )

    passage_keys = {
        (source_id, passage.passage_id)
        for source_id, source in artifact.sources.items()
        for passage in source.passages.passages
    }
    for claim in artifact.claims.claims:
        for source_ref in claim.source_refs:
            if (source_ref.source_id, source_ref.passage_id) not in passage_keys:
                errors.append(
                    f"claim {claim.claim_id} references missing passage "
                    f"{source_ref.source_id}/{source_ref.passage_id}"
                )

    errors.extend(verify_sha256sums(artifact.root))
    return tuple(errors)


def _classify_integrity_errors(errors: list[str]) -> DeviationType:
    """Map integrity-check failures to the locked deviation vocabulary."""
    if not errors:
        return "intake_hash_mismatch"
    if any(_is_contract_version_error(error) for error in errors):
        return "vocabulary_drift"
    if any(_is_missing_required_error(error) for error in errors):
        return "missing_required_field"
    if any(_is_hash_error(error) for error in errors):
        return "intake_hash_mismatch"
    return "schema_validation_failure"


def _classify_value_error(message: str) -> DeviationType:
    """Classify load-time ValueError messages."""
    if _is_contract_version_error(message):
        return "vocabulary_drift"
    if _is_missing_required_error(message):
        return "missing_required_field"
    if _is_hash_error(message):
        return "intake_hash_mismatch"
    return "schema_validation_failure"


def _is_contract_version_error(message: str) -> bool:
    return "CONTRACT_VERSION is" in message or "CONTRACT_VERSION mismatch" in message


def _is_missing_required_error(message: str) -> bool:
    missing_patterns = (
        "file missing",
        "File does not exist",
        "directory is missing",
        "directory not found",
        "not found:",
        "references missing file",
        "Expected one content.",
    )
    return any(pattern in message for pattern in missing_patterns)


def _is_hash_error(message: str) -> bool:
    hash_patterns = (
        "corpus_hash",
        "content_hash mismatch",
        "SHA256SUMS mismatch",
        "SHA256SUMS missing entries",
    )
    return any(pattern in message for pattern in hash_patterns)


def _find_content_file(source_dir: Path) -> Path:
    content_files = [
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.stem == "content" and path.suffix in CONTENT_SUFFIXES
    ]
    if len(content_files) != 1:
        raise FileNotFoundError(f"Expected one content.{{md,txt,pdf}} file in {source_dir}")
    return content_files[0]


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
