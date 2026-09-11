#!/usr/bin/env python3
"""Raw execution stage. Must not import or inspect gold."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import controls
import evaluator


def canonical(row: dict) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_rows(path: Path, rows: list[dict]) -> str:
    data = "".join(canonical(row) + "\n" for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8", newline="\n")
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("cases")
    p.add_argument("output_dir")
    args = p.parse_args()
    cases = load_cases(Path(args.cases))
    out = Path(args.output_dir)
    target_rows = [evaluator.evaluate(c) for c in cases]
    hashes = {"TARGET": write_rows(out / "target_raw.jsonl", target_rows)}
    for name in controls.CONTROLS:
        rows = controls.evaluate_control(name, cases)
        hashes[name] = write_rows(out / f"{name}.jsonl", rows)
    (out / "RAW_HASHES.json").write_text(canonical(hashes) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
