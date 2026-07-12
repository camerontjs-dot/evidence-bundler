"""Finalize reviewed C-B bundles from draft bundles and review sidecars."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from shutil import rmtree
from uuid import NAMESPACE_URL, uuid4, uuid5

from evidence_bundler import __version__
from evidence_bundler.contracts.hashing import (
    compute_bundle_tree_hash,
    hash_text,
    write_sha256sums,
)
from evidence_bundler.contracts.writer import validate_bundle_tree
from evidence_bundler.contracts.yaml_io import (
    load_model_yaml,
    model_to_yaml_dict,
    write_model_yaml,
    yaml_to_string,
)
from evidence_bundler.models.cb import (
    AuditConfig,
    BundleManifest,
    ClaimAuditUnit,
    ClaimEvidencePassage,
    EvidenceBuilderInfo,
    PassageRecord,
    ReviewerSignOff,
    SourceProfile,
    TransformationRecord,
    ValidationSetRef,
)
from evidence_bundler.models.common import (
    CONTRACT_VERSION,
    PENDING_HASH,
    ContractVersion,
    HashValue,
    NonBlankStr,
    StrictBaseModel,
)
from evidence_bundler.models.refinement import (
    ExcerptRefinementFile,
    ExcerptRefinementMember,
)
from evidence_bundler.models.review import ReviewAnnotation, ReviewDecision
from evidence_bundler.output.refiner import load_excerpt_refinement
from evidence_bundler.review.io import (
    compute_review_annotations_hash,
    load_review_annotations,
)


class FinalizeBundleError(ValueError):
    """Raised when a reviewed bundle cannot be finalized safely."""


class FinalizeProvenanceFile(StrictBaseModel):
    """Sidecar provenance record for the finalization step."""

    schema_version: ContractVersion = CONTRACT_VERSION

    draft_bundle_id: NonBlankStr
    draft_bundle_hash: HashValue
    annotation_path: NonBlankStr
    annotation_hash: HashValue
    refinement_path: NonBlankStr
    refinement_hash: HashValue
    final_bundle_id: NonBlankStr
    final_bundle_hash: HashValue
    generated_at_utc: NonBlankStr


@dataclass(frozen=True)
class FinalizeBundleResult:
    """Result returned after writing a finalized reviewed bundle."""

    bundle_dir: Path
    provenance_path: Path
    manifest: BundleManifest
    provenance: FinalizeProvenanceFile


@dataclass(frozen=True)
class _DraftCandidate:
    annotation: ReviewAnnotation
    passage: ClaimEvidencePassage
    container: str


@dataclass(frozen=True)
class _FinalPassageUse:
    claim_id: str
    annotation: ReviewAnnotation
    draft_candidate: _DraftCandidate


_CandidateKey = tuple[str, str, str]


def finalize_bundle(
    draft_bundle_dir: Path,
    annotation_path: Path,
    refinement_path: Path,
    output_dir: Path,
    *,
    provenance_path: Path | None = None,
    generated_at_utc: str | None = None,
) -> FinalizeBundleResult:
    """Write a reviewed C-B bundle from a draft bundle and Phase 3 sidecars."""
    draft_bundle_dir = draft_bundle_dir.resolve()
    annotation_path = annotation_path.resolve()
    refinement_path = refinement_path.resolve()
    output_dir = output_dir.resolve()
    provenance_path = (
        provenance_path.resolve()
        if provenance_path is not None
        else _default_provenance_path(output_dir)
    )
    generated_at = generated_at_utc or _utc_now()

    _assert_output_outside_draft(draft_bundle_dir, output_dir)
    _assert_output_ready(output_dir)
    _assert_sidecar_outside_bundle(output_dir, provenance_path, "Finalize provenance")
    _assert_sidecar_outside_bundle(draft_bundle_dir, provenance_path, "Finalize provenance")
    _assert_provenance_ready(provenance_path)

    before_draft_hash = compute_bundle_tree_hash(draft_bundle_dir)
    annotations = load_review_annotations(annotation_path, draft_bundle_dir)
    refinement = load_excerpt_refinement(refinement_path, draft_bundle_dir, annotation_path)
    annotation_hash = compute_review_annotations_hash(annotation_path)
    refinement_hash = compute_excerpt_refinement_hash(refinement_path)

    draft_manifest = _load_manifest(draft_bundle_dir)
    claims = _load_claims(draft_bundle_dir)
    draft_candidates = _load_draft_candidates(claims, annotations.annotations)
    _validate_exact_annotation_coverage(draft_candidates, annotations.annotations)
    replacements = _cluster_replacements(refinement, annotations.annotations)
    final_uses = _final_passage_uses(draft_candidates, replacements)
    final_bundle_id = str(
        uuid5(
            NAMESPACE_URL,
            (
                "evidence-bundler-final:"
                f"{draft_manifest.bundle_id}:{annotation_hash}:{refinement_hash}"
            ),
        )
    )

    tmp_dir = output_dir.parent / f".{output_dir.name}.tmp-{uuid4().hex}"
    try:
        _write_final_bundle(
            draft_bundle_dir=draft_bundle_dir,
            output_dir=tmp_dir,
            draft_manifest=draft_manifest,
            claims=claims,
            final_uses=final_uses,
            final_bundle_id=final_bundle_id,
            generated_at_utc=generated_at,
            annotation_hash=annotation_hash,
            refinement_hash=refinement_hash,
        )
        manifest = _load_manifest(tmp_dir)
        if output_dir.exists():
            output_dir.rmdir()
        tmp_dir.rename(output_dir)
    except Exception:
        if tmp_dir.exists():
            rmtree(tmp_dir)
        raise

    if compute_bundle_tree_hash(draft_bundle_dir) != before_draft_hash:
        if output_dir.exists():
            rmtree(output_dir)
        raise FinalizeBundleError("Draft bundle changed while finalizing reviewed bundle.")

    provenance = FinalizeProvenanceFile(
        draft_bundle_id=draft_manifest.bundle_id,
        draft_bundle_hash=before_draft_hash,
        annotation_path=annotation_path.as_posix(),
        annotation_hash=annotation_hash,
        refinement_path=refinement_path.as_posix(),
        refinement_hash=refinement_hash,
        final_bundle_id=manifest.bundle_id,
        final_bundle_hash=manifest.bundle.bundle_hash,
        generated_at_utc=generated_at,
    )
    write_model_yaml(provenance, provenance_path)
    return FinalizeBundleResult(
        bundle_dir=output_dir,
        provenance_path=provenance_path,
        manifest=manifest,
        provenance=provenance,
    )


def compute_excerpt_refinement_hash(path: Path) -> str:
    """Hash excerpt refinement from canonical model YAML, not raw file bytes."""
    file = load_model_yaml(ExcerptRefinementFile, path)
    return hash_text(yaml_to_string(model_to_yaml_dict(file)))


def _write_final_bundle(
    *,
    draft_bundle_dir: Path,
    output_dir: Path,
    draft_manifest: BundleManifest,
    claims: dict[str, ClaimAuditUnit],
    final_uses: list[_FinalPassageUse],
    final_bundle_id: str,
    generated_at_utc: str,
    annotation_hash: str,
    refinement_hash: str,
) -> None:
    output_dir.mkdir(parents=True)
    _write_contract_version(output_dir)
    _copy_audit_config(draft_bundle_dir, output_dir)
    _copy_validation_set_ref(draft_bundle_dir, output_dir)

    passage_records = _load_passage_records(draft_bundle_dir)
    source_profiles = _load_source_profiles(draft_bundle_dir)
    uses_by_claim = _uses_by_claim(final_uses)
    cited_by_passage = _cited_by_passage(final_uses)
    final_passage_records = _final_passage_records(
        passage_records=passage_records,
        cited_by_passage=cited_by_passage,
        final_bundle_id=final_bundle_id,
        generated_at_utc=generated_at_utc,
    )
    _write_source_profiles(output_dir, source_profiles, final_passage_records)
    _write_passage_records(output_dir, final_passage_records)
    _write_claims(
        output_dir=output_dir,
        claims=claims,
        uses_by_claim=uses_by_claim,
        final_bundle_id=final_bundle_id,
    )

    reviewer_sign_off_required = any(
        use.annotation.decision == "needs-review" for use in final_uses
    )
    manifest = _final_manifest(
        draft_manifest=draft_manifest,
        final_bundle_id=final_bundle_id,
        generated_at_utc=generated_at_utc,
        total_evidence_passages=len(final_passage_records),
        every_claim_has_at_least_one_passage=all(
            bool(uses_by_claim.get(claim_id)) for claim_id in claims
        ),
        reviewer_sign_off_required=reviewer_sign_off_required,
    )
    manifest_path = output_dir / "bundle_manifest.yaml"
    write_model_yaml(manifest, manifest_path)
    manifest = manifest.model_copy(
        update={
            "bundle": manifest.bundle.model_copy(
                update={"bundle_hash": compute_bundle_tree_hash(output_dir)}
            )
        }
    )
    write_model_yaml(manifest, manifest_path)
    write_sha256sums(output_dir)
    errors = validate_bundle_tree(output_dir)
    if errors:
        raise FinalizeBundleError("; ".join(errors))


def _load_manifest(bundle_dir: Path) -> BundleManifest:
    return load_model_yaml(BundleManifest, bundle_dir / "bundle_manifest.yaml")


def _load_claims(bundle_dir: Path) -> dict[str, ClaimAuditUnit]:
    claims: dict[str, ClaimAuditUnit] = {}
    for claim_path in sorted((bundle_dir / "claims").glob("*.yaml")):
        claim = load_model_yaml(ClaimAuditUnit, claim_path)
        if claim.claim_id in claims:
            raise FinalizeBundleError(f"Duplicate claim file for claim_id: {claim.claim_id}")
        claims[claim.claim_id] = claim
    return claims


def _load_draft_candidates(
    claims: dict[str, ClaimAuditUnit],
    annotations: list[ReviewAnnotation],
) -> dict[_CandidateKey, _DraftCandidate]:
    annotation_by_key = _annotation_by_key(annotations)
    candidates: dict[_CandidateKey, _DraftCandidate] = {}
    missing: list[_CandidateKey] = []
    for claim in claims.values():
        for passage in claim.evidence_passages:
            key = (claim.claim_id, passage.source_id, passage.passage_id)
            if key in candidates:
                raise FinalizeBundleError(f"Duplicate draft candidate: {_format_key(key)}")
            annotation = annotation_by_key.get(key)
            if annotation is None:
                missing.append(key)
                continue
            if annotation.evidence_role != "supporting":
                raise FinalizeBundleError(
                    "Review annotation role does not match draft evidence container: "
                    f"{_format_key(key)} role={annotation.evidence_role!r}"
                )
            candidates[key] = _DraftCandidate(
                annotation=annotation,
                passage=passage,
                container="evidence",
            )
        for passage in claim.counterevidence_passages:
            key = (claim.claim_id, passage.source_id, passage.passage_id)
            if key in candidates:
                raise FinalizeBundleError(f"Duplicate draft candidate: {_format_key(key)}")
            annotation = annotation_by_key.get(key)
            if annotation is None:
                missing.append(key)
                continue
            if annotation.evidence_role not in {"contradicting", "conditional"}:
                raise FinalizeBundleError(
                    "Review annotation role does not match draft counterevidence container: "
                    f"{_format_key(key)} role={annotation.evidence_role!r}"
                )
            candidates[key] = _DraftCandidate(
                annotation=annotation,
                passage=passage,
                container="counterevidence",
            )
    if missing:
        raise FinalizeBundleError(
            "Review annotations missing draft candidate(s): "
            + ", ".join(_format_key(key) for key in sorted(missing))
        )
    return candidates


def _validate_exact_annotation_coverage(
    draft_candidates: dict[_CandidateKey, _DraftCandidate],
    annotations: list[ReviewAnnotation],
) -> None:
    draft_keys = set(draft_candidates)
    annotation_keys = {_annotation_key(annotation) for annotation in annotations}
    missing = sorted(draft_keys - annotation_keys)
    extra = sorted(annotation_keys - draft_keys)
    if missing:
        raise FinalizeBundleError(
            "Review annotations missing draft candidate(s): "
            + ", ".join(_format_key(key) for key in missing)
        )
    if extra:
        raise FinalizeBundleError(
            "Review annotations reference unknown draft candidate(s): "
            + ", ".join(_format_key(key) for key in extra)
        )


def _annotation_by_key(
    annotations: list[ReviewAnnotation],
) -> dict[_CandidateKey, ReviewAnnotation]:
    by_key: dict[_CandidateKey, ReviewAnnotation] = {}
    for annotation in annotations:
        key = _annotation_key(annotation)
        if key in by_key:
            raise FinalizeBundleError(f"Duplicate review annotation: {_format_key(key)}")
        by_key[key] = annotation
    return by_key


def _cluster_replacements(
    refinement: ExcerptRefinementFile,
    annotations: list[ReviewAnnotation],
) -> dict[_CandidateKey, _CandidateKey]:
    annotation_by_key = _annotation_by_key(annotations)
    replacements: dict[_CandidateKey, _CandidateKey] = {}
    seen_members: set[_CandidateKey] = set()
    for cluster in refinement.clusters:
        member_keys = [_member_key(member) for member in cluster.members]
        representative_key = _member_key(cluster.representative)
        if representative_key not in member_keys:
            raise FinalizeBundleError(
                f"Refinement cluster {cluster.cluster_id} representative is not a member."
            )
        for member in cluster.members:
            key = _member_key(member)
            if key in seen_members:
                raise FinalizeBundleError(
                    f"Refinement member appears in multiple clusters: {_format_key(key)}"
                )
            seen_members.add(key)
            annotation = annotation_by_key.get(key)
            if annotation is None:
                raise FinalizeBundleError(
                    "Refinement references unknown review annotation: " f"{_format_key(key)}"
                )
            if annotation.decision != member.decision:
                raise FinalizeBundleError(
                    "Refinement member decision does not match review annotation: "
                    f"{_format_key(key)}"
                )
            if annotation.evidence_role != member.evidence_role:
                raise FinalizeBundleError(
                    "Refinement member role does not match review annotation: "
                    f"{_format_key(key)}"
                )
        if any(_is_ship_decision(annotation_by_key[key].decision) for key in member_keys):
            representative = annotation_by_key[representative_key]
            if not _is_ship_decision(representative.decision):
                raise FinalizeBundleError(
                    "Refinement cluster has ship-eligible member but non-shipping "
                    f"representative: {cluster.cluster_id}"
                )
            for key in member_keys:
                replacements[key] = representative_key
    return replacements


def _final_passage_uses(
    draft_candidates: dict[_CandidateKey, _DraftCandidate],
    replacements: dict[_CandidateKey, _CandidateKey],
) -> list[_FinalPassageUse]:
    uses: dict[tuple[str, str, str], _FinalPassageUse] = {}
    for key in sorted(draft_candidates):
        candidate = draft_candidates[key]
        annotation = candidate.annotation
        if not _is_ship_decision(annotation.decision):
            continue
        if annotation.evidence_role == "insufficient":
            raise FinalizeBundleError(
                "Cannot ship review annotation with evidence_role='insufficient': "
                f"{_format_key(key)}"
            )
        final_key = replacements.get(key, key)
        final_candidate = draft_candidates.get(final_key)
        if final_candidate is None:
            raise FinalizeBundleError(
                "Refinement representative is missing from draft candidates: "
                f"{_format_key(final_key)}"
            )
        use_key = (annotation.claim_id, final_key[1], final_key[2])
        uses[use_key] = _FinalPassageUse(
            claim_id=annotation.claim_id,
            annotation=final_candidate.annotation,
            draft_candidate=final_candidate,
        )
    return [uses[key] for key in sorted(uses)]


def _uses_by_claim(final_uses: list[_FinalPassageUse]) -> dict[str, list[_FinalPassageUse]]:
    by_claim: dict[str, list[_FinalPassageUse]] = {}
    for use in final_uses:
        by_claim.setdefault(use.claim_id, []).append(use)
    for claim_id, uses in by_claim.items():
        by_claim[claim_id] = sorted(
            uses,
            key=lambda use: (
                0 if _routes_to_evidence(use.annotation) else 1,
                use.draft_candidate.passage.source_id,
                use.draft_candidate.passage.passage_id,
            ),
        )
    return by_claim


def _cited_by_passage(final_uses: list[_FinalPassageUse]) -> dict[tuple[str, str], set[str]]:
    cited: dict[tuple[str, str], set[str]] = {}
    for use in final_uses:
        passage = use.draft_candidate.passage
        cited.setdefault((passage.source_id, passage.passage_id), set()).add(use.claim_id)
    return cited


def _load_passage_records(bundle_dir: Path) -> dict[tuple[str, str], PassageRecord]:
    records: dict[tuple[str, str], PassageRecord] = {}
    for passage_path in sorted((bundle_dir / "evidence").glob("*/passages/*.yaml")):
        record = load_model_yaml(PassageRecord, passage_path)
        records[(record.source_id, record.passage_id)] = record
    return records


def _load_source_profiles(bundle_dir: Path) -> dict[str, SourceProfile]:
    profiles: dict[str, SourceProfile] = {}
    for profile_path in sorted((bundle_dir / "evidence").glob("*/source_profile.yaml")):
        profile = load_model_yaml(SourceProfile, profile_path)
        profiles[profile.source_id] = profile
    return profiles


def _final_passage_records(
    *,
    passage_records: dict[tuple[str, str], PassageRecord],
    cited_by_passage: dict[tuple[str, str], set[str]],
    final_bundle_id: str,
    generated_at_utc: str,
) -> dict[tuple[str, str], PassageRecord]:
    final_records: dict[tuple[str, str], PassageRecord] = {}
    for key in sorted(cited_by_passage):
        record = passage_records.get(key)
        if record is None:
            raise FinalizeBundleError(f"Draft passage record missing: {_format_passage_key(key)}")
        final_records[key] = record.model_copy(
            update={
                "bundle_id": final_bundle_id,
                "cited_by_claims": sorted(cited_by_passage[key]),
                "provenance": record.provenance.model_copy(
                    update={"bundle_created_at_utc": generated_at_utc}
                ),
            }
        )
    return final_records


def _write_claims(
    *,
    output_dir: Path,
    claims: dict[str, ClaimAuditUnit],
    uses_by_claim: dict[str, list[_FinalPassageUse]],
    final_bundle_id: str,
) -> None:
    for claim_id, claim in sorted(claims.items()):
        evidence_passages: list[ClaimEvidencePassage] = []
        counterevidence_passages: list[ClaimEvidencePassage] = []
        for use in uses_by_claim.get(claim_id, []):
            passage = use.draft_candidate.passage
            if _routes_to_evidence(use.annotation):
                evidence_passages.append(passage)
            else:
                counterevidence_passages.append(passage)
        updated = claim.model_copy(
            update={
                "bundle_id": final_bundle_id,
                "evidence_passages": evidence_passages,
                "counterevidence_passages": counterevidence_passages,
            }
        )
        write_model_yaml(updated, output_dir / "claims" / f"{claim_id}.yaml")


def _write_source_profiles(
    output_dir: Path,
    source_profiles: dict[str, SourceProfile],
    passage_records: dict[tuple[str, str], PassageRecord],
) -> None:
    for source_id in sorted({source_id for source_id, _passage_id in passage_records}):
        profile = source_profiles.get(source_id)
        if profile is None:
            raise FinalizeBundleError(f"Draft source profile missing: {source_id}")
        write_model_yaml(profile, output_dir / "evidence" / source_id / "source_profile.yaml")


def _write_passage_records(
    output_dir: Path,
    passage_records: dict[tuple[str, str], PassageRecord],
) -> None:
    for (source_id, passage_id), record in sorted(passage_records.items()):
        write_model_yaml(
            record,
            output_dir / "evidence" / source_id / "passages" / f"{passage_id}.yaml",
        )


def _copy_audit_config(draft_bundle_dir: Path, output_dir: Path) -> None:
    audit_config = load_model_yaml(AuditConfig, draft_bundle_dir / "audit_config.yaml")
    write_model_yaml(audit_config, output_dir / "audit_config.yaml")


def _copy_validation_set_ref(draft_bundle_dir: Path, output_dir: Path) -> None:
    validation_ref = load_model_yaml(
        ValidationSetRef,
        draft_bundle_dir / "validation_set_ref.yaml",
    )
    write_model_yaml(validation_ref, output_dir / "validation_set_ref.yaml")


def _final_manifest(
    *,
    draft_manifest: BundleManifest,
    final_bundle_id: str,
    generated_at_utc: str,
    total_evidence_passages: int,
    every_claim_has_at_least_one_passage: bool,
    reviewer_sign_off_required: bool,
) -> BundleManifest:
    return draft_manifest.model_copy(
        update={
            "bundle_id": final_bundle_id,
            "generated_at_utc": generated_at_utc,
            "evidence_builder": EvidenceBuilderInfo(
                version=__version__,
                config_hash=draft_manifest.evidence_builder.config_hash,
                operator=draft_manifest.evidence_builder.operator,
                build_timestamp_utc=generated_at_utc,
            ),
            "bundle": draft_manifest.bundle.model_copy(
                update={
                    "total_evidence_passages": total_evidence_passages,
                    "bundle_hash": PENDING_HASH,
                }
            ),
            "transformations": [
                *draft_manifest.transformations,
                TransformationRecord(
                    type="review_finalize",
                    description=(
                        "Applied review annotations and excerpt refinement to produce a "
                        "reviewed C-B bundle. Finalization hashes are recorded in the "
                        "separate finalize provenance sidecar."
                    ),
                    claims_affected=[],
                ),
            ],
            "quality_gates": draft_manifest.quality_gates.model_copy(
                update={
                    "every_claim_has_at_least_one_passage": (
                        every_claim_has_at_least_one_passage
                    ),
                    "every_passage_links_to_source_profile": True,
                    "source_hashes_verified": True,
                    "bundle_integrity_verified": True,
                }
            ),
            "reviewer_sign_off": ReviewerSignOff(required=reviewer_sign_off_required),
        }
    )


def _routes_to_evidence(annotation: ReviewAnnotation) -> bool:
    if annotation.evidence_role == "supporting":
        return True
    if annotation.evidence_role in {"contradicting", "conditional"}:
        return False
    raise FinalizeBundleError(
        "Cannot route review annotation with evidence_role="
        f"{annotation.evidence_role!r}: {_format_key(_annotation_key(annotation))}"
    )


def _is_ship_decision(decision: ReviewDecision) -> bool:
    return decision in {"accepted", "needs-review"}


def _annotation_key(annotation: ReviewAnnotation) -> _CandidateKey:
    return (annotation.claim_id, annotation.source_id, annotation.passage_id)


def _member_key(member: ExcerptRefinementMember) -> _CandidateKey:
    return (member.claim_id, member.source_id, member.passage_id)


def _format_key(key: _CandidateKey) -> str:
    return f"{key[0]}/{key[1]}/{key[2]}"


def _format_passage_key(key: tuple[str, str]) -> str:
    return f"{key[0]}/{key[1]}"


def _assert_output_ready(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FinalizeBundleError(f"Output directory is not empty: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)


def _assert_output_outside_draft(draft_bundle_dir: Path, output_dir: Path) -> None:
    draft_root = draft_bundle_dir.resolve()
    target = output_dir.resolve()
    if target == draft_root or target.is_relative_to(draft_root):
        raise FinalizeBundleError(
            "Final bundle output must be written outside the sealed draft bundle."
        )


def _assert_provenance_ready(provenance_path: Path) -> None:
    if provenance_path.exists():
        raise FinalizeBundleError(f"Finalize provenance file already exists: {provenance_path}")
    provenance_path.parent.mkdir(parents=True, exist_ok=True)


def _assert_sidecar_outside_bundle(
    bundle_dir: Path,
    sidecar_path: Path,
    artifact_label: str,
) -> None:
    bundle_root = bundle_dir.resolve()
    target = sidecar_path.resolve()
    if target == bundle_root or target.is_relative_to(bundle_root):
        raise FinalizeBundleError(f"{artifact_label} must be written outside the sealed bundle.")


def _default_provenance_path(output_dir: Path) -> Path:
    return output_dir.with_name(f"{output_dir.name}_finalize_provenance.yaml")


def _write_contract_version(output_dir: Path) -> None:
    (output_dir / "CONTRACT_VERSION").write_text(f"{CONTRACT_VERSION}\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
