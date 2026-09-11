from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "research" / "proposition_compiler_evaluator_rc1"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_rc0_regression_surface() -> None:
    evaluator = load("pc_rc1_eval_test", ROOT / "evaluator.py")
    gold = {
        row["case_id"]: row["expected_disposition"]
        for row in rows(ROOT / "GOLD" / "regression_gold.jsonl")
    }
    got = {
        case["case_id"]: evaluator.evaluate(case)["disposition"]
        for case in rows(ROOT / "regression_cases.jsonl")
    }
    assert got == gold


def test_replay_is_byte_identical() -> None:
    evaluator = load("pc_rc1_eval_replay", ROOT / "evaluator.py")
    cases = rows(ROOT / "regression_cases.jsonl")
    first = [evaluator.evaluate(case) for case in cases]
    second = [evaluator.evaluate(case) for case in cases]
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":")
    )


def test_target_runtime_does_not_reference_gold() -> None:
    for name in ("evaluator.py", "controls.py", "run_raw.py"):
        text = (ROOT / name).read_text().lower()
        assert "gold.jsonl" not in text
        assert "expected_disposition" not in text
