from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from evidence_bundler.models.retrieval import CandidateEvidence, RetrievalConfig
from evidence_bundler.retrieval.embedding_retriever import (
    SemanticIndex,
    TextEmbedder,
    load_embedding_model,
)
from evidence_bundler.retrieval.reranker import ParentReranker, load_reranker_model
from research.retrieval_characterization_block_b_dev_rc1.runtime_runner import (
    BENCHMARK_TREE_SHA256,
    EMBEDDING_MODEL,
    EMBEDDING_REVISION,
    SEMANTIC_QUERY_PREFIX,
    build_chunks,
    canonical_json_bytes,
    load_json,
    load_jsonl,
    ordered_passages,
)

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
RERANK_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
CANDIDATE_MULTIPLIER = 4
ADAPTER_ID = "eb-rc2-semantic4k-minilm-rerank-dev-v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _semantic_config() -> RetrievalConfig:
    return RetrievalConfig(
        retrieval_method="semantic",
        embedding_model=EMBEDDING_MODEL,
        embedding_model_revision=EMBEDDING_REVISION,
        semantic_query_prefix=SEMANTIC_QUERY_PREFIX,
        require_immutable_model_revisions=True,
    )


def _candidate(hit: Any, claim_text: str) -> CandidateEvidence:
    return CandidateEvidence(
        claim_id="research-case",
        claim_text=claim_text,
        parent_chunk=hit.chunk,
        matched_child_chunk=hit.chunk,
        child_rank=int(hit.rank),
        lexical_score=None,
        semantic_score=float(hit.semantic_score),
        fusion_score=None,
        rerank_score=None,
        retrieval_method="semantic",
        llm_assisted=False,
        evidence_role="supporting",
    )


def run_case(
    *,
    all_passages: list[dict[str, Any]],
    case: dict[str, Any],
    subsets: dict[str, dict[str, Any]],
    embedder: TextEmbedder,
    reranker: ParentReranker,
    apparatus_sha: str,
) -> tuple[dict[str, Any], int, int]:
    subset_id = str(case["accessible_subset_id"])
    source_ids = [str(value) for value in subsets[subset_id]["source_ids"]]
    rows = ordered_passages(all_passages, source_ids)
    chunks, by_chunk_id = build_chunks(rows)
    k = int(case["runtime_config"]["maximum_passages"])
    candidate_limit = CANDIDATE_MULTIPLIER * k
    config = _semantic_config()

    semantic = SemanticIndex.build(
        chunks,
        embedder=embedder,
        corpus_hash=f"sha256:{BENCHMARK_TREE_SHA256}",
        embedding_model=EMBEDDING_MODEL,
        embedding_model_revision=EMBEDDING_REVISION,
        semantic_query_prefix=(
            str(config.semantic_query_prefix)
            if config.semantic_query_prefix is not None
            else None
        ),
        show_progress_bar=False,
    )
    semantic_hits = semantic.query(str(case["claim_text"]), top_k=candidate_limit)
    candidates = [_candidate(hit, str(case["claim_text"])) for hit in semantic_hits]
    reranked = reranker.rerank(str(case["claim_text"]), candidates)
    selected = reranked[:k]

    hits: list[dict[str, Any]] = []
    for rank, candidate in enumerate(selected, start=1):
        chunk_id = candidate.parent_chunk.chunk_id
        row = by_chunk_id[chunk_id]
        hits.append(
            {
                "rank": rank,
                "source_id": row["source_id"],
                "passage_id": row["passage_id"],
                "score": float(candidate.rerank_score or 0.0),
                "text": row["text"],
            }
        )

    config_record = {
        "adapter_id": ADAPTER_ID,
        "apparatus_sha": apparatus_sha,
        "semantic_candidate_multiplier": CANDIDATE_MULTIPLIER,
        "semantic_candidate_requested": candidate_limit,
        "semantic_candidate_actual": len(candidates),
        "final_top_k": k,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_revision": EMBEDDING_REVISION,
        "semantic_query_prefix": SEMANTIC_QUERY_PREFIX,
        "rerank_model": RERANK_MODEL,
        "rerank_revision": RERANK_REVISION,
        "rerank_pair_count": len(candidates),
        "bm25_enabled": False,
        "rrf_enabled": False,
        "contradiction_enabled": False,
        "source_subset": subset_id,
        "representation": "one frozen RC2 runtime passage -> one DocumentChunk",
    }
    configuration_id = "sha256:" + sha256_bytes(canonical_json_bytes(config_record))
    source_ids_digest = sha256_bytes(canonical_json_bytes(sorted(source_ids)))

    result = {
        "schema_version": "1.0",
        "case_id": case["case_id"],
        "hits": hits,
        "search_scope": {
            "actual_searchable_subset_id": subset_id,
            "observed_scope": {
                "subset_id": subset_id,
                "source_count": len(source_ids),
                "source_ids_sha256": source_ids_digest,
                "receipt_owner": "research_adapter",
            },
        },
        "completeness_claim": {
            "status": "not_established",
            "basis": (
                "The adapter records the frozen aperture; reranking does not establish "
                "corpus completeness."
            ),
        },
        "answerability_claim": {
            "status": "not_established",
            "basis": "Retrieval/reranking is not semantic answerability assessment.",
        },
        "run_identity": {
            "retriever_id": f"evidence-bundler-semantic4k-rerank@{apparatus_sha}",
            "configuration_id": configuration_id,
            "run_id": f"{apparatus_sha}:{case['case_id']}:{ADAPTER_ID}",
            "adapter_id": ADAPTER_ID,
            "representation": "frozen_rc2_presegmented_passages",
        },
        "diagnostic_receipt": config_record,
    }
    return result, len(chunks), len(candidates)


def run_split(
    *,
    runtime_root: Path,
    apparatus_sha: str,
    output: Path,
    embedder: TextEmbedder | None = None,
    rerank_model: Any | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    all_passages = load_jsonl(runtime_root / "passages.jsonl")
    cases = load_jsonl(runtime_root / "dev_cases.jsonl")
    subsets_payload = load_json(runtime_root / "apertures.json")
    subsets = {str(row["subset_id"]): row for row in subsets_payload["subsets"]}

    if embedder is None:
        embedder = load_embedding_model(
            EMBEDDING_MODEL,
            revision=EMBEDDING_REVISION,
        )
    if rerank_model is None:
        rerank_model = load_reranker_model(
            RERANK_MODEL,
            revision=RERANK_REVISION,
        )
    reranker = ParentReranker(rerank_model)

    results: list[dict[str, Any]] = []
    total_passage_encodes = 0
    total_rerank_pairs = 0
    for case in sorted(cases, key=lambda row: str(row["case_id"])):
        result, passage_count, rerank_pairs = run_case(
            all_passages=all_passages,
            case=case,
            subsets=subsets,
            embedder=embedder,
            reranker=reranker,
            apparatus_sha=apparatus_sha,
        )
        results.append(result)
        total_passage_encodes += passage_count
        total_rerank_pairs += rerank_pairs

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        for result in results:
            handle.write(canonical_json_bytes(result))

    return {
        "schema_version": "1.0",
        "adapter_id": ADAPTER_ID,
        "apparatus_sha": apparatus_sha,
        "benchmark_tree_sha256": BENCHMARK_TREE_SHA256,
        "split": "dev",
        "case_count": len(results),
        "semantic_candidate_multiplier": CANDIDATE_MULTIPLIER,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_revision": EMBEDDING_REVISION,
        "rerank_model": RERANK_MODEL,
        "rerank_revision": RERANK_REVISION,
        "semantic_passage_encodes": total_passage_encodes,
        "semantic_query_encodes": len(cases),
        "rerank_pair_count": total_rerank_pairs,
        "returned_hits": sum(len(row["hits"]) for row in results),
        "elapsed_seconds": time.perf_counter() - started,
        "output_sha256": sha256_bytes(output.read_bytes()),
        "production_chunking_measured": False,
        "native_aperture_receipts_measured": False,
        "semantic_answerability_measured": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--apparatus-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run_split(
        runtime_root=args.runtime_root,
        apparatus_sha=args.apparatus_sha,
        output=args.output,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
