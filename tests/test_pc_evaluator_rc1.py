from __future__ import annotations
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"research"/"proposition_compiler_evaluator_rc1"
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def rows(path):return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def test_rc0_regression_surface():
    e=load("pc_rc1_eval_test",ROOT/"evaluator.py")
    g={r["case_id"]:r["expected_disposition"] for r in rows(ROOT/"GOLD"/"regression_gold.jsonl")}
    got={c["case_id"]:e.evaluate(c)["disposition"] for c in rows(ROOT/"regression_cases.jsonl")}
    assert got==g
def test_replay_is_byte_identical():
    e=load("pc_rc1_eval_replay",ROOT/"evaluator.py");cases=rows(ROOT/"regression_cases.jsonl")
    a=[e.evaluate(c) for c in cases];b=[e.evaluate(c) for c in cases]
    assert json.dumps(a,sort_keys=True,separators=(",",":"))==json.dumps(b,sort_keys=True,separators=(",",":"))
def test_target_runtime_does_not_reference_gold():
    for name in ("evaluator.py","controls.py","run_raw.py"):
        t=(ROOT/name).read_text().lower();assert "gold.jsonl" not in t;assert "expected_disposition" not in t
