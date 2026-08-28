from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever

SUT_SHA = "c8189c31adbab11729c31430c2070126224a2d42"
SCHEMA_VERSION = "1.0"
ADAPTER_ID = "eb-rc1-bm25-frozen-passage-adapter-v1"


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
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TypeError(f"{path}: JSONL row must be an object")
            rows.append(value)
    return rows


def passage_chunks(
    runtime_root: Path,
    source_ids: list[str],
    *,
    reverse_source_order: bool = False,
) -> tuple[list[DocumentChunk], dict[str, dict[str, Any]]]:
    ordered_source_ids = list(source_ids)
    if reverse_source_order:
        ordered_source_ids.reverse()

    chunks: list[DocumentChunk] = []
    by_chunk_id: dict[str, dict[str, Any]] = {}
    for source_id in ordered_source_ids:
        source_dir = runtime_root / "sources" / source_id
        metadata = load_json(source_dir / "metadata.json")
        if metadata["source_id"] != source_id:
            raise ValueError(f"source identity mismatch: {source_id}")
        content_bytes = (source_dir / "content.txt").read_bytes()
        content_text = content_bytes.decode("utf-8")
        if len(content_bytes) != len(content_text):
            raise ValueError(
                f"{source_id}: adapter requires byte offsets to equal Python character offsets"
            )
        if hashlib.sha256(content_bytes).hexdigest() != metadata["content_hash"]:
            raise ValueError(f"content hash mismatch: {source_id}")
        for passage in metadata["passages"]:
            if passage["offset_unit"] != "utf8_byte":
                raise ValueError(f"unsupported offset unit in {source_id}")
            start = int(passage["start_offset"])
            end = int(passage["end_offset"])
            text_bytes = content_bytes[start:end]
            text = text_bytes.decode("utf-8")
            if hashlib.sha256(text_bytes).hexdigest() != passage["text_sha256"]:
                raise ValueError(
                    f"passage hash mismatch: {source_id}/{passage['passage_id']}"
                )
            # The frozen benchmark's permitted source metadata defines exact passage
            # units. Each unit is adapted to one flat production DocumentChunk.
            chunk_id = f"{source_id}:{passage['passage_id']}"
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                source_id=source_id,
                source_path=source_dir / "content.txt",
                title=metadata.get("title"),
                chunk_level="paragraph",
                parent_chunk_id=None,
                heading_path=[],
                section_tag=None,
                char_start=start,
                char_end=end,
                chunk_hash=f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}",
                excerpt=" ".join(text.split())[:240],
                text=text,
            )
            chunks.append(chunk)
            by_chunk_id[chunk_id] = {
                "source_id": source_id,
                "passage_id": passage["passage_id"],
                "start_offset": start,
                "end_offset": end,
                "offset_unit": passage["offset_unit"],
                "text": text,
            }
    return chunks, by_chunk_id


def scope_record(subset: dict[str, Any]) -> dict[str, Any]:
    source_ids = sorted(subset["source_ids"])
    digest = sha256_bytes(canonical_json_bytes(source_ids))
    return {
        "subset_id": subset["subset_id"],
        "source_count": len(source_ids),
        "source_ids_sha256": digest,
    }


def run_case(
    runtime_root: Path,
    case: dict[str, Any],
    subsets: dict[str, dict[str, Any]],
    *,
    reverse_source_order: bool,
) -> dict[str, Any]:
    runtime_config = case["runtime_config"]
    if runtime_config.get("retrieval_mode") != "ordinary":
        raise ValueError(
            f"{case['case_id']}: unsupported retrieval_mode "
            f"{runtime_config.get('retrieval_mode')!r}"
        )
    if runtime_config.get("include_permitted_metadata") is not True:
        raise ValueError(
            f"{case['case_id']}: expected include_permitted_metadata=true"
        )

    subset_id = case["accessible_subset_id"]
    subset = subsets[subset_id]
    k = int(runtime_config["maximum_passages"])
    chunks, by_chunk_id = passage_chunks(
        runtime_root,
        list(subset["source_ids"]),
        reverse_source_order=reverse_source_order,
    )
    retriever = BM25Retriever(chunks)
    hits = retriever.query(case["claim_text"], top_k=k, score_floor=0.0)

    normalized_hits: list[dict[str, Any]] = []
    for rank, hit in enumerate(hits, 1):
        row = by_chunk_id[hit.chunk.chunk_id]
        normalized_hits.append(
            {
                "source_id": row["source_id"],
                "passage_id": row["passage_id"],
                "anchor": {
                    "start_offset": row["start_offset"],
                    "end_offset": row["end_offset"],
                    "offset_unit": row["offset_unit"],
                    "transform_id": None,
                },
                "rank": rank,
                "score": float(hit.score),
                "text": row["text"],
            }
        )

    config_record = {
        "adapter_id": ADAPTER_ID,
        "sut_sha": SUT_SHA,
        "retrieval_method": "bm25",
        "query_construction": "case.claim_text verbatim",
        "score_floor": 0.0,
        "top_k": k,
        "index_unit": "frozen benchmark passage metadata; one flat production DocumentChunk per passage",
        "source_subset": subset_id,
        "source_order": "reverse" if reverse_source_order else "canonical",
        "completeness_mapping": "not_established because c818 retrieval nomination does not establish corpus completeness",
    }
    configuration_id = "sha256:" + sha256_bytes(canonical_json_bytes(config_record))
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case["case_id"],
        "hits": normalized_hits,
        "search_scope": {
            "actual_searchable_subset_id": subset_id,
            "observed_scope": scope_record(subset),
        },
        "completeness_claim": {
            "status": "not_established",
            "basis": (
                "Research adapter records the mechanically mounted named subset; "
                "c818 retrieval nomination does not itself establish corpus completeness."
            ),
        },
        "run_identity": {
            "retriever_id": f"evidence-bundler-bm25@{SUT_SHA}",
            "configuration_id": configuration_id,
            "run_id": f"{SUT_SHA}:{case['case_id']}:{ADAPTER_ID}",
            "adapter_id": ADAPTER_ID,
            "source_order": "reverse" if reverse_source_order else "canonical",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reverse-source-order", action="store_true")
    args = parser.parse_args()

    case_path = args.runtime_root / "cases" / f"{args.split}_cases.jsonl"
    subset_payload = load_json(args.runtime_root / "aperture" / "subsets.json")
    subsets = {row["subset_id"]: row for row in subset_payload["subsets"]}
    cases = load_jsonl(case_path)

    results = [
        run_case(
            args.runtime_root,
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
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
