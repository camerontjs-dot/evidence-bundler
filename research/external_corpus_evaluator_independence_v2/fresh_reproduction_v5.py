from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any


class EvaluationError(ValueError):
    """Raised when an artifact violates External Corpus Evaluator Contract v0.3."""


_RELEVANCE_DEGREES = {"DECISIVE", "PARTIAL", "TOPICAL", "IRRELEVANT", "UNKNOWN"}
_ROLES = {"SUPPORT", "COUNTEREVIDENCE", "NEUTRAL_OR_NOT_APPLICABLE", "UNKNOWN"}
_GROUP_KINDS = {"JOINTLY_REQUIRED", "ALTERNATIVE_SUFFICIENT"}
_QRELS_MODES = {"complete_relevant_set", "partial"}


def _fail(message: str) -> None:
    raise EvaluationError(message)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        _fail(f"{label} must be a list")
    return value


def _require_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{label} must be a non-empty string")
    return value


def _unique_records(records: list[Any], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for i, raw in enumerate(records):
        record = _require_object(raw, f"{label}[{i}]")
        ident = _require_id(record.get(key), f"{label}[{i}].{key}")
        if ident in result:
            _fail(f"duplicate {label} {key}: {ident}")
        result[ident] = record
    return result


def _has_reconstructable_locator(passage: dict[str, Any]) -> bool:
    for key in ("locator", "representation_id", "representation_sha256"):
        value = passage.get(key)
        if isinstance(value, str) and value:
            return True
    representation = passage.get("representation")
    if isinstance(representation, str) and representation:
        return True
    if isinstance(representation, dict) and representation:
        return True
    return False


def _validate_identities(manifest: dict[str, Any], gold: dict[str, Any], run: dict[str, Any]) -> None:
    for key in ("corpus_version", "corpus_sha256", "benchmark_sha256"):
        values = [artifact.get(key) for artifact in (manifest, gold, run)]
        if any(value is None for value in values) or len(set(values)) != 1:
            _fail(f"identity mismatch for {key}")


def _validate_manifest(manifest: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    queries = _unique_records(_require_list(manifest.get("queries"), "manifest.queries"), "query_id", "manifest.queries")
    sources = _unique_records(_require_list(manifest.get("sources"), "manifest.sources"), "source_id", "manifest.sources")
    passages = _unique_records(_require_list(manifest.get("passages"), "manifest.passages"), "passage_id", "manifest.passages")

    for passage_id, passage in passages.items():
        source_id = _require_id(passage.get("source_id"), f"manifest passage {passage_id}.source_id")
        if source_id not in sources:
            _fail(f"manifest passage {passage_id} references unknown source {source_id}")
        if not _has_reconstructable_locator(passage):
            _fail(f"manifest passage {passage_id} lacks reconstructable locator/representation identity")
    return queries, sources, passages


def _validate_judgment(judgment: dict[str, Any], label: str) -> None:
    degree = judgment.get("relevance_degree")
    binary = judgment.get("binary_relevant")
    gain = judgment.get("gain")
    role = judgment.get("role")

    if degree not in _RELEVANCE_DEGREES:
        _fail(f"{label} has invalid relevance_degree")
    if role not in _ROLES:
        _fail(f"{label} has invalid role")

    if degree == "UNKNOWN":
        if binary is not None or gain is not None or role != "UNKNOWN":
            _fail(f"{label} UNKNOWN judgment must have null binary/gain and UNKNOWN role")
        return

    if role == "UNKNOWN":
        _fail(f"{label} resolved judgment cannot have UNKNOWN role")
    if not isinstance(binary, bool):
        _fail(f"{label} resolved judgment must have boolean binary_relevant")
    if not _is_int(gain) or gain < 0:
        _fail(f"{label} resolved judgment must have non-negative integer gain")
    if binary and gain <= 0:
        _fail(f"{label} binary_relevant=true requires positive gain")
    if not binary and gain != 0:
        _fail(f"{label} binary_relevant=false requires gain 0")


def _validate_gold(
    gold: dict[str, Any], manifest_query_ids: set[str], manifest_passage_ids: set[str]
) -> tuple[str, bool, dict[str, dict[str, Any]]]:
    qrels_mode = gold.get("qrels_mode")
    if qrels_mode not in _QRELS_MODES:
        _fail("gold.qrels_mode is invalid")
    ndcg_eligible = gold.get("ndcg_eligible")
    if not isinstance(ndcg_eligible, bool):
        _fail("gold.ndcg_eligible must be boolean")

    query_records = _unique_records(_require_list(gold.get("queries"), "gold.queries"), "query_id", "gold.queries")
    if set(query_records) != manifest_query_ids:
        _fail("gold query-ID set does not exactly match manifest")

    global_group_ids: set[str] = set()
    for query_id, query in query_records.items():
        judgments = _unique_records(
            _require_list(query.get("judgments"), f"gold query {query_id}.judgments"),
            "passage_id",
            f"gold query {query_id}.judgments",
        )
        for passage_id, judgment in judgments.items():
            if passage_id not in manifest_passage_ids:
                _fail(f"gold query {query_id} judgment references unknown passage {passage_id}")
            _validate_judgment(judgment, f"gold query {query_id} judgment {passage_id}")

        groups = _require_list(query.get("groups"), f"gold query {query_id}.groups")
        local_group_ids: set[str] = set()
        for i, raw_group in enumerate(groups):
            group = _require_object(raw_group, f"gold query {query_id}.groups[{i}]")
            group_id = _require_id(group.get("group_id"), f"gold query {query_id}.groups[{i}].group_id")
            if group_id in local_group_ids or group_id in global_group_ids:
                _fail(f"duplicate group_id: {group_id}")
            local_group_ids.add(group_id)
            global_group_ids.add(group_id)
            if group.get("group_kind") not in _GROUP_KINDS:
                _fail(f"group {group_id} has invalid group_kind")
            members = _require_list(group.get("passage_ids"), f"group {group_id}.passage_ids")
            if not members:
                _fail(f"group {group_id} must be non-empty")
            seen_members: set[str] = set()
            for j, member_raw in enumerate(members):
                member = _require_id(member_raw, f"group {group_id}.passage_ids[{j}]")
                if member in seen_members:
                    _fail(f"group {group_id} contains duplicate passage {member}")
                seen_members.add(member)
                if member not in manifest_passage_ids:
                    _fail(f"group {group_id} references unknown passage {member}")
    return qrels_mode, ndcg_eligible, query_records


def _validate_run(
    run: dict[str, Any], manifest_query_ids: set[str], manifest_passage_ids: set[str]
) -> tuple[int, dict[str, dict[str, Any]]]:
    k = run.get("k")
    if not _is_int(k) or k <= 0:
        _fail("run.k must be a positive integer")

    query_records = _unique_records(_require_list(run.get("queries"), "run.queries"), "query_id", "run.queries")
    if set(query_records) != manifest_query_ids:
        _fail("run query-ID set does not exactly match manifest")

    for query_id, query in query_records.items():
        hits = _require_list(query.get("hits"), f"run query {query_id}.hits")
        if len(hits) > k:
            _fail(f"run query {query_id} returns more than K hits")
        seen_passages: set[str] = set()
        ranks: list[int] = []
        for i, raw_hit in enumerate(hits):
            hit = _require_object(raw_hit, f"run query {query_id}.hits[{i}]")
            rank = hit.get("rank")
            if not _is_int(rank):
                _fail(f"run query {query_id} has non-integer rank")
            ranks.append(rank)
            passage_id = _require_id(hit.get("passage_id"), f"run query {query_id}.hits[{i}].passage_id")
            if passage_id in seen_passages:
                _fail(f"run query {query_id} has duplicate hit passage {passage_id}")
            seen_passages.add(passage_id)
            if passage_id not in manifest_passage_ids:
                _fail(f"run query {query_id} references unknown passage {passage_id}")
        if ranks != list(range(1, len(hits) + 1)):
            _fail(f"run query {query_id} ranks must be contiguous 1..N in ranked order")
    return k, query_records


def _gain_at_rank(gain: int, rank: int) -> float:
    return (2**gain - 1) / math.log2(rank + 1)


def _average_defined(values: list[float | int | None]) -> float | None:
    defined = [float(value) for value in values if value is not None]
    return sum(defined) / len(defined) if defined else None


def evaluate(manifest: dict[str, Any], gold: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    """Validate and score one frozen external-corpus run under contract v0.3."""
    manifest = _require_object(manifest, "manifest")
    gold = _require_object(gold, "gold")
    run = _require_object(run, "run")

    _validate_identities(manifest, gold, run)
    manifest_queries, _sources, manifest_passages = _validate_manifest(manifest)
    manifest_query_ids = set(manifest_queries)
    manifest_passage_ids = set(manifest_passages)
    qrels_mode, ndcg_eligible, gold_queries = _validate_gold(gold, manifest_query_ids, manifest_passage_ids)
    k, run_queries = _validate_run(run, manifest_query_ids, manifest_passage_ids)

    per_query: dict[str, dict[str, Any]] = {}
    for query_id in sorted(manifest_query_ids):
        gold_query = gold_queries[query_id]
        run_query = run_queries[query_id]
        judgments = {j["passage_id"]: j for j in gold_query["judgments"]}
        hits = run_query["hits"]
        retrieved = [hit["passage_id"] for hit in hits]
        retrieved_set = set(retrieved)

        positives = [j for j in judgments.values() if j["binary_relevant"] is True]
        support_positives = [j for j in positives if j["role"] == "SUPPORT"]
        counter_positives = [j for j in positives if j["role"] == "COUNTEREVIDENCE"]

        hit_at_k: int | None = None if not positives else int(any(j["passage_id"] in retrieved_set for j in positives))
        evidence_recall: float | None = None
        if support_positives:
            evidence_recall = sum(j["passage_id"] in retrieved_set for j in support_positives) / len(support_positives)
        counter_recall: float | None = None
        if counter_positives:
            counter_recall = sum(j["passage_id"] in retrieved_set for j in counter_positives) / len(counter_positives)

        unresolved = any(j["relevance_degree"] == "UNKNOWN" for j in judgments.values())
        positive_gain_levels = {j["gain"] for j in judgments.values() if _is_int(j["gain"]) and j["gain"] > 0}
        ndcg: float | None = None
        if ndcg_eligible and qrels_mode == "complete_relevant_set" and not unresolved and len(positive_gain_levels) >= 2:
            dcg = 0.0
            for hit in hits:
                judgment = judgments.get(hit["passage_id"])
                gain = judgment["gain"] if judgment is not None and _is_int(judgment["gain"]) else 0
                dcg += _gain_at_rank(gain, hit["rank"])
            ideal_gains = sorted(
                (j["gain"] for j in judgments.values() if _is_int(j["gain"]) and j["gain"] > 0),
                reverse=True,
            )[:k]
            idcg = sum(_gain_at_rank(gain, rank) for rank, gain in enumerate(ideal_gains, start=1))
            ndcg = dcg / idcg

        groups = gold_query["groups"]
        group_coverage: float | None = None
        if groups:
            satisfied = 0
            for group in groups:
                members = set(group["passage_ids"])
                if group["group_kind"] == "JOINTLY_REQUIRED":
                    covered = members <= retrieved_set
                else:
                    covered = bool(members & retrieved_set)
                satisfied += int(covered)
            group_coverage = satisfied / len(groups)

        if hits:
            judgment_coverage = sum(passage_id in judgments for passage_id in retrieved) / len(hits)
            resolved_coverage = sum(
                passage_id in judgments and judgments[passage_id]["binary_relevant"] is not None
                for passage_id in retrieved
            ) / len(hits)
        else:
            judgment_coverage = 1.0
            resolved_coverage = 1.0

        per_query[query_id] = {
            "hit@K": hit_at_k,
            "evidence_recall@K": evidence_recall,
            "counterevidence_recall@K": counter_recall,
            "nDCG@K": ndcg,
            "joint_group_coverage@K": group_coverage,
            "judgment_coverage@K": judgment_coverage,
            "resolved_judgment_coverage@K": resolved_coverage,
        }

    metric_names = (
        "hit@K",
        "evidence_recall@K",
        "counterevidence_recall@K",
        "nDCG@K",
        "joint_group_coverage@K",
        "judgment_coverage@K",
        "resolved_judgment_coverage@K",
    )
    aggregate = {
        metric: _average_defined([per_query[query_id][metric] for query_id in sorted(per_query)])
        for metric in metric_names
    }
    return {
        "k": k,
        "qrels_mode": qrels_mode,
        "metric_interpretation": "lower_bound" if qrels_mode == "partial" else "complete_relevant_set",
        "per_query": per_query,
        "aggregate": aggregate,
    }


def _canonicalize(value: Any, parent_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {key: _canonicalize(value[key], key) for key in sorted(value)}
    if isinstance(value, list):
        items = [_canonicalize(item, None) for item in value]
        if parent_key == "queries":
            return sorted(items, key=lambda item: item["query_id"])
        if parent_key == "judgments":
            return sorted(items, key=lambda item: item["passage_id"])
        if parent_key == "groups":
            return sorted(items, key=lambda item: item["group_id"])
        if parent_key == "passage_ids":
            return sorted(items)
        return items
    return value


def canonical_json_bytes(gold: dict[str, Any]) -> bytes:
    """Return canonical-json-v1 bytes for hidden-gold commitment."""
    canonical = _canonicalize(copy.deepcopy(_require_object(gold, "gold")))
    return json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def gold_commitment(gold: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(gold)).hexdigest()


def verify_gold_commitment(gold: dict[str, Any], expected_sha256: str) -> bool:
    if not isinstance(expected_sha256, str):
        return False
    return gold_commitment(gold) == expected_sha256.lower()
