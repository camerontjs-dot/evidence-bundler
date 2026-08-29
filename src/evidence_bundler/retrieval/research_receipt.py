"""Machine-readable research-arm receipts for retrieval characterization apparatus.

This module is research infrastructure. It does not alter production retrieval defaults.
"""

from __future__ import annotations

import json
import os
import platform
import re
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from evidence_bundler.contracts.hashing import compute_bundle_tree_hash, hash_file, hash_text
from evidence_bundler.contracts.intake import verify_intake
from evidence_bundler.contracts.writer import BundleBuildResult, _retrieval_config_hash
from evidence_bundler.ingest.chunker import chunk_source_documents
from evidence_bundler.ingest.loader import load_source_documents
from evidence_bundler.models.document import ChunkSpec
from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.retrieval.embedding_retriever import compute_semantic_chunk_set_hash

FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
NON_IDENTITY_CONFIG_FIELDS = ("embedding_model_cache_dir", "semantic_index_path")
_CANONICAL_MODEL_IDS = {
    "cross-encoder/ms-marco-MiniLM-L-6-v2": "cross-encoder/ms-marco-MiniLM-L6-v2",
}


class ResearchArmReceiptError(ValueError):
    """Raised when a research-arm receipt cannot be constructed truthfully."""


def canonical_model_id(model_id: str) -> str:
    """Return the canonical model identifier used in research receipts."""
    return _CANONICAL_MODEL_IDS.get(model_id, model_id)


def normalized_identity_config(config: RetrievalConfig) -> dict[str, Any]:
    """Return the computation identity config with documented path-only fields excluded."""
    data = config.model_dump(mode="json")
    for field_name in NON_IDENTITY_CONFIG_FIELDS:
        data.pop(field_name, None)
    return data


def build_research_arm_receipt(
    *,
    scaffold_run_dir: Path,
    result: BundleBuildResult,
    config: RetrievalConfig,
    apparatus_commit_sha: str,
    apparatus_tree_sha: str,
    report_path: Path | None = None,
) -> dict[str, Any]:
    """Build a replay-oriented receipt for one explicit research retrieval arm."""
    for label, value in (
        ("apparatus_commit_sha", apparatus_commit_sha),
        ("apparatus_tree_sha", apparatus_tree_sha),
    ):
        if not FULL_SHA_RE.fullmatch(value):
            raise ResearchArmReceiptError(f"{label} must be a full 40-hex Git SHA")

    intake = verify_intake(scaffold_run_dir)
    if not intake.valid or intake.artifact is None:
        raise ResearchArmReceiptError("scaffold intake must be valid before receipt creation")
    artifact = intake.artifact

    documents = load_source_documents(artifact)
    chunks = chunk_source_documents(
        documents,
        ChunkSpec(
            max_chars=config.chunk_max_chars,
            overlap_chars=config.chunk_overlap_chars,
        ),
    )
    chunk_set_hash = compute_semantic_chunk_set_hash(chunks)
    config_hash = _retrieval_config_hash(config)
    identity_config = normalized_identity_config(config)

    model_identity = {
        "embedding_model": canonical_model_id(str(config.embedding_model)),
        "embedding_model_revision": (
            str(config.embedding_model_revision)
            if config.embedding_model_revision is not None
            else None
        ),
        "reranker_model": canonical_model_id(str(config.rerank_model)),
        "reranker_model_revision": (
            str(config.rerank_model_revision)
            if config.rerank_model_revision is not None
            else None
        ),
    }
    arm_identity_payload = {
        "apparatus_commit_sha": apparatus_commit_sha,
        "apparatus_tree_sha": apparatus_tree_sha,
        "source_run_id": str(artifact.manifest.run_id),
        "source_corpus_hash": str(artifact.manifest.corpus.corpus_hash),
        "retrieval_config_hash": config_hash,
        "identity_config": identity_config,
        "chunk_set_hash": chunk_set_hash,
        "model_identity": model_identity,
    }
    arm_identity = hash_text(
        json.dumps(arm_identity_payload, sort_keys=True, separators=(",", ":"))
    )

    bundle_hash = compute_bundle_tree_hash(result.bundle_dir)
    if bundle_hash != result.manifest.bundle.bundle_hash:
        raise ResearchArmReceiptError("bundle hash does not match sealed manifest")

    report_hash = None
    if report_path is not None:
        if not report_path.exists():
            raise ResearchArmReceiptError(f"report path does not exist: {report_path}")
        report_hash = hash_file(report_path)

    return {
        "schema": "evidence-bundler-research-arm-receipt-v1",
        "scope": "research infrastructure; no retrieval-quality claim",
        "arm_identity": arm_identity,
        "apparatus": {
            "repository": "camerontjs-dot/evidence-bundler",
            "commit_sha": apparatus_commit_sha,
            "tree_sha": apparatus_tree_sha,
        },
        "source": {
            "run_id": str(artifact.manifest.run_id),
            "corpus_hash": str(artifact.manifest.corpus.corpus_hash),
        },
        "retrieval_config": config.model_dump(mode="json"),
        "identity_config": identity_config,
        "non_identity_config_fields": list(NON_IDENTITY_CONFIG_FIELDS),
        "retrieval_config_hash": config_hash,
        "chunking": {
            "chunk_max_chars": config.chunk_max_chars,
            "chunk_overlap_chars": config.chunk_overlap_chars,
            "ordered_chunk_set_hash": chunk_set_hash,
            "chunk_count": len(chunks),
        },
        "models": model_identity,
        "runtime": {
            "python": sys.version.split()[0],
            "packages": _runtime_package_versions(),
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            },
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "note": "device metadata only; this receipt is not a latency or cost measurement",
        },
        "outputs": {
            "bundle_hash": bundle_hash,
            "report_hash": report_hash,
        },
        "executed_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_research_arm_receipt(
    receipt: dict[str, Any],
    path: Path,
) -> tuple[Path, str]:
    """Write deterministic-key JSON plus a SHA-256 sidecar and return its hash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt_hash = hash_file(path)
    path.with_suffix(path.suffix + ".sha256").write_text(
        receipt_hash.removeprefix("sha256:") + "  " + path.name + "\n",
        encoding="utf-8",
    )
    return path, receipt_hash


def _runtime_package_versions() -> dict[str, str | None]:
    names = (
        "evidence-bundler",
        "sentence-transformers",
        "faiss-cpu",
        "rank-bm25",
        "pydantic",
    )
    result: dict[str, str | None] = {}
    for name in names:
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = None
    return result
