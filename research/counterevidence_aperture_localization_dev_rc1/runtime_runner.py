from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from evidence_bundler.models.ca import ScaffoldClaim
from evidence_bundler.models.retrieval import (
    DEFAULT_CONTRADICTION_QUERY_PREFIXES,
    RetrievalConfig,
)
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
from evidence_bundler.retrieval.embedding_retriever import (
    SemanticIndex,
    SemanticSearchHit,
    TextEmbedder,
    load_embedding_model,
)
from evidence_bundler.retrieval.hits import ChunkSearchHit
from evidence_bundler.retrieval.hybrid import reciprocal_rank_fusion
from evidence_bundler.retrieval.parent_aggregator import aggregate_parent_candidates
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
ADAPTER_ID = "eb-rc2-counterevidence-aperture-localization-dev-v1"
FROZEN_PREFIXES = (
    "evidence against",
    "limitations of",
    "contradicts the claim that",
    "does not support",
    "fails to demonstrate",
)
DEPTH_MULTIPLIERS = (1, 2, 4)


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
        scaffold_notes="RC2 dev counterevidence aperture localization diagnostic",
    )


def _config(*, k: int, child_depth: int) -> RetrievalConfig:
    return RetrievalConfig(
        retrieval_method="hybrid",
        top_k=k,
        child_top_k=child_depth,
        lexical_score_floor=0.0,
        embedding_model=EMBEDDING_MODEL,
        embedding_model_revision=EMBEDDING_REVISION,
        semantic_child_top_k=child_depth,
        semantic_query_prefix=SEMANTIC_QUERY_PREFIX,
        rrf_candidate_pool=child_depth,
        rrf_k_constant=RRF_K,
        rerank_enabled=False,
        contradiction_enabled=True,
        contradiction_top_k=k,
        counterevidence_lexical_child_top_k=child_depth,
        counterevidence_semantic_child_top_k=child_depth,
        contradiction_query_prefixes=list(FROZEN_PREFIXES),
        contradiction_rerank_enabled=False,
        contradiction_text_gate_enabled=False,
        require_immutable_model_revisions=True,
    )


def _lexical_row(hit: ChunkSearchHit, by_chunk_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = by_chunk_id[hit.chunk.chunk_id]
    return {
        "rank": int(hit.rank),
        "chunk_id": hit.chunk.chunk_id,
        "source_id": source["source_id"],
        "passage_id": source["passage_id"],
        "score": float(hit.score),
    }


def _semantic_row(
    hit: SemanticSearchHit,
    by_chunk_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source = by_chunk_id[hit.chunk.chunk_id]
    return {
        "rank": int(hit.rank),
        "chunk_id": hit.chunk.chunk_id,
        "source_id": source["source_id"],
        "passage_id": source["passage_id"],
        "score": float(hit.semantic_score),
    }


def _is_better_lexical(candidate: ChunkSearchHit, current: ChunkSearchHit) -> bool:
    if candidate.score != current.score:
        return candidate.score > current.score
    if candidate.rank != current.rank:
        return candidate.rank < current.rank
    return candidate.chunk.chunk_id < current.chunk.chunk_id


def _is_better_semantic(candidate: SemanticSearchHit, current: SemanticSearchHit) -> bool:
    if candidate.semantic_score != current.semantic_score:
        return candidate.semantic_score > current.semantic_score
    if candidate.rank != current.rank:
        return candidate.rank < current.rank
    return candidate.chunk.chunk_id < current.chunk.chunk_id


def _make_fused_hit(
    *,
    chunk_id: str,
    fusion_score: float,
    fused_rank: int,
    chunks_by_id: dict[str, Any],
    lexical_by_id: dict[str, ChunkSearchHit],
    semantic_by_id: dict[str, SemanticSearchHit],
) -> ChunkSearchHit:
    chunk = chunks_by_id[chunk_id]
    lexical = lexical_by_id.get(chunk_id)
    semantic = semantic_by_id.get(chunk_id)
    return ChunkSearchHit(
        chunk=chunk,
        score=float(fusion_score),
        rank=int(fused_rank),
        lexical_score=float(lexical.score) if lexical is not None else None,
        semantic_score=(float(semantic.semantic_score) if semantic is not None else None),
        fusion_score=float(fusion_score),
        lexical_rank=int(lexical.rank) if lexical is not None else None,
        semantic_rank=int(semantic.rank) if semantic is not None else None,
    )


def _supporting_semantic_k(
    *,
    claim_text: str,
    k: int,
    semantic_index: SemanticIndex,
    by_chunk_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _semantic_row(hit, by_chunk_id)
        for hit in semantic_index.query(claim_text, top_k=k)
    ]


def _depth_record(
    *,
    case: dict[str, Any],
    k: int,
    child_depth: int,
    bm25_index: BM25Retriever,
    semantic_index: SemanticIndex,
    chunks_by_id: dict[str, Any],
    by_chunk_id: dict[str, dict[str, Any]],
    support_passage_ids: set[str],
) -> dict[str, Any]:
    rankings: list[list[str]] = []
    prefix_rows: list[dict[str, Any]] = []
    lexical_by_id: dict[str, ChunkSearchHit] = {}
    semantic_by_id: dict[str, SemanticSearchHit] = {}

    for prefix_index, prefix in enumerate(FROZEN_PREFIXES, start=1):
        query = f"{prefix} {str(case['claim_text']).strip()}"
        lexical_hits = bm25_index.query(
            query,
            top_k=child_depth,
            score_floor=0.0,
        )
        semantic_hits = semantic_index.query(query, top_k=child_depth)
        rankings.append([hit.chunk.chunk_id for hit in lexical_hits])
        rankings.append([hit.chunk.chunk_id for hit in semantic_hits])

        for hit in lexical_hits:
            current = lexical_by_id.get(hit.chunk.chunk_id)
            if current is None or _is_better_lexical(hit, current):
                lexical_by_id[hit.chunk.chunk_id] = hit
        for hit in semantic_hits:
            current = semantic_by_id.get(hit.chunk.chunk_id)
            if current is None or _is_better_semantic(hit, current):
                semantic_by_id[hit.chunk.chunk_id] = hit

        lexical_rows = [_lexical_row(hit, by_chunk_id) for hit in lexical_hits]
        semantic_rows = [_semantic_row(hit, by_chunk_id) for hit in semantic_hits]
        union_passage_ids = sorted(
            {row["passage_id"] for row in lexical_rows}
            | {row["passage_id"] for row in semantic_rows}
        )
        prefix_rows.append(
            {
                "prefix_index": prefix_index,
                "prefix": prefix,
                "query": query,
                "lexical": lexical_rows,
                "semantic": semantic_rows,
                "union_passage_ids": union_passage_ids,
            }
        )

    fused = reciprocal_rank_fusion(rankings, k=RRF_K)
    fused_hits = [
        _make_fused_hit(
            chunk_id=row.chunk_id,
            fusion_score=row.fusion_score,
            fused_rank=row.rank,
            chunks_by_id=chunks_by_id,
            lexical_by_id=lexical_by_id,
            semantic_by_id=semantic_by_id,
        )
        for row in fused
    ]
    fused_rows: list[dict[str, Any]] = []
    for row, hit in zip(fused, fused_hits, strict=True):
        source = by_chunk_id[row.chunk_id]
        fused_rows.append(
            {
                "rank": int(row.rank),
                "chunk_id": row.chunk_id,
                "source_id": source["source_id"],
                "passage_id": source["passage_id"],
                "fusion_score": float(row.fusion_score),
                "best_lexical_rank": hit.lexical_rank,
                "best_semantic_rank": hit.semantic_rank,
                "lexical_score": hit.lexical_score,
                "semantic_score": hit.semantic_score,
            }
        )

    config = _config(k=k, child_depth=child_depth)
    parent_candidates = aggregate_parent_candidates(
        claim=_claim(case),
        hits=fused_hits,
        chunks_by_id=chunks_by_id,
        config=config,
        limit=max(1, len(chunks_by_id)),
    )
    parent_rows: list[dict[str, Any]] = []
    for rank, candidate in enumerate(parent_candidates, start=1):
        source = by_chunk_id[candidate.parent_chunk.chunk_id]
        parent_rows.append(
            {
                "rank": rank,
                "chunk_id": candidate.parent_chunk.chunk_id,
                "matched_child_chunk_id": candidate.matched_child_chunk.chunk_id,
                "source_id": source["source_id"],
                "passage_id": source["passage_id"],
                "fusion_score": candidate.fusion_score,
                "lexical_score": candidate.lexical_score,
                "semantic_score": candidate.semantic_score,
            }
        )

    final_rows = parent_rows[:k]
    final_passage_ids = [str(row["passage_id"]) for row in final_rows]
    duplicate_passage_ids = sorted(set(final_passage_ids) & support_passage_ids)

    return {
        "child_depth": child_depth,
        "depth_multiplier": child_depth // k,
        "prefix_rankings": prefix_rows,
        "candidate_union_passage_ids": sorted(
            {
                passage_id
                for prefix_row in prefix_rows
                for passage_id in prefix_row["union_passage_ids"]
            }
        ),
        "fused_rrf_order": fused_rows,
        "parent_candidate_order": parent_rows,
        "final_k": final_rows,
        "final_k_passage_ids": final_passage_ids,
        "support_channel_duplicate_passage_ids": duplicate_passage_ids,
        "support_channel_duplicate_count": len(duplicate_passage_ids),
    }


def run_split(
    *,
    runtime_root: Path,
    apparatus_sha: str,
    output: Path,
    embedder: TextEmbedder | None = None,
) -> dict[str, Any]:
    if tuple(DEFAULT_CONTRADICTION_QUERY_PREFIXES) != FROZEN_PREFIXES:
        raise RuntimeError("Frozen contradiction prefixes no longer match predecessor source")
    if BENCHMARK_TREE_SHA256 != "0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad":
        raise RuntimeError("Frozen benchmark identity mismatch")
    if EMBEDDING_MODEL != "BAAI/bge-small-en-v1.5":
        raise RuntimeError("Frozen embedding model mismatch")
    if EMBEDDING_REVISION != "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a":
        raise RuntimeError("Frozen embedding revision mismatch")

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
    total_counter_queries = 0
    for case in sorted(cases, key=lambda row: str(row["case_id"])):
        subset_id = str(case["accessible_subset_id"])
        source_ids = [str(value) for value in subsets[subset_id]["source_ids"]]
        passages = ordered_passages(all_passages, source_ids)
        chunks, by_chunk_id = build_chunks(passages)
        chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        k = int(case["runtime_config"]["maximum_passages"])

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
        supporting = _supporting_semantic_k(
            claim_text=str(case["claim_text"]),
            k=k,
            semantic_index=semantic_index,
            by_chunk_id=by_chunk_id,
        )
        support_passage_ids = {str(row["passage_id"]) for row in supporting}
        depth_records = [
            _depth_record(
                case=case,
                k=k,
                child_depth=k * multiplier,
                bm25_index=bm25_index,
                semantic_index=semantic_index,
                chunks_by_id=chunks_by_id,
                by_chunk_id=by_chunk_id,
                support_passage_ids=support_passage_ids,
            )
            for multiplier in DEPTH_MULTIPLIERS
        ]
        total_passage_encodes += len(chunks)
        total_counter_queries += (
            len(FROZEN_PREFIXES) * 2 * len(DEPTH_MULTIPLIERS)
        )
        output_rows.append(
            {
                "schema_version": "1.0",
                "case_id": case["case_id"],
                "family": case["family"],
                "accessible_subset_id": subset_id,
                "k": k,
                "supporting_semantic_k": supporting,
                "depths": depth_records,
            }
        )

    record = {
        "schema_version": "1.0",
        "experiment": "counterevidence-aperture-localization-dev-rc1",
        "adapter_id": ADAPTER_ID,
        "apparatus_sha": apparatus_sha,
        "predecessor_final_head": "d02b7c61dc0d2779f35a8fa9eb534d9c301abdd8",
        "predecessor_decisive_implementation": "755a1877cb321b8e9a24e6a770ce7dd40e19433f",
        "predecessor_run": 33284797206,
        "benchmark_tree_sha256": BENCHMARK_TREE_SHA256,
        "split": "dev",
        "embedding_model": EMBEDDING_MODEL,
        "embedding_revision": EMBEDDING_REVISION,
        "contradiction_prefixes": list(FROZEN_PREFIXES),
        "rrf_k": RRF_K,
        "text_role_gate_enabled": False,
        "contradiction_rerank_enabled": False,
        "depth_multipliers": list(DEPTH_MULTIPLIERS),
        "semantic_passage_encodes": total_passage_encodes,
        "counter_query_count": total_counter_queries,
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
        "counter_query_count": total_counter_queries,
        "contradiction_prefix_count": len(FROZEN_PREFIXES),
        "depth_multipliers": list(DEPTH_MULTIPLIERS),
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
