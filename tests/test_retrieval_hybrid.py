"""Hybrid retrieval fusion tests for Phase 2b Unit 3."""

from __future__ import annotations

import pytest

from evidence_bundler.retrieval.hybrid import reciprocal_rank_fusion


def test_rrf_overlap_boosts_shared_child_hits() -> None:
    fused = reciprocal_rank_fusion(
        [
            ["lexical-only", "shared", "tail"],
            ["shared", "semantic-only"],
        ],
        k=60,
    )

    assert [hit.chunk_id for hit in fused] == [
        "shared",
        "lexical-only",
        "semantic-only",
        "tail",
    ]
    assert fused[0].lexical_rank == 2
    assert fused[0].semantic_rank == 1
    assert fused[0].fusion_score > fused[1].fusion_score


def test_rrf_preserves_lexical_only_and_semantic_only_hits() -> None:
    fused = reciprocal_rank_fusion([["lex"], ["sem"]], k=60)

    by_id = {hit.chunk_id: hit for hit in fused}
    assert set(by_id) == {"lex", "sem"}
    assert by_id["lex"].lexical_rank == 1
    assert by_id["lex"].semantic_rank is None
    assert by_id["sem"].lexical_rank is None
    assert by_id["sem"].semantic_rank == 1


def test_rrf_empty_rankings_return_no_hits() -> None:
    assert reciprocal_rank_fusion([], k=60) == []
    assert reciprocal_rank_fusion([[], []], k=60) == []


def test_rrf_ties_break_by_lexical_rank_then_chunk_id() -> None:
    fused = reciprocal_rank_fusion([["b", "a"], ["a", "b"]], k=60)

    assert [hit.chunk_id for hit in fused] == ["b", "a"]
    assert fused[0].fusion_score == pytest.approx(fused[1].fusion_score)


def test_rrf_repeated_calls_are_deterministic() -> None:
    rankings = [["b", "a", "c", "a"], ["c", "b", "d"]]

    first = reciprocal_rank_fusion(rankings, k=60)
    second = reciprocal_rank_fusion(rankings, k=60)

    assert first == second


def test_rrf_rejects_non_positive_k() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        reciprocal_rank_fusion([["chunk"]], k=0)
