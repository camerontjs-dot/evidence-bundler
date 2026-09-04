"""Semantic child/leaf retrieval with FAISS-compatible persistence."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from pydantic import Field

from evidence_bundler.contracts.hashing import hash_text
from evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml
from evidence_bundler.models.common import HashValue, NonBlankStr, StrictBaseModel
from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.retrieval._indexable import select_indexable_chunks

NORMALIZE_EMBEDDINGS: Literal[True] = True


class SemanticIndexError(Exception):
    """Raised when a semantic index cannot be built, saved, or queried."""


class SemanticIndexDependencyError(SemanticIndexError):
    """Raised when optional semantic retrieval dependencies are unavailable."""


class SemanticIndexManifestMismatch(SemanticIndexError):
    """Raised when a persisted index does not match the active corpus/config."""


class TextEmbedder(Protocol):
    """Minimal SentenceTransformer-compatible encoder boundary."""

    def encode(self, texts: Sequence[str], **kwargs: object) -> Any:
        """Encode one or more texts into dense vectors."""


class SemanticIndexManifest(StrictBaseModel):
    """Manifest for a persisted C-A-specific semantic index artifact."""

    corpus_hash: HashValue
    embedding_model: NonBlankStr
    embedding_model_revision: NonBlankStr | None = None
    chunk_set_hash: HashValue | None = None
    embedding_dim: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    normalize_embeddings: Literal[True] = NORMALIZE_EMBEDDINGS
    semantic_query_prefix: NonBlankStr | None = None
    built_at_utc: NonBlankStr


@dataclass(frozen=True)
class SemanticSearchHit:
    """A ranked child/leaf chunk returned by semantic retrieval."""

    chunk: DocumentChunk
    semantic_score: float
    rank: int
    chunk_index: int


class SemanticIndex:
    """FAISS-compatible semantic index over retrieval child/leaf chunks."""

    def __init__(
        self,
        *,
        chunks: list[DocumentChunk],
        embedder: TextEmbedder,
        manifest: SemanticIndexManifest,
        embeddings: list[list[float]] | None = None,
        faiss_index: object | None = None,
    ) -> None:
        self.chunks = list(chunks)
        self.embedder = embedder
        self.manifest = manifest
        self.embeddings = embeddings or []
        self._faiss_index = faiss_index

    @classmethod
    def build(
        cls,
        chunks: list[DocumentChunk],
        *,
        embedder: TextEmbedder,
        corpus_hash: str,
        embedding_model: str,
        embedding_model_revision: str | None = None,
        semantic_query_prefix: str | None,
        show_progress_bar: bool = False,
    ) -> SemanticIndex:
        """Build an in-memory semantic index over the shared child/leaf chunk set."""
        indexed_chunks = select_indexable_chunks(chunks)
        embeddings = _encode_texts(
            embedder,
            [chunk.text for chunk in indexed_chunks],
            show_progress_bar=show_progress_bar,
        )
        embedding_dim = len(embeddings[0]) if embeddings else 0
        manifest = SemanticIndexManifest(
            corpus_hash=corpus_hash,
            embedding_model=embedding_model,
            embedding_model_revision=embedding_model_revision,
            chunk_set_hash=compute_semantic_chunk_set_hash(indexed_chunks),
            embedding_dim=embedding_dim,
            chunk_count=len(indexed_chunks),
            normalize_embeddings=NORMALIZE_EMBEDDINGS,
            semantic_query_prefix=semantic_query_prefix,
            built_at_utc=_utc_now(),
        )
        return cls(
            chunks=indexed_chunks,
            embedder=embedder,
            manifest=manifest,
            embeddings=embeddings,
            faiss_index=_build_faiss_index(embeddings),
        )

    @classmethod
    def load(
        cls,
        index_dir: Path,
        *,
        embedder: TextEmbedder,
        corpus_hash: str,
        embedding_model: str,
        embedding_model_revision: str | None = None,
        chunk_set_hash: str | None = None,
        semantic_query_prefix: str | None = None,
    ) -> SemanticIndex:
        """Load a persisted semantic index if its manifest matches active inputs."""
        manifest = load_model_yaml(SemanticIndexManifest, index_dir / "manifest.yaml")
        _validate_manifest(
            manifest,
            corpus_hash=corpus_hash,
            embedding_model=embedding_model,
            embedding_model_revision=embedding_model_revision,
            chunk_set_hash=chunk_set_hash,
        )
        chunks = _read_chunks_jsonl(index_dir / "chunks.jsonl")
        if manifest.chunk_count != len(chunks):
            raise SemanticIndexManifestMismatch(
                "semantic index chunk_count does not match chunks.jsonl"
            )
        faiss_index = _read_faiss_index(index_dir / "vectors.faiss")
        _validate_faiss_index_shape(faiss_index, manifest)
        if semantic_query_prefix is not None:
            manifest = manifest.model_copy(
                update={"semantic_query_prefix": semantic_query_prefix}
            )
        return cls(
            chunks=chunks,
            embedder=embedder,
            manifest=manifest,
            faiss_index=faiss_index,
        )

    def save(self, index_dir: Path) -> None:
        """Persist the index as vectors.faiss, chunks.jsonl, and manifest.yaml."""
        faiss_index = self._faiss_index or _build_required_faiss_index(self.embeddings)
        index_dir.mkdir(parents=True, exist_ok=True)
        _write_chunks_jsonl(self.chunks, index_dir / "chunks.jsonl")
        write_model_yaml(self.manifest, index_dir / "manifest.yaml")
        _write_faiss_index(faiss_index, index_dir / "vectors.faiss")

    def query(self, query_text: str, *, top_k: int = 20) -> list[SemanticSearchHit]:
        """Return ranked child/leaf hits sorted by descending semantic score."""
        ranked = self._rank_query(query_text, top_k=top_k)
        return [
            SemanticSearchHit(
                chunk=self.chunks[chunk_index],
                semantic_score=score,
                rank=rank,
                chunk_index=chunk_index,
            )
            for rank, (chunk_index, score) in enumerate(ranked, start=1)
        ]

    def ranked_indices(self, query_text: str, *, top_k: int = 20) -> list[int]:
        """Return RRF-ready row indices, most relevant first."""
        return [chunk_index for chunk_index, _score in self._rank_query(query_text, top_k=top_k)]

    def ranked_chunk_ids(self, query_text: str, *, top_k: int = 20) -> list[str]:
        """Return RRF-ready chunk ids, most relevant first."""
        return [hit.chunk.chunk_id for hit in self.query(query_text, top_k=top_k)]

    def _rank_query(self, query_text: str, *, top_k: int) -> list[tuple[int, float]]:
        if top_k <= 0 or not query_text.strip() or not self.chunks:
            return []
        query_vector = _encode_query(
            self.embedder,
            query_text,
            semantic_query_prefix=self.manifest.semantic_query_prefix,
        )
        if self._faiss_index is not None:
            ranked = _search_faiss(
                self._faiss_index,
                query_vector,
                top_k=min(top_k, len(self.chunks)),
            )
        else:
            ranked = _search_embeddings(self.embeddings, query_vector)
        return _sort_ranked_pairs(ranked, self.chunks)[:top_k]


def load_embedding_model(
    model_name: str,
    cache_dir: Path | None = None,
    *,
    revision: str | None = None,
) -> TextEmbedder:
    """Load a SentenceTransformer model with optional cache and immutable revision."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - exercised only without optional dep.
        raise SemanticIndexDependencyError(
            "sentence-transformers is required for real semantic retrieval"
        ) from exc

    kwargs: dict[str, object] = {}
    if cache_dir is not None:
        kwargs["cache_folder"] = str(cache_dir)
    if revision is not None:
        kwargs["revision"] = revision
    return cast(TextEmbedder, SentenceTransformer(model_name, **kwargs))



def _encode_texts(
    embedder: TextEmbedder,
    texts: list[str],
    *,
    show_progress_bar: bool,
) -> list[list[float]]:
    if not texts:
        return []
    return _to_vector_list(
        embedder.encode(
            texts,
            normalize_embeddings=NORMALIZE_EMBEDDINGS,
            show_progress_bar=show_progress_bar,
        )
    )


def _encode_query(
    embedder: TextEmbedder,
    query_text: str,
    *,
    semantic_query_prefix: str | None,
) -> list[float]:
    if semantic_query_prefix:
        separator = "" if semantic_query_prefix.endswith(" ") else " "
        prefixed = f"{semantic_query_prefix}{separator}{query_text}"
    else:
        prefixed = query_text
    vectors = _to_vector_list(
        embedder.encode([prefixed], normalize_embeddings=NORMALIZE_EMBEDDINGS)
    )
    if len(vectors) != 1:
        raise SemanticIndexError("Embedder returned an unexpected query vector shape")
    return vectors[0]


def _to_vector_list(encoded: Any) -> list[list[float]]:
    if hasattr(encoded, "tolist"):
        encoded = encoded.tolist()
    if not isinstance(encoded, list):
        raise SemanticIndexError("Embedder returned a non-list vector payload")
    if encoded and all(isinstance(value, int | float) for value in encoded):
        encoded = [encoded]
    vectors: list[list[float]] = []
    for vector in encoded:
        if not isinstance(vector, list):
            raise SemanticIndexError("Embedder returned an invalid vector")
        vectors.append([float(value) for value in vector])
    return vectors


def _search_embeddings(
    embeddings: list[list[float]],
    query_vector: list[float],
) -> list[tuple[int, float]]:
    if not embeddings:
        return []
    return [
        (index, _dot_product(embedding, query_vector))
        for index, embedding in enumerate(embeddings)
    ]


def _dot_product(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise SemanticIndexError("Embedding dimension mismatch")
    return sum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=True)
    )


def _sort_ranked_pairs(
    ranked: list[tuple[int, float]],
    chunks: list[DocumentChunk],
) -> list[tuple[int, float]]:
    return sorted(
        ranked,
        key=lambda item: (
            -item[1],
            chunks[item[0]].char_start,
            chunks[item[0]].chunk_id,
        ),
    )


def _build_faiss_index(embeddings: list[list[float]]) -> object | None:
    if not embeddings:
        return None
    try:
        return _build_required_faiss_index(embeddings)
    except SemanticIndexDependencyError:
        return None


def _build_required_faiss_index(embeddings: list[list[float]]) -> object:
    if not embeddings:
        raise SemanticIndexError("Cannot persist an empty semantic index")
    try:
        import faiss
    except ImportError as exc:  # pragma: no cover - depends on optional dep presence.
        raise SemanticIndexDependencyError(
            "faiss-cpu is required to persist semantic indexes"
        ) from exc

    array = _as_float32_array(embeddings)
    index = faiss.IndexFlatIP(array.shape[1])
    index.add(array)
    return cast(object, index)



def _write_faiss_index(index: Any, path: Path) -> None:
    try:
        import faiss
    except ImportError as exc:  # pragma: no cover - depends on optional dep presence.
        raise SemanticIndexDependencyError(
            "faiss-cpu is required to persist semantic indexes"
        ) from exc

    faiss.write_index(index, str(path))


def _read_faiss_index(path: Path) -> Any:
    try:
        import faiss
    except ImportError as exc:  # pragma: no cover - depends on optional dep presence.
        raise SemanticIndexDependencyError(
            "faiss-cpu is required to load semantic indexes"
        ) from exc

    return faiss.read_index(str(path))


def _search_faiss(
    index: Any,
    query_vector: list[float],
    *,
    top_k: int,
) -> list[tuple[int, float]]:
    if top_k <= 0:
        return []
    scores, indices = index.search(_as_float32_array([query_vector]), top_k)
    return [
        (int(chunk_index), float(scores[0][rank]))
        for rank, chunk_index in enumerate(indices[0])
        if int(chunk_index) >= 0
    ]


def _as_float32_array(vectors: list[list[float]]) -> Any:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - numpy arrives with FAISS/ST deps.
        raise SemanticIndexDependencyError(
            "numpy is required for semantic vector operations"
        ) from exc

    return np.asarray(vectors, dtype=np.float32)


def _write_chunks_jsonl(chunks: list[DocumentChunk], path: Path) -> None:
    lines = [
        json.dumps(
            {
                "row_index": index,
                "chunk": chunk.model_dump(mode="json"),
            },
            sort_keys=True,
        )
        for index, chunk in enumerate(chunks)
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _read_chunks_jsonl(path: Path) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for expected_index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("row_index") != expected_index:
            raise SemanticIndexManifestMismatch("chunks.jsonl row_index sequence is invalid")
        chunks.append(DocumentChunk.model_validate(row["chunk"]))
    return chunks


def _validate_manifest(
    manifest: SemanticIndexManifest,
    *,
    corpus_hash: str,
    embedding_model: str,
    embedding_model_revision: str | None = None,
    chunk_set_hash: str | None = None,
) -> None:
    mismatches = []
    if manifest.corpus_hash != corpus_hash:
        mismatches.append("corpus_hash")
    if manifest.embedding_model != embedding_model:
        mismatches.append("embedding_model")
    if manifest.embedding_model_revision != embedding_model_revision:
        mismatches.append("embedding_model_revision")
    if chunk_set_hash is not None and manifest.chunk_set_hash != chunk_set_hash:
        mismatches.append("chunk_set_hash")
    if manifest.normalize_embeddings is not NORMALIZE_EMBEDDINGS:
        mismatches.append("normalize_embeddings")
    if mismatches:
        raise SemanticIndexManifestMismatch(
            "semantic index manifest mismatch: " + ", ".join(mismatches)
        )


def compute_semantic_chunk_set_hash(chunks: list[DocumentChunk]) -> str:
    """Hash the ordered semantic-index rows so cached indexes cannot alias chunk geometry."""
    indexed_chunks = select_indexable_chunks(chunks)
    rows = [
        {
            "chunk_id": chunk.chunk_id,
            "chunk_hash": chunk.chunk_hash,
            "source_id": chunk.source_id,
            "parent_chunk_id": chunk.parent_chunk_id,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
        }
        for chunk in indexed_chunks
    ]
    return hash_text(json.dumps(rows, sort_keys=True, separators=(",", ":")))


def _validate_faiss_index_shape(index: object, manifest: SemanticIndexManifest) -> None:
    mismatches = []
    if getattr(index, "d", None) != manifest.embedding_dim:
        mismatches.append("embedding_dim")
    if getattr(index, "ntotal", None) != manifest.chunk_count:
        mismatches.append("chunk_count")
    if mismatches:
        raise SemanticIndexManifestMismatch(
            "semantic index vectors.faiss mismatch: " + ", ".join(mismatches)
        )


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
