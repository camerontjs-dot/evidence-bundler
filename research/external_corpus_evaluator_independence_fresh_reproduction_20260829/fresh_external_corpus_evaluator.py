#!/usr/bin/env python3
"""Independent implementation of External Corpus Retrieval Evaluator Contract v0.2-draft.

Implemented from the frozen contract and authorized dummy inputs only.
No existing evaluator, canonicalizer, test, expected-output, or comparison artifact
was consulted before this file was frozen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence


RELEVANCE_DEGREES = {"DECISIVE", "PARTIAL", "TOPICAL", "IRRELEVANT", "UNKNOWN"}
ROLES = {"SUPPORT", "COUNTEREVIDENCE", "NEUTRAL_OR_NOT_APPLICABLE", "UNKNOWN"}
GROUP_KINDS = {"JOINTLY_REQUIRED", "ALTERNATIVE_SUFFICIENT"}
QRELS_MODES = {"complete_relevant_set", "partial"}


class EvalContractError(ValueError):
    """Raised when an input violates the frozen evaluator contract."""


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvalContractError(message)


def _require_mapping(value: Any, where: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{where} must be an object")
    return value


def _require_list(value: Any, where: str) -> List[Any]:
    _require(isinstance(value, list), f"{where} must be a list")
    return value


def _require_nonempty_string(value: Any, where: str) -> str:
    _require(isinstance(value, str) and bool(value), f"{where} must be a non-empty string")
    return value


def _unique_ids(records: Sequence[Any], key: str, where: str) -> Dict[str, Mapping[str, Any]]:
    out: Dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(records):
        record = _require_mapping(raw, f"{where}[{index}]")
        ident = _require_nonempty_string(record.get(key), f"{where}[{index}].{key}")
        _require(ident not in out, f"duplicate {key} {ident!r} in {where}")
        out[ident] = record
    return out


def _identity_tuple(obj: Mapping[str, Any], where: str) -> tuple[str, str, str]:
    return (
        _require_nonempty_string(obj.get("corpus_version"), f"{where}.corpus_version"),
        _require_nonempty_string(obj.get("corpus_sha256"), f"{where}.corpus_sha256"),
        _require_nonempty_string(obj.get("benchmark_sha256"), f"{where}.benchmark_sha256"),
    )


def _canonicalize(value: Any, parent_key: str | None = None) -> Any:
    if isinstance(value, Mapping):
        return {key: _canonicalize(value[key], key) for key in sorted(value)}
    if isinstance(value, list):
        items = [_canonicalize(item, None) for item in value]
        if parent_key == "queries":
            return sorted(items, key=lambda x: x["query_id"])
        if parent_key == "judgments":
            return sorted(items, key=lambda x: x["passage_id"])
        if parent_key == "groups":
            return sorted(items, key=lambda x: x["group_id"])
        if parent_key == "passage_ids":
            return sorted(items)
        return items
    return value


def canonical_json_bytes(gold: Mapping[str, Any]) -> bytes:
    canonical = _canonicalize(gold)
    return json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def commitment_sha256(gold: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(gold)).hexdigest()


def _validate_manifest(manifest: Mapping[str, Any]) -> tuple[Dict[str, Mapping[str, Any]], Dict[str, Mapping[str, Any]], Dict[str, Mapping[str, Any]]]:
    queries = _unique_ids(_require_list(manifest.get("queries"), "manifest.queries"), "query_id", "manifest.queries")
    sources = _unique_ids(_require_list(manifest.get("sources"), "manifest.sources"), "source_id", "manifest.sources")
    passages = _unique_ids(_require_list(manifest.get("passages"), "manifest.passages"), "passage_id", "manifest.passages")

    for passage_id, passage in passages.items():
        source_id = _require_nonempty_string(passage.get("source_id"), f"manifest.passages[{passage_id}].source_id")
        _require(source_id in sources, f"passage {passage_id!r} references unknown source {source_id!r}")
        locator = passage.get("locator")
        representation = passage.get("representation_identity")
        _require(
            (isinstance(locator, str) and bool(locator)) or representation is not None,
            f"passage {passage_id!r} lacks a reconstructable locator/representation identity",
        )
    return queries, sources, passages


def _validate_gold(
    gold: Mapping[str, Any],
    manifest_queries: Mapping[str, Mapping[str, Any]],
    passages: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Mapping[str, Any]]:
    qrels_mode = gold.get("qrels_mode")
    _require(qrels_mode in QRELS_MODES, f"invalid qrels_mode {qrels_mode!r}")
    _require(isinstance(gold.get("ndcg_eligible"), bool), "gold.ndcg_eligible must be boolean")

    gold_queries = _unique_ids(_require_list(gold.get("queries"), "gold.queries"), "query_id", "gold.queries")
    _require(set(gold_queries) == set(manifest_queries), "gold query-ID set must exactly match manifest query-ID set")

    for query_id, query in gold_queries.items():
        judgments = _unique_ids(_require_list(query.get("judgments"), f"gold[{query_id}].judgments"), "passage_id", f"gold[{query_id}].judgments")
        for passage_id, judgment in judgments.items():
            _require(passage_id in passages, f"judgment references unknown passage {passage_id!r}")
            degree = judgment.get("relevance_degree")
            role = judgment.get("role")
            binary = judgment.get("binary_relevant")
            gain = judgment.get("gain")
            _require(degree in RELEVANCE_DEGREES, f"invalid relevance_degree {degree!r}")
            _require(role in ROLES, f"invalid role {role!r}")
            if degree == "UNKNOWN":
                _require(binary is None and gain is None, "UNKNOWN judgment requires null binary_relevant and gain")
            else:
                _require(isinstance(binary, bool), "resolved judgment requires boolean binary_relevant")
                _require(_is_int(gain) and gain >= 0, "resolved judgment requires non-negative integer gain")
                if binary:
                    _require(gain > 0, "binary_relevant=true requires positive gain")
                else:
                    _require(gain == 0, "binary_relevant=false requires gain 0")

        groups = _unique_ids(_require_list(query.get("groups"), f"gold[{query_id}].groups"), "group_id", f"gold[{query_id}].groups")
        for group_id, group in groups.items():
            kind = group.get("group_kind")
            _require(kind in GROUP_KINDS, f"invalid group_kind {kind!r}")
            member_list = _require_list(group.get("passage_ids"), f"group {group_id}.passage_ids")
            _require(bool(member_list), f"group {group_id!r} must have at least one member")
            members: List[str] = []
            for member in member_list:
                members.append(_require_nonempty_string(member, f"group {group_id}.passage_ids member"))
            _require(len(set(members)) == len(members), f"group {group_id!r} passage_ids must form a set")
            for passage_id in members:
                _require(passage_id in passages, f"group {group_id!r} references unknown passage {passage_id!r}")
    return gold_queries


def _validate_run(
    run: Mapping[str, Any],
    manifest_queries: Mapping[str, Mapping[str, Any]],
    gold_queries: Mapping[str, Mapping[str, Any]],
    passages: Mapping[str, Mapping[str, Any]],
) -> tuple[int, Dict[str, Mapping[str, Any]]]:
    k = run.get("k")
    _require(_is_int(k) and k > 0, "run.k must be a positive integer")
    run_queries = _unique_ids(_require_list(run.get("queries"), "run.queries"), "query_id", "run.queries")
    _require(set(run_queries) == set(gold_queries), "run query-ID set must exactly match gold query-ID set")
    _require(set(run_queries) == set(manifest_queries), "run query-ID set must exactly match manifest query-ID set")

    for query_id, query in run_queries.items():
        hits = _require_list(query.get("hits"), f"run[{query_id}].hits")
        _require(len(hits) <= k, f"query {query_id!r} has more than K hits")
        seen_passages = set()
        for expected_rank, raw_hit in enumerate(hits, start=1):
            hit = _require_mapping(raw_hit, f"run[{query_id}].hits[{expected_rank - 1}]")
            rank = hit.get("rank")
            _require(_is_int(rank) and rank == expected_rank, f"query {query_id!r} ranks must be contiguous 1..N")
            passage_id = _require_nonempty_string(hit.get("passage_id"), f"run[{query_id}].hits[{expected_rank - 1}].passage_id")
            _require(passage_id in passages, f"run hit references unknown passage {passage_id!r}")
            _require(passage_id not in seen_passages, f"duplicate ranked-hit passage_id {passage_id!r} for query {query_id!r}")
            seen_passages.add(passage_id)
    return k, run_queries


def _mean_defined(values: Iterable[float | int | None]) -> float | None:
    defined = [float(value) for value in values if value is not None]
    return sum(defined) / len(defined) if defined else None


def _ndcg_at_k(judgments: Mapping[str, Mapping[str, Any]], hit_ids: Sequence[str], k: int) -> float:
    gain_by_passage = {
        passage_id: int(judgment["gain"])
        for passage_id, judgment in judgments.items()
        if judgment.get("gain") is not None
    }
    dcg = 0.0
    for rank, passage_id in enumerate(hit_ids[:k], start=1):
        gain = gain_by_passage.get(passage_id, 0)
        dcg += ((2 ** gain) - 1) / math.log2(rank + 1)

    ideal_gains = sorted(gain_by_passage.values(), reverse=True)[:k]
    idcg = sum(((2 ** gain) - 1) / math.log2(rank + 1) for rank, gain in enumerate(ideal_gains, start=1))
    _require(idcg > 0, "nDCG eligibility requires positive ideal gain")
    return dcg / idcg


def evaluate(manifest: Mapping[str, Any], gold: Mapping[str, Any], run: Mapping[str, Any]) -> Dict[str, Any]:
    manifest = _require_mapping(manifest, "manifest")
    gold = _require_mapping(gold, "gold")
    run = _require_mapping(run, "run")

    manifest_identity = _identity_tuple(manifest, "manifest")
    gold_identity = _identity_tuple(gold, "gold")
    run_identity = _identity_tuple(run, "run")
    _require(manifest_identity == gold_identity == run_identity, "manifest/gold/run identity mismatch")

    manifest_queries, _sources, passages = _validate_manifest(manifest)
    gold_queries = _validate_gold(gold, manifest_queries, passages)
    k, run_queries = _validate_run(run, manifest_queries, gold_queries, passages)

    qrels_mode = gold["qrels_mode"]
    ndcg_eligible = gold["ndcg_eligible"]
    metric_interpretation = "lower_bound" if qrels_mode == "partial" else "complete_relevant_set"

    per_query: Dict[str, Dict[str, Any]] = {}
    for query_id in sorted(gold_queries):
        gold_query = gold_queries[query_id]
        run_query = run_queries[query_id]
        judgments = _unique_ids(gold_query["judgments"], "passage_id", f"gold[{query_id}].judgments")
        groups = _unique_ids(gold_query["groups"], "group_id", f"gold[{query_id}].groups")
        hit_ids = [hit["passage_id"] for hit in run_query["hits"]]
        hit_set = set(hit_ids)

        known_positive = {pid for pid, j in judgments.items() if j.get("binary_relevant") is True}
        support_positive = {pid for pid, j in judgments.items() if j.get("binary_relevant") is True and j.get("role") == "SUPPORT"}
        counter_positive = {pid for pid, j in judgments.items() if j.get("binary_relevant") is True and j.get("role") == "COUNTEREVIDENCE"}

        hit_at_k = None if not known_positive else (1 if hit_set & known_positive else 0)
        evidence_recall = None if not support_positive else len(hit_set & support_positive) / len(support_positive)
        counter_recall = None if not counter_positive else len(hit_set & counter_positive) / len(counter_positive)

        unresolved_unknown_exists = any(j.get("relevance_degree") == "UNKNOWN" for j in judgments.values())
        positive_gain_levels = {
            j["gain"]
            for j in judgments.values()
            if j.get("gain") is not None and j.get("gain") > 0
        }
        ndcg = None
        if ndcg_eligible and qrels_mode == "complete_relevant_set" and not unresolved_unknown_exists and len(positive_gain_levels) >= 2:
            ndcg = _ndcg_at_k(judgments, hit_ids, k)

        group_coverage = None
        if groups:
            satisfied = 0
            for group in groups.values():
                members = set(group["passage_ids"])
                if group["group_kind"] == "JOINTLY_REQUIRED":
                    covered = members.issubset(hit_set)
                else:
                    covered = bool(members & hit_set)
                satisfied += int(covered)
            group_coverage = satisfied / len(groups)

        if hit_ids:
            judgment_coverage = sum(pid in judgments for pid in hit_ids) / len(hit_ids)
            resolved_judgment_coverage = sum(pid in judgments and judgments[pid].get("binary_relevant") is not None for pid in hit_ids) / len(hit_ids)
        else:
            judgment_coverage = 1.0
            resolved_judgment_coverage = 1.0

        per_query[query_id] = {
            "hit@K": hit_at_k,
            "evidence_recall@K": evidence_recall,
            "counterevidence_recall@K": counter_recall,
            "nDCG@K": ndcg,
            "joint_group_coverage@K": group_coverage,
            "judgment_coverage@K": judgment_coverage,
            "resolved_judgment_coverage@K": resolved_judgment_coverage,
            "metric_interpretation": metric_interpretation,
        }

    aggregate_metric_names = [
        "hit@K",
        "evidence_recall@K",
        "counterevidence_recall@K",
        "nDCG@K",
        "joint_group_coverage@K",
        "judgment_coverage@K",
        "resolved_judgment_coverage@K",
    ]
    aggregate = {
        name: _mean_defined(metrics[name] for metrics in per_query.values())
        for name in aggregate_metric_names
    }

    return {
        "valid": True,
        "k": k,
        "qrels_mode": qrels_mode,
        "metric_interpretation": metric_interpretation,
        "gold_commitment_sha256": commitment_sha256(gold),
        "per_query": per_query,
        "macro_average": aggregate,
    }


def _load(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a ranked run under External Corpus Retrieval Evaluator Contract v0.2-draft")
    parser.add_argument("manifest")
    parser.add_argument("gold")
    parser.add_argument("run")
    args = parser.parse_args()
    try:
        result = evaluate(_load(args.manifest), _load(args.gold), _load(args.run))
    except (EvalContractError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
