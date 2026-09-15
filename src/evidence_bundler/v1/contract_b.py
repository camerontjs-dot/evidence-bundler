"""Non-semantic Evidence Bundler V1 -> released Contract B 1.2 projection."""

from __future__ import annotations

import json
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Final, Literal
from uuid import NAMESPACE_URL, uuid5

from evidence_bundler.contracts.factual_context import (
    Anchor,
    ApertureObservation,
    ClaimContext,
    ContractBFactualContext,
    ExplicitValue,
    HistoryCountCheck,
    HistoryLink,
    PassageContext,
    SourceContext,
    attach_factual_context,
)
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
    AuditFields,
    AuditRulePolicies,
    AuditScoringConfig,
    BundleManifest,
    BundleStats,
    ClaimAuditUnit,
    ClaimEvidencePassage,
    EvidenceBuilderInfo,
    PassageProvenance,
    PassageRecord,
    QualityGates,
    ReviewerSignOff,
    SourceProfile,
    TransformationRecord,
    ValidationSetRef,
)
from evidence_bundler.models.common import PENDING_HASH
from evidence_bundler.v1.package import V1Config, canonical_json_bytes, hash_json, validate_package

CONTRACT_B_VERSION: Final[Literal["1.2.0"]] = "1.2.0"
CONTRACT_B_PRODUCTION_LOCK = "c314e53bd91c0736aa4370a364673b069aceb43e"
FROZEN_V1_IMPLEMENTATION_COMMIT = "c4e3f97ec8f0bd36180954c3aa382418925bf947"
FROZEN_V1_IMPLEMENTATION_TREE = "1d254e38cb0e174635efc7687c2b0ab091aa52b3"
INTEGRATION_PROFILE_ID = "eb-v1-integration-10x3-rc0"
INTEGRATION_CONFIG_SHA256 = (
    "sha256:5b10d0c29794e80d6876a99e26bcf6ec6a27a4c5165aee78054a6bc32759f4bc"
)
CARRIER_SCHEMA = "eb-v1-contract-b-1.2-compatibility-carrier-v1"
PROJECTION_RECEIPT_SCHEMA = "eb-v1-contract-b-projection-receipt-v1"
INTEGRATION_CONFIG = V1Config(candidate_depth=10, retained_k=3)

if INTEGRATION_CONFIG.identity != INTEGRATION_CONFIG_SHA256:  # pragma: no cover
    raise RuntimeError("frozen V1 integration config identity drift")


class ContractBProjectionError(ValueError):
    """Raised when the V1 -> B1.2 boundary cannot proceed safely."""


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise ContractBProjectionError(f"{label} shape mismatch: {actual}")
    return value


def _nonblank(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractBProjectionError(f"{label} must be nonblank")
    return value


def load_compatibility_carrier(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractBProjectionError(f"invalid compatibility carrier: {exc}") from exc
    return validate_compatibility_carrier(value)


def validate_integration_package(value: dict[str, Any]) -> dict[str, Any]:
    package = validate_package(value)
    if package["config"] != INTEGRATION_CONFIG.as_payload():
        raise ContractBProjectionError(
            "native package config is not the frozen eb-v1-integration-10x3-rc0 profile"
        )
    if package["config_sha256"] != INTEGRATION_CONFIG_SHA256:
        raise ContractBProjectionError("native package config identity mismatch")
    if package["diagnostics"]["root_retrieval"] is not None:
        raise ContractBProjectionError("integration candidate forbids root diagnostic retrieval")
    return package


def validate_compatibility_carrier(value: Any) -> dict[str, Any]:
    carrier = _exact(
        value,
        {
            "schema",
            "scope",
            "authority",
            "legacy_claim_fields",
            "source_profile",
            "passage_record",
            "manifest",
            "audit_config",
        },
        "carrier",
    )
    if carrier["schema"] != CARRIER_SCHEMA or carrier["scope"] != "integration_candidate_only":
        raise ContractBProjectionError("compatibility carrier identity/scope mismatch")
    authority = _exact(
        carrier["authority"],
        {
            "actual_upstream_contract",
            "contract_b_core_compatibility_only",
            "supplies_contract_a_authority",
            "supplies_cal_semantic_authority",
            "semantic_use_authorized",
        },
        "carrier.authority",
    )
    if authority != {
        "actual_upstream_contract": "contract-a-v2.0.0",
        "contract_b_core_compatibility_only": True,
        "supplies_contract_a_authority": False,
        "supplies_cal_semantic_authority": False,
        "semantic_use_authorized": False,
    }:
        raise ContractBProjectionError("compatibility carrier authority boundary mismatch")

    legacy = _exact(
        carrier["legacy_claim_fields"],
        {
            "claim_type",
            "workflow_condition",
            "scaffold_support_status",
            "scaffold_claim_strength",
            "scaffold_extraction_fidelity",
            "scaffold_counterevidence_found",
            "scaffold_downgraded",
        },
        "carrier.legacy_claim_fields",
    )
    if legacy != {
        "claim_type": "retrieval_seed",
        "workflow_condition": "baseline",
        "scaffold_support_status": "uncertain",
        "scaffold_claim_strength": 0.0,
        "scaffold_extraction_fidelity": 0.0,
        "scaffold_counterevidence_found": False,
        "scaffold_downgraded": False,
    }:
        raise ContractBProjectionError("legacy claim compatibility payload weakened/drifted")

    source = _exact(
        carrier["source_profile"],
        {
            "source_type",
            "title_template",
            "authors",
            "publication_date",
            "url_template",
            "access_date_utc",
            "trust_level",
            "retrieval_query",
            "notes",
        },
        "carrier.source_profile",
    )
    if source["source_type"] != "other" or source["trust_level"] != "background":
        raise ContractBProjectionError("source compatibility payload must remain non-authoritative")
    for key in ("title_template", "url_template", "access_date_utc", "retrieval_query", "notes"):
        _nonblank(source[key], f"carrier.source_profile.{key}")
    if not isinstance(source["authors"], list):
        raise ContractBProjectionError("carrier.source_profile.authors must be an array")

    passage = _exact(
        carrier["passage_record"],
        {"section", "paragraph_index", "extraction_method"},
        "carrier.passage_record",
    )
    if passage["extraction_method"] != "auto_retrieved":
        raise ContractBProjectionError("passage compatibility extraction_method drift")
    if isinstance(passage["paragraph_index"], bool) or not isinstance(
        passage["paragraph_index"], int
    ):
        raise ContractBProjectionError("passage compatibility paragraph_index must be integer")

    manifest = _exact(
        carrier["manifest"],
        {
            "generated_at_utc",
            "source_contract_version_compatibility_value",
            "source_corpus_hash_semantics",
            "operator",
            "validation_set_version",
            "validation_set_hash",
            "validation_set_description",
            "validation_set_notes",
            "reviewer_sign_off_required",
        },
        "carrier.manifest",
    )
    if manifest["source_contract_version_compatibility_value"] != CONTRACT_B_VERSION:
        raise ContractBProjectionError("carrier Contract B version mismatch")
    if manifest["source_corpus_hash_semantics"] != "canonical_contract_a2_sources_digest":
        raise ContractBProjectionError("carrier source-corpus hash semantics mismatch")
    if manifest["reviewer_sign_off_required"] is not False:
        raise ContractBProjectionError("carrier cannot invent reviewer sign-off")

    audit = _exact(
        carrier["audit_config"],
        {"config_id", "scoring", "rule_policies", "known_limitations", "change_log"},
        "carrier.audit_config",
    )
    if audit["config_id"] != "cal-rules-v1.2.0":
        raise ContractBProjectionError("carrier audit policy must equal cal-rules-v1.2.0")
    try:
        AuditScoringConfig(**audit["scoring"])
        AuditRulePolicies(**audit["rule_policies"])
        [AuditConfigChange(**row) for row in audit["change_log"]]
    except Exception as exc:  # noqa: BLE001
        raise ContractBProjectionError(f"invalid compatibility audit config: {exc}") from exc
    return carrier


def _claims(package: dict[str, Any]) -> list[dict[str, Any]]:
    root = package["contract_a"]["root_proposition"]
    rows = [
        {
            "proposition_id": root["proposition_id"],
            "text": root["text"],
            "text_sha256": root["text_sha256"],
            "role": "root",
            "sequence": None,
        }
    ]
    seen = {root["proposition_id"]}
    for target in package["primary_targets"]:
        if target["proposition_id"] not in seen:
            rows.append(dict(target))
            seen.add(target["proposition_id"])
    return rows


def _passages(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in package["candidates"]:
        passage = {
            "passage_id": row["passage_id"],
            "source_id": row["source_id"],
            "source_content_sha256": row["source_content_sha256"],
            "char_start": row["char_start"],
            "char_end": row["char_end"],
            "passage_sha256": row["passage_sha256"],
            "text": row["text"],
        }
        prior = result.get(str(row["passage_id"]))
        if prior is not None and prior != passage:
            raise ContractBProjectionError("native passage identity collision")
        result[str(row["passage_id"])] = passage
    return result


def _review_decision(candidate: dict[str, Any]) -> str:
    if candidate["selection_state"] == "retained":
        decision = str(candidate["admission_state"])
        if decision not in {"accepted", "rejected", "needs-review"}:
            raise ContractBProjectionError("retained candidate admission state invalid")
        return decision
    if candidate["selection_state"] == "not_retained":
        if candidate["admission_state"] != "not_applicable":
            raise ContractBProjectionError("non-retained candidate admission state drift")
        return "needs-review"
    raise ContractBProjectionError("unknown selection state")


def _write_base_bundle(
    package: dict[str, Any], carrier: dict[str, Any], bundle_dir: Path, bundle_id: str
) -> None:
    if bundle_dir.exists() and any(bundle_dir.iterdir()):
        raise ContractBProjectionError(f"non-empty Contract B output: {bundle_dir}")
    (bundle_dir / "claims").mkdir(parents=True, exist_ok=True)
    (bundle_dir / "evidence").mkdir(parents=True, exist_ok=True)

    contract_a = package["contract_a"]
    source_by_id = {str(row["source_id"]): row for row in contract_a["sources"]}
    claim_rows = _claims(package)
    claim_ids = [str(row["proposition_id"]) for row in claim_rows]
    passage_by_id = _passages(package)
    legacy = carrier["legacy_claim_fields"]
    source_cfg = carrier["source_profile"]
    passage_cfg = carrier["passage_record"]
    manifest_cfg = carrier["manifest"]
    audit_cfg = carrier["audit_config"]

    by_claim: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    accepted_by_passage: dict[str, set[str]] = defaultdict(set)
    for candidate in package["candidates"]:
        claim_id = str(candidate["proposition_id"])
        source_id = str(candidate["source_id"])
        by_claim[claim_id].append(candidate)
        by_source[source_id].append(candidate)
        if (
            candidate["selection_state"] == "retained"
            and candidate["admission_state"] == "accepted"
        ):
            accepted_by_passage[str(candidate["passage_id"])].add(claim_id)

    (bundle_dir / "CONTRACT_VERSION").write_text(CONTRACT_B_VERSION + "\n", encoding="utf-8")
    validation = ValidationSetRef(
        schema_version=CONTRACT_B_VERSION,
        validation_set_version=manifest_cfg["validation_set_version"],
        validation_set_hash=manifest_cfg["validation_set_hash"],
        frozen_at_utc=manifest_cfg["generated_at_utc"],
        description=manifest_cfg["validation_set_description"],
        notes=manifest_cfg["validation_set_notes"],
    )
    write_model_yaml(validation, bundle_dir / "validation_set_ref.yaml")

    audit = AuditConfig(
        config_id=audit_cfg["config_id"],
        config_hash=PENDING_HASH,
        schema_version=CONTRACT_B_VERSION,
        frozen_at_utc=manifest_cfg["generated_at_utc"],
        scoring=AuditScoringConfig(**audit_cfg["scoring"]),
        rule_policies=AuditRulePolicies(**audit_cfg["rule_policies"]),
        known_limitations=list(audit_cfg["known_limitations"]),
        change_log=[AuditConfigChange(**row) for row in audit_cfg["change_log"]],
    )
    audit_path = bundle_dir / "audit_config.yaml"
    write_model_yaml(audit, audit_path)
    audit = audit.model_copy(update={"config_hash": hash_audit_config_file(audit_path)})
    write_model_yaml(audit, audit_path)

    for claim in claim_rows:
        claim_id = str(claim["proposition_id"])
        accepted = sorted(
            (
                row
                for row in by_claim.get(claim_id, [])
                if row["selection_state"] == "retained" and row["admission_state"] == "accepted"
            ),
            key=lambda row: (row["nomination_rank"], row["passage_id"]),
        )
        evidence = [
            ClaimEvidencePassage(
                passage_id=row["passage_id"],
                source_id=row["source_id"],
                passage_text=row["text"],
                section=passage_cfg["section"],
                char_start=row["char_start"],
                char_end=row["char_end"],
                source_trust_level=source_cfg["trust_level"],
                passage_hash=row["passage_sha256"],
            )
            for row in accepted
        ]
        unit = ClaimAuditUnit(
            claim_id=claim_id,
            bundle_id=bundle_id,
            schema_version=CONTRACT_B_VERSION,
            claim_text=claim["text"],
            claim_type=legacy["claim_type"],
            workflow_condition=legacy["workflow_condition"],
            task_id=contract_a["work"]["work_id"],
            scaffold_support_status=legacy["scaffold_support_status"],
            scaffold_claim_strength=legacy["scaffold_claim_strength"],
            scaffold_extraction_fidelity=legacy["scaffold_extraction_fidelity"],
            scaffold_counterevidence_found=legacy["scaffold_counterevidence_found"],
            scaffold_downgraded=legacy["scaffold_downgraded"],
            evidence_passages=evidence,
            counterevidence_passages=[],
            audit=AuditFields(),
        )
        write_model_yaml(unit, bundle_dir / "claims" / f"{claim_id}.yaml")

    for source_id, candidates in sorted(by_source.items()):
        source = source_by_id[source_id]
        source_url = str(source_cfg["url_template"]).format(source_id=source_id)
        profile = SourceProfile(
            source_id=source_id,
            schema_version=CONTRACT_B_VERSION,
            bibliographic=SourceBibliographic(
                source_type=source_cfg["source_type"],
                title=str(source_cfg["title_template"]).format(source_id=source_id),
                authors=list(source_cfg["authors"]),
                publication_date=source_cfg["publication_date"],
                pmid=None,
                doi=None,
                url=source_url,
                access_date_utc=source_cfg["access_date_utc"],
            ),
            trust_level=source_cfg["trust_level"],
            content_hash=source["content_sha256"],
            retrieved_for=sorted({str(row["proposition_id"]) for row in candidates}),
            retrieval_query=source_cfg["retrieval_query"],
            retrieval_rank=min(int(row["nomination_rank"]) for row in candidates),
            notes=source_cfg["notes"],
        )
        write_model_yaml(profile, bundle_dir / "evidence" / source_id / "source_profile.yaml")

    for passage_id, passage in sorted(passage_by_id.items()):
        source_id = str(passage["source_id"])
        source_url = str(source_cfg["url_template"]).format(source_id=source_id)
        record = PassageRecord(
            passage_id=passage_id,
            source_id=source_id,
            bundle_id=bundle_id,
            schema_version=CONTRACT_B_VERSION,
            passage_text=passage["text"],
            section=passage_cfg["section"],
            paragraph_index=passage_cfg["paragraph_index"],
            char_start=passage["char_start"],
            char_end=passage["char_end"],
            passage_hash=passage["passage_sha256"],
            cited_by_claims=sorted(accepted_by_passage.get(passage_id, set())),
            extraction_method=passage_cfg["extraction_method"],
            provenance=PassageProvenance(
                source_url=source_url,
                source_access_date_utc=source_cfg["access_date_utc"],
                source_content_hash=passage["source_content_sha256"],
                scaffold_run_id=contract_a["handoff_id"],
                evidence_builder_version=package["producer"]["producer_version"],
                bundle_created_at_utc=manifest_cfg["generated_at_utc"],
            ),
        )
        write_model_yaml(
            record,
            bundle_dir / "evidence" / source_id / "passages" / f"{passage_id}.yaml",
        )

    manifest = BundleManifest(
        bundle_id=bundle_id,
        schema_version=CONTRACT_B_VERSION,
        generated_at_utc=manifest_cfg["generated_at_utc"],
        source_run_id=contract_a["handoff_id"],
        source_contract_version=manifest_cfg["source_contract_version_compatibility_value"],
        source_corpus_hash=hash_json(contract_a["sources"]),
        evidence_builder=EvidenceBuilderInfo(
            version=package["producer"]["producer_version"],
            config_hash=package["config_sha256"],
            operator=manifest_cfg["operator"],
            build_timestamp_utc=manifest_cfg["generated_at_utc"],
        ),
        bundle=BundleStats(
            total_claims_in_source=len(claim_rows),
            claims_included=len(claim_rows),
            claims_excluded=0,
            exclusion_rationale="none",
            total_evidence_passages=len(passage_by_id),
            bundle_hash=PENDING_HASH,
        ),
        transformations=[
            TransformationRecord(
                type="evidence_bundler_v1_native_package_projection",
                description=(
                    f"Non-semantic projection from native package {package['package_sha256']} "
                    f"under config {package['config_sha256']}; retrieval, retention and admission "
                    "are not recomputed."
                ),
                claims_affected=claim_ids,
            ),
            TransformationRecord(
                type="contract_b_legacy_compatibility_carrier",
                description=(
                    f"Legacy B-only payload from carrier {hash_json(carrier)}; carrier supplies "
                    "neither Contract A nor CAL semantic authority."
                ),
                claims_affected=claim_ids,
            ),
        ],
        quality_gates=QualityGates(
            every_claim_has_at_least_one_passage=all(
                any(
                    row["selection_state"] == "retained" and row["admission_state"] == "accepted"
                    for row in by_claim.get(claim_id, [])
                )
                for claim_id in claim_ids
            ),
            every_passage_links_to_source_profile=True,
            source_hashes_verified=True,
            bundle_integrity_verified=True,
        ),
        audit_config_version=audit.config_id,
        audit_config_hash=audit.config_hash,
        validation_set_version=validation.validation_set_version,
        validation_set_hash=validation.validation_set_hash,
        reviewer_sign_off=ReviewerSignOff(required=False),
    )
    manifest_path = bundle_dir / "bundle_manifest.yaml"
    write_model_yaml(manifest, manifest_path)
    manifest = manifest.model_copy(
        update={
            "bundle": manifest.bundle.model_copy(
                update={"bundle_hash": compute_bundle_tree_hash(bundle_dir)}
            )
        }
    )
    write_model_yaml(manifest, manifest_path)
    write_sha256sums(bundle_dir)


def _attach_extension(package: dict[str, Any], bundle_dir: Path) -> None:
    contract_a = package["contract_a"]
    claim_rows = _claims(package)
    root_id = str(contract_a["root_proposition"]["proposition_id"])
    children = {
        str(row["proposition_id"]): row for row in contract_a["decomposition"].get("children", [])
    }
    plans = {str(row["retrieval_id"]): row for row in package["retrieval_plans"]}
    executions = {str(row["retrieval_id"]): row for row in package["retrieval_executions"]}
    passage_by_id = _passages(package)

    counts: dict[str, list[int]] = {str(row["proposition_id"]): [0, 0, 0] for row in claim_rows}
    history: list[HistoryLink] = []
    for candidate in package["candidates"]:
        claim_id = str(candidate["proposition_id"])
        decision = _review_decision(candidate)
        counts[claim_id][0] += 1
        if decision != "needs-review":
            counts[claim_id][1] += 1
        if decision == "accepted":
            counts[claim_id][2] += 1
        history.append(
            HistoryLink(
                link_id=f"{candidate['query_id']}:{candidate['passage_id']}",
                claim_id=claim_id,
                passage_id=candidate["passage_id"],
                nomination={
                    "method": package["config"]["retrieval_engine"],
                    "query_id": candidate["query_id"],
                    "retrieval_id": candidate["retrieval_id"],
                    "proposition_id": claim_id,
                    "retrieval_lane": candidate["retrieval_lane"],
                    "rank": candidate["nomination_rank"],
                    "selection_state": candidate["selection_state"],
                    "candidate_depth": package["config"]["candidate_depth"],
                    "retained_k": package["config"]["retained_k"],
                    "config_sha256": package["config_sha256"],
                    "native_package_sha256": package["package_sha256"],
                },
                review={
                    "decision": decision,
                    "native_admission_state": candidate["admission_state"],
                    "encoding": (
                        "native"
                        if candidate["selection_state"] == "retained"
                        else "contract_b_needs_review_for_native_not_applicable"
                    ),
                },
            )
        )

    claim_contexts: list[ClaimContext] = []
    for claim in claim_rows:
        claim_id = str(claim["proposition_id"])
        origin: dict[str, Any] = {
            "contract_a_handoff_id": contract_a["handoff_id"],
            "role": "root" if claim_id == root_id else "declared_child",
            "text_sha256": claim["text_sha256"],
        }
        if claim_id != root_id:
            origin.update(
                {
                    "parent_claim_id": root_id,
                    "decomposition_id": contract_a["decomposition"]["decomposition_id"],
                    "sequence": children[claim_id]["sequence"],
                }
            )
        claim_contexts.append(
            ClaimContext(
                claim_id=claim_id,
                origin=ExplicitValue(state="known", value=origin),
                atomicity=ExplicitValue(state="unknown", value=None),
            )
        )

    aperture: list[ApertureObservation] = []
    for retrieval_id, execution in sorted(executions.items()):
        plan = plans[retrieval_id]
        candidates = [row for row in package["candidates"] if row["retrieval_id"] == retrieval_id]
        retained = [row for row in candidates if row["selection_state"] == "retained"]
        aperture.append(
            ApertureObservation(
                claim_id=plan["proposition_id"],
                search_scope={
                    "query_id": plan["query_id"],
                    "retrieval_id": retrieval_id,
                    "retrieval_lane": plan["retrieval_lane"],
                    "requested_source_ids": plan["requested_source_ids"],
                    "searched_source_ids": execution["searched_source_ids"],
                    "candidate_depth_limit": execution["candidate_depth_limit"],
                    "retained_k": package["config"]["retained_k"],
                    "config_sha256": package["config_sha256"],
                },
                outcome=ExplicitValue(
                    state="known",
                    value={
                        "status": execution["status"],
                        "returned_count": execution["returned_count"],
                        "candidate_depth_hit": execution["candidate_depth_hit"],
                        "aperture_state": execution["aperture_state"],
                        "retained_count": len(retained),
                        "accepted_count": sum(
                            row["admission_state"] == "accepted" for row in retained
                        ),
                        "rejected_count": sum(
                            row["admission_state"] == "rejected" for row in retained
                        ),
                        "needs_review_count": sum(
                            row["admission_state"] == "needs-review" for row in retained
                        ),
                        "not_retained_count": sum(
                            row["selection_state"] == "not_retained" for row in candidates
                        ),
                    },
                ),
                limitations=[
                    "Candidate depth is bounded and does not establish corpus completeness.",
                    "Nomination, retention and admission are distinct non-semantic stages.",
                    (
                        "B1.2 lacks native admission_state=not_applicable; non-retained candidates "
                        "use review.decision=needs-review only as compatibility encoding while "
                        "preserving native_admission_state=not_applicable."
                    ),
                    "No support, refutation, applicability, completeness or verdict is emitted.",
                ],
            )
        )

    extension = ContractBFactualContext(
        history_complete=True,
        claims=claim_contexts,
        sources=[
            SourceContext(source_id=source_id)
            for source_id in sorted({str(row["source_id"]) for row in package["candidates"]})
        ],
        passages=[
            PassageContext(
                passage_id=passage_id,
                anchors=[
                    Anchor(type="source_id", value=row["source_id"]),
                    Anchor(type="source_content_sha256", value=row["source_content_sha256"]),
                    Anchor(type="char_start", value=row["char_start"]),
                    Anchor(type="char_end", value=row["char_end"]),
                    Anchor(type="passage_sha256", value=row["passage_sha256"]),
                ],
            )
            for passage_id, row in sorted(passage_by_id.items())
        ],
        history=history,
        history_count_checks=[
            HistoryCountCheck(
                claim_id=claim_id,
                candidate=values[0],
                reviewed=values[1],
                admitted=values[2],
            )
            for claim_id, values in sorted(counts.items())
        ],
        aperture=aperture,
    )
    attach_factual_context(bundle_dir, extension)


def _receipt(
    package: dict[str, Any], carrier: dict[str, Any], bundle: BundleManifest
) -> dict[str, Any]:
    value = {
        "schema": PROJECTION_RECEIPT_SCHEMA,
        "profile_id": INTEGRATION_PROFILE_ID,
        "frozen_v1_implementation": {
            "commit": FROZEN_V1_IMPLEMENTATION_COMMIT,
            "tree": FROZEN_V1_IMPLEMENTATION_TREE,
        },
        "native_package_sha256": package["package_sha256"],
        "native_config_sha256": package["config_sha256"],
        "compatibility_carrier_sha256": hash_json(carrier),
        "contract_b_authority": {
            "version": CONTRACT_B_VERSION,
            "production_lock": CONTRACT_B_PRODUCTION_LOCK,
        },
        "bundle_id": bundle.bundle_id,
        "bundle_hash": bundle.bundle.bundle_hash,
        "counts": {
            "candidate_relationships": len(package["candidates"]),
            "retained_relationships": sum(
                row["selection_state"] == "retained" for row in package["candidates"]
            ),
            "accepted_relationships": sum(
                row["selection_state"] == "retained" and row["admission_state"] == "accepted"
                for row in package["candidates"]
            ),
            "unique_candidate_passages": len(_passages(package)),
        },
        "compatibility_encoding": {
            "native_not_retained_admission_state": "not_applicable",
            "contract_b_review_decision": "needs-review",
            "semantic_effect": "none; CAL admits only review.decision=accepted",
        },
        "mappings": [
            {
                "proposition_id": row["proposition_id"],
                "query_id": row["query_id"],
                "retrieval_id": row["retrieval_id"],
                "retrieval_lane": row["retrieval_lane"],
                "native_passage_id": row["passage_id"],
                "contract_b_passage_id": row["passage_id"],
                "source_id": row["source_id"],
                "source_content_sha256": row["source_content_sha256"],
                "char_start": row["char_start"],
                "char_end": row["char_end"],
                "passage_sha256": row["passage_sha256"],
                "nomination_rank": row["nomination_rank"],
                "selection_state": row["selection_state"],
                "native_admission_state": row["admission_state"],
                "contract_b_review_decision": _review_decision(row),
            }
            for row in package["candidates"]
        ],
        "receipt_sha256": "sha256:" + "0" * 64,
    }
    value["receipt_sha256"] = _receipt_hash(value)
    return value


def _receipt_hash(value: dict[str, Any]) -> str:
    payload = deepcopy(value)
    payload.pop("receipt_sha256", None)
    return hash_json(payload)


def validate_projection_receipt(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema") != PROJECTION_RECEIPT_SCHEMA:
        raise ContractBProjectionError("projection receipt schema mismatch")
    if value.get("receipt_sha256") != _receipt_hash(value):
        raise ContractBProjectionError("projection receipt hash mismatch")
    if value.get("profile_id") != INTEGRATION_PROFILE_ID:
        raise ContractBProjectionError("projection receipt profile mismatch")
    if value.get("contract_b_authority") != {
        "version": CONTRACT_B_VERSION,
        "production_lock": CONTRACT_B_PRODUCTION_LOCK,
    }:
        raise ContractBProjectionError("projection receipt Contract B authority mismatch")
    return value


def project_contract_b(
    *, package: dict[str, Any], compatibility_carrier: dict[str, Any], out_dir: Path
) -> dict[str, Any]:
    """Project one exact V1 10/3 native package into released Contract B 1.2."""
    package = validate_integration_package(package)
    carrier = validate_compatibility_carrier(compatibility_carrier)
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir = out_dir / "contract_b"
    receipt_path = out_dir / "projection_receipt.json"
    if receipt_path.exists() or (bundle_dir.exists() and any(bundle_dir.iterdir())):
        raise ContractBProjectionError("projection output already exists")

    carrier_sha = hash_json(carrier)
    bundle_id = str(
        uuid5(
            NAMESPACE_URL,
            f"eb-v1-contract-b:{INTEGRATION_PROFILE_ID}:{package['package_sha256']}:"
            f"{carrier_sha}:{CONTRACT_B_VERSION}",
        )
    )
    _write_base_bundle(package, carrier, bundle_dir, bundle_id)
    _attach_extension(package, bundle_dir)
    errors = validate_bundle_tree(bundle_dir)
    if errors:
        raise ContractBProjectionError("; ".join(errors))
    bundle = load_model_yaml(BundleManifest, bundle_dir / "bundle_manifest.yaml")
    receipt = _receipt(package, carrier, bundle)
    validate_projection_receipt(receipt)
    receipt_path.write_bytes(canonical_json_bytes(receipt))
    return receipt


__all__ = [
    "CARRIER_SCHEMA",
    "CONTRACT_B_PRODUCTION_LOCK",
    "CONTRACT_B_VERSION",
    "ContractBProjectionError",
    "FROZEN_V1_IMPLEMENTATION_COMMIT",
    "FROZEN_V1_IMPLEMENTATION_TREE",
    "INTEGRATION_CONFIG",
    "INTEGRATION_CONFIG_SHA256",
    "INTEGRATION_PROFILE_ID",
    "PROJECTION_RECEIPT_SCHEMA",
    "load_compatibility_carrier",
    "project_contract_b",
    "validate_compatibility_carrier",
    "validate_integration_package",
    "validate_projection_receipt",
]
