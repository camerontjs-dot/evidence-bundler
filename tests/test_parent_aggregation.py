"""Parent aggregation tests for Phase 2a retrieval."""

from __future__ import annotations

from pathlib import Path

from evidence_bundler.contracts.hashing import hash_text
from evidence_bundler.models.ca import ScaffoldClaim
from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.retrieval.bm25_retriever import ChunkSearchHit
from evidence_bundler.retrieval.parent_aggregator import aggregate_parent_candidates


def test_parent_aggregation_uses_max_child_score() -> None:
    parent = _chunk("parent", "Parent context for retained checklist.", 0, 38, level="section")
    low = _chunk("child-low", "Checklist retained.", 4, 23, parent_chunk_id="parent")
    high = _chunk("child-high", "Final audit review checklist.", 24, 53, parent_chunk_id="parent")

    candidates = aggregate_parent_candidates(
        claim=_claim(),
        hits=[
            ChunkSearchHit(chunk=low, score=1.0, rank=1),
            ChunkSearchHit(chunk=high, score=3.0, rank=2),
        ],
        chunks_by_id={chunk.chunk_id: chunk for chunk in [parent, low, high]},
        config=RetrievalConfig(top_k=5),
    )

    assert len(candidates) == 1
    assert candidates[0].parent_chunk == parent
    assert candidates[0].matched_child_chunk == high
    assert candidates[0].lexical_score == 3.0


def test_parent_aggregation_returns_parent_context_and_child_excerpt() -> None:
    parent = _chunk("parent", "## Methods\n\nThe sponsor should retain the checklist.", 0, 50)
    child = _chunk(
        "child",
        "The sponsor should retain the checklist.",
        12,
        50,
        parent_chunk_id="parent",
    )

    candidates = aggregate_parent_candidates(
        claim=_claim(),
        hits=[ChunkSearchHit(chunk=child, score=2.0, rank=1)],
        chunks_by_id={parent.chunk_id: parent, child.chunk_id: child},
        config=RetrievalConfig(top_k=5),
    )

    assert candidates[0].parent_chunk.text.startswith("## Methods")
    assert candidates[0].matched_child_chunk.excerpt == "The sponsor should retain the checklist."


def test_parent_aggregation_ties_are_deterministic_by_rank_then_parent_position() -> None:
    parent_late = _chunk("parent-late", "Late parent.", 40, 52)
    parent_early = _chunk("parent-early", "Early parent.", 10, 23)
    child_late = _chunk("child-late", "Same score.", 42, 53, parent_chunk_id="parent-late")
    child_early = _chunk("child-early", "Same score.", 12, 23, parent_chunk_id="parent-early")

    candidates = aggregate_parent_candidates(
        claim=_claim(),
        hits=[
            ChunkSearchHit(chunk=child_late, score=2.0, rank=1),
            ChunkSearchHit(chunk=child_early, score=2.0, rank=1),
        ],
        chunks_by_id={
            chunk.chunk_id: chunk
            for chunk in [parent_late, parent_early, child_late, child_early]
        },
        config=RetrievalConfig(top_k=5),
    )

    assert [candidate.parent_chunk.chunk_id for candidate in candidates] == [
        "parent-early",
        "parent-late",
    ]


def test_parent_aggregation_top_k_truncation_is_stable() -> None:
    parent_a = _chunk("parent-a", "Parent A.", 0, 9)
    parent_b = _chunk("parent-b", "Parent B.", 10, 19)
    child_a = _chunk("child-a", "Candidate A.", 0, 12, parent_chunk_id="parent-a")
    child_b = _chunk("child-b", "Candidate B.", 10, 22, parent_chunk_id="parent-b")

    candidates = aggregate_parent_candidates(
        claim=_claim(),
        hits=[
            ChunkSearchHit(chunk=child_a, score=4.0, rank=1),
            ChunkSearchHit(chunk=child_b, score=3.0, rank=2),
        ],
        chunks_by_id={chunk.chunk_id: chunk for chunk in [parent_a, parent_b, child_a, child_b]},
        config=RetrievalConfig(top_k=1),
    )

    assert [candidate.parent_chunk.chunk_id for candidate in candidates] == ["parent-a"]


def test_parent_aggregation_accepts_explicit_pool_limit_above_top_k() -> None:
    parent_a = _chunk("parent-a", "Parent A.", 0, 9)
    parent_b = _chunk("parent-b", "Parent B.", 10, 19)
    child_a = _chunk("child-a", "Candidate A.", 0, 12, parent_chunk_id="parent-a")
    child_b = _chunk("child-b", "Candidate B.", 10, 22, parent_chunk_id="parent-b")

    candidates = aggregate_parent_candidates(
        claim=_claim(),
        hits=[
            ChunkSearchHit(chunk=child_a, score=4.0, rank=1),
            ChunkSearchHit(chunk=child_b, score=3.0, rank=2),
        ],
        chunks_by_id={chunk.chunk_id: chunk for chunk in [parent_a, parent_b, child_a, child_b]},
        config=RetrievalConfig(top_k=1),
        limit=2,
    )

    assert [candidate.parent_chunk.chunk_id for candidate in candidates] == [
        "parent-a",
        "parent-b",
    ]


def test_parent_aggregation_preserves_missing_lexical_score_for_hybrid_semantic_only() -> None:
    parent = _chunk("parent", "Parent context.", 0, 15)
    child = _chunk("child", "Semantic-only child.", 0, 20, parent_chunk_id="parent")

    candidates = aggregate_parent_candidates(
        claim=_claim(),
        hits=[
            ChunkSearchHit(
                chunk=child,
                score=0.01,
                rank=1,
                semantic_score=0.8,
                fusion_score=0.01,
            )
        ],
        chunks_by_id={parent.chunk_id: parent, child.chunk_id: child},
        config=RetrievalConfig(retrieval_method="hybrid", top_k=5),
    )

    assert candidates[0].lexical_score is None
    assert candidates[0].semantic_score == 0.8
    assert candidates[0].fusion_score == 0.01


def _claim() -> ScaffoldClaim:
    return ScaffoldClaim(
        claim_id="clm-test",
        claim_type="extracted_claim",
        claim_text="The sponsor should retain the checklist.",
        support_status="sourced",
        claim_strength=0.8,
        extraction_fidelity=0.9,
        source_refs=[],
        counterevidence_checked=True,
        counterevidence_found=False,
        downgraded=False,
    )


def _chunk(
    chunk_id: str,
    text: str,
    start: int,
    end: int,
    *,
    level: str = "paragraph",
    parent_chunk_id: str | None = None,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        source_id="src-test",
        source_path=Path("content.md"),
        title="Test",
        chunk_level=level,  # type: ignore[arg-type]
        parent_chunk_id=parent_chunk_id,
        heading_path=[],
        section_tag=None,
        char_start=start,
        char_end=end,
        chunk_hash=hash_text(text),
        excerpt=text,
        text=text,
    )
