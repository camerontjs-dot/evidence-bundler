"""Research-only real-model smoke for Evidence Bundler retrieval machinery.

This does not evaluate retrieval quality on Pilot scientific material. It only proves
that the production BM25, semantic index, hybrid fusion, and reranker components can
run together with the configured real model families on a tiny synthetic corpus.
"""

from __future__ import annotations

import json
from pathlib import Path

from evidence_bundler.contracts.hashing import hash_text
from evidence_bundler.models.document import DocumentChunk
from evidence_bundler.models.retrieval import CandidateEvidence, RetrievalConfig
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
from evidence_bundler.retrieval.embedding_retriever import SemanticIndex, load_embedding_model
from evidence_bundler.retrieval.hybrid import reciprocal_rank_fusion
from evidence_bundler.retrieval.reranker import ParentReranker, load_reranker_model


def chunk(chunk_id: str, text: str, start: int) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        source_id=f"src-{chunk_id}",
        source_path=Path(f"{chunk_id}.md"),
        title=chunk_id,
        chunk_level="paragraph",
        parent_chunk_id=None,
        heading_path=[],
        section_tag=None,
        char_start=start,
        char_end=start + len(text),
        chunk_hash=hash_text(text),
        excerpt=text,
        text=text,
    )


def candidate(parent: DocumentChunk, claim: str, fusion_score: float) -> CandidateEvidence:
    return CandidateEvidence(
        claim_id="machinery-smoke",
        claim_text=claim,
        parent_chunk=parent,
        matched_child_chunk=parent,
        child_rank=1,
        fusion_score=fusion_score,
        retrieval_method="hybrid",
        evidence_role="supporting",
    )


def main() -> None:
    config = RetrievalConfig(retrieval_method="hybrid", rerank_enabled=True)
    chunks = [
        chunk(
            "cardiac",
            "The clinical trial tracked myocardial infarction outcomes for twelve months.",
            0,
        ),
        chunk(
            "audit",
            "Every administrator action is recorded in an immutable audit log.",
            100,
        ),
        chunk(
            "weather",
            "The local weather forecast predicts rain on Thursday afternoon.",
            200,
        ),
    ]
    query = "heart attack outcomes"

    bm25 = BM25Retriever(chunks)
    lexical = bm25.query(query, top_k=3)

    embedder = load_embedding_model(config.embedding_model, config.embedding_model_cache_dir)
    semantic = SemanticIndex.build(
        chunks,
        embedder=embedder,
        corpus_hash=hash_text("\n".join(c.text for c in chunks)),
        embedding_model=config.embedding_model,
        semantic_query_prefix=config.semantic_query_prefix,
        show_progress_bar=False,
    )
    semantic_first = semantic.query(query, top_k=3)
    semantic_second = semantic.query(query, top_k=3)
    semantic_ids_first = [hit.chunk.chunk_id for hit in semantic_first]
    semantic_ids_second = [hit.chunk.chunk_id for hit in semantic_second]
    semantic_scores_first = [hit.semantic_score for hit in semantic_first]
    semantic_scores_second = [hit.semantic_score for hit in semantic_second]

    if semantic_ids_first != semantic_ids_second or semantic_scores_first != semantic_scores_second:
        raise AssertionError("real semantic retrieval was not repeatable across identical calls")
    if "cardiac" not in semantic_ids_first[:2]:
        raise AssertionError(
            f"semantic smoke did not place the intended paraphrase target in top 2: {semantic_ids_first}"
        )

    fused = reciprocal_rank_fusion(
        [
            [hit.chunk.chunk_id for hit in lexical],
            semantic_ids_first,
        ],
        k=config.rrf_k_constant,
    )
    fused_by_id = {hit.chunk_id: hit.fusion_score for hit in fused}

    claim = "Administrator actions are logged."
    reranker = ParentReranker(load_reranker_model(config.rerank_model))
    rerank_candidates = [
        candidate(chunks[1], claim, fused_by_id.get("audit", 0.01)),
        candidate(chunks[2], claim, fused_by_id.get("weather", 0.01)),
    ]
    first_rerank = reranker.rerank(claim, rerank_candidates)
    second_rerank = reranker.rerank(claim, rerank_candidates)

    first_signature = [
        (item.parent_chunk.chunk_id, item.rerank_score) for item in first_rerank
    ]
    second_signature = [
        (item.parent_chunk.chunk_id, item.rerank_score) for item in second_rerank
    ]
    if first_signature != second_signature:
        raise AssertionError("real reranker was not repeatable across identical calls")
    if first_signature[0][0] != "audit":
        raise AssertionError(f"reranker did not rank the relevant passage first: {first_signature}")

    receipt = {
        "scope": "research-only synthetic machinery smoke; not retrieval-quality evidence",
        "retrieval_config": config.model_dump(mode="json"),
        "model_identity_warning": (
            "Evidence Bundler config records model names but not immutable HF revision SHAs."
        ),
        "query": query,
        "lexical": [
            {"chunk_id": hit.chunk.chunk_id, "score": hit.score} for hit in lexical
        ],
        "semantic": [
            {"chunk_id": hit.chunk.chunk_id, "score": hit.semantic_score}
            for hit in semantic_first
        ],
        "hybrid_rrf": [
            {"chunk_id": hit.chunk_id, "score": hit.fusion_score} for hit in fused
        ],
        "rerank": [
            {"chunk_id": item.parent_chunk.chunk_id, "score": item.rerank_score}
            for item in first_rerank
        ],
    }
    print(json.dumps(receipt, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
