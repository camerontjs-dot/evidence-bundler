from __future__ import annotations

import math
from typing import Any


class ContractError(ValueError):
    pass


VALID_DEGREES = {"DECISIVE", "PARTIAL", "TOPICAL", "IRRELEVANT", "UNKNOWN"}
VALID_ROLES = {"SUPPORT", "COUNTEREVIDENCE", "NEUTRAL_OR_NOT_APPLICABLE", "UNKNOWN"}
VALID_GROUPS = {"JOINTLY_REQUIRED", "ALTERNATIVE_SUFFICIENT"}


def _need(ok: bool, message: str) -> None:
    if not ok:
        raise ContractError(message)


def _index(rows: Any, key: str, label: str) -> dict[str, dict[str, Any]]:
    _need(isinstance(rows, list), f"{label} must be a list")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        _need(isinstance(row, dict), f"{label} rows must be objects")
        ident = row.get(key)
        _need(isinstance(ident, str) and bool(ident) and ident not in result, f"bad/duplicate {label} ID")
        result[ident] = row
    return result


def _validate_manifest(manifest: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    qmap = _index(manifest.get("queries"), "query_id", "manifest query")
    smap = _index(manifest.get("sources"), "source_id", "manifest source")
    pmap = _index(manifest.get("passages"), "passage_id", "manifest passage")
    for pid, passage in pmap.items():
        sid = passage.get("source_id")
        _need(isinstance(sid, str) and sid in smap, f"passage {pid} references unknown source")
        locator = passage.get("locator")
        representation = passage.get("representation_identity")
        _need((isinstance(locator, str) and bool(locator)) or representation is not None, f"passage {pid} lacks locator/representation")
    return set(qmap), set(smap), set(pmap)


def _validate_judgments(query: dict[str, Any], passage_ids: set[str]) -> None:
    judgments = query.get("judgments", [])
    groups = query.get("groups", [])
    _need(isinstance(judgments, list) and isinstance(groups, list), "judgments/groups must be lists")

    seen_j: set[str] = set()
    for j in judgments:
        _need(isinstance(j, dict), "judgment must be object")
        pid = j.get("passage_id")
        degree = j.get("relevance_degree")
        role = j.get("role")
        binary = j.get("binary_relevant")
        gain = j.get("gain")
        _need(isinstance(pid, str) and pid in passage_ids and pid not in seen_j, "bad/duplicate judgment passage")
        _need(degree in VALID_DEGREES and role in VALID_ROLES, "invalid degree/role")
        if degree == "UNKNOWN":
            _need(binary is None and gain is None, "UNKNOWN must be null-valued")
        else:
            _need(type(binary) is bool and type(gain) is int and gain >= 0, "bad resolved judgment")
            _need((binary and gain > 0) or ((not binary) and gain == 0), "binary/gain inconsistency")
        seen_j.add(pid)

    seen_g: set[str] = set()
    for group in groups:
        _need(isinstance(group, dict), "group must be object")
        gid = group.get("group_id")
        kind = group.get("group_kind")
        members = group.get("passage_ids")
        _need(isinstance(gid, str) and bool(gid) and gid not in seen_g, "bad/duplicate group ID")
        _need(kind in VALID_GROUPS, "bad group kind")
        _need(isinstance(members, list) and bool(members) and all(isinstance(x, str) and x for x in members), "bad group members")
        _need(len(set(members)) == len(members) and set(members) <= passage_ids, "duplicate/unknown group member")
        seen_g.add(gid)


def _ndcg_ok(query: dict[str, Any], gold: dict[str, Any]) -> bool:
    if gold.get("ndcg_eligible") is not True or gold.get("qrels_mode") != "complete_relevant_set":
        return False
    rows = query.get("judgments", [])
    if any(j.get("binary_relevant") is None for j in rows):
        return False
    positive_levels = {j.get("gain") for j in rows if type(j.get("gain")) is int and j.get("gain") > 0}
    return len(positive_levels) >= 2


def _score(query: dict[str, Any], ranked: list[str], k: int, allow_ndcg: bool) -> dict[str, float | None]:
    top = ranked[:k]
    got = set(top)
    judgments = {j["passage_id"]: j for j in query.get("judgments", [])}
    relevant = {pid for pid, j in judgments.items() if j["binary_relevant"] is True}
    support = {pid for pid, j in judgments.items() if j["binary_relevant"] is True and j["role"] == "SUPPORT"}
    counter = {pid for pid, j in judgments.items() if j["binary_relevant"] is True and j["role"] == "COUNTEREVIDENCE"}

    def fraction(target: set[str]) -> float | None:
        return None if not target else len(got & target) / len(target)

    groups = query.get("groups", [])
    group_value = None
    if groups:
        flags: list[bool] = []
        for group in groups:
            members = set(group["passage_ids"])
            flags.append(members <= got if group["group_kind"] == "JOINTLY_REQUIRED" else bool(members & got))
        group_value = sum(flags) / len(flags)

    ndcg = None
    if allow_ndcg:
        observed = [judgments.get(pid, {}).get("gain") or 0 for pid in top]
        ideal = sorted((j["gain"] for j in judgments.values() if j["gain"] is not None), reverse=True)[:k]
        dcg = sum(((2**gain) - 1) / math.log2(i + 2) for i, gain in enumerate(observed))
        idcg = sum(((2**gain) - 1) / math.log2(i + 2) for i, gain in enumerate(ideal))
        ndcg = None if idcg == 0 else dcg / idcg

    return {
        "hit_at_k": None if not relevant else float(bool(got & relevant)),
        "evidence_recall_at_k": fraction(support),
        "counterevidence_recall_at_k": fraction(counter),
        "ndcg_at_k": ndcg,
        "joint_group_coverage_at_k": group_value,
        "judgment_coverage_at_k": 1.0 if not top else sum(pid in judgments for pid in top) / len(top),
        "resolved_judgment_coverage_at_k": 1.0 if not top else sum(pid in judgments and judgments[pid]["binary_relevant"] is not None for pid in top) / len(top),
    }


def evaluate(manifest: dict[str, Any], gold: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    _need(all(isinstance(x, dict) for x in (manifest, gold, run)), "objects required")
    for key in ("corpus_version", "corpus_sha256", "benchmark_sha256"):
        _need(len({manifest.get(key), gold.get(key), run.get(key)}) == 1, f"identity mismatch: {key}")

    k = run.get("k")
    _need(type(k) is int and k > 0, "positive K required")
    mode = gold.get("qrels_mode")
    _need(mode in {"complete_relevant_set", "partial"}, "bad qrels mode")
    _need(type(gold.get("ndcg_eligible")) is bool, "ndcg_eligible must be boolean")

    manifest_queries, _sources, passages = _validate_manifest(manifest)
    gmap = _index(gold.get("queries"), "query_id", "gold query")
    rrows = _index(run.get("queries"), "query_id", "run query")
    _need(set(gmap) == manifest_queries, "gold query set must match manifest")
    _need(set(rrows) == manifest_queries, "run query set must match manifest")

    for query in gmap.values():
        _validate_judgments(query, passages)

    ranked: dict[str, list[str]] = {}
    for qid, row in rrows.items():
        hits = row.get("hits")
        _need(isinstance(hits, list) and len(hits) <= k, "bad hit list")
        ids: list[str] = []
        ranks: list[int] = []
        for hit in hits:
            _need(isinstance(hit, dict), "hit must be object")
            pid, rank = hit.get("passage_id"), hit.get("rank")
            _need(isinstance(pid, str) and pid in passages and type(rank) is int, "bad hit identity/rank")
            ids.append(pid)
            ranks.append(rank)
        _need(ranks == list(range(1, len(ids) + 1)) and len(ids) == len(set(ids)), "rank/duplicate violation")
        ranked[qid] = ids

    ndcg_flags = {qid: _ndcg_ok(gmap[qid], gold) for qid in sorted(gmap)}
    per = {qid: _score(gmap[qid], ranked[qid], k, ndcg_flags[qid]) for qid in sorted(gmap)}
    names = list(next(iter(per.values()))) if per else []
    aggregate: dict[str, float | None] = {}
    for name in names:
        values = [row[name] for row in per.values() if row[name] is not None]
        aggregate[name] = None if not values else sum(values) / len(values)

    return {
        "status": "ok",
        "k": k,
        "qrels_mode": mode,
        "metric_interpretation": "lower_bound" if mode == "partial" else "point_estimate",
        "ndcg_eligible": any(ndcg_flags.values()),
        "ndcg_eligible_by_query": ndcg_flags,
        "aggregate": aggregate,
        "per_query": per,
    }
