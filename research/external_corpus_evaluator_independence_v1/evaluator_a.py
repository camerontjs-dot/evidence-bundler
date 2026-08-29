from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


class ContractError(ValueError):
    pass


DEGREES = {"DECISIVE", "PARTIAL", "TOPICAL", "IRRELEVANT", "UNKNOWN"}
ROLES = {"SUPPORT", "COUNTEREVIDENCE", "NEUTRAL_OR_NOT_APPLICABLE", "UNKNOWN"}
GROUP_KINDS = {"JOINTLY_REQUIRED", "ALTERNATIVE_SUFFICIENT"}


@dataclass(frozen=True)
class EvalContext:
    k: int
    corpus_ids: frozenset[str]


def _validate_envelope(manifest: dict[str, Any], gold: dict[str, Any], run: dict[str, Any]) -> EvalContext:
    for name, obj in (("manifest", manifest), ("gold", gold), ("run", run)):
        if not isinstance(obj, dict):
            raise ContractError(f"{name} must be an object")
    for key in ("corpus_version", "corpus_sha256", "benchmark_sha256"):
        if gold.get(key) != manifest.get(key) or run.get(key) != manifest.get(key):
            raise ContractError(f"identity mismatch: {key}")
    k = run.get("k")
    if type(k) is not int or k <= 0:
        raise ContractError("k must be a positive integer")
    passages = manifest.get("passages")
    if not isinstance(passages, list) or not passages:
        raise ContractError("manifest passages must be non-empty")
    ids = [p.get("passage_id") if isinstance(p, dict) else None for p in passages]
    if not all(isinstance(x, str) for x in ids) or len(set(ids)) != len(ids):
        raise ContractError("manifest passage IDs must be unique strings")
    return EvalContext(k=k, corpus_ids=frozenset(ids))


def _validate_judgment(j: dict[str, Any], corpus_ids: frozenset[str]) -> None:
    pid = j.get("passage_id")
    degree = j.get("relevance_degree")
    binary = j.get("binary_relevant")
    gain = j.get("gain")
    role = j.get("role")
    if not isinstance(pid, str) or pid not in corpus_ids:
        raise ContractError("judgment references unknown passage")
    if degree not in DEGREES or role not in ROLES:
        raise ContractError("invalid relevance degree or role")
    if degree == "UNKNOWN":
        if binary is not None or gain is not None:
            raise ContractError("UNKNOWN must have null binary_relevant and gain")
        return
    if type(binary) is not bool or type(gain) is not int or gain < 0:
        raise ContractError("resolved judgments require boolean relevance and non-negative integer gain")
    if binary and gain <= 0:
        raise ContractError("relevant judgment must have positive gain")
    if not binary and gain != 0:
        raise ContractError("non-relevant judgment must have zero gain")


def _index_gold(gold: dict[str, Any], corpus_ids: frozenset[str]) -> dict[str, dict[str, Any]]:
    rows = gold.get("queries")
    if not isinstance(rows, list) or not rows:
        raise ContractError("gold queries required")
    out: dict[str, dict[str, Any]] = {}
    for q in rows:
        qid = q.get("query_id") if isinstance(q, dict) else None
        if not isinstance(qid, str) or qid in out:
            raise ContractError("gold query IDs must be unique strings")
        judgments = q.get("judgments", [])
        groups = q.get("groups", [])
        if not isinstance(judgments, list) or not isinstance(groups, list):
            raise ContractError("judgments/groups must be lists")
        seen: set[str] = set()
        for j in judgments:
            if not isinstance(j, dict):
                raise ContractError("invalid judgment")
            _validate_judgment(j, corpus_ids)
            pid = j["passage_id"]
            if pid in seen:
                raise ContractError("duplicate judgment passage ID")
            seen.add(pid)
        group_ids: set[str] = set()
        for g in groups:
            if not isinstance(g, dict):
                raise ContractError("invalid group")
            gid = g.get("group_id")
            kind = g.get("group_kind")
            members = g.get("passage_ids")
            if not isinstance(gid, str) or gid in group_ids or kind not in GROUP_KINDS:
                raise ContractError("invalid/duplicate group")
            if not isinstance(members, list) or not members or not all(isinstance(x, str) for x in members):
                raise ContractError("invalid group members")
            if len(set(members)) != len(members) or not set(members) <= corpus_ids:
                raise ContractError("duplicate/unknown group member")
            group_ids.add(gid)
        out[qid] = q
    return out


def _index_run(run: dict[str, Any], corpus_ids: frozenset[str], k: int) -> dict[str, list[str]]:
    rows = run.get("queries")
    if not isinstance(rows, list) or not rows:
        raise ContractError("run queries required")
    out: dict[str, list[str]] = {}
    for row in rows:
        qid = row.get("query_id") if isinstance(row, dict) else None
        hits = row.get("hits") if isinstance(row, dict) else None
        if not isinstance(qid, str) or qid in out or not isinstance(hits, list) or len(hits) > k:
            raise ContractError("invalid run query/hit list")
        ids: list[str] = []
        for rank, hit in enumerate(hits, 1):
            if not isinstance(hit, dict) or hit.get("rank") != rank:
                raise ContractError("ranks must be contiguous integers starting at 1")
            pid = hit.get("passage_id")
            if not isinstance(pid, str) or pid not in corpus_ids:
                raise ContractError("run references unknown passage")
            ids.append(pid)
        if len(ids) != len(set(ids)):
            raise ContractError("duplicate ranked passage ID")
        out[qid] = ids
    return out


def _macro(values: list[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return None if not vals else sum(vals) / len(vals)


def _query_metrics(q: dict[str, Any], hits: list[str], k: int, allow_ndcg: bool) -> dict[str, float | None]:
    top = hits[:k]
    got = set(top)
    judgments = {j["passage_id"]: j for j in q.get("judgments", [])}
    relevant = {p for p, j in judgments.items() if j["binary_relevant"] is True}
    support = {p for p, j in judgments.items() if j["binary_relevant"] is True and j["role"] == "SUPPORT"}
    counter = {p for p, j in judgments.items() if j["binary_relevant"] is True and j["role"] == "COUNTEREVIDENCE"}

    def recall(target: set[str]) -> float | None:
        return None if not target else len(got & target) / len(target)

    groups = q.get("groups", [])
    group_coverage = None
    if groups:
        satisfied = 0
        for g in groups:
            members = set(g["passage_ids"])
            satisfied += members <= got if g["group_kind"] == "JOINTLY_REQUIRED" else bool(members & got)
        group_coverage = satisfied / len(groups)

    ndcg = None
    if allow_ndcg:
        dcg = sum(((2 ** (judgments.get(pid, {}).get("gain") or 0)) - 1) / math.log2(rank + 1) for rank, pid in enumerate(top, 1))
        ideal = sorted((j["gain"] for j in judgments.values() if j["gain"] is not None), reverse=True)[:k]
        idcg = sum(((2**gain) - 1) / math.log2(rank + 1) for rank, gain in enumerate(ideal, 1))
        ndcg = None if idcg == 0 else dcg / idcg

    return {
        "hit_at_k": None if not relevant else float(bool(got & relevant)),
        "evidence_recall_at_k": recall(support),
        "counterevidence_recall_at_k": recall(counter),
        "ndcg_at_k": ndcg,
        "joint_group_coverage_at_k": group_coverage,
        "judgment_coverage_at_k": 1.0 if not top else sum(pid in judgments for pid in top) / len(top),
        "resolved_judgment_coverage_at_k": 1.0 if not top else sum(pid in judgments and judgments[pid]["binary_relevant"] is not None for pid in top) / len(top),
    }


def evaluate(manifest: dict[str, Any], gold: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    ctx = _validate_envelope(manifest, gold, run)
    gold_by_q = _index_gold(gold, ctx.corpus_ids)
    run_by_q = _index_run(run, ctx.corpus_ids, ctx.k)
    if set(gold_by_q) != set(run_by_q):
        raise ContractError("query set mismatch")
    mode = gold.get("qrels_mode")
    if mode not in {"complete_relevant_set", "partial"}:
        raise ContractError("invalid qrels_mode")
    judgments = [j for q in gold_by_q.values() for j in q.get("judgments", [])]
    positive_gains = {j["gain"] for j in judgments if isinstance(j.get("gain"), int) and j["gain"] > 0}
    has_unknown = any(j["binary_relevant"] is None for j in judgments)
    allow_ndcg = bool(gold.get("ndcg_eligible")) and mode == "complete_relevant_set" and not has_unknown and len(positive_gains) >= 2
    per_query = {qid: _query_metrics(gold_by_q[qid], run_by_q[qid], ctx.k, allow_ndcg) for qid in sorted(gold_by_q)}
    names = next(iter(per_query.values())).keys()
    aggregate = {name: _macro([m[name] for m in per_query.values()]) for name in names}
    return {"status": "ok", "k": ctx.k, "qrels_mode": mode, "metric_interpretation": "lower_bound" if mode == "partial" else "point_estimate", "ndcg_eligible": allow_ndcg, "aggregate": aggregate, "per_query": per_query}
