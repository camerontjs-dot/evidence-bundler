#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import bm25_adapter
import evaluator

TOKEN_RE = re.compile(r"[a-z0-9]+")
LEXICAL = ("bm25", "token_overlap", "tfidf_cosine", "char_trigram")
INVARIANT_SYSTEMS = ("oracle", "bm25", "token_overlap", "tfidf_cosine", "char_trigram", "hard_negative_biased")


def tok(s: str) -> list[str]:
    return TOKEN_RE.findall(s.lower())


def trigrams(s: str) -> set[str]:
    x = " ".join(tok(s))
    return {x[i:i + 3] for i in range(max(0, len(x) - 2))}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load(root: Path):
    cases, passage_map, scopes, gold = evaluator.load_benchmark(root)
    passage_list = evaluator.read_jsonl(root / "runtime/passages.jsonl")
    return cases, passage_map, passage_list, scopes, gold


def candidates(case: dict[str, Any], passage_list: list[dict[str, Any]], scopes: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = set(scopes[case["accessible_subset_id"]]["source_ids"])
    return [p for p in passage_list if p["source_id"] in allowed]


def base_result(case: dict[str, Any], hits: list[dict[str, Any]], retriever_id: str, completeness: str = "not_established", answerability: str = "not_established") -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "case_id": case["case_id"],
        "hits": hits,
        "search_scope": {"actual_searchable_subset_id": case["accessible_subset_id"]},
        "completeness_claim": {"status": completeness},
        "answerability_claim": {"status": answerability},
        "run_identity": {
            "retriever_id": retriever_id,
            "configuration_id": "eb-rc3-control-v1",
            "run_id": f"{retriever_id}-{case['case_id']}",
        },
    }


def make_hit(p: dict[str, Any], rank: int, score: float) -> dict[str, Any]:
    return {"rank": rank, "source_id": p["source_id"], "passage_id": p["passage_id"], "score": float(score), "text": p["text"]}


def lexical_rank(strategy: str, case: dict[str, Any], cands: list[dict[str, Any]]) -> list[tuple[dict[str, Any], float]]:
    k = int(case["runtime_config"]["maximum_passages"])
    q = case["claim_text"]
    if strategy == "token_overlap":
        qset = set(tok(q))
        rows = [(p, len(qset & set(tok(p["text"]))) / max(1, len(qset))) for p in cands]
    elif strategy == "char_trigram":
        qg = trigrams(q)
        rows = []
        for p in cands:
            pg = trigrams(p["text"])
            rows.append((p, len(qg & pg) / max(1, len(qg | pg))))
    elif strategy == "tfidf_cosine":
        docs = [tok(p["text"]) for p in cands]
        qtokens = tok(q)
        n = len(docs)
        df = Counter()
        for d in docs:
            df.update(set(d))
        def vec(tokens: list[str]) -> dict[str, float]:
            tf = Counter(tokens)
            return {t: c * (math.log((n + 1) / (df.get(t, 0) + 1)) + 1.0) for t, c in tf.items()}
        qv = vec(qtokens)
        qn = math.sqrt(sum(v * v for v in qv.values())) or 1.0
        rows = []
        for p, d in zip(cands, docs):
            dv = vec(d)
            dn = math.sqrt(sum(v * v for v in dv.values())) or 1.0
            dot = sum(qv.get(t, 0.0) * v for t, v in dv.items())
            rows.append((p, dot / (qn * dn)))
    else:
        raise ValueError(strategy)
    rows.sort(key=lambda row: (-row[1], row[0]["char_start"], row[0]["passage_id"]))
    return rows[:k]


def produce(strategy: str, case: dict[str, Any], passage_list: list[dict[str, Any]], passage_map: dict[tuple[str, str], dict[str, Any]], scopes: dict[str, Any], gold_row: dict[str, Any]) -> dict[str, Any]:
    cands = candidates(case, passage_list, scopes)
    k = int(case["runtime_config"]["maximum_passages"])
    if strategy == "null":
        return base_result(case, [], strategy)
    if strategy == "oracle":
        ids = [(d["source_id"], d["passage_id"]) for d in gold_row["decisive"]]
        hits = [make_hit(passage_map[key], i, 100.0 - i) for i, key in enumerate(ids[:k], 1)]
        return base_result(case, hits, strategy)
    if strategy == "first_n":
        rows = sorted(cands, key=lambda p: (p["passage_order"], p["passage_id"]))[:k]
        return base_result(case, [make_hit(p, i, 0.0) for i, p in enumerate(rows, 1)], strategy)
    if strategy == "return_all":
        rows = sorted(cands, key=lambda p: (p["passage_order"], p["passage_id"]))
        return base_result(case, [make_hit(p, i, 0.0) for i, p in enumerate(rows, 1)], strategy)
    if strategy in {"token_overlap", "tfidf_cosine", "char_trigram"}:
        rows = lexical_rank(strategy, case, cands)
        return base_result(case, [make_hit(p, i, score) for i, (p, score) in enumerate(rows, 1)], strategy)
    if strategy == "bm25":
        return base_result(case, bm25_adapter.run_bm25(case, cands), strategy)
    if strategy == "hard_negative_biased":
        hard = {(h["source_id"], h["passage_id"]) for h in gold_row.get("hard_negatives", [])}
        rows = sorted(cands, key=lambda p: (0 if (p["source_id"], p["passage_id"]) in hard else 1, p["passage_order"], p["passage_id"]))[:k]
        return base_result(case, [make_hit(p, i, 1.0 if (p["source_id"], p["passage_id"]) in hard else 0.0) for i, p in enumerate(rows, 1)], strategy)
    if strategy == "provenance_corrupt":
        r = produce("oracle", case, passage_list, passage_map, scopes, gold_row)
        if r["hits"]:
            r["hits"][0]["text"] += " [corrupted]"
        r["run_identity"]["retriever_id"] = strategy
        return r
    if strategy == "completeness_liar":
        r = produce("oracle", case, passage_list, passage_map, scopes, gold_row)
        r["completeness_claim"]["status"] = "comprehensive"
        r["run_identity"]["retriever_id"] = strategy
        return r
    if strategy == "answerability_liar":
        r = produce("oracle", case, passage_list, passage_map, scopes, gold_row)
        r["answerability_claim"]["status"] = "answer_present"
        r["run_identity"]["retriever_id"] = strategy
        return r
    raise ValueError(strategy)


def run_strategy(strategy: str, cases: dict[str, dict[str, Any]], passage_list: list[dict[str, Any]], passage_map: dict[tuple[str, str], dict[str, Any]], scopes: dict[str, Any], gold: dict[str, dict[str, Any]], thresholds: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results = [produce(strategy, cases[cid], passage_list, passage_map, scopes, gold[cid]) for cid in sorted(cases)]
    evaluated = evaluator.evaluate_run_obj(cases, passage_map, scopes, gold, results, thresholds) if hasattr(evaluator, "evaluate_run_obj") else evaluator.evaluate_run_from_loaded(cases, passage_map, scopes, gold, results, thresholds)
    return results, evaluated


def failure_categories(failures: list[str]) -> set[str]:
    cats: set[str] = set()
    for f in failures:
        if f.startswith("combined_low_overlap_case_hit") or f.startswith("combined_low_overlap_decisive_recall"):
            cats.add("combined_coverage")
        elif "mrr" in f:
            cats.add("ranking_quality")
        elif f.startswith(("L01_", "L02_", "L03_")):
            cats.add("family_floor")
        elif f.startswith("C01_"):
            cats.add("counterevidence")
        elif f in {"budget_violations", "invalid_provenance_hits", "out_of_scope_hits", "scope_mismatches", "false_completeness_claims", "answerability_overclaims", "shape_errors", "coverage_errors"}:
            cats.add("technical_integrity")
    return cats


def hit_signature(results: list[dict[str, Any]]) -> dict[str, list[tuple[str, str, int, float]]]:
    out = {}
    for r in results:
        out[r["case_id"]] = [(h["source_id"], h["passage_id"], h["rank"], float(h["score"])) for h in r["hits"]]
    return out


def compare_signatures(a: dict[str, list[tuple[str, str, int, float]]], b: dict[str, list[tuple[str, str, int, float]]], tol: float) -> dict[str, Any]:
    identity_rank_equal = True
    max_score_delta = 0.0
    mismatches: list[str] = []
    for cid in sorted(set(a) | set(b)):
        aa, bb = a.get(cid, []), b.get(cid, [])
        if [(x[0], x[1], x[2]) for x in aa] != [(x[0], x[1], x[2]) for x in bb]:
            identity_rank_equal = False
            mismatches.append(cid)
            continue
        for x, y in zip(aa, bb):
            max_score_delta = max(max_score_delta, abs(x[3] - y[3]))
    return {"identity_rank_equal": identity_rank_equal, "max_score_delta": max_score_delta, "within_score_tolerance": max_score_delta <= tol, "mismatch_cases": mismatches}


def run_mutations(cases, passage_list, passage_map, scopes, gold, thresholds, oracle_results):
    probes: dict[str, Any] = {}
    cid = "L01-01"
    original_metric = evaluator.evaluate_case(cases[cid], gold[cid], next(r for r in oracle_results if r["case_id"] == cid), passage_map, scopes)
    mutated_gold = copy.deepcopy(gold[cid])
    mutated_gold["decisive"] = [{**mutated_gold["decisive"][0], **mutated_gold["hard_negatives"][0]}]
    mutated_metric = evaluator.evaluate_case(cases[cid], mutated_gold, next(r for r in oracle_results if r["case_id"] == cid), passage_map, scopes)
    probes["decisive_identity_mutation"] = {
        "before_case_hit": original_metric["case_hit_at_5"],
        "after_case_hit": mutated_metric["case_hit_at_5"],
        "before_recall": original_metric["decisive_recall_at_5"],
        "after_recall": mutated_metric["decisive_recall_at_5"],
        "passed": mutated_metric["case_hit_at_5"] < original_metric["case_hit_at_5"] and mutated_metric["decisive_recall_at_5"] < original_metric["decisive_recall_at_5"],
    }

    hard_result = produce("hard_negative_biased", cases[cid], passage_list, passage_map, scopes, gold[cid])
    before_hard = evaluator.evaluate_case(cases[cid], gold[cid], hard_result, passage_map, scopes)
    hg = copy.deepcopy(gold[cid])
    alt = next(p for p in candidates(cases[cid], passage_list, scopes) if p["passage_order"] == 6)
    hg["hard_negatives"] = [{"source_id": alt["source_id"], "passage_id": alt["passage_id"]}]
    after_hard = evaluator.evaluate_case(cases[cid], hg, hard_result, passage_map, scopes)
    probes["hard_negative_identity_mutation"] = {
        "before_hard_negative_hits": before_hard["hard_negative_hits_at_5"],
        "after_hard_negative_hits": after_hard["hard_negative_hits_at_5"],
        "passed": before_hard["hard_negative_hits_at_5"] != after_hard["hard_negative_hits_at_5"],
    }

    corrupt = copy.deepcopy(next(r for r in oracle_results if r["case_id"] == cid))
    corrupt["hits"][0]["text"] += "x"
    before_p = evaluator.evaluate_case(cases[cid], gold[cid], next(r for r in oracle_results if r["case_id"] == cid), passage_map, scopes)
    after_p = evaluator.evaluate_case(cases[cid], gold[cid], corrupt, passage_map, scopes)
    probes["provenance_text_mutation"] = {
        "before_invalid": before_p["invalid_provenance_hits"],
        "after_invalid": after_p["invalid_provenance_hits"],
        "passed": after_p["invalid_provenance_hits"] > before_p["invalid_provenance_hits"],
    }

    partial = copy.deepcopy(oracle_results)
    idx = next(i for i, r in enumerate(partial) if r["case_id"] == cid)
    partial[idx] = base_result(cases[cid], [], "family-mutation-probe")
    base_eval = evaluator.evaluate_run_from_loaded(cases, passage_map, scopes, gold, partial, thresholds)
    mutated_all_gold = copy.deepcopy(gold)
    mutated_all_gold[cid]["family"] = "L02"
    mut_eval = evaluator.evaluate_run_from_loaded(cases, passage_map, scopes, mutated_all_gold, partial, thresholds)
    probes["family_label_mutation"] = {
        "before_L01": base_eval["summary"]["families"]["L01"],
        "after_L01": mut_eval["summary"]["families"]["L01"],
        "before_L02": base_eval["summary"]["families"]["L02"],
        "after_L02": mut_eval["summary"]["families"]["L02"],
        "combined_before": base_eval["summary"]["low_overlap"],
        "combined_after": mut_eval["summary"]["low_overlap"],
        "passed": base_eval["summary"]["families"]["L01"] != mut_eval["summary"]["families"]["L01"] and base_eval["summary"]["low_overlap"] == mut_eval["summary"]["low_overlap"],
    }

    coverage_eval = evaluator.evaluate_run_from_loaded(cases, passage_map, scopes, gold, oracle_results[:-1], thresholds)
    probes["result_coverage_mismatch"] = {
        "coverage_errors": coverage_eval["summary"]["coverage_errors"],
        "qualified": coverage_eval["summary"]["qualified_absolute_target"],
        "passed": coverage_eval["summary"]["coverage_errors"] > 0 and not coverage_eval["summary"]["qualified_absolute_target"],
    }
    return probes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-root", type=Path, required=True)
    ap.add_argument("--thresholds", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
    production_identity = bm25_adapter.verify_production_identity(args.repo_root)
    cases, passage_map, passage_list, scopes, gold = load(args.benchmark_root)

    strategies = ["oracle", "bm25", "null", "first_n", "token_overlap", "tfidf_cosine", "char_trigram", "return_all", "provenance_corrupt", "hard_negative_biased", "completeness_liar", "answerability_liar"]
    controls: dict[str, Any] = {}
    raw_results: dict[str, list[dict[str, Any]]] = {}
    for strategy in strategies:
        results = [produce(strategy, cases[cid], passage_list, passage_map, scopes, gold[cid]) for cid in sorted(cases)]
        evaluated = evaluator.evaluate_run_from_loaded(cases, passage_map, scopes, gold, results, thresholds)
        raw_results[strategy] = results
        controls[strategy] = {"summary": evaluated["summary"], "results_sha256": sha(results)}

    # Deterministic replay over the entire frozen control surface.
    replay_hashes: dict[str, str] = {}
    for strategy in strategies:
        replay = [produce(strategy, cases[cid], passage_list, passage_map, scopes, gold[cid]) for cid in sorted(cases)]
        replay_hashes[strategy] = sha(replay)
    deterministic = all(replay_hashes[s] == controls[s]["results_sha256"] for s in strategies)

    # Enumeration reversal changes only input enumeration, not passage identities/order fields.
    reversed_passages = list(reversed(passage_list))
    invariance: dict[str, Any] = {}
    tol = float(thresholds["score_invariance_absolute_tolerance"])
    for strategy in INVARIANT_SYSTEMS:
        rev = [produce(strategy, cases[cid], reversed_passages, passage_map, scopes, gold[cid]) for cid in sorted(cases)]
        invariance[strategy] = compare_signatures(hit_signature(raw_results[strategy]), hit_signature(rev), tol)
        invariance[strategy]["passed"] = invariance[strategy]["identity_rank_equal"] and invariance[strategy]["within_score_tolerance"]

    mutations = run_mutations(cases, passage_list, passage_map, scopes, gold, thresholds, raw_results["oracle"])

    lexical_failure_categories: set[str] = set()
    for strategy in ("token_overlap", "tfidf_cosine", "char_trigram"):
        lexical_failure_categories |= failure_categories(controls[strategy]["summary"]["qualification_failures"])

    bm25_low_fail = any(
        f.startswith(("combined_low_overlap", "L01_", "L02_", "L03_"))
        for f in controls["bm25"]["summary"]["qualification_failures"]
    )
    oracle = controls["oracle"]["summary"]
    hard = controls["hard_negative_biased"]["summary"]
    gate_checks = {
        "oracle_qualifies_perfectly": oracle["qualified_absolute_target"] and oracle["low_overlap"]["case_hit_at_5"] == 1.0 and oracle["low_overlap"]["decisive_recall_at_5"] == 1.0 and oracle["c01"]["counterevidence_recall_at_5"] == 1.0 and all(oracle[k] == 0 for k in ("budget_violations", "invalid_provenance_hits", "out_of_scope_hits", "scope_mismatches", "false_completeness_claims", "answerability_overclaims", "shape_errors", "coverage_errors")),
        "bm25_fails_primary_low_overlap_gate": bm25_low_fail,
        "token_overlap_fails": not controls["token_overlap"]["summary"]["qualified_absolute_target"],
        "tfidf_cosine_fails": not controls["tfidf_cosine"]["summary"]["qualified_absolute_target"],
        "char_trigram_fails": not controls["char_trigram"]["summary"]["qualified_absolute_target"],
        "lexical_failure_diversity": len(lexical_failure_categories) >= int(thresholds["weak_control_min_distinct_failure_categories"]),
        "null_fails": not controls["null"]["summary"]["qualified_absolute_target"],
        "first_n_fails": not controls["first_n"]["summary"]["qualified_absolute_target"],
        "return_all_budget_fails": controls["return_all"]["summary"]["budget_violations"] > 0 and not controls["return_all"]["summary"]["qualified_absolute_target"],
        "provenance_corrupt_fails": controls["provenance_corrupt"]["summary"]["invalid_provenance_hits"] > 0 and not controls["provenance_corrupt"]["summary"]["qualified_absolute_target"],
        "hard_negative_biased_underperforms_oracle": hard["low_overlap"]["case_hit_at_5"] < oracle["low_overlap"]["case_hit_at_5"] and hard["low_overlap"]["decisive_recall_at_5"] < oracle["low_overlap"]["decisive_recall_at_5"],
        "completeness_liar_fails": controls["completeness_liar"]["summary"]["false_completeness_claims"] > 0 and not controls["completeness_liar"]["summary"]["qualified_absolute_target"],
        "answerability_liar_fails": controls["answerability_liar"]["summary"]["answerability_overclaims"] > 0 and not controls["answerability_liar"]["summary"]["qualified_absolute_target"],
        "deterministic_replay": deterministic,
        "source_enumeration_invariance": all(v["passed"] for v in invariance.values()),
        "mutation_sensitivity": all(v["passed"] for v in mutations.values()),
    }

    out = {
        "record": "eb-rc3-first-sealed-apparatus-control",
        "production_identity": production_identity,
        "hybrid_sealed_exposed": False,
        "semantic_sealed_exposed": False,
        "gate_pass": all(gate_checks.values()),
        "gate_checks": gate_checks,
        "lexical_failure_categories": sorted(lexical_failure_categories),
        "controls": controls,
        "deterministic_replay": {"passed": deterministic, "replay_hashes": replay_hashes},
        "source_enumeration_invariance": invariance,
        "mutation_probes": mutations,
        "raw_bm25_results": raw_results["bm25"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate_pass": out["gate_pass"], "gate_checks": gate_checks, "bm25": controls["bm25"]["summary"], "oracle": oracle, "lexical_failure_categories": out["lexical_failure_categories"]}, sort_keys=True, indent=2))
    raise SystemExit(0 if out["gate_pass"] else 2)


if __name__ == "__main__":
    main()
