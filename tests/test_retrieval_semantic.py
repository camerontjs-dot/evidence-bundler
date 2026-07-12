"""Semantic retrieval component tests for Phase 2b Unit 2."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from evidence_bundler.contracts.hashing import hash_text
from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.retrieval._indexable import select_indexable_chunks
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
from evidence_bundler.retrieval.embedding_retriever import (
    SemanticIndex,
    SemanticIndexManifest,
    SemanticIndexManifestMismatch,
)

PREFIX = "Represent this sentence for searching relevant passages: "
MODEL = "fake-semantic-model"
CORPUS_HASH = hash_text("semantic-corpus")


class FakeEmbedder:
    """Deterministic fake embedding model for fast semantic tests."""

    def __init__(self) -> None:
        self.encoded_batches: list[list[str]] = []

    def encode(self, texts: Sequence[str], **_kwargs: object) -> list[list[float]]:
        batch = list(texts)
        self.encoded_batches.append(batch)
        return [_vector_for(text) for text in batch]


def test_semantic_index_uses_shared_child_leaf_selection() -> None:
    chunks = [
        _chunk(chunk_id="parent", text="Parent audit context.", start=0, end=21),
        _chunk(
            chunk_id="child",
            text="Submission checklist child detail.",
            start=1,
            end=33,
            parent_chunk_id="parent",
        ),
        _chunk(chunk_id="flat", text="Flat fallback text.", start=40, end=59),
    ]

    index = _build_index(chunks, FakeEmbedder())
    bm25 = BM25Retriever(chunks)

    assert [chunk.chunk_id for chunk in index.chunks] == [
        chunk.chunk_id for chunk in select_indexable_chunks(chunks)
    ]
    assert [chunk.chunk_id for chunk in index.chunks] == [
        chunk.chunk_id for chunk in bm25.indexed_chunks
    ]


def test_semantic_query_returns_ranked_hits_for_vocabulary_mismatch() -> None:
    chunks = [
        _chunk(
            chunk_id="target",
            text="The trial tracked myocardial infarction outcomes.",
            start=0,
            end=49,
        ),
        _chunk(
            chunk_id="other",
            text="The sponsor retained the submission checklist.",
            start=50,
            end=95,
        ),
    ]
    index = _build_index(chunks, FakeEmbedder())

    hits = index.query("heart attack outcomes", top_k=1)

    assert [hit.chunk.chunk_id for hit in hits] == ["target"]
    assert hits[0].rank == 1
    assert hits[0].chunk_index == 0
    assert hits[0].semantic_score > 0
    assert index.ranked_indices("heart attack outcomes", top_k=2) == [0, 1]
    assert index.ranked_chunk_ids("heart attack outcomes", top_k=2) == ["target", "other"]


def test_semantic_query_prefix_applies_to_queries_only() -> None:
    embedder = FakeEmbedder()
    index = _build_index(
        [
            _chunk(
                chunk_id="target",
                text="The trial tracked myocardial infarction.",
                start=0,
                end=40,
            )
        ],
        embedder,
    )

    index.query("heart attack", top_k=1)

    corpus_batch = embedder.encoded_batches[0]
    query_batch = embedder.encoded_batches[1]
    assert corpus_batch == ["The trial tracked myocardial infarction."]
    assert query_batch == [f"{PREFIX}heart attack"]


def test_semantic_empty_query_and_empty_corpus_return_no_hits() -> None:
    index = _build_index(
        [
            _chunk(
                chunk_id="target",
                text="The trial tracked myocardial infarction.",
                start=0,
                end=40,
            )
        ],
        FakeEmbedder(),
    )
    empty_index = _build_index([], FakeEmbedder())

    assert index.query("") == []
    assert index.ranked_indices("   ") == []
    assert empty_index.query("heart attack") == []


def test_semantic_index_persistence_validates_manifest(tmp_path: Path) -> None:
    pytest.importorskip("faiss")
    index_dir = tmp_path / "semantic_index"
    embedder = FakeEmbedder()
    index = _build_index(
        [
            _chunk(
                chunk_id="target",
                text="The trial tracked myocardial infarction.",
                start=0,
                end=40,
            )
        ],
        embedder,
    )

    index.save(index_dir)
    loaded = SemanticIndex.load(
        index_dir,
        embedder=FakeEmbedder(),
        corpus_hash=CORPUS_HASH,
        embedding_model=MODEL,
    )
    manifest = load_model_yaml(SemanticIndexManifest, index_dir / "manifest.yaml")

    assert (index_dir / "vectors.faiss").exists()
    assert (index_dir / "chunks.jsonl").exists()
    assert manifest.normalize_embeddings is True
    assert manifest.chunk_count == 1
    assert loaded.ranked_indices("heart attack", top_k=1) == [0]
    with pytest.raises(SemanticIndexManifestMismatch, match="corpus_hash"):
        SemanticIndex.load(
            index_dir,
            embedder=FakeEmbedder(),
            corpus_hash=hash_text("other-corpus"),
            embedding_model=MODEL,
        )


def test_semantic_index_load_rejects_vector_manifest_shape_mismatch(tmp_path: Path) -> None:
    pytest.importorskip("faiss")
    index_dir = tmp_path / "semantic_index"
    index = _build_index(
        [
            _chunk(
                chunk_id="target",
                text="The trial tracked myocardial infarction.",
                start=0,
                end=40,
            )
        ],
        FakeEmbedder(),
    )
    index.save(index_dir)
    manifest_path = index_dir / "manifest.yaml"
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest_path.write_text(manifest_text.replace("embedding_dim: 3", "embedding_dim: 4"))

    with pytest.raises(SemanticIndexManifestMismatch, match="embedding_dim"):
        SemanticIndex.load(
            index_dir,
            embedder=FakeEmbedder(),
            corpus_hash=CORPUS_HASH,
            embedding_model=MODEL,
        )


def _build_index(chunks: list[DocumentChunk], embedder: FakeEmbedder) -> SemanticIndex:
    return SemanticIndex.build(
        chunks,
        embedder=embedder,
        corpus_hash=CORPUS_HASH,
        embedding_model=MODEL,
        semantic_query_prefix=PREFIX,
    )


def _chunk(
    *,
    chunk_id: str,
    text: str,
    start: int,
    end: int,
    parent_chunk_id: str | None = None,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        source_id="src-test",
        source_path=Path("content.md"),
        title="Test",
        chunk_level="paragraph",
        parent_chunk_id=parent_chunk_id,
        heading_path=[],
        section_tag=None,
        char_start=start,
        char_end=end,
        chunk_hash=hash_text(text),
        excerpt=text,
        text=text,
    )


def _vector_for(text: str) -> list[float]:
    lowered = text.lower()
    if "myocardial infarction" in lowered or "heart attack" in lowered:
        return [1.0, 0.0, 0.0]
    if "submission checklist" in lowered:
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]
