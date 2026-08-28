#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path
from typing import Any

COUNTER = {"decisive_counterevidence", "decisive_contradiction", "decisive_refutation"}
QUALIFIER = {"decisive_qualifier", "decisive_exception"}


def load_json(path: Path) -> Any: return json.loads(path.read_text(encoding="utf-8"))
def load_jsonl(path: Path) -> list[dict[str, Any]]: return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
def ratio(n: int, d: int) -> float | None: return None if d == 0 else n / d

def load_benchmark(root: Path, split: str):
    passages = {(p["source_id"], p["passage_id"]): p for p in load_jsonl(root / "runtime" / "passages.jsonl")}
    cases = {c["case_id"]: c for c in load_jsonl(root / "runtime" / f"{split}_cases.jsonl")}
    gold = defaultdict(list)
    for row in load_jsonl(root / "evaluator_only" / f"{split}_gold.jsonl"): gold[row["case_id"]].append(row)
    subsets = {s["subset_id"]: s for s in load_json(root / "runtime" / "apertures.json")["subsets"]}
    return passages, cases, gold, subsets


def evaluate_case(case, rows, result, passages, subsets):
    errors=[]
    if result.get("schema_version") != "1.0": errors.append("schema_version")
    if result.get("case_id") != case["case_id"]: errors.append("case_id")
    hits = result.get("hits") if isinstance(result.get("hits"), list) else []
    k = int(case["runtime_config"]["maximum_passages"])
    budget_violation = int(len(hits) > k)
    bounded = hits[:k]
    expected_subset = case["accessible_subset_id"]
    actual_subset = result.get("search_scope", {}).get("actual_searchable_subset_id")
    observed_subset = result.get("search_scope", {}).get("observed_scope", {}).get("subset_id")
    scope_mismatch = int(actual_subset != expected_subset or observed_subset != actual_subset)
    accessible_sources = set(subsets.get(actual_subset, {}).get("source_ids", []))
    valid_ids=[]; invalid_prov=0; out_of_scope=0
    for i, h in enumerate(bounded,1):
        if not isinstance(h, dict) or h.get("rank") != i: errors.append(f"rank:{i}"); continue
        ident=(h.get("source_id"), h.get("passage_id"))
        if ident not in passages:
            invalid_prov += 1; valid_ids.append(None); continue
        if ident[0] not in accessible_sources: out_of_scope += 1
        # Exact text reconstruction is part of provenance integrity.
        if h.get("text") != passages[ident]["text"]: invalid_prov += 1; valid_ids.append(None); continue
        valid_ids.append(ident)
    valid_set={x for x in valid_ids if x is not None}
    decisive=[r for r in rows if r.get("decisive")]
    accessible_decisive=[r for r in decisive if r["source_id"] in accessible_sources]
    decisive_ids={(r["source_id"],r["passage_id"]) for r in accessible_decisive}
    counter_ids={(r["source_id"],r["passage_id"]) for r in accessible_decisive if r["relevance_class"] in COUNTER}
    qualifier_ids={(r["source_id"],r["passage_id"]) for r in accessible_decisive if r["relevance_class"] in QUALIFIER}
    hard_ids={(r["source_id"],r["passage_id"]) for r in rows if r["relevance_class"]=="hard_negative" and r["source_id"] in accessible_sources}
    found_decisive=decisive_ids & valid_set
    first_decisive_rank=None; hard_before=0
    for rank,ident in enumerate(valid_ids,1):
        if ident in decisive_ids and first_decisive_rank is None: first_decisive_rank=rank
        if first_decisive_rank is None and ident in hard_ids: hard_before += 1
    groups=defaultdict(set)
    for r in accessible_decisive:
        if r.get("joint_group_id"): groups[r["joint_group_id"]].add((r["source_id"],r["passage_id"]))
    complete_groups=sum(1 for members in groups.values() if members <= valid_set)
    partial_groups=sum(1 for members in groups.values() if (members & valid_set) and not (members <= valid_set))
    completeness_status=result.get("completeness_claim",{}).get("status")
    subset_kind=subsets.get(actual_subset,{}).get("scope_kind")
    false_completeness=int(subset_kind=="bounded" and completeness_status in {"full_corpus","comprehensive"})
    answerability_status=result.get("answerability_claim",{}).get("status")
    answerability_overclaim=int(answerability_status in {"answer_present","no_answer"})
    return {
        "case_id": case["case_id"], "family": case["family"], "expected_answerability": case["expected_answerability"],
        "shape_errors": len(errors), "budget_violations": budget_violation, "invalid_provenance_hits": invalid_prov,
        "out_of_scope_hits": out_of_scope, "scope_mismatches": scope_mismatch, "false_completeness_claims": false_completeness,
        "answerability_overclaims": answerability_overclaim,
        "applicable_decisive": len(decisive_ids), "found_decisive": len(found_decisive),
        "case_hit": None if not decisive_ids else int(bool(found_decisive)),
        "counter_total": len(counter_ids), "counter_found": len(counter_ids & valid_set),
        "qualifier_total": len(qualifier_ids), "qualifier_found": len(qualifier_ids & valid_set),
        "joint_groups": len(groups), "complete_joint_groups": complete_groups, "partial_joint_groups": partial_groups,
        "first_decisive_rank": first_decisive_rank, "hard_negative_before_first_decisive": hard_before,
        "hard_negative_hits_at_k": len(hard_ids & valid_set), "hits_at_k": len(bounded),
    }


def aggregate(case_metrics: list[dict[str,Any]], thresholds: dict[str,Any]) -> dict[str,Any]:
    answerable=[m for m in case_metrics if m["applicable_decisive"]>0]
    total_dec=sum(m["applicable_decisive"] for m in answerable); found_dec=sum(m["found_decisive"] for m in answerable)
    total_counter=sum(m["counter_total"] for m in answerable); found_counter=sum(m["counter_found"] for m in answerable)
    total_qual=sum(m["qualifier_total"] for m in answerable); found_qual=sum(m["qualifier_found"] for m in answerable)
    total_groups=sum(m["joint_groups"] for m in answerable); complete_groups=sum(m["complete_joint_groups"] for m in answerable)
    reciprocal=[1/m["first_decisive_rank"] for m in answerable if m["first_decisive_rank"]]
    families={}
    for fam in sorted({m["family"] for m in case_metrics}):
        fm=[m for m in case_metrics if m["family"]==fam and m["applicable_decisive"]>0]
        fd=sum(m["applicable_decisive"] for m in fm); ff=sum(m["found_decisive"] for m in fm)
        families[fam]={
            "answerable_cases":len(fm),
            "case_hit_at_k":ratio(sum(m["case_hit"] for m in fm if m["case_hit"] is not None),len(fm)),
            "decisive_annotation_recall_at_k":ratio(ff,fd),
            "counterevidence_recall_at_k":ratio(sum(m["counter_found"] for m in fm),sum(m["counter_total"] for m in fm)),
            "qualifier_exception_recall_at_k":ratio(sum(m["qualifier_found"] for m in fm),sum(m["qualifier_total"] for m in fm)),
            "complete_joint_group_coverage_at_k":ratio(sum(m["complete_joint_groups"] for m in fm),sum(m["joint_groups"] for m in fm)),
        }
    summary={
        "cases":len(case_metrics), "answerable_cases":len(answerable),
        "case_hit_at_k":ratio(sum(m["case_hit"] for m in answerable),len(answerable)),
        "decisive_annotation_recall_at_k":ratio(found_dec,total_dec),
        "counterevidence_recall_at_k":ratio(found_counter,total_counter),
        "qualifier_exception_recall_at_k":ratio(found_qual,total_qual),
        "complete_joint_group_coverage_at_k":ratio(complete_groups,total_groups),
        "first_decisive_mrr":ratio(sum(reciprocal),len(answerable)),
        "budget_violations":sum(m["budget_violations"] for m in case_metrics),
        "invalid_provenance_hits":sum(m["invalid_provenance_hits"] for m in case_metrics),
        "out_of_scope_hits":sum(m["out_of_scope_hits"] for m in case_metrics),
        "scope_mismatches":sum(m["scope_mismatches"] for m in case_metrics),
        "false_completeness_claims":sum(m["false_completeness_claims"] for m in case_metrics),
        "answerability_overclaims":sum(m["answerability_overclaims"] for m in case_metrics),
        "shape_errors":sum(m["shape_errors"] for m in case_metrics),
        "hard_negative_before_first_decisive":sum(m["hard_negative_before_first_decisive"] for m in case_metrics),
        "hard_negative_hits_at_k":sum(m["hard_negative_hits_at_k"] for m in case_metrics),
        "families":families,
    }
    failures=[]
    for key in ("case_hit_at_k","decisive_annotation_recall_at_k","counterevidence_recall_at_k","qualifier_exception_recall_at_k","complete_joint_group_coverage_at_k"):
        value=summary[key]
        if value is not None and value < thresholds[key]: failures.append(f"{key}:{value:.6f}<{thresholds[key]:.6f}")
    zero_gates={
        "budget_violations":"max_budget_violations", "invalid_provenance_hits":"max_invalid_provenance_hits",
        "out_of_scope_hits":"max_out_of_scope_hits", "false_completeness_claims":"max_false_completeness_claims",
        "answerability_overclaims":"max_answerability_overclaims",
    }
    for metric,tkey in zero_gates.items():
        if summary[metric] > thresholds[tkey]: failures.append(f"{metric}:{summary[metric]}>{thresholds[tkey]}")
    if summary["scope_mismatches"]: failures.append(f"scope_mismatches:{summary['scope_mismatches']}>0")
    if summary["shape_errors"]: failures.append(f"shape_errors:{summary['shape_errors']}>0")
    for fam,metrics in families.items():
        if metrics["case_hit_at_k"] is not None and metrics["case_hit_at_k"] < thresholds["family_case_hit_at_k"]:
            failures.append(f"{fam}.case_hit_at_k:{metrics['case_hit_at_k']:.6f}<{thresholds['family_case_hit_at_k']:.6f}")
        if metrics["decisive_annotation_recall_at_k"] is not None and metrics["decisive_annotation_recall_at_k"] < thresholds["family_decisive_annotation_recall_at_k"]:
            failures.append(f"{fam}.decisive_annotation_recall_at_k:{metrics['decisive_annotation_recall_at_k']:.6f}<{thresholds['family_decisive_annotation_recall_at_k']:.6f}")
    summary["qualification_failures"]=failures; summary["qualified"]=not failures
    return summary


def evaluate(root: Path, split: str, results_path: Path, thresholds_path: Path) -> dict[str,Any]:
    thresholds=load_json(thresholds_path); passages,cases,gold,subsets=load_benchmark(root,split)
    results={r["case_id"]:r for r in load_jsonl(results_path)}
    missing=sorted(set(cases)-set(results)); extra=sorted(set(results)-set(cases))
    if missing or extra: raise RuntimeError(f"result coverage mismatch missing={missing} extra={extra}")
    case_metrics=[evaluate_case(cases[cid],gold[cid],results[cid],passages,subsets) for cid in sorted(cases)]
    return {"schema_version":"1.0","split":split,"summary":aggregate(case_metrics,thresholds),"case_metrics":case_metrics}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--benchmark-root",required=True,type=Path); ap.add_argument("--split",required=True,choices=["dev","sealed"]); ap.add_argument("--results",required=True,type=Path); ap.add_argument("--thresholds",required=True,type=Path); ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args(); out=evaluate(a.benchmark_root,a.split,a.results,a.thresholds); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(out["summary"],indent=2,sort_keys=True))
if __name__=="__main__": main()
