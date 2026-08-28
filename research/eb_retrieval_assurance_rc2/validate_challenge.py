#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from collections import defaultdict
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+")
DECISIVE_CLASSES = {"decisive_support", "decisive_counterevidence", "decisive_qualifier", "decisive_exception"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))

def overlap(query: str, text: str) -> float:
    q, t = tokens(query), tokens(text)
    return 0.0 if not q else len(q & t) / len(q)


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    manifest = load_json(root / "manifest.json")
    receipt = load_json(root / "freeze_receipt.json")
    passages = load_jsonl(root / "runtime" / "passages.jsonl")
    apertures = {x["subset_id"]: x for x in load_json(root / "runtime" / "apertures.json")["subsets"]}
    passage_by_id = {(p["source_id"], p["passage_id"]): p for p in passages}
    if len(passage_by_id) != len(passages): errors.append("duplicate passage identity")

    splits = manifest["splits_generated"]
    all_cases: dict[str, dict[str, Any]] = {}
    all_gold: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for split in splits:
        cases = load_jsonl(root / "runtime" / f"{split}_cases.jsonl")
        gold = load_jsonl(root / "evaluator_only" / f"{split}_gold.jsonl")
        for c in cases:
            if c["case_id"] in all_cases: errors.append(f"duplicate case {c['case_id']}")
            all_cases[c["case_id"]] = c
        for g in gold:
            all_gold[g["case_id"]].append(g)

    # Runtime/gold physical separation.
    runtime_text = "\n".join(p.read_text(encoding="utf-8") for p in (root / "runtime").rglob("*") if p.is_file())
    for forbidden in ("relevance_class", "joint_group_id", "decisive_counterevidence", "hard_negative"):
        if forbidden in runtime_text:
            errors.append(f"runtime leakage token: {forbidden}")

    low_overlap_cases = 0
    lexical_trap_cases = 0
    joint_groups = 0
    multi_source_groups = 0
    no_answer_cases = 0
    bounded_cases = 0

    for case_id, case in all_cases.items():
        subset_id = case["accessible_subset_id"]
        if subset_id not in apertures:
            errors.append(f"{case_id}: missing aperture")
            continue
        accessible_sources = set(apertures[subset_id]["source_ids"])
        rows = all_gold.get(case_id, [])
        if not rows: errors.append(f"{case_id}: missing gold")
        for row in rows:
            ident = (row["source_id"], row["passage_id"])
            if ident not in passage_by_id:
                errors.append(f"{case_id}: gold unknown passage {ident}")
        decisive = [r for r in rows if r["decisive"]]
        accessible_decisive = [r for r in decisive if r["source_id"] in accessible_sources]
        expected = case["expected_answerability"]
        if expected == "answerable" and not accessible_decisive:
            errors.append(f"{case_id}: answerable without accessible decisive")
        if expected != "answerable" and accessible_decisive:
            errors.append(f"{case_id}: non-answerable aperture exposes decisive")
        if expected == "no_answer_in_full_aperture":
            no_answer_cases += 1
            if decisive:
                errors.append(f"{case_id}: no-answer contains decisive gold")
        if expected == "not_answerable_within_aperture":
            bounded_cases += 1
            if not decisive:
                errors.append(f"{case_id}: aperture-boundary case lacks hidden decisive")

        # Measure generic lexical-trap property independently of any weak control implementation.
        if accessible_decisive:
            decis_overlaps = [overlap(case["claim_text"], passage_by_id[(r["source_id"], r["passage_id"])] ["text"]) for r in accessible_decisive]
            hard = [r for r in rows if r["relevance_class"] == "hard_negative" and r["source_id"] in accessible_sources]
            hard_overlaps = [overlap(case["claim_text"], passage_by_id[(r["source_id"], r["passage_id"])] ["text"]) for r in hard]
            if min(decis_overlaps) <= 0.45:
                low_overlap_cases += 1
            if hard_overlaps and max(hard_overlaps) > max(decis_overlaps):
                lexical_trap_cases += 1

        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in decisive:
            if r.get("joint_group_id"):
                groups[r["joint_group_id"]].append(r)
        for gid, members in groups.items():
            if len(members) < 2:
                errors.append(f"{case_id}: joint group {gid} has <2 members")
            joint_groups += 1
            if len({m["source_id"] for m in members}) > 1:
                multi_source_groups += 1

    # Family construction invariants.
    family_counts = defaultdict(int)
    for case in all_cases.values(): family_counts[case["family"]] += 1
    expected_per_split = {"dev": 2, "sealed": 8}
    for split in splits:
        expected = expected_per_split[split]
        for family in sorted(manifest["families"]):
            observed = sum(1 for c in all_cases.values() if c["split"] == split and c["family"] == family)
            if observed != expected: errors.append(f"{split}/{family}: expected {expected}, got {observed}")

    # Integrity receipt.
    for line in (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        if sha(root / rel) != digest: errors.append(f"sha mismatch {rel}")

    summary = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "cases": len(all_cases),
            "passages": len(passages),
            "low_overlap_answerable_cases": low_overlap_cases,
            "lexical_trap_answerable_cases": lexical_trap_cases,
            "joint_groups": joint_groups,
            "multi_source_joint_groups": multi_source_groups,
            "no_answer_cases": no_answer_cases,
            "bounded_aperture_cases": bounded_cases,
        },
        "receipt": receipt,
    }
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--benchmark-root", required=True, type=Path); ap.add_argument("--output", type=Path)
    args = ap.parse_args(); result = validate(args.benchmark_root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
if __name__ == "__main__": main()
