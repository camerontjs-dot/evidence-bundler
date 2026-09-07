from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

PROFILE_SCHEMA = "research-eb-profile-rc0-v1"
COHORT_SCHEMA = "research-eb-rc0-cohort-v1"
ADMISSION_SCHEMA = "research-eb-rc0-admission-v1"
RECEIPT_SCHEMA = "research-eb-rc0-runtime-receipt-v1"
CONTRACT_A_SCHEMA = "contract-a-wire-candidate-rc2"
CONTRACT_B_VERSION = "1.2.0"
DECLARED_CHILD_LANE = "declared_child"
DIAGNOSTIC_ROOT_LANE = "diagnostic_root_rescue"
TOKEN_RE = re.compile(r"\w+")


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def query_id(case_id: str, proposition_id: str, lane: str, text: str) -> str:
    payload = f"{case_id}\0{proposition_id}\0{lane}\0{text}".encode("utf-8")
    return "query:" + hashlib.sha256(payload).hexdigest()[:24]


def validate_contract_a(value: dict[str, Any]) -> None:
    """Validate the Contract A 2.0.0 RC2 wire invariants used by this research build."""
    expected_top = {
        "schema",
        "handoff_id",
        "producer",
        "work",
        "root_proposition",
        "decomposition",
        "sources",
        "handoff_sha256",
    }
    if set(value) != expected_top:
        raise ValueError("Contract A top-level keys do not match the released RC2 wire")
    if value["schema"] != CONTRACT_A_SCHEMA:
        raise ValueError("Contract A schema token mismatch")

    root = value["root_proposition"]
    if set(root) != {"proposition_id", "text", "text_sha256"}:
        raise ValueError("root proposition shape mismatch")
    if root["text_sha256"] != hash_text(root["text"]):
        raise ValueError("root proposition hash mismatch")

    decomposition = value["decomposition"]
    if decomposition.get("state") != "declared":
        raise ValueError("RC0 qualification requires an authoritative declared decomposition")
    if set(decomposition) != {"state", "decomposition_id", "operator", "children"}:
        raise ValueError("declared decomposition shape mismatch")
    if decomposition["operator"] != "all_of":
        raise ValueError("RC0 qualification requires all_of decomposition")
    children = decomposition["children"]
    if len(children) < 2:
        raise ValueError("declared all_of requires at least two children")
    ids: list[str] = []
    texts: list[str] = []
    sequences: list[int] = []
    for index, child in enumerate(children, start=1):
        if set(child) != {"proposition_id", "text", "text_sha256", "sequence"}:
            raise ValueError("child proposition shape mismatch")
        if child["text_sha256"] != hash_text(child["text"]):
            raise ValueError(f"child proposition hash mismatch: {child['proposition_id']}")
        if child["sequence"] != index:
            raise ValueError("child sequence must be contiguous and preserve source order")
        ids.append(child["proposition_id"])
        texts.append(child["text"])
        sequences.append(child["sequence"])
    if root["proposition_id"] in ids or len(ids) != len(set(ids)):
        raise ValueError("child proposition identity collision")
    if len(texts) != len(set(texts)) or len(sequences) != len(set(sequences)):
        raise ValueError("declared child text/sequence collision")

    source_ids: list[str] = []
    for source in value["sources"]:
        if set(source) != {"source_id", "media_type", "content", "content_sha256"}:
            raise ValueError("source shape mismatch")
        if source["media_type"] not in {
            "text/plain; charset=utf-8",
            "text/markdown; charset=utf-8",
        }:
            raise ValueError("source media type mismatch")
        if source["content_sha256"] != hash_text(source["content"]):
            raise ValueError(f"source content hash mismatch: {source['source_id']}")
        source_ids.append(source["source_id"])
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source_id")

    payload = dict(value)
    supplied = payload.pop("handoff_sha256")
    expected = "sha256:" + hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    if supplied != expected:
        raise ValueError("Contract A whole-object handoff hash mismatch")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def bm25_scores(query: str, passages: list[dict[str, Any]]) -> list[tuple[float, str]]:
    """Small pinned Okapi BM25 qualification retriever. No learned/rerank state."""
    documents = [tokenize(str(row["text"])) for row in passages]
    if not documents:
        return []
    document_count = len(documents)
    average_length = sum(len(row) for row in documents) / document_count
    document_frequency: Counter[str] = Counter()
    for document in documents:
        document_frequency.update(set(document))

    query_terms = tokenize(query)
    k1 = 1.5
    b = 0.75
    scores: list[tuple[float, str]] = []
    for document, passage in zip(documents, passages, strict=True):
        term_frequency = Counter(document)
        document_length = len(document)
        score = 0.0
        for term in query_terms:
            frequency = term_frequency.get(term, 0)
            if frequency == 0:
                continue
            df = document_frequency[term]
            idf = math.log(1.0 + (document_count - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (
                1.0 - b + b * document_length / average_length
            )
            score += idf * frequency * (k1 + 1.0) / denominator
        scores.append((score, str(passage["evidence_id"])))
    return sorted(scores, key=lambda row: (-row[0], row[1]))


def _decision_for(
    explicit: dict[str, Any], evidence_id: str
) -> tuple[str, str]:
    if evidence_id in explicit.get("accepted", []):
        return "accepted", "explicit_human_research_admission"
    if evidence_id in explicit.get("rejected", []):
        return "rejected", "explicit_human_research_rejection"
    if evidence_id in explicit.get("needs-review", []):
        return "needs-review", "explicit_unresolved_review"
    return "needs-review", "not_explicitly_adjudicated"


def build_runtime_receipt(
    *,
    cohort: dict[str, Any],
    admission: dict[str, Any],
    profile: dict[str, Any],
    diagnostic_root_rescue: bool = False,
) -> dict[str, Any]:
    if cohort.get("schema") != COHORT_SCHEMA:
        raise ValueError("cohort schema mismatch")
    if admission.get("schema") != ADMISSION_SCHEMA:
        raise ValueError("admission schema mismatch")
    if profile.get("schema") != PROFILE_SCHEMA:
        raise ValueError("profile schema mismatch")

    candidate_depth = int(profile["retrieval"]["per_query_candidate_depth"])
    retained_k = int(profile["retrieval"]["retained_k"])
    if candidate_depth < retained_k:
        raise ValueError("candidate depth must be >= retained K")

    case_receipts: list[dict[str, Any]] = []
    for case in cohort["cases"]:
        case_id = str(case["case_id"])
        contract_a = case["contract_a"]
        validate_contract_a(contract_a)
        passages = case["passages"]
        passage_by_id = {str(row["evidence_id"]): row for row in passages}
        if len(passage_by_id) != len(passages):
            raise ValueError(f"duplicate physical evidence ID in {case_id}")

        expected_source_ids = {row["source_id"] for row in passages}
        declared_source_ids = {row["source_id"] for row in contract_a["sources"]}
        if not expected_source_ids.issubset(declared_source_ids):
            raise ValueError(f"passage source outside Contract A source declaration: {case_id}")

        query_specs: list[dict[str, Any]] = []
        for child in contract_a["decomposition"]["children"]:
            query_specs.append(
                {
                    "proposition_id": child["proposition_id"],
                    "proposition_role": "declared_child",
                    "sequence": child["sequence"],
                    "lane": DECLARED_CHILD_LANE,
                    "text": child["text"],
                }
            )
        if diagnostic_root_rescue:
            query_specs.append(
                {
                    "proposition_id": contract_a["root_proposition"]["proposition_id"],
                    "proposition_role": "root",
                    "sequence": None,
                    "lane": DIAGNOSTIC_ROOT_LANE,
                    "text": contract_a["root_proposition"]["text"],
                }
            )

        candidate_rows: list[dict[str, Any]] = []
        retained_rows: list[dict[str, Any]] = []
        admission_rows: list[dict[str, Any]] = []
        review_case = admission["cases"].get(case_id, {})

        for spec in query_specs:
            qid = query_id(case_id, spec["proposition_id"], spec["lane"], spec["text"])
            ranked = bm25_scores(spec["text"], passages)
            positive = [row for row in ranked if row[0] > 0.0][:candidate_depth]
            for rank, (score, evidence_id) in enumerate(positive, start=1):
                passage = passage_by_id[evidence_id]
                candidate = {
                    "query_id": qid,
                    "root_proposition_id": contract_a["root_proposition"]["proposition_id"],
                    "proposition_id": spec["proposition_id"],
                    "proposition_role": spec["proposition_role"],
                    "retrieval_lane": spec["lane"],
                    "evidence_id": evidence_id,
                    "source_id": passage["source_id"],
                    "rank": rank,
                    "score": round(score, 12),
                    "score_kind": "research_okapi_bm25_v1",
                }
                candidate_rows.append(candidate)
                if rank <= retained_k:
                    retained = dict(candidate)
                    retained["retained"] = True
                    retained_rows.append(retained)

                    explicit = review_case.get(spec["proposition_id"], {})
                    decision, basis = _decision_for(explicit, evidence_id)
                    admission_rows.append(
                        {
                            "query_id": qid,
                            "proposition_id": spec["proposition_id"],
                            "retrieval_lane": spec["lane"],
                            "evidence_id": evidence_id,
                            "decision": decision,
                            "admission_basis": basis,
                            "reviewer_id": admission["reviewer"]["id"],
                            "reviewer_type": admission["reviewer"]["type"],
                        }
                    )

        case_receipts.append(
            {
                "case_id": case_id,
                "contract_a_handoff_id": contract_a["handoff_id"],
                "contract_a_handoff_sha256": contract_a["handoff_sha256"],
                "root_proposition": contract_a["root_proposition"],
                "declared_children": contract_a["decomposition"]["children"],
                "candidate_pool": candidate_rows,
                "retained": retained_rows,
                "admission": admission_rows,
                "flattened_parent_child": False,
                "diagnostic_root_rescue_enabled": diagnostic_root_rescue,
            }
        )

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "profile_id": profile["profile_id"],
        "profile_sha256": "sha256:" + sha256_bytes(canonical_bytes(profile)),
        "cohort_sha256": "sha256:" + sha256_bytes(canonical_bytes(cohort)),
        "admission_fixture_sha256": "sha256:" + sha256_bytes(canonical_bytes(admission)),
        "diagnostic_root_rescue_enabled": diagnostic_root_rescue,
        "cases": case_receipts,
    }
    return receipt


def _write_contract_b_bundle(
    *,
    case: dict[str, Any],
    case_receipt: dict[str, Any],
    profile: dict[str, Any],
    bundle_dir: Path,
) -> dict[str, Any]:
    """Construct and validate a sealed Contract B 1.2 bundle without running CAL."""
    from evidence_bundler import __version__
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
        hash_text as eb_hash_text,
        write_sha256sums,
    )
    from evidence_bundler.contracts.writer import validate_bundle_tree
    from evidence_bundler.contracts.yaml_io import write_model_yaml
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

    if bundle_dir.exists() and any(bundle_dir.iterdir()):
        raise ValueError(f"non-empty Contract B output: {bundle_dir}")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    generated_at = "2026-09-06T00:00:00Z"
    case_id = str(case["case_id"])
    contract_a = case["contract_a"]
    bundle_id = str(uuid5(NAMESPACE_URL, f"research-eb-rc0:{profile['profile_id']}:{case_id}"))
    passage_by_id = {row["evidence_id"]: row for row in case["passages"]}

    retained_by_claim: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_receipt["retained"]:
        retained_by_claim[row["proposition_id"]].append(row)

    retained_ids = sorted({row["evidence_id"] for row in case_receipt["retained"]})
    (bundle_dir / "CONTRACT_VERSION").write_text(CONTRACT_B_VERSION + "\n", encoding="utf-8")

    audit_config = AuditConfig(
        config_id="research-cal-rc0-contract-b-compat",
        config_hash=PENDING_HASH,
        schema_version=CONTRACT_B_VERSION,
        frozen_at_utc=generated_at,
        scoring=AuditScoringConfig(
            support_threshold_sourced=0.80,
            support_threshold_partial=0.55,
            counterevidence_weight=0.30,
        ),
        rule_policies=AuditRulePolicies(
            require_passage_level_match=True,
            flag_unsupported_threshold=0.40,
            false_caution_detection=True,
            false_caution_threshold=0.85,
            overstated_detection=True,
            needs_source_detection=True,
        ),
        known_limitations=[
            "Required Contract B 1.2 audit-config compatibility surface only; this RC0 track does not run CAL.",
            "No audit verdict, semantic relation, support, refutation, warrant, or proposition truth is assigned here.",
        ],
        change_log=[
            AuditConfigChange(
                version="research-rc0",
                date="2026-09-06",
                changes="No Contract B schema change; research-only handoff uses the released 1.2 surface.",
                rationale="Provide a valid sealed B 1.2 bundle for the parallel CAL RC0 consumer.",
            )
        ],
    )
    audit_path = bundle_dir / "audit_config.yaml"
    write_model_yaml(audit_config, audit_path)
    audit_config = audit_config.model_copy(
        update={"config_hash": hash_audit_config_file(audit_path)}
    )
    write_model_yaml(audit_config, audit_path)

    validation_ref = ValidationSetRef(
        schema_version=CONTRACT_B_VERSION,
        validation_set_version="research-cal-rc0-handoff-qualification-v1",
        validation_set_hash="sha256:" + sha256_bytes(canonical_bytes(case["passages"])),
        frozen_at_utc=generated_at,
        description="Research EB RC0 handoff qualification cohort pointer.",
        notes="Evaluator gold is separate and is not consumed by the EB runtime.",
    )
    write_model_yaml(validation_ref, bundle_dir / "validation_set_ref.yaml")

    claim_rows = [contract_a["root_proposition"]] + [
        {
            "proposition_id": child["proposition_id"],
            "text": child["text"],
            "text_sha256": child["text_sha256"],
        }
        for child in contract_a["decomposition"]["children"]
    ]
    for claim in claim_rows:
        evidence_passages: list[ClaimEvidencePassage] = []
        for retained in retained_by_claim.get(claim["proposition_id"], []):
            passage = passage_by_id[retained["evidence_id"]]
            text = passage["text"]
            evidence_passages.append(
                ClaimEvidencePassage(
                    passage_id=passage["evidence_id"],
                    source_id=passage["source_id"],
                    passage_text=text,
                    section="RC0 qualification fixture",
                    char_start=0,
                    char_end=len(text),
                    source_trust_level="primary",
                    passage_hash=eb_hash_text(text),
                )
            )
        unit = ClaimAuditUnit(
            claim_id=claim["proposition_id"],
            bundle_id=bundle_id,
            schema_version=CONTRACT_B_VERSION,
            claim_text=claim["text"],
            claim_type="extracted_claim",
            workflow_condition="full_scaffold",
            task_id=f"research-cal-rc0:{case_id}",
            scaffold_support_status="uncertain",
            scaffold_claim_strength=0.0,
            scaffold_extraction_fidelity=1.0,
            scaffold_counterevidence_found=False,
            scaffold_downgraded=False,
            evidence_passages=evidence_passages,
            counterevidence_passages=[],
            audit=AuditFields(),
        )
        write_model_yaml(unit, bundle_dir / "claims" / f"{claim['proposition_id']}.yaml")

    for evidence_id in retained_ids:
        passage = passage_by_id[evidence_id]
        source_id = passage["source_id"]
        text = passage["text"]
        cited_by = sorted(
            {
                row["proposition_id"]
                for row in case_receipt["retained"]
                if row["evidence_id"] == evidence_id
            }
        )
        source_profile = SourceProfile(
            source_id=source_id,
            schema_version=CONTRACT_B_VERSION,
            bibliographic=SourceBibliographic(
                source_type="regulatory_guidance",
                title=f"RC0 qualification source {source_id}",
                authors=["Research EB Profile RC0 fixture"],
                publication_date="2026-09-06",
                pmid=None,
                doi=None,
                url=f"https://example.test/{source_id}",
                access_date_utc=generated_at,
            ),
            trust_level="primary",
            content_hash=eb_hash_text(text),
            retrieved_for=cited_by,
            retrieval_query="See Contract B factual-context nomination history.",
            retrieval_rank=min(
                row["rank"]
                for row in case_receipt["retained"]
                if row["evidence_id"] == evidence_id
            ),
            notes="Research-only qualification source; proposition/lane retrieval history is in the factual-context extension.",
        )
        write_model_yaml(
            source_profile,
            bundle_dir / "evidence" / source_id / "source_profile.yaml",
        )
        record = PassageRecord(
            passage_id=evidence_id,
            source_id=source_id,
            bundle_id=bundle_id,
            schema_version=CONTRACT_B_VERSION,
            passage_text=text,
            section="RC0 qualification fixture",
            paragraph_index=0,
            char_start=0,
            char_end=len(text),
            passage_hash=eb_hash_text(text),
            cited_by_claims=cited_by,
            extraction_method="scaffold_cited",
            provenance=PassageProvenance(
                source_url=f"https://example.test/{source_id}",
                source_access_date_utc=generated_at,
                source_content_hash=eb_hash_text(text),
                scaffold_run_id=contract_a["handoff_id"],
                evidence_builder_version=__version__,
                bundle_created_at_utc=generated_at,
            ),
        )
        write_model_yaml(
            record,
            bundle_dir / "evidence" / source_id / "passages" / f"{evidence_id}.yaml",
        )

    manifest = BundleManifest(
        bundle_id=bundle_id,
        schema_version=CONTRACT_B_VERSION,
        generated_at_utc=generated_at,
        source_run_id=contract_a["handoff_id"],
        source_contract_version=CONTRACT_B_VERSION,
        source_corpus_hash="sha256:" + sha256_bytes(canonical_bytes(contract_a["sources"])),
        evidence_builder=EvidenceBuilderInfo(
            version=__version__,
            config_hash="sha256:" + sha256_bytes(canonical_bytes(profile["retrieval"])),
            operator="research-eb-profile-rc0",
            build_timestamp_utc=generated_at,
        ),
        bundle=BundleStats(
            total_claims_in_source=len(claim_rows),
            claims_included=len(claim_rows),
            claims_excluded=0,
            exclusion_rationale="none",
            total_evidence_passages=len(retained_ids),
            bundle_hash=PENDING_HASH,
        ),
        transformations=[
            TransformationRecord(
                type="research_rc0_declared_child_retrieval",
                description=(
                    "Research-only per-declared-child retrieval and explicit review-state handoff; "
                    "no semantic support/refutation assessment."
                ),
                claims_affected=[row["proposition_id"] for row in claim_rows],
            )
        ],
        quality_gates=QualityGates(
            every_claim_has_at_least_one_passage=all(
                bool(retained_by_claim.get(row["proposition_id"])) for row in claim_rows
            ),
            every_passage_links_to_source_profile=True,
            source_hashes_verified=True,
            bundle_integrity_verified=True,
        ),
        audit_config_version="research-cal-rc0-contract-b-compat",
        audit_config_hash=audit_config.config_hash,
        validation_set_version=validation_ref.validation_set_version,
        validation_set_hash=validation_ref.validation_set_hash,
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

    review_by_key = {
        (row["proposition_id"], row["evidence_id"]): row
        for row in case_receipt["admission"]
    }
    history: list[HistoryLink] = []
    for retained in case_receipt["retained"]:
        review = review_by_key[(retained["proposition_id"], retained["evidence_id"])]
        history.append(
            HistoryLink(
                link_id=(
                    f"{case_id}:{retained['proposition_id']}:{retained['retrieval_lane']}:"
                    f"{retained['evidence_id']}"
                ),
                claim_id=retained["proposition_id"],
                passage_id=retained["evidence_id"],
                nomination={
                    "method": "research_okapi_bm25_v1",
                    "query_id": retained["query_id"],
                    "proposition_id": retained["proposition_id"],
                    "retrieval_lane": retained["retrieval_lane"],
                    "rank": retained["rank"],
                    "score": retained["score"],
                    "retained": True,
                },
                review={
                    "decision": review["decision"],
                    "reviewer_id": review["reviewer_id"],
                    "reviewer_type": review["reviewer_type"],
                    "basis": review["admission_basis"],
                },
            )
        )

    all_claim_ids = [row["proposition_id"] for row in claim_rows]
    counts: dict[str, list[int]] = {claim_id: [0, 0, 0] for claim_id in all_claim_ids}
    for link in history:
        counts[link.claim_id][0] += 1
        if link.review["decision"] != "needs-review":
            counts[link.claim_id][1] += 1
        if link.review["decision"] == "accepted":
            counts[link.claim_id][2] += 1

    extension = ContractBFactualContext(
        history_complete=True,
        claims=[
            ClaimContext(
                claim_id=contract_a["root_proposition"]["proposition_id"],
                origin=ExplicitValue(
                    state="known",
                    value={
                        "contract_a_handoff_id": contract_a["handoff_id"],
                        "role": "root",
                    },
                ),
                atomicity=ExplicitValue(state="unknown", value=None),
            )
        ]
        + [
            ClaimContext(
                claim_id=child["proposition_id"],
                origin=ExplicitValue(
                    state="known",
                    value={
                        "contract_a_handoff_id": contract_a["handoff_id"],
                        "role": "declared_child",
                        "parent_claim_id": contract_a["root_proposition"]["proposition_id"],
                        "decomposition_id": contract_a["decomposition"]["decomposition_id"],
                        "sequence": child["sequence"],
                    },
                ),
                atomicity=ExplicitValue(state="unknown", value=None),
            )
            for child in contract_a["decomposition"]["children"]
        ],
        sources=[
            SourceContext(source_id=passage_by_id[evidence_id]["source_id"])
            for evidence_id in retained_ids
        ],
        passages=[
            PassageContext(
                passage_id=evidence_id,
                anchors=[
                    Anchor(type="physical_evidence_id", value=evidence_id),
                    Anchor(type="source_id", value=passage_by_id[evidence_id]["source_id"]),
                ],
            )
            for evidence_id in retained_ids
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
        aperture=[
            ApertureObservation(
                claim_id=child["proposition_id"],
                search_scope={
                    "retrieval_lane": DECLARED_CHILD_LANE,
                    "candidate_depth": profile["retrieval"]["per_query_candidate_depth"],
                    "retained_k": profile["retrieval"]["retained_k"],
                    "root_union": False,
                },
                outcome=ExplicitValue(
                    state="known",
                    value={
                        "candidate_count": sum(
                            row["proposition_id"] == child["proposition_id"]
                            for row in case_receipt["candidate_pool"]
                        ),
                        "retained_count": sum(
                            row["proposition_id"] == child["proposition_id"]
                            for row in case_receipt["retained"]
                        ),
                    },
                ),
                limitations=[
                    "Retrieval nomination is not evidence admission.",
                    "No CAL semantic engine is invoked in this track.",
                ],
            )
            for child in contract_a["decomposition"]["children"]
        ],
    )
    attach_factual_context(bundle_dir, extension)
    errors = validate_bundle_tree(bundle_dir)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "case_id": case_id,
        "bundle_id": bundle_id,
        "contract_b_version": CONTRACT_B_VERSION,
        "bundle_hash": manifest.bundle.bundle_hash,
        "tree_validation": "PASS",
        "extension_path": "extensions/contract-b-factual-context-v1.json",
    }


def build_all_contract_b(
    *,
    cohort: dict[str, Any],
    receipt: dict[str, Any],
    profile: dict[str, Any],
    out_dir: Path,
) -> list[dict[str, Any]]:
    case_by_id = {row["case_id"]: row for row in cohort["cases"]}
    results: list[dict[str, Any]] = []
    for case_receipt in receipt["cases"]:
        case_id = case_receipt["case_id"]
        results.append(
            _write_contract_b_bundle(
                case=case_by_id[case_id],
                case_receipt=case_receipt,
                profile=profile,
                bundle_dir=out_dir / "contract_b" / case_id,
            )
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--diagnostic-root-rescue", action="store_true")
    parser.add_argument("--receipt-only", action="store_true")
    args = parser.parse_args()

    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    admission = json.loads(args.admission.read_text(encoding="utf-8"))
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    receipt = build_runtime_receipt(
        cohort=cohort,
        admission=admission,
        profile=profile,
        diagnostic_root_rescue=args.diagnostic_root_rescue,
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = args.out_dir / "runtime_receipt.json"
    receipt_path.write_bytes(canonical_bytes(receipt))

    contract_b_results: list[dict[str, Any]] = []
    if not args.receipt_only:
        contract_b_results = build_all_contract_b(
            cohort=cohort,
            receipt=receipt,
            profile=profile,
            out_dir=args.out_dir,
        )
    summary = {
        "receipt_sha256": sha256_bytes(receipt_path.read_bytes()),
        "case_count": len(receipt["cases"]),
        "contract_b_results": contract_b_results,
    }
    (args.out_dir / "build_summary.json").write_bytes(canonical_bytes(summary))
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
