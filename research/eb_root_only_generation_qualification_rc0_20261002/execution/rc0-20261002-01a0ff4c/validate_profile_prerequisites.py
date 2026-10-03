"""Mechanical compatibility check of immutable writer artifacts.

This inspects profile structure only; it judges no root or supplied proposal.
Exit 1 means the frozen profiles cannot satisfy the declared review protocol.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    freeze = json.loads((HERE / "PROFILE-FREEZE.PUBLIC.json").read_bytes())
    for name, expected in freeze["file_sha256"].items():
        assert "sha256:" + hashlib.sha256((HERE / "profiles" / name).read_bytes()).hexdigest() == expected
    config = json.loads((HERE / "profiles/EVALUATOR-CONFIG.json").read_bytes())
    schema = json.loads((HERE / "profiles/REVIEW-SCHEMA.json").read_bytes())
    config_decisions = set(config.get("constraints", {}).get("decision_values", []))
    wire_decisions = set(schema.get("constraints", {}).get("decision_values", []))
    findings = []
    if "uncertain" not in config_decisions or "uncertain" not in wire_decisions:
        findings.append({"id": "MISSING_UNCERTAIN_REVIEW_DECISION", "required_by": "PROFILE-WRITER-TASK.md evaluator mode paragraph", "observed_config_decisions": sorted(config_decisions), "observed_schema_decisions": sorted(wire_decisions)})
    required_fields = {"row_alias", "root_status", "decision", "checks"}
    available = set(schema.get("properties", {})) | set(schema.get("fields", {}))
    if not required_fields <= available:
        findings.append({"id": "DECISIVE_REVIEW_WIRE_UNDEFINED", "required_fields": sorted(required_fields), "defined_fields": sorted(available)})
    if not {"calibration", "decisive"} <= set(config.get("modes", {})):
        findings.append({"id": "EVALUATOR_MODES_UNDEFINED", "observed_modes": sorted(config.get("modes", {}))})
    receipt = {"schema": "eb-generation-profile-prerequisite-check-v1", "checked_at": datetime.now(timezone.utc).isoformat(), "engine": "python3 standard-library structural checks", "code_sha256": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "inputs": freeze["file_sha256"], "findings": findings, "result": "BLOCKED_PROFILE_CONFIGURATION" if findings else "STRUCTURE_COMPLETE", "semantic_cases_evaluated": 0, "generation_capability": "UNKNOWN", "permitted_repair": False}
    with (HERE / "PROFILE-PREREQUISITES.PUBLIC.json").open("x") as output:
        json.dump(receipt, output, indent=2)
        output.write("\n")
    print(json.dumps({"result": receipt["result"], "findings": [item["id"] for item in findings]}))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
