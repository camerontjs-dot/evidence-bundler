from __future__ import annotations

import copy
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from research.source_access_firewall import reader
from research.source_access_firewall.fixture_factory import (
    FORBIDDEN_VALUES,
    TRIPWIRE_PREFIX,
    write_query_fixture,
    write_source_fixture,
)
from research.source_access_firewall.static_guard import scan_source_text

REQUEST = ["query_id", "query_title", "query_text"]


def _read(tmp_path: Path, fixture: Path, *, requested=REQUEST, registry=None):
    receipt = tmp_path / "receipt.json"
    result = reader.read_projected(
        artifact_id="synthetic-query",
        artifact_type="freshstack_query_parquet",
        paths=[fixture],
        requested_logical_fields=requested,
        receipt_path=receipt,
        batch_size=2,
        registry=registry,
    )
    return result, json.loads(receipt.read_text(encoding="utf-8"))


def _returned_rows(result: reader.AccessResult):
    return [row for file_batches in result.batches_by_file for batch in file_batches for row in batch.to_pylist()]


def test_normal_allowlisted_query_read_never_returns_tripwire(tmp_path: Path, capsys):
    fixture = tmp_path / "normal.parquet"
    write_query_fixture(fixture)
    result, receipt = _read(tmp_path, fixture)
    rows = _returned_rows(result)
    assert rows and set(rows[0]) == set(REQUEST)
    assert TRIPWIRE_PREFIX not in json.dumps(rows, sort_keys=True)
    assert receipt["forbidden_columns_deserialized"] is False
    assert receipt["result"] == "SUCCESS"
    assert all(call["columns_argument"] == REQUEST for call in receipt["physical_read_calls"])
    captured = capsys.readouterr()
    assert TRIPWIRE_PREFIX not in captured.out
    assert TRIPWIRE_PREFIX not in captured.err


def test_reordered_physical_columns(tmp_path: Path):
    fixture = tmp_path / "reordered.parquet"
    base_order = list(FORBIDDEN_VALUES) + ["query_text", "query_id", "query_title"]
    write_query_fixture(fixture, column_order=base_order)
    result, receipt = _read(tmp_path, fixture)
    assert set(_returned_rows(result)[0]) == set(REQUEST)
    assert receipt["forbidden_columns_deserialized"] is False


def test_extra_unknown_column_is_reported_but_not_returned(tmp_path: Path):
    fixture = tmp_path / "unknown.parquet"
    write_query_fixture(fixture, extra_unknown=True)
    result, receipt = _read(tmp_path, fixture)
    unknown = receipt["unknown_columns_present"][0]["columns"]
    assert "harmless_extra" in unknown
    assert "harmless_extra" not in _returned_rows(result)[0]


def test_missing_required_allowed_column_fails_closed_before_read(tmp_path: Path):
    fixture = tmp_path / "missing.parquet"
    write_query_fixture(fixture, omit_allowed="query_text")
    with pytest.raises(reader.AccessFirewallError) as exc:
        _read(tmp_path, fixture)
    assert exc.value.code == "MISSING_REQUIRED_FIELD"
    assert exc.value.receipt["physical_read_calls"] == []


def test_forbidden_present_but_not_requested_is_safe(tmp_path: Path):
    fixture = tmp_path / "forbidden-present.parquet"
    write_query_fixture(fixture)
    result, receipt = _read(tmp_path, fixture)
    assert "nuggets" in receipt["explicitly_forbidden_columns_present"][0]["columns"]
    assert "nuggets" not in _returned_rows(result)[0]
    assert receipt["forbidden_columns_deserialized"] is False


def test_forbidden_explicit_request_fails_closed(tmp_path: Path):
    fixture = tmp_path / "forbidden-request.parquet"
    write_query_fixture(fixture)
    with pytest.raises(reader.AccessFirewallError) as exc:
        _read(tmp_path, fixture, requested=[*REQUEST, "nuggets"])
    assert exc.value.code == "FORBIDDEN_FIELD_REQUESTED"
    assert exc.value.receipt["physical_read_calls"] == []


def test_wildcard_request_fails_closed(tmp_path: Path):
    fixture = tmp_path / "wildcard.parquet"
    write_query_fixture(fixture)
    with pytest.raises(reader.AccessFirewallError) as exc:
        _read(tmp_path, fixture, requested=["*"])
    assert exc.value.code == "WILDCARD_FORBIDDEN"


def test_columns_none_fails_closed(tmp_path: Path):
    fixture = tmp_path / "none.parquet"
    write_query_fixture(fixture)
    with pytest.raises(reader.AccessFirewallError) as exc:
        _read(tmp_path, fixture, requested=None)
    assert exc.value.code == "COLUMNS_NONE_FORBIDDEN"


def test_empty_allowlist_fails_closed(tmp_path: Path):
    fixture = tmp_path / "empty-registry.parquet"
    write_query_fixture(fixture)
    registry = copy.deepcopy(reader.load_registry())
    registry["artifact_types"]["freshstack_query_parquet"]["allowed_logical_to_physical"] = {}
    with pytest.raises(reader.AccessFirewallError) as exc:
        _read(tmp_path, fixture, registry=registry)
    assert exc.value.code == "EMPTY_ALLOWLIST"


def test_nested_forbidden_field_is_detected_and_not_returned(tmp_path: Path):
    fixture = tmp_path / "nested.parquet"
    write_query_fixture(fixture, nested_forbidden=True)
    result, receipt = _read(tmp_path, fixture)
    assert "metadata.evidence" in receipt["explicitly_forbidden_columns_present"][0]["columns"]
    assert TRIPWIRE_PREFIX not in json.dumps(_returned_rows(result), sort_keys=True)


def test_nested_allowed_leaf_projection_does_not_hydrate_forbidden_sibling(tmp_path: Path):
    fixture = tmp_path / "source-nested.parquet"
    write_source_fixture(fixture, nested_metadata=True)
    receipt = tmp_path / "source-receipt.json"
    result = reader.read_projected(
        artifact_id="synthetic-source",
        artifact_type="source_corpus_parquet",
        paths=[fixture],
        requested_logical_fields=["source_id", "source_text", "source_url"],
        receipt_path=receipt,
    )
    rows = _returned_rows(result)
    assert TRIPWIRE_PREFIX not in json.dumps(rows, sort_keys=True)
    assert "metadata.evidence" in result.receipt["explicitly_forbidden_columns_present"][0]["columns"]
    assert result.receipt["forbidden_columns_deserialized"] is False


def test_parent_struct_projection_is_rejected(tmp_path: Path):
    fixture = tmp_path / "source-parent.parquet"
    write_source_fixture(fixture, nested_metadata=True)
    registry = copy.deepcopy(reader.load_registry())
    registry["artifact_types"]["source_corpus_parquet"]["allowed_logical_to_physical"]["source_url"] = ["metadata"]
    receipt = tmp_path / "parent-receipt.json"
    with pytest.raises(reader.AccessFirewallError) as exc:
        reader.read_projected(
            artifact_id="synthetic-source-parent",
            artifact_type="source_corpus_parquet",
            paths=[fixture],
            requested_logical_fields=["source_id", "source_text", "source_url"],
            receipt_path=receipt,
            registry=registry,
        )
    assert exc.value.code == "PARENT_PROJECTION_UNSAFE"
    assert exc.value.receipt["physical_read_calls"] == []


def test_serialization_reorder_dictionary_encoding_invariant(tmp_path: Path):
    first = tmp_path / "dict.parquet"
    second = tmp_path / "plain.parquet"
    write_query_fixture(first, use_dictionary=True)
    write_query_fixture(second, use_dictionary=False)
    a, _ = _read(tmp_path / "a", first)
    b, _ = _read(tmp_path / "b", second)
    assert _returned_rows(a) == _returned_rows(b)


def test_multiple_row_groups(tmp_path: Path):
    fixture = tmp_path / "rowgroups.parquet"
    write_query_fixture(fixture, row_count=7, row_group_size=2)
    result, receipt = _read(tmp_path, fixture)
    assert len(_returned_rows(result)) == 7
    assert receipt["forbidden_columns_deserialized"] is False


def test_multiple_files_are_preflighted_then_projected(tmp_path: Path):
    a = tmp_path / "a.parquet"
    b = tmp_path / "b.parquet"
    write_query_fixture(a, row_count=2)
    write_query_fixture(b, row_count=3, extra_unknown=True)
    receipt = tmp_path / "multi-receipt.json"
    result = reader.read_projected(
        artifact_id="multi",
        artifact_type="freshstack_query_parquet",
        paths=[a, b],
        requested_logical_fields=REQUEST,
        receipt_path=receipt,
        batch_size=2,
    )
    assert [sum(batch.num_rows for batch in group) for group in result.batches_by_file] == [2, 3]
    assert result.receipt["forbidden_columns_deserialized"] is False


def test_schema_drift_fails_before_any_file_is_materialized(tmp_path: Path):
    a = tmp_path / "ok.parquet"
    b = tmp_path / "drift.parquet"
    write_query_fixture(a)
    write_query_fixture(b, omit_allowed="query_text")
    receipt = tmp_path / "drift-receipt.json"
    with pytest.raises(reader.AccessFirewallError) as exc:
        reader.read_projected(
            artifact_id="drift",
            artifact_type="freshstack_query_parquet",
            paths=[a, b],
            requested_logical_fields=REQUEST,
            receipt_path=receipt,
        )
    assert exc.value.code == "MISSING_REQUIRED_FIELD"
    assert exc.value.receipt["physical_read_calls"] == []


def test_registered_forbidden_alias_is_blocked(tmp_path: Path):
    fixture = tmp_path / "alias.parquet"
    write_query_fixture(fixture, forbidden_alias="rel_ids")
    _, receipt = _read(tmp_path, fixture)
    assert "rel_ids" in receipt["explicitly_forbidden_columns_present"][0]["columns"]
    with pytest.raises(reader.AccessFirewallError) as exc:
        _read(tmp_path / "request", fixture, requested=[*REQUEST, "rel_ids"])
    assert exc.value.code == "FORBIDDEN_FIELD_REQUESTED"


def test_unknown_renamed_field_is_unknown_and_unread(tmp_path: Path):
    fixture = tmp_path / "unknown-renamed.parquet"
    write_query_fixture(fixture, unknown_renamed="mystery_relblob")
    result, receipt = _read(tmp_path, fixture)
    assert "mystery_relblob" in receipt["unknown_columns_present"][0]["columns"]
    assert "mystery_relblob" not in _returned_rows(result)[0]


def test_malformed_schema_duplicate_field_fails_closed(monkeypatch, tmp_path: Path):
    fixture = tmp_path / "valid.parquet"
    write_query_fixture(fixture)
    malformed = pa.schema([pa.field("query_id", pa.string()), pa.field("query_id", pa.string()), pa.field("query_title", pa.string()), pa.field("query_text", pa.string())])
    monkeypatch.setattr(pq, "read_schema", lambda _path: malformed)
    with pytest.raises(reader.AccessFirewallError) as exc:
        _read(tmp_path, fixture)
    assert exc.value.code == "MALFORMED_SCHEMA"
    assert exc.value.receipt["physical_read_calls"] == []


def test_corrupt_parquet_fails_during_schema_preflight(tmp_path: Path):
    fixture = tmp_path / "corrupt.parquet"
    fixture.write_bytes(b"not parquet")
    with pytest.raises(reader.AccessFirewallError) as exc:
        _read(tmp_path, fixture)
    assert exc.value.code == "SCHEMA_INSPECTION_FAILED"
    assert exc.value.receipt["physical_read_calls"] == []


def test_projected_api_failure_has_no_unprojected_fallback(monkeypatch, tmp_path: Path):
    fixture = tmp_path / "api-failure.parquet"
    write_query_fixture(fixture)
    seen: dict[str, object] = {}

    class FailingParquet:
        def iter_batches(self, **kwargs):
            seen.update(kwargs)
            raise OSError("synthetic projected API failure")

    monkeypatch.setattr(reader, "_open_parquet_file", lambda _path: FailingParquet())
    with pytest.raises(reader.AccessFirewallError) as exc:
        _read(tmp_path, fixture)
    assert exc.value.code == "PROJECTED_READ_FAILED"
    assert seen["columns"] == REQUEST
    assert seen["use_pandas_metadata"] is False
    assert len(exc.value.receipt["physical_read_calls"]) == 1


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("pf.iter_batches()", "UNPROJECTED_ITER_BATCHES"),
        ("pq.read_table(path)", "UNPROJECTED_READ_TABLE"),
        ("batch.to_pylist()", "BANNED_TO_PYLIST"),
        ("pq.read_pandas(path)", "BANNED_READ_PANDAS"),
        ("from datasets import load_dataset\nload_dataset('x')", "HIGH_LEVEL_DATASET_IMPORT"),
    ],
)
def test_static_guard_catches_unsafe_surfaces(source: str, code: str):
    findings = scan_source_text(source, path="research/source_access_firewall/bad.py", safe_reader=False)
    assert code in {item["code"] for item in findings}


def test_static_guard_allows_explicit_projected_call_inside_reader():
    findings = scan_source_text(
        "pf.iter_batches(columns=['query_id'], use_pandas_metadata=False)",
        path="research/source_access_firewall/reader.py",
        safe_reader=True,
    )
    assert findings == []


def test_static_guard_rejects_none_projection_inside_reader():
    findings = scan_source_text(
        "pf.iter_batches(columns=None)",
        path="research/source_access_firewall/reader.py",
        safe_reader=True,
    )
    assert "UNPROJECTED_ITER_BATCHES" in {item["code"] for item in findings}
