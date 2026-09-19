"""Evidence-world construction for the maintained V1 candidate."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Literal

from evidence_bundler import __version__
from evidence_bundler.ingest import chunk_source_documents
from evidence_bundler.models.document import ChunkSpec, DocumentChunk, SourceDocument
from evidence_bundler.v1.contract_a import (
    CONTRACT_A_RELEASE_COMMIT,
    CONTRACT_A_VALIDATOR_BLOB,
    CONTRACT_A_VERSION,
    PrimaryTarget,
    primary_targets,
    validate_contract_a,
)
from evidence_bundler.v1.package import (
    PACKAGE_CONTRACT_VERSION,
    PACKAGE_SCHEMA,
    EvidencePackageValidationError,
    V1Config,
    compute_package_sha256,
    hash_text,
    passage_identity,
    query_identity,
    retrieval_identity,
    validate_package,
)
from evidence_bundler.v1.retrieval import query_bm25

DECLARED_CHILD_LANE = "declared_child"
ROOT_LANE = "root"
DIAGNOSTIC_ROOT_LANE = "diagnostic_root_rescue"


def _source_documents(contract_a: dict[str, Any]) -> list[SourceDocument]:
    documents: list[SourceDocument] = []
    for source in contract_a["sources"]:
        media_type = str(source["media_type"])
        suffix = ".md" if media_type.startswith("text/markdown") else ".txt"
        content_type: Literal["markdown", "text"] = (
            "markdown" if suffix == ".md" else "text"
        )
        documents.append(
            SourceDocument(
                source_id=str(source["source_id"]),
                content_path=Path("contract-a") / f"{source['source_id']}{suffix}",
                content_type=content_type,
                raw_text=str(source["content"]),
                content_hash=str(source["content_sha256"]),
                metadata={},
                passages={},
            )
        )
    return documents


def _lane_for_target(target: PrimaryTarget) -> str:
    return DECLARED_CHILD_LANE if target["role"] == "declared_child" else ROOT_LANE


def _candidate_row(
    *,
    hit_chunk: DocumentChunk,
    rank: int,
    retrieval_id: str,
    query_id: str,
    proposition_id: str,
    lane: str,
    retained_k: int,
    admission: dict[tuple[str, str], str],
    source_hashes: dict[str, str],
) -> dict[str, Any]:
    selection_state = "retained" if rank <= retained_k else "not_retained"
    source_hash = source_hashes[hit_chunk.source_id]
    passage_sha = hash_text(hit_chunk.text)
    passage_id = passage_identity(
        source_id=hit_chunk.source_id,
        source_content_sha256=source_hash,
        char_start=hit_chunk.char_start,
        char_end=hit_chunk.char_end,
        passage_sha256=passage_sha,
    )
    admission_state = (
        admission.get((proposition_id, passage_id), "needs-review")
        if selection_state == "retained"
        else "not_applicable"
    )
    return {
        "retrieval_id": retrieval_id,
        "query_id": query_id,
        "proposition_id": proposition_id,
        "retrieval_lane": lane,
        "passage_id": passage_id,
        "source_id": hit_chunk.source_id,
        "source_content_sha256": source_hash,
        "char_start": hit_chunk.char_start,
        "char_end": hit_chunk.char_end,
        "passage_sha256": passage_sha,
        "text": hit_chunk.text,
        "nomination_rank": rank,
        "selection_state": selection_state,
        "admission_state": admission_state,
    }


def _diagnostic_candidate(
    *,
    hit_chunk: DocumentChunk,
    rank: int,
    source_hashes: dict[str, str],
) -> dict[str, Any]:
    source_hash = source_hashes[hit_chunk.source_id]
    passage_sha = hash_text(hit_chunk.text)
    return {
        "passage_id": passage_identity(
            source_id=hit_chunk.source_id,
            source_content_sha256=source_hash,
            char_start=hit_chunk.char_start,
            char_end=hit_chunk.char_end,
            passage_sha256=passage_sha,
        ),
        "source_id": hit_chunk.source_id,
        "source_content_sha256": source_hash,
        "char_start": hit_chunk.char_start,
        "char_end": hit_chunk.char_end,
        "passage_sha256": passage_sha,
        "text": hit_chunk.text,
        "nomination_rank": rank,
    }


def _assert_admission_bindings(
    admission: dict[tuple[str, str], str], candidates: list[dict[str, Any]]
) -> None:
    retained = {
        (str(row["proposition_id"]), str(row["passage_id"]))
        for row in candidates
        if row["selection_state"] == "retained"
    }
    unknown = sorted(set(admission) - retained)
    if unknown:
        rendered = ", ".join(
            f"{proposition_id}/{passage_id}" for proposition_id, passage_id in unknown
        )
        raise EvidencePackageValidationError(
            "admission decisions may bind only retained normative candidates; "
            f"unbound decisions: {rendered}"
        )


def build_package(
    *,
    contract_a: dict[str, Any],
    config: V1Config | None = None,
    admission: dict[tuple[str, str], str] | None = None,
    not_run_target_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Build one deterministic, self-contained V1 candidate evidence package.

    Retrieval failures are not converted into partial success.  The only
    supported partial-execution state is an explicit ``not_run`` declaration
    supplied before execution for one or more already-authoritative targets.
    """
    contract_a = validate_contract_a(contract_a)
    effective_config = config or V1Config()
    review = dict(admission or {})
    not_run = set(not_run_target_ids or set())
    targets = primary_targets(contract_a)
    target_ids = {target["proposition_id"] for target in targets}
    unknown_not_run = sorted(not_run - target_ids)
    if unknown_not_run:
        raise EvidencePackageValidationError(
            f"not_run target ids are not Contract A primary targets: {unknown_not_run}"
        )
    if effective_config.root_diagnostic and contract_a["decomposition"]["state"] != "declared":
        raise EvidencePackageValidationError(
            "root diagnostic is only meaningful for a declared decomposition"
        )

    documents = _source_documents(contract_a)
    source_hashes = {
        str(source["source_id"]): str(source["content_sha256"])
        for source in contract_a["sources"]
    }
    source_ids = sorted(source_hashes)
    chunks = chunk_source_documents(
        documents,
        ChunkSpec(
            max_chars=effective_config.chunk_max_chars,
            overlap_chars=effective_config.chunk_overlap_chars,
        ),
    )
    plans: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for target in targets:
        lane = _lane_for_target(target)
        query_id = query_identity(
            contract_a_sha256=str(contract_a["handoff_sha256"]),
            proposition_id=target["proposition_id"],
            text_sha256=target["text_sha256"],
            retrieval_lane=lane,
            config_sha256=effective_config.identity,
        )
        retrieval_id = retrieval_identity(query_id)
        plans.append(
            {
                "retrieval_id": retrieval_id,
                "query_id": query_id,
                "proposition_id": target["proposition_id"],
                "retrieval_lane": lane,
                "query_text_sha256": target["text_sha256"],
                "requested_source_ids": source_ids,
                "intended_retrieval_ids": [retrieval_id],
            }
        )

        if target["proposition_id"] in not_run:
            executions.append(
                {
                    "retrieval_id": retrieval_id,
                    "status": "not_run",
                    "searched_source_ids": [],
                    "returned_source_ids": [],
                    "returned_count": 0,
                    "candidate_depth_limit": effective_config.candidate_depth,
                    "candidate_depth_hit": False,
                    "aperture_state": "not_run",
                }
            )
            continue

        hits = query_bm25(target["text"], chunks, top_k=effective_config.candidate_depth)
        lane_candidates: list[dict[str, Any]] = []
        for rank, hit in enumerate(hits, start=1):
            row = _candidate_row(
                hit_chunk=hit.chunk,
                rank=rank,
                retrieval_id=retrieval_id,
                query_id=query_id,
                proposition_id=target["proposition_id"],
                lane=lane,
                retained_k=effective_config.retained_k,
                admission=review,
                source_hashes=source_hashes,
            )
            lane_candidates.append(row)
        candidates.extend(lane_candidates)
        returned_sources = sorted({str(row["source_id"]) for row in lane_candidates})
        depth_hit = len(lane_candidates) == effective_config.candidate_depth
        executions.append(
            {
                "retrieval_id": retrieval_id,
                "status": "completed",
                "searched_source_ids": source_ids,
                "returned_source_ids": returned_sources,
                "returned_count": len(lane_candidates),
                "candidate_depth_limit": effective_config.candidate_depth,
                "candidate_depth_hit": depth_hit,
                "aperture_state": "bounded_at_limit" if depth_hit else "bounded_under_limit",
            }
        )

    _assert_admission_bindings(review, candidates)

    diagnostic: dict[str, Any] | None = None
    if effective_config.root_diagnostic:
        root = contract_a["root_proposition"]
        diagnostic_target = PrimaryTarget(
            proposition_id=str(root["proposition_id"]),
            text=str(root["text"]),
            text_sha256=str(root["text_sha256"]),
            role="root",
            sequence=None,
        )
        query_id = query_identity(
            contract_a_sha256=str(contract_a["handoff_sha256"]),
            proposition_id=diagnostic_target["proposition_id"],
            text_sha256=diagnostic_target["text_sha256"],
            retrieval_lane=DIAGNOSTIC_ROOT_LANE,
            config_sha256=effective_config.identity,
        )
        retrieval_id = retrieval_identity(query_id)
        hits = query_bm25(root["text"], chunks, top_k=effective_config.candidate_depth)
        diagnostic_candidates = [
            _diagnostic_candidate(hit_chunk=hit.chunk, rank=rank, source_hashes=source_hashes)
            for rank, hit in enumerate(hits, start=1)
        ]
        diagnostic = {
            "normative": False,
            "retrieval_lane": DIAGNOSTIC_ROOT_LANE,
            "retrieval_id": retrieval_id,
            "query_id": query_id,
            "proposition_id": root["proposition_id"],
            "query_text_sha256": root["text_sha256"],
            "requested_source_ids": source_ids,
            "searched_source_ids": source_ids,
            "returned_count": len(diagnostic_candidates),
            "candidate_depth_limit": effective_config.candidate_depth,
            "candidate_depth_hit": len(diagnostic_candidates) == effective_config.candidate_depth,
            "candidates": diagnostic_candidates,
        }

    statuses = [str(row["status"]) for row in executions]
    execution_state = (
        "not_run"
        if all(status == "not_run" for status in statuses)
        else "complete"
        if all(status == "completed" for status in statuses)
        else "partial"
    )

    package: dict[str, Any] = {
        "schema": PACKAGE_SCHEMA,
        "contract_version": PACKAGE_CONTRACT_VERSION,
        "producer": {
            "producer_id": "camerontjs-dot/evidence-bundler",
            "producer_version": __version__,
        },
        "contract_a_authority": {
            "contract_version": CONTRACT_A_VERSION,
            "release_commit": CONTRACT_A_RELEASE_COMMIT,
            "validator_blob": CONTRACT_A_VALIDATOR_BLOB,
        },
        "contract_a": deepcopy(contract_a),
        "config": effective_config.as_payload(),
        "config_sha256": effective_config.identity,
        "execution_state": execution_state,
        "primary_targets": [dict(target) for target in targets],
        "retrieval_plans": plans,
        "retrieval_executions": executions,
        "candidates": candidates,
        "diagnostics": {"root_retrieval": diagnostic},
        "package_sha256": "sha256:" + "0" * 64,
    }
    package["package_sha256"] = compute_package_sha256(package)
    return validate_package(package)
