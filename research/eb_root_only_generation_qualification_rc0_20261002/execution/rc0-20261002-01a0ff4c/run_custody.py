"""Single direct raw API custody session; execute no cases or semantic roles."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from prepare_writer import DIGEST, MODEL, DESTINATION, encoded, digest, save, now, HERE, PACKET

NAMES = [
    "prepare_writer.py", "RUNTIME-CAPABILITIES.PUBLIC.json", "WRITER-ROUTE-FREEZE.PUBLIC.json",
    "WRITER-APERTURE-CHECK.PUBLIC.json", "MODEL-IDENTITY-AFTER-WRITING.PUBLIC.json",
    "writer/REQUEST.native.json", "writer/RESPONSE.native.json", "writer/OUTPUT.raw.txt",
    "writer/ATTEMPT-START.PUBLIC.json", "writer/ATTEMPT-END.PUBLIC.json", "PROFILE-FREEZE.PUBLIC.json",
    "profiles/PRIMARY-PROMPT.txt", "profiles/PRIMARY-CONFIG.json", "profiles/EVALUATOR-PROMPT.txt",
    "profiles/EVALUATOR-CONFIG.json", "profiles/REVIEW-SCHEMA.json", "profiles/WRITER-RECEIPT.json",
]
PACKET_NAMES = ["BOOTSTRAP-MANIFEST.json", "PROFILE-WRITER-TASK.md", "AUTHORING-RUBRIC.json", "SCHEMAS.json"]


def main():
    inputs = {}
    hashes = {}
    for name in NAMES:
        data = (HERE / name).read_bytes()
        inputs[name] = data.decode()
        hashes[name] = digest(data)
    for name in PACKET_NAMES:
        data = (PACKET / name).read_bytes()
        relative = "../../" + name
        inputs[relative] = data.decode()
        hashes[relative] = digest(data)
    scope = {"schema": "eb-custody-explicit-receipt-allowlist-v1", "created_at": now(), "files": hashes, "unseen_semantic_answers": "NOT_SUPPLIED", "effective_internal_tokens": "UNKNOWN", "actual_backend_weights": "UNKNOWN"}
    save("CUSTODY-SCOPE.PUBLIC.json", scope)
    output_schema = {"type": "object", "properties": {"verification_code": {"type": "string"}, "assessment": {"type": "object", "properties": {"disposition": {"type": "string"}, "assurance": {"type": "string"}, "unknowns": {"type": "array", "items": {"type": "string"}}}, "required": ["disposition", "assurance", "unknowns"]}}, "required": ["verification_code", "assessment"]}
    prompt = "<|im_start|>system\n" + (HERE / "CUSTODY-TASK.md").read_text() + "\n<|im_end|>\n<|im_start|>user\n" + json.dumps({"receipt_allowlist": scope, "receipt_bytes_utf8": inputs}, ensure_ascii=False) + "\n<|im_end|>\n<|im_start|>assistant\n"
    request = {"model": MODEL, "prompt": prompt, "raw": True, "stream": False, "think": False, "format": output_schema, "options": {"num_ctx": 32768, "num_predict": 8192, "temperature": 0, "seed": 503, "top_k": 20, "top_p": 0.95, "presence_penalty": 1.5}, "keep_alive": 0}
    request_bytes = encoded(request)
    request_hash = save("custody/REQUEST.native.json", request_bytes)
    save("CUSTODY-LAUNCH-FREEZE.PUBLIC.json", {"frozen_at": now(), "request_sha256": request_hash, "task_sha256": digest((HERE / "CUSTODY-TASK.md").read_bytes()), "code_sha256": digest(Path(__file__).read_bytes()), "scope_sha256": digest(encoded(scope)), "route": "new raw stateless API request; no tools, context reuse or role replacement", "requested_model": MODEL, "service_reported_model_digest": DIGEST, "custody_session_budget": 1})
    save("custody/ATTEMPT-START.PUBLIC.json", {"started_at": now(), "request_sha256": request_hash, "invocation": 1})
    req = urllib.request.Request(DESTINATION + "/api/generate", data=request_bytes, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=1200) as response:
            native = response.read()
        native_hash = save("custody/RESPONSE.native.json", native)
        parsed = json.loads(native)
        output_hash = save("custody/OUTPUT.raw.txt", parsed.get("response", "").encode())
        save("custody/ATTEMPT-END.PUBLIC.json", {"completed_at": now(), "native_response_sha256": native_hash, "output_sha256": output_hash, "model": parsed.get("model", "UNKNOWN"), "done": parsed.get("done"), "done_reason": parsed.get("done_reason")})
        print(json.dumps({"custody_sessions": 1, "native_response_sha256": native_hash, "done_reason": parsed.get("done_reason")}))
    except Exception as error:
        save("custody/TRANSPORT-FAILURE.PUBLIC.json", {"occurred_at": now(), "error_type": type(error).__name__, "message": str(error), "invocation_consumed": True, "retry_permitted": False})
        raise


if __name__ == "__main__":
    main()
