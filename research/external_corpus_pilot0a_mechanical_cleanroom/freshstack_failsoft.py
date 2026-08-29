from __future__ import annotations

import importlib.util
import json
import os
from collections import defaultdict
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("acquire_sources.py")
spec = importlib.util.spec_from_file_location("pilot0a_acquire", MODULE_PATH)
m = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m)

OUT = Path(os.environ.get("PILOT0A_OUT", "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    api = m.HfApi()
    official_files = m.hf_files(m.CORPUS_REPO, m.CORPUS_REV)
    query_files = m.hf_files(m.QUERY_REPO, m.QUERY_REV)

    official_rows: dict[str, list[dict]] = {}
    query_receipt = {}
    topic_receipt = {}

    for topic, selected_index in m.TOPICS.items():
        cfiles = m.data_files_for_topic(official_files, topic, "train")
        qfiles = m.data_files_for_topic(query_files, topic, "test")
        cpaths = [m.download_hf(m.CORPUS_REPO, m.CORPUS_REV, f) for f in cfiles]
        qpaths = [m.download_hf(m.QUERY_REPO, m.QUERY_REV, f) for f in qfiles]

        rows = []
        for row in m.iter_parquet_rows(cpaths):
            rows.append(m.flatten_meta(row))
        official_rows[topic] = rows

        qcount = 0
        selected = None
        for i, row in enumerate(m.iter_parquet_rows(qpaths)):
            qcount += 1
            if i == selected_index:
                selected = {
                    "topic": topic,
                    "physical_test_row_index": selected_index,
                    "query_id": str(row.get("query_id", row.get("id", ""))),
                    "query_title": row.get("query_title", "") or "",
                    "query_text": row.get("query_text", "") or "",
                }

        query_receipt[topic] = {
            "frozen_selected_index": selected_index,
            "observed_test_rows": qcount,
            "selected_row_present": selected is not None,
            "files": qfiles,
            "selected_query": selected,
        }
        topic_receipt[topic] = {
            "official_corpus_rows": len(rows),
            "official_corpus_files": cfiles,
            "official_schema": m.schema_names(cpaths[0]) if cpaths else [],
            "official_file_sha256": {f: m.sha256_bytes(p.read_bytes()) for f, p in zip(cfiles, cpaths)},
        }

    m.write_json("freshstack-query-reconstruction.json", {
        "dataset": m.QUERY_REPO,
        "revision": m.QUERY_REV,
        "topics": query_receipt,
        "no_readme_opened": True,
        "no_qrels_opened": True,
        "no_candidate_lists_opened": True,
        "no_retrieval_results_opened": True,
    })
    m.write_json("freshstack-official-corpus-summary.json", {
        "dataset": m.CORPUS_REPO,
        "revision": m.CORPUS_REV,
        "topics": topic_receipt,
    })

    hist = m.find_historical_revision(api, official_files)
    join = {
        "historical_discovery": hist,
        "status": "NOT_EXECUTED",
        "topics": {},
        "unmatched_official": 0,
        "ambiguous_official": 0,
        "duplicate_historical_keys": 0,
        "unmatched_historical": 0,
    }
    failures = []

    if hist.get("revision"):
        hrev = hist["revision"]
        hfiles = m.hf_files(m.CORPUS_REPO, hrev)
        join["status"] = "EXECUTED"
        for topic, rows in official_rows.items():
            hnames = m.data_files_for_topic(hfiles, topic, "train")
            hpaths = [m.download_hf(m.CORPUS_REPO, hrev, f) for f in hnames]
            by_key = defaultdict(list)
            hcount = 0
            for row in m.iter_parquet_rows(hpaths):
                flat = m.flatten_meta(row)
                by_key[m.row_key(topic, flat)].append(flat)
                hcount += 1
            duplicate_keys = sum(1 for matches in by_key.values() if len(matches) > 1)
            matched_keys = set()
            unmatched = 0
            ambiguous = 0
            for row in rows:
                key = m.row_key(topic, row)
                matches = by_key.get(key, [])
                if len(matches) == 1:
                    row["commit_id"] = matches[0].get("commit_id")
                    matched_keys.add(key)
                elif len(matches) == 0:
                    unmatched += 1
                    failures.append({"topic": topic, "_id": row["_id"], "reason": "UNMATCHED_OFFICIAL", "text_sha256": key[2]})
                else:
                    ambiguous += 1
                    failures.append({"topic": topic, "_id": row["_id"], "reason": "AMBIGUOUS_OFFICIAL", "match_count": len(matches), "text_sha256": key[2]})
            unmatched_hist = sum(len(v) for k, v in by_key.items() if k not in matched_keys)
            join["topics"][topic] = {
                "official_rows": len(rows),
                "historical_rows": hcount,
                "historical_files": hnames,
                "historical_file_sha256": {f: m.sha256_bytes(p.read_bytes()) for f, p in zip(hnames, hpaths)},
                "unmatched_official": unmatched,
                "ambiguous_official": ambiguous,
                "duplicate_historical_keys": duplicate_keys,
                "unmatched_historical_rows": unmatched_hist,
            }
            join["unmatched_official"] += unmatched
            join["ambiguous_official"] += ambiguous
            join["duplicate_historical_keys"] += duplicate_keys
            join["unmatched_historical"] += unmatched_hist

    m.write_json("freshstack-provenance-join-summary.json", join)
    with (OUT / "freshstack-join-failures.jsonl").open("w", encoding="utf-8") as f:
        for row in failures:
            m.safe_json(row)
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    binding = {"status": "NOT_EXECUTED", "reason": "deterministic historical join unavailable or incomplete"}
    if join["status"] == "EXECUTED" and join["unmatched_official"] == 0 and join["ambiguous_official"] == 0:
        binding = m.verify_source_bindings(official_rows)
        binding["status"] = "EXECUTED"
    m.write_json("freshstack-source-binding-summary.json", binding)
    print("FreshStack fail-soft source-only reconstruction completed; inspect artifact only.")


if __name__ == "__main__":
    main()
