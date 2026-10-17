#!/usr/bin/env python3
"""One-attempt EB reviewer transport. No tools, project imports, history or retries.

Uses the existing local Ollama HTTP service. Review content is drawn only from
an exact public reviewer ZIP. The controller, not the model, owns file I/O.
This qualifies a bounded information path, not reviewer semantic reliability.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import stat
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL = "qwen3.5:9b"
MODEL_DIGEST = "c97eb11d70b1acdc88af01eef566c1fe4f7fbe93eb1afc06871132f293ff425a"
VERSION = "0.40.5"
ZIP_DIGEST = "efe9148bd46a211fa6139bdd9ceb5959e0971b87d82d397dc63b2101c88bdf0d"
CASES = tuple(f"p{i:02d}" for i in range(1, 9))
MEMBERS = ("REVIEWER-RULE.md",) + tuple(
    f"{c}/{n}" for c in CASES for n in ("review_context.md", "review_record.json")
)
STATES = ("accepted", "rejected", "needs-review")
OPTIONS = {"temperature": 0, "seed": 137, "num_ctx": 8192,
           "num_predict": 4096, "num_thread": 4, "presence_penalty": 0}
MAX_BYTES = 2 * 1024 * 1024


def need(value: Any, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def encode(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        need(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def parse(value: bytes | str) -> Any:
    return json.loads(value, object_pairs_hook=unique_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value if isinstance(value, bytes) else encode(value))


def packet(raw: bytes, expected: str = ZIP_DIGEST) -> dict[str, bytes]:
    need(sha(raw) == expected, "review ZIP identity mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        need(len(entries) == len(MEMBERS), "review ZIP member count mismatch")
        need(sorted(e.filename for e in entries) == sorted(MEMBERS), "member allowlist mismatch")
        for entry in entries:
            need(not entry.is_dir() and not stat.S_ISLNK(entry.external_attr >> 16),
                 "directory or symlink in reviewer ZIP")
            need(entry.file_size < MAX_BYTES, "oversized review file")
        return {name: archive.read(name) for name in MEMBERS}


def target_ids(context: str) -> list[str]:
    ids = re.findall(r"^## Target `([^`]+)`", context, re.MULTILINE)
    need(bool(ids) and len(ids) == len(set(ids)), "target identity unavailable")
    return ids


def obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def output_schema(record: dict[str, Any], targets: list[str]) -> dict[str, Any]:
    rows = record["decisions"]
    def choices(key: str) -> dict[str, Any]:
        values = sorted({row[key] for row in rows})
        return {"type": "string", **({"enum": values} if values else {})}
    row = obj({"proposition_id": choices("proposition_id"),
               "passage_id": choices("passage_id"),
               "decision": {"type": "string", "enum": list(STATES)},
               "reason": {"type": "string", "minLength": 1}})
    native = obj({"schema": {"type": "string", "const": record["schema"]},
                  "bindings": obj({k: {"type": "string", "const": v}
                                   for k, v in record["bindings"].items()}),
                  "decisions": {"type": "array", "items": row,
                                "minItems": len(rows), "maxItems": len(rows)}})
    return obj({"review_record": native,
                "target_notes": obj({t: {"type": "string", "minLength": 1} for t in targets})})


def make_request(files: dict[str, bytes], case: str) -> dict[str, Any]:
    need(case in CASES, "case outside allowlist")
    context = files[f"{case}/review_context.md"].decode("utf-8")
    template = files[f"{case}/review_record.json"].decode("utf-8")
    user = json.dumps({"files": {f"{case}/review_context.md": context,
                                f"{case}/review_record.json": template}}, ensure_ascii=False)
    return {"model": MODEL, "messages": [
        {"role": "system", "content": files["REVIEWER-RULE.md"].decode("utf-8")},
        {"role": "user", "content": user}],
        "tools": [], "stream": False, "think": False, "keep_alive": 0,
        "options": dict(OPTIONS), "format": output_schema(parse(template), target_ids(context))}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: Any, msg: Any,
                         headers: Any, newurl: Any) -> None:
        raise ValueError("provider redirect refused")


def http(endpoint: str, body: bytes | None = None, timeout: int = 15) -> bytes:
    need(endpoint in ("version", "tags", "show", "ps", "chat"), "endpoint not permitted")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request("http://127.0.0.1:11434/api/" + endpoint,
                                     data=body, headers={"Content-Type": "application/json"})
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
    need(len(raw) <= MAX_BYTES, "provider response too large")
    return raw


def identity() -> dict[str, Any]:
    version = parse(http("version"))
    models = parse(http("tags"))["models"]
    model = next(m for m in models if m["name"] == MODEL)
    show = parse(http("show", encode({"model": MODEL})))
    need(version["version"] == VERSION, "Ollama version moved")
    need(model["digest"] == MODEL_DIGEST, "model digest moved")
    need(not show.get("system") and not show.get("messages"), "model supplies prior context")
    return {"version": version, "model": model,
            "model_show_sha256": sha(encode(show)), "model_show": show}


def validate_return(result: Any, original: dict[str, Any], targets: list[str]) -> None:
    need(isinstance(result, dict) and set(result) == {"review_record", "target_notes"},
         "review response envelope mismatch")
    record = result["review_record"]
    need(isinstance(record, dict) and set(record) == set(original), "record fields changed")
    need(record["schema"] == original["schema"] and record["bindings"] == original["bindings"],
         "review binding/schema changed")
    rows = record["decisions"]
    need(isinstance(rows, list) and len(rows) == len(original["decisions"]), "pair count changed")
    for before, after in zip(original["decisions"], rows):
        need(isinstance(after, dict) and set(after) == set(before), "decision fields changed")
        need(all(after[k] == before[k] for k in ("proposition_id", "passage_id")),
             "pair identity/order changed")
        need(after["decision"] in STATES, "invalid decision")
        need(isinstance(after["reason"], str) and bool(after["reason"].strip()), "blank reason")
    notes = result["target_notes"]
    need(isinstance(notes, dict) and set(notes) == set(targets), "target notes mismatch")
    need(all(isinstance(n, str) and n.strip() for n in notes.values()), "blank target note")


def prepare(archive: Path, out: Path) -> None:
    raw = archive.read_bytes()
    files = packet(raw)
    out.mkdir(parents=True, exist_ok=False)
    save(out / "REVIEWER-ONLY.zip", raw)
    ids = identity()
    save(out / "MODEL-IDENTITY.json", ids)
    requests = {}
    for case in CASES:
        body = encode(make_request(files, case))
        save(out / "requests" / f"{case}.json", body)
        requests[case] = sha(body)
    freeze = {"schema": "eb137-local-review-transport-v1", "at_utc": now(),
              "runner_sha256": sha(Path(__file__).read_bytes()), "zip_sha256": sha(raw),
              "model_digest": MODEL_DIGEST, "model_show_sha256": ids["model_show_sha256"],
              "model": MODEL, "provider_version": VERSION, "request_sha256": requests,
              "member_sha256": {n: sha(b) for n, b in files.items()},
              "options": OPTIONS, "attempts_per_case": 1, "case_order": CASES,
              "external_tools": [], "history_messages": 0,
              "transport_schema_basis": "Template keys/bindings/IDs and all three decisions only",
              "execution_admitted": False}
    save(out / "TRANSPORT-FREEZE.json", freeze)
    print("PREPARED: eight exact no-tools requests; not executed", flush=True)


def run(out: Path) -> None:
    freeze_raw = (out / "TRANSPORT-FREEZE.json").read_bytes()
    freeze = parse(freeze_raw)
    admission = parse((out / "ACTOR-ADMISSION.json").read_bytes())
    need(admission["admitted"] is True and admission["transport_freeze_sha256"] == sha(freeze_raw),
         "missing exact actor admission")
    need(sha(Path(__file__).read_bytes()) == freeze["runner_sha256"], "runner changed after freeze")
    files = packet((out / "REVIEWER-ONLY.zip").read_bytes())
    started = now()
    save(out / "ATTEMPT.json", {"started_utc": started, "attempt": 1,
                                "transport_freeze_sha256": sha(freeze_raw)})
    receipts = []
    try:
        for case in CASES:
            before = identity()
            need(before["model_show_sha256"] == freeze["model_show_sha256"], "model config drift")
            need(not parse(http("ps"))["models"], "provider not idle; no worker interrupted")
            payload = (out / "requests" / f"{case}.json").read_bytes()
            need(sha(payload) == freeze["request_sha256"][case], "request changed")
            need(payload == encode(make_request(files, case)), "request exceeds frozen aperture")
            start = now()
            save(out / "raw" / case / "LAUNCH.json", {"at_utc": start,
                 "request_sha256": sha(payload), "model_digest": MODEL_DIGEST,
                 "files_delivered": ["REVIEWER-RULE.md", f"{case}/review_context.md",
                                     f"{case}/review_record.json"], "tools": [], "history": []})
            tick = time.monotonic()
            raw = http("chat", payload, timeout=300)
            elapsed = time.monotonic() - tick
            save(out / "raw" / case / "response.json", raw)
            response = parse(raw)
            need(response.get("done") is True and response.get("done_reason") == "stop",
                 "incomplete model response; no retry")
            need(response.get("model") == MODEL, "response model mismatch")
            message = response["message"]
            need(not message.get("tool_calls"), "model requested a tool; not executed")
            content = message["content"].encode("utf-8")
            save(out / "raw" / case / "first-content.json", content)
            result = parse(content)
            original = parse(files[f"{case}/review_record.json"])
            targets = target_ids(files[f"{case}/review_context.md"].decode("utf-8"))
            validate_return(result, original, targets)
            after = identity()
            need(after["model_show_sha256"] == before["model_show_sha256"], "provider identity changed")
            save(out / "reviews" / case / "review_record.json", result["review_record"])
            save(out / "reviews" / case / "target_notes.json", result["target_notes"])
            receipt = {"case": case, "started_utc": start, "ended_utc": now(),
                       "elapsed_seconds": elapsed, "timing_unit": "one upstream target incl. required children",
                       "required_target_ids": targets, "child_time_separately_observed": len(targets) == 1,
                       "external_raw_lookups": 0, "tool_calls_executed": 0,
                       "request_sha256": sha(payload), "response_sha256": sha(raw),
                       "first_content_sha256": sha(content), "model_digest": MODEL_DIGEST,
                       "actions_observed": ["deliver fixed context", "receive model JSON", "validate exact record"],
                       "backend_metrics": {k: v for k, v in response.items() if k != "message"}}
            save(out / "reviews" / case / "RECEIPT.json", receipt)
            receipts.append(receipt)
            print(case + ": first response recorded, no re-review", flush=True)
        frozen = {str(p.relative_to(out)): sha(p.read_bytes())
                  for folder in ("raw", "reviews") for p in sorted((out / folder).rglob("*"))
                  if p.is_file()}
        save(out / "REVIEW-FREEZE.json", {"schema": "eb137-local-first-decisions-v1",
             "frozen_utc": now(), "started_utc": started, "files": frozen,
             "actor_admission_sha256": sha((out / "ACTOR-ADMISSION.json").read_bytes()),
             "semantic_evaluation": "NOT_RUN", "cases": receipts})
        print("ALL_FIRST_DECISIONS_FROZEN; semantic evaluation not performed", flush=True)
    except Exception as exc:
        save(out / "FIRST-FAILURE.json", {"at_utc": now(), "type": type(exc).__name__,
             "error": str(exc), "completed_cases": [r["case"] for r in receipts],
             "retry": "NONE", "semantic_disposition": "UNESTABLISHED"})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("archive", type=Path)
    p.add_argument("out", type=Path)
    r = sub.add_parser("run")
    r.add_argument("out", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.archive, args.out)
    else:
        run(args.out)


if __name__ == "__main__":
    main()
