"""Validate the RC3 context-free execution candidate without invoking the writer."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RC3_SOURCE = "55c2940d6822a6c666441f61900b2cadcfbde046"
RC3_DIR = "research/eb_root_generation_prereq_rc3_apparatus_20261003"

IDENTICAL = [
    "AUTHORING-RUBRIC.json",
    "PROFILE-SURFACE.json",
    "PROFILE-WRITER-TASK.md",
    "BOOTSTRAP-MANIFEST.json",
    "CUSTODY-SCHEMA.json",
    "WRITER-TRANSPORT.json",
    "LAUNCH-STATUS.json",
    "validate_setup.py",
    "check_execution.py",
    "run_writer.py",
]


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def predecessor_bytes(name: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{RC3_SOURCE}:{RC3_DIR}/{name}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout


def read(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def validate() -> dict:
    authority = read("EXECUTION-AUTHORITY.json")
    need(authority["qualified_apparatus"]["source_commit"] == RC3_SOURCE, "qualified RC3 source drift")
    need(
        authority["historical_evidence"]["rc3_apparatus_evidence_head"]
        == "2990f02c330f1b47b5e1138925f1d7df5bfd1a95",
        "RC3 evidence head drift",
    )
    need(
        authority["historical_evidence"]["rc3_apparatus_disposition"]
        == "SUPPORTED_FOR_PREREQUISITE_EXECUTION_CANDIDATE",
        "RC3 apparatus not supported",
    )
    need(authority["setup_task_writer_invocation_authorized"] is False, "setup writer authority leak")
    need(
        authority["future_writer_invocation_authorized_only_after_exact_candidate_gates"] is True,
        "future execution gate missing",
    )

    for name in IDENTICAL:
        need((HERE / name).read_bytes() == predecessor_bytes(name), "qualified RC3 byte drift: " + name)

    status = read("LAUNCH-STATUS.json")
    need(status["execution"] == "NOT_RUN", "execution must be NOT_RUN")
    need(status["profile_writer_attempts_consumed"] == 0, "writer attempt already consumed")
    need(status["custody_attempts_consumed"] == 0, "custody attempt already consumed")
    for field in (
        "semantic_calibration_attempts_authorized",
        "target_generation_attempts_authorized",
        "weak_generator_attempts_authorized",
        "decisive_review_attempts_authorized",
        "tally_attempts_authorized",
    ):
        need(status[field] == 0, field + " must remain zero")

    budget = authority["future_execution_budget"]
    need(budget["profile_writer_attempts"] == 1, "future writer budget")
    need(budget["custody_attempts"] == 1, "future custody budget")
    for field in (
        "semantic_calibration_attempts",
        "target_generation_attempts",
        "weak_generator_attempts",
        "decisive_review_attempts",
        "tally_attempts",
    ):
        need(budget[field] == 0, field + " must remain zero")

    import check_execution
    import run_writer

    need(
        run_writer.SOURCE_FILES
        == [
            "BOOTSTRAP-MANIFEST.json",
            "PROFILE-WRITER-TASK.md",
            "AUTHORING-RUBRIC.json",
            "PROFILE-SURFACE.json",
        ],
        "writer aperture drift",
    )
    need(run_writer.PROFILE_FILES == check_execution.REQUIRED, "writer/checker profile set drift")

    candidate_checked = False
    candidate_path = HERE / "CANDIDATE.json"
    if candidate_path.exists():
        candidate = read("CANDIDATE.json")
        observed_tree = subprocess.run(
            ["git", "rev-parse", candidate["source_commit"] + "^{tree}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        need(observed_tree == candidate["source_tree"], "candidate source tree drift")
        for relative, expected_blob in candidate["frozen_blobs"].items():
            path = ROOT / relative
            need(path.is_file() and not path.is_symlink(), "missing frozen file: " + relative)
            observed_blob = subprocess.run(
                ["git", "hash-object", str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            need(observed_blob == expected_blob, "frozen blob drift: " + relative)
        candidate_checked = True

    return {
        "execution_candidate_validation": "PASS",
        "qualified_rc3_identical_files": len(IDENTICAL),
        "writer_attempts_consumed": 0,
        "custody_attempts_consumed": 0,
        "future_writer_attempts_authorized_after_gates": 1,
        "future_custody_attempts_authorized_after_gates": 1,
        "semantic_and_generation_stage_budgets": 0,
        "candidate_closure_checked": candidate_checked,
        "model_or_network_execution": "NOT_RUN",
        "generation_capability": "UNKNOWN",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
