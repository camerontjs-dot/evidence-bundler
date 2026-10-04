"""Mechanical validation for the frozen classifier qualification setup."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

EXPECTED_IDS = {
    "BASELINE_PASS",
    "PROFILE_MISSING_CALIBRATION_OUTPUT",
    "PROFILE_MISSING_DECISIVE_OUTPUT",
    "PROFILE_MISSING_CALIBRATION_DECISION",
    "PROFILE_WRONG_DECISIVE_DECISION_ENUM",
    "PROFILE_MALFORMED_REVIEW_JSON",
    "PROFILE_PRIMARY_CONFIG_DRIFT",
    "PROFILE_EVALUATOR_CONFIG_DRIFT",
    "PROFILE_EVALUATOR_PROMPT_MISSING_UNCERTAIN",
    "PROFILE_FILE_MISSING",
    "CUSTODY_REQUEST_HASH_MISMATCH",
    "CUSTODY_RESPONSE_HASH_MISMATCH",
    "CUSTODY_RESPONSE_INCOMPLETE",
    "CUSTODY_RESPONSE_TRUNCATED",
    "CUSTODY_RUNTIME_DIGEST_MISMATCH",
    "CUSTODY_PROFILE_HASH_MISMATCH",
    "CONTAMINATION_FORBIDDEN_SOURCE",
    "APPARATUS_RAW_KEYERROR_OUTPUT",
}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def validate() -> dict:
    witness = read("RC2-WITNESS.PUBLIC.json")
    need(witness["predecessor_pr"] == 127, "predecessor PR")
    need(witness["predecessor_final_head"] == "534f6801998d96c72783fa1895d6a404dec7ec1a", "predecessor head")
    need(witness["predecessor_checker_blob"] == "21a3fe9e9dbb90cb8894e8c1ee36d78a61e99a74", "predecessor checker")
    need(witness["frozen_checker_reason"] == "'output'", "RC2 witness reason")
    need(witness["response_complete"] is True and witness["truncated"] is False, "RC2 complete response witness")
    need(witness["five_profile_files_extracted"] is True, "RC2 five-file witness")

    matrix = read("MUTATION-MATRIX.json")
    rows = matrix["cases"]
    ids = [row["id"] for row in rows]
    need(len(ids) == len(set(ids)), "duplicate case id")
    need(set(ids) == EXPECTED_IDS, "matrix coverage drift")
    need(len(rows) == 18, "frozen matrix count")

    allowed_categories = {None, "PROFILE_CONFIGURATION", "CUSTODY_VERIFICATION", "CONTAMINATION", "APPARATUS_ERROR"}
    allowed_dispositions = {None, "BLOCKED_PROFILE_CONFIGURATION", "BLOCKED_CUSTODY_VERIFICATION", "CONTAMINATED", "INCONCLUSIVE"}
    need(all(row["expected_category"] in allowed_categories for row in rows), "invalid expected category")
    need(all(row["expected_disposition"] in allowed_dispositions for row in rows), "invalid expected disposition")

    surface_blob = subprocess.run(
        ["git", "hash-object", str(HERE / "PROFILE-SURFACE.json")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    transport_blob = subprocess.run(
        ["git", "hash-object", str(HERE / "WRITER-TRANSPORT.json")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    need(surface_blob == "a97d2d196f64960ff5f17c999a3ab70d2309d549", "RC2 profile surface drift")
    need(transport_blob == "3ae2788e3796f6853e17246ff12ae464c497b59e", "RC2 transport drift")

    candidate_path = HERE / "CANDIDATE.json"
    candidate_checked = False
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
        for relative, blob in candidate["frozen_blobs"].items():
            path = ROOT / relative
            need(path.is_file() and not path.is_symlink(), "missing frozen file: " + relative)
            observed = subprocess.run(
                ["git", "hash-object", str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            need(observed == blob, "frozen blob drift: " + relative)
        candidate_checked = True

    return {
        "mechanical_setup": "PASS",
        "matrix_cases": 18,
        "rc2_witness_bound": True,
        "rc2_profile_surface_reused": True,
        "rc2_transport_reused": True,
        "candidate_closure_checked": candidate_checked,
        "model_or_network_execution": "NOT_RUN",
        "generation_capability": "UNKNOWN",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
