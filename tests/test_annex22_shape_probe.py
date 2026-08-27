from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from evidence_bundler.experiments.annex22_shape_probe import (
    ShapeProbeError,
    build_blinded_cal_view,
    cal_view_hash,
    load_prototype,
    mutate_nomination_hypotheses,
    reconstruct_provenance,
    validate_prototype,
)

_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "annex22-shape"
    / "prototype-bundle.yaml"
)


def _claims_by_id(view: dict[str, object]) -> dict[str, dict[str, object]]:
    claims = view["claims"]
    assert isinstance(claims, list)
    return {claim["claim_id"]: claim for claim in claims if isinstance(claim, dict)}


def _sources_by_id(view: dict[str, object]) -> dict[str, dict[str, object]]:
    sources = view["sources"]
    assert isinstance(sources, list)
    return {source["source_id"]: source for source in sources if isinstance(source, dict)}


def test_annex22_fixture_validates() -> None:
    bundle = load_prototype(_FIXTURE)
    validate_prototype(bundle)


def test_blinded_view_preserves_distinct_coverage_states() -> None:
    view = build_blinded_cal_view(load_prototype(_FIXTURE))
    claims = _claims_by_id(view)

    assert claims["clm-N1"]["coverage"]["outcome"] == "no_candidates"
    assert claims["clm-N2"]["coverage"]["outcome"] == "all_rejected"
    assert claims["clm-N3"]["coverage"]["outcome"] == "partial_review"
    assert claims["clm-N4"]["coverage"]["outcome"] == "admitted"

    assert claims["clm-N1"]["passages"] == []
    assert claims["clm-N2"]["passages"] == []
    assert len(claims["clm-N3"]["passages"]) == 1
    assert len(claims["clm-N4"]["passages"]) == 1


def test_blinded_view_preserves_source_status_as_structured_metadata() -> None:
    view = build_blinded_cal_view(load_prototype(_FIXTURE))
    source = _sources_by_id(view)["src-annex22-draft"]

    assert source["document_status"] == "draft_consultation"
    assert source["publisher"] == "European Commission"
    assert source["jurisdiction"] == "EU"


def test_nomination_hypotheses_do_not_change_blinded_view() -> None:
    bundle = load_prototype(_FIXTURE)
    mutated = mutate_nomination_hypotheses(bundle)

    assert build_blinded_cal_view(bundle) == build_blinded_cal_view(mutated)
    assert cal_view_hash(bundle) == cal_view_hash(mutated)


def test_blinding_invariance_is_not_vacuous() -> None:
    bundle = load_prototype(_FIXTURE)
    changed = deepcopy(bundle)
    passages = changed["passages"]
    assert isinstance(passages, list)
    first = passages[0]
    assert isinstance(first, dict)
    first["text"] = f"{first['text']} changed"

    assert cal_view_hash(bundle) != cal_view_hash(changed)


def test_blinded_view_excludes_upstream_semantic_hints() -> None:
    view = build_blinded_cal_view(load_prototype(_FIXTURE))
    serialized = json.dumps(view, sort_keys=True)

    forbidden = (
        "hypothesized_role",
        "retrieval_run_id",
        "reviewed_by",
        "support_candidate",
        "counter_candidate",
        "scaffold_support_status",
    )
    for token in forbidden:
        assert token not in serialized


def test_provenance_reconstruction_reaches_source_and_anchor() -> None:
    bundle = load_prototype(_FIXTURE)
    path = reconstruct_provenance(bundle, "clm-B", "psg-intended-use")

    assert path["link"]["link_id"] == "lnk-B-intended"
    assert path["source"]["source_id"] == "src-annex22-draft"
    assert path["source"]["document_status"] == "draft_consultation"
    assert path["passage"]["anchors"] == [{"type": "clause", "value": "3"}]


def test_validation_rejects_inconsistent_coverage_counts() -> None:
    bundle = load_prototype(_FIXTURE)
    broken = deepcopy(bundle)
    coverage = broken["coverage"]
    assert isinstance(coverage, list)
    target = next(item for item in coverage if item["claim_id"] == "clm-N2")
    target["admitted_count"] = 1

    with pytest.raises(ShapeProbeError, match="Coverage counts"):
        validate_prototype(broken)
