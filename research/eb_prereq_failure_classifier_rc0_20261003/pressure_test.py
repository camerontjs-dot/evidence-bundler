"""Frozen synthetic pressure matrix for prerequisite failure classification."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import classifier

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def baseline_objects() -> dict[str, Any]:
    surface = json.loads((HERE / "PROFILE-SURFACE.json").read_text(encoding="utf-8"))
    transport = json.loads((HERE / "WRITER-TRANSPORT.json").read_text(encoding="utf-8"))

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
    request = {
        "model": transport["model"],
        "raw": transport["raw"],
        "stream": transport["stream"],
        "think": transport["think"],
        "keep_alive": transport["keep_alive"],
        "options": copy.deepcopy(transport["options"]),
        "format": copy.deepcopy(transport["response_format"]),
        "prompt": "synthetic fixture only",
    }
    response = {"done": True, "done_reason": "stop", "response": "synthetic fixture only"}

    return {
        "transport": transport,
        "primary": primary,
        "evaluator": evaluator,
        "review": review,
        "primary_prompt": "Primary synthetic prompt preserves the frozen root-only proposal-null profile requirements.",
        "evaluator_prompt": "Evaluator synthetic prompt defines calibration and decisive modes with explicit uncertain handling.",
        "request": request,
        "response": response,
    }


def materialize(root: Path) -> Path:
    obj = baseline_objects()
    execution = root / "execution"
    writer = execution / "writer"
    profiles = execution / "profiles"
    writer.mkdir(parents=True)
    profiles.mkdir()

    write_json(writer / "REQUEST.native.json", obj["request"])
    write_json(writer / "RESPONSE.native.json", obj["response"])
    write_json(profiles / "PRIMARY-CONFIG.json", obj["primary"])
    write_json(profiles / "EVALUATOR-CONFIG.json", obj["evaluator"])
    write_json(profiles / "REVIEW-SCHEMA.json", obj["review"])
    (profiles / "PRIMARY-PROMPT.txt").write_text(obj["primary_prompt"], encoding="utf-8")
    (profiles / "EVALUATOR-PROMPT.txt").write_text(obj["evaluator_prompt"], encoding="utf-8")

    receipt = {
        "response_complete": True,
        "truncated": False,
        "done_reason": "stop",
        "forbidden_sources_opened": [],
        "native_request_sha256": sha256(writer / "REQUEST.native.json"),
        "native_response_sha256": sha256(writer / "RESPONSE.native.json"),
        "reported_model_digest": obj["transport"]["service_reported_digest"],
        "extracted_files_sha256": {name: sha256(profiles / name) for name in classifier.REQUIRED_FILES},
    }
    write_json(execution / "CUSTODY-RECEIPT.json", receipt)
    return execution


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def refresh_profile_hashes(execution: Path) -> None:
    receipt = read_json(execution / "CUSTODY-RECEIPT.json")
    receipt["extracted_files_sha256"] = {
        name: sha256(execution / "profiles" / name)
        for name in classifier.REQUIRED_FILES
        if (execution / "profiles" / name).is_file()
    }
    write_json(execution / "CUSTODY-RECEIPT.json", receipt)


def mutate(execution: Path, name: str) -> dict[str, Any] | None:
    profiles = execution / "profiles"
    receipt_path = execution / "CUSTODY-RECEIPT.json"

    if name == "none":
        return None
    if name == "raw_keyerror_output":
        return classifier.classify_exception(KeyError("output"))

    if name == "missing_calibration_output":
        review = read_json(profiles / "REVIEW-SCHEMA.json")
        del review["modes"]["calibration"]["output"]
        write_json(profiles / "REVIEW-SCHEMA.json", review)
        refresh_profile_hashes(execution)
    elif name == "missing_decisive_output":
        review = read_json(profiles / "REVIEW-SCHEMA.json")
        del review["modes"]["decisive"]["output"]
        write_json(profiles / "REVIEW-SCHEMA.json", review)
        refresh_profile_hashes(execution)
    elif name == "missing_calibration_decision":
        review = read_json(profiles / "REVIEW-SCHEMA.json")
        del review["modes"]["calibration"]["decision"]
        write_json(profiles / "REVIEW-SCHEMA.json", review)
        refresh_profile_hashes(execution)
    elif name == "wrong_decisive_decision_enum":
        review = read_json(profiles / "REVIEW-SCHEMA.json")
        review["modes"]["decisive"]["decision"] = ["accept", "reject"]
        write_json(profiles / "REVIEW-SCHEMA.json", review)
        refresh_profile_hashes(execution)
    elif name == "malformed_review_json":
        (profiles / "REVIEW-SCHEMA.json").write_text('{"modes": ', encoding="utf-8")
        refresh_profile_hashes(execution)
    elif name == "primary_config_drift":
        primary = read_json(profiles / "PRIMARY-CONFIG.json")
        primary["input_mode"] = "other"
        write_json(profiles / "PRIMARY-CONFIG.json", primary)
        refresh_profile_hashes(execution)
    elif name == "evaluator_config_drift":
        evaluator = read_json(profiles / "EVALUATOR-CONFIG.json")
        evaluator["modes"] = ["calibration"]
        write_json(profiles / "EVALUATOR-CONFIG.json", evaluator)
        refresh_profile_hashes(execution)
    elif name == "evaluator_prompt_missing_uncertain":
        (profiles / "EVALUATOR-PROMPT.txt").write_text(
            "Evaluator synthetic prompt defines calibration and decisive modes but deliberately omits the required ambiguity token.",
            encoding="utf-8",
        )
        refresh_profile_hashes(execution)
    elif name == "profile_file_missing":
        (profiles / "REVIEW-SCHEMA.json").unlink()
    elif name == "request_hash_mismatch":
        receipt = read_json(receipt_path)
        receipt["native_request_sha256"] = "sha256:" + "0" * 64
        write_json(receipt_path, receipt)
    elif name == "response_hash_mismatch":
        receipt = read_json(receipt_path)
        receipt["native_response_sha256"] = "sha256:" + "1" * 64
        write_json(receipt_path, receipt)
    elif name == "response_incomplete":
        receipt = read_json(receipt_path)
        receipt["response_complete"] = False
        write_json(receipt_path, receipt)
    elif name == "response_truncated":
        receipt = read_json(receipt_path)
        receipt["truncated"] = True
        receipt["done_reason"] = "length"
        write_json(receipt_path, receipt)
    elif name == "runtime_digest_mismatch":
        receipt = read_json(receipt_path)
        receipt["reported_model_digest"] = "not-the-frozen-digest"
        write_json(receipt_path, receipt)
    elif name == "profile_hash_mismatch":
        receipt = read_json(receipt_path)
        receipt["extracted_files_sha256"]["PRIMARY-PROMPT.txt"] = "sha256:" + "2" * 64
        write_json(receipt_path, receipt)
    elif name == "forbidden_source":
        receipt = read_json(receipt_path)
        receipt["forbidden_sources_opened"] = ["forbidden-answer-bearing-source"]
        write_json(receipt_path, receipt)
    else:
        raise ValueError("unknown mutation: " + name)
    return None


def run_case(row: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="eb-classifier-") as tmp:
        execution = materialize(Path(tmp))
        direct = mutate(execution, row["mutation"])
        result = direct if direct is not None else classifier.check_execution(execution)

    observed = {
        "id": row["id"],
        "result": result["result"],
        "category": result.get("category"),
        "code": result.get("code"),
        "disposition": result.get("disposition"),
    }
    expected = {
        "result": row["expected_result"],
        "category": row["expected_category"],
        "code": row["expected_code"],
        "disposition": row["expected_disposition"],
    }
    if {k: observed[k] for k in expected} != expected:
        raise AssertionError({"case": row["id"], "expected": expected, "observed": observed})
    return observed


def run() -> dict[str, Any]:
    matrix = json.loads((HERE / "MUTATION-MATRIX.json").read_text(encoding="utf-8"))
    results = [run_case(row) for row in matrix["cases"]]

    raw_witness = "'output'"
    legacy = classifier.legacy_rc2_message_classifier(raw_witness)
    if legacy != "BLOCKED_CUSTODY_VERIFICATION":
        raise AssertionError("legacy control no longer reproduces RC2-style misclassification")

    profile_cases = [row for row in results if row["category"] == classifier.PROFILE]
    contamination_cases = [row for row in results if row["category"] == classifier.CONTAMINATION]
    if not profile_cases or not contamination_cases:
        raise AssertionError("discrimination populations missing")

    weak_failures = {
        "rc2_message_heuristic_raw_output_witness": legacy != "BLOCKED_PROFILE_CONFIGURATION",
        "everything_custody_profile_boundary": any(
            classifier.everything_custody_classifier(row["id"]) != row["disposition"]
            for row in profile_cases
        ),
        "everything_custody_contamination_boundary": any(
            classifier.everything_custody_classifier(row["id"]) != row["disposition"]
            for row in contamination_cases
        ),
    }
    if not all(weak_failures.values()):
        raise AssertionError({"weak_classifier_discrimination": weak_failures})

    return {
        "schema": "eb-prereq-failure-classifier-pressure-result-v1",
        "result": "PASS",
        "cases": len(results),
        "profile_failures": len(profile_cases),
        "custody_failures": sum(row["category"] == classifier.CUSTODY for row in results),
        "contamination_failures": len(contamination_cases),
        "apparatus_failures": sum(row["category"] == classifier.APPARATUS for row in results),
        "weak_classifier_discrimination": weak_failures,
        "generation_capability": "UNKNOWN",
        "model_or_network_execution": "NOT_RUN",
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
