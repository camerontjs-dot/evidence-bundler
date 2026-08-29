from pathlib import Path

from research.source_access_firewall.static_guard import scan_paths, scan_source_text


def test_direct_parquet_import_outside_safe_reader_is_rejected():
    findings = scan_source_text(
        "import pyarrow.parquet as pq\n",
        path="research/future_scientific_reader.py",
        safe_reader=False,
    )
    assert "PARQUET_BYPASS_IMPORT" in {item["code"] for item in findings}


def test_research_scope_catches_future_direct_reader(tmp_path: Path):
    future = tmp_path / "research" / "future_scientific_reader.py"
    future.parent.mkdir(parents=True)
    future.write_text(
        "import pyarrow.parquet as pq\n"
        "def read(path):\n"
        "    return pq.read_table(path, columns=['query_id'])\n",
        encoding="utf-8",
    )
    findings = scan_paths((tmp_path / "research").rglob("*.py"), tmp_path)
    codes = {item["code"] for item in findings}
    assert "PARQUET_BYPASS_IMPORT" in codes
    assert "PARQUET_BYPASS_CALL" in codes
