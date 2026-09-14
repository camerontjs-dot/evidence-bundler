from __future__ import annotations

import json
import tempfile
from pathlib import Path

from validator import (
    DuplicateKeyError,
    extract_trace_final_message,
    validate_output_text,
)


def expect_failure(name: str, fn, expected_types=(Exception,)) -> str:
    try:
        fn()
    except expected_types as exc:
        return type(exc).__name__
    raise AssertionError(f"negative control did not fail: {name}")


def main() -> dict:
    expected = {
        "a": "KEEP_DISTINCT",
        "b": "DROP_REDUNDANT",
        "c": "DROP_DISTRACTOR",
        "d": "UNRESOLVED",
    }
    reviewer_id = "synthetic-selftest"

    good_obj = {
        "schema": "eb-codex-serialization-harness-result-v1",
        "reviewer_id": reviewer_id,
        "labels": expected,
    }
    good_text = json.dumps(good_obj, separators=(",", ":"))
    validate_output_text(good_text, expected, reviewer_id)

    duplicate_text = (
        '{"schema":"eb-codex-serialization-harness-result-v1",'
        '"reviewer_id":"synthetic-selftest","labels":{'
        '"a":"KEEP_DISTINCT","a":"KEEP_DISTINCT",'
        '"b":"DROP_REDUNDANT","c":"DROP_DISTRACTOR","d":"UNRESOLVED"}}'
    )

    missing = json.loads(good_text)
    del missing["labels"]["d"]
    extra = json.loads(good_text)
    extra["labels"]["x"] = "KEEP_DISTINCT"
    invalid = json.loads(good_text)
    invalid["labels"]["a"] = "INVALID"
    wrong = json.loads(good_text)
    wrong["labels"]["a"] = "DROP_REDUNDANT"
    wrong_reviewer = json.loads(good_text)
    wrong_reviewer["reviewer_id"] = "wrong"

    rejected = {
        "duplicate_key": expect_failure(
            "duplicate_key",
            lambda: validate_output_text(duplicate_text, expected, reviewer_id),
            (DuplicateKeyError,),
        ),
        "missing_id": expect_failure(
            "missing_id",
            lambda: validate_output_text(json.dumps(missing), expected, reviewer_id),
        ),
        "extra_id": expect_failure(
            "extra_id",
            lambda: validate_output_text(json.dumps(extra), expected, reviewer_id),
        ),
        "invalid_label": expect_failure(
            "invalid_label",
            lambda: validate_output_text(json.dumps(invalid), expected, reviewer_id),
        ),
        "wrong_valid_label": expect_failure(
            "wrong_valid_label",
            lambda: validate_output_text(json.dumps(wrong), expected, reviewer_id),
        ),
        "wrong_reviewer_id": expect_failure(
            "wrong_reviewer_id",
            lambda: validate_output_text(json.dumps(wrong_reviewer), expected, reviewer_id),
        ),
    }

    with tempfile.TemporaryDirectory(prefix="eb-serialization-selftest-") as td:
        td = Path(td)
        good_trace = td / "good.trace.jsonl"
        good_trace.write_text(
            "\n".join([
                json.dumps({"type":"thread.started","thread_id":"t1"}),
                json.dumps({"type":"item.completed","item":{
                    "type":"command_execution",
                    "command":"cat SYNTHETIC_INPUT.json SERIALIZATION_TASK.md",
                }}),
                json.dumps({"type":"item.completed","item":{
                    "type":"agent_message",
                    "text":good_text,
                }}),
            ]) + "\n",
            encoding="utf-8",
        )
        msg, meta = extract_trace_final_message(good_trace)
        if msg != good_text or meta["thread_id"] != "t1":
            raise AssertionError("good trace extraction mismatch")

        forbidden_trace = td / "forbidden.trace.jsonl"
        forbidden_trace.write_text(
            "\n".join([
                json.dumps({"type":"thread.started","thread_id":"t2"}),
                json.dumps({"type":"item.completed","item":{
                    "type":"command_execution","command":"ls -la",
                }}),
                json.dumps({"type":"item.completed","item":{
                    "type":"agent_message","text":good_text,
                }}),
            ]) + "\n",
            encoding="utf-8",
        )
        rejected["forbidden_command"] = expect_failure(
            "forbidden_command",
            lambda: extract_trace_final_message(forbidden_trace),
        )

        duplicate_message_trace = td / "duplicate-message.trace.jsonl"
        duplicate_message_trace.write_text(
            "\n".join([
                json.dumps({"type":"thread.started","thread_id":"t3"}),
                json.dumps({"type":"item.completed","item":{
                    "type":"command_execution",
                    "command":"cat SYNTHETIC_INPUT.json SERIALIZATION_TASK.md",
                }}),
                json.dumps({"type":"item.completed","item":{"type":"agent_message","text":good_text}}),
                json.dumps({"type":"item.completed","item":{"type":"agent_message","text":good_text}}),
            ]) + "\n",
            encoding="utf-8",
        )
        rejected["duplicate_agent_message"] = expect_failure(
            "duplicate_agent_message",
            lambda: extract_trace_final_message(duplicate_message_trace),
        )

    return {
        "schema":"eb-codex-serialization-harness-selftest-v1",
        "valid_control_passed": True,
        "negative_controls": rejected,
        "pass": all(v != "NOT_REJECTED" for v in rejected.values()),
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
