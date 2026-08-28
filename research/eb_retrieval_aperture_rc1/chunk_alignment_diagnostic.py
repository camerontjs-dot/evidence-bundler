from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from evidence_bundler.ingest.chunker import chunk_source_documents
from evidence_bundler.models.document import SourceDocument


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    documents: list[SourceDocument] = []
    passage_hashes: set[tuple[str, str]] = set()
    passage_count = 0
    for source_dir in sorted(
        path for path in (args.runtime_root / "sources").iterdir() if path.is_dir()
    ):
        metadata = load_json(source_dir / "metadata.json")
        content_path = source_dir / "content.txt"
        content_bytes = content_path.read_bytes()
        content_text = content_bytes.decode("utf-8")
        if hashlib.sha256(content_bytes).hexdigest() != metadata["content_hash"]:
            raise ValueError(f"content hash mismatch: {metadata['source_id']}")
        for passage in metadata["passages"]:
            passage_count += 1
            passage_hashes.add((metadata["source_id"], passage["text_sha256"]))
        documents.append(
            SourceDocument(
                source_id=metadata["source_id"],
                content_path=content_path,
                content_type="text",
                raw_text=content_text,
                content_hash=f"sha256:{metadata['content_hash']}",
                metadata=metadata,
                passages={"benchmark_passages": metadata["passages"]},
                title=metadata.get("title"),
            )
        )

    chunks = chunk_source_documents(documents)
    exact_text_matches = 0
    for chunk in chunks:
        digest = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
        if (chunk.source_id, digest) in passage_hashes:
            exact_text_matches += 1

    record = {
        "schema_version": "1.0",
        "diagnostic": "production-c818-chunker-vs-frozen-passage-units",
        "source_count": len(documents),
        "frozen_passage_count": passage_count,
        "production_chunk_count": len(chunks),
        "production_chunks_exactly_equal_to_one_frozen_passage": exact_text_matches,
        "production_chunks_not_exactly_equal_to_one_frozen_passage": (
            len(chunks) - exact_text_matches
        ),
        "interpretation_boundary": (
            "This diagnostic is apparatus/extraction evidence only. The decisive "
            "retrieval run uses frozen permitted passage units so the exact-identity "
            "evaluator does not silently award overlap credit to coalesced chunks."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(record))
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
