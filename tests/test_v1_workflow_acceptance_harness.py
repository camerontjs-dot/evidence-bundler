"""Apparatus unit checks with fabricated records; no EB executions or semantic judgments."""
import importlib.util
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/qualification/run_v1_workflow_acceptance.py"
SPEC = importlib.util.spec_from_file_location("workflow_harness", SCRIPT)
h = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h)


def records():
    package = {"primary_targets": [{"proposition_id": "target"}], "candidates": [
        {"proposition_id": "target", "passage_id": "passage", "selection_state": "retained",
         "admission_state": "needs-review"},
        {"proposition_id": "target", "passage_id": "decoy", "selection_state": "excluded",
         "admission_state": "not_applicable"}], "package_sha256": "before"}
    entry = {"case_id": "p01", "bindings": {"input_sha256": "frozen"}}
    review = {"schema": "eb-workflow-review-v1", "case_id": "p01",
              "bindings": deepcopy(entry["bindings"]), "reviewer": "Unit test",
              "elapsed_seconds": 1, "manual_friction": "Fabricated record; none observed.",
              "coverage_notes": {"target": "Unit fixture coverage note."}, "decisions": [
                  {"proposition_id": "target", "passage_id": "passage", "decision": "accepted",
                   "reason": "Fabricated rationale for validation only."}]}
    return package, entry, review


@pytest.mark.parametrize("mutation", [
    lambda r: r["bindings"].update(input_sha256="changed"),
    lambda r: r.update(case_id="p02"),
    lambda r: r.update(schema="other"),
    lambda r: r.update(extra=True),
    lambda r: r["decisions"].clear(),
    lambda r: r["decisions"].append(deepcopy(r["decisions"][0])),
    lambda r: r["decisions"][0].update(passage_id="decoy"),
    lambda r: r["decisions"][0].update(decision="supports"),
    lambda r: r["decisions"][0].update(reason="  "),
    lambda r: r["coverage_notes"].clear(),
    lambda r: r["coverage_notes"].update(target=""),
    lambda r: r.update(elapsed_seconds=True),
    lambda r: r.update(elapsed_seconds=float("nan")),
    lambda r: r.update(elapsed_seconds=-1),
    lambda r: r.update(manual_friction=""),
])
def test_review_rejects_incomplete_or_stale_records(mutation):
    package, entry, review = records()
    mutation(review)
    with pytest.raises(ValueError):
        h.check_review(review, entry, package)


def test_exact_review_and_honest_empty_are_legal():
    package, entry, review = records()
    assert h.check_review(review, entry, package) == {("target", "passage"): "accepted"}
    package["candidates"] = []
    review["decisions"] = []
    assert h.check_review(review, entry, package) == {}


def test_replay_permits_only_admission_changes():
    before, _, _ = records()
    after = deepcopy(before)
    after["package_sha256"] = "after"
    after["candidates"][0]["admission_state"] = "accepted"
    decisions = {("target", "passage"): "accepted"}
    h.check_replay(before, after, decisions)
    after["candidates"][1]["selection_state"] = "retained"
    with pytest.raises(ValueError, match="non-admission replay drift"):
        h.check_replay(before, after, decisions)


@pytest.mark.parametrize("changed", ["input", "native", "inspect", "packet"])
def test_original_snapshot_changes_block_replay(tmp_path, changed):
    paths = {"input": tmp_path / "inputs/p01.contract-a.json",
             "native": tmp_path / f"unreviewed/p01/{h.NATIVE}",
             "inspect": tmp_path / "logs/inspect.stdout.txt",
             "packet": tmp_path / "review-packets/p01.md"}
    for path in paths.values():
        h.write(path, b"fabricated snapshot\n")
    state = {"kit": str(h.KIT), "kit_freeze_sha256": h.file_sha(h.KIT / "FREEZE.json"),
             "helper_sha256": h.file_sha(SCRIPT), "inspect_sha256": h.file_sha(paths["inspect"]),
             "cases": [{"case_id": "p01", "bindings": {
                 "input_sha256": h.file_sha(paths["input"]),
                 "review_packet_sha256": h.file_sha(paths["packet"])},
                 "unreviewed_files": h.hashes(tmp_path / "unreviewed/p01")}]}
    h.write(tmp_path / "PREPARED.json", state)
    h.checked_state(tmp_path)
    paths[changed].write_bytes(b"changed\n")
    with pytest.raises(ValueError):
        h.checked_state(tmp_path)


def test_frozen_kit_rejects_edits_and_extra_members(tmp_path):
    kit = tmp_path / "kit"
    shutil.copytree(h.KIT, kit)
    h.verify_kit(kit)
    extra = kit / "extra.txt"
    extra.write_text("unexpected")
    with pytest.raises(ValueError, match="missing/extra"):
        h.verify_kit(kit)
    extra.unlink()
    (kit / "inputs/p01.contract-a.json").write_text("changed")
    with pytest.raises(ValueError, match="kit changed"):
        h.verify_kit(kit)


def test_checkout_detection_uses_git_authority_not_marker_presence(tmp_path):
    marker = tmp_path / "marker"
    (marker / ".git").mkdir(parents=True)
    assert not h.inside_checkout(marker / "not-created")
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repository)], check=True)
    assert h.inside_checkout(repository / "not-created")


@pytest.mark.parametrize("mode, expected_code", [("honest", 0), ("reject", 2), ("accept", 2)])
def test_evaluate_mode_exit_and_preserved_result(tmp_path, monkeypatch, mode, expected_code):
    """Exercise main/evaluate on fabricated frozen state, never real product output."""
    expected = h.read(h.KIT / "EXPECTED-OPPORTUNITIES.json")
    cases = []
    for case in expected["cases"]:
        counts = {t: int((mode == "accept" and t != "clm-p08") or (
            mode == "honest" and t in expected["mandatory_adequate_targets"]))
            for t in case["targets"]}
        cases.append({"case_id": case["case_id"],
                      "targets": {t: {"accepted": n} for t, n in counts.items()},
                      "all_targets_have_admitted_evidence": all(counts.values())})
    h.write(tmp_path / "PREPARED.json", {"fabricated": True})
    h.write(tmp_path / "reviews/p01.json", {"fabricated": True})
    h.write(tmp_path / "replay/reviews/p01.json", {"fabricated": True})
    h.write(tmp_path / "replay/REVIEW-FREEZE.json", {
        "prepared_sha256": h.file_sha(tmp_path / "PREPARED.json"),
        "review_hashes": h.hashes(tmp_path / "reviews")})
    h.write(tmp_path / "replay/COVERAGE.json", {"cases": cases})
    h.write(tmp_path / "replay/RESULT.json", {
        "review_freeze_sha256": h.file_sha(tmp_path / "replay/REVIEW-FREEZE.json"),
        "output_hashes": {}, "coverage_sha256": h.file_sha(tmp_path / "replay/COVERAGE.json")})
    monkeypatch.setattr(h, "checked_state", lambda _: {"kit": str(h.KIT), "kit_closure": "unit"})
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "evaluate", "--run-dir", str(tmp_path)])
    assert h.main() == expected_code
    result_path = tmp_path / "evaluate/RESULT.json"
    result_bytes = result_path.read_bytes()
    result = h.read(result_path)
    assert result["disposition"].startswith("PASS" if expected_code == 0 else "FAIL")
    assert not result["fabricated_gate_controls"]["always_reject"]["passed"]
    assert not result["fabricated_gate_controls"]["always_accept"]["passed"]
    assert not (tmp_path / "evaluate/FIRST-FAILURE.json").exists()
    assert h.main() == 1  # Existing phase is never retried or overwritten.
    assert result_path.read_bytes() == result_bytes
