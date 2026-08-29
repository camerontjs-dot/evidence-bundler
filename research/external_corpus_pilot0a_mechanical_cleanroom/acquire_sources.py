from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

OUT = Path(os.environ.get("PILOT0A_OUT", "out"))
OUT.mkdir(parents=True, exist_ok=True)

CORPUS_REPO = "freshstack/corpus-oct-2024"
CORPUS_REV = "069f66dc323e163b48b10d08408d282733d4393b"
QUERY_REPO = "freshstack/queries-oct-2024-unfiltered"
QUERY_REV = "00150066ff2959688ad03ce7148ffb652f2fee38"
TOPICS = {
    "langchain": 271,
    "yolo": 42,
    "laravel": 121,
    "angular": 248,
    "godot": 36,
}
SCIFACT_URL = "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz"
SCIFACT_EXPECTED_SHA256 = "11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be"
SCIFACT_EXPECTED_SIZE = 3115079
SCIFACT_INDICES = [199, 66, 278, 114, 123]

# Scientific firewall: output may contain only source/provenance fields. These names are
# explicitly forbidden from any output before scientific gold freeze.
FORBIDDEN_OUTPUT_KEYS = {
    "nuggets",
    "relevant_corpus_ids",
    "non_relevant_corpus_ids",
    "answer_text",
    "accepted_answer",
    "evidence",
    "label",
    "labels",
    "rationale",
    "rationales",
    "sentences",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def safe_json(obj: Any) -> None:
    def walk(v: Any, path: str = "$") -> None:
        if isinstance(v, dict):
            for k, val in v.items():
                if k in FORBIDDEN_OUTPUT_KEYS:
                    raise RuntimeError(f"forbidden output key at {path}.{k}")
                walk(val, f"{path}.{k}")
        elif isinstance(v, list):
            for i, val in enumerate(v):
                walk(val, f"{path}[{i}]")
    walk(obj)


def write_json(name: str, obj: Any) -> None:
    safe_json(obj)
    p = OUT / name
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def hf_files(repo_id: str, revision: str) -> list[str]:
    api = HfApi()
    files = api.list_repo_files(repo_id=repo_id, repo_type="dataset", revision=revision)
    # Listing a filename is permitted; forbidden surfaces are never downloaded/opened.
    return sorted(files)


def data_files_for_topic(files: Iterable[str], topic: str, split: str) -> list[str]:
    allowed_ext = (".parquet", ".jsonl", ".json")
    out = []
    for f in files:
        fl = f.lower()
        if not fl.endswith(allowed_ext):
            continue
        if topic.lower() not in fl:
            continue
        if split.lower() not in fl:
            continue
        if any(x in fl for x in ("qrel", "nugget", "result", "leaderboard", "retrieval")):
            continue
        out.append(f)
    return sorted(out)


def download_hf(repo_id: str, revision: str, filename: str) -> Path:
    if filename.lower().endswith("readme.md"):
        raise RuntimeError("README download prohibited")
    p = hf_hub_download(repo_id=repo_id, repo_type="dataset", revision=revision, filename=filename)
    return Path(p)


def iter_parquet_rows(paths: list[Path]):
    for p in paths:
        pf = pq.ParquetFile(p)
        for batch in pf.iter_batches(batch_size=4096):
            for row in batch.to_pylist():
                yield row


def schema_names(path: Path) -> list[str]:
    return pq.ParquetFile(path).schema_arrow.names


def flatten_meta(row: dict[str, Any]) -> dict[str, Any]:
    md = row.get("metadata") or {}
    if isinstance(md, str):
        try:
            md = json.loads(md)
        except Exception:
            md = {}
    if not isinstance(md, dict):
        md = {}
    return {
        "_id": str(row.get("_id", row.get("id", ""))),
        "text": row.get("text", "") or "",
        "url": md.get("url", row.get("url")),
        "start": md.get("start_byte", row.get("start_byte")),
        "end": md.get("end_byte", row.get("end_byte")),
        "commit_id": md.get("commit_id", row.get("commit_id")),
    }


def row_key(topic: str, r: dict[str, Any]) -> tuple[Any, ...]:
    return (
        topic,
        r["_id"],
        sha256_text(r["text"]),
        r.get("url"),
        r.get("start"),
        r.get("end"),
    )


def find_historical_revision(api: HfApi, pinned_files: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "searched_via": "same-dataset Hugging Face Git history only",
        "revision": None,
        "schema": None,
        "checked_commits": [],
        "status": "NOT_FOUND",
    }
    try:
        commits = api.list_repo_commits(CORPUS_REPO, repo_type="dataset", revision="main")
    except Exception as e:
        result["status"] = "HISTORY_UNAVAILABLE"
        result["error_type"] = type(e).__name__
        return result

    for c in commits[:40]:
        cid = c.commit_id
        if cid == CORPUS_REV:
            continue
        rec = {"commit_id": cid}
        result["checked_commits"].append(rec)
        try:
            files = hf_files(CORPUS_REPO, cid)
            candidates = data_files_for_topic(files, "langchain", "train")
            if not candidates:
                rec["schema_status"] = "NO_LANGCHAIN_TRAIN_DATA_FILE"
                continue
            p = download_hf(CORPUS_REPO, cid, candidates[0])
            names = schema_names(p)
            rec["schema_names"] = names
            # We only need the presence of commit_id. No relevance-bearing field is read.
            if "commit_id" in names or "metadata" in names:
                first = next(iter_parquet_rows([p]), None)
                if first is None:
                    continue
                flat = flatten_meta(first)
                if flat.get("commit_id"):
                    result.update({"revision": cid, "schema": names, "status": "FOUND"})
                    return result
        except Exception as e:
            rec["error_type"] = type(e).__name__
    return result


def parse_github_url(url: str | None) -> tuple[str, str, str] | None:
    if not url:
        return None
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)$", url)
    if not m:
        return None
    owner, repo, branch, path = m.groups()
    return f"{owner}/{repo}", branch, path


def github_json(url: str) -> Any:
    token = os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "pilot0a-cleanroom"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def github_bytes(url: str) -> bytes:
    token = os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "pilot0a-cleanroom"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def expand_commit(repo: str, commit_id: str) -> str:
    obj = github_json(f"https://api.github.com/repos/{repo}/commits/{commit_id}")
    return obj["sha"]


def source_archive(repo: str, commit: str, target: Path) -> Path:
    data = github_bytes(f"https://api.github.com/repos/{repo}/tarball/{commit}")
    target.write_bytes(data)
    return target


def extract_tar_gz(path: Path, outdir: Path) -> Path:
    with tarfile.open(path, "r:gz") as tf:
        tf.extractall(outdir)
    roots = [p for p in outdir.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(f"unexpected archive root count: {len(roots)}")
    return roots[0]


def verify_source_bindings(official_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    # Group rows by immutable repo+commit after historical join has supplied commit_id.
    groups: dict[tuple[str, str], list[tuple[str, dict[str, Any], str]]] = defaultdict(list)
    parse_failures = []
    for topic, rows in official_rows.items():
        for r in rows:
            parsed = parse_github_url(r.get("url"))
            if not parsed:
                parse_failures.append({"topic": topic, "_id": r["_id"], "reason": "URL_PARSE"})
                continue
            repo, branch, path = parsed
            cid = r.get("commit_id")
            if not cid:
                parse_failures.append({"topic": topic, "_id": r["_id"], "reason": "NO_COMMIT"})
                continue
            groups[(repo, cid)].append((topic, r, path))

    summary: dict[str, Any] = {
        "groups": [],
        "parse_failures": parse_failures,
        "all_rows_bound": False,
    }
    total_checked = 0
    total_failed = len(parse_failures)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for gi, ((repo, cid), items) in enumerate(sorted(groups.items())):
            try:
                full = expand_commit(repo, cid)
                arc = source_archive(repo, full, td / f"src-{gi}.tar.gz")
                root = extract_tar_gz(arc, td / f"src-{gi}")
                failures = []
                file_hashes: dict[str, str] = {}
                for topic, r, relpath in items:
                    fp = root / relpath
                    if not fp.exists() or not fp.is_file():
                        failures.append({"topic": topic, "_id": r["_id"], "reason": "MISSING_SOURCE_FILE", "path": relpath})
                        continue
                    raw = fp.read_bytes()
                    file_hashes.setdefault(relpath, sha256_bytes(raw))
                    try:
                        text = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        failures.append({"topic": topic, "_id": r["_id"], "reason": "SOURCE_UTF8_DECODE", "path": relpath})
                        continue
                    s, e = r.get("start"), r.get("end")
                    if not isinstance(s, int) or not isinstance(e, int) or s < 0 or e < s or e > len(text):
                        failures.append({"topic": topic, "_id": r["_id"], "reason": "OFFSET_RANGE", "path": relpath})
                        continue
                    if text[s:e] != r["text"]:
                        failures.append({"topic": topic, "_id": r["_id"], "reason": "SLICE_MISMATCH", "path": relpath})
                        continue
                    total_checked += 1
                total_failed += len(failures)
                licenses = []
                for cand in sorted(root.iterdir()):
                    if cand.is_file() and cand.name.lower().startswith(("license", "copying")):
                        b = cand.read_bytes()
                        licenses.append({"path": cand.name, "sha256": sha256_bytes(b), "bytes": len(b)})
                summary["groups"].append({
                    "repo": repo,
                    "recorded_commit_id": cid,
                    "full_commit": full,
                    "rows": len(items),
                    "checked_ok": len(items) - len(failures),
                    "failure_count": len(failures),
                    "failures": failures[:200],
                    "all_failure_count_preserved": len(failures),
                    "unique_source_files": len(file_hashes),
                    "source_file_sha256": file_hashes,
                    "license_files": licenses,
                })
            except Exception as e:
                total_failed += len(items)
                summary["groups"].append({
                    "repo": repo,
                    "recorded_commit_id": cid,
                    "rows": len(items),
                    "error_type": type(e).__name__,
                    "failure_count": len(items),
                })
    summary["verified_rows"] = total_checked
    summary["failed_rows"] = total_failed
    summary["all_rows_bound"] = total_failed == 0
    return summary


def acquire_freshstack() -> dict[str, Any]:
    api = HfApi()
    official_files = hf_files(CORPUS_REPO, CORPUS_REV)
    query_files = hf_files(QUERY_REPO, QUERY_REV)
    write_json("freshstack-official-file-list.json", {
        "repo": CORPUS_REPO,
        "revision": CORPUS_REV,
        "files": [f for f in official_files if not f.lower().endswith("readme.md")],
        "readme_opened": False,
    })
    write_json("freshstack-query-file-list.json", {
        "repo": QUERY_REPO,
        "revision": QUERY_REV,
        "files": [f for f in query_files if not f.lower().endswith("readme.md")],
        "readme_opened": False,
    })

    selected_queries = []
    official_rows: dict[str, list[dict[str, Any]]] = {}
    topic_summary: dict[str, Any] = {}

    for topic, index in TOPICS.items():
        cfiles = data_files_for_topic(official_files, topic, "train")
        qfiles = data_files_for_topic(query_files, topic, "test")
        cpaths = [download_hf(CORPUS_REPO, CORPUS_REV, f) for f in cfiles]
        qpaths = [download_hf(QUERY_REPO, QUERY_REV, f) for f in qfiles]
        if not cpaths or not qpaths:
            topic_summary[topic] = {"status": "FILES_NOT_RESOLVED", "corpus_files": cfiles, "query_files": qfiles}
            continue

        rows = []
        for row in iter_parquet_rows(cpaths):
            flat = flatten_meta(row)
            rows.append(flat)
        official_rows[topic] = rows

        qrow = None
        for i, row in enumerate(iter_parquet_rows(qpaths)):
            if i == index:
                qrow = {
                    "topic": topic,
                    "physical_test_row_index": index,
                    "query_id": str(row.get("query_id", row.get("id", ""))),
                    "query_title": row.get("query_title", "") or "",
                    "query_text": row.get("query_text", "") or "",
                }
                break
        if qrow is None:
            raise RuntimeError(f"query index {topic}:{index} not found")
        selected_queries.append(qrow)
        topic_summary[topic] = {
            "status": "OFFICIAL_LOADED",
            "official_rows": len(rows),
            "official_schema": schema_names(cpaths[0]),
            "official_file_sha256": {f: sha256_bytes(p.read_bytes()) for f, p in zip(cfiles, cpaths)},
            "query_files": qfiles,
            "query_file_sha256": {f: sha256_bytes(p.read_bytes()) for f, p in zip(qfiles, qpaths)},
        }

    write_json("freshstack-selected-queries.json", {"queries": selected_queries})

    hist = find_historical_revision(api, official_files)
    join_summary: dict[str, Any] = {
        "historical_discovery": hist,
        "status": "NOT_EXECUTED",
        "topics": {},
        "unmatched_official": 0,
        "unmatched_historical": 0,
        "duplicate_historical_keys": 0,
        "ambiguous_official": 0,
    }
    join_failures = []

    if hist.get("revision"):
        hrev = hist["revision"]
        hfiles = hf_files(CORPUS_REPO, hrev)
        join_summary["status"] = "EXECUTED"
        for topic, rows in official_rows.items():
            hpnames = data_files_for_topic(hfiles, topic, "train")
            hpaths = [download_hf(CORPUS_REPO, hrev, f) for f in hpnames]
            index_map: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
            hcount = 0
            for row in iter_parquet_rows(hpaths):
                flat = flatten_meta(row)
                index_map[row_key(topic, flat)].append(flat)
                hcount += 1
            duplicates = sum(1 for v in index_map.values() if len(v) > 1)
            matched_keys = set()
            unmatched = ambiguous = 0
            for r in rows:
                k = row_key(topic, r)
                matches = index_map.get(k, [])
                if len(matches) == 1:
                    r["commit_id"] = matches[0].get("commit_id")
                    matched_keys.add(k)
                elif len(matches) == 0:
                    unmatched += 1
                    join_failures.append({"topic": topic, "_id": r["_id"], "reason": "UNMATCHED_OFFICIAL", "key_text_sha256": k[2]})
                else:
                    ambiguous += 1
                    join_failures.append({"topic": topic, "_id": r["_id"], "reason": "AMBIGUOUS_OFFICIAL", "match_count": len(matches), "key_text_sha256": k[2]})
            unmatched_hist = sum(len(v) for k, v in index_map.items() if k not in matched_keys)
            join_summary["topics"][topic] = {
                "official_rows": len(rows),
                "historical_rows": hcount,
                "unmatched_official": unmatched,
                "ambiguous_official": ambiguous,
                "duplicate_historical_keys": duplicates,
                "unmatched_historical_rows": unmatched_hist,
                "historical_files": hpnames,
                "historical_file_sha256": {f: sha256_bytes(p.read_bytes()) for f, p in zip(hpnames, hpaths)},
            }
            join_summary["unmatched_official"] += unmatched
            join_summary["ambiguous_official"] += ambiguous
            join_summary["duplicate_historical_keys"] += duplicates
            join_summary["unmatched_historical"] += unmatched_hist

    with gzip.open(OUT / "freshstack-join-failures.jsonl.gz", "wt", encoding="utf-8") as gz:
        for row in join_failures:
            safe_json(row)
            gz.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")

    source_bindings = {
        "status": "NOT_EXECUTED",
        "reason": "historical commit-bearing representation not found",
    }
    if join_summary["status"] == "EXECUTED" and join_summary["unmatched_official"] == 0 and join_summary["ambiguous_official"] == 0:
        source_bindings = verify_source_bindings(official_rows)
        source_bindings["status"] = "EXECUTED"
        source_bindings.pop("reason", None)

    write_json("freshstack-provenance-join-summary.json", join_summary)
    write_json("freshstack-source-binding-summary.json", source_bindings)
    write_json("freshstack-topic-summary.json", topic_summary)

    return {
        "official_dataset_revision": CORPUS_REV,
        "query_dataset_revision": QUERY_REV,
        "topic_summary": topic_summary,
        "historical": hist,
        "join": join_summary,
        "source_binding": source_bindings,
    }


def acquire_scifact() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        arc = td / "data.tar.gz"
        req = urllib.request.Request(SCIFACT_URL, headers={"User-Agent": "pilot0a-cleanroom"})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
            headers = dict(r.headers.items())
        arc.write_bytes(data)
        actual_sha = sha256_bytes(data)
        actual_size = len(data)
        root = extract_tar_gz(arc, td / "extracted")

        claims = list((root / "claims_dev.jsonl").read_text(encoding="utf-8").splitlines())
        corpus_path = root / "corpus.jsonl"
        corpus_by_id = {}
        with corpus_path.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                corpus_by_id[str(row["doc_id"])] = row

        selected = []
        cited_ids = set()
        for idx in SCIFACT_INDICES:
            raw = json.loads(claims[idx])
            # Mechanical redaction before any persistence/output.
            cited = [str(x) for x in raw.get("cited_doc_ids", [])]
            cited_ids.update(cited)
            selected.append({
                "physical_line_index": idx,
                "claim_id": str(raw.get("id")),
                "claim": raw.get("claim", ""),
                "cited_doc_ids": cited,
                "sanitized_row_sha256": sha256_text(json.dumps({"id": raw.get("id"), "claim": raw.get("claim", ""), "cited_doc_ids": cited}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)),
            })

        abstracts = []
        missing = []
        for did in sorted(cited_ids):
            row = corpus_by_id.get(did)
            if row is None:
                missing.append(did)
                continue
            abstract = row.get("abstract", [])
            abstracts.append({
                "doc_id": did,
                "title": row.get("title", ""),
                "abstract": abstract,
                "abstract_joined_lf_sha256": sha256_text("\n".join(abstract)),
                "sanitized_document_sha256": sha256_text(json.dumps({"doc_id": row.get("doc_id"), "title": row.get("title", ""), "abstract": abstract}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)),
            })

        file_hashes = {}
        for p in sorted(root.rglob("*")):
            if p.is_file():
                rel = str(p.relative_to(root))
                file_hashes[rel] = {"sha256": sha256_bytes(p.read_bytes()), "bytes": p.stat().st_size}

        out = {
            "canonical_repo_commit": "68b98a56d93e0f9da0d2aab4e6c3294699a0f72e",
            "acquisition_url_kind": "mutable release/latest",
            "archive_expected_sha256": SCIFACT_EXPECTED_SHA256,
            "archive_actual_sha256": actual_sha,
            "archive_expected_size": SCIFACT_EXPECTED_SIZE,
            "archive_actual_size": actual_size,
            "archive_match": actual_sha == SCIFACT_EXPECTED_SHA256 and actual_size == SCIFACT_EXPECTED_SIZE,
            "http_metadata": {
                "etag": headers.get("ETag"),
                "last_modified": headers.get("Last-Modified"),
                "content_length": headers.get("Content-Length"),
            },
            "selected_claims": selected,
            "cited_abstracts": abstracts,
            "missing_cited_doc_ids": missing,
            "archive_file_hashes": file_hashes,
            "published_evidence_output": False,
        }
        write_json("scifact-reconstruction.json", out)
        return out


def main() -> None:
    summary: dict[str, Any] = {
        "firewall": {
            "general_web_search_used": False,
            "freshstack_readme_opened": False,
            "freshstack_qrels_opened": False,
            "freshstack_candidate_lists_opened": False,
            "freshstack_retrieval_results_opened": False,
            "scifact_published_evidence_output": False,
            "retriever_executed": False,
        }
    }
    try:
        summary["freshstack"] = acquire_freshstack()
    except Exception as e:
        summary["freshstack"] = {"status": "ERROR", "error_type": type(e).__name__, "error": str(e)[:1000]}
    try:
        summary["scifact"] = acquire_scifact()
    except Exception as e:
        summary["scifact"] = {"status": "ERROR", "error_type": type(e).__name__, "error": str(e)[:1000]}
    write_json("acquisition-summary.json", summary)
    # Intentionally do not print dataset rows, schemas containing values, or external content.
    print("Pilot 0A source-only acquisition completed; inspect artifact files only.")


if __name__ == "__main__":
    main()
