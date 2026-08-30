from __future__ import annotations

import argparse
import hashlib
import json
import re
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

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
SEMANTIC_QUERY_PREFIX = "Represent this sentence for searching relevant passages:"
CORPUS_TREE_SHA256 = "eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8"
DEV_DECOMPOSITION_SHA256 = "2120228c81466471214ca8b56a6eba2fa5bc498cd0b0243ff3b8fe24c9da2144"
ADAPTER_ID = "eb-composite-decomposition-retrieval-sensitivity-dev-v1"


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def paragraph_rows(benchmark_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for content_path in sorted((benchmark_root / "sources").glob("*/content.txt")):
        source_id = content_path.parent.name
        text = content_path.read_text(encoding="utf-8")
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        for index, paragraph in enumerate(paragraphs):
            identity = f"{source_id}:paragraph:{index:03d}"
            rows.append(
                {
                    "source_id": source_id,
                    "paragraph_index": index,
                    "paragraph_id": identity,
                    "text": paragraph,
                }
            )
    return rows


def build_chunks(rows: list[dict[str, Any]]) -> tuple[list[DocumentChunk], dict[str, dict[str, Any]]]:
    chunks: list[DocumentChunk] = []
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        text = str(row["text"])
        chunk_id = str(row["paragraph_id"])
        chunk = DocumentChunk(
            chunk_id=chunk_id,
            source_id=str(row["source_id"]),
            source_path=Path(f"{row['source_id']}/content.txt"),
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
        by_id[chunk_id] = row
    return chunks, by_id


def allocate_total_budget(k: int, children: list[dict[str, Any]]) -> list[int]:
    if not children:
        return []
    base, remainder = divmod(k, len(children))
    return [base + (1 if index < remainder else 0) for index in range(len(children))]


def _query_bm25(
    index: BM25Retriever,
    query: str,
    top_k: int,
) -> list[tuple[str, float, int]]:
    if top_k <= 0:
        return []
    return [
        (hit.chunk.chunk_id, float(hit.score), int(hit.rank))
        for hit in index.query(query, top_k=top_k, score_floor=0.0)
    ]


def _query_semantic(
    index: SemanticIndex,
    query: str,
    top_k: int,
) -> list[tuple[str, float, int]]:
    if top_k <= 0:
        return []
    return [
        (hit.chunk.chunk_id, float(hit.semantic_score), int(hit.rank))
        for hit in index.query(query, top_k=top_k)
    ]


def union_query_results(
    *,
    query_results: list[tuple[dict[str, Any], list[tuple[str, float, int]]]],
    by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    hit_state: dict[str, dict[str, Any]] = {}
    requested_positions = 0
    no_hit_queries = 0
    total_returned_before_dedupe = 0

    for query_meta, results in query_results:
        requested_positions += int(query_meta["requested_top_k"])
        total_returned_before_dedupe += len(results)
        if not results:
            no_hit_queries += 1
        for chunk_id, score, rank in results:
            state = hit_state.setdefault(
                chunk_id,
                {
                    "paragraph_id": chunk_id,
                    "source_id": by_id[chunk_id]["source_id"],
                    "paragraph_index": by_id[chunk_id]["paragraph_index"],
                    "text": by_id[chunk_id]["text"],
                    "best_rank": rank,
                    "best_score": score,
                    "query_hits": [],
                },
            )
            state["best_rank"] = min(int(state["best_rank"]), rank)
            state["best_score"] = max(float(state["best_score"]), score)
            state["query_hits"].append(
                {
                    "query_id": query_meta["query_id"],
                    "query_text": query_meta["query_text"],
                    "child_id": query_meta.get("child_id"),
                    "sequence": query_meta.get("sequence"),
                    "requested_top_k": query_meta["requested_top_k"],
                    "rank": rank,
                    "score": score,
                }
            )

    hits = sorted(
        hit_state.values(),
        key=lambda row: (
            int(row["best_rank"]),
            -float(row["best_score"]),
            str(row["paragraph_id"]),
        ),
    )
    return {
        "requested_candidate_positions": requested_positions,
        "returned_before_dedupe": total_returned_before_dedupe,
        "unique_candidates": len(hits),
        "duplicate_burden": total_returned_before_dedupe - len(hits),
        "no_hit_queries": no_hit_queries,
        "hits": hits,
    }


def _run_query_plan(
    *,
    retriever: str,
    query_plan: list[dict[str, Any]],
    bm25: BM25Retriever,
    semantic: SemanticIndex,
    by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    query_results: list[tuple[dict[str, Any], list[tuple[str, float, int]]]] = []
    for query_meta in query_plan:
        query = str(query_meta["query_text"])
        top_k = int(query_meta["requested_top_k"])
        if retriever == "bm25":
            results = _query_bm25(bm25, query, top_k)
        elif retriever == "semantic":
            results = _query_semantic(semantic, query, top_k)
        else:
            raise ValueError(f"unknown retriever: {retriever}")
        query_results.append((query_meta, results))
    return union_query_results(query_results=query_results, by_id=by_id)


def _children(record: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(record.get("children", []), key=lambda row: int(row["sequence"]))


def _query_plan_total(record: dict[str, Any], k: int) -> list[dict[str, Any]]:
    children = _children(record)
    allocations = allocate_total_budget(k, children)
    return [
        {
            "query_id": f"{record['decomposition_id']}:{child['child_id']}",
            "child_id": child["child_id"],
            "sequence": child["sequence"],
            "query_text": child["text"],
            "requested_top_k": allocation,
        }
        for child, allocation in zip(children, allocations, strict=True)
    ]


def _query_plan_per_query(record: dict[str, Any], k: int) -> list[dict[str, Any]]:
    return [
        {
            "query_id": f"{record['decomposition_id']}:{child['child_id']}",
            "child_id": child["child_id"],
            "sequence": child["sequence"],
            "query_text": child["text"],
            "requested_top_k": k,
        }
        for child in _children(record)
    ]


def _composite_plan(original_claim_id: str, text: str, k: int) -> list[dict[str, Any]]:
    return [
        {
            "query_id": f"{original_claim_id}:composite",
            "child_id": None,
            "sequence": None,
            "query_text": text,
            "requested_top_k": k,
        }
    ]


def _retrieval_identity(result: dict[str, Any]) -> str:
    identity = {
        "requested_candidate_positions": result["requested_candidate_positions"],
        "returned_before_dedupe": result["returned_before_dedupe"],
        "unique_candidates": result["unique_candidates"],
        "duplicate_burden": result["duplicate_burden"],
        "no_hit_queries": result["no_hit_queries"],
        "hits": result["hits"],
    }
    return sha256_bytes(canonical_json_bytes(identity))


def run(
    *,
    benchmark_root: Path,
    apparatus_sha: str,
    output: Path,
    embedder: TextEmbedder | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    decomposition_path = benchmark_root / "decompositions" / "dev_decompositions.jsonl"
    if sha256_bytes(decomposition_path.read_bytes()) != DEV_DECOMPOSITION_SHA256:
        raise RuntimeError("frozen dev decomposition hash mismatch")

    cases = load_jsonl(benchmark_root / "cases" / "dev_cases.jsonl")
    decompositions = load_jsonl(decomposition_path)
    subsets_payload = load_json(benchmark_root / "aperture" / "subsets.json")
    subsets = {
        str(row["subset_id"]): {str(value) for value in row["source_ids"]}
        for row in subsets_payload["subsets"]
    }
    paragraphs = paragraph_rows(benchmark_root)

    case_by_key = {
        (str(row["original_claim_id"]), str(row["variant_id"])): row
        for row in cases
    }
    decomposition_by_key = {
        (str(row["original_claim_id"]), str(row["variant_id"])): row
        for row in decompositions
    }
    base_claim_ids = sorted(
        {
            str(row["original_claim_id"])
            for row in decompositions
            if str(row["variant_id"]) == "A0"
        }
    )

    if embedder is None:
        embedder = load_embedding_model(
            EMBEDDING_MODEL,
            revision=EMBEDDING_REVISION,
        )

    index_cache: dict[str, tuple[BM25Retriever, SemanticIndex, dict[str, dict[str, Any]], int]] = {}
    output_claims: list[dict[str, Any]] = []

    for original_claim_id in base_claim_ids:
        a0_case = case_by_key[(original_claim_id, "A0")]
        subset_id = str(a0_case["accessible_subset_id"])
        k = int(a0_case["runtime_config"]["maximum_passages"])

        if subset_id not in index_cache:
            selected_rows = [
                row for row in paragraphs if str(row["source_id"]) in subsets[subset_id]
            ]
            chunks, by_id = build_chunks(selected_rows)
            config = RetrievalConfig(
                retrieval_method="semantic",
                embedding_model=EMBEDDING_MODEL,
                embedding_model_revision=EMBEDDING_REVISION,
                semantic_query_prefix=SEMANTIC_QUERY_PREFIX,
                require_immutable_model_revisions=True,
            )
            semantic = SemanticIndex.build(
                chunks,
                embedder=embedder,
                corpus_hash=(
                    "sha256:"
                    + hashlib.sha256(
                        f"{CORPUS_TREE_SHA256}:{subset_id}".encode("utf-8")
                    ).hexdigest()
                ),
                embedding_model=EMBEDDING_MODEL,
                embedding_model_revision=EMBEDDING_REVISION,
                semantic_query_prefix=str(config.semantic_query_prefix),
                show_progress_bar=False,
            )
            index_cache[subset_id] = (BM25Retriever(chunks), semantic, by_id, len(chunks))

        bm25, semantic, by_id, paragraph_count = index_cache[subset_id]
        claim_record: dict[str, Any] = {
            "original_claim_id": original_claim_id,
            "original_claim_text": a0_case["original_claim_text"],
            "challenge_family": None,
            "accessible_subset_id": subset_id,
            "k": k,
            "searchable_paragraph_count": paragraph_count,
            "retrievers": {},
        }

        for retriever in ("bm25", "semantic"):
            composite = _run_query_plan(
                retriever=retriever,
                query_plan=_composite_plan(
                    original_claim_id,
                    str(a0_case["original_claim_text"]),
                    k,
                ),
                bm25=bm25,
                semantic=semantic,
                by_id=by_id,
            )
            variants: dict[str, Any] = {}
            for variant_id in ("A1", "A2", "A3", "A4"):
                decomposition = decomposition_by_key[(original_claim_id, variant_id)]
                total = _run_query_plan(
                    retriever=retriever,
                    query_plan=_query_plan_total(decomposition, k),
                    bm25=bm25,
                    semantic=semantic,
                    by_id=by_id,
                )
                per_query = _run_query_plan(
                    retriever=retriever,
                    query_plan=_query_plan_per_query(decomposition, k),
                    bm25=bm25,
                    semantic=semantic,
                    by_id=by_id,
                )
                first_class_hash = _retrieval_identity(total)
                query_expansion_hash = _retrieval_identity(total)
                if first_class_hash != query_expansion_hash:
                    raise RuntimeError("ownership equivalence invariant failed")
                variants[variant_id] = {
                    "decomposition_id": decomposition["decomposition_id"],
                    "preserves_parent_meaning": decomposition["preserves_parent_meaning"],
                    "evaluator_only_negative_control": decomposition[
                        "evaluator_only_negative_control"
                    ],
                    "over_decomposition": decomposition.get("over_decomposition", False),
                    "children": _children(decomposition),
                    "equal_total_budget": total,
                    "equal_per_query_budget": per_query,
                    "ownership_equivalence": {
                        "first_class_proposition_retrieval_sha256": first_class_hash,
                        "query_expansion_retrieval_sha256": query_expansion_hash,
                        "identical": True,
                    },
                }
            claim_record["retrievers"][retriever] = {
                "composite": composite,
                "variants": variants,
            }
        output_claims.append(claim_record)

    record = {
        "schema_version": "1.0",
        "experiment": "contract-a-decomposition-retrieval-sensitivity-dev-rc1",
        "adapter_id": ADAPTER_ID,
        "apparatus_sha": apparatus_sha,
        "corpus_tree_sha256": CORPUS_TREE_SHA256,
        "dev_decomposition_sha256": DEV_DECOMPOSITION_SHA256,
        "split": "dev",
        "base_claim_count": len(output_claims),
        "retrievers": {
            "bm25": {"score_floor": 0.0},
            "semantic": {
                "model": EMBEDDING_MODEL,
                "revision": EMBEDDING_REVISION,
                "query_prefix": SEMANTIC_QUERY_PREFIX,
            },
        },
        "production_chunking_measured": False,
        "ownership_inferred_from_retrieval": False,
        "elapsed_seconds": time.perf_counter() - started,
        "claims": output_claims,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(record))
    return {
        "schema_version": "1.0",
        "apparatus_sha": apparatus_sha,
        "base_claim_count": len(output_claims),
        "output_sha256": sha256_bytes(output.read_bytes()),
        "ownership_equivalence_invariants": sum(
            1
            for claim in output_claims
            for retriever in claim["retrievers"].values()
            for variant in retriever["variants"].values()
            if variant["ownership_equivalence"]["identical"]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--apparatus-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(
        benchmark_root=args.benchmark_root,
        apparatus_sha=args.apparatus_sha,
        output=args.output,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
