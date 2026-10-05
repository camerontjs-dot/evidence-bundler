"""Structured execution checker for the RC3 prerequisite apparatus successor."""
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

REQUIRED = [
    "PRIMARY-PROMPT.txt",
    "PRIMARY-CONFIG.json",
    "EVALUATOR-PROMPT.txt",
    "EVALUATOR-CONFIG.json",
    "REVIEW-SCHEMA.json",
]

ALLOWED_SOURCES = [
    "BOOTSTRAP-MANIFEST.json",
    "PROFILE-WRITER-TASK.md",
    "AUTHORING-RUBRIC.json",
    "PROFILE-SURFACE.json",
]

PROMPT_PREFIX = "<|im_start|>user\n"
PROMPT_SUFFIX = "\n<|im_end|>\n<|im_start|>assistant\n"


@dataclass
class DiagnosticFailure(Exception):
    category: str
    code: str
    detail: str

    def result(self) -> dict[str, Any]:
        return {
            "schema": "eb-root-generation-prereq-execution-check-rc3-v1",
            "result": "FAIL",
            "category": self.category,
            "code": self.code,
            "detail": self.detail,
            "disposition": DISPOSITION[self.category],
            "generation_capability": "UNKNOWN",
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
        return exc.result()
    return {
        "schema": "eb-root-generation-prereq-execution-check-rc3-v1",
        "result": "FAIL",
        "category": APPARATUS,
        "code": "APPARATUS_UNEXPECTED_EXCEPTION",
        "detail": f"{type(exc).__name__}: {exc}",
        "disposition": DISPOSITION[APPARATUS],
        "generation_capability": "UNKNOWN",
    }


def parse_writer_prompt(prompt: str) -> dict[str, Any]:
    require(prompt.startswith(PROMPT_PREFIX), CUSTODY, "CUSTODY_PROMPT_PREFIX", "writer prompt prefix mismatch")
    require(prompt.endswith(PROMPT_SUFFIX), CUSTODY, "CUSTODY_PROMPT_SUFFIX", "writer prompt suffix mismatch")
    inner = prompt[len(PROMPT_PREFIX):-len(PROMPT_SUFFIX)]
    try:
        payload = json.loads(inner)
    except json.JSONDecodeError as exc:
        fail(CUSTODY, "CUSTODY_PROMPT_JSON", f"writer prompt JSON invalid: {exc.msg}")
    require(isinstance(payload, dict), CUSTODY, "CUSTODY_PROMPT_OBJECT", "writer prompt payload must be object")
    require(set(payload) == {"sources", "actual_runtime_capability_metadata"}, CUSTODY, "CUSTODY_PROMPT_FIELDS", "writer prompt top-level fields mismatch")
    sources = key(payload, "sources", CUSTODY, "CUSTODY_PROMPT_SOURCES_MISSING", "writer prompt")
    require(isinstance(sources, dict), CUSTODY, "CUSTODY_PROMPT_SOURCES_TYPE", "writer prompt sources must be object")
    require(set(sources) == set(ALLOWED_SOURCES), CUSTODY, "CUSTODY_PROMPT_SOURCE_SET", "writer prompt source set mismatch")
    for name in ALLOWED_SOURCES:
        require(
            sources[name] == (HERE / name).read_text(encoding="utf-8"),
            CUSTODY,
            "CUSTODY_PROMPT_SOURCE_BYTES",
            "writer prompt source bytes mismatch: " + name,
        )
    return payload


def check(execution_dir: Path) -> dict[str, Any]:
    try:
        return _check(execution_dir)
    except BaseException as exc:
        return classify_exception(exc)


def _check(execution_dir: Path) -> dict[str, Any]:
    bootstrap = read_json(HERE / "BOOTSTRAP-MANIFEST.json", APPARATUS, "APPARATUS_BOOTSTRAP_JSON", "bootstrap")
    surface = read_json(HERE / "PROFILE-SURFACE.json", APPARATUS, "APPARATUS_SURFACE_JSON", "profile surface")
    custody_schema = read_json(HERE / "CUSTODY-SCHEMA.json", APPARATUS, "APPARATUS_CUSTODY_SCHEMA_JSON", "custody schema")
    transport = read_json(HERE / "WRITER-TRANSPORT.json", APPARATUS, "APPARATUS_TRANSPORT_JSON", "writer transport")
    candidate = read_json(HERE / "CANDIDATE.json", APPARATUS, "APPARATUS_CANDIDATE_JSON", "candidate")

    receipt_path = execution_dir / "CUSTODY-RECEIPT.json"
    request_path = execution_dir / "writer" / "REQUEST.native.json"
    response_path = execution_dir / "writer" / "RESPONSE.native.json"
    profiles = execution_dir / "profiles"

    require(receipt_path.is_file(), CUSTODY, "CUSTODY_RECEIPT_MISSING", "custody receipt missing")
    require(request_path.is_file(), CUSTODY, "CUSTODY_REQUEST_MISSING", "native request missing")
    require(response_path.is_file(), CUSTODY, "CUSTODY_RESPONSE_MISSING", "native response missing")
    require(profiles.is_dir(), PROFILE, "PROFILE_DIRECTORY_MISSING", "profiles directory missing")

    receipt = read_json(receipt_path, CUSTODY, "CUSTODY_RECEIPT_JSON_INVALID", "custody receipt")
    required_receipt = set(custody_schema["required_fields"])
    require(required_receipt <= set(receipt), CUSTODY, "CUSTODY_RECEIPT_FIELDS", "custody receipt required fields missing")
    require(receipt["schema"] == custody_schema["schema"], CUSTODY, "CUSTODY_RECEIPT_SCHEMA", "custody receipt schema mismatch")
    require(receipt["setup_source_commit"] == candidate["source_commit"], CUSTODY, "CUSTODY_SETUP_SOURCE", "setup source identity mismatch")

    runtime = bootstrap["writer_runtime"]
    require(receipt["destination"] == runtime["destination"], CUSTODY, "CUSTODY_RUNTIME_DESTINATION", "destination mismatch")
    require(receipt["service_version"] == runtime["service_version"], CUSTODY, "CUSTODY_RUNTIME_SERVICE", "service version mismatch")
    require(receipt["reported_model"] == runtime["reported_model"], CUSTODY, "CUSTODY_RUNTIME_MODEL", "model mismatch")
    require(receipt["reported_model_digest"] == runtime["service_reported_digest"], CUSTODY, "CUSTODY_RUNTIME_DIGEST", "runtime digest mismatch")

    require(receipt["response_complete"] is True, CUSTODY, "CUSTODY_RESPONSE_INCOMPLETE", "response_complete must be true")
    require(receipt["truncated"] is False, CUSTODY, "CUSTODY_RESPONSE_TRUNCATED", "truncated must be false")
    require(receipt["done_reason"] != "length", CUSTODY, "CUSTODY_RESPONSE_TRUNCATED", "done_reason must not be length")
    require(receipt["forbidden_sources_opened"] == [], CONTAMINATION, "CONTAMINATION_FORBIDDEN_SOURCE", "forbidden source exposure recorded")

    opened = receipt["opened_sources"]
    require(isinstance(opened, list) and len(opened) == 4, CUSTODY, "CUSTODY_OPENED_SOURCE_COUNT", "opened source count mismatch")
    try:
        opened_map = {row["name"]: row["sha256"] for row in opened}
    except Exception as exc:
        fail(CUSTODY, "CUSTODY_OPENED_SOURCE_SHAPE", f"opened source shape invalid: {type(exc).__name__}")
    require(set(opened_map) == set(ALLOWED_SOURCES), CUSTODY, "CUSTODY_OPENED_SOURCE_SET", "opened source set mismatch")
    for name in ALLOWED_SOURCES:
        require(opened_map[name] == sha256(HERE / name), CUSTODY, "CUSTODY_OPENED_SOURCE_HASH", "opened source hash drift: " + name)

    require(receipt["native_request_sha256"] == sha256(request_path), CUSTODY, "CUSTODY_REQUEST_HASH", "native request hash mismatch")
    require(receipt["native_response_sha256"] == sha256(response_path), CUSTODY, "CUSTODY_RESPONSE_HASH", "native response hash mismatch")

    request = read_json(request_path, CUSTODY, "CUSTODY_REQUEST_JSON_INVALID", "native request")
    require(request.get("model") == transport["model"], CUSTODY, "CUSTODY_REQUEST_MODEL", "request model mismatch")
    require(request.get("raw") == transport["raw"], CUSTODY, "CUSTODY_REQUEST_RAW", "request raw mismatch")
    require(request.get("stream") == transport["stream"], CUSTODY, "CUSTODY_REQUEST_STREAM", "request stream mismatch")
    require(request.get("think") == transport["think"], CUSTODY, "CUSTODY_REQUEST_THINK", "request think mismatch")
    require(request.get("keep_alive") == transport["keep_alive"], CUSTODY, "CUSTODY_REQUEST_KEEP_ALIVE", "request keep_alive mismatch")
    require(request.get("options") == transport["options"], CUSTODY, "CUSTODY_REQUEST_OPTIONS", "request options mismatch")
    require(request.get("format") == transport["response_format"], CUSTODY, "CUSTODY_REQUEST_FORMAT", "request response format mismatch")

    prompt = key(request, "prompt", CUSTODY, "CUSTODY_REQUEST_PROMPT_MISSING", "native request")
    require(isinstance(prompt, str), CUSTODY, "CUSTODY_REQUEST_PROMPT_TYPE", "native request prompt must be string")
    prompt_payload = parse_writer_prompt(prompt)
    runtime_payload = prompt_payload["actual_runtime_capability_metadata"]
    require(runtime_payload["destination"] == receipt["destination"], CUSTODY, "CUSTODY_PROMPT_RUNTIME_DESTINATION", "prompt runtime destination mismatch")
    require(runtime_payload["service_version"] == receipt["service_version"], CUSTODY, "CUSTODY_PROMPT_RUNTIME_SERVICE", "prompt runtime service mismatch")
    require(runtime_payload["model"] == receipt["reported_model"], CUSTODY, "CUSTODY_PROMPT_RUNTIME_MODEL", "prompt runtime model mismatch")
    require(runtime_payload["service_reported_model_digest"] == receipt["reported_model_digest"], CUSTODY, "CUSTODY_PROMPT_RUNTIME_DIGEST", "prompt runtime digest mismatch")

    extracted = receipt["extracted_files_sha256"]
    require(isinstance(extracted, dict), CUSTODY, "CUSTODY_PROFILE_HASH_SET_TYPE", "extracted profile hashes must be object")
    require(surface["required_files"] == REQUIRED, APPARATUS, "APPARATUS_REQUIRED_FILE_ORDER", "profile surface required file order drift")
    for name in REQUIRED:
        path = profiles / name
        require(path.is_file() and not path.is_symlink(), PROFILE, "PROFILE_FILE_MISSING", "profile file missing: " + name)

    require(set(extracted) == set(REQUIRED), CUSTODY, "CUSTODY_PROFILE_HASH_SET", "extracted profile hash set mismatch")
    for name in REQUIRED:
        require(extracted[name] == sha256(profiles / name), CUSTODY, "CUSTODY_PROFILE_HASH", "profile hash mismatch: " + name)
        require((profiles / name).stat().st_size > 0, PROFILE, "PROFILE_FILE_EMPTY", "profile file empty: " + name)

    primary = read_json(profiles / "PRIMARY-CONFIG.json", PROFILE, "PROFILE_PRIMARY_CONFIG_JSON_INVALID", "primary config")
    evaluator = read_json(profiles / "EVALUATOR-CONFIG.json", PROFILE, "PROFILE_EVALUATOR_CONFIG_JSON_INVALID", "evaluator config")
    review = read_json(profiles / "REVIEW-SCHEMA.json", PROFILE, "PROFILE_REVIEW_JSON_INVALID", "review schema")

    primary_required = surface["primary"]["config_required"]
    for field, code in (
        ("role", "PROFILE_PRIMARY_CONFIG_ROLE"),
        ("input_mode", "PROFILE_PRIMARY_CONFIG_INPUT_MODE"),
        ("output_mode", "PROFILE_PRIMARY_CONFIG_OUTPUT_MODE"),
        ("extra_context", "PROFILE_PRIMARY_CONFIG_EXTRA_CONTEXT"),
        ("proposal_required_null", "PROFILE_PRIMARY_CONFIG_PROPOSAL_NULL"),
    ):
        value = key(primary, field, PROFILE, code + "_MISSING", "primary config")
        require(value == primary_required[field], PROFILE, code, f"primary {field} mismatch")

    evaluator_required = surface["evaluator"]["config_required"]
    for field, code in (
        ("role", "PROFILE_EVALUATOR_CONFIG_ROLE"),
        ("modes", "PROFILE_EVALUATOR_CONFIG_MODES"),
        ("shared_semantic_instructions", "PROFILE_EVALUATOR_CONFIG_SHARED"),
        ("proposal_editing", "PROFILE_EVALUATOR_CONFIG_EDITING"),
        ("review_schema_file", "PROFILE_EVALUATOR_CONFIG_SCHEMA_FILE"),
    ):
        value = key(evaluator, field, PROFILE, code + "_MISSING", "evaluator config")
        require(value == evaluator_required[field], PROFILE, code, f"evaluator {field} mismatch")

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

    try:
        primary_prompt = (profiles / "PRIMARY-PROMPT.txt").read_text(encoding="utf-8")
        evaluator_prompt = (profiles / "EVALUATOR-PROMPT.txt").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        fail(PROFILE, "PROFILE_PROMPT_READ", f"profile prompt read failure: {type(exc).__name__}")

    require(len(primary_prompt.strip()) > 40, PROFILE, "PROFILE_PRIMARY_PROMPT_SIZE", "primary prompt too small")
    require(len(evaluator_prompt.strip()) > 40, PROFILE, "PROFILE_EVALUATOR_PROMPT_SIZE", "evaluator prompt too small")
    lower_eval = evaluator_prompt.lower()
    require("uncertain" in lower_eval, PROFILE, "PROFILE_EVALUATOR_PROMPT_UNCERTAIN", "evaluator prompt missing uncertain")
    require("calibration" in lower_eval, PROFILE, "PROFILE_EVALUATOR_PROMPT_CALIBRATION", "evaluator prompt missing calibration")
    require("decisive" in lower_eval, PROFILE, "PROFILE_EVALUATOR_PROMPT_DECISIVE", "evaluator prompt missing decisive")

    forbidden_profile_markers = [
        "ROOTS.PUBLIC.json",
        "ORACLE.PUBLIC.json",
        "METAMORPHIC.PUBLIC.json",
        "REVIEWER-CALIBRATION.PUBLIC.json",
    ]
    joined = "\n".join([
        primary_prompt,
        evaluator_prompt,
        json.dumps(primary, sort_keys=True),
        json.dumps(evaluator, sort_keys=True),
        json.dumps(review, sort_keys=True),
    ])
    for marker in forbidden_profile_markers:
        require(marker not in joined, CONTAMINATION, "CONTAMINATION_PROFILE_MARKER", "forbidden marker in profile: " + marker)

    return {
        "schema": "eb-root-generation-prereq-execution-check-rc3-v1",
        "result": "PASS",
        "category": None,
        "code": None,
        "detail": "frozen prerequisite checker passed",
        "disposition": "SUPPORTED_FOR_GENERATION_EXECUTION",
        "execution_id": receipt["execution_id"],
        "setup_source_commit": candidate["source_commit"],
        "writer_aperture": "PASS",
        "runtime_binding": "PASS",
        "transport_binding": "PASS",
        "native_custody": "PASS",
        "profile_file_count": 5,
        "profile_surface": "PASS",
        "semantic_execution": "NOT_RUN_NOT_AUTHORIZED",
        "generation_capability": "UNKNOWN",
    }
