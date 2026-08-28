from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever

SUT_SHA = "c8189c31adbab11729c31430c2070126224a2d42"
SCHEMA_VERSION = "1.0"
ADAPTER_ID = "eb-rc2-real-bm25-presegmented-adapter-v1"


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise TypeError(f"{path}: JSONL row must be an object")
        rows.append(row)
    return rows


def ordered_passages(
    all_passages: list[dict[str, Any]],
    source_ids: list[str],
    *,
    reverse_source_order: bool,
) -> list[dict[str, Any]]:
    allowed = set(source_ids)
    selected = [p for p in all_passages if p["source_id"] in allowed]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        grouped[row["source_id"]].append(row)

    source_order = sorted(
        grouped,
        key=lambda sid: (
            min(int(p["source_order"]) for p in grouped[sid]),
            sid,
        ),
        reverse=reverse_source_order,
    )
    out: list[dict[str, Any]] = []
    for source_id in source_order:
        out.extend(
            sorted(
                grouped[source_id],
                key=lambda p: (int(p["passage_order"]), p["passage_id"]),
            )
        )
    return out


def build_chunks(
    rows: list[dict[str, Any]],
) -> tuple[list[DocumentChunk], dict[str, dict[str, Any]]]:
    chunks: list[DocumentChunk] = []
    by_chunk_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        text = row["text"]
        chunk_id = f"{row['source_id']}:{row['passage_id']}"
        chunk = DocumentChunk(
            chunk_id=chunk_id,
            source_id=row["source_id"],
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


def run_case(
    all_passages: list[dict[str, Any]],
    case: dict[str, Any],
    subsets: dict[str, dict[str, Any]],
    *,
    reverse_source_order: bool,
) -> dict[str, Any]:
    subset_id = case["accessible_subset_id"]
    subset = subsets[subset_id]
    source_ids = list(subset["source_ids"])
    k = int(case["runtime_config"]["maximum_passages"])
    rows = ordered_passages(
        all_passages,
        source_ids,
        reverse_source_order=reverse_source_order,
    )
    chunks, by_chunk_id = build_chunks(rows)
    retriever = BM25Retriever(chunks)
    hits = retriever.query(case["claim_text"], top_k=k, score_floor=0.0)

    normalized_hits: list[dict[str, Any]] = []
    for rank, hit in enumerate(hits, 1):
        row = by_chunk_id[hit.chunk.chunk_id]
        normalized_hits.append(
            {
                "rank": rank,
                "source_id": row["source_id"],
                "passage_id": row["passage_id"],
                "score": float(hit.score),
                "text": row["text"],
            }
        )

    config_record = {
        "adapter_id": ADAPTER_ID,
        "sut_sha": SUT_SHA,
        "retrieval_method": "production BM25Retriever",
        "query_construction": "case.claim_text verbatim",
        "score_floor": 0.0,
        "top_k": k,
        "index_unit": "one frozen RC2 runtime passage adapted to one production DocumentChunk",
        "source_subset": subset_id,
        "source_order": "reverse" if reverse_source_order else "canonical",
    }
    configuration_id = "sha256:" + sha256_bytes(canonical_json_bytes(config_record))
    source_ids_digest = sha256_bytes(canonical_json_bytes(sorted(source_ids)))

    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case["case_id"],
        "hits": normalized_hits,
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
            "basis": "The adapter records the mounted frozen aperture; production BM25 retrieval does not establish corpus completeness.",
        },
        "answerability_claim": {
            "status": "not_established",
            "basis": "Retrieval nomination is not a semantic answerability assessment.",
        },
        "run_identity": {
            "retriever_id": f"evidence-bundler-bm25@{SUT_SHA}",
            "configuration_id": configuration_id,
            "run_id": f"{SUT_SHA}:{case['case_id']}:{ADAPTER_ID}:{'reverse' if reverse_source_order else 'canonical'}",
            "adapter_id": ADAPTER_ID,
            "representation": "frozen_rc2_presegmented_passages",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--split", choices=("dev", "sealed"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reverse-source-order", action="store_true")
    args = parser.parse_args()

    all_passages = load_jsonl(args.runtime_root / "passages.jsonl")
    cases = load_jsonl(args.runtime_root / f"{args.split}_cases.jsonl")
    subsets_payload = load_json(args.runtime_root / "apertures.json")
    subsets = {row["subset_id"]: row for row in subsets_payload["subsets"]}

    results = [
        run_case(
            all_passages,
            case,
            subsets,
            reverse_source_order=args.reverse_source_order,
        )
        for case in sorted(cases, key=lambda row: row["case_id"])
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as handle:
        for result in results:
            handle.write(canonical_json_bytes(result))

    receipt = {
        "schema_version": "1.0",
        "adapter_id": ADAPTER_ID,
        "sut_sha": SUT_SHA,
        "split": args.split,
        "case_count": len(results),
        "source_order": "reverse" if args.reverse_source_order else "canonical",
        "output_sha256": sha256_bytes(args.output.read_bytes()),
        "production_chunking_measured": False,
        "native_aperture_receipts_measured": False,
        "semantic_answerability_measured": False,
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
