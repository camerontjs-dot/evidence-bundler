from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
from evidence_bundler.retrieval.embedding_retriever import SemanticIndex, TextEmbedder
from research.contract_a_decomposition_retrieval_sensitivity_dev_rc1.runtime_runner import (
    CORPUS_TREE_SHA256,
    EMBEDDING_MODEL,
    EMBEDDING_REVISION,
    SEMANTIC_QUERY_PREFIX,
    build_chunks,
    load_embedding_model,
    paragraph_rows,
)

ADAPTER_ID = "eb-parent-child-complementarity-dev-v1"
STRATEGY_ORDER = ("D1", "D2", "D3", "D4", "D5a", "D5b", "D6")
RETRIEVERS = ("bm25", "semantic")
BUDGET_MODES = ("equal_total", "equal_per_query")


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _paragraphs_from_contract_sources(obj: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in obj["sources"]:
        source_id = str(source["source_id"])
        paragraphs = [
            part.strip()
            for part in re.split(r"\n\s*\n", str(source["content"]))
            if part.strip()
        ]
        for index, paragraph in enumerate(paragraphs):
            rows.append(
                {
                    "source_id": source_id,
                    "paragraph_index": index,
                    "paragraph_id": f"{source_id}:paragraph:{index:03d}",
                    "text": paragraph,
                }
            )
    return rows


def _verify_source_equivalence(
    *, obj: dict[str, Any], benchmark_root: Path
) -> None:
    benchmark = {
        (str(row["source_id"]), int(row["paragraph_index"])): str(row["text"])
        for row in paragraph_rows(benchmark_root)
    }
    for row in _paragraphs_from_contract_sources(obj):
        key = (str(row["source_id"]), int(row["paragraph_index"]))
        if benchmark.get(key) != str(row["text"]):
            raise RuntimeError(f"Contract A source bytes differ from frozen benchmark: {key}")


def _query_bm25(
    index: BM25Retriever, query: str, top_k: int
) -> list[tuple[str, float, int]]:
    if top_k <= 0:
        return []
    return [
        (hit.chunk.chunk_id, float(hit.score), int(hit.rank))
        for hit in index.query(query, top_k=top_k, score_floor=0.0)
    ]


def _query_semantic(
    index: SemanticIndex, query: str, top_k: int
) -> list[tuple[str, float, int]]:
    if top_k <= 0:
        return []
    return [
        (hit.chunk.chunk_id, float(hit.semantic_score), int(hit.rank))
        for hit in index.query(query, top_k=top_k)
    ]


def _alloc(total: int, count: int) -> list[int]:
    if count <= 0:
        return []
    base, remainder = divmod(total, count)
    return [base + (1 if index < remainder else 0) for index in range(count)]


def _lanes(obj: dict[str, Any], *, include_root: bool, include_children: bool) -> list[dict[str, Any]]:
    lanes: list[dict[str, Any]] = []
    root = obj["root_proposition"]
    if include_root:
        lanes.append(
            {
                "proposition_id": root["proposition_id"],
                "proposition_role": "root",
                "retrieval_lane": "root_lane",
                "sequence": 0,
                "query_text": root["text"],
            }
        )
    if include_children and obj["decomposition"]["state"] == "declared":
        for child in sorted(
            obj["decomposition"]["children"], key=lambda row: int(row["sequence"])
        ):
            lanes.append(
                {
                    "proposition_id": child["proposition_id"],
                    "proposition_role": "child",
                    "retrieval_lane": "child_lane",
                    "sequence": int(child["sequence"]),
                    "query_text": child["text"],
                }
            )
    return lanes


def _plan(
    obj: dict[str, Any], *, arm: str, budget_mode: str, k: int
) -> list[dict[str, Any]]:
    if arm == "R0":
        lanes = _lanes(obj, include_root=True, include_children=False)
    elif arm == "R1":
        lanes = _lanes(obj, include_root=False, include_children=True)
    elif arm == "R2":
        lanes = _lanes(obj, include_root=True, include_children=True)
    else:
        raise ValueError(f"unknown arm: {arm}")
    if budget_mode == "equal_total":
        allocations = _alloc(k, len(lanes))
    elif budget_mode == "equal_per_query":
        allocations = [k] * len(lanes)
    else:
        raise ValueError(f"unknown budget mode: {budget_mode}")
    return [
        {
            **lane,
            "query_id": f"{lane['retrieval_lane']}:{lane['proposition_id']}",
            "requested_top_k": allocation,
        }
        for lane, allocation in zip(lanes, allocations, strict=True)
    ]


def _run_plan(
    *,
    retriever: str,
    plan: list[dict[str, Any]],
    bm25: BM25Retriever,
    semantic: SemanticIndex,
    by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    states: dict[str, dict[str, Any]] = {}
    requested = 0
    returned = 0
    no_hit_queries = 0
    for lane in plan:
        top_k = int(lane["requested_top_k"])
        requested += top_k
        if retriever == "bm25":
            results = _query_bm25(bm25, str(lane["query_text"]), top_k)
        elif retriever == "semantic":
            results = _query_semantic(semantic, str(lane["query_text"]), top_k)
        else:
            raise ValueError(retriever)
        returned += len(results)
        if not results:
            no_hit_queries += 1
        for paragraph_id, score, rank in results:
            state = states.setdefault(
                paragraph_id,
                {
                    "paragraph_id": paragraph_id,
                    "source_id": by_id[paragraph_id]["source_id"],
                    "paragraph_index": by_id[paragraph_id]["paragraph_index"],
                    "text": by_id[paragraph_id]["text"],
                    "best_rank": rank,
                    "best_score": score,
                    "relationships": [],
                },
            )
            state["best_rank"] = min(int(state["best_rank"]), rank)
            state["best_score"] = max(float(state["best_score"]), score)
            state["relationships"].append(
                {
                    "query_id": lane["query_id"],
                    "proposition_id": lane["proposition_id"],
                    "proposition_role": lane["proposition_role"],
                    "retrieval_lane": lane["retrieval_lane"],
                    "sequence": lane["sequence"],
                    "requested_top_k": top_k,
                    "rank": rank,
                    "score": score,
                }
            )

    hits = sorted(
        states.values(),
        key=lambda row: (
            int(row["best_rank"]),
            -float(row["best_score"]),
            str(row["paragraph_id"]),
        ),
    )
    root_only: list[str] = []
    child_only: list[str] = []
    both: list[str] = []
    for hit in hits:
        roles = {str(rel["proposition_role"]) for rel in hit["relationships"]}
        if roles == {"root"}:
            root_only.append(str(hit["paragraph_id"]))
        elif roles == {"child"}:
            child_only.append(str(hit["paragraph_id"]))
        elif roles == {"root", "child"}:
            both.append(str(hit["paragraph_id"]))

    return {
        "query_plan": plan,
        "requested_candidate_positions": requested,
        "returned_before_dedupe": returned,
        "unique_candidates": len(hits),
        "duplicate_burden": returned - len(hits),
        "no_hit_queries": no_hit_queries,
        "source_diversity": len({str(hit["source_id"]) for hit in hits}),
        "root_only_passage_ids": root_only,
        "child_only_passage_ids": child_only,
        "both_passage_ids": both,
        "hits": hits,
    }


def _flatten_r2(r2: dict[str, Any]) -> dict[str, Any]:
    flattened_hits = [
        {
            "paragraph_id": hit["paragraph_id"],
            "source_id": hit["source_id"],
            "paragraph_index": hit["paragraph_index"],
            "text": hit["text"],
            "best_rank": hit["best_rank"],
            "best_score": hit["best_score"],
        }
        for hit in r2["hits"]
    ]
    return {
        "derived_from": "R2",
        "same_physical_passage_ids": [str(hit["paragraph_id"]) for hit in flattened_hits],
        "proposition_and_lane_attribution_removed": True,
        "requested_candidate_positions": r2["requested_candidate_positions"],
        "returned_before_dedupe": r2["returned_before_dedupe"],
        "unique_candidates": r2["unique_candidates"],
        "duplicate_burden": r2["duplicate_burden"],
        "source_diversity": r2["source_diversity"],
        "hits": flattened_hits,
    }


def run(
    *,
    benchmark_root: Path,
    fixture_dir: Path,
    expected_manifest_sha256: str,
    apparatus_sha: str,
    output: Path,
    embedder: TextEmbedder | None = None,
) -> dict[str, Any]:
    manifest_path = fixture_dir / "MANIFEST.json"
    actual_manifest_sha = sha256_bytes(manifest_path.read_bytes())
    if actual_manifest_sha != expected_manifest_sha256:
        raise RuntimeError("frozen Contract A fixture manifest digest mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if embedder is None:
        embedder = load_embedding_model(EMBEDDING_MODEL, revision=EMBEDDING_REVISION)

    started = time.perf_counter()
    output_cases: list[dict[str, Any]] = []
    for claim_id in sorted({str(row["original_claim_id"]) for row in manifest["records"]}):
        strategy_records = {
            str(row["strategy"]): row
            for row in manifest["records"]
            if str(row["original_claim_id"]) == claim_id
        }
        reference_obj = json.loads(
            (fixture_dir / str(strategy_records["D1"]["path"])).read_text(encoding="utf-8")
        )
        _verify_source_equivalence(obj=reference_obj, benchmark_root=benchmark_root)
        paragraphs = _paragraphs_from_contract_sources(reference_obj)
        chunks, by_id = build_chunks(paragraphs)
        bm25 = BM25Retriever(chunks)
        semantic = SemanticIndex.build(
            chunks,
            embedder=embedder,
            corpus_hash="sha256:"
            + hashlib.sha256(f"{CORPUS_TREE_SHA256}:{claim_id}".encode()).hexdigest(),
            embedding_model=EMBEDDING_MODEL,
            embedding_model_revision=EMBEDDING_REVISION,
            semantic_query_prefix=SEMANTIC_QUERY_PREFIX,
            show_progress_bar=False,
        )
        k = 12
        case_out: dict[str, Any] = {
            "original_claim_id": claim_id,
            "k": k,
            "source_ids": [str(row["source_id"]) for row in reference_obj["sources"]],
            "searchable_paragraph_count": len(paragraphs),
            "strategies": {},
        }
        for strategy in STRATEGY_ORDER:
            manifest_row = strategy_records[strategy]
            obj = json.loads((fixture_dir / str(manifest_row["path"])).read_text(encoding="utf-8"))
            if canonical_json_bytes(obj["root_proposition"]) != canonical_json_bytes(
                reference_obj["root_proposition"]
            ) or canonical_json_bytes(obj["sources"]) != canonical_json_bytes(
                reference_obj["sources"]
            ):
                raise RuntimeError(f"root/source treatment invariant failed: {claim_id} {strategy}")
            strategy_out: dict[str, Any] = {
                "decomposition_state": obj["decomposition"]["state"],
                "decomposition_id": obj["decomposition"].get("decomposition_id"),
                "handoff_sha256": obj["handoff_sha256"],
                "child_count": len(obj["decomposition"].get("children", [])),
                "retrievers": {},
            }
            for retriever in RETRIEVERS:
                retriever_out: dict[str, Any] = {}
                for budget_mode in BUDGET_MODES:
                    r0 = _run_plan(
                        retriever=retriever,
                        plan=_plan(obj, arm="R0", budget_mode=budget_mode, k=k),
                        bm25=bm25,
                        semantic=semantic,
                        by_id=by_id,
                    )
                    if obj["decomposition"]["state"] == "declared":
                        r1 = _run_plan(
                            retriever=retriever,
                            plan=_plan(obj, arm="R1", budget_mode=budget_mode, k=k),
                            bm25=bm25,
                            semantic=semantic,
                            by_id=by_id,
                        )
                        r2 = _run_plan(
                            retriever=retriever,
                            plan=_plan(obj, arm="R2", budget_mode=budget_mode, k=k),
                            bm25=bm25,
                            semantic=semantic,
                            by_id=by_id,
                        )
                        r3 = _flatten_r2(r2)
                    else:
                        r1 = None
                        r2 = None
                        r3 = None
                    retriever_out[budget_mode] = {"R0": r0, "R1": r1, "R2": r2, "R3": r3}
                strategy_out["retrievers"][retriever] = retriever_out
            case_out["strategies"][strategy] = strategy_out
        output_cases.append(case_out)

    record = {
        "schema_version": "1.0",
        "experiment": "decomposition-parent-child-complementarity-dev-rc1",
        "adapter_id": ADAPTER_ID,
        "apparatus_sha": apparatus_sha,
        "fixture_manifest_sha256": expected_manifest_sha256,
        "corpus_tree_sha256": CORPUS_TREE_SHA256,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_revision": EMBEDDING_REVISION,
        "split": "dev",
        "cases": output_cases,
        "elapsed_seconds": time.perf_counter() - started,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(record))
    return {
        "case_count": len(output_cases),
        "output_sha256": sha256_bytes(output.read_bytes()),
        "apparatus_sha": apparatus_sha,
        "fixture_manifest_sha256": expected_manifest_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--fixture-dir", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--apparatus-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(
        benchmark_root=args.benchmark_root,
        fixture_dir=args.fixture_dir,
        expected_manifest_sha256=args.expected_manifest_sha256,
        apparatus_sha=args.apparatus_sha,
        output=args.output,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
