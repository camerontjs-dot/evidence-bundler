"""Parent-level reranker tests."""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

import pytest

from evidence_bundler.contracts.hashing import hash_text
from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.models.retrieval import CandidateEvidence
from evidence_bundler.retrieval.reranker import ParentReranker, RerankerError, load_reranker_model


def test_parent_reranker_orders_by_cross_encoder_score() -> None:
    model = FakeCrossEncoder({"Parent A": -2.0, "Parent B": -1.0})
    reranker = ParentReranker(model)

    reranked = reranker.rerank(
        "claim text",
        [make_candidate("parent-a", "Parent A"), make_candidate("parent-b", "Parent B")],
    )

    assert [candidate.parent_chunk.chunk_id for candidate in reranked] == [
        "parent-b",
        "parent-a",
    ]
    assert [candidate.rerank_score for candidate in reranked] == [-1.0, -2.0]
    assert model.pairs == [("claim text", "Parent A"), ("claim text", "Parent B")]


def test_parent_reranker_ties_by_fusion_score_then_position_then_chunk_id() -> None:
    candidates = [
        make_candidate("parent-c", "Parent C", char_start=20, fusion_score=0.5),
        make_candidate("parent-a", "Parent A", char_start=10, fusion_score=0.5),
        make_candidate("parent-b", "Parent B", char_start=0, fusion_score=0.7),
    ]
    model = FakeCrossEncoder(
        {
            "Parent A": 1.0,
            "Parent B": 1.0,
            "Parent C": 1.0,
        }
    )

    reranked = ParentReranker(model).rerank("claim text", candidates)

    assert [candidate.parent_chunk.chunk_id for candidate in reranked] == [
        "parent-b",
        "parent-a",
        "parent-c",
    ]


def test_parent_reranker_returns_empty_candidates_without_model_call() -> None:
    model = FakeCrossEncoder({})

    assert ParentReranker(model).rerank("claim text", []) == []
    assert model.pairs == []


def test_parent_reranker_rejects_unexpected_score_count() -> None:
    model = ShortScoreCrossEncoder()

    with pytest.raises(RerankerError, match="unexpected number"):
        ParentReranker(model).rerank(
            "claim text",
            [make_candidate("parent-a", "Parent A"), make_candidate("parent-b", "Parent B")],
        )


@pytest.mark.skipif(
    os.environ.get("EVIDENCE_BUNDLER_RUN_RERANKER_SMOKE") != "1",
    reason="set EVIDENCE_BUNDLER_RUN_RERANKER_SMOKE=1 to run real reranker smoke",
)
def test_real_cross_encoder_reranker_smoke() -> None:
    reranker = ParentReranker(load_reranker_model("cross-encoder/ms-marco-MiniLM-L-6-v2"))

    reranked = reranker.rerank(
        "The sponsor should retain the submission checklist.",
        [
            make_candidate("checklist", "The sponsor retained the submission checklist."),
            make_candidate("unrelated", "The PDF extraction path preserved source text."),
        ],
    )

    assert len(reranked) == 2
    assert all(candidate.rerank_score is not None for candidate in reranked)


class FakeCrossEncoder:
    """Deterministic fake cross-encoder keyed by parent text."""

    def __init__(self, scores_by_parent_text: dict[str, float]) -> None:
        self.scores_by_parent_text = scores_by_parent_text
        self.pairs: list[tuple[str, str]] = []

    def predict(self, sentence_pairs: Sequence[tuple[str, str]], **_kwargs: object) -> list[float]:
        self.pairs = list(sentence_pairs)
        return [self.scores_by_parent_text[parent_text] for _claim, parent_text in self.pairs]


class ShortScoreCrossEncoder:
    def predict(self, sentence_pairs: Sequence[tuple[str, str]], **_kwargs: object) -> list[float]:
        return [0.0 for _pair in list(sentence_pairs)[:-1]]


def make_candidate(
    chunk_id: str,
    text: str,
    *,
    char_start: int = 0,
    fusion_score: float = 0.1,
    rerank_score: float | None = None,
) -> CandidateEvidence:
    parent = make_chunk(chunk_id, text, char_start=char_start)
    child = make_chunk(
        f"{chunk_id}-child",
        text,
        char_start=char_start,
        parent_chunk_id=chunk_id,
    )
    return CandidateEvidence(
        claim_id="clm-test",
        claim_text="claim text",
        parent_chunk=parent,
        matched_child_chunk=child,
        child_rank=1,
        fusion_score=fusion_score,
        rerank_score=rerank_score,
        retrieval_method="hybrid",
        evidence_role="supporting",
    )


def make_chunk(
    chunk_id: str,
    text: str,
    *,
    char_start: int = 0,
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
        char_start=char_start,
        char_end=char_start + len(text),
        chunk_hash=hash_text(text),
        excerpt=text,
        text=text,
    )
