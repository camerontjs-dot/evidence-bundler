"""Contradiction retrieval helpers for ADR-010."""

from __future__ import annotations

from evidence_bundler.models.retrieval import RetrievalConfig
from evidence_bundler.retrieval.contradiction import (
    build_contradiction_queries,
    classify_role,
)


def test_build_contradiction_queries_uses_configured_prefix_order() -> None:
    queries = build_contradiction_queries(
        "The sponsor retained the checklist.",
        ["evidence against", "limitations of"],
    )

    assert queries == [
        "evidence against The sponsor retained the checklist.",
        "limitations of The sponsor retained the checklist.",
    ]


def test_classify_role_tags_disconfirming_language() -> None:
    role = classify_role(
        "The intervention showed no significant effect in the confirmatory cohort.",
        RetrievalConfig(retrieval_method="hybrid"),
    )

    assert role == "contradicting"


def test_classify_role_tags_conditional_language() -> None:
    role = classify_role(
        "The checklist applies only when the final audit packet includes appendices.",
        RetrievalConfig(retrieval_method="hybrid"),
    )

    assert role == "conditional"


def test_classify_role_tags_insufficient_without_gate_match() -> None:
    role = classify_role(
        "The checklist was retained in the final audit packet.",
        RetrievalConfig(retrieval_method="hybrid"),
    )

    assert role == "insufficient"


def test_classify_role_prioritizes_contradicting_when_both_patterns_match() -> None:
    role = classify_role(
        "The checklist had no effect only when patients over 65 were reviewed.",
        RetrievalConfig(retrieval_method="hybrid"),
    )

    assert role == "contradicting"


def test_classify_role_without_text_gate_tags_contradicting() -> None:
    role = classify_role(
        "The checklist was retained in the final audit packet.",
        RetrievalConfig(retrieval_method="hybrid", contradiction_text_gate_enabled=False),
    )

    assert role == "contradicting"


def test_classify_role_benign_incidental_patterns() -> None:
    config = RetrievalConfig(retrieval_method="hybrid")

    # Benign passages with bare "no", "not", "however" should not classify as contradicting.
    assert classify_role("The patient showed no pain.", config) == "insufficient"
    assert (
        classify_role("The study was small; however, the effect was positive.", config)
        == "insufficient"
    )
    assert classify_role("The results were not unexpected.", config) == "insufficient"

    # Multi-word disconfirming patterns should still classify as contradicting.
    assert classify_role("There is no significant effect.", config) == "contradicting"
    assert classify_role("The treatment did not succeed.", config) == "contradicting"
    assert (
        classify_role("However, no effect was seen in patients over 65.", config)
        == "contradicting"
    )

