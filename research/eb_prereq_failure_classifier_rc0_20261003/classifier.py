"""Structured prerequisite diagnostic checker and disposition classifier."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

PROFILE = "PROFILE_CONFIGURATION"
CUSTODY = "CUSTODY_VERIFICATION"
CONTAMINATION = "CONTAMINATION"
APPARATUS = "APPARATUS_ERROR"

DISPOSITION = {
    PROFILE: "BLOCKED_PROFILE_CONFIGURATION",
    CUSTODY: "BLOCKED_CUSTODY_VERIFICATION",
    CONTAMINATION: "CONTAMINATED",
    APPARATUS: "INCONCLUSIVE",
}

REQUIRED_FILES = [
    "PRIMARY-PROMPT.txt",
    "PRIMARY-CONFIG.json",
    "EVALUATOR-PROMPT.txt",
    "EVALUATOR-CONFIG.json",
    "REVIEW-SCHEMA.json",
]


@dataclass
class DiagnosticFailure(Exception):
    category: str
    code: str
    detail: str

    def as_result(self) -> dict[str, Any]:
        return {
            "result": "FAIL",
            "category": self.category,
            "code": self.code,
            "detail": self.detail,
            "disposition": DISPOSITION[self.category],
        }


def fail(category: str, code: str, detail: str) -> None:
    raise DiagnosticFailure(category, code, detail)


def require(condition: bool, category: str, code: str, detail: str) -> None:
    if not condition:
        fail(category, code, detail)


def key(obj: dict[str, Any], name: str, category: str, code: str, context: str) -> Any:
    if name not in obj:
        fail(category, code, f"{context} missing field: {name}")
    return obj[name]


def read_json(path: Path, category: str, code: str, context: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(category, code, f"{context} invalid JSON: {type(exc).__name__}")
    require(isinstance(value, dict), category, code, f"{context} must be object")
    return value


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def classify_exception(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, DiagnosticFailure):
        return exc.as_result()
    return {
        "result": "FAIL",
        "category": APPARATUS,
        "code": "APPARATUS_UNEXPECTED_EXCEPTION",
        "detail": f"{type(exc).__name__}: {exc}",
        "disposition": DISPOSITION[APPARATUS],
    }


def check_execution(execution_dir: Path) -> dict[str, Any]:
    try:
        return _check_execution(execution_dir)
    except BaseException as exc:
        return classify_exception(exc)


def _check_execution(execution_dir: Path) -> dict[str, Any]:
    surface = read_json(HERE / "PROFILE-SURFACE.json", APPARATUS, "APPARATUS_SURFACE_JSON", "profile surface")
    transport = read_json(HERE / "WRITER-TRANSPORT.json", APPARATUS, "APPARATUS_TRANSPORT_JSON", "writer transport")

    receipt_path = execution_dir / "CUSTODY-RECEIPT.json"
    request_path = execution_dir / "writer" / "REQUEST.native.json"
    response_path = execution_dir / "writer" / "RESPONSE.native.json"
    profiles = execution_dir / "profiles"

    require(receipt_path.is_file(), CUSTODY, "CUSTODY_RECEIPT_MISSING", "custody receipt missing")
    require(request_path.is_file(), CUSTODY, "CUSTODY_REQUEST_MISSING", "native request missing")
    require(response_path.is_file(), CUSTODY, "CUSTODY_RESPONSE_MISSING", "native response missing")
    require(profiles.is_dir(), PROFILE, "PROFILE_DIRECTORY_MISSING", "profiles directory missing")

    receipt = read_json(receipt_path, CUSTODY, "CUSTODY_RECEIPT_JSON_INVALID", "custody receipt")

    response_complete = key(receipt, "response_complete", CUSTODY, "CUSTODY_RESPONSE_COMPLETE_MISSING", "custody receipt")
    truncated = key(receipt, "truncated", CUSTODY, "CUSTODY_TRUNCATED_MISSING", "custody receipt")
    done_reason = key(receipt, "done_reason", CUSTODY, "CUSTODY_DONE_REASON_MISSING", "custody receipt")
    forbidden = key(receipt, "forbidden_sources_opened", CUSTODY, "CUSTODY_FORBIDDEN_SOURCES_MISSING", "custody receipt")

    require(response_complete is True, CUSTODY, "CUSTODY_RESPONSE_INCOMPLETE", "response_complete must be true")
    require(truncated is False, CUSTODY, "CUSTODY_RESPONSE_TRUNCATED", "truncated must be false")
    require(done_reason != "length", CUSTODY, "CUSTODY_RESPONSE_TRUNCATED", "done_reason must not be length")
    require(forbidden == [], CONTAMINATION, "CONTAMINATION_FORBIDDEN_SOURCE", "forbidden source exposure recorded")

    expected_request_hash = key(receipt, "native_request_sha256", CUSTODY, "CUSTODY_REQUEST_HASH_MISSING", "custody receipt")
    expected_response_hash = key(receipt, "native_response_sha256", CUSTODY, "CUSTODY_RESPONSE_HASH_MISSING", "custody receipt")
    require(expected_request_hash == sha256(request_path), CUSTODY, "CUSTODY_REQUEST_HASH", "native request hash mismatch")
    require(expected_response_hash == sha256(response_path), CUSTODY, "CUSTODY_RESPONSE_HASH", "native response hash mismatch")

    request = read_json(request_path, CUSTODY, "CUSTODY_REQUEST_JSON_INVALID", "native request")
    for field in ("model", "raw", "stream", "think", "keep_alive", "options", "format"):
        require(field in request, CUSTODY, "CUSTODY_REQUEST_FIELD_MISSING", f"native request missing field: {field}")
    require(request["model"] == transport["model"], CUSTODY, "CUSTODY_REQUEST_MODEL", "request model mismatch")
    require(request["raw"] == transport["raw"], CUSTODY, "CUSTODY_REQUEST_RAW", "request raw mismatch")
    require(request["stream"] == transport["stream"], CUSTODY, "CUSTODY_REQUEST_STREAM", "request stream mismatch")
    require(request["think"] == transport["think"], CUSTODY, "CUSTODY_REQUEST_THINK", "request think mismatch")
    require(request["keep_alive"] == transport["keep_alive"], CUSTODY, "CUSTODY_REQUEST_KEEP_ALIVE", "request keep_alive mismatch")
    require(request["options"] == transport["options"], CUSTODY, "CUSTODY_REQUEST_OPTIONS", "request options mismatch")
    require(request["format"] == transport["response_format"], CUSTODY, "CUSTODY_REQUEST_FORMAT", "request format mismatch")

    reported_digest = key(receipt, "reported_model_digest", CUSTODY, "CUSTODY_RUNTIME_DIGEST_MISSING", "custody receipt")
    require(reported_digest == transport["service_reported_digest"], CUSTODY, "CUSTODY_RUNTIME_DIGEST", "runtime digest mismatch")

    extracted = key(receipt, "extracted_files_sha256", CUSTODY, "CUSTODY_PROFILE_HASH_SET_MISSING", "custody receipt")
    require(isinstance(extracted, dict), CUSTODY, "CUSTODY_PROFILE_HASH_SET_TYPE", "extracted profile hashes must be object")

    for name in REQUIRED_FILES:
        path = profiles / name
        require(path.is_file() and not path.is_symlink(), PROFILE, "PROFILE_FILE_MISSING", f"profile file missing: {name}")

    require(set(extracted) == set(REQUIRED_FILES), CUSTODY, "CUSTODY_PROFILE_HASH_SET", "extracted profile hash set mismatch")
    for name in REQUIRED_FILES:
        require(extracted[name] == sha256(profiles / name), CUSTODY, "CUSTODY_PROFILE_HASH", f"profile hash mismatch: {name}")

    primary = read_json(profiles / "PRIMARY-CONFIG.json", PROFILE, "PROFILE_PRIMARY_CONFIG_JSON_INVALID", "primary config")
    evaluator = read_json(profiles / "EVALUATOR-CONFIG.json", PROFILE, "PROFILE_EVALUATOR_CONFIG_JSON_INVALID", "evaluator config")
    review = read_json(profiles / "REVIEW-SCHEMA.json", PROFILE, "PROFILE_REVIEW_JSON_INVALID", "review schema")

    primary_required = surface["primary"]["config_required"]
    require(key(primary, "input_mode", PROFILE, "PROFILE_PRIMARY_CONFIG_INPUT_MODE_MISSING", "primary config") == primary_required["input_mode"], PROFILE, "PROFILE_PRIMARY_CONFIG_INPUT_MODE", "primary input_mode mismatch")
    require(key(primary, "role", PROFILE, "PROFILE_PRIMARY_CONFIG_ROLE_MISSING", "primary config") == primary_required["role"], PROFILE, "PROFILE_PRIMARY_CONFIG_ROLE", "primary role mismatch")
    require(key(primary, "output_mode", PROFILE, "PROFILE_PRIMARY_CONFIG_OUTPUT_MODE_MISSING", "primary config") == primary_required["output_mode"], PROFILE, "PROFILE_PRIMARY_CONFIG_OUTPUT_MODE", "primary output_mode mismatch")
    require(key(primary, "extra_context", PROFILE, "PROFILE_PRIMARY_CONFIG_EXTRA_CONTEXT_MISSING", "primary config") == primary_required["extra_context"], PROFILE, "PROFILE_PRIMARY_CONFIG_EXTRA_CONTEXT", "primary extra_context mismatch")
    require(key(primary, "proposal_required_null", PROFILE, "PROFILE_PRIMARY_CONFIG_PROPOSAL_NULL_MISSING", "primary config") == primary_required["proposal_required_null"], PROFILE, "PROFILE_PRIMARY_CONFIG_PROPOSAL_NULL", "primary proposal_required_null mismatch")

    evaluator_required = surface["evaluator"]["config_required"]
    require(key(evaluator, "role", PROFILE, "PROFILE_EVALUATOR_CONFIG_ROLE_MISSING", "evaluator config") == evaluator_required["role"], PROFILE, "PROFILE_EVALUATOR_CONFIG_ROLE", "evaluator role mismatch")
    require(key(evaluator, "modes", PROFILE, "PROFILE_EVALUATOR_CONFIG_MODES_MISSING", "evaluator config") == evaluator_required["modes"], PROFILE, "PROFILE_EVALUATOR_CONFIG_MODES", "evaluator modes mismatch")
    require(key(evaluator, "shared_semantic_instructions", PROFILE, "PROFILE_EVALUATOR_CONFIG_SHARED_MISSING", "evaluator config") == evaluator_required["shared_semantic_instructions"], PROFILE, "PROFILE_EVALUATOR_CONFIG_SHARED", "shared semantic instructions mismatch")
    require(key(evaluator, "proposal_editing", PROFILE, "PROFILE_EVALUATOR_CONFIG_EDITING_MISSING", "evaluator config") == evaluator_required["proposal_editing"], PROFILE, "PROFILE_EVALUATOR_CONFIG_EDITING", "proposal editing mismatch")
    require(key(evaluator, "review_schema_file", PROFILE, "PROFILE_EVALUATOR_CONFIG_SCHEMA_FILE_MISSING", "evaluator config") == evaluator_required["review_schema_file"], PROFILE, "PROFILE_EVALUATOR_CONFIG_SCHEMA_FILE", "review schema file mismatch")

    modes = key(review, "modes", PROFILE, "PROFILE_REVIEW_MODES_MISSING", "review schema")
    require(isinstance(modes, dict), PROFILE, "PROFILE_REVIEW_MODES_TYPE", "review modes must be object")
    require(set(modes) == {"calibration", "decisive"}, PROFILE, "PROFILE_REVIEW_MODES_SET", "review modes mismatch")
    calibration = key(modes, "calibration", PROFILE, "PROFILE_CALIBRATION_MODE_MISSING", "review modes")
    decisive = key(modes, "decisive", PROFILE, "PROFILE_DECISIVE_MODE_MISSING", "review modes")
    require(isinstance(calibration, dict), PROFILE, "PROFILE_CALIBRATION_MODE_TYPE", "calibration mode must be object")
    require(isinstance(decisive, dict), PROFILE, "PROFILE_DECISIVE_MODE_TYPE", "decisive mode must be object")

    expected_cal = surface["evaluator"]["modes"]["calibration"]
    expected_dec = surface["evaluator"]["modes"]["decisive"]

    calibration_output = key(calibration, "output", PROFILE, "PROFILE_CALIBRATION_OUTPUT_MISSING", "calibration mode")
    calibration_decision = key(calibration, "decision", PROFILE, "PROFILE_CALIBRATION_DECISION_MISSING", "calibration mode")
    require(calibration_output == expected_cal["output"], PROFILE, "PROFILE_CALIBRATION_OUTPUT_WIRE", "calibration output wire mismatch")
    require(calibration_decision == expected_cal["decision"], PROFILE, "PROFILE_CALIBRATION_DECISION_ENUM", "calibration decision enum mismatch")

    decisive_output = key(decisive, "output", PROFILE, "PROFILE_DECISIVE_OUTPUT_MISSING", "decisive mode")
    decisive_status = key(decisive, "root_status", PROFILE, "PROFILE_DECISIVE_ROOT_STATUS_MISSING", "decisive mode")
    decisive_decision = key(decisive, "decision", PROFILE, "PROFILE_DECISIVE_DECISION_MISSING", "decisive mode")
    decisive_checks = key(decisive, "checks", PROFILE, "PROFILE_DECISIVE_CHECKS_MISSING", "decisive mode")
    require(decisive_output == expected_dec["output"], PROFILE, "PROFILE_DECISIVE_OUTPUT_WIRE", "decisive output wire mismatch")
    require(decisive_status == expected_dec["root_status"], PROFILE, "PROFILE_DECISIVE_ROOT_STATUS_ENUM", "decisive root_status enum mismatch")
    require(decisive_decision == expected_dec["decision"], PROFILE, "PROFILE_DECISIVE_DECISION_ENUM", "decisive decision enum mismatch")
    require(decisive_checks == expected_dec["checks"], PROFILE, "PROFILE_DECISIVE_CHECKS", "decisive checks mismatch")

    primary_prompt = (profiles / "PRIMARY-PROMPT.txt").read_text(encoding="utf-8")
    evaluator_prompt = (profiles / "EVALUATOR-PROMPT.txt").read_text(encoding="utf-8")
    require(len(primary_prompt.strip()) > 40, PROFILE, "PROFILE_PRIMARY_PROMPT_SIZE", "primary prompt too small")
    require(len(evaluator_prompt.strip()) > 40, PROFILE, "PROFILE_EVALUATOR_PROMPT_SIZE", "evaluator prompt too small")
    lower_eval = evaluator_prompt.lower()
    require("uncertain" in lower_eval, PROFILE, "PROFILE_EVALUATOR_PROMPT_UNCERTAIN", "evaluator prompt missing uncertain")
    require("calibration" in lower_eval, PROFILE, "PROFILE_EVALUATOR_PROMPT_CALIBRATION", "evaluator prompt missing calibration")
    require("decisive" in lower_eval, PROFILE, "PROFILE_EVALUATOR_PROMPT_DECISIVE", "evaluator prompt missing decisive")

    return {
        "result": "PASS",
        "category": None,
        "code": None,
        "detail": "synthetic prerequisite fixture accepted",
        "disposition": None,
    }


def legacy_rc2_message_classifier(message: str) -> str:
    profile_terms = (
        "primary config",
        "evaluator config",
        "review ",
        "profile ",
        "evaluator prompt",
    )
    return "BLOCKED_PROFILE_CONFIGURATION" if any(term in message for term in profile_terms) else "BLOCKED_CUSTODY_VERIFICATION"


def everything_custody_classifier(_: str) -> str:
    return "BLOCKED_CUSTODY_VERIFICATION"
