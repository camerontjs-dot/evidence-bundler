from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT / "research" / "cal_rc0_contract_b_handoff"


def test_runtime_surface_does_not_import_cal_or_evaluator_gold() -> None:
    paths = [
        RESEARCH_ROOT / "build_handoff.py",
        RESEARCH_ROOT / "qualified_handoff.py",
        RESEARCH_ROOT / "qualification_runner.py",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert all(not name.startswith("claim_audit_lab") for name in imported)
        assert "audit_claims" not in text

    runtime_text = (RESEARCH_ROOT / "build_handoff.py").read_text(encoding="utf-8")
    wrapper_text = (RESEARCH_ROOT / "qualified_handoff.py").read_text(encoding="utf-8")
    assert "evaluator_gold" not in runtime_text
    assert "evaluator_gold" not in wrapper_text
