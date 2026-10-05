"""Validate RC5 as the final full-wire prompt-binding successor."""
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
    "BOOTSTRAP-MANIFEST.json",
    "CUSTODY-SCHEMA.json",
    "WRITER-TRANSPORT.json",
    "LAUNCH-STATUS.json",
    "validate_setup.py",
    "check_execution.py",
    "run_writer.py",
]

REQUIRED_TASK_TOKENS = [
    '"role": "primary"',
    '"input_mode": "root_only_proposal_null"',
    '"role": "semantic_evaluator"',
    '"modes": ["calibration", "decisive"]',
    '"shared_semantic_instructions": true',
    '"proposal_editing": false',
    '"review_schema_file": "REVIEW-SCHEMA.json"',
    "Do not put mode objects inside EVALUATOR-CONFIG.json.",
    "PROFILE_CONFIGURATION",
]


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def rc3_bytes(name: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{RC3_SOURCE}:{RC3_DIR}/{name}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout


def read(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def validate() -> dict:
    authority = read("SUCCESSOR-AUTHORITY.json")
    need(authority["qualified_apparatus_source"] == RC3_SOURCE, "qualified apparatus drift")
    need(authority["predecessor_rc4"]["terminal_head"] == "00e85597e219b56d369d7bc7f1cf99871e7bfe51", "RC4 terminal head drift")
    need(authority["predecessor_rc4"]["checker_code"] == "PROFILE_EVALUATOR_CONFIG_MODES", "RC4 witness drift")
    need(authority["terminal_research_rule"]["profile_failure"] == "FALSIFIED_PROFILE_AUTHORING_RELIABILITY", "terminal rule drift")
    need(authority["setup_writer_invocation_authorized"] is False, "setup writer authority leak")

    for name in IDENTICAL:
        need((HERE / name).read_bytes() == rc3_bytes(name), "RC3 invariant drift: " + name)

    task = (HERE / "PROFILE-WRITER-TASK.md").read_text(encoding="utf-8")
    need(task.encode("utf-8") != rc3_bytes("PROFILE-WRITER-TASK.md"), "task did not change")
    for token in REQUIRED_TASK_TOKENS[:-1]:
        need(token in task, "missing full-wire task token: " + token)

    status = read("LAUNCH-STATUS.json")
    need(status["execution"] == "NOT_RUN", "execution must remain NOT_RUN")
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

    candidate_checked = False
    if (HERE / "CANDIDATE.json").exists():
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
        "successor_control": "PASS",
        "rc3_identical_files": len(IDENTICAL),
        "controlled_change": "PROFILE-WRITER-TASK.md full machine-surface binding",
        "terminal_profile_failure_rule": "FALSIFIED_PROFILE_AUTHORING_RELIABILITY",
        "writer_attempts_consumed": 0,
        "custody_attempts_consumed": 0,
        "semantic_and_generation_budgets": 0,
        "candidate_closure_checked": candidate_checked,
        "model_or_network_execution": "NOT_RUN",
        "generation_capability": "UNKNOWN",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
