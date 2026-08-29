import math


class EvalError(ValueError):
    pass


def _validate(contract, run):
    if run.get("query_id") != contract.get("query_id"):
        raise EvalError("query_id mismatch")
    K = contract.get("K")
    if not isinstance(K, int) or K < 1:
        raise EvalError("invalid K")
    hits = run.get("hits")
    if not isinstance(hits, list):
        raise EvalError("hits must be list")
    if len(hits) > K:
        raise EvalError("K exceeded")
    passage_by_id = {p["passage_id"]: p for p in contract["passages"]}
    if len(passage_by_id) != len(contract["passages"]):
        raise EvalError("duplicate passage registry id")
    seen = set()
    for i, h in enumerate(hits, 1):
        if h.get("rank") != i:
            raise EvalError("non-contiguous rank")
        pid = h.get("passage_id")
        if pid in seen:
            raise EvalError("duplicate returned passage")
        seen.add(pid)
        if pid not in passage_by_id:
            raise EvalError("unknown passage_id")
        if "source_id" in h and h["source_id"] != passage_by_id[pid]["source_id"]:
            raise EvalError("source provenance mismatch")
    return passage_by_id


def evaluate(contract, run):
    passage_by_id = _validate(contract, run)
    ranked = [h["passage_id"] for h in run["hits"]]
    rank = {pid: i + 1 for i, pid in enumerate(ranked)}
    judgments = contract.get("judgments", [])
    judged = {}
    for j in judgments:
        pid = j["passage_id"]
        if pid not in passage_by_id:
            raise EvalError("judgment references unknown passage")
        if pid in judged:
            raise EvalError("duplicate judgment")
        status = j.get("status", "JUDGED")
        if status not in {"JUDGED", "UNKNOWN"}:
            raise EvalError("bad judgment status")
        grade = j.get("grade")
        if status == "UNKNOWN":
            if grade is not None:
                raise EvalError("unknown judgment may not carry grade")
        elif not isinstance(grade, int) or grade < 0:
            raise EvalError("invalid grade")
        judged[pid] = j

    rel = {pid for pid, j in judged.items() if j["status"] == "JUDGED" and j["grade"] > 0}
    retrieved_rel = rel.intersection(ranked)
    hit = 1 if retrieved_rel else 0
    evidence_recall = len(retrieved_rel) / len(rel) if rel else None

    counter = {
        pid
        for pid, j in judged.items()
        if j["status"] == "JUDGED" and j["grade"] > 0 and j.get("role") == "COUNTEREVIDENCE"
    }
    counter_recall = len(counter.intersection(ranked)) / len(counter) if counter else None

    dcg = 0.0
    for i, pid in enumerate(ranked, 1):
        j = judged.get(pid)
        gain = 0 if j is None or j["status"] == "UNKNOWN" else (2 ** j["grade"] - 1)
        dcg += gain / math.log2(i + 1)
    ideal_grades = sorted(
        [j["grade"] for j in judged.values() if j["status"] == "JUDGED" and j["grade"] > 0], reverse=True
    )[: contract["K"]]
    idcg = sum((2**g - 1) / math.log2(i + 1) for i, g in enumerate(ideal_grades, 1))
    ndcg = dcg / idcg if idcg else None

    groups = contract.get("evidence_groups", [])
    group_results = []
    for g in groups:
        members = g["passage_ids"]
        if not members or any(m not in passage_by_id for m in members):
            raise EvalError("invalid evidence group")
        mode = g["mode"]
        if mode == "JOINTLY_REQUIRED":
            ok = all(m in rank for m in members)
        elif mode == "ALTERNATIVE_SUFFICIENT":
            ok = any(m in rank for m in members)
        else:
            raise EvalError("invalid group mode")
        group_results.append({"group_id": g["group_id"], "covered": ok})
    group_coverage = (
        sum(1 for x in group_results if x["covered"]) / len(group_results) if group_results else None
    )

    return {
        "query_id": contract["query_id"],
        "K": contract["K"],
        "hit_at_K": hit,
        "evidence_recall_at_K": evidence_recall,
        "ndcg_at_K": ndcg,
        "counterevidence_recall_at_K": counter_recall,
        "group_coverage_at_K": group_coverage,
        "group_results": group_results,
        "retrieved_passage_ids": ranked,
    }
