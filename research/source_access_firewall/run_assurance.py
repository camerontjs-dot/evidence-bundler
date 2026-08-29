from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Callable

from research.source_access_firewall import reader
from research.source_access_firewall.fixture_factory import (
    write_manifest,
    write_query_fixture,
    write_source_fixture,
)

REQUEST = ["query_id", "query_title", "query_text"]


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _attempt(name: str, receipt_dir: Path, fn: Callable[[Path], object], expected: str) -> dict[str, object]:
    receipt = receipt_dir / f"{name}.json"
    actual = "SUCCESS"
    failure_code = None
    try:
        fn(receipt)
    except reader.AccessFirewallError as exc:
        actual = "FAIL_CLOSED"
        failure_code = exc.code
    return {
        "case": name,
        "expected": expected,
        "actual": actual,
        "failure_code": failure_code,
        "receipt": receipt.name,
        "pass": actual == expected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    fixtures = out / "fixtures"
    receipts = out / "receipts"
    fixtures.mkdir(parents=True, exist_ok=True)
    receipts.mkdir(parents=True, exist_ok=True)

    manifest = []
    normal = fixtures / "normal.parquet"
    manifest.append(write_query_fixture(normal))
    reordered = fixtures / "reordered.parquet"
    manifest.append(write_query_fixture(reordered, column_order=["nuggets", "query_text", "query_id", "query_title", "relevant_corpus_ids", "non_relevant_corpus_ids", "answer_text", "accepted_answer", "evidence", "rationale", "retrieval_score", "candidate_ids"]))
    unknown = fixtures / "unknown.parquet"
    manifest.append(write_query_fixture(unknown, extra_unknown=True))
    missing = fixtures / "missing.parquet"
    manifest.append(write_query_fixture(missing, omit_allowed="query_text"))
    nested = fixtures / "nested.parquet"
    manifest.append(write_query_fixture(nested, nested_forbidden=True))
    alias = fixtures / "alias.parquet"
    manifest.append(write_query_fixture(alias, forbidden_alias="rel_ids"))
    unknown_renamed = fixtures / "unknown-renamed.parquet"
    manifest.append(write_query_fixture(unknown_renamed, unknown_renamed="mystery_relblob"))
    rowgroups = fixtures / "rowgroups.parquet"
    manifest.append(write_query_fixture(rowgroups, row_count=7, row_group_size=2))
    source = fixtures / "source.parquet"
    manifest.append(write_source_fixture(source))
    write_manifest(out / "fixture-manifest.json", manifest)

    def run_one(path: Path, receipt: Path, requested=REQUEST, registry=None):
        return reader.read_projected(
            artifact_id=f"synthetic:{path.name}",
            artifact_type="freshstack_query_parquet",
            paths=[path],
            requested_logical_fields=requested,
            receipt_path=receipt,
            batch_size=2,
            registry=registry,
        )

    cases = [
        _attempt("normal", receipts, lambda r: run_one(normal, r), "SUCCESS"),
        _attempt("reordered", receipts, lambda r: run_one(reordered, r), "SUCCESS"),
        _attempt("extra_unknown", receipts, lambda r: run_one(unknown, r), "SUCCESS"),
        _attempt("missing_required", receipts, lambda r: run_one(missing, r), "FAIL_CLOSED"),
        _attempt("forbidden_present_not_requested", receipts, lambda r: run_one(normal, r), "SUCCESS"),
        _attempt("forbidden_requested", receipts, lambda r: run_one(normal, r, [*REQUEST, "nuggets"]), "FAIL_CLOSED"),
        _attempt("wildcard", receipts, lambda r: run_one(normal, r, ["*"]), "FAIL_CLOSED"),
        _attempt("columns_none", receipts, lambda r: run_one(normal, r, None), "FAIL_CLOSED"),
        _attempt("nested_forbidden", receipts, lambda r: run_one(nested, r), "SUCCESS"),
        _attempt("registered_alias", receipts, lambda r: run_one(alias, r), "SUCCESS"),
        _attempt("unknown_renamed", receipts, lambda r: run_one(unknown_renamed, r), "SUCCESS"),
        _attempt("multiple_row_groups", receipts, lambda r: run_one(rowgroups, r), "SUCCESS"),
    ]
    empty_registry = copy.deepcopy(reader.load_registry())
    empty_registry["artifact_types"]["freshstack_query_parquet"]["allowed_logical_to_physical"] = {}
    cases.append(_attempt("empty_allowlist", receipts, lambda r: run_one(normal, r, REQUEST, empty_registry), "FAIL_CLOSED"))
    corrupt = fixtures / "corrupt.parquet"
    corrupt.write_bytes(b"not parquet")
    cases.append(_attempt("corrupt_parquet", receipts, lambda r: run_one(corrupt, r), "FAIL_CLOSED"))

    summary = {
        "assurance_run_version": "1.0.0",
        "case_count": len(cases),
        "passed": sum(1 for case in cases if case["pass"]),
        "failed": sum(1 for case in cases if not case["pass"]),
        "cases": cases,
    }
    _write(out / "dummy-adversarial-results.json", summary)
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
