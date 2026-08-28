#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+")
LOW_FAMILIES = {"L01", "L02", "L03"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def tok(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def overlap(query: str, passage: str) -> float:
    q = tok(query)
    return len(q & tok(passage)) / max(1, len(q))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path, rc2_root: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    cases = read_jsonl(root / "runtime/sealed_cases.jsonl")
    passages = read_jsonl(root / "runtime/passages.jsonl")
    sources = read_jsonl(root / "runtime/sources.jsonl")
    scopes = json.loads((root / "runtime/scopes.json").read_text(encoding="utf-8"))
    gold = read_jsonl(root / "evaluator_only/sealed_gold.jsonl")

    if len(cases) != 64:
        errors.append(f"sealed_case_count={len(cases)} expected=64")
    if len(passages) != 64 * 9:
        errors.append(f"passage_count={len(passages)} expected=576")
    if len(sources) != 64:
        errors.append(f"source_count={len(sources)} expected=64")

    case_by_id = {c["case_id"]: c for c in cases}
    passage_by_id = {(p["source_id"], p["passage_id"]): p for p in passages}
    source_by_id = {s["source_id"]: s for s in sources}
    gold_by_id = {g["case_id"]: g for g in gold}

    if len(case_by_id) != len(cases): errors.append("duplicate case_id")
    if len(passage_by_id) != len(passages): errors.append("duplicate source/passage identity")
    if len(source_by_id) != len(sources): errors.append("duplicate source_id")
    if len(gold_by_id) != len(gold): errors.append("duplicate gold case_id")
    if set(case_by_id) != set(gold_by_id): errors.append("runtime/gold case coverage mismatch")

    family_counts = Counter(g.get("family") for g in gold)
    expected_counts = {"L01": 16, "L02": 16, "L03": 16, "C01": 16}
    if dict(family_counts) != expected_counts:
        errors.append(f"family_counts={dict(family_counts)} expected={expected_counts}")

    runtime_forbidden = {"family", "decisive", "hard_negatives", "entity_stem", "answerable", "construction"}
    for c in cases:
        leaked = runtime_forbidden & set(c)
        if leaked: errors.append(f"{c['case_id']}: evaluator-only fields leaked into runtime case: {sorted(leaked)}")
        if c.get("runtime_config", {}).get("maximum_passages") != 5:
            errors.append(f"{c['case_id']}: maximum_passages != 5")
        sid = c.get("accessible_subset_id")
        if sid not in scopes:
            errors.append(f"{c['case_id']}: missing scope {sid}")

    source_passage_counts = Counter(p["source_id"] for p in passages)
    for sid, n in source_passage_counts.items():
        if n != 9: errors.append(f"{sid}: passage_count={n} expected=9")

    # Reconstruct exact passage text from the frozen runtime source records.
    for p in passages:
        source = source_by_id.get(p["source_id"])
        if source is None:
            errors.append(f"{p['passage_id']}: source missing")
            continue
        start, end = p["char_start"], p["char_end"]
        if source["text"][start:end] != p["text"]:
            errors.append(f"{p['passage_id']}: source slice does not reconstruct passage text")
        if hashlib.sha256(p["text"].encode("utf-8")).hexdigest() != p["text_sha256"]:
            errors.append(f"{p['passage_id']}: text_sha256 mismatch")

    low_overlap_stats: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for g in gold:
        cid = g["case_id"]
        c = case_by_id[cid]
        scope = scopes[c["accessible_subset_id"]]
        allowed_sources = set(scope.get("source_ids", []))
        if len(allowed_sources) != 1:
            errors.append(f"{cid}: expected exactly one source in scope")
        decisives = g.get("decisive", [])
        if not decisives:
            errors.append(f"{cid}: no decisive identity")
            continue
        for d in decisives:
            if (d["source_id"], d["passage_id"]) not in passage_by_id:
                errors.append(f"{cid}: decisive passage absent")
            if d["source_id"] not in allowed_sources:
                errors.append(f"{cid}: decisive passage inaccessible")
        for h in g.get("hard_negatives", []):
            if (h["source_id"], h["passage_id"]) not in passage_by_id:
                errors.append(f"{cid}: hard negative absent")
            if h["source_id"] not in allowed_sources:
                errors.append(f"{cid}: hard negative inaccessible")

        if g["family"] in LOW_FAMILIES:
            d = passage_by_id[(decisives[0]["source_id"], decisives[0]["passage_id"])]
            h0 = g["hard_negatives"][0]
            h = passage_by_id[(h0["source_id"], h0["passage_id"])]
            dov = overlap(c["claim_text"], d["text"])
            hov = overlap(c["claim_text"], h["text"])
            low_overlap_stats[g["family"]].append({"case_id": cid, "decisive_overlap": dov, "hard_negative_overlap": hov})
            if not hov > dov:
                errors.append(f"{cid}: hard-negative lexical overlap {hov:.3f} not greater than decisive {dov:.3f}")
            if dov >= 0.60:
                errors.append(f"{cid}: decisive lexical overlap {dov:.3f} is not sufficiently reduced")
            if d["passage_order"] <= 5:
                errors.append(f"{cid}: decisive passage is within first-N K=5")
            in_scope = [p for p in passages if p["source_id"] in allowed_sources]
            if len(in_scope) <= 5:
                errors.append(f"{cid}: insufficient distractors to defeat return-all at K=5")

    # Verify the committed frozen-byte manifest before any retrieval control is allowed.
    sums_path = root / "SHA256SUMS"
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        path = root / rel
        if not path.exists() or sha256(path) != digest:
            errors.append(f"frozen-byte mismatch: {rel}")

    rc2_checks = {"performed": False, "query_reuse": 0, "passage_reuse": 0, "entity_stem_reuse": 0}
    if rc2_root is not None and rc2_root.exists():
        rc2_checks["performed"] = True
        rc2_cases_path = rc2_root / "runtime/sealed_cases.jsonl"
        rc2_passages_path = rc2_root / "runtime/passages.jsonl"
        rc2_cases = read_jsonl(rc2_cases_path) if rc2_cases_path.exists() else []
        rc2_passages = read_jsonl(rc2_passages_path) if rc2_passages_path.exists() else []
        rc2_claims = {str(c.get("claim_text", "")).strip().lower() for c in rc2_cases}
        rc2_texts = {str(p.get("text", "")).strip().lower() for p in rc2_passages}
        rc2_all = "\n".join(sorted(rc2_claims | rc2_texts))
        for c in cases:
            if c["claim_text"].strip().lower() in rc2_claims:
                rc2_checks["query_reuse"] += 1
                errors.append(f"{c['case_id']}: exact RC2 query text reused")
        for p in passages:
            if p["text"].strip().lower() in rc2_texts:
                rc2_checks["passage_reuse"] += 1
                errors.append(f"{p['passage_id']}: exact RC2 passage text reused")
        for g in gold:
            stem = g["entity_stem"].lower()
            if re.search(rf"\b{re.escape(stem)}\b", rc2_all):
                rc2_checks["entity_stem_reuse"] += 1
                errors.append(f"{g['case_id']}: RC2 fictional entity stem reused: {g['entity_stem']}")

    stats = {
        fam: {
            "min_decisive_overlap": min(r["decisive_overlap"] for r in rows),
            "max_decisive_overlap": max(r["decisive_overlap"] for r in rows),
            "min_hard_negative_overlap": min(r["hard_negative_overlap"] for r in rows),
            "all_hard_negative_greater": all(r["hard_negative_overlap"] > r["decisive_overlap"] for r in rows),
        }
        for fam, rows in sorted(low_overlap_stats.items())
    }
    return {
        "valid": not errors,
        "errors": errors,
        "sealed_cases": len(cases),
        "passages": len(passages),
        "family_counts": dict(sorted(family_counts.items())),
        "runtime_gold_physical_separation": True,
        "low_overlap_stats": stats,
        "rc2_nonreuse": rc2_checks,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-root", type=Path, required=True)
    ap.add_argument("--rc2-root", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = validate(args.benchmark_root, args.rc2_root)
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
