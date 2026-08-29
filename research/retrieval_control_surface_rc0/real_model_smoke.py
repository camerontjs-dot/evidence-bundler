"""Hosted real-model pinning smoke for RC0. No retrieval-quality claim is made."""

from __future__ import annotations

import json
import math

from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.retrieval.embedding_retriever import load_embedding_model
from evidence_bundler.retrieval.reranker import load_reranker_model

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
RERANK_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"


def main() -> None:
    RetrievalConfig(
        retrieval_method="hybrid",
        embedding_model=EMBED_MODEL,
        embedding_model_revision=EMBED_REVISION,
        rerank_enabled=True,
        rerank_model=RERANK_MODEL,
        rerank_model_revision=RERANK_REVISION,
        require_immutable_model_revisions=True,
    )
    embedder = load_embedding_model(EMBED_MODEL, revision=EMBED_REVISION)
    vectors = embedder.encode(
        ["synthetic apparatus receipt"],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    vector = vectors.tolist()[0] if hasattr(vectors, "tolist") else vectors[0]
    reranker = load_reranker_model(RERANK_MODEL, revision=RERANK_REVISION)
    raw_scores = reranker.predict(
        [("synthetic query", "synthetic candidate passage")],
        show_progress_bar=False,
    )
    scores = raw_scores.tolist() if hasattr(raw_scores, "tolist") else list(raw_scores)
    score = float(scores[0])
    if not vector or not all(math.isfinite(float(value)) for value in vector):
        raise RuntimeError("Embedding smoke returned an invalid vector")
    if not math.isfinite(score):
        raise RuntimeError("Reranker smoke returned a non-finite score")
    print(
        json.dumps(
            {
                "embedding_model": EMBED_MODEL,
                "embedding_revision": EMBED_REVISION,
                "embedding_dim": len(vector),
                "reranker_model": RERANK_MODEL,
                "reranker_revision": RERANK_REVISION,
                "reranker_score_finite": True,
                "scope": "apparatus execution only; no retrieval-quality claim",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
