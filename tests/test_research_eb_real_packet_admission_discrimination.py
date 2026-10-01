from __future__ import annotations

import copy
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
    package["package_sha256"] = APP.package_content_sha256(package)
    monkeypatch.setattr(APP, "EXPECTED_PACKAGE_SHA256", package["package_sha256"])
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

    assert summary["primary_disposition"] == "SUPPORTED FOR PROMOTION"
    assert summary["bounded_result"] == "BOUNDED_POSITIVE_ADMISSION_DISCRIMINATION"
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
    assert summary["primary_disposition"] == "SUPPORTED FOR PROMOTION"

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
