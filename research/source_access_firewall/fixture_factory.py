from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

import pyarrow as pa
import pyarrow.parquet as pq

TRIPWIRE_PREFIX = "FORBIDDEN_TRIPWIRE_DO_NOT_DESERIALIZE"
FORBIDDEN_VALUES: dict[str, Any] = {
    "nuggets": [f"{TRIPWIRE_PREFIX}:nuggets"],
    "relevant_corpus_ids": [f"{TRIPWIRE_PREFIX}:relevant"],
    "non_relevant_corpus_ids": [f"{TRIPWIRE_PREFIX}:nonrelevant"],
    "answer_text": f"{TRIPWIRE_PREFIX}:answer_text",
    "accepted_answer": f"{TRIPWIRE_PREFIX}:accepted_answer",
    "evidence": f"{TRIPWIRE_PREFIX}:evidence",
    "rationale": f"{TRIPWIRE_PREFIX}:rationale",
    "retrieval_score": 999999.125,
    "candidate_ids": [f"{TRIPWIRE_PREFIX}:candidate"],
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _rows(count: int) -> list[dict[str, Any]]:
    rows = []
    for i in range(count):
        row: dict[str, Any] = {
            "query_id": f"q-{i:03d}",
            "query_title": f"Synthetic title {i}",
            "query_text": f"Synthetic query text {i}",
        }
        for key, value in FORBIDDEN_VALUES.items():
            if isinstance(value, list):
                row[key] = [f"{item}:{i}" for item in value]
            elif isinstance(value, str):
                row[key] = f"{value}:{i}"
            else:
                row[key] = value + i
        rows.append(row)
    return rows


def write_query_fixture(
    path: Path,
    *,
    row_count: int = 4,
    column_order: Sequence[str] | None = None,
    extra_unknown: bool = False,
    forbidden_alias: str | None = None,
    unknown_renamed: str | None = None,
    nested_forbidden: bool = False,
    omit_allowed: str | None = None,
    row_group_size: int | None = None,
    use_dictionary: bool = True,
) -> dict[str, Any]:
    rows = _rows(row_count)
    if omit_allowed:
        for row in rows:
            row.pop(omit_allowed, None)
    if extra_unknown:
        for i, row in enumerate(rows):
            row["harmless_extra"] = f"unknown-{i}"
    if forbidden_alias:
        for row in rows:
            row[forbidden_alias] = row.pop("relevant_corpus_ids")
    if unknown_renamed:
        for row in rows:
            row[unknown_renamed] = row.pop("relevant_corpus_ids")
    if nested_forbidden:
        for row in rows:
            row["metadata"] = {
                "safe_url": "https://example.invalid/source",
                "evidence": row.pop("evidence"),
            }
    table = pa.Table.from_pylist(rows)
    if column_order is not None:
        table = table.select(list(column_order))
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        table,
        path,
        row_group_size=row_group_size,
        use_dictionary=use_dictionary,
        write_statistics=False,
    )
    return {
        "path": path.name,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": row_count,
        "physical_columns": table.schema.names,
        "row_group_size": row_group_size,
        "use_dictionary": use_dictionary,
        "write_statistics": False,
    }


def write_source_fixture(path: Path, *, nested_metadata: bool = False) -> dict[str, Any]:
    if nested_metadata:
        rows = [
            {
                "_id": "src-1",
                "text": "synthetic source text",
                "metadata": {
                    "url": "https://example.invalid/src",
                    "start_byte": 0,
                    "end_byte": 21,
                    "commit_id": "deadbeef",
                    "evidence": f"{TRIPWIRE_PREFIX}:nested-source",
                },
            }
        ]
    else:
        rows = [
            {
                "_id": "src-1",
                "text": "synthetic source text",
                "url": "https://example.invalid/src",
                "start_byte": 0,
                "end_byte": 21,
                "commit_id": "deadbeef",
                "evidence": f"{TRIPWIRE_PREFIX}:source",
            }
        ]
    table = pa.Table.from_pylist(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, write_statistics=False)
    return {
        "path": path.name,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "physical_columns": table.schema.names,
        "write_statistics": False,
    }


def write_manifest(path: Path, entries: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"fixture_manifest_version": "1.0.0", "fixtures": list(entries)}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
