"""Retrieval config validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from evidence_bundler.contracts.hashing import hash_text
from evidence_bundler.contracts.writer import _retrieval_config_hash
from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.models.retrieval import CandidateEvidence, RetrievalConfig


def test_rerank_config_requires_hybrid_retrieval() -> None:
    with pytest.raises(ValidationError, match="rerank_enabled requires"):
        RetrievalConfig(retrieval_method="bm25", rerank_enabled=True)

    with pytest.raises(ValidationError, match="rerank_enabled requires"):
        RetrievalConfig(retrieval_method="semantic", rerank_enabled=True)


def test_rerank_config_accepts_hybrid_retrieval() -> None:
    config = RetrievalConfig(retrieval_method="hybrid", rerank_enabled=True)

    assert config.rerank_enabled is True


def test_contradiction_config_requires_hybrid_retrieval() -> None:
    with pytest.raises(ValidationError, match="contradiction_enabled requires"):
        RetrievalConfig(retrieval_method="bm25", contradiction_enabled=True)


def test_contradiction_rerank_requires_contradiction_enabled() -> None:
    with pytest.raises(ValidationError, match="contradiction_rerank_enabled requires"):
        RetrievalConfig(
            retrieval_method="hybrid",
            rerank_enabled=True,
            contradiction_rerank_enabled=True,
        )


def test_contradiction_rerank_requires_supporting_rerank_enabled() -> None:
    with pytest.raises(ValidationError, match="contradiction_rerank_enabled requires"):
        RetrievalConfig(
            retrieval_method="hybrid",
            contradiction_enabled=True,
            contradiction_rerank_enabled=True,
        )


def test_contradiction_config_fields_participate_in_config_hash() -> None:
    base = RetrievalConfig(retrieval_method="hybrid", contradiction_enabled=True)
    with_extra_prefix = base.model_copy(
        update={
            "contradiction_query_prefixes": [
                *base.contradiction_query_prefixes,
                "contraindicated in",
            ]
        }
    )
    gate_disabled = base.model_copy(update={"contradiction_text_gate_enabled": False})

    assert _retrieval_config_hash(base) != _retrieval_config_hash(with_extra_prefix)
    assert _retrieval_config_hash(base) != _retrieval_config_hash(gate_disabled)


def test_candidate_rerank_score_accepts_negative_logits() -> None:
    parent = _chunk("parent", "Parent text.")
    child = _chunk("child", "Parent text.", parent_chunk_id="parent")

    candidate = CandidateEvidence(
        claim_id="clm-test",
        claim_text="claim text",
        parent_chunk=parent,
        matched_child_chunk=child,
        child_rank=1,
        fusion_score=0.1,
        rerank_score=-2.5,
        retrieval_method="hybrid",
        evidence_role="supporting",
    )

    assert candidate.rerank_score == -2.5


def _chunk(
    chunk_id: str,
    text: str,
    *,
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
        char_start=0,
        char_end=len(text),
        chunk_hash=hash_text(text),
        excerpt=text,
        text=text,
    )
