"""Successor observability and replay tests for retrieval research-arm apparatus."""

from __future__ import annotations

from pathlib import Path

import pytest

from evidence_bundler.contracts.writer import _retrieval_config_hash, build_retrieval_bundle
from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.retrieval.bm25_retriever import BM25Retriever
from evidence_bundler.retrieval.contradiction import (
    build_contradiction_queries,
    classify_role,
)
from evidence_bundler.retrieval.embedding_retriever import SemanticIndex
from evidence_bundler.retrieval.hybrid import reciprocal_rank_fusion
from evidence_bundler.retrieval.research_receipt import (
    build_research_arm_receipt,
    normalized_identity_config,
    write_research_arm_receipt,
)

COMMIT_SHA = "a" * 40
TREE_SHA = "b" * 40


class RecordingEmbedder:
    def __init__(self) -> None:
        self.encoded: list[str] = []

    def encode(self, texts: list[str], **_kwargs: object) -> list[list[float]]:
        self.encoded.extend(texts)
        return [_vector_for(text) for text in texts]


def _vector_for(text: str) -> list[float]:
    lowered = text.lower()
    return [
        float("submission" in lowered or "review" in lowered),
        float("plain" in lowered or "text" in lowered),
        float("pdf" in lowered or "extraction" in lowered),
        0.25,
    ]


def test_receipt_is_reconstructable_and_replay_stable(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    config = RetrievalConfig(
        retrieval_method="bm25",
        top_k=2,
        child_top_k=4,
        semantic_query_prefix="receipt-must-preserve-this-prefix: ",
        embedding_model_cache_dir=tmp_path / "cache-a",
    )
    report_a = tmp_path / "report-a.md"
    first = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        tmp_path / "bundle-a",
        config=config,
        report_out=report_a,
    )
    receipt_a = build_research_arm_receipt(
        scaffold_run_dir=mixed_scaffold_run_tmp,
        result=first,
        config=config,
        apparatus_commit_sha=COMMIT_SHA,
        apparatus_tree_sha=TREE_SHA,
        report_path=report_a,
    )
    receipt_path, receipt_hash = write_research_arm_receipt(
        receipt_a,
        tmp_path / "arm-receipt.json",
    )

    assert receipt_path.exists()
    assert receipt_path.with_suffix(".json.sha256").exists()
    assert receipt_hash.startswith("sha256:")
    assert receipt_a["retrieval_config"]["semantic_query_prefix"] == (
        "receipt-must-preserve-this-prefix: "
    )
    assert receipt_a["identity_config"] == normalized_identity_config(config)
    assert "embedding_model_cache_dir" not in receipt_a["identity_config"]
    assert receipt_a["non_identity_config_fields"] == [
        "embedding_model_cache_dir",
        "semantic_index_path",
    ]
    assert receipt_a["chunking"]["ordered_chunk_set_hash"].startswith("sha256:")
    assert receipt_a["outputs"]["bundle_hash"] == first.manifest.bundle.bundle_hash
    assert receipt_a["outputs"]["report_hash"] is not None

    replay_config = RetrievalConfig.model_validate(receipt_a["retrieval_config"])
    second = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        tmp_path / "bundle-b",
        config=replay_config,
    )
    receipt_b = build_research_arm_receipt(
        scaffold_run_dir=mixed_scaffold_run_tmp,
        result=second,
        config=replay_config,
        apparatus_commit_sha=COMMIT_SHA,
        apparatus_tree_sha=TREE_SHA,
    )

    assert _retrieval_config_hash(replay_config) == receipt_a["retrieval_config_hash"]
    assert receipt_b["arm_identity"] == receipt_a["arm_identity"]
    assert receipt_b["chunking"]["ordered_chunk_set_hash"] == (
        receipt_a["chunking"]["ordered_chunk_set_hash"]
    )
    assert first.retrieval_report is not None
    assert second.retrieval_report is not None
    assert first.retrieval_report.claim_summaries == second.retrieval_report.claim_summaries


def test_cache_path_is_recorded_but_not_arm_identity(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
) -> None:
    config_a = RetrievalConfig(embedding_model_cache_dir=tmp_path / "cache-a")
    config_b = RetrievalConfig(embedding_model_cache_dir=tmp_path / "cache-b")
    first = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        tmp_path / "cache-bundle-a",
        config=config_a,
    )
    second = build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        tmp_path / "cache-bundle-b",
        config=config_b,
    )
    receipt_a = build_research_arm_receipt(
        scaffold_run_dir=mixed_scaffold_run_tmp,
        result=first,
        config=config_a,
        apparatus_commit_sha=COMMIT_SHA,
        apparatus_tree_sha=TREE_SHA,
    )
    receipt_b = build_research_arm_receipt(
        scaffold_run_dir=mixed_scaffold_run_tmp,
        result=second,
        config=config_b,
        apparatus_commit_sha=COMMIT_SHA,
        apparatus_tree_sha=TREE_SHA,
    )

    assert receipt_a["retrieval_config"]["embedding_model_cache_dir"] != (
        receipt_b["retrieval_config"]["embedding_model_cache_dir"]
    )
    assert receipt_a["arm_identity"] == receipt_b["arm_identity"]


def test_semantic_query_prefix_mutation_changes_encoded_query_and_identity(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    embedders: list[RecordingEmbedder] = []

    def loader(*_args: object, **_kwargs: object) -> RecordingEmbedder:
        embedder = RecordingEmbedder()
        embedders.append(embedder)
        return embedder

    monkeypatch.setattr("evidence_bundler.contracts.writer.load_embedding_model", loader)

    configs = [
        RetrievalConfig(
            retrieval_method="semantic",
            semantic_child_top_k=2,
            semantic_query_prefix="prefix-a: ",
            embedding_model="fake-semantic",
        ),
        RetrievalConfig(
            retrieval_method="semantic",
            semantic_child_top_k=2,
            semantic_query_prefix="prefix-b: ",
            embedding_model="fake-semantic",
        ),
    ]
    for index, config in enumerate(configs):
        build_retrieval_bundle(
            mixed_scaffold_run_tmp,
            tmp_path / f"semantic-prefix-{index}",
            config=config,
        )

    assert any(text.startswith("prefix-a: ") for text in embedders[0].encoded)
    assert any(text.startswith("prefix-b: ") for text in embedders[1].encoded)
    assert _retrieval_config_hash(configs[0]) != _retrieval_config_hash(configs[1])


def test_parent_candidate_budget_mutation_changes_parent_aggregation_limit(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from evidence_bundler.contracts import writer

    original = writer.aggregate_parent_candidates
    observed_limits: list[int | None] = []

    def spy_aggregate(**kwargs: object) -> list[object]:
        observed_limits.append(kwargs.get("limit"))  # type: ignore[arg-type]
        return original(**kwargs)  # type: ignore[arg-type,return-value]

    monkeypatch.setattr(writer, "aggregate_parent_candidates", spy_aggregate)

    for budget in (2, 4):
        build_retrieval_bundle(
            mixed_scaffold_run_tmp,
            tmp_path / f"parent-budget-{budget}",
            config=RetrievalConfig(
                retrieval_method="bm25",
                top_k=1,
                parent_candidate_top_k=budget,
                child_top_k=8,
            ),
        )

    claim_count = len(observed_limits) // 2
    assert claim_count > 0
    assert observed_limits[:claim_count] == [2] * claim_count
    assert observed_limits[claim_count:] == [4] * claim_count


def test_counterevidence_child_budgets_are_independently_observable(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: RecordingEmbedder(),
    )
    lexical_observed: list[int] = []
    semantic_observed: list[int] = []
    original_lexical = BM25Retriever.query
    original_semantic = SemanticIndex.query

    def lexical_spy(
        self: BM25Retriever,
        query_text: str,
        *,
        top_k: int = 20,
        score_floor: float = 0.0,
    ) -> list[object]:
        if query_text.startswith("evidence against "):
            lexical_observed.append(top_k)
        return original_lexical(self, query_text, top_k=top_k, score_floor=score_floor)

    def semantic_spy(
        self: SemanticIndex,
        query_text: str,
        *,
        top_k: int = 20,
    ) -> list[object]:
        if query_text.startswith("evidence against "):
            semantic_observed.append(top_k)
        return original_semantic(self, query_text, top_k=top_k)

    monkeypatch.setattr(BM25Retriever, "query", lexical_spy)
    monkeypatch.setattr(SemanticIndex, "query", semantic_spy)

    build_retrieval_bundle(
        mixed_scaffold_run_tmp,
        tmp_path / "counter-budget",
        config=RetrievalConfig(
            retrieval_method="hybrid",
            top_k=2,
            rrf_candidate_pool=5,
            semantic_child_top_k=5,
            contradiction_enabled=True,
            contradiction_query_prefixes=["evidence against"],
            contradiction_text_gate_enabled=False,
            counterevidence_lexical_child_top_k=2,
            counterevidence_semantic_child_top_k=3,
            embedding_model="fake-semantic",
        ),
    )

    assert lexical_observed and set(lexical_observed) == {2}
    assert semantic_observed and set(semantic_observed) == {3}


def test_rrf_constant_mutation_changes_fusion_computation() -> None:
    rankings = [["a", "b", "c"], ["b", "c", "a"]]
    small = reciprocal_rank_fusion(rankings, k=1)
    large = reciprocal_rank_fusion(rankings, k=60)

    assert [row.chunk_id for row in small] == [row.chunk_id for row in large]
    assert [row.fusion_score for row in small] != [row.fusion_score for row in large]


def test_contradiction_prefix_and_text_gate_are_computationally_observable() -> None:
    claim = "the treatment improves survival"
    assert build_contradiction_queries(claim, ["evidence against"]) != (
        build_contradiction_queries(claim, ["limitations of"])
    )

    gated = RetrievalConfig(
        retrieval_method="hybrid",
        contradiction_enabled=True,
        contradiction_text_gate_enabled=True,
    )
    ungated = gated.model_copy(update={"contradiction_text_gate_enabled": False})
    passage = "A plain passage without a disconfirming lexical pattern."

    assert classify_role(passage, gated) == "insufficient"
    assert classify_role(passage, ungated) == "contradicting"


def test_new_research_controls_preserve_defaults() -> None:
    config = RetrievalConfig()

    assert config.parent_candidate_top_k is None
    assert config.counterevidence_lexical_child_top_k is None
    assert config.counterevidence_semantic_child_top_k is None
    assert config.top_k == 5
    assert config.rrf_candidate_pool == 50
    assert config.semantic_child_top_k == 50
