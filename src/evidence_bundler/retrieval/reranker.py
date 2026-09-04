"""Parent-level cross-encoder reranking for retrieval nominees."""

from __future__ import annotations

from collections.abc import Sequence
from math import inf
from pathlib import Path
from typing import Any, Protocol, cast

from evidence_bundler.models.retrieval import CandidateEvidence


class RerankerError(Exception):
    """Raised when parent reranking cannot score candidate evidence."""


class RerankerDependencyError(RerankerError):
    """Raised when optional reranker dependencies are unavailable."""


class CrossEncoderModel(Protocol):
    """Minimal SentenceTransformers CrossEncoder-compatible boundary."""

    def predict(self, sentence_pairs: Sequence[tuple[str, str]], **kwargs: object) -> Any:
        """Score claim/parent-text sentence pairs."""


class ParentReranker:
    """Rerank already-aggregated parent candidates with a cross-encoder."""

    def __init__(self, model: CrossEncoderModel) -> None:
        self.model = model

    def rerank(
        self,
        claim_text: str,
        candidates: Sequence[CandidateEvidence],
    ) -> list[CandidateEvidence]:
        """Return candidates with rerank scores in deterministic rerank order."""
        if not candidates:
            return []

        pairs = [(claim_text, candidate.parent_chunk.text) for candidate in candidates]
        scores = _coerce_scores(
            self.model.predict(
                pairs,
                show_progress_bar=False,
            )
        )
        if len(scores) != len(candidates):
            raise RerankerError("Reranker returned an unexpected number of scores")

        scored_candidates = [
            candidate.model_copy(update={"rerank_score": score})
            for candidate, score in zip(candidates, scores, strict=True)
        ]
        return sorted(scored_candidates, key=_rerank_sort_key)


def load_reranker_model(
    model_name: str,
    cache_dir: Path | None = None,
    *,
    revision: str | None = None,
) -> CrossEncoderModel:
    """Load a SentenceTransformers CrossEncoder at an optional immutable revision."""
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:  # pragma: no cover - exercised only without optional dep.
        raise RerankerDependencyError(
            "sentence-transformers is required for real cross-encoder reranking"
        ) from exc

    kwargs: dict[str, object] = {}
    if cache_dir is not None:
        kwargs["cache_folder"] = str(cache_dir)
    if revision is not None:
        kwargs["revision"] = revision
    return cast(CrossEncoderModel, CrossEncoder(model_name, **kwargs))



def _coerce_scores(raw_scores: Any) -> list[float]:
    if hasattr(raw_scores, "tolist"):
        raw_scores = raw_scores.tolist()
    if isinstance(raw_scores, int | float):
        return [float(raw_scores)]
    if not isinstance(raw_scores, list):
        raise RerankerError("Reranker returned a non-list score payload")
    return [float(score) for score in raw_scores]


def _rerank_sort_key(candidate: CandidateEvidence) -> tuple[float, float, int, str]:
    return (
        _descending_score(candidate.rerank_score),
        _descending_score(candidate.fusion_score),
        candidate.parent_chunk.char_start,
        candidate.parent_chunk.chunk_id,
    )


def _descending_score(score: float | None) -> float:
    return inf if score is None else -score
