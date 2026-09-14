from __future__ import annotations

import json
import tempfile
from pathlib import Path

from validator import (
    DuplicateKeyError,
    validate_output_text,
    validate_trace_and_final,
)


def expect_failure(name: str, fn, expected_types=(Exception,)) -> str:
    try:
        fn()
    except expected_types as exc:
        return type(exc).__name__
    raise AssertionError(f"negative control did not fail: {name}")


def _write_trace(
    path: Path,
    messages: list[str],
    command: str = "cat SYNTHETIC_INPUT.json SERIALIZATION_TASK.md",
) -> None:
    rows = [json.dumps({"type": "thread.started", "thread_id": "t1"})]
    rows.append(
        json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "command_execution", "command": command},
            }
        )
    )
    rows.extend(
        json.dumps(
            {"type": "item.completed", "item": {"type": "agent_message", "text": text}}
        )
        for text in messages
    )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


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

    with tempfile.TemporaryDirectory(prefix="eb-serialization-selftest-") as td_raw:
        td = Path(td_raw)
        final = td / "FINAL.json"
        final.write_text(good_text, encoding="utf-8")

        good_trace = td / "good.trace.jsonl"
        _write_trace(good_trace, ["I will read the authorized files.", good_text])
        meta = validate_trace_and_final(good_trace, final, expected, reviewer_id)
        if meta["completed_agent_message_count"] != 2:
            raise AssertionError("status+result trace agent-message count mismatch")
        if meta["status_agent_message_count"] != 1:
            raise AssertionError("status+result trace status-message count mismatch")

        forbidden_trace = td / "forbidden.trace.jsonl"
        _write_trace(forbidden_trace, [good_text], command="ls -la")
        rejected["forbidden_command"] = expect_failure(
            "forbidden_command",
            lambda: validate_trace_and_final(forbidden_trace, final, expected, reviewer_id),
        )

        duplicate_result_trace = td / "duplicate-result.trace.jsonl"
        _write_trace(duplicate_result_trace, [good_text, good_text])
        rejected["duplicate_result_message"] = expect_failure(
            "duplicate_result_message",
            lambda: validate_trace_and_final(
                duplicate_result_trace, final, expected, reviewer_id
            ),
        )

        result_not_last_trace = td / "result-not-last.trace.jsonl"
        _write_trace(result_not_last_trace, [good_text, "done"])
        rejected["result_not_last"] = expect_failure(
            "result_not_last",
            lambda: validate_trace_and_final(
                result_not_last_trace, final, expected, reviewer_id
            ),
        )

        malformed_result_trace = td / "malformed-result.trace.jsonl"
        malformed_result = json.dumps(
            {
                "schema": "eb-codex-serialization-harness-result-v1",
                "reviewer_id": reviewer_id,
                "labels": {"a": "KEEP_DISTINCT"},
            }
        )
        _write_trace(malformed_result_trace, [malformed_result, good_text])
        rejected["malformed_result_message"] = expect_failure(
            "malformed_result_message",
            lambda: validate_trace_and_final(
                malformed_result_trace, final, expected, reviewer_id
            ),
        )

    return {
        "schema": "eb-codex-serialization-harness-selftest-v2",
        "valid_control_passed": True,
        "status_message_control_passed": True,
        "negative_controls": rejected,
        "pass": all(v != "NOT_REJECTED" for v in rejected.values()),
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
