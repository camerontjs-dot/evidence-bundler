from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from evidence_bundler.contracts.factual_context import PROHIBITED_KEYS
from evidence_bundler.contracts.writer import validate_bundle_tree
from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.cb import ClaimAuditUnit, PassageRecord, SourceProfile
from evidence_bundler.v1 import V1Config, build_package
from evidence_bundler.v1.contract_a import compute_handoff_sha256
from evidence_bundler.v1.contract_b import (
    CONTRACT_B_PRODUCTION_LOCK,
    INTEGRATION_CONFIG,
    INTEGRATION_CONFIG_SHA256,
    INTEGRATION_PROFILE_ID,
    ContractBProjectionError,
    project_contract_b,
    validate_compatibility_carrier,
    validate_projection_receipt,
)
from evidence_bundler.v1.package import compute_package_sha256

ROOT = Path(__file__).resolve().parents[1]
CARRIER_PATH = (
    ROOT
    / "research"
    / "eb_v1_integration_candidate"
    / "contract_b_compatibility_carrier.json"
)


def _hash_text(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _contract_a() -> dict[str, Any]:
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
    value: dict[str, Any] = {
        "schema": "contract-a-wire-candidate-rc2",
        "handoff_id": "handoff-v1-contract-b-test",
        "producer": {"producer_id": "test", "producer_version": "1"},
        "work": {"work_id": "work-v1-contract-b-test"},
        "root_proposition": {
            "proposition_id": "ROOT",
            "text": root_text,
            "text_sha256": _hash_text(root_text),
        },
        "decomposition": {
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
        },
        "sources": [
            {
                "source_id": f"S{index:02d}",
                "media_type": "text/plain; charset=utf-8",
                "content": text,
                "content_sha256": _hash_text(text),
            }
            for index, text in enumerate(source_texts, start=1)
        ],
        "handoff_sha256": "sha256:" + "0" * 64,
    }
    value["handoff_sha256"] = compute_handoff_sha256(value)
    return value


def _carrier() -> dict[str, Any]:
    return json.loads(CARRIER_PATH.read_text(encoding="utf-8"))


def _package() -> dict[str, Any]:
    initial = build_package(contract_a=_contract_a(), config=INTEGRATION_CONFIG)
    c1 = [
        row
        for row in initial["candidates"]
        if row["proposition_id"] == "C1" and row["selection_state"] == "retained"
    ]
    c2 = [
        row
        for row in initial["candidates"]
        if row["proposition_id"] == "C2" and row["selection_state"] == "retained"
    ]
    admission = {
        ("C1", c1[0]["passage_id"]): "accepted",
        ("C1", c1[1]["passage_id"]): "rejected",
        ("C2", c2[0]["passage_id"]): "accepted",
    }
    return build_package(
        contract_a=_contract_a(),
        config=INTEGRATION_CONFIG,
        admission=admission,
    )


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(key)
            keys.update(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_walk_keys(child))
    return keys


def test_integration_profile_is_exact_10x3_without_changing_generic_v1_default() -> None:
    assert INTEGRATION_PROFILE_ID == "eb-v1-integration-10x3-rc0"
    assert INTEGRATION_CONFIG.identity == INTEGRATION_CONFIG_SHA256
    assert INTEGRATION_CONFIG.candidate_depth == 10
    assert INTEGRATION_CONFIG.retained_k == 3
    assert V1Config().candidate_depth == 5
    assert V1Config().retained_k == 3


def test_projection_emits_valid_released_contract_b_and_bound_receipt(tmp_path: Path) -> None:
    package = _package()
    receipt = project_contract_b(
        package=package,
        compatibility_carrier=_carrier(),
        out_dir=tmp_path,
    )

    assert validate_bundle_tree(tmp_path / "contract_b") == []
    assert receipt["profile_id"] == INTEGRATION_PROFILE_ID
    assert receipt["native_package_sha256"] == package["package_sha256"]
    assert receipt["native_config_sha256"] == INTEGRATION_CONFIG_SHA256
    assert receipt["contract_b_authority"] == {
        "version": "1.2.0",
        "production_lock": CONTRACT_B_PRODUCTION_LOCK,
    }
    assert validate_projection_receipt(receipt) == receipt
    on_disk = json.loads((tmp_path / "projection_receipt.json").read_text(encoding="utf-8"))
    assert on_disk == receipt


def test_projection_preserves_full_candidate_history_and_native_not_applicable(
    tmp_path: Path,
) -> None:
    package = _package()
    receipt = project_contract_b(
        package=package,
        compatibility_carrier=_carrier(),
        out_dir=tmp_path,
    )
    extension = json.loads(
        (
            tmp_path
            / "contract_b"
            / "extensions"
            / "contract-b-factual-context-v1.json"
        ).read_text(encoding="utf-8")
    )
    assert len(extension["history"]) == len(package["candidates"])
    assert len(receipt["mappings"]) == len(package["candidates"])

    native_nonretained = next(
        row for row in package["candidates"] if row["selection_state"] == "not_retained"
    )
    history = next(
        row
        for row in extension["history"]
        if row["claim_id"] == native_nonretained["proposition_id"]
        and row["passage_id"] == native_nonretained["passage_id"]
    )
    assert history["nomination"]["selection_state"] == "not_retained"
    assert history["review"]["native_admission_state"] == "not_applicable"
    assert history["review"]["decision"] == "needs-review"
    assert history["review"]["encoding"] == (
        "contract_b_needs_review_for_native_not_applicable"
    )

    accepted = {
        (row["proposition_id"], row["passage_id"])
        for row in package["candidates"]
        if row["selection_state"] == "retained" and row["admission_state"] == "accepted"
    }
    admitted_in_extension = {
        (row["claim_id"], row["passage_id"])
        for row in extension["history"]
        if row["review"]["decision"] == "accepted"
    }
    assert admitted_in_extension == accepted
    assert not (PROHIBITED_KEYS & _walk_keys(extension))


def test_claim_units_expose_only_native_accepted_passages_while_all_candidates_remain_canonical(
    tmp_path: Path,
) -> None:
    package = _package()
    project_contract_b(
        package=package,
        compatibility_carrier=_carrier(),
        out_dir=tmp_path,
    )
    bundle = tmp_path / "contract_b"
    expected = {
        claim_id: {
            row["passage_id"]
            for row in package["candidates"]
            if row["proposition_id"] == claim_id
            and row["selection_state"] == "retained"
            and row["admission_state"] == "accepted"
        }
        for claim_id in {"ROOT", "C1", "C2"}
    }
    for claim_id, expected_ids in expected.items():
        unit = load_model_yaml(ClaimAuditUnit, bundle / "claims" / f"{claim_id}.yaml")
        assert {row.passage_id for row in unit.evidence_passages} == expected_ids

    canonical_passage_ids = {path.stem for path in bundle.glob("evidence/*/passages/*.yaml")}
    assert canonical_passage_ids == {row["passage_id"] for row in package["candidates"]}


def test_source_and_passage_bytes_bind_exactly_to_native_contract_a(tmp_path: Path) -> None:
    package = _package()
    project_contract_b(
        package=package,
        compatibility_carrier=_carrier(),
        out_dir=tmp_path,
    )
    candidate = package["candidates"][0]
    bundle = tmp_path / "contract_b"
    source = next(
        row
        for row in package["contract_a"]["sources"]
        if row["source_id"] == candidate["source_id"]
    )
    profile = load_model_yaml(
        SourceProfile,
        bundle / "evidence" / candidate["source_id"] / "source_profile.yaml",
    )
    passage = load_model_yaml(
        PassageRecord,
        bundle
        / "evidence"
        / candidate["source_id"]
        / "passages"
        / f"{candidate['passage_id']}.yaml",
    )
    assert profile.content_hash == source["content_sha256"]
    assert passage.provenance.source_content_hash == source["content_sha256"]
    assert passage.char_start == candidate["char_start"]
    assert passage.char_end == candidate["char_end"]
    assert passage.passage_hash == candidate["passage_sha256"]
    assert source["content"][passage.char_start : passage.char_end] == passage.passage_text


def test_projection_is_byte_deterministic_for_same_package_and_carrier(tmp_path: Path) -> None:
    package = _package()
    carrier = _carrier()
    first = tmp_path / "first"
    second = tmp_path / "second"
    project_contract_b(package=package, compatibility_carrier=carrier, out_dir=first)
    project_contract_b(package=package, compatibility_carrier=carrier, out_dir=second)
    assert _tree_bytes(first) == _tree_bytes(second)


def test_carrier_is_causally_downstream_and_cannot_mutate_native_package(tmp_path: Path) -> None:
    package = _package()
    frozen = deepcopy(package)
    carrier = _carrier()
    mutated = deepcopy(carrier)
    mutated["source_profile"]["title_template"] = "Compatibility title {source_id}"
    mutated["source_profile"]["notes"] = "Different compatibility-only notes."

    first = project_contract_b(
        package=package,
        compatibility_carrier=carrier,
        out_dir=tmp_path / "first",
    )
    second = project_contract_b(
        package=package,
        compatibility_carrier=mutated,
        out_dir=tmp_path / "second",
    )
    assert package == frozen
    assert first["native_package_sha256"] == second["native_package_sha256"]
    assert first["mappings"] == second["mappings"]
    assert first["compatibility_carrier_sha256"] != second["compatibility_carrier_sha256"]


def test_weakened_or_incomplete_carrier_fails_closed() -> None:
    carrier = _carrier()
    weakened = deepcopy(carrier)
    weakened["authority"]["semantic_use_authorized"] = True
    with pytest.raises(ContractBProjectionError, match="authority boundary"):
        validate_compatibility_carrier(weakened)

    incomplete = deepcopy(carrier)
    del incomplete["passage_record"]["paragraph_index"]
    with pytest.raises(ContractBProjectionError, match="shape mismatch"):
        validate_compatibility_carrier(incomplete)


def test_wrong_retrieval_config_is_rejected_at_projection_boundary(tmp_path: Path) -> None:
    package = build_package(contract_a=_contract_a(), config=V1Config())
    with pytest.raises(ContractBProjectionError, match="frozen eb-v1-integration-10x3-rc0"):
        project_contract_b(
            package=package,
            compatibility_carrier=_carrier(),
            out_dir=tmp_path,
        )


def test_native_package_tamper_fails_before_contract_b_emission(tmp_path: Path) -> None:
    package = _package()
    tampered = deepcopy(package)
    tampered["candidates"][0]["passage_sha256"] = "sha256:" + "f" * 64
    tampered["package_sha256"] = compute_package_sha256(tampered)
    with pytest.raises(Exception, match="passage_sha256 mismatch"):
        project_contract_b(
            package=tampered,
            compatibility_carrier=_carrier(),
            out_dir=tmp_path,
        )
    assert not (tmp_path / "contract_b").exists()


def test_projection_receipt_tamper_fails_closed(tmp_path: Path) -> None:
    receipt = project_contract_b(
        package=_package(),
        compatibility_carrier=_carrier(),
        out_dir=tmp_path,
    )
    tampered = deepcopy(receipt)
    tampered["native_config_sha256"] = "sha256:" + "a" * 64
    with pytest.raises(ContractBProjectionError, match="receipt hash mismatch"):
        validate_projection_receipt(tampered)


def test_exact_cal_contract_b_consumer_accepts_projection_when_installed(tmp_path: Path) -> None:
    factual_context = pytest.importorskip("claim_audit_lab.contracts.factual_context")
    package = _package()
    project_contract_b(
        package=package,
        compatibility_carrier=_carrier(),
        out_dir=tmp_path,
    )
    view = factual_context.load_contract_b_intake(
        tmp_path / "contract_b",
        deviations_dir=tmp_path / "cal-deviations",
    )
    assert view.extension_state == "present"
    assert view.intake_ledger is not None
    assert view.semantic_context is not None
    admitted = {
        (claim["claim_id"], passage["passage_id"])
        for claim in view.semantic_context["claims"]
        for passage in claim["admitted_passages"]
    }
    expected = {
        (row["proposition_id"], row["passage_id"])
        for row in package["candidates"]
        if row["selection_state"] == "retained" and row["admission_state"] == "accepted"
    }
    assert admitted == expected
