from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
from evidence_bundler.retrieval.embedding_retriever import (
    SemanticIndex,
    TextEmbedder,
    load_embedding_model,
)
from evidence_bundler.retrieval.hybrid import reciprocal_rank_fusion

SCHEMA_VERSION = "1.0"
ADAPTER_ID = "eb-rc2-current-stack-presegmented-block-b-dev-v1"
BENCHMARK_TREE_SHA256 = "0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
SEMANTIC_QUERY_PREFIX = "Represent this sentence for searching relevant passages:"
RRF_K = 60


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise TypeError(f"{path}: JSONL row must be an object")
        rows.append(value)
    return rows


def ordered_passages(
    all_passages: list[dict[str, Any]],
    source_ids: list[str],
    *,
    reverse_source_order: bool = False,
) -> list[dict[str, Any]]:
    allowed = set(source_ids)
    selected = [row for row in all_passages if row["source_id"] in allowed]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        grouped[str(row["source_id"])].append(row)
    source_order = sorted(
        grouped,
        key=lambda sid: (
            min(int(p["source_order"]) for p in grouped[sid]),
            sid,
        ),
        reverse=reverse_source_order,
    )
    output: list[dict[str, Any]] = []
    for source_id in source_order:
        output.extend(
            sorted(
                grouped[source_id],
                key=lambda p: (int(p["passage_order"]), str(p["passage_id"])),
            )
        )
    return output


def build_chunks(
    rows: list[dict[str, Any]],
) -> tuple[list[DocumentChunk], dict[str, dict[str, Any]]]:
    chunks: list[DocumentChunk] = []
    by_chunk_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        text = str(row["text"])
        chunk_id = f"{row['source_id']}:{row['passage_id']}"
        chunk = DocumentChunk(
            chunk_id=chunk_id,
            source_id=str(row["source_id"]),
            source_path=Path(f"{row['source_id']}.txt"),
            title=None,
            chunk_level="paragraph",
            parent_chunk_id=None,
            heading_path=[],
            section_tag=None,
            char_start=0,
            char_end=len(text),
            chunk_hash=f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}",
            excerpt=" ".join(text.split())[:240],
            text=text,
        )
        chunks.append(chunk)
        by_chunk_id[chunk_id] = row
    return chunks, by_chunk_id


def _arm_config(arm: str) -> RetrievalConfig:
    if arm == "bm25":
        return RetrievalConfig(retrieval_method="bm25")
    if arm == "semantic":
        return RetrievalConfig(
            retrieval_method="semantic",
            embedding_model=EMBEDDING_MODEL,
            embedding_model_revision=EMBEDDING_REVISION,
            semantic_query_prefix=SEMANTIC_QUERY_PREFIX,
            require_immutable_model_revisions=True,
        )
    if arm == "hybrid":
        return RetrievalConfig(
            retrieval_method="hybrid",
            embedding_model=EMBEDDING_MODEL,
            embedding_model_revision=EMBEDDING_REVISION,
            semantic_query_prefix=SEMANTIC_QUERY_PREFIX,
            rrf_k_constant=RRF_K,
            rerank_enabled=False,
            contradiction_enabled=False,
            require_immutable_model_revisions=True,
        )
    raise ValueError(f"unsupported arm: {arm}")


def _build_semantic_index(
    chunks: list[DocumentChunk],
    embedder: TextEmbedder,
    config: RetrievalConfig,
) -> SemanticIndex:
    return SemanticIndex.build(
        chunks,
        embedder=embedder,
        corpus_hash=f"sha256:{BENCHMARK_TREE_SHA256}",
        embedding_model=str(config.embedding_model),
        embedding_model_revision=(
            str(config.embedding_model_revision)
            if config.embedding_model_revision is not None
            else None
        ),
        semantic_query_prefix=(
            str(config.semantic_query_prefix)
            if config.semantic_query_prefix is not None
            else None
        ),
        show_progress_bar=False,
    )


def _rank(
    *,
    arm: str,
    claim_text: str,
    k: int,
    chunks: list[DocumentChunk],
    embedder: TextEmbedder | None,
    config: RetrievalConfig,
) -> list[tuple[str, float]]:
    if arm == "bm25":
        lexical = BM25Retriever(chunks)
        return [(hit.chunk.chunk_id, float(hit.score)) for hit in lexical.query(
            claim_text,
            top_k=k,
            score_floor=0.0,
        )]

    if embedder is None:
        raise ValueError(f"{arm} requires an embedder")
    semantic = _build_semantic_index(chunks, embedder, config)

    if arm == "semantic":
        return [
            (hit.chunk.chunk_id, float(hit.semantic_score))
            for hit in semantic.query(claim_text, top_k=k)
        ]

    lexical = BM25Retriever(chunks)
    lexical_hits = lexical.query(claim_text, top_k=k, score_floor=0.0)
    semantic_hits = semantic.query(claim_text, top_k=k)
    fused = reciprocal_rank_fusion(
        [
            [hit.chunk.chunk_id for hit in lexical_hits],
            [hit.chunk.chunk_id for hit in semantic_hits],
        ],
        k=config.rrf_k_constant,
    )
    return [(row.chunk_id, float(row.fusion_score)) for row in fused[:k]]


def run_case(
    *,
    all_passages: list[dict[str, Any]],
    case: dict[str, Any],
    subsets: dict[str, dict[str, Any]],
    arm: str,
    apparatus_sha: str,
    embedder: TextEmbedder | None,
    reverse_source_order: bool = False,
) -> dict[str, Any]:
    subset_id = str(case["accessible_subset_id"])
    subset = subsets[subset_id]
    source_ids = [str(value) for value in subset["source_ids"]]
    k = int(case["runtime_config"]["maximum_passages"])
    rows = ordered_passages(
        all_passages,
        source_ids,
        reverse_source_order=reverse_source_order,
    )
    chunks, by_chunk_id = build_chunks(rows)
    config = _arm_config(arm)
    ranked = _rank(
        arm=arm,
        claim_text=str(case["claim_text"]),
        k=k,
        chunks=chunks,
        embedder=embedder,
        config=config,
    )
    hits = []
    for rank, (chunk_id, score) in enumerate(ranked, start=1):
        row = by_chunk_id[chunk_id]
        hits.append(
            {
                "rank": rank,
                "source_id": row["source_id"],
                "passage_id": row["passage_id"],
                "score": score,
                "text": row["text"],
            }
        )

    config_record = {
        "adapter_id": ADAPTER_ID,
        "apparatus_sha": apparatus_sha,
        "arm": arm,
        "query_construction": "case.claim_text verbatim",
        "output_top_k": k,
        "lexical_candidate_top_k": k if arm in {"bm25", "hybrid"} else 0,
        "semantic_candidate_top_k": k if arm in {"semantic", "hybrid"} else 0,
        "hybrid_rrf_k": RRF_K if arm == "hybrid" else None,
        "embedding_model": EMBEDDING_MODEL if arm in {"semantic", "hybrid"} else None,
        "embedding_revision": EMBEDDING_REVISION if arm in {"semantic", "hybrid"} else None,
        "semantic_query_prefix": (
            SEMANTIC_QUERY_PREFIX if arm in {"semantic", "hybrid"} else None
        ),
        "rerank_enabled": False,
        "contradiction_enabled": False,
        "representation": "one frozen RC2 runtime passage -> one DocumentChunk",
        "source_subset": subset_id,
        "source_order": "reverse" if reverse_source_order else "canonical",
    }
    configuration_id = "sha256:" + sha256_bytes(canonical_json_bytes(config_record))
    source_ids_digest = sha256_bytes(canonical_json_bytes(sorted(source_ids)))

    return {
        "schema_version": SCHEMA_VERSION,
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
            "basis": "The adapter records the frozen aperture; retrieval does not establish corpus completeness.",
        },
        "answerability_claim": {
            "status": "not_established",
            "basis": "Retrieval nomination is not semantic answerability assessment.",
        },
        "run_identity": {
            "retriever_id": f"evidence-bundler-{arm}@{apparatus_sha}",
            "configuration_id": configuration_id,
            "run_id": f"{apparatus_sha}:{case['case_id']}:{ADAPTER_ID}:{arm}",
            "adapter_id": ADAPTER_ID,
            "representation": "frozen_rc2_presegmented_passages",
        },
        "diagnostic_receipt": config_record,
    }


def run_split(
    *,
    runtime_root: Path,
    split: str,
    arm: str,
    apparatus_sha: str,
    output: Path,
    reverse_source_order: bool = False,
    embedder: TextEmbedder | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    all_passages = load_jsonl(runtime_root / "passages.jsonl")
    cases = load_jsonl(runtime_root / f"{split}_cases.jsonl")
    subsets_payload = load_json(runtime_root / "apertures.json")
    subsets = {str(row["subset_id"]): row for row in subsets_payload["subsets"]}

    if arm in {"semantic", "hybrid"} and embedder is None:
        embedder = load_embedding_model(
            EMBEDDING_MODEL,
            revision=EMBEDDING_REVISION,
        )

    results = [
        run_case(
            all_passages=all_passages,
            case=case,
            subsets=subsets,
            arm=arm,
            apparatus_sha=apparatus_sha,
            embedder=embedder,
            reverse_source_order=reverse_source_order,
        )
        for case in sorted(cases, key=lambda row: str(row["case_id"]))
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        for result in results:
            handle.write(canonical_json_bytes(result))

    elapsed_seconds = time.perf_counter() - started
    total_hits = sum(len(result["hits"]) for result in results)
    total_source_candidate_positions = sum(
        int(result["diagnostic_receipt"]["lexical_candidate_top_k"])
        + int(result["diagnostic_receipt"]["semantic_candidate_top_k"])
        for result in results
    )
    return {
        "schema_version": "1.0",
        "adapter_id": ADAPTER_ID,
        "apparatus_sha": apparatus_sha,
        "benchmark_tree_sha256": BENCHMARK_TREE_SHA256,
        "split": split,
        "arm": arm,
        "case_count": len(results),
        "returned_hits": total_hits,
        "elapsed_seconds": elapsed_seconds,
        "semantic_index_passage_encodes": (
            sum(len(ordered_passages(all_passages, [str(value) for value in subsets[str(case["accessible_subset_id"])]["source_ids"]])) for case in cases)
            if arm in {"semantic", "hybrid"}
            else 0
        ),
        "semantic_query_encodes": len(cases) if arm in {"semantic", "hybrid"} else 0,
        "source_candidate_positions_budgeted": total_source_candidate_positions,
        "output_sha256": sha256_bytes(output.read_bytes()),
        "embedding_model": EMBEDDING_MODEL if arm in {"semantic", "hybrid"} else None,
        "embedding_revision": EMBEDDING_REVISION if arm in {"semantic", "hybrid"} else None,
        "rerank_enabled": False,
        "contradiction_enabled": False,
        "production_chunking_measured": False,
        "native_aperture_receipts_measured": False,
        "semantic_answerability_measured": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--split", choices=("dev",), required=True)
    parser.add_argument("--arm", choices=("bm25", "semantic", "hybrid"), required=True)
    parser.add_argument("--apparatus-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reverse-source-order", action="store_true")
    args = parser.parse_args()
    receipt = run_split(
        runtime_root=args.runtime_root,
        split=args.split,
        arm=args.arm,
        apparatus_sha=args.apparatus_sha,
        output=args.output,
        reverse_source_order=args.reverse_source_order,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
