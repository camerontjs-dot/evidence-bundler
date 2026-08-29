"""Mutation tests for the RC0 retrieval experiment control surface."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from pydantic import ValidationError

from evidence_bundler.contracts.hashing import hash_text
from evidence_bundler.contracts.writer import _retrieval_config_hash, build_retrieval_bundle
from evidence_bundler.ingest.chunker import chunk_source_document
from evidence_bundler.models.document import ChunkSpec, SourceDocument
from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
from evidence_bundler.retrieval.embedding_retriever import (
    SemanticIndexManifest,
    SemanticIndexManifestMismatch,
    _validate_manifest,
    compute_semantic_chunk_set_hash,
    load_embedding_model,
)
from evidence_bundler.retrieval.reranker import load_reranker_model

EMBED_REV_A = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
EMBED_REV_B = "1111111111111111111111111111111111111111"
RERANK_REV = "233902d25c440f23af6f7d6e94d2946bac0bee0a"


class FakeEmbedder:
    def encode(self, texts: list[str], **_kwargs: object) -> list[list[float]]:
        return [_vector_for(text) for text in texts]


def _vector_for(text: str) -> list[float]:
    lowered = text.lower()
    return [
        float("submission" in lowered or "review" in lowered),
        float("plain" in lowered or "text" in lowered),
        float("pdf" in lowered or "extraction" in lowered),
        0.25,
    ]


def test_model_revision_mutation_changes_identity() -> None:
    base = RetrievalConfig(
        retrieval_method="semantic",
        embedding_model_revision=EMBED_REV_A,
        require_immutable_model_revisions=True,
    )
    mutated = base.model_copy(update={"embedding_model_revision": EMBED_REV_B})

    assert _retrieval_config_hash(base) != _retrieval_config_hash(mutated)


def test_immutable_execution_fails_closed_without_full_commit_revisions() -> None:
    with pytest.raises(ValidationError, match="requires embedding_model_revision"):
        RetrievalConfig(
            retrieval_method="semantic",
            require_immutable_model_revisions=True,
        )
    with pytest.raises(ValidationError, match="full 40-hex commit SHA"):
        RetrievalConfig(
            retrieval_method="semantic",
            embedding_model_revision="main",
        )
    with pytest.raises(ValidationError, match="requires rerank_model_revision"):
        RetrievalConfig(
            retrieval_method="hybrid",
            embedding_model_revision=EMBED_REV_A,
            rerank_enabled=True,
            require_immutable_model_revisions=True,
        )


def test_embedding_loader_passes_declared_revision(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_sentence_transformer(model_name: str, **kwargs: object) -> object:
        calls.append((model_name, dict(kwargs)))
        return object()

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        types.SimpleNamespace(SentenceTransformer=fake_sentence_transformer),
    )

    load_embedding_model("model-a", Path("cache-a"), revision=EMBED_REV_A)

    assert calls == [
        ("model-a", {"cache_folder": "cache-a", "revision": EMBED_REV_A})
    ]


def test_reranker_loader_passes_declared_revision(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_cross_encoder(model_name: str, **kwargs: object) -> object:
        calls.append((model_name, dict(kwargs)))
        return object()

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        types.SimpleNamespace(CrossEncoder=fake_cross_encoder),
    )

    load_reranker_model("reranker-a", revision=RERANK_REV)

    assert calls == [("reranker-a", {"revision": RERANK_REV})]


def test_semantic_manifest_rejects_revision_and_chunk_set_aliasing() -> None:
    manifest = SemanticIndexManifest(
        corpus_hash=hash_text("corpus"),
        embedding_model="model-a",
        embedding_model_revision=EMBED_REV_A,
        chunk_set_hash=hash_text("chunks-a"),
        embedding_dim=4,
        chunk_count=2,
        semantic_query_prefix=None,
        built_at_utc="2026-08-29T00:00:00Z",
    )

    with pytest.raises(SemanticIndexManifestMismatch, match="embedding_model_revision"):
        _validate_manifest(
            manifest,
            corpus_hash=manifest.corpus_hash,
            embedding_model="model-a",
            embedding_model_revision=EMBED_REV_B,
            chunk_set_hash=manifest.chunk_set_hash,
        )
    with pytest.raises(SemanticIndexManifestMismatch, match="chunk_set_hash"):
        _validate_manifest(
            manifest,
            corpus_hash=manifest.corpus_hash,
            embedding_model="model-a",
            embedding_model_revision=EMBED_REV_A,
            chunk_set_hash=hash_text("chunks-b"),
        )


def test_chunk_geometry_mutation_changes_identity_and_chunk_set() -> None:
    text = " ".join(f"token-{index:03d}" for index in range(180))
    document = SourceDocument(
        source_id="src-geometry",
        content_path=Path("content.txt"),
        content_type="text",
        raw_text=text,
        content_hash=hash_text(text),
        metadata={},
        passages={},
    )
    default_config = RetrievalConfig()
    mutated_config = RetrievalConfig(chunk_max_chars=240, chunk_overlap_chars=40)
    default_chunks = chunk_source_document(
        document,
        ChunkSpec(
            max_chars=default_config.chunk_max_chars,
            overlap_chars=default_config.chunk_overlap_chars,
        ),
    )
    mutated_chunks = chunk_source_document(
        document,
        ChunkSpec(
            max_chars=mutated_config.chunk_max_chars,
            overlap_chars=mutated_config.chunk_overlap_chars,
        ),
    )

    assert _retrieval_config_hash(default_config) != _retrieval_config_hash(mutated_config)
    assert [chunk.chunk_id for chunk in default_chunks] != [
        chunk.chunk_id for chunk in mutated_chunks
    ]
    assert compute_semantic_chunk_set_hash(default_chunks) != compute_semantic_chunk_set_hash(
        mutated_chunks
    )


def test_semantic_budget_mutation_changes_pre_fusion_candidates_without_lexical_change(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    small = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        tmp_path / "hybrid-small-semantic-budget",
        config=RetrievalConfig(
            retrieval_method="hybrid",
            top_k=10,
            rrf_candidate_pool=4,
            semantic_child_top_k=1,
            lexical_score_floor=999.0,
            embedding_model="fake-semantic",
        ),
    )
    large = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        tmp_path / "hybrid-large-semantic-budget",
        config=RetrievalConfig(
            retrieval_method="hybrid",
            top_k=10,
            rrf_candidate_pool=4,
            semantic_child_top_k=4,
            lexical_score_floor=999.0,
            embedding_model="fake-semantic",
        ),
    )

    assert small.retrieval_report is not None
    assert large.retrieval_report is not None
    assert small.retrieval_report.retrieval_config.rrf_candidate_pool == 4
    assert large.retrieval_report.retrieval_config.rrf_candidate_pool == 4
    small_summary = small.retrieval_report.claim_summaries[0]
    large_summary = large.retrieval_report.claim_summaries[0]
    assert small_summary.total_fused_child_hits == 1
    assert large_summary.total_fused_child_hits == 4
    assert small_summary.semantic_only_child_hits == 1
    assert large_summary.semantic_only_child_hits == 4


def test_lexical_budget_mutation_changes_pre_fusion_bm25_budget_without_semantic_change(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    observed_top_k: list[int] = []
    original_query = BM25Retriever.query

    def spy_query(
        self: BM25Retriever,
        query_text: str,
        *,
        top_k: int = 20,
        score_floor: float = 0.0,
    ) -> list[object]:
        observed_top_k.append(top_k)
        return original_query(self, query_text, top_k=top_k, score_floor=score_floor)

    monkeypatch.setattr(BM25Retriever, "query", spy_query)
    for lexical_budget in (1, 4):
        build_retrieval_bundle(
            mixed_scaffold_run_tmp,
            tmp_path / f"hybrid-lexical-{lexical_budget}",
            config=RetrievalConfig(
                retrieval_method="hybrid",
                top_k=10,
                rrf_candidate_pool=lexical_budget,
                semantic_child_top_k=3,
                embedding_model="fake-semantic",
            ),
        )

    claim_count = len(observed_top_k) // 2
    assert claim_count > 0
    assert observed_top_k[:claim_count] == [1] * claim_count
    assert observed_top_k[claim_count:] == [4] * claim_count


def test_default_control_surface_preserves_live_pre_rc0_machinery_defaults() -> None:
    config = RetrievalConfig()
    chunk_spec = ChunkSpec()

    assert config.retrieval_method == "bm25"
    assert config.chunk_max_chars == chunk_spec.max_chars == 1800
    assert config.chunk_overlap_chars == chunk_spec.overlap_chars == 80
    assert config.embedding_model_revision is None
    assert config.rerank_model_revision is None
    assert config.require_immutable_model_revisions is False
    assert config.rrf_candidate_pool == 50
    assert config.semantic_child_top_k == 50
