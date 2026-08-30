from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
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
    load_json,
    load_jsonl,
    ordered_passages,
)

MULTIPLIERS = (1, 2, 4)


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity(chunk_id: str, by_chunk_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    row = by_chunk_id[chunk_id]
    return {
        "source_id": row["source_id"],
        "passage_id": row["passage_id"],
    }


def run_candidate_pools(
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

    config = RetrievalConfig(
        retrieval_method="semantic",
        embedding_model=EMBEDDING_MODEL,
        embedding_model_revision=EMBEDDING_REVISION,
        semantic_query_prefix=SEMANTIC_QUERY_PREFIX,
        require_immutable_model_revisions=True,
    )
    if embedder is None:
        embedder = load_embedding_model(
            EMBEDDING_MODEL,
            revision=EMBEDDING_REVISION,
        )

    output_cases: list[dict[str, Any]] = []
    total_passage_encodes = 0
    for case in sorted(cases, key=lambda row: str(row["case_id"])):
        subset_id = str(case["accessible_subset_id"])
        source_ids = [str(value) for value in subsets[subset_id]["source_ids"]]
        rows = ordered_passages(all_passages, source_ids)
        chunks, by_chunk_id = build_chunks(rows)
        total_passage_encodes += len(chunks)
        k = int(case["runtime_config"]["maximum_passages"])
        max_requested = max(MULTIPLIERS) * k

        lexical = BM25Retriever(chunks)
        lexical_hits = lexical.query(
            str(case["claim_text"]),
            top_k=max_requested,
            score_floor=0.0,
        )
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
        semantic_hits = semantic.query(str(case["claim_text"]), top_k=max_requested)

        multiplier_rows: dict[str, Any] = {}
        for multiplier in MULTIPLIERS:
            requested = multiplier * k
            lexical_slice = lexical_hits[:requested]
            semantic_slice = semantic_hits[:requested]
            multiplier_rows[str(multiplier)] = {
                "requested_per_retriever": requested,
                "lexical": [
                    {
                        **_identity(hit.chunk.chunk_id, by_chunk_id),
                        "rank": rank,
                        "score": float(hit.score),
                    }
                    for rank, hit in enumerate(lexical_slice, start=1)
                ],
                "semantic": [
                    {
                        **_identity(hit.chunk.chunk_id, by_chunk_id),
                        "rank": rank,
                        "score": float(hit.semantic_score),
                    }
                    for rank, hit in enumerate(semantic_slice, start=1)
                ],
            }

        output_cases.append(
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "accessible_subset_id": subset_id,
                "k": k,
                "multipliers": multiplier_rows,
            }
        )

    record = {
        "schema_version": "1.0",
        "experiment": "retrieval-candidate-pool-aperture-dev-rc1",
        "apparatus_sha": apparatus_sha,
        "benchmark_tree_sha256": BENCHMARK_TREE_SHA256,
        "split": "dev",
        "multipliers": list(MULTIPLIERS),
        "embedding_model": EMBEDDING_MODEL,
        "embedding_revision": EMBEDDING_REVISION,
        "semantic_query_prefix": SEMANTIC_QUERY_PREFIX,
        "bm25_score_floor": 0.0,
        "rerank_enabled": False,
        "rrf_enabled": False,
        "contradiction_enabled": False,
        "semantic_passage_encodes": total_passage_encodes,
        "semantic_query_encodes": len(cases),
        "elapsed_seconds": time.perf_counter() - started,
        "cases": output_cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(record))
    return {
        "schema_version": "1.0",
        "apparatus_sha": apparatus_sha,
        "case_count": len(output_cases),
        "output_sha256": sha256_bytes(output.read_bytes()),
        "multipliers": list(MULTIPLIERS),
        "semantic_passage_encodes": total_passage_encodes,
        "semantic_query_encodes": len(cases),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--apparatus-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run_candidate_pools(
        runtime_root=args.runtime_root,
        apparatus_sha=args.apparatus_sha,
        output=args.output,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
