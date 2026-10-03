"""Prepare and run one allowlisted raw API profile-writing invocation.

Research only. No target, evaluator, case, oracle, or control read occurs here.
The raw native response is preserved before profile extraction; no retries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent.parent
REPO = PACKET.parent.parent
DESTINATION = "http://127.0.0.1:11434"
MODEL = "qwen3.5:9b"
DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
ALLOW = ("BOOTSTRAP-MANIFEST.json", "PROFILE-WRITER-TASK.md", "AUTHORING-RUBRIC.json", "SCHEMAS.json")


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def save(name, data):
    if not isinstance(data, bytes):
        data = encoded(data)
    path = HERE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write(data)
    return digest(data)


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args]).decode().strip()


def http(endpoint, value=None):
    data = None if value is None else encoded(value)
    request = urllib.request.Request(DESTINATION + endpoint, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
    return body, json.loads(body)


def prepare():
    assert git("rev-parse", "HEAD") == "0988ee8756ce595477695d0cd451fb8d82002e88"
    candidate = json.loads((PACKET / "CANDIDATE.R1.json").read_bytes())
    assert git("rev-parse", candidate["source_commit"] + "^{tree}") == candidate["source_tree"]
    closure = []
    for path, blob in candidate["frozen_blobs"].items():
        data = (REPO / path).read_bytes()
        assert git("rev-parse", candidate["source_commit"] + ":" + path) == blob
        assert git("hash-object", path) == blob
        assert digest(data) == candidate["frozen_raw_sha256"][path]
        closure.append({"path": path, "blob": blob, "sha256": digest(data)})
    manifest = json.loads((PACKET / "SETUP-MANIFEST.json").read_bytes())
    assert git("rev-parse", manifest["upstream_source"] + "^{tree}") == manifest["upstream_source_tree"]
    inherited = []
    upstream = "research/eb_prospective_authoring_retrieval_rc2_20261002/"
    for name, blob in manifest["origin_blobs"].items():
        assert git("rev-parse", manifest["upstream_source"] + ":" + upstream + name) == blob
        inherited.append({"name": name, "blob": blob, "sha256": digest((PACKET / name).read_bytes())})
    save("IDENTITY-CLOSURE.PUBLIC.json", {"schema": "eb-generation-execution-identity-v1", "checked_at": now(), "envelope": git("rev-parse", "HEAD"), "envelope_tree": git("rev-parse", "HEAD^{tree}"), "source": candidate["source_commit"], "source_tree": candidate["source_tree"], "closure": closure, "inherited": inherited})
    _, version = http("/api/version")
    _, tags = http("/api/tags")
    matches = [row for row in tags["models"] if row["name"] == MODEL]
    assert len(matches) == 1 and matches[0]["digest"] == DIGEST
    native_show, show = http("/api/show", {"model": MODEL})
    native_dir = Path(os.environ["EB_RC0_NATIVE_DIR"])
    native_dir.mkdir(parents=True, exist_ok=True)
    with (native_dir / "MODEL-SHOW.native.json").open("xb") as output:
        output.write(native_show)
    assert "completion" in show["capabilities"]
    capability = {
        "schema": "eb-observed-raw-runtime-capabilities-v1",
        "observed_at": now(), "destination": DESTINATION, "endpoint": "/api/generate",
        "service_version": version["version"], "model": MODEL,
        "service_reported_model_digest": DIGEST,
        "native_model_metadata_sha256": digest(native_show),
        "template": show.get("template"), "default_system": show.get("system", ""),
        "capabilities": show["capabilities"], "thinking": show.get("thinking", "UNKNOWN"),
        "model_details": show["details"], "raw_prompt": True,
        "history_field": "ABSENT", "session_resume": "ABSENT", "tool_dispatch": "ABSENT",
        "format_capability": "JSON schema transport; returned profile file strings are extracted verbatim and hashed by the collector",
        "allowed_output_artifacts": ["PRIMARY-PROMPT.txt", "PRIMARY-CONFIG.json", "EVALUATOR-PROMPT.txt", "EVALUATOR-CONFIG.json", "REVIEW-SCHEMA.json", "WRITER-RECEIPT.json"],
        "observable_parameters": {"raw": True, "stream": False, "think": False, "options": {"num_ctx": 32768, "num_predict": 8192, "temperature": 0, "seed": 502, "top_k": 20, "top_p": 0.95, "presence_penalty": 1.5}},
        "backend_weight_attestation": "UNKNOWN", "server_internal_effective_token_sequence": "UNKNOWN",
        "documented_raw_api": "https://docs.ollama.com/api/generate",
    }
    save("RUNTIME-CAPABILITIES.PUBLIC.json", capability)
    access = []
    sources = {}
    for name in ALLOW:
        data = (PACKET / name).read_bytes()
        sources[name] = data.decode("utf-8")
        access.append({"name": name, "sha256": digest(data)})
    output_properties = {name: {"type": "string"} for name in capability["allowed_output_artifacts"]}
    output_schema = {"type": "object", "properties": {"files": {"type": "object", "properties": output_properties, "required": list(output_properties), "additionalProperties": False}}, "required": ["files"], "additionalProperties": False}
    prompt = "<|im_start|>user\n" + json.dumps({"sources": sources, "actual_runtime_capability_metadata": capability}, ensure_ascii=False) + "\n<|im_end|>\n<|im_start|>assistant\n"
    request = {"model": MODEL, "prompt": prompt, "format": output_schema, **capability["observable_parameters"], "keep_alive": 0}
    request_hash = save("writer/REQUEST.native.json", request)
    save("WRITER-ROUTE-FREEZE.PUBLIC.json", {
        "schema": "eb-fresh-profile-writer-route-v1", "frozen_at": now(),
        "source_allowlist": access, "capability_sha256": digest(encoded(capability)),
        "request_sha256": request_hash, "route_code_sha256": digest(Path(__file__).read_bytes()),
        "route": "direct local raw stateless API; no agent CLI, memory, tools, history or repository hydration supplied",
        "aperture_assurance": "observable API request boundary; server internals require custody verification",
        "profile_writing_invocations": 0, "generation_and_evaluator_invocations": 0,
    })
    print(json.dumps({"preparation": "FROZEN", "closure_blobs": len(closure), "inherited_blobs": len(inherited), "request_sha256": request_hash}))


def invoke():
    freeze = json.loads((HERE / "WRITER-ROUTE-FREEZE.PUBLIC.json").read_bytes())
    request_bytes = (HERE / "writer/REQUEST.native.json").read_bytes()
    assert digest(request_bytes) == freeze["request_sha256"]
    assert digest(Path(__file__).read_bytes()) == freeze["route_code_sha256"]
    save("writer/ATTEMPT-START.PUBLIC.json", {"schema": "eb-profile-writing-attempt-v1", "started_at": now(), "invocation": 1, "request_sha256": digest(request_bytes), "consumed_if_transport_begins": True})
    request = urllib.request.Request(DESTINATION + "/api/generate", data=request_bytes, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=1200) as response:
            native = response.read()
            status = response.status
        native_hash = save("writer/RESPONSE.native.json", native)
        parsed = json.loads(native)
        output = parsed.get("response", "")
        output_hash = save("writer/OUTPUT.raw.txt", output.encode())
        save("writer/ATTEMPT-END.PUBLIC.json", {"schema": "eb-profile-writing-attempt-v1", "completed_at": now(), "http_status": status, "native_response_sha256": native_hash, "output_sha256": output_hash, "model": parsed.get("model", "UNKNOWN"), "done": parsed.get("done"), "done_reason": parsed.get("done_reason"), "prompt_eval_count": parsed.get("prompt_eval_count"), "eval_count": parsed.get("eval_count")})
        print(json.dumps({"writing_invocations": 1, "response_sha256": native_hash, "done": parsed.get("done"), "done_reason": parsed.get("done_reason")}))
    except Exception as error:
        save("writer/TRANSPORT-FAILURE.PUBLIC.json", {"occurred_at": now(), "error_type": type(error).__name__, "message": str(error), "invocation_consumed": True, "retry_permitted": False})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "invoke"])
    args = parser.parse_args()
    prepare() if args.command == "prepare" else invoke()
