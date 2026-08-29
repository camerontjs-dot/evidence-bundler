from __future__ import annotations

import math
from typing import Any


class ContractError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def evaluate(manifest: dict[str, Any], gold: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(manifest, dict) and isinstance(gold, dict) and isinstance(run, dict), "objects required")
    for key in ("corpus_version", "corpus_sha256", "benchmark_sha256"):
        _require(manifest.get(key) == gold.get(key) == run.get(key), f"identity mismatch: {key}")
    k = run.get("k")
    _require(type(k) is int and k > 0, "positive integer K required")
    passage_rows = manifest.get("passages")
    _require(isinstance(passage_rows, list) and passage_rows, "passages required")
    passage_ids = [p.get("passage_id") if isinstance(p, dict) else None for p in passage_rows]
    _require(all(isinstance(x, str) for x in passage_ids), "string passage IDs required")
    _require(len(set(passage_ids)) == len(passage_ids), "duplicate corpus passage ID")
    corpus = set(passage_ids)

    gold_rows = gold.get("queries")
    run_rows = run.get("queries")
    _require(isinstance(gold_rows, list) and gold_rows, "gold queries required")
    _require(isinstance(run_rows, list) and run_rows, "run queries required")
    gold_map: dict[str, dict[str, Any]] = {}
    for row in gold_rows:
        _require(isinstance(row, dict) and isinstance(row.get("query_id"), str), "invalid gold query")
        qid = row["query_id"]
        _require(qid not in gold_map, "duplicate gold query")
        gold_map[qid] = row
    run_map: dict[str, list[str]] = {}
    for row in run_rows:
        _require(isinstance(row, dict) and isinstance(row.get("query_id"), str), "invalid run query")
        qid = row["query_id"]
        _require(qid not in run_map, "duplicate run query")
        hits = row.get("hits")
        _require(isinstance(hits, list) and len(hits) <= k, "invalid hit list")
        ids: list[str] = []
        ranks: list[int] = []
        for hit in hits:
            _require(isinstance(hit, dict), "invalid hit")
            pid = hit.get("passage_id")
            rank = hit.get("rank")
            _require(isinstance(pid, str) and pid in corpus, "unknown hit passage")
            _require(type(rank) is int, "integer rank required")
            ids.append(pid)
            ranks.append(rank)
        _require(ranks == list(range(1, len(hits) + 1)), "malformed ranks")
        _require(len(ids) == len(set(ids)), "duplicate hit passage")
        run_map[qid] = ids
    _require(set(gold_map) == set(run_map), "query set mismatch")

    mode = gold.get("qrels_mode")
    _require(mode in {"complete_relevant_set", "partial"}, "invalid qrels_mode")
    prepared: dict[str, dict[str, Any]] = {}
    max_grade = 0
    for qid, row in gold_map.items():
        judgments = row.get("judgments", [])
        groups = row.get("groups", [])
        _require(isinstance(judgments, list) and isinstance(groups, list), "judgments/groups must be lists")
        by_pid: dict[str, tuple[int, str]] = {}
        for judgment in judgments:
            _require(isinstance(judgment, dict), "invalid judgment")
            pid = judgment.get("passage_id")
            grade = judgment.get("grade")
            role = judgment.get("role")
            _require(isinstance(pid, str) and pid in corpus and pid not in by_pid, "invalid judgment passage")
            _require(type(grade) is int and grade >= 0, "invalid grade")
            _require(role in {"support", "counterevidence", "other"}, "invalid role")
            by_pid[pid] = (grade, role)
            max_grade = max(max_grade, grade)
        normalized_groups: list[frozenset[str]] = []
        seen_group_ids: set[str] = set()
        for group in groups:
            _require(isinstance(group, dict) and isinstance(group.get("group_id"), str), "invalid group")
            gid = group["group_id"]
            members = group.get("required_passage_ids")
            _require(gid not in seen_group_ids, "duplicate group ID")
            _require(isinstance(members, list) and members and all(isinstance(x, str) for x in members), "invalid group members")
            _require(len(set(members)) == len(members) and set(members) <= corpus, "invalid group membership")
            seen_group_ids.add(gid)
            normalized_groups.append(frozenset(members))
        prepared[qid] = {"judgments": by_pid, "groups": normalized_groups}

    allow_ndcg = bool(gold.get("ndcg_eligible")) and max_grade > 1 and mode == "complete_relevant_set"
    per_query: dict[str, dict[str, float | None]] = {}
    for qid in sorted(prepared):
        judgments: dict[str, tuple[int, str]] = prepared[qid]["judgments"]
        ranked = run_map[qid][:k]
        got = set(ranked)
        positives = {p for p, (g, _) in judgments.items() if g > 0}
        supports = {p for p, (g, r) in judgments.items() if g > 0 and r == "support"}
        counters = {p for p, (g, r) in judgments.items() if g > 0 and r == "counterevidence"}
        groups: list[frozenset[str]] = prepared[qid]["groups"]

        def recall(target: set[str]) -> float | None:
            return None if not target else len(got & target) / len(target)

        ndcg: float | None = None
        if allow_ndcg:
            gains = [judgments.get(pid, (0, "other"))[0] for pid in ranked]
            ideal = sorted((g for g, _ in judgments.values()), reverse=True)[:k]
            dcg = sum(((2**g) - 1) / math.log2(i + 2) for i, g in enumerate(gains))
            idcg = sum(((2**g) - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
            ndcg = None if idcg == 0 else dcg / idcg
        per_query[qid] = {
            "hit_at_k": None if not positives else float(bool(got & positives)),
            "evidence_recall_at_k": recall(supports),
            "counterevidence_recall_at_k": recall(counters),
            "ndcg_at_k": ndcg,
            "joint_group_coverage_at_k": None if not groups else sum(group <= got for group in groups) / len(groups),
            "judgment_coverage_at_k": 1.0 if not ranked else sum(pid in judgments for pid in ranked) / len(ranked),
        }

    names = list(next(iter(per_query.values())))
    aggregate: dict[str, float | None] = {}
    for name in names:
        numbers = [metrics[name] for metrics in per_query.values() if metrics[name] is not None]
        aggregate[name] = None if not numbers else sum(numbers) / len(numbers)
    return {"status": "ok", "k": k, "qrels_mode": mode, "metric_interpretation": "lower_bound" if mode == "partial" else "point_estimate", "ndcg_eligible": allow_ndcg, "aggregate": aggregate, "per_query": per_query}
