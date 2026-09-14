from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
EXPECTED_CODEX_VERSION = "codex-cli 0.154.0"
RUN_COUNT = 12

sys.path.insert(0, str(HERE))
from selftest import main as run_selftest
from validator import load_expected, sha256_bytes, validate_trace_and_final

PROMPT_BASE = (
    "CONTEXT-FREE REQUIRED. This is a synthetic non-semantic serialization harness. "
    "Use only SYNTHETIC_INPUT.json and SERIALIZATION_TASK.md in the current working directory. "
    "Your only authorized shell command is exactly: "
    "cat SYNTHETIC_INPUT.json SERIALIZATION_TASK.md. "
    "Do not inspect parent directories, GitHub, the internet, other files, prior runs, or another output. "
    "Read both authorized files completely, follow SERIALIZATION_TASK.md exactly, and return only the JSON object."
)


class HarnessStop(RuntimeError):
    def __init__(self, status: str, step: str, detail: str):
        super().__init__(detail)
        self.status = status
        self.step = step
        self.detail = detail


def sha_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def command_text(args: list[str], cwd: Path | None = None) -> str:
    cp = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if cp.returncode != 0:
        raise HarnessStop("ENVIRONMENT_BLOCKED", "command", f"{args!r} exited {cp.returncode}: {cp.stdout}")
    return cp.stdout.strip()


def ensure_clean_checkout() -> str:
    status = subprocess.check_output(["git", "-C", str(REPO), "status", "--porcelain"], text=True)
    if status.strip():
        raise HarnessStop("ENVIRONMENT_BLOCKED", "clean_checkout", "harness checkout is not clean")
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()


def verify_frozen_fixture() -> dict:
    packet = json.loads((HERE / "SYNTHETIC_INPUT.json").read_text(encoding="utf-8"))
    expected = load_expected(HERE / "EXPECTED_LABELS.json")
    schema = json.loads((HERE / "OUTPUT_SCHEMA.json").read_text(encoding="utf-8"))

    if packet.get("schema") != "eb-codex-serialization-harness-input-v1":
        raise HarnessStop("NOT_QUALIFIED", "fixture", "synthetic packet schema mismatch")
    items = packet.get("items")
    if not isinstance(items, list) or len(items) != 96:
        raise HarnessStop("NOT_QUALIFIED", "fixture", "synthetic packet must contain exactly 96 items")
    packet_ids = [x.get("relation_id") for x in items]
    if len(packet_ids) != len(set(packet_ids)):
        raise HarnessStop("NOT_QUALIFIED", "fixture", "synthetic packet contains duplicate relation IDs")
    if set(packet_ids) != set(expected):
        raise HarnessStop("NOT_QUALIFIED", "fixture", "expected-label relation set differs from packet")

    bucket_map = {0:"KEEP_DISTINCT",1:"DROP_REDUNDANT",2:"DROP_DISTRACTOR",3:"UNRESOLVED"}
    for item in items:
        rid = item.get("relation_id")
        bucket = item.get("bucket")
        if bucket not in bucket_map or expected.get(rid) != bucket_map[bucket]:
            raise HarnessStop("NOT_QUALIFIED", "fixture", f"bucket/expected mismatch for {rid}")

    labels_schema = schema.get("properties", {}).get("labels", {})
    if set(labels_schema.get("required", [])) != set(expected):
        raise HarnessStop("NOT_QUALIFIED", "fixture", "output-schema required relation set mismatch")
    if set(labels_schema.get("properties", {})) != set(expected):
        raise HarnessStop("NOT_QUALIFIED", "fixture", "output-schema property relation set mismatch")
    if labels_schema.get("additionalProperties") is not False:
        raise HarnessStop("NOT_QUALIFIED", "fixture", "output schema must forbid extra label properties")

    return {
        "item_count": len(items),
        "unique_relation_id_count": len(set(packet_ids)),
        "packet_sha256": sha_file(HERE / "SYNTHETIC_INPUT.json"),
        "expected_labels_sha256": sha_file(HERE / "EXPECTED_LABELS.json"),
        "output_schema_sha256": sha_file(HERE / "OUTPUT_SCHEMA.json"),
        "task_sha256": sha_file(HERE / "SERIALIZATION_TASK.md"),
    }


def capability_check() -> dict:
    if shutil.which("codex") is None:
        raise HarnessStop("ENVIRONMENT_BLOCKED", "capability", "codex CLI not found on PATH")
    version = command_text(["codex", "--version"]).splitlines()[0].strip()
    if version != EXPECTED_CODEX_VERSION:
        raise HarnessStop("ENVIRONMENT_BLOCKED", "capability", f"installed Codex version differs from frozen V4 version: {version!r} != {EXPECTED_CODEX_VERSION!r}")
    help_text = command_text(["codex", "exec", "--help"])
    required_flags = ["--output-schema","--output-last-message","--json","--ephemeral","--ignore-user-config","--ignore-rules","--sandbox"]
    missing = [flag for flag in required_flags if flag not in help_text]
    if missing:
        raise HarnessStop("ENVIRONMENT_BLOCKED", "capability", f"codex exec missing required flags: {missing}")
    return {"codex_version": version, "required_flags": required_flags, "output_schema_supported": True}


def make_execution_dir() -> tuple[str, Path]:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    execution_id = f"{stamp}-{uuid.uuid4().hex[:8]}"
    root = HERE / "executions" / execution_id
    root.mkdir(parents=True, exist_ok=False)
    return execution_id, root


def atomic_json(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run_child(execution_id: str, execution_root: Path, ordinal: int, expected_labels: dict[str, str]) -> dict:
    run_name = f"run_{ordinal:02d}"
    run_dir = execution_root / run_name
    run_dir.mkdir(exist_ok=False)
    for name in ["SYNTHETIC_INPUT.json", "SERIALIZATION_TASK.md", "OUTPUT_SCHEMA.json"]:
        shutil.copy2(HERE / name, run_dir / name)
    reviewer_id = f"{execution_id}-{run_name}"
    final_path = run_dir / "FINAL.json"
    trace_path = run_dir / "TRACE.jsonl"
    stderr_path = run_dir / "STDERR.log"
    for path in (final_path, trace_path, stderr_path):
        if path.exists():
            raise HarnessStop("NOT_QUALIFIED", "fresh_output_path", f"output path unexpectedly exists: {path}")
    prompt = PROMPT_BASE + f' Set reviewer_id exactly to "{reviewer_id}".'
    cmd = [
        "codex","exec","--ephemeral","--ignore-user-config","--ignore-rules","--skip-git-repo-check",
        "--sandbox","read-only","--json","--output-schema",str((run_dir / "OUTPUT_SCHEMA.json").resolve()),
        "--output-last-message",str(final_path.resolve()),prompt,
    ]
    with trace_path.open("xb") as trace_fh, stderr_path.open("xb") as stderr_fh:
        cp = subprocess.run(cmd, cwd=run_dir, stdout=trace_fh, stderr=stderr_fh)
    if cp.returncode != 0:
        raise HarnessStop("NOT_QUALIFIED", "child_execution", f"{run_name} exited {cp.returncode}; preserved at {run_dir}")
    if not final_path.is_file():
        raise HarnessStop("NOT_QUALIFIED", "child_output", f"{run_name} did not create FINAL.json")
    trace_meta = validate_trace_and_final(trace_path, final_path, expected_labels, reviewer_id)
    return {
        "run_name":run_name,"reviewer_id":reviewer_id,"final_sha256":sha_file(final_path),
        "trace_sha256":sha_file(trace_path),"stderr_sha256":sha_file(stderr_path),
        "final_size":final_path.stat().st_size,"trace_size":trace_path.stat().st_size,
        "stderr_size":stderr_path.stat().st_size,**trace_meta,
    }


def write_result(execution_root: Path, status: str, head: str | None, fixture: dict | None, selftest: dict | None, capability: dict | None, runs: list[dict], failure: dict | None) -> None:
    result = {
        "schema":"eb-codex-serialization-harness-result-v1","harness_status":status,
        "scientific_result":False,"rc1_resume_authorized":False,"source_head":head,
        "fixture":fixture,"selftest":selftest,"capability":capability,
        "required_run_count":RUN_COUNT,"completed_run_count":len(runs),"runs":runs,"failure":failure,
        "qualification_rule":"QUALIFIED only if all 12 fresh synthetic Codex executions pass every structural, isolation, deterministic-value, duplicate-key, and trace/final identity check.",
        "stop_boundary":"HARNESS_QUALIFICATION_ONLY_NO_RC1_EXECUTION",
    }
    atomic_json(execution_root / "HARNESS_RESULT.json", result)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test-only", action="store_true")
    args = ap.parse_args()
    if args.self_test_only:
        print(json.dumps(run_selftest(), indent=2, sort_keys=True))
        return 0
    head = fixture = selftest = capability = None
    runs: list[dict] = []
    execution_id: str | None = None
    execution_root: Path | None = None
    try:
        head = ensure_clean_checkout()
        execution_id, execution_root = make_execution_dir()
        fixture = verify_frozen_fixture()
        selftest = run_selftest()
        atomic_json(execution_root / "SELFTEST_RESULT.json", selftest)
        if selftest.get("pass") is not True:
            raise HarnessStop("NOT_QUALIFIED", "selftest", "deterministic structural self-test failed")
        capability = capability_check()
        atomic_json(execution_root / "CAPABILITY.json", capability)
        expected_labels = load_expected(HERE / "EXPECTED_LABELS.json")
        for ordinal in range(1, RUN_COUNT + 1):
            runs.append(run_child(execution_id, execution_root, ordinal, expected_labels))
            atomic_json(execution_root / "RUN_RECEIPTS.json", {"runs": runs})
        write_result(execution_root,"QUALIFIED",head,fixture,selftest,capability,runs,None)
        print("HARNESS_STATUS=QUALIFIED")
        print(f"EXECUTION_ID={execution_id}")
        print(f"EXECUTION_DIR={execution_root}")
        print(f"COMPLETED_RUNS={len(runs)}")
        print("RC1_RESUME_AUTHORIZED=no")
        return 0
    except HarnessStop as exc:
        failure = {"step": exc.step, "detail": exc.detail}
        if execution_root is not None:
            write_result(execution_root,exc.status,head,fixture,selftest,capability,runs,failure)
        print(f"HARNESS_STATUS={exc.status}")
        print(f"EXECUTION_ID={execution_id or 'none'}")
        print(f"EXECUTION_DIR={execution_root or 'none'}")
        print(f"COMPLETED_RUNS={len(runs)}")
        print(f"FAILING_STEP={exc.step}")
        print(f"ERROR={exc.detail}")
        print("RC1_RESUME_AUTHORIZED=no")
        return 20
    except Exception as exc:
        failure = {"step": "unexpected_harness_error", "detail": f"{type(exc).__name__}: {exc}"}
        if execution_root is not None:
            write_result(execution_root,"HARNESS_ERROR",head,fixture,selftest,capability,runs,failure)
        print("HARNESS_STATUS=HARNESS_ERROR")
        print(f"EXECUTION_ID={execution_id or 'none'}")
        print(f"EXECUTION_DIR={execution_root or 'none'}")
        print(f"COMPLETED_RUNS={len(runs)}")
        print(f"ERROR={type(exc).__name__}: {exc}")
        print("RC1_RESUME_AUTHORIZED=no")
        return 21


if __name__ == "__main__":
    raise SystemExit(main())
