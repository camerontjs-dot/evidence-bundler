from __future__ import annotations

import math
from typing import Any


class ContractError(ValueError):
    pass


def _ok(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def evaluate(manifest: dict[str, Any], gold: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    _ok(all(isinstance(x, dict) for x in (manifest, gold, run)), "objects required")
    for key in ("corpus_version", "corpus_sha256", "benchmark_sha256"):
        _ok(len({manifest.get(key), gold.get(key), run.get(key)}) == 1, f"identity mismatch: {key}")
    k = run.get("k")
    _ok(type(k) is int and k > 0, "positive K required")

    passage_rows = manifest.get("passages")
    _ok(isinstance(passage_rows, list) and passage_rows, "passages required")
    corpus_list = [x.get("passage_id") if isinstance(x, dict) else None for x in passage_rows]
    _ok(all(isinstance(x, str) for x in corpus_list) and len(corpus_list) == len(set(corpus_list)), "bad corpus IDs")
    corpus = set(corpus_list)

    mode = gold.get("qrels_mode")
    _ok(mode in {"complete_relevant_set", "partial"}, "bad qrels mode")
    gold_rows = gold.get("queries")
    run_rows = run.get("queries")
    _ok(isinstance(gold_rows, list) and gold_rows and isinstance(run_rows, list) and run_rows, "query rows required")

    gmap: dict[str, dict[str, Any]] = {}
    unknown_exists = False
    positive_gains: set[int] = set()
    for q in gold_rows:
        _ok(isinstance(q, dict) and isinstance(q.get("query_id"), str), "bad gold query")
        qid = q["query_id"]
        _ok(qid not in gmap, "duplicate gold query")
        js = q.get("judgments", [])
        gs = q.get("groups", [])
        _ok(isinstance(js, list) and isinstance(gs, list), "bad judgment/group collections")
        seen_j: set[str] = set()
        for j in js:
            _ok(isinstance(j, dict), "bad judgment")
            pid = j.get("passage_id")
            degree = j.get("relevance_degree")
            binary = j.get("binary_relevant")
            gain = j.get("gain")
            role = j.get("role")
            _ok(isinstance(pid, str) and pid in corpus and pid not in seen_j, "bad judgment passage")
            _ok(degree in {"DECISIVE", "PARTIAL", "TOPICAL", "IRRELEVANT", "UNKNOWN"}, "bad degree")
            _ok(role in {"SUPPORT", "COUNTEREVIDENCE", "NEUTRAL_OR_NOT_APPLICABLE", "UNKNOWN"}, "bad role")
            if degree == "UNKNOWN":
                _ok(binary is None and gain is None, "UNKNOWN must be null-valued")
                unknown_exists = True
            else:
                _ok(type(binary) is bool and type(gain) is int and gain >= 0, "resolved judgment shape")
                _ok((binary and gain > 0) or ((not binary) and gain == 0), "binary/gain inconsistency")
                if gain > 0:
                    positive_gains.add(gain)
            seen_j.add(pid)
        seen_g: set[str] = set()
        for group in gs:
            _ok(isinstance(group, dict), "bad group")
            gid = group.get("group_id")
            kind = group.get("group_kind")
            members = group.get("passage_ids")
            _ok(isinstance(gid, str) and gid not in seen_g, "bad group ID")
            _ok(kind in {"JOINTLY_REQUIRED", "ALTERNATIVE_SUFFICIENT"}, "bad group kind")
            _ok(isinstance(members, list) and members and all(isinstance(x, str) for x in members), "bad group members")
            _ok(len(set(members)) == len(members) and set(members) <= corpus, "bad group membership")
            seen_g.add(gid)
        gmap[qid] = q

    rmap: dict[str, list[str]] = {}
    for q in run_rows:
        _ok(isinstance(q, dict) and isinstance(q.get("query_id"), str), "bad run query")
        qid = q["query_id"]
        hits = q.get("hits")
        _ok(qid not in rmap and isinstance(hits, list) and len(hits) <= k, "bad run hit list")
        ids: list[str] = []
        ranks: list[int] = []
        for h in hits:
            _ok(isinstance(h, dict), "bad hit")
            pid, rank = h.get("passage_id"), h.get("rank")
            _ok(isinstance(pid, str) and pid in corpus and type(rank) is int, "bad hit identity/rank")
            ids.append(pid); ranks.append(rank)
        _ok(ranks == list(range(1, len(ids) + 1)) and len(ids) == len(set(ids)), "rank/duplicate violation")
        rmap[qid] = ids
    _ok(set(gmap) == set(rmap), "query set mismatch")

    ndcg_allowed = bool(gold.get("ndcg_eligible")) and mode == "complete_relevant_set" and not unknown_exists and len(positive_gains) >= 2
    per: dict[str, dict[str, float | None]] = {}
    for qid in sorted(gmap):
        q = gmap[qid]
        ranked = rmap[qid][:k]
        got = set(ranked)
        js = {j["passage_id"]: j for j in q.get("judgments", [])}
        rel = {p for p, j in js.items() if j["binary_relevant"] is True}
        sup = {p for p, j in js.items() if j["binary_relevant"] is True and j["role"] == "SUPPORT"}
        ctr = {p for p, j in js.items() if j["binary_relevant"] is True and j["role"] == "COUNTEREVIDENCE"}
        def frac(target: set[str]) -> float | None:
            return None if not target else len(got & target) / len(target)
        groups = q.get("groups", [])
        group_value = None
        if groups:
            flags = []
            for group in groups:
                members = set(group["passage_ids"])
                flags.append(members <= got if group["group_kind"] == "JOINTLY_REQUIRED" else bool(members & got))
            group_value = sum(flags) / len(flags)
        ndcg = None
        if ndcg_allowed:
            observed = [js.get(pid, {}).get("gain") or 0 for pid in ranked]
            ideal = sorted((j["gain"] for j in js.values() if j["gain"] is not None), reverse=True)[:k]
            dcg = sum(((2**g)-1)/math.log2(i+2) for i,g in enumerate(observed))
            idcg = sum(((2**g)-1)/math.log2(i+2) for i,g in enumerate(ideal))
            ndcg = None if idcg == 0 else dcg/idcg
        per[qid] = {
            "hit_at_k": None if not rel else float(bool(got & rel)),
            "evidence_recall_at_k": frac(sup),
            "counterevidence_recall_at_k": frac(ctr),
            "ndcg_at_k": ndcg,
            "joint_group_coverage_at_k": group_value,
            "judgment_coverage_at_k": 1.0 if not ranked else sum(p in js for p in ranked)/len(ranked),
            "resolved_judgment_coverage_at_k": 1.0 if not ranked else sum(p in js and js[p]["binary_relevant"] is not None for p in ranked)/len(ranked),
        }
    names = list(next(iter(per.values())))
    aggregate: dict[str, float | None] = {}
    for name in names:
        vals = [row[name] for row in per.values() if row[name] is not None]
        aggregate[name] = None if not vals else sum(vals)/len(vals)
    return {"status":"ok","k":k,"qrels_mode":mode,"metric_interpretation":"lower_bound" if mode=="partial" else "point_estimate","ndcg_eligible":ndcg_allowed,"aggregate":aggregate,"per_query":per}
