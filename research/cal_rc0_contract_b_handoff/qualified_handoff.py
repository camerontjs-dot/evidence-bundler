from __future__ import annotations

from pathlib import Path
from typing import Any

from evidence_bundler.contracts import factual_context as factual_context_module
from evidence_bundler.contracts.hashing import (
    compute_bundle_tree_hash,
    hash_audit_config_file,
    write_sha256sums,
)
from evidence_bundler.contracts.writer import validate_bundle_tree
from evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml
from evidence_bundler.models.ca import SourceBibliographic
from evidence_bundler.models.cb import (
    AuditConfig,
    AuditConfigChange,
    AuditRulePolicies,
    AuditScoringConfig,
    BundleManifest,
    ClaimAuditUnit,
    PassageRecord,
    SourceProfile,
    TransformationRecord,
    ValidationSetRef,
)
from evidence_bundler.models.common import PENDING_HASH

from .build_handoff import build_all_contract_b as _build_all_contract_b

CARRIER_SCHEMA = "research-contract-b-1.2-compatibility-carrier-v1"


def dedupe_source_contexts(extension: Any) -> Any:
    """Normalize repeated source-context references without changing evidence identity."""
    seen: set[str] = set()
    sources = []
    for source in extension.sources:
        if source.source_id in seen:
            continue
        seen.add(source.source_id)
        sources.append(source)
    return extension.model_copy(update={"sources": sources})


def validate_compatibility_carrier(carrier: dict[str, Any]) -> None:
    """Fail closed unless the separate legacy-B compatibility authority is explicit."""
    expected_top = {
        "schema",
        "scope",
        "authority",
        "legacy_claim_fields",
        "source_profile",
        "passage_record",
        "manifest",
        "audit_config",
    }
    if set(carrier) != expected_top:
        raise ValueError("Contract B compatibility carrier top-level shape mismatch")
    if carrier["schema"] != CARRIER_SCHEMA:
        raise ValueError("Contract B compatibility carrier schema mismatch")
    if carrier["scope"] != "qualification_only":
        raise ValueError("Contract B compatibility carrier is not qualification-only")

    authority = carrier["authority"]
    expected_authority = {
        "actual_upstream_contract": "contract-a-v2.0.0",
        "contract_b_core_compatibility_only": True,
        "supplies_contract_a_authority": False,
        "supplies_cal_semantic_authority": False,
        "semantic_use_authorized": False,
    }
    if authority != expected_authority:
        raise ValueError("Contract B compatibility carrier authority boundary mismatch")

    claim_fields = carrier["legacy_claim_fields"]
    if set(claim_fields) != {
        "claim_type",
        "workflow_condition",
        "scaffold_support_status",
        "scaffold_claim_strength",
        "scaffold_extraction_fidelity",
        "scaffold_counterevidence_found",
        "scaffold_downgraded",
    }:
        raise ValueError("legacy Contract B claim compatibility field set mismatch")

    source_profile = carrier["source_profile"]
    if set(source_profile) != {
        "source_type",
        "title_template",
        "authors",
        "publication_date",
        "url_template",
        "access_date_utc",
        "trust_level",
        "retrieval_query",
        "notes",
    }:
        raise ValueError("Contract B source-profile compatibility field set mismatch")

    passage_record = carrier["passage_record"]
    if set(passage_record) != {"section", "extraction_method"}:
        raise ValueError("Contract B passage compatibility field set mismatch")

    manifest = carrier["manifest"]
    if set(manifest) != {
        "generated_at_utc",
        "source_contract_version_compatibility_value",
        "source_corpus_hash_semantics",
        "operator",
        "validation_set_version",
    }:
        raise ValueError("Contract B manifest compatibility field set mismatch")
    if manifest["source_corpus_hash_semantics"] != (
        "canonical_contract_a2_sources_digest_compatibility_only"
    ):
        raise ValueError("unsupported compatibility source-corpus-hash semantics")

    audit = carrier["audit_config"]
    if set(audit) != {
        "config_id",
        "scoring",
        "rule_policies",
        "known_limitations",
        "change_log",
    }:
        raise ValueError("Contract B audit-config compatibility field set mismatch")


def _rewrite_claims(
    *, bundle_dir: Path, case: dict[str, Any], carrier: dict[str, Any]
) -> None:
    fields = carrier["legacy_claim_fields"]
    task_id = str(case["contract_a"]["work"]["work_id"])
    trust_level = carrier["source_profile"]["trust_level"]
    for path in sorted((bundle_dir / "claims").glob("*.yaml")):
        unit = load_model_yaml(ClaimAuditUnit, path)
        evidence = [
            row.model_copy(update={"source_trust_level": trust_level})
            for row in unit.evidence_passages
        ]
        counterevidence = [
            row.model_copy(update={"source_trust_level": trust_level})
            for row in unit.counterevidence_passages
        ]
        unit = unit.model_copy(
            update={
                "claim_type": fields["claim_type"],
                "workflow_condition": fields["workflow_condition"],
                "task_id": task_id,
                "scaffold_support_status": fields["scaffold_support_status"],
                "scaffold_claim_strength": fields["scaffold_claim_strength"],
                "scaffold_extraction_fidelity": fields["scaffold_extraction_fidelity"],
                "scaffold_counterevidence_found": fields[
                    "scaffold_counterevidence_found"
                ],
                "scaffold_downgraded": fields["scaffold_downgraded"],
                "evidence_passages": evidence,
                "counterevidence_passages": counterevidence,
            }
        )
        write_model_yaml(unit, path)


def _rewrite_sources_and_passages(
    *, bundle_dir: Path, case: dict[str, Any], carrier: dict[str, Any]
) -> None:
    source_cfg = carrier["source_profile"]
    passage_cfg = carrier["passage_record"]
    contract_a = case["contract_a"]
    source_by_id = {str(row["source_id"]): row for row in contract_a["sources"]}

    evidence_root = bundle_dir / "evidence"
    for source_dir in sorted(path for path in evidence_root.iterdir() if path.is_dir()):
        profile_path = source_dir / "source_profile.yaml"
        profile = load_model_yaml(SourceProfile, profile_path)
        source = source_by_id.get(profile.source_id)
        if source is None:
            raise ValueError(f"Contract B source not present in Contract A 2.0: {profile.source_id}")

        source_url = str(source_cfg["url_template"]).format(source_id=profile.source_id)
        bibliographic = SourceBibliographic(
            source_type=source_cfg["source_type"],
            title=str(source_cfg["title_template"]).format(source_id=profile.source_id),
            authors=list(source_cfg["authors"]),
            publication_date=source_cfg["publication_date"],
            pmid=None,
            doi=None,
            url=source_url,
            access_date_utc=source_cfg["access_date_utc"],
        )
        profile = profile.model_copy(
            update={
                "bibliographic": bibliographic,
                "trust_level": source_cfg["trust_level"],
                "content_hash": source["content_sha256"],
                "retrieval_query": source_cfg["retrieval_query"],
                "notes": source_cfg["notes"],
            }
        )
        write_model_yaml(profile, profile_path)

        for passage_path in sorted((source_dir / "passages").glob("*.yaml")):
            passage = load_model_yaml(PassageRecord, passage_path)
            source_text = str(source["content"])
            occurrence_count = source_text.count(passage.passage_text)
            if occurrence_count != 1:
                raise ValueError(
                    f"passage text must have one exact Contract A source occurrence: "
                    f"{passage.passage_id} observed={occurrence_count}"
                )
            char_start = source_text.index(passage.passage_text)
            char_end = char_start + len(passage.passage_text)
            provenance = passage.provenance.model_copy(
                update={
                    "source_url": source_url,
                    "source_access_date_utc": source_cfg["access_date_utc"],
                    "source_content_hash": source["content_sha256"],
                    "scaffold_run_id": contract_a["handoff_id"],
                    "bundle_created_at_utc": carrier["manifest"]["generated_at_utc"],
                }
            )
            passage = passage.model_copy(
                update={
                    "section": passage_cfg["section"],
                    "char_start": char_start,
                    "char_end": char_end,
                    "extraction_method": passage_cfg["extraction_method"],
                    "provenance": provenance,
                }
            )
            write_model_yaml(passage, passage_path)


def _rewrite_audit_config(*, bundle_dir: Path, carrier: dict[str, Any]) -> AuditConfig:
    cfg = carrier["audit_config"]
    audit = AuditConfig(
        config_id=cfg["config_id"],
        config_hash=PENDING_HASH,
        schema_version="1.2.0",
        frozen_at_utc=carrier["manifest"]["generated_at_utc"],
        scoring=AuditScoringConfig(**cfg["scoring"]),
        rule_policies=AuditRulePolicies(**cfg["rule_policies"]),
        known_limitations=list(cfg["known_limitations"]),
        change_log=[AuditConfigChange(**row) for row in cfg["change_log"]],
    )
    path = bundle_dir / "audit_config.yaml"
    write_model_yaml(audit, path)
    audit = audit.model_copy(update={"config_hash": hash_audit_config_file(path)})
    write_model_yaml(audit, path)
    return audit


def _rewrite_validation_ref(
    *, bundle_dir: Path, carrier: dict[str, Any]
) -> ValidationSetRef:
    path = bundle_dir / "validation_set_ref.yaml"
    ref = load_model_yaml(ValidationSetRef, path)
    ref = ref.model_copy(
        update={
            "validation_set_version": carrier["manifest"]["validation_set_version"],
            "frozen_at_utc": carrier["manifest"]["generated_at_utc"],
            "description": "Research EB RC0 handoff qualification cohort pointer.",
            "notes": (
                "Evaluator gold is separate. Legacy Contract B compatibility state is supplied "
                "by a qualification-only carrier and is not Contract A 2.0 authority."
            ),
        }
    )
    write_model_yaml(ref, path)
    return ref


def _reseal_manifest(
    *,
    bundle_dir: Path,
    case: dict[str, Any],
    carrier: dict[str, Any],
    audit: AuditConfig,
    validation_ref: ValidationSetRef,
) -> BundleManifest:
    path = bundle_dir / "bundle_manifest.yaml"
    manifest = load_model_yaml(BundleManifest, path)
    compatibility_note = TransformationRecord(
        type="contract_b_legacy_compatibility_carrier",
        description=(
            "Qualification-only legacy Contract B core metadata supplied by a separate explicit "
            "compatibility carrier. Contract A 2.0 remains the actual upstream proposition/source "
            "authority; the carrier supplies no CAL semantic authority."
        ),
        claims_affected=[row.claim_id for row in [
            load_model_yaml(ClaimAuditUnit, claim_path)
            for claim_path in sorted((bundle_dir / "claims").glob("*.yaml"))
        ]],
    )
    evidence_builder = manifest.evidence_builder.model_copy(
        update={
            "operator": carrier["manifest"]["operator"],
            "build_timestamp_utc": carrier["manifest"]["generated_at_utc"],
        }
    )
    manifest = manifest.model_copy(
        update={
            "generated_at_utc": carrier["manifest"]["generated_at_utc"],
            "source_run_id": case["contract_a"]["handoff_id"],
            "source_contract_version": carrier["manifest"][
                "source_contract_version_compatibility_value"
            ],
            "evidence_builder": evidence_builder,
            "bundle": manifest.bundle.model_copy(update={"bundle_hash": PENDING_HASH}),
            "transformations": list(manifest.transformations) + [compatibility_note],
            "audit_config_version": audit.config_id,
            "audit_config_hash": audit.config_hash,
            "validation_set_version": validation_ref.validation_set_version,
            "validation_set_hash": validation_ref.validation_set_hash,
        }
    )
    write_model_yaml(manifest, path)
    manifest = manifest.model_copy(
        update={
            "bundle": manifest.bundle.model_copy(
                update={"bundle_hash": compute_bundle_tree_hash(bundle_dir)}
            )
        }
    )
    write_model_yaml(manifest, path)
    write_sha256sums(bundle_dir)
    return manifest


def apply_compatibility_carrier(
    *, bundle_dir: Path, case: dict[str, Any], carrier: dict[str, Any]
) -> BundleManifest:
    """Rewrite legacy B-only fields from the explicit carrier and reseal the bundle."""
    validate_compatibility_carrier(carrier)
    _rewrite_claims(bundle_dir=bundle_dir, case=case, carrier=carrier)
    _rewrite_sources_and_passages(bundle_dir=bundle_dir, case=case, carrier=carrier)
    audit = _rewrite_audit_config(bundle_dir=bundle_dir, carrier=carrier)
    validation_ref = _rewrite_validation_ref(bundle_dir=bundle_dir, carrier=carrier)
    manifest = _reseal_manifest(
        bundle_dir=bundle_dir,
        case=case,
        carrier=carrier,
        audit=audit,
        validation_ref=validation_ref,
    )
    errors = validate_bundle_tree(bundle_dir)
    if errors:
        raise ValueError("; ".join(errors))
    return manifest


def build_all_contract_b_qualified(
    *,
    cohort: dict[str, Any],
    receipt: dict[str, Any],
    profile: dict[str, Any],
    compatibility_carrier: dict[str, Any],
    out_dir: Path,
) -> list[dict[str, Any]]:
    """Build qualification B bundles only behind an explicit legacy compatibility carrier.

    Retrieval, retention, admission, and Contract A identity remain frozen upstream of this
    adapter. The carrier exists because Contract B 1.2 still requires legacy C-A fields that
    Contract A 2.0 deliberately does not carry. Missing or malformed carrier state fails closed.
    """
    validate_compatibility_carrier(compatibility_carrier)
    original_attach = factual_context_module.attach_factual_context

    def normalized_attach(bundle_dir: Path, extension: Any) -> Path:
        return original_attach(bundle_dir, dedupe_source_contexts(extension))

    factual_context_module.attach_factual_context = normalized_attach
    try:
        results = _build_all_contract_b(
            cohort=cohort,
            receipt=receipt,
            profile=profile,
            out_dir=out_dir,
        )
    finally:
        factual_context_module.attach_factual_context = original_attach

    case_by_id = {str(row["case_id"]): row for row in cohort["cases"]}
    refreshed: list[dict[str, Any]] = []
    for result in results:
        row = dict(result)
        case_id = str(row["case_id"])
        bundle_dir = out_dir / "contract_b" / case_id
        manifest = apply_compatibility_carrier(
            bundle_dir=bundle_dir,
            case=case_by_id[case_id],
            carrier=compatibility_carrier,
        )
        row["bundle_hash"] = manifest.bundle.bundle_hash
        row["compatibility_carrier_schema"] = compatibility_carrier["schema"]
        row["actual_upstream_contract"] = compatibility_carrier["authority"][
            "actual_upstream_contract"
        ]
        row["legacy_contract_b_core_compatibility"] = "EXPLICIT_SEPARATE_CARRIER"
        refreshed.append(row)
    return refreshed


__all__ = [
    "CARRIER_SCHEMA",
    "apply_compatibility_carrier",
    "build_all_contract_b_qualified",
    "dedupe_source_contexts",
    "validate_compatibility_carrier",
]
