#!/usr/bin/env python3
"""Check frozen reviewed bundles with installed canonical B/CAL; no semantic assessment."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PINS = {"contract_b": "c314e53bd91c0736aa4370a364673b069aceb43e",
        "cal": "64b6c7702696c851057c1cf0b2c105b1c81db543"}
EXTENSION = "extensions/contract-b-factual-context-v1.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root):
    return {p.relative_to(root).as_posix(): digest(p)
            for p in sorted(root.rglob("*")) if p.is_file()}


def error(exc):
    return {"type": type(exc).__name__, "message": str(exc)}


def check_case(case_id, directory, output, canonical, consumer):
    native_path = directory / "native_eb_v1_package.json"
    receipt_path = directory / "projection_receipt.json"
    native, receipt = read(native_path), read(receipt_path)
    expected = sorted((r["proposition_id"], r["passage_id"]) for r in native["candidates"]
                      if r["selection_state"] == "retained" and r["admission_state"] == "accepted")
    row = {"case_id": case_id, "native_file_sha256": digest(native_path),
           "native_package_sha256": native["package_sha256"],
           "receipt_file_sha256": digest(receipt_path), "receipt_sha256": receipt["receipt_sha256"],
           "expected_admitted_pairs": expected, "errors": []}
    binding = receipt["native_package_sha256"] == native["package_sha256"]
    row["receipt_native_binding"] = binding
    bundle = directory / "contract_b"
    try:
        report = canonical.verify(bundle, against_pin="1.2.0")
        row["canonical"] = {"passed": report.passed, "errors": report.errors,
                            "checked_files": report.checked_files,
                            "extension_checked": EXTENSION in report.checked_files}
    except Exception as exc:
        row["errors"].append({"phase": "canonical", **error(exc)})
    try:
        view = consumer.load_contract_b_intake(bundle, deviations_dir=output / case_id)
        require(view.extension_state == "present", "CAL factual extension absent")
        require(view.intake_ledger is not None and view.semantic_context is not None,
                "CAL intake or semantic-context view absent")
        actual = sorted((c["claim_id"], p["passage_id"])
                        for c in view.semantic_context["claims"] for p in c["admitted_passages"])
        row["cal"] = {"extension_state": view.extension_state, "actual_admitted_pairs": actual,
                      "exact_pair_match": actual == expected}
    except Exception as exc:
        row["errors"].append({"phase": "cal", **error(exc)})
    row["passed"] = (binding and len(expected) == len(set(expected)) and not row["errors"]
                     and row.get("canonical", {}).get("passed", False)
                     and row.get("canonical", {}).get("extension_checked", False)
                     and row.get("cal", {}).get("exact_pair_match", False))
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="Completed replay run.")
    parser.add_argument("--output", type=Path, required=True, help="Fresh report directory.")
    parser.add_argument("--installed-identity", type=Path, required=True,
                        help="Separate receipt binding installed artifacts to expected commits.")
    args = parser.parse_args()
    run, output = args.run_dir.resolve(), args.output.resolve()
    if output.is_relative_to(run) or output.exists():
        parser.error("output must be fresh and outside the replay run")
    output.mkdir(parents=True, exist_ok=False)
    record = {"schema": "eb-v1-workflow-consumer-check-v1", "run_dir": str(run),
              "at_utc": datetime.now(UTC).isoformat(), "checker_sha256": digest(Path(__file__)),
              "expected_authority_commits": PINS, "cases": [], "errors": [],
              "identity_limit": "Pins require separately recorded installed artifact identity. "
              "This check binds that receipt but does not attest commits from module versions.",
              "scope": "Actual B/CAL integrity and admitted-pair checks; no semantic validation."}
    try:
        identity = args.installed_identity.resolve()
        record["installed_identity_receipt"] = {"path": str(identity), "sha256": digest(identity)}
        result_path = run / "replay/RESULT.json"
        result = read(result_path)
        require(result["status"] == "REPLAY_COMPLETE", "replay is not complete")
        root = run / "replay/outputs"
        require(hashes(root) == result["output_hashes"], "reviewed output hashes changed")
        require(digest(run / "replay/REVIEW-FREEZE.json") == result["review_freeze_sha256"],
                "review freeze changed")
        case_ids = [f"p{i:02d}" for i in range(1, 9)]
        require(sorted(p.name for p in root.iterdir()) == case_ids, "expected eight case outputs")
        record["replay_result_sha256"] = digest(result_path)
        record["recorded_output_hashes_verified"] = True
        record["runtime"] = {"python": sys.version, "executable": sys.executable,
                             "prefix": sys.prefix, "modules": {}, "versions": {}}
        modules = []
        for name in ("validators.verify_contract_integrity",
                     "claim_audit_lab.contracts.factual_context"):
            module = importlib.import_module(name)
            origin = Path(module.__file__).resolve()
            record["runtime"]["modules"][name] = {"path": str(origin), "sha256": digest(origin)}
            modules.append(module)
        for name in ("apparatus-contracts", "claim-audit-lab", "evidence-bundler"):
            record["runtime"]["versions"][name] = importlib.metadata.version(name)
        for cid in case_ids:
            try:
                row = check_case(cid, root / cid, output / "cal-deviations", *modules)
            except Exception as exc:
                row = {"case_id": cid, "passed": False, "errors": [error(exc)]}
            record["cases"].append(row)
        require(hashes(root) == result["output_hashes"], "consumer checks changed reviewed outputs")
    except Exception as exc:
        record["errors"].append(error(exc))
    passed = not record["errors"] and len(record["cases"]) == 8
    record["passed"] = passed and all(row["passed"] for row in record["cases"])
    record["disposition"] = ("PASS" if record["passed"] else "FAIL") + "_B_CAL_CONSUMER_CHECKS"
    with (output / "RESULT.json").open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(record["disposition"])
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
