from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

LABELS = {"KEEP_DISTINCT", "DROP_REDUNDANT", "DROP_DISTRACTOR", "UNRESOLVED"}
RESULT_SCHEMA = "eb-codex-serialization-harness-result-v1"


class DuplicateKeyError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise DuplicateKeyError(f"duplicate JSON object key: {key}")
        out[key] = value
    return out


def load_json_no_duplicates_text(text: str) -> Any:
    return json.loads(text, object_pairs_hook=reject_duplicate_pairs)


def load_json_no_duplicates(path: Path) -> Any:
    return load_json_no_duplicates_text(path.read_text(encoding="utf-8"))


def load_expected(path: Path) -> dict[str, str]:
    obj = load_json_no_duplicates(path)
    if not isinstance(obj, dict) or not obj:
        raise ValueError("expected-label map must be a non-empty object")
    for rid, label in obj.items():
        if not isinstance(rid, str) or label not in LABELS:
            raise ValueError("expected-label map invalid")
    return obj


def validate_output_text(
    text: str,
    expected_labels: dict[str, str],
    expected_reviewer_id: str,
) -> dict[str, Any]:
    obj = load_json_no_duplicates_text(text)
    if not isinstance(obj, dict):
        raise ValueError("final output must be one JSON object")
    if set(obj) != {"schema", "reviewer_id", "labels"}:
        raise ValueError(f"top-level key mismatch: {sorted(obj)}")
    if obj["schema"] != RESULT_SCHEMA:
        raise ValueError("result schema mismatch")
    if obj["reviewer_id"] != expected_reviewer_id:
        raise ValueError("reviewer_id mismatch")
    labels = obj["labels"]
    if not isinstance(labels, dict):
        raise ValueError("labels must be an object")
    expected_ids = set(expected_labels)
    actual_ids = set(labels)
    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids)
        extra = sorted(actual_ids - expected_ids)
        raise ValueError(f"relation-id set mismatch missing={missing} extra={extra}")
    for rid, got in labels.items():
        if got not in LABELS:
            raise ValueError(f"invalid label for {rid}: {got}")
        want = expected_labels[rid]
        if got != want:
            raise ValueError(f"deterministic label mismatch for {rid}: {got} != {want}")
    return obj


def validate_output_file(
    path: Path,
    expected_labels: dict[str, str],
    expected_reviewer_id: str,
) -> dict[str, Any]:
    return validate_output_text(
        path.read_text(encoding="utf-8"),
        expected_labels,
        expected_reviewer_id,
    )


_ALLOWED_COMMANDS = {
    "cat SYNTHETIC_INPUT.json SERIALIZATION_TASK.md",
    "/bin/zsh -lc 'cat SYNTHETIC_INPUT.json SERIALIZATION_TASK.md'",
    "/bin/bash -lc 'cat SYNTHETIC_INPUT.json SERIALIZATION_TASK.md'",
}


def extract_trace_final_message(trace_path: Path) -> tuple[str, dict[str, Any]]:
    completed_commands: list[str] = []
    final_messages: list[str] = []
    forbidden_items: list[str] = []
    thread_ids: list[str] = []

    for raw in trace_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        event = json.loads(raw)
        if event.get("type") == "thread.started" and isinstance(event.get("thread_id"), str):
            thread_ids.append(event["thread_id"])
        if event.get("type") != "item.completed":
            continue
        item = event.get("item") or {}
        typ = item.get("type")
        if typ == "command_execution":
            cmd = item.get("command")
            if isinstance(cmd, str):
                completed_commands.append(cmd)
        elif typ in {"agent_message", "assistant_message"}:
            text = item.get("text")
            if isinstance(text, str):
                final_messages.append(text)
        elif typ in {"mcp_tool_call", "web_search", "file_change", "collab_tool_call"}:
            forbidden_items.append(str(typ))

    if len(completed_commands) != 1:
        raise ValueError(f"expected exactly one completed child command, got {len(completed_commands)}")
    if completed_commands[0] not in _ALLOWED_COMMANDS:
        raise ValueError(f"unexpected child command: {completed_commands[0]}")
    if forbidden_items:
        raise ValueError(f"forbidden child trace items: {forbidden_items}")
    if len(final_messages) != 1:
        raise ValueError(f"expected exactly one completed agent message, got {len(final_messages)}")
    if len(set(thread_ids)) > 1:
        raise ValueError(f"multiple thread IDs in one child trace: {thread_ids}")

    meta = {
        "completed_command": completed_commands[0],
        "completed_agent_message_count": len(final_messages),
        "thread_id": thread_ids[0] if thread_ids else None,
    }
    return final_messages[0], meta


def validate_trace_and_final(
    trace_path: Path,
    final_path: Path,
    expected_labels: dict[str, str],
    expected_reviewer_id: str,
) -> dict[str, Any]:
    trace_message, trace_meta = extract_trace_final_message(trace_path)
    final_text = final_path.read_text(encoding="utf-8")
    if trace_message.strip() != final_text.strip():
        raise ValueError("trace final agent message differs from --output-last-message file")
    validate_output_text(trace_message, expected_labels, expected_reviewer_id)
    validate_output_text(final_text, expected_labels, expected_reviewer_id)
    return {
        **trace_meta,
        "trace_final_sha256": sha256_bytes(trace_message.strip().encode("utf-8")),
        "output_final_sha256": sha256_bytes(final_text.strip().encode("utf-8")),
        "trace_final_text_equal": True,
    }
