"""Offline integration pressure test for the RC3 checker and launcher."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import check_execution
import run_writer

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def baseline(execution: Path) -> None:
    transport = read_json(HERE / "WRITER-TRANSPORT.json")
    surface = read_json(HERE / "PROFILE-SURFACE.json")
    candidate = read_json(HERE / "CANDIDATE.json")

    writer = execution / "writer"
    profiles = execution / "profiles"
    writer.mkdir(parents=True)
    profiles.mkdir()

    runtime = {
        "destination": transport["destination"],
        "service_version": transport["service_version"],
        "model": transport["model"],
        "service_reported_model_digest": transport["service_reported_digest"],
        "actual_backend_weight_attestation": "UNKNOWN",
        "raw_api_history_field": "ABSENT",
        "session_resume": "ABSENT",
    }
    prompt, opened = run_writer.build_prompt(runtime)
    request = run_writer.build_request(transport, prompt)
    response = {"done": True, "done_reason": "stop", "response": "synthetic fixture"}

    write_json(writer / "REQUEST.native.json", request)
    write_json(writer / "RESPONSE.native.json", response)

    primary = copy.deepcopy(surface["primary"]["config_required"])
    evaluator = copy.deepcopy(surface["evaluator"]["config_required"])
    review = {
        "modes": {
            "calibration": {
                "output": copy.deepcopy(surface["evaluator"]["modes"]["calibration"]["output"]),
                "decision": copy.deepcopy(surface["evaluator"]["modes"]["calibration"]["decision"]),
            },
            "decisive": {
                "output": copy.deepcopy(surface["evaluator"]["modes"]["decisive"]["output"]),
                "root_status": copy.deepcopy(surface["evaluator"]["modes"]["decisive"]["root_status"]),
                "decision": copy.deepcopy(surface["evaluator"]["modes"]["decisive"]["decision"]),
                "checks": copy.deepcopy(surface["evaluator"]["modes"]["decisive"]["checks"]),
            },
        }
    }
    write_json(profiles / "PRIMARY-CONFIG.json", primary)
    write_json(profiles / "EVALUATOR-CONFIG.json", evaluator)
    write_json(profiles / "REVIEW-SCHEMA.json", review)
    (profiles / "PRIMARY-PROMPT.txt").write_text(
        "Primary synthetic prompt preserves the root-only proposal-null contract and exact output requirements.",
        encoding="utf-8",
    )
    (profiles / "EVALUATOR-PROMPT.txt").write_text(
        "Evaluator synthetic prompt defines calibration and decisive modes with explicit uncertain handling.",
        encoding="utf-8",
    )

    receipt = {
        "schema": "eb-root-generation-external-custody-rc1-v1",
        "execution_id": "synthetic-rc3-apparatus",
        "setup_source_commit": candidate["source_commit"],
        "started_at": "2026-10-03T00:00:00+00:00",
        "completed_at": "2026-10-03T00:00:01+00:00",
        "destination": transport["destination"],
        "service_version": transport["service_version"],
        "reported_model": transport["model"],
        "reported_model_digest": transport["service_reported_digest"],
        "actual_backend_weight_attestation": "UNKNOWN",
        "session_id": "SYNTHETIC",
        "no_history_mechanism": "SYNTHETIC",
        "opened_sources": opened,
        "forbidden_sources_opened": [],
        "native_request_sha256": sha256(writer / "REQUEST.native.json"),
        "native_response_sha256": sha256(writer / "RESPONSE.native.json"),
        "response_complete": True,
        "truncated": False,
        "done_reason": "stop",
        "extracted_files_sha256": {
            name: sha256(profiles / name) for name in check_execution.REQUIRED
        },
    }
    write_json(execution / "CUSTODY-RECEIPT.json", receipt)


def refresh_hashes(execution: Path) -> None:
    receipt = read_json(execution / "CUSTODY-RECEIPT.json")
    receipt["extracted_files_sha256"] = {
        name: sha256(execution / "profiles" / name)
        for name in check_execution.REQUIRED
        if (execution / "profiles" / name).is_file()
    }
    write_json(execution / "CUSTODY-RECEIPT.json", receipt)


def mutate(execution: Path, mutation: str) -> dict[str, Any] | None:
    profiles = execution / "profiles"
    receipt_path = execution / "CUSTODY-RECEIPT.json"

    if mutation == "none":
        return None
    if mutation == "raw_keyerror_output":
        return check_execution.classify_exception(KeyError("output"))
    if mutation == "missing_calibration_output":
        review = read_json(profiles / "REVIEW-SCHEMA.json")
        del review["modes"]["calibration"]["output"]
        write_json(profiles / "REVIEW-SCHEMA.json", review)
        refresh_hashes(execution)
    elif mutation == "missing_decisive_output":
        review = read_json(profiles / "REVIEW-SCHEMA.json")
        del review["modes"]["decisive"]["output"]
        write_json(profiles / "REVIEW-SCHEMA.json", review)
        refresh_hashes(execution)
    elif mutation == "missing_calibration_decision":
        review = read_json(profiles / "REVIEW-SCHEMA.json")
        del review["modes"]["calibration"]["decision"]
        write_json(profiles / "REVIEW-SCHEMA.json", review)
        refresh_hashes(execution)
    elif mutation == "wrong_decisive_decision_enum":
        review = read_json(profiles / "REVIEW-SCHEMA.json")
        review["modes"]["decisive"]["decision"] = ["accept", "reject"]
        write_json(profiles / "REVIEW-SCHEMA.json", review)
        refresh_hashes(execution)
    elif mutation == "malformed_review_json":
        (profiles / "REVIEW-SCHEMA.json").write_text('{"modes": ', encoding="utf-8")
        refresh_hashes(execution)
    elif mutation == "primary_config_drift":
        primary = read_json(profiles / "PRIMARY-CONFIG.json")
        primary["input_mode"] = "other"
        write_json(profiles / "PRIMARY-CONFIG.json", primary)
        refresh_hashes(execution)
    elif mutation == "evaluator_config_drift":
        evaluator = read_json(profiles / "EVALUATOR-CONFIG.json")
        evaluator["modes"] = ["calibration"]
        write_json(profiles / "EVALUATOR-CONFIG.json", evaluator)
        refresh_hashes(execution)
    elif mutation == "evaluator_prompt_missing_uncertain":
        (profiles / "EVALUATOR-PROMPT.txt").write_text(
            "Evaluator synthetic prompt defines calibration and decisive modes while omitting the ambiguity marker.",
            encoding="utf-8",
        )
        refresh_hashes(execution)
    elif mutation == "profile_file_missing":
        (profiles / "REVIEW-SCHEMA.json").unlink()
    elif mutation == "request_hash_mismatch":
        receipt = read_json(receipt_path)
        receipt["native_request_sha256"] = "sha256:" + "0" * 64
        write_json(receipt_path, receipt)
    elif mutation == "response_hash_mismatch":
        receipt = read_json(receipt_path)
        receipt["native_response_sha256"] = "sha256:" + "1" * 64
        write_json(receipt_path, receipt)
    elif mutation == "response_incomplete":
        receipt = read_json(receipt_path)
        receipt["response_complete"] = False
        write_json(receipt_path, receipt)
    elif mutation == "response_truncated":
        receipt = read_json(receipt_path)
        receipt["truncated"] = True
        receipt["done_reason"] = "length"
        write_json(receipt_path, receipt)
    elif mutation == "runtime_digest_mismatch":
        receipt = read_json(receipt_path)
        receipt["reported_model_digest"] = "wrong"
        write_json(receipt_path, receipt)
    elif mutation == "profile_hash_mismatch":
        receipt = read_json(receipt_path)
        receipt["extracted_files_sha256"]["PRIMARY-PROMPT.txt"] = "sha256:" + "2" * 64
        write_json(receipt_path, receipt)
    elif mutation == "forbidden_source":
        receipt = read_json(receipt_path)
        receipt["forbidden_sources_opened"] = ["forbidden-source"]
        write_json(receipt_path, receipt)
    else:
        raise ValueError("unknown mutation: " + mutation)
    return None


def legacy_rc2_message_classifier(message: str) -> str:
    profile_terms = (
        "primary config",
        "evaluator config",
        "review ",
        "profile ",
        "evaluator prompt",
    )
    return "BLOCKED_PROFILE_CONFIGURATION" if any(term in message for term in profile_terms) else "BLOCKED_CUSTODY_VERIFICATION"


def everything_custody(_: str) -> str:
    return "BLOCKED_CUSTODY_VERIFICATION"


def run_case(row: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="eb-rc3-apparatus-") as tmp:
        execution = Path(tmp) / "execution"
        baseline(execution)
        direct = mutate(execution, row["mutation"])
        result = direct if direct is not None else check_execution.check(execution)

    observed = {
        "result": result.get("result"),
        "category": result.get("category"),
        "code": result.get("code"),
        "disposition": None if result.get("result") == "PASS" else result.get("disposition"),
    }
    expected = {
        "result": row["expected_result"],
        "category": row["expected_category"],
        "code": row["expected_code"],
        "disposition": row["expected_disposition"],
    }
    if observed != expected:
        raise AssertionError({"case": row["id"], "expected": expected, "observed": observed})

    disposition, reason = run_writer.normalize_checker_result(result)
    expected_launcher = (
        "SUPPORTED_FOR_GENERATION_EXECUTION"
        if row["expected_result"] == "PASS"
        else row["expected_disposition"]
    )
    if disposition != expected_launcher:
        raise AssertionError(
            {"case": row["id"], "expected_launcher": expected_launcher, "observed_launcher": disposition, "reason": reason}
        )

    return {
        "id": row["id"],
        **observed,
        "launcher_disposition": disposition,
    }


def run() -> dict[str, Any]:
    matrix = read_json(HERE / "MUTATION-MATRIX.json")
    results = [run_case(row) for row in matrix["cases"]]

    raw_message = "'output'"
    legacy = legacy_rc2_message_classifier(raw_message)
    profile_results = [r for r in results if r["category"] == check_execution.PROFILE]
    contamination_results = [r for r in results if r["category"] == check_execution.CONTAMINATION]

    weak = {
        "rc2_message_heuristic_raw_output_witness": legacy != "BLOCKED_PROFILE_CONFIGURATION",
        "everything_custody_profile_boundary": any(everything_custody(r["id"]) != r["disposition"] for r in profile_results),
        "everything_custody_contamination_boundary": any(everything_custody(r["id"]) != r["disposition"] for r in contamination_results),
    }
    if not all(weak.values()):
        raise AssertionError({"weak_classifier_discrimination": weak})

    return {
        "schema": "eb-root-generation-prereq-rc3-apparatus-pressure-v1",
        "result": "PASS",
        "cases": len(results),
        "baseline_passes": sum(r["result"] == "PASS" for r in results),
        "profile_failures": len(profile_results),
        "custody_failures": sum(r["category"] == check_execution.CUSTODY for r in results),
        "contamination_failures": len(contamination_results),
        "apparatus_failures": sum(r["category"] == check_execution.APPARATUS for r in results),
        "launcher_structured_mapping": "PASS",
        "weak_classifier_discrimination": weak,
        "model_or_network_execution": "NOT_RUN",
        "generation_capability": "UNKNOWN",
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
