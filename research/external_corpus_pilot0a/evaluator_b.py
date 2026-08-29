from math import log2


class ContractFailure(Exception):
    pass


def score(spec, output):
    k = spec["K"]
    if type(k) is not int or k <= 0:
        raise ContractFailure("K")
    if output.get("query_id") != spec.get("query_id"):
        raise ContractFailure("query")
    rows = output.get("hits")
    if type(rows) is not list or len(rows) > k:
        raise ContractFailure("budget")

    passages = {}
    for p in spec.get("passages", []):
        key = p.get("passage_id")
        if not key or key in passages:
            raise ContractFailure("passages")
        passages[key] = p

    result_ids = []
    for zero, row in enumerate(rows):
        if row.get("rank") != zero + 1:
            raise ContractFailure("rank")
        key = row.get("passage_id")
        if key not in passages or key in result_ids:
            raise ContractFailure("identity")
        if row.get("source_id", passages[key]["source_id"]) != passages[key]["source_id"]:
            raise ContractFailure("provenance")
        result_ids.append(key)

    label = {}
    for j in spec.get("judgments", []):
        key = j.get("passage_id")
        if key not in passages or key in label:
            raise ContractFailure("judgments")
        if j.get("status", "JUDGED") == "UNKNOWN":
            if j.get("grade") is not None:
                raise ContractFailure("unknown-grade")
            label[key] = (None, j.get("role"))
        else:
            g = j.get("grade")
            if type(g) is not int or g < 0:
                raise ContractFailure("grade")
            label[key] = (g, j.get("role"))

    positives = [p for p, (g, _) in label.items() if g is not None and g > 0]
    positive_hits = [p for p in result_ids if p in positives]
    hit = int(bool(positive_hits))
    recall = None if not positives else len(positive_hits) / len(positives)

    counters = [
        p for p, (g, r) in label.items() if g is not None and g > 0 and r == "COUNTEREVIDENCE"
    ]
    crecall = None if not counters else len(set(counters) & set(result_ids)) / len(counters)

    gains = []
    for p in result_ids:
        g = label.get(p, (None, None))[0]
        gains.append(0 if g is None else 2**g - 1)
    actual = sum(v / log2(pos + 2) for pos, v in enumerate(gains))
    target_grades = sorted((g for g, _ in label.values() if g is not None and g > 0), reverse=True)[:k]
    ideal = sum((2**g - 1) / log2(pos + 2) for pos, g in enumerate(target_grades))
    ndcg = None if ideal == 0 else actual / ideal

    gr = []
    for group in spec.get("evidence_groups", []):
        members = group.get("passage_ids", [])
        if not members or any(p not in passages for p in members):
            raise ContractFailure("group members")
        if group.get("mode") == "JOINTLY_REQUIRED":
            covered = set(members).issubset(set(result_ids))
        elif group.get("mode") == "ALTERNATIVE_SUFFICIENT":
            covered = bool(set(members) & set(result_ids))
        else:
            raise ContractFailure("group mode")
        gr.append({"group_id": group["group_id"], "covered": covered})
    gcov = None if not gr else sum(int(g["covered"]) for g in gr) / len(gr)

    return {
        "query_id": spec["query_id"],
        "K": k,
        "hit_at_K": hit,
        "evidence_recall_at_K": recall,
        "ndcg_at_K": ndcg,
        "counterevidence_recall_at_K": crecall,
        "group_coverage_at_K": gcov,
        "group_results": gr,
        "retrieved_passage_ids": result_ids,
    }
