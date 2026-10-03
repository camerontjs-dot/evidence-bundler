"""Verify RC2 is RC1 apparatus plus only the preregistered service-version substitution."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREDECESSOR_COMMIT = "ac948782db183bd209f0907cdd7c6e04d13bf15a"
PREDECESSOR_DIR = "research/eb_root_generation_prereq_rc1_20261003"

IDENTICAL = [
    "AUTHORING-RUBRIC.json",
    "PROFILE-SURFACE.json",
    "PROFILE-WRITER-TASK.md",
    "CUSTODY-SCHEMA.json",
    "LAUNCH-STATUS.json",
    "run_writer.py",
    "check_execution.py",
    "validate_setup.py",
]
VERSION_ONLY = [
    "BOOTSTRAP-MANIFEST.json",
    "WRITER-TRANSPORT.json",
]


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def predecessor_bytes(name: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{PREDECESSOR_COMMIT}:{PREDECESSOR_DIR}/{name}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return result.stdout


def validate() -> dict:
    control = json.loads((HERE / "PREDECESSOR-CONTROL.json").read_text(encoding="utf-8"))
    need(control["predecessor"]["frozen_source_commit"] == PREDECESSOR_COMMIT, "predecessor commit")

    for name in IDENTICAL:
        need((HERE / name).read_bytes() == predecessor_bytes(name), "apparatus drift: " + name)

    old = b'"0.34.4"'
    new = b'"0.35.1"'
    for name in VERSION_ONLY:
        before = predecessor_bytes(name)
        after = (HERE / name).read_bytes()
        need(before.count(old) == 1, "predecessor service-version multiplicity: " + name)
        need(before.count(new) == 0, "predecessor already contains successor version: " + name)
        expected = before.replace(old, new)
        need(after == expected, "non-version drift: " + name)
        need(after.count(new) == 1 and after.count(old) == 0, "successor service-version multiplicity: " + name)

    return {
        "successor_control": "PASS",
        "predecessor_source_commit": PREDECESSOR_COMMIT,
        "identical_apparatus_files": len(IDENTICAL),
        "version_only_files": VERSION_ONLY,
        "controlled_substitution": "0.34.4 -> 0.35.1",
        "generation_capability": "UNKNOWN",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
