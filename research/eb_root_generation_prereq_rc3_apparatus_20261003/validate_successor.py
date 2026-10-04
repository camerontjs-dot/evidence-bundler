"""Verify RC3 apparatus preserves RC2 invariants and only changes diagnostic integration."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RC2_COMMIT = "e850d812036d0eca2ab1c79185bf871a9636684a"
RC2_DIR = "research/eb_root_generation_prereq_rc2_20261003"

IDENTICAL = [
    "AUTHORING-RUBRIC.json",
    "PROFILE-SURFACE.json",
    "PROFILE-WRITER-TASK.md",
    "BOOTSTRAP-MANIFEST.json",
    "CUSTODY-SCHEMA.json",
    "WRITER-TRANSPORT.json",
    "LAUNCH-STATUS.json",
    "validate_setup.py",
]

EXPECTED_CLASSIFIER_SOURCE = "6e666ab20c02a9b9a7ec5e649d16d282bedccb27"
EXPECTED_CLASSIFIER_EVIDENCE = "9da73dc3a9d4d413a55dce6ce48f9774d0a9ec07"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def predecessor_bytes(name: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{RC2_COMMIT}:{RC2_DIR}/{name}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout


def validate() -> dict:
    authority = json.loads((HERE / "APPARATUS-AUTHORITY.json").read_text(encoding="utf-8"))
    need(authority["predecessor_rc2"]["source_commit"] == RC2_COMMIT, "RC2 authority drift")
    classifier = authority["failure_classifier_qualification"]
    need(classifier["source_commit"] == EXPECTED_CLASSIFIER_SOURCE, "classifier source drift")
    need(classifier["evidence_head"] == EXPECTED_CLASSIFIER_EVIDENCE, "classifier evidence drift")
    need(classifier["disposition"] == "SUPPORTED_FOR_APPARATUS_SUCCESSOR", "classifier not supported")
    need(authority["writer_execution_authorized"] is False, "writer authority leak")

    for name in IDENTICAL:
        need((HERE / name).read_bytes() == predecessor_bytes(name), "RC2 invariant drift: " + name)

    matrix_blob = subprocess.run(
        ["git", "hash-object", str(HERE / "MUTATION-MATRIX.json")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    need(matrix_blob == "e68aed2a3435d783a5e6a4c26656f5d85dde421a", "qualified mutation matrix drift")

    import check_execution
    import run_writer

    need(run_writer.SOURCE_FILES == [
        "BOOTSTRAP-MANIFEST.json",
        "PROFILE-WRITER-TASK.md",
        "AUTHORING-RUBRIC.json",
        "PROFILE-SURFACE.json",
    ], "writer source aperture drift")
    need(run_writer.PROFILE_FILES == check_execution.REQUIRED, "writer/checker profile file-set drift")

    raw = check_execution.classify_exception(KeyError("output"))
    need(raw["category"] == "APPARATUS_ERROR", "unexpected exception category")
    need(raw["code"] == "APPARATUS_UNEXPECTED_EXCEPTION", "unexpected exception code")
    need(raw["disposition"] == "INCONCLUSIVE", "unexpected exception disposition")

    disposition, _ = run_writer.normalize_checker_result(raw)
    need(disposition == "INCONCLUSIVE", "launcher unexpected-exception mapping")

    return {
        "successor_control": "PASS",
        "rc2_identical_files": len(IDENTICAL),
        "qualified_classifier_authority": "BOUND",
        "qualified_mutation_matrix": "BOUND",
        "structured_unexpected_exception": "INCONCLUSIVE",
        "writer_execution_authorized": False,
        "generation_capability": "UNKNOWN",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
