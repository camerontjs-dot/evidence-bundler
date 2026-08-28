#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from importlib.metadata import version
from pathlib import Path
from typing import Any

from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever

PRODUCTION_SOURCE_SHA = "c8189c31adbab11729c31430c2070126224a2d42"
EXPECTED_BLOBS = {
    "src/evidence_bundler/retrieval/bm25_retriever.py": "f8d7dd7e56710453edbca7c51aeea6da949ff903",
    "src/evidence_bundler/retrieval/_indexable.py": "c7da32bd54e6948ab992a1374d0e524947418b60",
    "src/evidence_bundler/retrieval/hits.py": "032f319d982236e613b766a88b29119b9e49a4be",
    "src/evidence_bundler/models/document.py": "29751aa7420d4b22f44b9548be36e6a038ca4a57",
}
EXPECTED_RANK_BM25_VERSION = "0.2.2"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def verify_production_identity(repo_root: Path) -> dict[str, Any]:
    observed: dict[str, str] = {}
    mismatches: dict[str, dict[str, str]] = {}
    for rel, expected in EXPECTED_BLOBS.items():
        data = (repo_root / rel).read_bytes()
        actual = git_blob_sha(data)
        observed[rel] = actual
        if actual != expected:
            mismatches[rel] = {"expected": expected, "actual": actual}
    rank_version = version("rank-bm25")
    if rank_version != EXPECTED_RANK_BM25_VERSION:
        mismatches["rank-bm25"] = {"expected": EXPECTED_RANK_BM25_VERSION, "actual": rank_version}
    if mismatches:
        raise RuntimeError(f"production BM25 identity mismatch: {mismatches}")
    return {
        "production_source_sha": PRODUCTION_SOURCE_SHA,
        "blobs": observed,
        "rank_bm25_version": rank_version,
        "identity_verified": True,
    }


def _chunk(p: dict[str, Any]) -> DocumentChunk:
    digest = hashlib.sha256(p["text"].encode("utf-8")).hexdigest()
    return DocumentChunk(
        chunk_id=p["passage_id"],
        source_id=p["source_id"],
        source_path=Path(p["source_path"]),
        title=None,
        chunk_level="paragraph",
        parent_chunk_id=None,
        heading_path=[],
        section_tag=None,
        char_start=int(p["char_start"]),
        char_end=int(p["char_end"]),
        chunk_hash=f"sha256:{digest}",
        excerpt=p["text"][:240],
        text=p["text"],
    )


def run_bm25(case: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks = [_chunk(p) for p in candidates]
    retriever = BM25Retriever(chunks)
    hits = retriever.query(case["claim_text"], top_k=int(case["runtime_config"]["maximum_passages"]), score_floor=0.0)
    by_id = {p["passage_id"]: p for p in candidates}
    out: list[dict[str, Any]] = []
    for hit in hits:
        p = by_id[hit.chunk.chunk_id]
        out.append({
            "rank": hit.rank,
            "source_id": p["source_id"],
            "passage_id": p["passage_id"],
            "score": float(hit.score),
            "text": p["text"],
        })
    return out
