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
    query_ids: frozenset[str]
    source_ids: frozenset[str]
    passage_ids: frozenset[str]


def _unique_ids(rows: Any, key: str, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise ContractError(f"{label} must be a list")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ContractError(f"{label} rows must be objects")
        ident = row.get(key)
        if not isinstance(ident, str) or not ident or ident in out:
            raise ContractError(f"{label} IDs must be unique non-empty strings")
        out[ident] = row
    return out


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

    queries = _unique_ids(manifest.get("queries"), "query_id", "manifest queries")
    sources = _unique_ids(manifest.get("sources"), "source_id", "manifest sources")
    passages = _unique_ids(manifest.get("passages"), "passage_id", "manifest passages")

    for pid, passage in passages.items():
        sid = passage.get("source_id")
        if not isinstance(sid, str) or sid not in sources:
            raise ContractError(f"passage {pid!r} references unknown source")
        locator = passage.get("locator")
        representation = passage.get("representation_identity")
        if not ((isinstance(locator, str) and locator) or representation is not None):
            raise ContractError(f"passage {pid!r} lacks reconstructable locator/representation identity")

    return EvalContext(
        k=k,
        query_ids=frozenset(queries),
        source_ids=frozenset(sources),
        passage_ids=frozenset(passages),
    )


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


def _index_gold(gold: dict[str, Any], ctx: EvalContext) -> dict[str, dict[str, Any]]:
    rows = _unique_ids(gold.get("queries"), "query_id", "gold queries")
    if set(rows) != set(ctx.query_ids):
        raise ContractError("gold query set must match manifest query set")

    for qid, q in rows.items():
        judgments = q.get("judgments", [])
        groups = q.get("groups", [])
        if not isinstance(judgments, list) or not isinstance(groups, list):
            raise ContractError("judgments/groups must be lists")
        seen: set[str] = set()
        for j in judgments:
            if not isinstance(j, dict):
                raise ContractError("invalid judgment")
            _validate_judgment(j, ctx.passage_ids)
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
            if not isinstance(gid, str) or not gid or gid in group_ids or kind not in GROUP_KINDS:
                raise ContractError("invalid/duplicate group")
            if not isinstance(members, list) or not members or not all(isinstance(x, str) and x for x in members):
                raise ContractError("invalid group members")
            if len(set(members)) != len(members) or not set(members) <= ctx.passage_ids:
                raise ContractError("duplicate/unknown group member")
            group_ids.add(gid)
    return rows


def _index_run(run: dict[str, Any], ctx: EvalContext) -> dict[str, list[str]]:
    rows = _unique_ids(run.get("queries"), "query_id", "run queries")
    if set(rows) != set(ctx.query_ids):
        raise ContractError("run query set must match manifest query set")

    out: dict[str, list[str]] = {}
    for qid, row in rows.items():
        hits = row.get("hits")
        if not isinstance(hits, list) or len(hits) > ctx.k:
            raise ContractError("invalid run hit list")
        ids: list[str] = []
        for rank, hit in enumerate(hits, 1):
            if not isinstance(hit, dict) or type(hit.get("rank")) is not int or hit.get("rank") != rank:
                raise ContractError("ranks must be contiguous integers starting at 1")
            pid = hit.get("passage_id")
            if not isinstance(pid, str) or pid not in ctx.passage_ids:
                raise ContractError("run references unknown passage")
            ids.append(pid)
        if len(ids) != len(set(ids)):
            raise ContractError("duplicate ranked passage ID")
        out[qid] = ids
    return out


def _macro(values: list[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return None if not vals else sum(vals) / len(vals)


def _query_ndcg_eligible(q: dict[str, Any], gold: dict[str, Any]) -> bool:
    if gold.get("ndcg_eligible") is not True or gold.get("qrels_mode") != "complete_relevant_set":
        return False
    judgments = q.get("judgments", [])
    if any(j.get("binary_relevant") is None for j in judgments):
        return False
    gains = {j["gain"] for j in judgments if type(j.get("gain")) is int and j["gain"] > 0}
    return len(gains) >= 2


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
    mode = gold.get("qrels_mode")
    if mode not in {"complete_relevant_set", "partial"}:
        raise ContractError("invalid qrels_mode")
    if type(gold.get("ndcg_eligible")) is not bool:
        raise ContractError("ndcg_eligible must be boolean")

    gold_by_q = _index_gold(gold, ctx)
    run_by_q = _index_run(run, ctx)
    if set(gold_by_q) != set(run_by_q):
        raise ContractError("query set mismatch")

    ndcg_by_query = {qid: _query_ndcg_eligible(gold_by_q[qid], gold) for qid in sorted(gold_by_q)}
    per_query = {
        qid: _query_metrics(gold_by_q[qid], run_by_q[qid], ctx.k, ndcg_by_query[qid])
        for qid in sorted(gold_by_q)
    }
    metric_names = next(iter(per_query.values())).keys() if per_query else []
    aggregate = {name: _macro([m[name] for m in per_query.values()]) for name in metric_names}

    return {
        "status": "ok",
        "k": ctx.k,
        "qrels_mode": mode,
        "metric_interpretation": "lower_bound" if mode == "partial" else "point_estimate",
        "ndcg_eligible": any(ndcg_by_query.values()),
        "ndcg_eligible_by_query": ndcg_by_query,
        "aggregate": aggregate,
        "per_query": per_query,
    }
