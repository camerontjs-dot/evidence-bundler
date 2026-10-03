"""Frozen one-shot launcher/custodian for RC1 prerequisite profile writing."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import check_execution

HERE = Path(__file__).resolve().parent
SOURCE_FILES = [
    "BOOTSTRAP-MANIFEST.json",
    "PROFILE-WRITER-TASK.md",
    "AUTHORING-RUBRIC.json",
    "PROFILE-SURFACE.json",
]
PROFILE_FILES = [
    "PRIMARY-PROMPT.txt",
    "PRIMARY-CONFIG.json",
    "EVALUATOR-PROMPT.txt",
    "EVALUATOR-CONFIG.json",
    "REVIEW-SCHEMA.json",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def http_json(url: str, *, body: dict | None = None, timeout: int = 30) -> tuple[dict, bytes]:
    data = None if body is None else json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    return json.loads(raw), raw


def runtime_preflight(transport: dict) -> dict:
    base = transport["destination"].removesuffix("/api/generate")
    version, _ = http_json(base + "/api/version")
    tags, _ = http_json(base + "/api/tags")
    matched = None
    for row in tags.get("models", []):
        if row.get("name") == transport["model"] or row.get("model") == transport["model"]:
            matched = row
            break
    if matched is None:
        raise RuntimeError("BLOCKED_AUTHORITY: pinned writer model not present")
    digest = matched.get("digest")
    if version.get("version") != transport["service_version"]:
        raise RuntimeError("BLOCKED_AUTHORITY: service version mismatch")
    if digest != transport["service_reported_digest"]:
        raise RuntimeError("BLOCKED_AUTHORITY: model digest mismatch")
    return {
        "destination": transport["destination"],
        "service_version": version["version"],
        "model": transport["model"],
        "service_reported_model_digest": digest,
        "actual_backend_weight_attestation": "UNKNOWN",
        "raw_api_history_field": "ABSENT",
        "session_resume": "ABSENT",
    }


def build_prompt(runtime: dict) -> tuple[str, list[dict]]:
    sources = {}
    opened = []
    for name in SOURCE_FILES:
        path = HERE / name
        body = path.read_text(encoding="utf-8")
        sources[name] = body
        opened.append({"name": name, "sha256": sha256_file(path)})
    payload = {
        "sources": sources,
        "actual_runtime_capability_metadata": runtime,
    }
    prompt = (
        check_execution.PROMPT_PREFIX
        + json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        + check_execution.PROMPT_SUFFIX
    )
    return prompt, opened


def build_request(transport: dict, prompt: str) -> dict:
    return {
        "model": transport["model"],
        "prompt": prompt,
        "raw": transport["raw"],
        "stream": transport["stream"],
        "think": transport["think"],
        "keep_alive": transport["keep_alive"],
        "options": transport["options"],
        "format": transport["response_format"],
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_check_failure(execution_dir: Path, disposition: str, reason: str) -> None:
    write_json(
        execution_dir / "CUSTODY-CHECK.PUBLIC.json",
        {
            "schema": "eb-root-generation-prereq-execution-check-rc1-v1",
            "result": "FAIL",
            "reason": reason,
            "disposition": disposition,
            "generation_capability": "UNKNOWN",
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution-dir", required=True)
    args = parser.parse_args()

    execution_dir = Path(args.execution_dir).resolve()
    if execution_dir.exists():
        raise SystemExit("execution directory already exists; refusing possible rerun")
    (execution_dir / "writer").mkdir(parents=True)
    (execution_dir / "profiles").mkdir()

    candidate = read_json(HERE / "CANDIDATE.json")
    transport = read_json(HERE / "WRITER-TRANSPORT.json")

    try:
        runtime = runtime_preflight(transport)
    except Exception as exc:
        write_json(
            execution_dir / "ATTEMPT-STATUS.json",
            {
                "schema": "eb-root-generation-prereq-attempt-status-rc1-v1",
                "writer_invocation_started": False,
                "writer_attempt_consumed": False,
                "custody_attempt_consumed": False,
                "status": str(exc),
                "recorded_at": now(),
                "generation_capability": "UNKNOWN",
            },
        )
        raise

    prompt, opened = build_prompt(runtime)
    request_obj = build_request(transport, prompt)
    request_bytes = (json.dumps(request_obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    request_path = execution_dir / "writer" / "REQUEST.native.json"
    request_path.write_bytes(request_bytes)

    started = now()
    write_json(
        execution_dir / "ATTEMPT-STATUS.json",
        {
            "schema": "eb-root-generation-prereq-attempt-status-rc1-v1",
            "writer_invocation_started": True,
            "writer_attempt_consumed": True,
            "custody_attempt_consumed": True,
            "status": "IN_PROGRESS",
            "started_at": started,
            "generation_capability": "UNKNOWN",
        },
    )

    response_path = execution_dir / "writer" / "RESPONSE.native.json"
    try:
        response_obj, response_bytes = http_json(
            transport["destination"], body=request_obj, timeout=900
        )
        response_path.write_bytes(response_bytes)
    except Exception as exc:
        reason = "writer transport/runtime failure after invocation began"
        write_json(
            execution_dir / "FAILURE.PUBLIC.json",
            {
                "schema": "eb-root-generation-prereq-failure-rc1-v1",
                "disposition": "BLOCKED_CUSTODY_VERIFICATION",
                "reason": reason,
                "exception": type(exc).__name__,
                "recorded_at": now(),
                "generation_capability": "UNKNOWN",
            },
        )
        write_check_failure(execution_dir, "BLOCKED_CUSTODY_VERIFICATION", reason)
        raise

    completed = now()
    done_reason = response_obj.get("done_reason")
    complete = bool(response_obj.get("done")) and done_reason != "length"
    truncated = done_reason == "length"

    extracted = {}
    extraction_error = None
    try:
        parsed = json.loads(response_obj["response"])
        output_files = parsed["files"]
        if set(output_files) != set(PROFILE_FILES):
            raise ValueError("returned file set mismatch")
        for name in PROFILE_FILES:
            if not isinstance(output_files[name], str):
                raise ValueError("profile file is not string: " + name)
            path = execution_dir / "profiles" / name
            path.write_text(output_files[name], encoding="utf-8")
            extracted[name] = sha256_file(path)
    except Exception as exc:
        extraction_error = str(exc)

    receipt = {
        "schema": "eb-root-generation-external-custody-rc1-v1",
        "execution_id": execution_dir.name,
        "setup_source_commit": candidate["source_commit"],
        "started_at": started,
        "completed_at": completed,
        "destination": runtime["destination"],
        "service_version": runtime["service_version"],
        "reported_model": runtime["model"],
        "reported_model_digest": runtime["service_reported_model_digest"],
        "actual_backend_weight_attestation": runtime["actual_backend_weight_attestation"],
        "session_id": "STATELESS_RAW_API_NO_RESUME_HANDLE",
        "no_history_mechanism": "raw_api_request_contains_only_frozen_source_bundle_and_runtime_metadata",
        "opened_sources": opened,
        "forbidden_sources_opened": [],
        "native_request_sha256": sha256_file(request_path),
        "native_response_sha256": sha256_file(response_path),
        "response_complete": complete,
        "truncated": truncated,
        "done_reason": done_reason,
        "extracted_files_sha256": extracted,
    }
    write_json(execution_dir / "CUSTODY-RECEIPT.json", receipt)

    if not complete:
        disposition = "BLOCKED_CUSTODY_VERIFICATION"
        reason = "writer response incomplete or length-truncated"
        write_check_failure(execution_dir, disposition, reason)
    elif extraction_error is not None:
        disposition = "BLOCKED_PROFILE_CONFIGURATION"
        reason = "writer response could not be extracted as exact five-file profile bundle: " + extraction_error
        write_check_failure(execution_dir, disposition, reason)
    else:
        try:
            result = check_execution.check(execution_dir)
        except Exception as exc:
            message = str(exc)
            profile_terms = (
                "primary config",
                "evaluator config",
                "review ",
                "profile ",
                "evaluator prompt",
            )
            disposition = (
                "BLOCKED_PROFILE_CONFIGURATION"
                if any(term in message for term in profile_terms)
                else "BLOCKED_CUSTODY_VERIFICATION"
            )
            reason = message
            write_check_failure(execution_dir, disposition, reason)
        else:
            disposition = "SUPPORTED_FOR_GENERATION_EXECUTION"
            reason = "frozen prerequisite checker passed"
            result["disposition"] = disposition
            write_json(execution_dir / "CUSTODY-CHECK.PUBLIC.json", result)

    final_status = {
        "schema": "eb-root-generation-prereq-attempt-status-rc1-v1",
        "writer_invocation_started": True,
        "writer_attempt_consumed": True,
        "custody_attempt_consumed": True,
        "status": disposition,
        "reason": reason,
        "completed_at": completed,
        "generation_capability": "UNKNOWN",
        "semantic_execution": "NOT_RUN_NOT_AUTHORIZED",
    }
    write_json(execution_dir / "ATTEMPT-STATUS.json", final_status)

    print(json.dumps(final_status, sort_keys=True))
    return 0 if disposition == "SUPPORTED_FOR_GENERATION_EXECUTION" else 2


if __name__ == "__main__":
    sys.exit(main())
