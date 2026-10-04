"""Frozen execution checker for RC1 profile/custody prerequisites only."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
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


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> dict:
    def unique(items):
        result = {}
        for key, value in items:
            need(key not in result, "duplicate JSON key: " + str(path))
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def parse_writer_prompt(prompt: str) -> dict:
    need(prompt.startswith(PROMPT_PREFIX), "writer prompt prefix")
    need(prompt.endswith(PROMPT_SUFFIX), "writer prompt suffix")
    inner = prompt[len(PROMPT_PREFIX):-len(PROMPT_SUFFIX)]
    payload = json.loads(inner)
    need(set(payload) == {"sources", "actual_runtime_capability_metadata"}, "writer prompt top-level fields")
    sources = payload["sources"]
    need(set(sources) == set(ALLOWED_SOURCES), "writer prompt source set")
    for name in ALLOWED_SOURCES:
        need(sources[name] == (HERE / name).read_text(encoding="utf-8"), "writer source bytes: " + name)
    return payload


def check(execution_dir: Path) -> dict:
    bootstrap = read_json(HERE / "BOOTSTRAP-MANIFEST.json")
    surface = read_json(HERE / "PROFILE-SURFACE.json")
    custody_schema = read_json(HERE / "CUSTODY-SCHEMA.json")
    transport = read_json(HERE / "WRITER-TRANSPORT.json")
    candidate = read_json(HERE / "CANDIDATE.json")
    receipt = read_json(execution_dir / "CUSTODY-RECEIPT.json")

    need(set(custody_schema["required_fields"]) <= set(receipt), "missing custody field")
    need(receipt["schema"] == custody_schema["schema"], "custody schema")
    need(receipt["setup_source_commit"] == candidate["source_commit"], "setup source identity")
    runtime = bootstrap["writer_runtime"]
    need(receipt["destination"] == runtime["destination"], "destination drift")
    need(receipt["service_version"] == runtime["service_version"], "service version drift")
    need(receipt["reported_model"] == runtime["reported_model"], "writer model drift")
    need(receipt["reported_model_digest"] == runtime["service_reported_digest"], "writer digest drift")
    need(receipt["response_complete"] is True, "incomplete writer response")
    need(receipt["truncated"] is False, "truncated writer response")
    need(receipt["done_reason"] != "length", "length stop")
    need(receipt["forbidden_sources_opened"] == [], "forbidden source exposure")

    opened = receipt["opened_sources"]
    need(isinstance(opened, list) and len(opened) == 4, "opened source count")
    opened_map = {row["name"]: row["sha256"] for row in opened}
    need(set(opened_map) == set(ALLOWED_SOURCES), "opened source set")
    for name in ALLOWED_SOURCES:
        need(opened_map[name] == sha256(HERE / name), "opened source hash drift: " + name)

    request_path = execution_dir / "writer" / "REQUEST.native.json"
    response_path = execution_dir / "writer" / "RESPONSE.native.json"
    need(request_path.is_file() and response_path.is_file(), "native request/response missing")
    need(receipt["native_request_sha256"] == sha256(request_path), "native request digest")
    need(receipt["native_response_sha256"] == sha256(response_path), "native response digest")

    request = read_json(request_path)
    need(request["model"] == transport["model"], "request model")
    need(request["raw"] == transport["raw"], "request raw")
    need(request["stream"] == transport["stream"], "request stream")
    need(request["think"] == transport["think"], "request think")
    need(request["keep_alive"] == transport["keep_alive"], "request keep_alive")
    need(request["options"] == transport["options"], "request options")
    need(request["format"] == transport["response_format"], "request response format")
    prompt_payload = parse_writer_prompt(request["prompt"])
    runtime_payload = prompt_payload["actual_runtime_capability_metadata"]
    need(runtime_payload["destination"] == receipt["destination"], "prompt runtime destination")
    need(runtime_payload["service_version"] == receipt["service_version"], "prompt runtime service")
    need(runtime_payload["model"] == receipt["reported_model"], "prompt runtime model")
    need(runtime_payload["service_reported_model_digest"] == receipt["reported_model_digest"], "prompt runtime digest")

    profiles = execution_dir / "profiles"
    need(profiles.is_dir(), "profiles directory missing")
    extracted = receipt["extracted_files_sha256"]
    need(set(extracted) == set(REQUIRED), "extracted file set")
    need(surface["required_files"] == REQUIRED, "frozen required file order")
    for name in REQUIRED:
        path = profiles / name
        need(path.is_file() and not path.is_symlink(), "missing/symlink profile: " + name)
        need(extracted[name] == sha256(path), "profile digest drift: " + name)
        need(path.stat().st_size > 0, "empty profile: " + name)

    primary = read_json(profiles / "PRIMARY-CONFIG.json")
    evaluator = read_json(profiles / "EVALUATOR-CONFIG.json")
    review = read_json(profiles / "REVIEW-SCHEMA.json")

    for key, expected in surface["primary"]["config_required"].items():
        need(primary.get(key) == expected, "primary config: " + key)
    for key, expected in surface["evaluator"]["config_required"].items():
        need(evaluator.get(key) == expected, "evaluator config: " + key)

    need(set(review.get("modes", {})) == {"calibration", "decisive"}, "review modes")
    calibration = review["modes"]["calibration"]
    decisive = review["modes"]["decisive"]
    expected_cal = surface["evaluator"]["modes"]["calibration"]
    expected_dec = surface["evaluator"]["modes"]["decisive"]
    need(calibration["output"] == expected_cal["output"], "calibration output wire")
    need(calibration["decision"] == expected_cal["decision"], "calibration decisions")
    need(decisive["output"] == expected_dec["output"], "decisive output wire")
    need(decisive["root_status"] == expected_dec["root_status"], "root-status enum")
    need(decisive["decision"] == expected_dec["decision"], "decisive decisions")
    need(decisive["checks"] == expected_dec["checks"], "decisive checks")

    primary_prompt = (profiles / "PRIMARY-PROMPT.txt").read_text(encoding="utf-8")
    evaluator_prompt = (profiles / "EVALUATOR-PROMPT.txt").read_text(encoding="utf-8")
    need(len(primary_prompt.strip()) > 40, "primary prompt too small")
    need(len(evaluator_prompt.strip()) > 40, "evaluator prompt too small")
    lower_eval = evaluator_prompt.lower()
    for token in ("uncertain", "calibration", "decisive"):
        need(token in lower_eval, "evaluator prompt missing " + token)

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
        need(marker not in joined, "forbidden marker in profile: " + marker)

    return {
        "schema": "eb-root-generation-prereq-execution-check-rc1-v1",
        "result": "PASS",
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_execution.py EXECUTION_DIR")
    try:
        result = check(Path(sys.argv[1]).resolve())
    except Exception as exc:
        result = {
            "schema": "eb-root-generation-prereq-execution-check-rc1-v1",
            "result": "FAIL",
            "reason": str(exc),
            "generation_capability": "UNKNOWN",
        }
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(2)
    print(json.dumps(result, sort_keys=True))
