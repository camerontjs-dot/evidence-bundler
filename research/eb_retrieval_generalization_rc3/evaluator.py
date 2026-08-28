#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

LOW_FAMILIES = ("L01", "L02", "L03")
TECHNICAL_KEYS = (
    "budget_violations",
    "invalid_provenance_hits",
    "out_of_scope_hits",
    "scope_mismatches",
    "false_completeness_claims",
    "answerability_overclaims",
    "shape_errors",
    "coverage_errors",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_benchmark(root: Path) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]], dict[str, Any], dict[str, dict[str, Any]]]:
    cases = {r["case_id"]: r for r in read_jsonl(root / "runtime/sealed_cases.jsonl")}
    passages = {(r["source_id"], r["passage_id"]): r for r in read_jsonl(root / "runtime/passages.jsonl")}
    scopes = json.loads((root / "runtime/scopes.json").read_text(encoding="utf-8"))
    gold = {r["case_id"]: r for r in read_jsonl(root / "evaluator_only/sealed_gold.jsonl")}
    return cases, passages, scopes, gold


def empty_result(case: dict[str, Any], retriever_id: str = "missing") -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "case_id": case["case_id"],
        "hits": [],
        "search_scope": {"actual_searchable_subset_id": case["accessible_subset_id"]},
        "completeness_claim": {"status": "not_established"},
        "answerability_claim": {"status": "not_established"},
        "run_identity": {"retriever_id": retriever_id, "configuration_id": "missing", "run_id": f"missing-{case['case_id']}"},
    }


def _shape_errors(result: dict[str, Any]) -> int:
    required = {"schema_version", "case_id", "hits", "search_scope", "completeness_claim", "answerability_claim", "run_identity"}
    if not isinstance(result, dict):
        return 1
    errors = 0
    if set(result) != required: errors += 1
    if result.get("schema_version") != "1.0": errors += 1
    if not isinstance(result.get("case_id"), str): errors += 1
    hits = result.get("hits")
    if not isinstance(hits, list):
        return errors + 1
    for i, hit in enumerate(hits, 1):
        if not isinstance(hit, dict):
            errors += 1
            continue
        if set(hit) != {"rank", "source_id", "passage_id", "score", "text"}: errors += 1
        if hit.get("rank") != i: errors += 1
        if not isinstance(hit.get("source_id"), str) or not isinstance(hit.get("passage_id"), str): errors += 1
        if not isinstance(hit.get("text"), str): errors += 1
        if not isinstance(hit.get("score"), (int, float)): errors += 1
    scope = result.get("search_scope")
    if not isinstance(scope, dict) or set(scope) != {"actual_searchable_subset_id"} or not isinstance(scope.get("actual_searchable_subset_id"), str): errors += 1
    cc = result.get("completeness_claim")
    if not isinstance(cc, dict) or set(cc) != {"status"} or cc.get("status") not in {"not_established", "comprehensive", "full_corpus"}: errors += 1
    ac = result.get("answerability_claim")
    if not isinstance(ac, dict) or set(ac) != {"status"} or ac.get("status") not in {"not_established", "answer_present", "no_answer"}: errors += 1
    ri = result.get("run_identity")
    if not isinstance(ri, dict) or set(ri) != {"retriever_id", "configuration_id", "run_id"}: errors += 1
    return errors


def evaluate_case(case: dict[str, Any], gold: dict[str, Any], result: dict[str, Any], passages: dict[tuple[str, str], dict[str, Any]], scopes: dict[str, Any]) -> dict[str, Any]:
    shape_errors = _shape_errors(result)
    k = int(case["runtime_config"]["maximum_passages"])
    hits = result.get("hits", []) if isinstance(result.get("hits", []), list) else []
    budget_violations = int(len(hits) > k)

    expected_scope = case["accessible_subset_id"]
    actual_scope = result.get("search_scope", {}).get("actual_searchable_subset_id") if isinstance(result.get("search_scope"), dict) else None
    scope_mismatches = int(actual_scope != expected_scope)
    allowed_sources = set(scopes[expected_scope]["source_ids"])

    invalid_provenance_hits = 0
    out_of_scope_hits = 0
    hit_keys: list[tuple[str, str]] = []
    hit_rank: dict[tuple[str, str], int] = {}
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        key = (hit.get("source_id"), hit.get("passage_id"))
        hit_keys.append(key)
        if isinstance(hit.get("rank"), int) and key not in hit_rank:
            hit_rank[key] = hit["rank"]
        p = passages.get(key)
        if p is None or hit.get("text") != (p or {}).get("text"):
            invalid_provenance_hits += 1
        if hit.get("source_id") not in allowed_sources:
            out_of_scope_hits += 1

    completeness_status = result.get("completeness_claim", {}).get("status") if isinstance(result.get("completeness_claim"), dict) else None
    answerability_status = result.get("answerability_claim", {}).get("status") if isinstance(result.get("answerability_claim"), dict) else None
    false_completeness_claims = int(completeness_status not in {None, "not_established"})
    answerability_overclaims = int(answerability_status not in {None, "not_established"})

    decisive_keys = [(d["source_id"], d["passage_id"]) for d in gold["decisive"]]
    decisive_found = [key for key in decisive_keys if key in hit_rank and hit_rank[key] <= k]
    case_hit = float(bool(decisive_found))
    decisive_recall = len(decisive_found) / max(1, len(decisive_keys))
    first_decisive_rank = min((hit_rank[key] for key in decisive_keys if key in hit_rank and hit_rank[key] <= k), default=None)
    reciprocal_rank = 0.0 if first_decisive_rank is None else 1.0 / first_decisive_rank

    hard_keys = {(h["source_id"], h["passage_id"]) for h in gold.get("hard_negatives", [])}
    hard_hits = [key for key in hit_keys[:k] if key in hard_keys]
    hard_before_decisive = 0
    if first_decisive_rank is not None:
        hard_before_decisive = sum(1 for key in hard_hits if hit_rank.get(key, k + 1) < first_decisive_rank)
    else:
        hard_before_decisive = len(hard_hits)

    is_counter = gold["family"] == "C01"
    technical = {
        "budget_violations": budget_violations,
        "invalid_provenance_hits": invalid_provenance_hits,
        "out_of_scope_hits": out_of_scope_hits,
        "scope_mismatches": scope_mismatches,
        "false_completeness_claims": false_completeness_claims,
        "answerability_overclaims": answerability_overclaims,
        "shape_errors": shape_errors,
        "coverage_errors": 0,
    }
    return {
        "case_id": case["case_id"],
        "family": gold["family"],
        "case_hit_at_5": case_hit,
        "decisive_recall_at_5": decisive_recall,
        "first_decisive_rank": first_decisive_rank,
        "first_decisive_rr": reciprocal_rank,
        "counterevidence_case_hit_at_5": case_hit if is_counter else None,
        "counterevidence_recall_at_5": decisive_recall if is_counter else None,
        "hard_negative_hits_at_5": len(hard_hits),
        "hard_negative_before_first_decisive": hard_before_decisive,
        **technical,
    }


def aggregate(case_metrics: list[dict[str, Any]], thresholds: dict[str, Any], coverage_errors: int = 0) -> dict[str, Any]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for m in case_metrics:
        by_family[m["family"]].append(m)
    low = [m for m in case_metrics if m["family"] in LOW_FAMILIES]
    c01 = by_family.get("C01", [])

    def mean(rows: list[dict[str, Any]], key: str) -> float:
        return sum(float(r[key]) for r in rows) / max(1, len(rows))

    family_metrics = {
        fam: {
            "cases": len(by_family.get(fam, [])),
            "case_hit_at_5": mean(by_family.get(fam, []), "case_hit_at_5"),
            "decisive_recall_at_5": mean(by_family.get(fam, []), "decisive_recall_at_5"),
            "first_decisive_mrr": mean(by_family.get(fam, []), "first_decisive_rr"),
        }
        for fam in LOW_FAMILIES
    }
    technical = {k: sum(int(m[k]) for m in case_metrics) for k in TECHNICAL_KEYS}
    technical["coverage_errors"] += int(coverage_errors)

    summary = {
        "low_overlap": {
            "cases": len(low),
            "case_hit_at_5": mean(low, "case_hit_at_5"),
            "decisive_recall_at_5": mean(low, "decisive_recall_at_5"),
            "first_decisive_mrr": mean(low, "first_decisive_rr"),
        },
        "families": family_metrics,
        "c01": {
            "cases": len(c01),
            "counterevidence_case_hit_at_5": mean(c01, "counterevidence_case_hit_at_5") if c01 else 0.0,
            "counterevidence_recall_at_5": mean(c01, "counterevidence_recall_at_5") if c01 else 0.0,
        },
        "hard_negative_hits_at_5": sum(int(m["hard_negative_hits_at_5"]) for m in case_metrics),
        "hard_negative_before_first_decisive": sum(int(m["hard_negative_before_first_decisive"]) for m in case_metrics),
        **technical,
    }

    failures: list[str] = []
    lo = summary["low_overlap"]
    if lo["case_hit_at_5"] < thresholds["combined_low_overlap_case_hit_at_5_min"]:
        failures.append("combined_low_overlap_case_hit_at_5")
    if lo["decisive_recall_at_5"] < thresholds["combined_low_overlap_decisive_recall_at_5_min"]:
        failures.append("combined_low_overlap_decisive_recall_at_5")
    if lo["first_decisive_mrr"] < thresholds["combined_low_overlap_first_decisive_mrr_min"]:
        failures.append("combined_low_overlap_first_decisive_mrr")
    for fam in LOW_FAMILIES:
        fm = summary["families"][fam]
        if fm["case_hit_at_5"] < thresholds["per_low_overlap_family_case_hit_at_5_min"]:
            failures.append(f"{fam}_case_hit_at_5")
        if fm["decisive_recall_at_5"] < thresholds["per_low_overlap_family_decisive_recall_at_5_min"]:
            failures.append(f"{fam}_decisive_recall_at_5")
    if summary["c01"]["counterevidence_case_hit_at_5"] < thresholds["c01_counterevidence_case_hit_at_5_min"]:
        failures.append("C01_counterevidence_case_hit_at_5")
    if summary["c01"]["counterevidence_recall_at_5"] < thresholds["c01_counterevidence_recall_at_5_min"]:
        failures.append("C01_counterevidence_recall_at_5")

    tech_thresholds = {
        "budget_violations": "max_budget_violations",
        "invalid_provenance_hits": "max_invalid_provenance_hits",
        "out_of_scope_hits": "max_out_of_scope_hits",
        "scope_mismatches": "max_scope_mismatches",
        "false_completeness_claims": "max_false_completeness_claims",
        "answerability_overclaims": "max_answerability_overclaims",
        "shape_errors": "max_shape_errors",
        "coverage_errors": "max_coverage_errors",
    }
    for key, threshold_key in tech_thresholds.items():
        if int(summary[key]) > int(thresholds[threshold_key]):
            failures.append(key)

    summary["qualification_failures"] = failures
    summary["qualified_absolute_target"] = not failures
    return summary


def evaluate_run_from_loaded(cases: dict[str, dict[str, Any]], passages: dict[tuple[str, str], dict[str, Any]], scopes: dict[str, Any], gold: dict[str, dict[str, Any]], results: list[dict[str, Any]], thresholds: dict[str, Any]) -> dict[str, Any]:
    counts = Counter(r.get("case_id") for r in results if isinstance(r, dict))
    expected = set(cases)
    observed = {cid for cid in counts if isinstance(cid, str)}
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    duplicates = sorted(cid for cid, n in counts.items() if isinstance(cid, str) and n > 1)
    coverage_errors = len(missing) + len(extra) + len(duplicates)

    first_by_id: dict[str, dict[str, Any]] = {}
    for r in results:
        if isinstance(r, dict) and isinstance(r.get("case_id"), str) and r["case_id"] not in first_by_id:
            first_by_id[r["case_id"]] = r

    metrics: list[dict[str, Any]] = []
    for cid in sorted(cases):
        result = first_by_id.get(cid, empty_result(cases[cid]))
        metrics.append(evaluate_case(cases[cid], gold[cid], result, passages, scopes))
    summary = aggregate(metrics, thresholds, coverage_errors)
    return {
        "summary": summary,
        "coverage": {"missing": missing, "extra": extra, "duplicates": duplicates},
        "case_metrics": metrics,
    }


def evaluate_run(root: Path, results: list[dict[str, Any]], thresholds: dict[str, Any]) -> dict[str, Any]:
    cases, passages, scopes, gold = load_benchmark(root)
    return evaluate_run_from_loaded(cases, passages, scopes, gold, results, thresholds)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-root", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--thresholds", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    results = json.loads(args.results.read_text(encoding="utf-8"))
    thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
    out = evaluate_run(args.benchmark_root, results, thresholds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
