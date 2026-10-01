from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).parents[1]
    / "research"
    / "eb_real_packet_admission_discrimination_rc0_20261001"
    / "admission_discrimination.py"
)
SPEC = importlib.util.spec_from_file_location("admission_discrimination", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
APP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(APP)


def _oracle_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _oracle_hash(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _oracle_intrinsic(package: dict[str, object]) -> str:
    payload = copy.deepcopy(package)
    payload.pop("package_sha256", None)
    return _oracle_hash(_oracle_bytes(payload))


def _candidate(
    proposition_id: str,
    passage_id: str,
    rank: int,
    *,
    retained: bool,
) -> dict[str, object]:
    return {
        "proposition_id": proposition_id,
        "passage_id": passage_id,
        "nomination_rank": rank,
        "selection_state": "retained" if retained else "not_retained",
        "admission_state": "needs-review" if retained else "not_applicable",
        "text": f"passage text {proposition_id} {passage_id}",
    }


def _baseline(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    handoff = "sha256:" + "1" * 64
    candidates = []
    for proposition_id in ("P1", "P2"):
        for rank in range(1, 11):
            candidates.append(
                _candidate(
                    proposition_id,
                    f"{proposition_id}-passage-{rank}",
                    rank,
                    retained=rank <= 3,
                )
            )
    package: dict[str, object] = {
        "producer": {"producer_version": APP.EB_VERSION},
        "contract_a": {"handoff_sha256": handoff},
        "primary_targets": [
            {"proposition_id": "P1", "text": "target one"},
            {"proposition_id": "P2", "text": "target two"},
        ],
        "candidates": candidates,
        "package_sha256": "sha256:" + "0" * 64,
    }
    package["package_sha256"] = _oracle_intrinsic(package)
    monkeypatch.setattr(
        APP, "EXPECTED_RAW_FILE_SHA256", _oracle_hash(_oracle_bytes(package))
    )
    monkeypatch.setattr(
        APP, "EXPECTED_INTRINSIC_PACKAGE_SHA256", package["package_sha256"]
    )
    monkeypatch.setattr(APP, "EXPECTED_CONTRACT_A_HANDOFF_SHA256", handoff)
    return package


def _write(path: Path, value: object) -> None:
    APP.write_json(path, value)


def _freeze(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, object], Path, Path, Path, dict[str, object]]:
    package = _baseline(monkeypatch)
    package_path = tmp_path / "baseline.json"
    out_dir = tmp_path / "frozen"
    _write(package_path, package)
    receipt = APP.freeze(package_path, out_dir)
    return (
        package,
        out_dir / "FREEZE-RECEIPT.PUBLIC.json",
        out_dir / "PRIVATE-MAPPING.json",
        out_dir / "PRIVATE-REVIEW-PACKET.json",
        receipt,
    )


def _review(
    packet_path: Path,
    mapping_path: Path,
    *,
    reviewer: str,
    accepted_aliases: set[str],
    needs_review_aliases: set[str] | None = None,
) -> dict[str, object]:
    mapping = json.loads(mapping_path.read_text())
    needs_review_aliases = needs_review_aliases or set()
    decisions = []
    for row in mapping["rows"]:
        alias = row["candidate_alias"]
        if alias in accepted_aliases:
            decision, reason = "accepted", "on_target_adequate"
        elif alias in needs_review_aliases:
            decision, reason = "needs-review", "uncertain"
        else:
            decision, reason = "rejected", "wrong_target"
        decisions.append(
            {
                "candidate_alias": alias,
                "decision": decision,
                "reason": reason,
            }
        )
    return {
        "schema": APP.SCHEMA_REVIEW,
        "review_packet_sha256": APP.hash_file(packet_path),
        "reviewer": reviewer,
        "decisions": decisions,
    }


def _evaluate(
    tmp_path: Path,
    freeze_path: Path,
    mapping_path: Path,
    packet_path: Path,
    review_one: dict[str, object],
    review_two: dict[str, object],
) -> tuple[dict[str, object], Path]:
    review_one_path = tmp_path / "review-one.json"
    review_two_path = tmp_path / "review-two.json"
    summary_path = tmp_path / "summary.json"
    admission_path = tmp_path / "admission.json"
    _write(review_one_path, review_one)
    _write(review_two_path, review_two)
    summary = APP.evaluate(
        freeze_path,
        mapping_path,
        packet_path,
        [review_one_path, review_two_path],
        summary_path,
        admission_path,
    )
    return summary, admission_path


def test_freeze_hides_rank_and_binds_private_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _package, freeze_path, mapping_path, packet_path, receipt = _freeze(
        tmp_path, monkeypatch
    )
    packet = json.loads(packet_path.read_text())

    assert receipt["status"] == "FROZEN_FOR_SEPARATE_REVIEW"
    assert receipt["retained_count"] == 6
    assert receipt["candidate_count"] == 20
    assert receipt["accepted_count"] == 0
    assert receipt["baseline_raw_file_sha256"] == APP.EXPECTED_RAW_FILE_SHA256
    assert receipt["baseline_intrinsic_package_sha256"] == APP.EXPECTED_INTRINSIC_PACKAGE_SHA256
    assert APP.EXPECTED_RAW_FILE_SHA256 != APP.EXPECTED_INTRINSIC_PACKAGE_SHA256
    assert APP.package_content_sha256(_package) == _oracle_intrinsic(_package)
    assert receipt["contract_a_handoff_sha256"] == APP.EXPECTED_CONTRACT_A_HANDOFF_SHA256
    assert APP.hash_file(mapping_path) == receipt["private_mapping_sha256"]
    assert APP.hash_file(packet_path) == receipt["private_review_packet_sha256"]
    assert len(packet["rows"]) == 6
    assert all(
        set(row) == {"candidate_alias", "proposition_text", "passage_text"}
        for row in packet["rows"]
    )
    assert json.loads(freeze_path.read_text()) == receipt


def test_mixed_exact_review_that_beats_rank1_supports_bounded_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _package, freeze_path, mapping_path, packet_path, _receipt = _freeze(
        tmp_path, monkeypatch
    )
    mapping = json.loads(mapping_path.read_text())
    non_rank1 = next(
        row["candidate_alias"] for row in mapping["rows"] if row["nomination_rank"] == 2
    )
    accepted = {non_rank1}
    one = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-one",
        accepted_aliases=accepted,
    )
    two = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-two",
        accepted_aliases=accepted,
    )

    summary, admission_path = _evaluate(
        tmp_path, freeze_path, mapping_path, packet_path, one, two
    )

    assert summary["primary_disposition"] is None
    assert summary["research_state"] == "CONTINUE_TO_REPLAY"
    assert summary["bounded_result"] == "POSITIVE_ADMISSION_REVIEW_GATE_PASSED"
    assert summary["exact_review_agreement"] is True
    assert summary["consensus_counts"]["accepted"] == 1
    assert summary["weak_controls"]["rank1_would_match_consensus"] is False
    admission = json.loads(admission_path.read_text())
    assert admission["schema"] == APP.ADMISSION_SCHEMA
    assert len(admission["decisions"]) == 6
    assert sum(row["decision"] == "accepted" for row in admission["decisions"]) == 1


def test_zero_accepted_falsifies_admission_only_for_frozen_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _package, freeze_path, mapping_path, packet_path, _receipt = _freeze(
        tmp_path, monkeypatch
    )
    one = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-one",
        accepted_aliases=set(),
    )
    two = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-two",
        accepted_aliases=set(),
    )

    summary, admission_path = _evaluate(
        tmp_path, freeze_path, mapping_path, packet_path, one, two
    )

    assert summary["primary_disposition"] == "FALSIFIED"
    assert summary["bounded_result"] == "ADMISSION_ONLY_FALSIFIED_FOR_FROZEN_PACKET"
    assert not admission_path.exists()


def test_rank1_equivalence_is_inconclusive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _package, freeze_path, mapping_path, packet_path, _receipt = _freeze(
        tmp_path, monkeypatch
    )
    mapping = json.loads(mapping_path.read_text())
    rank1 = {
        row["candidate_alias"] for row in mapping["rows"] if row["nomination_rank"] == 1
    }
    one = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-one",
        accepted_aliases=rank1,
    )
    two = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-two",
        accepted_aliases=rank1,
    )

    summary, admission_path = _evaluate(
        tmp_path, freeze_path, mapping_path, packet_path, one, two
    )

    assert summary["primary_disposition"] == "INCONCLUSIVE"
    assert summary["bounded_result"] == "RANK1_WEAK_CONTROL_NOT_DISCRIMINATED"
    assert not admission_path.exists()


def test_review_disagreement_is_inconclusive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _package, freeze_path, mapping_path, packet_path, _receipt = _freeze(
        tmp_path, monkeypatch
    )
    mapping = json.loads(mapping_path.read_text())
    alias = mapping["rows"][0]["candidate_alias"]
    one = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-one",
        accepted_aliases={alias},
    )
    two = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-two",
        accepted_aliases=set(),
    )

    summary, admission_path = _evaluate(
        tmp_path, freeze_path, mapping_path, packet_path, one, two
    )

    assert summary["primary_disposition"] == "INCONCLUSIVE"
    assert summary["bounded_result"] == "REVIEW_DISAGREEMENT"
    assert summary["review_disagreement_count"] == 1
    assert not admission_path.exists()


def test_replay_verifier_proves_only_admission_state_changed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package, freeze_path, mapping_path, packet_path, _receipt = _freeze(
        tmp_path, monkeypatch
    )
    mapping = json.loads(mapping_path.read_text())
    non_rank1 = next(
        row["candidate_alias"] for row in mapping["rows"] if row["nomination_rank"] == 2
    )
    one = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-one",
        accepted_aliases={non_rank1},
    )
    two = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-two",
        accepted_aliases={non_rank1},
    )
    summary, admission_path = _evaluate(
        tmp_path, freeze_path, mapping_path, packet_path, one, two
    )
    assert summary["primary_disposition"] is None
    assert summary["research_state"] == "CONTINUE_TO_REPLAY"

    admission = json.loads(admission_path.read_text())
    decisions = {
        (row["proposition_id"], row["passage_id"]): row["decision"]
        for row in admission["decisions"]
    }
    admitted = copy.deepcopy(package)
    for row in admitted["candidates"]:
        key = (row["proposition_id"], row["passage_id"])
        if key in decisions:
            row["admission_state"] = decisions[key]
    admitted["package_sha256"] = APP.package_content_sha256(admitted)

    baseline_path = tmp_path / "baseline-replay.json"
    run_one_path = tmp_path / "run-one.json"
    run_two_path = tmp_path / "run-two.json"
    receipt_path = tmp_path / "replay-receipt.json"
    _write(baseline_path, package)
    _write(run_one_path, admitted)
    _write(run_two_path, admitted)

    receipt = APP.verify_replay(
        baseline_path,
        run_one_path,
        run_two_path,
        admission_path,
        receipt_path,
    )

    assert receipt["status"] == "PASS"
    assert receipt["byte_identical_replay"] is True
    assert receipt["only_retained_admission_state_changed"] is True
    assert receipt["admission_states_equal_sidecar"] is True


def test_evaluate_rejects_review_packet_field_leak(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _package, freeze_path, mapping_path, packet_path, receipt = _freeze(
        tmp_path, monkeypatch
    )
    packet = json.loads(packet_path.read_text())
    packet["rows"][0]["nomination_rank"] = 1
    _write(packet_path, packet)
    receipt["private_review_packet_sha256"] = APP.hash_file(packet_path)
    _write(freeze_path, receipt)

    with pytest.raises(APP.ApparatusError, match="leaked or omitted"):
        APP.evaluate(
            freeze_path,
            mapping_path,
            packet_path,
            [tmp_path / "unused-review-one.json", tmp_path / "unused-review-two.json"],
            tmp_path / "summary.json",
            tmp_path / "admission.json",
        )


def test_replay_verifier_rejects_non_admission_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package, freeze_path, mapping_path, packet_path, _receipt = _freeze(
        tmp_path, monkeypatch
    )
    mapping = json.loads(mapping_path.read_text())
    non_rank1 = next(
        row["candidate_alias"] for row in mapping["rows"] if row["nomination_rank"] == 2
    )
    one = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-one",
        accepted_aliases={non_rank1},
    )
    two = _review(
        packet_path,
        mapping_path,
        reviewer="reviewer-two",
        accepted_aliases={non_rank1},
    )
    summary, admission_path = _evaluate(
        tmp_path, freeze_path, mapping_path, packet_path, one, two
    )
    assert summary["research_state"] == "CONTINUE_TO_REPLAY"

    admission = json.loads(admission_path.read_text())
    decisions = {
        (row["proposition_id"], row["passage_id"]): row["decision"]
        for row in admission["decisions"]
    }
    admitted = copy.deepcopy(package)
    for row in admitted["candidates"]:
        key = (row["proposition_id"], row["passage_id"])
        if key in decisions:
            row["admission_state"] = decisions[key]
    admitted["candidates"][0]["text"] = "mutated non-admission state"
    admitted["package_sha256"] = APP.package_content_sha256(admitted)

    baseline_path = tmp_path / "baseline-drift.json"
    run_one_path = tmp_path / "run-one-drift.json"
    run_two_path = tmp_path / "run-two-drift.json"
    _write(baseline_path, package)
    _write(run_one_path, admitted)
    _write(run_two_path, admitted)

    with pytest.raises(APP.ApparatusError, match="outside retained admission_state"):
        APP.verify_replay(
            baseline_path,
            run_one_path,
            run_two_path,
            admission_path,
            tmp_path / "drift-receipt.json",
        )


def test_raw_file_substitution_preserves_semantics_but_fails_raw_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _baseline(monkeypatch)
    path = tmp_path / "different-serialization.json"
    path.write_bytes(_oracle_bytes(package) + b" \n")
    decoded = json.loads(path.read_bytes())
    assert decoded == package
    assert _oracle_intrinsic(decoded) == APP.EXPECTED_INTRINSIC_PACKAGE_SHA256
    assert APP.package_content_sha256(decoded) == decoded["package_sha256"]
    assert _oracle_hash(path.read_bytes()) != APP.EXPECTED_RAW_FILE_SHA256
    out = tmp_path / "not-produced"
    with pytest.raises(APP.ApparatusError, match="raw-file identity mismatch"):
        APP.freeze(path, out)
    assert not out.exists()


def test_resealed_payload_substitution_fails_frozen_raw_and_intrinsic_bindings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _baseline(monkeypatch)
    package["candidates"][0]["text"] = "synthetic substituted payload"
    package["package_sha256"] = _oracle_intrinsic(package)
    assert APP.package_content_sha256(package) == package["package_sha256"]
    assert package["package_sha256"] != APP.EXPECTED_INTRINSIC_PACKAGE_SHA256
    path = tmp_path / "resealed-substitution.json"
    path.write_bytes(_oracle_bytes(package))
    out = tmp_path / "not-produced"
    with pytest.raises(APP.ApparatusError, match="raw-file identity mismatch"):
        APP.freeze(path, out)
    assert not out.exists()
    # Independent payload gate, without the outer raw-file gate short-circuit.
    with pytest.raises(APP.ApparatusError, match="intrinsic package identity mismatch"):
        APP._validate_baseline_package(package)


def test_forged_embedded_identity_fails_intrinsic_recomputation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _baseline(monkeypatch)
    package["package_sha256"] = "sha256:" + "f" * 64
    path = tmp_path / "forged-embedded.json"
    path.write_bytes(_oracle_bytes(package))
    assert APP.package_content_sha256(package) != package["package_sha256"]
    out = tmp_path / "not-produced"
    with pytest.raises(APP.ApparatusError, match="raw-file identity mismatch"):
        APP.freeze(path, out)
    # Rebind only the synthetic outer byte gate to reach the independent intrinsic
    # recomputation gate. The decisive real input never uses a rebound expectation.
    monkeypatch.setattr(APP, "EXPECTED_RAW_FILE_SHA256", _oracle_hash(path.read_bytes()))
    with pytest.raises(APP.ApparatusError, match="intrinsic payload digest"):
        APP.freeze(path, out)
    assert not out.exists()


def test_noncanonical_bytes_fail_even_if_synthetic_raw_expectation_is_rebound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _baseline(monkeypatch)
    path = tmp_path / "noncanonical.json"
    path.write_text(json.dumps(package, indent=2) + "\n")
    monkeypatch.setattr(APP, "EXPECTED_RAW_FILE_SHA256", _oracle_hash(path.read_bytes()))
    out = tmp_path / "not-produced"
    with pytest.raises(APP.ApparatusError, match="not canonical V1 package bytes"):
        APP.freeze(path, out)
    assert not out.exists()


@pytest.mark.parametrize("cross_wiring", ["raw-to-intrinsic", "intrinsic-to-raw", "swap"])
def test_cross_wired_expected_identities_fail_in_the_intended_domain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cross_wiring: str,
) -> None:
    package = _baseline(monkeypatch)
    raw, intrinsic = APP.EXPECTED_RAW_FILE_SHA256, APP.EXPECTED_INTRINSIC_PACKAGE_SHA256
    assert raw != intrinsic
    path = tmp_path / "correct.json"
    path.write_bytes(_oracle_bytes(package))
    if cross_wiring in {"raw-to-intrinsic", "swap"}:
        monkeypatch.setattr(APP, "EXPECTED_INTRINSIC_PACKAGE_SHA256", raw)
    if cross_wiring in {"intrinsic-to-raw", "swap"}:
        monkeypatch.setattr(APP, "EXPECTED_RAW_FILE_SHA256", intrinsic)
    expected_reason = (
        "intrinsic package identity mismatch"
        if cross_wiring == "raw-to-intrinsic"
        else "raw-file identity mismatch"
    )
    out = tmp_path / "not-produced"
    with pytest.raises(APP.ApparatusError, match=expected_reason):
        APP.freeze(path, out)
    assert not out.exists()


def _conflated_predecessor_identity_gate(package: dict[str, object]) -> list[object]:
    """Intentionally wrong: reproduce the predecessor's raw/intrinsic category error."""
    if package.get("package_sha256") != APP.EXPECTED_RAW_FILE_SHA256:
        raise APP.ApparatusError("weak control: embedded intrinsic compared with expected raw")
    if APP.package_content_sha256(package) != APP.EXPECTED_RAW_FILE_SHA256:
        raise APP.ApparatusError("weak control: intrinsic recomputation compared with expected raw")
    return [row for row in package["candidates"] if row["selection_state"] == "retained"]


def test_conflated_implementation_fails_the_same_positive_freeze_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _baseline(monkeypatch)
    path = tmp_path / "positive-control.json"
    path.write_bytes(_oracle_bytes(package))
    corrected_out = tmp_path / "corrected"
    corrected = APP.freeze(path, corrected_out)
    assert corrected["status"] == "FROZEN_FOR_SEPARATE_REVIEW"
    assert all(
        (corrected_out / name).is_file()
        for name in (
            "FREEZE-RECEIPT.PUBLIC.json",
            "PRIVATE-MAPPING.json",
            "PRIVATE-REVIEW-PACKET.json",
        )
    )
    monkeypatch.setattr(APP, "_validate_baseline_package", _conflated_predecessor_identity_gate)
    conflated_out = tmp_path / "conflated"
    with pytest.raises(APP.ApparatusError, match="embedded intrinsic compared with expected raw"):
        APP.freeze(path, conflated_out)
    assert not conflated_out.exists()


@pytest.mark.parametrize("artifact", ["receipt", "mapping"])
@pytest.mark.parametrize("field", ["baseline_raw_file_sha256", "baseline_intrinsic_package_sha256"])
def test_evaluator_requires_each_frozen_identity_domain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    artifact: str,
    field: str,
) -> None:
    _package, freeze_path, mapping_path, packet_path, receipt = _freeze(tmp_path, monkeypatch)
    if artifact == "receipt":
        receipt[field] = "sha256:" + "f" * 64
    else:
        mapping = json.loads(mapping_path.read_bytes())
        mapping[field] = "sha256:" + "f" * 64
        _write(mapping_path, mapping)
        receipt["private_mapping_sha256"] = APP.hash_file(mapping_path)
    _write(freeze_path, receipt)
    with pytest.raises(APP.ApparatusError, match="authority"):
        APP.evaluate(
            freeze_path,
            mapping_path,
            packet_path,
            [tmp_path / "unused-one.json", tmp_path / "unused-two.json"],
            tmp_path / "summary.json",
            tmp_path / "admission.json",
        )
    assert not (tmp_path / "summary.json").exists()
    assert not (tmp_path / "admission.json").exists()


def test_mapping_retained_set_tamper_rejected_even_with_updated_file_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _package, freeze_path, mapping_path, packet_path, receipt = _freeze(tmp_path, monkeypatch)
    mapping = json.loads(mapping_path.read_bytes())
    mapping["rows"][0]["nomination_rank"] = 42
    _write(mapping_path, mapping)
    receipt["private_mapping_sha256"] = APP.hash_file(mapping_path)
    _write(freeze_path, receipt)
    with pytest.raises(APP.ApparatusError, match="retained-set binding mismatch"):
        APP.evaluate(
            freeze_path,
            mapping_path,
            packet_path,
            [tmp_path / "unused-one.json", tmp_path / "unused-two.json"],
            tmp_path / "summary.json",
            tmp_path / "admission.json",
        )


@pytest.mark.parametrize("stale_output", ["freeze", "summary", "admission", "replay"])
def test_stale_outputs_are_refused_without_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stale_output: str,
) -> None:
    package, freeze_path, mapping_path, packet_path, _receipt = _freeze(tmp_path, monkeypatch)
    sentinel_bytes = b"preserved first output\n"
    if stale_output == "freeze":
        sentinel = freeze_path.parent / "sentinel"
        sentinel.write_bytes(sentinel_bytes)
        with pytest.raises(APP.ApparatusError, match="non-empty freeze output"):
            APP.freeze(tmp_path / "baseline.json", freeze_path.parent)
    elif stale_output in {"summary", "admission"}:
        sentinel = tmp_path / f"{stale_output}.json"
        sentinel.write_bytes(sentinel_bytes)
        with pytest.raises(APP.ApparatusError, match=f"existing {stale_output} output"):
            APP.evaluate(
                freeze_path,
                mapping_path,
                packet_path,
                [tmp_path / "unused-one.json", tmp_path / "unused-two.json"],
                tmp_path / "summary.json",
                tmp_path / "admission.json",
            )
    else:
        sentinel = tmp_path / "replay.json"
        sentinel.write_bytes(sentinel_bytes)
        with pytest.raises(APP.ApparatusError, match="existing replay receipt"):
            APP.verify_replay(
                tmp_path / "baseline.json",
                tmp_path / "unused-one.json",
                tmp_path / "unused-two.json",
                tmp_path / "unused-admission.json",
                sentinel,
            )
    assert sentinel.read_bytes() == sentinel_bytes
    assert _oracle_intrinsic(package) == APP.EXPECTED_INTRINSIC_PACKAGE_SHA256


@pytest.mark.parametrize(
    "malformation", ["extra-field", "support-reason", "missing-row", "duplicate-alias"]
)
def test_exact_reviewer_rows_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    malformation: str,
) -> None:
    _package, _freeze_path, mapping_path, packet_path, _receipt = _freeze(tmp_path, monkeypatch)
    review = _review(packet_path, mapping_path, reviewer="synthetic", accepted_aliases=set())
    if malformation == "extra-field":
        review["decisions"][0]["support"] = True
    elif malformation == "support-reason":
        review["decisions"][0]["reason"] = "supports"
    elif malformation == "missing-row":
        review["decisions"].pop()
    else:
        review["decisions"][1]["candidate_alias"] = review["decisions"][0]["candidate_alias"]
    review_path = tmp_path / "invalid-review.json"
    _write(review_path, review)
    aliases = {row["candidate_alias"] for row in json.loads(mapping_path.read_bytes())["rows"]}
    with pytest.raises(APP.ApparatusError):
        APP._load_and_validate_review(
            review_path, packet_sha256=APP.hash_file(packet_path), aliases=aliases
        )


def test_admit_all_remains_inconclusive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _package, freeze_path, mapping_path, packet_path, _receipt = _freeze(tmp_path, monkeypatch)
    aliases = {row["candidate_alias"] for row in json.loads(mapping_path.read_bytes())["rows"]}
    one = _review(packet_path, mapping_path, reviewer="synthetic-one", accepted_aliases=aliases)
    two = _review(packet_path, mapping_path, reviewer="synthetic-two", accepted_aliases=aliases)
    summary, admission_path = _evaluate(tmp_path, freeze_path, mapping_path, packet_path, one, two)
    assert summary["primary_disposition"] == "INCONCLUSIVE"
    assert summary["bounded_result"] == "NO_NEGATIVE_DISCRIMINATION_HEADROOM"
    assert not admission_path.exists()


def _replay_specimen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, Path]:
    package = _baseline(monkeypatch)
    admitted = copy.deepcopy(package)
    retained = [row for row in admitted["candidates"] if row["selection_state"] == "retained"]
    decisions = []
    for index, row in enumerate(retained):
        row["admission_state"] = "accepted" if index == 1 else "rejected"
        decisions.append(
            {
                "proposition_id": row["proposition_id"],
                "passage_id": row["passage_id"],
                "decision": row["admission_state"],
            }
        )
    admitted["package_sha256"] = _oracle_intrinsic(admitted)
    paths = tuple(
        tmp_path / name for name in ("baseline.json", "run1.json", "run2.json", "sidecar.json")
    )
    for path, value in zip(
        paths,
        (package, admitted, admitted, {"schema": APP.ADMISSION_SCHEMA, "decisions": decisions}),
        strict=True,
    ):
        path.write_bytes(_oracle_bytes(value))
    return paths


def test_raw_byte_replay_inequality_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline, one, two, sidecar = _replay_specimen(tmp_path, monkeypatch)
    different = json.loads(two.read_bytes())
    different["candidates"][1]["admission_state"] = "needs-review"
    different["package_sha256"] = _oracle_intrinsic(different)
    two.write_bytes(_oracle_bytes(different))
    assert APP._normalized_without_admission(
        json.loads(one.read_bytes())
    ) == APP._normalized_without_admission(different)
    assert APP.package_content_sha256(different) == different["package_sha256"]
    assert one.read_bytes() != two.read_bytes()
    out = tmp_path / "replay-receipt.json"
    with pytest.raises(APP.ApparatusError, match="not raw-byte-identical"):
        APP.verify_replay(baseline, one, two, sidecar, out)
    assert not out.exists()


def test_replay_baseline_also_requires_raw_file_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline, one, two, sidecar = _replay_specimen(tmp_path, monkeypatch)
    baseline.write_bytes(baseline.read_bytes() + b" \n")
    out = tmp_path / "replay-receipt.json"
    with pytest.raises(APP.ApparatusError, match="raw-file identity mismatch"):
        APP.verify_replay(baseline, one, two, sidecar, out)
    assert not out.exists()
