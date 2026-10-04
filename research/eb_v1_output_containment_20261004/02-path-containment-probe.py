"""Harmless independent check that untrusted wire IDs cannot escape --out-dir.

All attempted writes stay inside this probe's own scratch directory. No source,
product, scientific record or user artifact is targeted.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def wire(claim_id: str, source_id: str) -> dict:
    claim = "cobalt orchard protocol"
    content = "cobalt orchard protocol appears in this synthetic engineering record."
    obj = {
        "schema": "contract-a-wire-candidate-rc2",
        "handoff_id": "independent-portable-path-probe",
        "producer": {"producer_id": "independent-engineering-probe", "producer_version": "1"},
        "work": {"work_id": "path-containment-only"},
        "root_proposition": {"proposition_id": claim_id, "text": claim, "text_sha256": digest(claim)},
        "decomposition": {"state": "not_decomposed"},
        "sources": [{"source_id": source_id, "media_type": "text/plain; charset=utf-8", "content": content, "content_sha256": digest(content)}],
    }
    encoded = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    obj["handoff_sha256"] = digest(encoded)
    return obj


def main() -> None:
    base = Path(sys.argv[1]).resolve()
    base.mkdir(parents=True, exist_ok=False)
    cli = Path(sys.executable).parent / "evidence-bundler-v1"
    outcomes = []
    for name in ("claim_traversal", "source_traversal", "absolute_claim", "absolute_source"):
        case = base / name
        case.mkdir()
        out = case / "requested-output"
        if "claim" in name:
            target = case / "owned-sentinel.yaml"
            claim_id = str(target.with_suffix("")) if name.startswith("absolute") else "../../../owned-sentinel"
            source_id = "source-safe"
        else:
            target = case / "owned-source" / "source_profile.yaml"
            target.parent.mkdir()
            source_id = str(target.parent) if name.startswith("absolute") else "../../../owned-source"
            claim_id = "claim-safe"
        target.write_text("PROBE_OWNED_SENTINEL_DO_NOT_OVERWRITE\n", encoding="utf-8")
        before = digest(target.read_text(encoding="utf-8"))
        input_path = case / "contract_a.json"
        input_path.write_text(json.dumps(wire(claim_id, source_id), indent=2) + "\n", encoding="utf-8")
        result = subprocess.run([str(cli), "run", str(input_path), "--out-dir", str(out)], cwd=case, text=True, capture_output=True, check=False)
        (case / "stdout.txt").write_text(result.stdout, encoding="utf-8")
        (case / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        after = digest(target.read_text(encoding="utf-8"))
        outcomes.append({"case": name, "command": [str(cli), "run", str(input_path), "--out-dir", str(out)], "exit_code": result.returncode, "outside_target": str(target), "requested_output": str(out), "outside_output": not target.is_relative_to(out), "sentinel_before": before, "sentinel_after": after, "sentinel_overwritten": before != after, "native_written": (out / "native_eb_v1_package.json").exists(), "receipt_written": (out / "projection_receipt.json").exists(), "stderr_tail": result.stderr[-3000:]})
    (base / "results.json").write_text(json.dumps(outcomes, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcomes, indent=2))


if __name__ == "__main__":
    main()
