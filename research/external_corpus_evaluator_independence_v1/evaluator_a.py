from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class EvalContext:
    k: int
    corpus_ids: frozenset[str]
    corpus_version: str
    corpus_sha256: str
    benchmark_sha256: str


def _validate_envelope(manifest: dict[str, Any], gold: dict[str, Any], run: dict[str, Any]) -> EvalContext:
    for name, obj in (("manifest", manifest), ("gold", gold), ("run", run)):
        if not isinstance(obj, dict):
            raise ContractError(f"{name} must be an object")
    for key in ("corpus_version", "corpus_sha256", "benchmark_sha256"):
        if gold.get(key) != manifest.get(key):
            raise ContractError(f"gold {key} mismatch")
        if run.get(key) != manifest.get(key):
            raise ContractError(f"run {key} mismatch")
    k = run.get("k")
    if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
        raise ContractError("k must be a positive integer")
    passages = manifest.get("passages")
    if not isinstance(passages, list) or not passages:
        raise ContractError("manifest passages must be a non-empty list")
    corpus_ids: list[str] = []
    for p in passages:
        if not isinstance(p, dict) or not isinstance(p.get("passage_id"), str):
            raise ContractError("every passage requires passage_id")
        corpus_ids.append(p["passage_id"])
    if len(set(corpus_ids)) != len(corpus_ids):
        raise ContractError("duplicate passage IDs in manifest")
    return EvalContext(k=k, corpus_ids=frozenset(corpus_ids), corpus_version=str(manifest["corpus_version"]), corpus_sha256=str(manifest["corpus_sha256"]), benchmark_sha256=str(manifest["benchmark_sha256"]))


def _index_gold(gold: dict[str, Any], corpus_ids: frozenset[str]) -> dict[str, dict[str, Any]]:
    queries = gold.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ContractError("gold queries must be a non-empty list")
    out: dict[str, dict[str, Any]] = {}
    for q in queries:
        qid = q.get("query_id") if isinstance(q, dict) else None
        if not isinstance(qid, str) or qid in out:
            raise ContractError("gold query IDs must be unique strings")
        judgments = q.get("judgments", [])
        if not isinstance(judgments, list):
            raise ContractError("judgments must be a list")
        seen: set[str] = set()
        for j in judgments:
            pid = j.get("passage_id") if isinstance(j, dict) else None
            if not isinstance(pid, str) or pid in seen:
                raise ContractError("judgment passage IDs must be unique strings per query")
            if pid not in corpus_ids:
                raise ContractError(f"gold judgment references unknown passage {pid}")
            seen.add(pid)
            grade = j.get("grade")
            if not isinstance(grade, int) or isinstance(grade, bool) or grade < 0:
                raise ContractError("judgment grade must be a non-negative integer")
            role = j.get("role")
            if role not in {"support", "counterevidence", "other"}:
                raise ContractError("judgment role must be support, counterevidence, or other")
        groups = q.get("groups", [])
        if not isinstance(groups, list):
            raise ContractError("groups must be a list")
        group_ids: set[str] = set()
        for g in groups:
            gid = g.get("group_id") if isinstance(g, dict) else None
            members = g.get("required_passage_ids") if isinstance(g, dict) else None
            if not isinstance(gid, str) or gid in group_ids:
                raise ContractError("group IDs must be unique strings per query")
            if not isinstance(members, list) or not members or not all(isinstance(x, str) for x in members):
                raise ContractError("group members must be a non-empty string list")
            if len(set(members)) != len(members):
                raise ContractError("duplicate passage IDs inside a group")
            unknown = set(members) - corpus_ids
            if unknown:
                raise ContractError(f"group references unknown passages: {sorted(unknown)}")
            group_ids.add(gid)
        out[qid] = q
    return out


def _index_run(run: dict[str, Any], corpus_ids: frozenset[str], k: int) -> dict[str, list[str]]:
    rows = run.get("queries")
    if not isinstance(rows, list) or not rows:
        raise ContractError("run queries must be a non-empty list")
    out: dict[str, list[str]] = {}
    for row in rows:
        qid = row.get("query_id") if isinstance(row, dict) else None
        hits = row.get("hits") if isinstance(row, dict) else None
        if not isinstance(qid, str) or qid in out:
            raise ContractError("run query IDs must be unique strings")
        if not isinstance(hits, list):
            raise ContractError("hits must be a list")
        if len(hits) > k:
            raise ContractError("run contains more than K hits")
        ids: list[str] = []
        for expected_rank, hit in enumerate(hits, start=1):
            if not isinstance(hit, dict):
                raise ContractError("each hit must be an object")
            if hit.get("rank") != expected_rank:
                raise ContractError("ranks must be contiguous integers starting at 1")
            pid = hit.get("passage_id")
            if not isinstance(pid, str):
                raise ContractError("hit passage_id must be a string")
            if pid not in corpus_ids:
                raise ContractError(f"run references unknown passage {pid}")
            ids.append(pid)
        if len(ids) != len(set(ids)):
            raise ContractError("duplicate passage IDs in a ranked list")
        out[qid] = ids
    return out


def _macro(values: list[float | None]) -> float | None:
    defined = [x for x in values if x is not None]
    return None if not defined else sum(defined) / len(defined)


def _query_metrics(qgold: dict[str, Any], hits: list[str], k: int, ndcg_eligible: bool) -> dict[str, Any]:
    top = hits[:k]
    top_set = set(top)
    judgments = {j["passage_id"]: j for j in qgold.get("judgments", [])}
    relevant = {pid for pid, j in judgments.items() if j["grade"] > 0}
    support = {pid for pid, j in judgments.items() if j["grade"] > 0 and j["role"] == "support"}
    counter = {pid for pid, j in judgments.items() if j["grade"] > 0 and j["role"] == "counterevidence"}
    hit = None if not relevant else float(bool(top_set & relevant))
    support_recall = None if not support else len(top_set & support) / len(support)
    counter_recall = None if not counter else len(top_set & counter) / len(counter)
    groups = qgold.get("groups", [])
    group_coverage = None
    if groups:
        complete = sum(set(g["required_passage_ids"]).issubset(top_set) for g in groups)
        group_coverage = complete / len(groups)
    judged_at_k = sum(pid in judgments for pid in top)
    judgment_coverage = 1.0 if not top else judged_at_k / len(top)
    ndcg: float | None = None
    if ndcg_eligible:
        dcg = 0.0
        for rank, pid in enumerate(top, start=1):
            grade = judgments.get(pid, {}).get("grade", 0)
            dcg += ((2**grade) - 1) / math.log2(rank + 1)
        ideal_grades = sorted((j["grade"] for j in judgments.values()), reverse=True)[:k]
        idcg = sum(((2**g) - 1) / math.log2(rank + 1) for rank, g in enumerate(ideal_grades, start=1))
        ndcg = None if idcg == 0.0 else dcg / idcg
    return {"hit_at_k": hit, "evidence_recall_at_k": support_recall, "counterevidence_recall_at_k": counter_recall, "ndcg_at_k": ndcg, "joint_group_coverage_at_k": group_coverage, "judgment_coverage_at_k": judgment_coverage}


def evaluate(manifest: dict[str, Any], gold: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    ctx = _validate_envelope(manifest, gold, run)
    gold_by_q = _index_gold(gold, ctx.corpus_ids)
    run_by_q = _index_run(run, ctx.corpus_ids, ctx.k)
    if set(run_by_q) != set(gold_by_q):
        missing = sorted(set(gold_by_q) - set(run_by_q))
        extra = sorted(set(run_by_q) - set(gold_by_q))
        raise ContractError(f"query set mismatch missing={missing} extra={extra}")
    qrels_mode = gold.get("qrels_mode")
    if qrels_mode not in {"complete_relevant_set", "partial"}:
        raise ContractError("qrels_mode must be complete_relevant_set or partial")
    grades = [j["grade"] for q in gold_by_q.values() for j in q.get("judgments", [])]
    graded = any(g > 1 for g in grades)
    ndcg_eligible = bool(gold.get("ndcg_eligible")) and graded and qrels_mode == "complete_relevant_set"
    per_query = {qid: _query_metrics(gold_by_q[qid], run_by_q[qid], ctx.k, ndcg_eligible) for qid in sorted(gold_by_q)}
    metric_names = next(iter(per_query.values())).keys()
    aggregate = {name: _macro([m[name] for m in per_query.values()]) for name in metric_names}
    return {"status": "ok", "k": ctx.k, "qrels_mode": qrels_mode, "metric_interpretation": "lower_bound" if qrels_mode == "partial" else "point_estimate", "ndcg_eligible": ndcg_eligible, "aggregate": aggregate, "per_query": per_query}
