from __future__ import annotations

import json
from pathlib import Path

from evidence_bundler.experiments.contract_b_seam_probe import (
    build_cal_measurement_view,
    build_handoff_variant,
    cal_measurement_view_hash,
    canonical_hash,
    collect_fact_ids,
    find_audit_judgment_keys,
    handoff_hash,
    load_fixture,
    mutate_downstream_assessments,
    mutate_mechanical_fact,
    mutate_nomination_metadata,
    validate_fixture,
)

_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "contract-b-seam"
    / "tri-repo-fixture.yaml"
)


def _passage_ids(view: dict[str, object]) -> set[str]:
    passages = view["admitted_passages"]
    assert isinstance(passages, list)
    return {
        passage["passage_id"]
        for passage in passages
        if isinstance(passage, dict) and isinstance(passage.get("passage_id"), str)
    }


def _link_by_id(handoff: dict[str, object], link_id: str) -> dict[str, object]:
    links = handoff["links"]
    assert isinstance(links, list)
    return next(
        link
        for link in links
        if isinstance(link, dict) and link.get("link_id") == link_id
    )


def test_fixture_validates() -> None:
    fixture = load_fixture(_FIXTURE)
    validate_fixture(fixture)


def test_minimal_context_preserves_required_facts_that_current_projection_lacks() -> None:
    fixture = load_fixture(_FIXTURE)
    required = set(fixture["required_mechanical_fact_ids"])

    current = build_handoff_variant(fixture, "current_cb")
    minimal = build_handoff_variant(fixture, "minimal_context")

    assert collect_fact_ids(current) == set()
    assert collect_fact_ids(minimal) == required


def test_minimal_context_contains_no_proposition_specific_audit_judgments() -> None:
    fixture = load_fixture(_FIXTURE)
    minimal = build_handoff_variant(fixture, "minimal_context")
    full = build_handoff_variant(fixture, "full_sidecar")

    assert find_audit_judgment_keys(minimal) == set()
    assert {
        "proposition_specific_relation",
        "semantic_validity",
        "temporal_applicability",
        "authority_applicability",
        "decision_participation",
        "completeness_conclusion",
        "verdict",
    } <= find_audit_judgment_keys(full)


def test_downstream_assessment_mutations_do_not_change_minimal_handoff() -> None:
    fixture = load_fixture(_FIXTURE)
    mutated = mutate_downstream_assessments(fixture)

    assert handoff_hash(fixture) == handoff_hash(mutated)
    assert cal_measurement_view_hash(fixture) == cal_measurement_view_hash(mutated)


def test_mechanical_fact_mutation_changes_handoff_and_cal_measurement_view() -> None:
    fixture = load_fixture(_FIXTURE)
    mutated = mutate_mechanical_fact(
        fixture, "fact-current-validation-version", "2.1"
    )

    assert handoff_hash(fixture) != handoff_hash(mutated)
    assert cal_measurement_view_hash(fixture) != cal_measurement_view_hash(mutated)


def test_nomination_metadata_is_auditable_but_blinded_from_cal_semantic_view() -> None:
    fixture = load_fixture(_FIXTURE)
    mutated = mutate_nomination_metadata(fixture)

    assert handoff_hash(fixture) != handoff_hash(mutated)
    assert cal_measurement_view_hash(fixture) == cal_measurement_view_hash(mutated)


def test_admitted_nondeciding_historical_evidence_is_not_erased_upstream() -> None:
    fixture = load_fixture(_FIXTURE)
    sidecar = fixture["cal_research_sidecar"]
    assert isinstance(sidecar, dict)
    assessments = sidecar["assessments"]
    assert isinstance(assessments, list)
    old_assessment = next(
        item
        for item in assessments
        if isinstance(item, dict) and item.get("passage_id") == "psg-validation-old"
    )
    assert old_assessment["temporal_applicability"] == "stale_for_current_state"
    assert old_assessment["decision_participation"] is False

    minimal = build_handoff_variant(fixture, "minimal_context")
    cal_view = build_cal_measurement_view(minimal)

    assert "psg-validation-old" in _passage_ids(cal_view)


def test_rejected_candidate_is_recoverable_in_handoff_but_not_admitted_to_cal() -> None:
    fixture = load_fixture(_FIXTURE)
    minimal = build_handoff_variant(fixture, "minimal_context")
    cal_view = build_cal_measurement_view(minimal)

    rejected = _link_by_id(minimal, "lnk-marketing")
    review = rejected["review"]
    assert isinstance(review, dict)
    assert review["decision"] == "rejected"

    passage_ids = _passage_ids(cal_view)
    assert "psg-marketing" not in passage_ids
    assert "psg-validation-current" in passage_ids


def test_coverage_facts_cross_without_completeness_judgment() -> None:
    fixture = load_fixture(_FIXTURE)
    minimal = build_handoff_variant(fixture, "minimal_context")
    cal_view = build_cal_measurement_view(minimal)

    coverage = cal_view["coverage"]
    assert isinstance(coverage, dict)
    assert coverage["candidate_count"] == 5
    assert coverage["reviewed_count"] == 5
    assert coverage["admitted_count"] == 4
    assert coverage["search_scope"]["closed_world"] is True

    serialized = json.dumps(cal_view, sort_keys=True)
    assert "completeness_conclusion" not in serialized
    assert "sufficient_for_fixture_only" not in serialized


def test_cal_measurement_view_contains_no_nomination_or_reviewer_hints() -> None:
    fixture = load_fixture(_FIXTURE)
    minimal = build_handoff_variant(fixture, "minimal_context")
    view = build_cal_measurement_view(minimal)
    serialized = json.dumps(view, sort_keys=True)

    forbidden = (
        "hypothesized_role",
        "retrieval_run_id",
        "scores",
        "rank",
        "reviewed_by",
        "reviewed_at_utc",
        "notes",
        "support_candidate",
        "counter_candidate",
        "qualifier_candidate",
    )
    for token in forbidden:
        assert token not in serialized


def test_full_sidecar_diff_is_exactly_downstream_research_state_plus_variant_label() -> None:
    fixture = load_fixture(_FIXTURE)
    minimal = build_handoff_variant(fixture, "minimal_context")
    full = build_handoff_variant(fixture, "full_sidecar")

    stripped_full = dict(full)
    sidecar = stripped_full.pop("cal_research_sidecar")
    stripped_full["variant"] = "minimal_context"

    assert canonical_hash(stripped_full) == canonical_hash(minimal)
    assert isinstance(sidecar, dict)
    assert sidecar["verdict"] == "supported_for_fixture_only"
