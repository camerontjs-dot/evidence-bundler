from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Iterable

SAFE_READER = "research/source_access_firewall/reader.py"
BANNED_ALWAYS = {"to_pylist", "to_table", "read_pandas", "load_dataset"}
PROJECTED_CALLS = {"iter_batches", "read_table"}


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _columns(node: ast.Call) -> ast.AST | None:
    for keyword in node.keywords:
        if keyword.arg == "columns":
            return keyword.value
    return None


def scan_source_text(source: str, *, path: str, safe_reader: bool) -> list[dict[str, object]]:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return [{"path": path, "line": exc.lineno or 0, "code": "SYNTAX_ERROR"}]
    findings: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] == "datasets":
                    findings.append({"path": path, "line": node.lineno, "code": "HIGH_LEVEL_DATASET_IMPORT"})
                if not safe_reader and alias.name == "pyarrow.parquet":
                    findings.append({"path": path, "line": node.lineno, "code": "PARQUET_BYPASS_IMPORT"})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".", 1)[0] == "datasets":
                findings.append({"path": path, "line": node.lineno, "code": "HIGH_LEVEL_DATASET_IMPORT"})
            if not safe_reader and module == "pyarrow.parquet":
                findings.append({"path": path, "line": node.lineno, "code": "PARQUET_BYPASS_IMPORT"})
        elif isinstance(node, ast.Call):
            name = _call_name(node)
            if name in BANNED_ALWAYS:
                findings.append({"path": path, "line": node.lineno, "code": f"BANNED_{name.upper()}"})
            if name in PROJECTED_CALLS:
                columns = _columns(node)
                if columns is None or (isinstance(columns, ast.Constant) and columns.value is None):
                    findings.append({"path": path, "line": node.lineno, "code": f"UNPROJECTED_{name.upper()}"})
                if not safe_reader:
                    findings.append({"path": path, "line": node.lineno, "code": "PARQUET_BYPASS_CALL"})
            if safe_reader and name in {"print", "debug", "info", "warning", "error", "exception"}:
                findings.append({"path": path, "line": node.lineno, "code": "ROW_LOGGING_SURFACE"})
    return findings


def scan_paths(paths: Iterable[Path], repo_root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in paths:
        if not path.is_file() or path.suffix != ".py":
            continue
        rel = path.relative_to(repo_root).as_posix()
        if "/tests/" in f"/{rel}/" or rel.endswith("/fixture_factory.py") or rel.endswith("/run_assurance.py"):
            continue
        findings.extend(
            scan_source_text(
                path.read_text(encoding="utf-8"),
                path=rel,
                safe_reader=rel == SAFE_READER,
            )
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    module_root = root / "research" / "source_access_firewall"
    findings = scan_paths(module_root.rglob("*.py"), root)
    result = {"guard_version": "1.0.0", "finding_count": len(findings), "findings": findings}
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
