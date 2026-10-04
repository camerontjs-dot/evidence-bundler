from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any

import pytest

from evidence_bundler.v1 import (
    ContractAValidationError,
    EvidencePackageValidationError,
    V1Config,
    build_package,
    validate_contract_a,
    validate_package,
)
from evidence_bundler.v1.contract_a import compute_handoff_sha256
from evidence_bundler.v1.package import compute_package_sha256


def _hash_text(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _contract_a(*, state: str = "declared") -> dict[str, Any]:
    root_text = "Alpha beta gamma delta and omega theta are both documented."
    child_one = "alpha beta gamma delta"
    child_two = "omega theta"
    source_texts = [
        "alpha appears in calibration note A.",
        "alpha appears in calibration note B.",
        "beta appears in calibration note A.",
        "beta appears in calibration note B.",
        "gamma appears in calibration note A.",
        "gamma appears in calibration note B.",
        "delta appears in calibration note A.",
        "delta appears in calibration note B.",
        "omega theta appears together in source nine.",
        "omega theta appears together in source ten.",
        "unrelated cobalt orchard material.",
        "unrelated marine quartz material.",
    ]
    sources = [
        {
            "source_id": f"S{index:02d}",
            "media_type": "text/plain; charset=utf-8",
            "content": text,
            "content_sha256": _hash_text(text),
        }
        for index, text in enumerate(source_texts, start=1)
    ]
    value: dict[str, Any] = {
        "schema": "contract-a-wire-candidate-rc2",
        "handoff_id": "handoff-v1-test",
        "producer": {"producer_id": "test", "producer_version": "1"},
        "work": {"work_id": "work-v1-test"},
        "root_proposition": {
            "proposition_id": "ROOT",
            "text": root_text,
            "text_sha256": _hash_text(root_text),
        },
        "decomposition": {"state": state},
        "sources": sources,
        "handoff_sha256": "sha256:" + "0" * 64,
    }
    if state == "declared":
        value["decomposition"] = {
            "state": "declared",
            "decomposition_id": "D1",
            "operator": "all_of",
            "children": [
                {
                    "proposition_id": "C1",
                    "text": child_one,
                    "text_sha256": _hash_text(child_one),
                    "sequence": 1,
                },
                {
                    "proposition_id": "C2",
                    "text": child_two,
                    "text_sha256": _hash_text(child_two),
                    "sequence": 2,
                },
            ],
        }
    value["handoff_sha256"] = compute_handoff_sha256(value)
    return value


def _reseal(package: dict[str, Any]) -> dict[str, Any]:
    package["package_sha256"] = compute_package_sha256(package)
    return package


def test_contract_a_exact_hash_validation_fails_closed() -> None:
    value = _contract_a()
    value["root_proposition"]["text"] = "mutated"
    with pytest.raises(ContractAValidationError, match="text_sha256 mismatch"):
        validate_contract_a(value)


def test_declared_children_get_independent_normative_lanes_and_full_history() -> None:
    package = build_package(contract_a=_contract_a())
    assert package["execution_state"] == "complete"
    assert [row["proposition_id"] for row in package["primary_targets"]] == ["C1", "C2"]
    assert [row["retrieval_lane"] for row in package["retrieval_plans"]] == [
        "declared_child",
        "declared_child",
    ]
    assert len({row["query_id"] for row in package["retrieval_plans"]}) == 2
    assert package["diagnostics"]["root_retrieval"] is None

    c1 = [row for row in package["candidates"] if row["proposition_id"] == "C1"]
    assert len(c1) == 5
    assert [row["nomination_rank"] for row in c1] == [1, 2, 3, 4, 5]
    assert [row["selection_state"] for row in c1] == [
        "retained",
        "retained",
        "retained",
        "not_retained",
        "not_retained",
    ]
    assert [row["admission_state"] for row in c1] == [
        "needs-review",
        "needs-review",
        "needs-review",
        "not_applicable",
        "not_applicable",
    ]


def test_explicit_admission_is_distinct_from_nomination_and_selection() -> None:
    initial = build_package(contract_a=_contract_a())
    first = next(
        row
        for row in initial["candidates"]
        if row["proposition_id"] == "C1" and row["selection_state"] == "retained"
    )
    admitted = build_package(
        contract_a=_contract_a(),
        admission={("C1", first["passage_id"]): "accepted"},
    )
    corresponding = next(
        row
        for row in admitted["candidates"]
        if row["proposition_id"] == "C1" and row["passage_id"] == first["passage_id"]
    )
    assert corresponding["nomination_rank"] == first["nomination_rank"]
    assert corresponding["selection_state"] == "retained"
    assert corresponding["admission_state"] == "accepted"
    serialized = str(admitted)
    assert "SUPPORTS" not in serialized
    assert "REFUTES" not in serialized
    assert "verdict" not in serialized


def test_admission_cannot_target_nonretained_or_unknown_candidate() -> None:
    package = build_package(contract_a=_contract_a())
    nonretained = next(
        row for row in package["candidates"] if row["selection_state"] == "not_retained"
    )
    with pytest.raises(EvidencePackageValidationError, match="retained normative candidates"):
        build_package(
            contract_a=_contract_a(),
            admission={(nonretained["proposition_id"], nonretained["passage_id"]): "accepted"},
        )


def test_passage_bytes_are_bound_to_embedded_contract_a_sources() -> None:
    package = build_package(contract_a=_contract_a())
    mutated = deepcopy(package)
    mutated["candidates"][0]["text"] += " tamper"
    _reseal(mutated)
    with pytest.raises(EvidencePackageValidationError, match="does not match source bytes"):
        validate_package(mutated)


def test_substituted_contract_a_identity_fails_even_when_outer_package_is_resealed() -> None:
    package = build_package(contract_a=_contract_a())
    mutated = deepcopy(package)
    mutated["contract_a"]["handoff_sha256"] = "sha256:" + "f" * 64
    _reseal(mutated)
    with pytest.raises(EvidencePackageValidationError, match="embedded Contract A"):
        validate_package(mutated)


def test_explicit_not_run_produces_partial_state_without_candidates_for_that_lane() -> None:
    package = build_package(contract_a=_contract_a(), not_run_target_ids={"C2"})
    assert package["execution_state"] == "partial"
    c2_plan = next(row for row in package["retrieval_plans"] if row["proposition_id"] == "C2")
    c2_execution = next(
        row
        for row in package["retrieval_executions"]
        if row["retrieval_id"] == c2_plan["retrieval_id"]
    )
    assert c2_execution["status"] == "not_run"
    assert c2_execution["aperture_state"] == "not_run"
    assert not [
        row
        for row in package["candidates"]
        if row["retrieval_id"] == c2_plan["retrieval_id"]
    ]


def test_root_diagnostic_is_separate_and_cannot_change_normative_candidates() -> None:
    baseline = build_package(contract_a=_contract_a())
    diagnostic = build_package(contract_a=_contract_a(), config=V1Config(root_diagnostic=True))
    assert diagnostic["diagnostics"]["root_retrieval"]["normative"] is False
    assert diagnostic["diagnostics"]["root_retrieval"]["retrieval_lane"] == "diagnostic_root_rescue"
    baseline_normative = [
        (row["proposition_id"], row["passage_id"], row["nomination_rank"])
        for row in baseline["candidates"]
    ]
    diagnostic_normative = [
        (row["proposition_id"], row["passage_id"], row["nomination_rank"])
        for row in diagnostic["candidates"]
    ]
    assert baseline_normative == diagnostic_normative


def test_unknown_decomposition_is_not_silently_treated_as_not_decomposed() -> None:
    with pytest.raises(ContractAValidationError, match="will not infer not_decomposed"):
        build_package(contract_a=_contract_a(state="unknown"))


def test_positive_not_decomposed_uses_exact_root_as_normative_target() -> None:
    package = build_package(contract_a=_contract_a(state="not_decomposed"))
    assert package["primary_targets"] == [
        {
            "proposition_id": "ROOT",
            "text": _contract_a(state="not_decomposed")["root_proposition"]["text"],
            "text_sha256": _contract_a(state="not_decomposed")["root_proposition"]["text_sha256"],
            "role": "root",
            "sequence": None,
        }
    ]
    assert package["retrieval_plans"][0]["retrieval_lane"] == "root"


def test_package_is_deterministic_for_identical_inputs() -> None:
    first = build_package(contract_a=_contract_a())
    second = build_package(contract_a=_contract_a())
    assert first == second
    assert first["package_sha256"] == second["package_sha256"]


def test_query_identity_substitution_fails_even_when_outer_package_is_resealed() -> None:
    package = build_package(contract_a=_contract_a())
    mutated = deepcopy(package)
    mutated["retrieval_plans"][0]["query_id"] = "query:" + "a" * 32
    _reseal(mutated)
    with pytest.raises(EvidencePackageValidationError, match="content-derived identity mismatch"):
        validate_package(mutated)
