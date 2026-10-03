"""Mechanical RC1 prerequisite checks only. No model or semantic execution."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(name: str) -> dict:
    def unique(items):
        result = {}
        for key, value in items:
            need(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    return json.loads((HERE / name).read_text(encoding="utf-8"), object_pairs_hook=unique)


def validate() -> dict:
    rubric = read("AUTHORING-RUBRIC.json")
    surface = read("PROFILE-SURFACE.json")
    bootstrap = read("BOOTSTRAP-MANIFEST.json")
    custody = read("CUSTODY-SCHEMA.json")
    transport = read("WRITER-TRANSPORT.json")
    status = read("LAUNCH-STATUS.json")

    need(rubric["schema"] == "eb-rc2-authoring-rubric-v1", "rubric schema")
    need("uncertain" in rubric["checker_reasons"], "rubric uncertainty reason")
    need("uncertain" in rubric["ineligible_reasons"], "rubric ineligible uncertainty")

    required_files = surface["required_files"]
    need(len(required_files) == 5 and len(set(required_files)) == 5, "five unique profile files")
    need(set(required_files) == {
        "PRIMARY-PROMPT.txt",
        "PRIMARY-CONFIG.json",
        "EVALUATOR-PROMPT.txt",
        "EVALUATOR-CONFIG.json",
        "REVIEW-SCHEMA.json",
    }, "exact profile file set")
    primary_required = surface["primary"]["config_required"]
    need(primary_required["input_mode"] == "root_only_proposal_null", "primary root-only mode")
    need(primary_required["extra_context"] is False, "primary extra context")
    need(primary_required["proposal_required_null"] is True, "primary proposal null")

    evaluator = surface["evaluator"]
    need(set(evaluator["modes"]) == {"calibration", "decisive"}, "two evaluator modes")
    need(evaluator["proposal_editing"] is False, "proposal editing prohibited")
    need("uncertain" in evaluator["modes"]["calibration"]["decision"], "calibration uncertainty")
    decisive = evaluator["modes"]["decisive"]
    need("uncertain" in decisive["decision"], "decisive decision uncertainty")
    need("uncertain" in decisive["root_status"], "decisive root-status uncertainty")
    need(decisive["output"] == ["row_alias", "root_status", "decision", "checks"], "decisive wire")
    need(decisive["checks"] == rubric["checks"], "decisive check names")

    allow = set(bootstrap["pre_freeze_allowlist"])
    deny = set(bootstrap["pre_freeze_denylist"])
    need(not allow.intersection(deny), "allow/deny collision")
    need(bootstrap["context_free_required"] is True, "context-free required")
    need(bootstrap["semantic_attempts_authorized"] == 0, "semantic execution prohibited")

    runtime = bootstrap["writer_runtime"]
    need(runtime["destination"] == transport["destination"], "transport destination binding")
    need(runtime["reported_model"] == transport["model"], "transport model binding")
    need(runtime["service_reported_digest"] == transport["service_reported_digest"], "transport digest binding")
    need(runtime["service_version"] == transport["service_version"], "transport service binding")
    need(transport["raw"] is True and transport["stream"] is False and transport["think"] is False, "raw transport flags")
    need(transport["options"] == {
        "num_ctx": 32768,
        "num_predict": 8192,
        "presence_penalty": 1.5,
        "seed": 502,
        "temperature": 0,
        "top_k": 20,
        "top_p": 0.95,
    }, "writer options drift")
    fmt_files = transport["response_format"]["properties"]["files"]
    need(fmt_files["required"] == required_files, "transport profile file order")

    for forbidden in (
        "ROOTS.PUBLIC.json",
        "ORACLE.PUBLIC.json",
        "METAMORPHIC.PUBLIC.json",
        "REVIEWER-CALIBRATION.PUBLIC.json",
        "RC0 returned profile files",
        "RC0 native writer/custody outputs",
        "run_writer.py",
        "check_execution.py",
    ):
        need(forbidden in deny, "missing denylist item: " + forbidden)

    need(custody["producer"] == "frozen_external_launcher_not_writer_model", "external custody")
    need(custody["model_generated_custody_receipt"] is False, "no model custody self-report")
    need(custody["constraints"]["response_complete"] is True, "complete response required")
    need(custody["constraints"]["truncated"] is False, "truncation prohibited")
    need(custody["constraints"]["extracted_files_sha256"] == required_files, "custody file coverage")
    need((HERE / "run_writer.py").is_file(), "frozen writer launcher missing")
    need((HERE / "check_execution.py").is_file(), "frozen execution checker missing")

    need(status["execution"] == "NOT_RUN", "execution must remain not run")
    need(status["profile_writer_attempts_consumed"] == 0, "writer attempt consumed in setup")
    need(status["custody_attempts_consumed"] == 0, "custody attempt consumed in setup")
    need(status["generation_capability"] == "UNKNOWN", "generation capability must remain unknown")
    for field in (
        "semantic_calibration_attempts_authorized",
        "target_generation_attempts_authorized",
        "weak_generator_attempts_authorized",
        "decisive_review_attempts_authorized",
        "tally_attempts_authorized",
    ):
        need(status[field] == 0, field + " must be zero")

    candidate_path = HERE / "CANDIDATE.json"
    candidate_checked = False
    if candidate_path.exists():
        candidate = read("CANDIDATE.json")
        need(candidate["schema"] == "eb-root-generation-prereq-candidate-rc1-v1", "candidate schema")
        source_commit = candidate["source_commit"]
        source_tree = candidate["source_tree"]
        observed_tree = subprocess.run(
            ["git", "rev-parse", source_commit + "^{tree}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        need(observed_tree == source_tree, "source tree drift")
        for relative, expected_blob in candidate["frozen_blobs"].items():
            path = ROOT / relative
            need(path.is_file() and not path.is_symlink(), "missing/symlink frozen file: " + relative)
            observed_blob = subprocess.run(
                ["git", "hash-object", str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            need(observed_blob == expected_blob, "blob drift: " + relative)
        candidate_checked = True

    return {
        "mechanical_setup": "PASS",
        "context_free_required": True,
        "profile_files_required": 5,
        "uncertainty_surface": "EXPLICIT",
        "writer_runtime": "PINNED",
        "writer_transport": "PINNED",
        "frozen_writer_launcher": True,
        "custody_producer": "FROZEN_EXTERNAL",
        "frozen_execution_checker": True,
        "model_generated_custody_receipt": False,
        "semantic_execution": "NOT_RUN_NOT_AUTHORIZED",
        "generation_capability": "UNKNOWN",
        "candidate_closure_checked": candidate_checked,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
