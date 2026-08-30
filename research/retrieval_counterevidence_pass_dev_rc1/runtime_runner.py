from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from evidence_bundler.models.ca import ScaffoldClaim
from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
from evidence_bundler.retrieval.contradiction import (
    DEFAULT_CONTRADICTION_QUERY_PREFIXES,
    retrieve_contradicting,
)
from evidence_bundler.retrieval.embedding_retriever import (
    SemanticIndex,
    TextEmbedder,
    load_embedding_model,
)
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

RRF_K = 60
ADAPTER_ID = "eb-rc2-counterevidence-pass-dev-v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _claim(case: dict[str, Any]) -> ScaffoldClaim:
    return ScaffoldClaim(
        claim_id=str(case["case_id"]),
        claim_type="retrieval_seed",
        claim_text=str(case["claim_text"]),
        support_status="uncertain",
        claim_strength=0.5,
        extraction_fidelity=1.0,
        source_refs=[],
        counterevidence_checked=False,
        counterevidence_found=False,
        downgraded=False,
        downgrade_reason=None,
        scaffold_notes="RC2 dev synthetic retrieval diagnostic",
    )


def _config(*, k: int, gate_enabled: bool) -> RetrievalConfig:
    return RetrievalConfig(
        retrieval_method="hybrid",
        top_k=k,
        child_top_k=k,
        lexical_score_floor=0.0,
        embedding_model=EMBEDDING_MODEL,
        embedding_model_revision=EMBEDDING_REVISION,
        semantic_child_top_k=k,
        semantic_query_prefix=SEMANTIC_QUERY_PREFIX,
        rrf_candidate_pool=k,
        rrf_k_constant=RRF_K,
        rerank_enabled=False,
        contradiction_enabled=True,
        contradiction_top_k=k,
        counterevidence_lexical_child_top_k=k,
        counterevidence_semantic_child_top_k=k,
        contradiction_query_prefixes=list(DEFAULT_CONTRADICTION_QUERY_PREFIXES),
        contradiction_rerank_enabled=False,
        contradiction_text_gate_enabled=gate_enabled,
        require_immutable_model_revisions=True,
    )


def _supporting_hits(
    *,
    claim_text: str,
    k: int,
    semantic_index: SemanticIndex,
    by_chunk_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "rank": rank,
            "source_id": by_chunk_id[hit.chunk.chunk_id]["source_id"],
            "passage_id": by_chunk_id[hit.chunk.chunk_id]["passage_id"],
            "score": float(hit.semantic_score),
            "text": by_chunk_id[hit.chunk.chunk_id]["text"],
        }
        for rank, hit in enumerate(semantic_index.query(claim_text, top_k=k), start=1)
    ]


def _counter_hits(
    *,
    claim: ScaffoldClaim,
    k: int,
    gate_enabled: bool,
    bm25_index: BM25Retriever,
    semantic_index: SemanticIndex,
    chunks_by_id: dict[str, Any],
    by_chunk_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    config = _config(k=k, gate_enabled=gate_enabled)
    candidates = retrieve_contradicting(
        claim=claim,
        bm25_index=bm25_index,
        semantic_index=semantic_index,
        reranker=None,
        chunks_by_id=chunks_by_id,
        config=config,
    )
    rows: list[dict[str, Any]] = []
    for rank, candidate in enumerate(candidates, start=1):
        source = by_chunk_id[candidate.parent_chunk.chunk_id]
        rows.append(
            {
                "rank": rank,
                "source_id": source["source_id"],
                "passage_id": source["passage_id"],
                "fusion_score": candidate.fusion_score,
                "lexical_score": candidate.lexical_score,
                "semantic_score": candidate.semantic_score,
                "evidence_role": candidate.evidence_role,
                "text": source["text"],
            }
        )
    return rows


def run_split(
    *,
    runtime_root: Path,
    apparatus_sha: str,
    output: Path,
    embedder: TextEmbedder | None = None,
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

    output_rows: list[dict[str, Any]] = []
    total_passage_encodes = 0
    total_counter_query_count = 0
    for case in sorted(cases, key=lambda row: str(row["case_id"])):
        subset_id = str(case["accessible_subset_id"])
        source_ids = [str(value) for value in subsets[subset_id]["source_ids"]]
        passages = ordered_passages(all_passages, source_ids)
        chunks, by_chunk_id = build_chunks(passages)
        chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        k = int(case["runtime_config"]["maximum_passages"])
        claim = _claim(case)

        semantic_index = SemanticIndex.build(
            chunks,
            embedder=embedder,
            corpus_hash=f"sha256:{BENCHMARK_TREE_SHA256}",
            embedding_model=EMBEDDING_MODEL,
            embedding_model_revision=EMBEDDING_REVISION,
            semantic_query_prefix=SEMANTIC_QUERY_PREFIX,
            show_progress_bar=False,
        )
        bm25_index = BM25Retriever(chunks)
        supporting = _supporting_hits(
            claim_text=str(case["claim_text"]),
            k=k,
            semantic_index=semantic_index,
            by_chunk_id=by_chunk_id,
        )
        gate_on = _counter_hits(
            claim=claim,
            k=k,
            gate_enabled=True,
            bm25_index=bm25_index,
            semantic_index=semantic_index,
            chunks_by_id=chunks_by_id,
            by_chunk_id=by_chunk_id,
        )
        gate_off = _counter_hits(
            claim=claim,
            k=k,
            gate_enabled=False,
            bm25_index=bm25_index,
            semantic_index=semantic_index,
            chunks_by_id=chunks_by_id,
            by_chunk_id=by_chunk_id,
        )
        total_passage_encodes += len(chunks)
        total_counter_query_count += 2 * len(DEFAULT_CONTRADICTION_QUERY_PREFIXES)

        output_rows.append(
            {
                "schema_version": "1.0",
                "case_id": case["case_id"],
                "family": case["family"],
                "accessible_subset_id": subset_id,
                "k": k,
                "supporting_semantic_k": supporting,
                "arms": {
                    "E0_disabled": [],
                    "E1_gate_on": gate_on,
                    "E2_gate_off": gate_off,
                },
                "receipt": {
                    "counter_lexical_child_top_k": k,
                    "counter_semantic_child_top_k": k,
                    "counter_output_top_k": k,
                    "contradiction_prefixes": list(DEFAULT_CONTRADICTION_QUERY_PREFIXES),
                    "rrf_k": RRF_K,
                    "contradiction_rerank_enabled": False,
                    "embedding_model": EMBEDDING_MODEL,
                    "embedding_revision": EMBEDDING_REVISION,
                },
            }
        )

    record = {
        "schema_version": "1.0",
        "experiment": "retrieval-counterevidence-pass-dev-rc1",
        "adapter_id": ADAPTER_ID,
        "apparatus_sha": apparatus_sha,
        "benchmark_tree_sha256": BENCHMARK_TREE_SHA256,
        "split": "dev",
        "embedding_model": EMBEDDING_MODEL,
        "embedding_revision": EMBEDDING_REVISION,
        "contradiction_prefixes": list(DEFAULT_CONTRADICTION_QUERY_PREFIXES),
        "rrf_k": RRF_K,
        "semantic_passage_encodes": total_passage_encodes,
        "supporting_query_count": len(cases),
        "counter_query_count_across_E1_E2": total_counter_query_count,
        "elapsed_seconds": time.perf_counter() - started,
        "cases": output_rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(record))
    return {
        "schema_version": "1.0",
        "apparatus_sha": apparatus_sha,
        "case_count": len(output_rows),
        "output_sha256": sha256_bytes(output.read_bytes()),
        "contradiction_prefix_count": len(DEFAULT_CONTRADICTION_QUERY_PREFIXES),
        "semantic_passage_encodes": total_passage_encodes,
        "counter_query_count_across_E1_E2": total_counter_query_count,
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
