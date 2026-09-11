"""Independent external-corpus retrieval evaluator for contract v0.4-draft.

This module was implemented from the written contract and permitted dummy fixtures only.
It intentionally has no dependency on other Evidence Bundler evaluator code.
"""

from __future__ import annotations

import copy
import hashlib
import hmac
import json
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


IDENTITY_KEYS = ("corpus_version", "corpus_sha256", "benchmark_sha256")
RELEVANCE_DEGREES = {"DECISIVE", "PARTIAL", "TOPICAL", "IRRELEVANT", "UNKNOWN"}
ROLES = {"SUPPORT", "COUNTEREVIDENCE", "NEUTRAL_OR_NOT_APPLICABLE", "UNKNOWN"}
GROUP_KINDS = {"JOINTLY_REQUIRED", "ALTERNATIVE_SUFFICIENT"}
QRELS_MODES = {"complete_relevant_set", "partial"}
METRIC_NAMES = (
    "hit_at_k",
    "evidence_recall_at_k",
    "counterevidence_recall_at_k",
    "ndcg_at_k",
    "joint_group_coverage_at_k",
    "judgment_coverage_at_k",
    "resolved_judgment_coverage_at_k",
)
RESULT_KEYS = (
    "status",
    "k",
    "qrels_mode",
    "metric_interpretation",
    "ndcg_eligible",
    "ndcg_eligible_by_query",
    "aggregate",
    "per_query",
)


class EvaluationError(ValueError):
    """Raised when an input artifact violates the evaluator contract."""


def _fail(message: str) -> None:
    raise EvaluationError(message)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> List[Any]:
    if not isinstance(value, list):
        _fail(f"{label} must be an array")
    return value


def _require_nonempty_id(value: Any, label: str) -> str:
    if not _is_nonempty_string(value):
        _fail(f"{label} must be a non-empty string")
    return value


def _validate_required_identities(
    manifest: Mapping[str, Any], gold: Mapping[str, Any], run: Mapping[str, Any]
) -> None:
    artifacts = (("manifest", manifest), ("hidden gold", gold), ("ranked run", run))
    for key in IDENTITY_KEYS:
        values: List[str] = []
        for label, artifact in artifacts:
            if key not in artifact:
                _fail(f"{label} missing required identity {key}")
            value = artifact[key]
            if not _is_nonempty_string(value):
                _fail(f"{label} identity {key} must be a non-empty string")
            values.append(value)
        if values[0] != values[1] or values[0] != values[2]:
            _fail(f"required identity mismatch for {key}")


def _unique_records(
    records: Sequence[Any], key: str, label: str
) -> Dict[str, Mapping[str, Any]]:
    result: Dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(records):
        record = _require_mapping(raw, f"{label}[{index}]")
        record_id = _require_nonempty_id(record.get(key), f"{label}[{index}].{key}")
        if record_id in result:
            _fail(f"duplicate {key}: {record_id}")
        result[record_id] = record
    return result


def _validate_manifest(manifest: Mapping[str, Any]) -> Tuple[Dict[str, Mapping[str, Any]], Dict[str, Mapping[str, Any]], Dict[str, Mapping[str, Any]]]:
    queries = _unique_records(_require_list(manifest.get("queries"), "manifest.queries"), "query_id", "manifest.queries")
    sources = _unique_records(_require_list(manifest.get("sources"), "manifest.sources"), "source_id", "manifest.sources")
    passages = _unique_records(_require_list(manifest.get("passages"), "manifest.passages"), "passage_id", "manifest.passages")

    for passage_id, passage in passages.items():
        source_id = _require_nonempty_id(passage.get("source_id"), f"passage {passage_id}.source_id")
        if source_id not in sources:
            _fail(f"passage {passage_id} references unknown source_id {source_id}")
        locator_ok = _is_nonempty_string(passage.get("locator"))
        representation_ok = _is_nonempty_string(passage.get("representation_identity"))
        if not (locator_ok or representation_ok):
            _fail(
                f"passage {passage_id} requires non-empty locator or representation_identity"
            )
    return queries, sources, passages


def _validate_gold(
    gold: Mapping[str, Any],
    manifest_queries: Mapping[str, Mapping[str, Any]],
    manifest_passages: Mapping[str, Mapping[str, Any]],
) -> Tuple[str, bool, Dict[str, Dict[str, Any]]]:
    qrels_mode = gold.get("qrels_mode")
    if qrels_mode not in QRELS_MODES:
        _fail("hidden gold qrels_mode is invalid")
    ndcg_flag = gold.get("ndcg_eligible")
    if not isinstance(ndcg_flag, bool):
        _fail("hidden gold ndcg_eligible must be boolean")

    raw_queries = _require_list(gold.get("queries"), "hidden gold.queries")
    gold_queries = _unique_records(raw_queries, "query_id", "hidden gold.queries")
    if set(gold_queries) != set(manifest_queries):
        _fail("hidden gold query-ID set must exactly match manifest")

    validated: Dict[str, Dict[str, Any]] = {}
    for query_id, query in gold_queries.items():
        if "judgments" not in query:
            _fail(f"gold query {query_id} missing judgments")
        if "groups" not in query:
            _fail(f"gold query {query_id} missing groups")
        raw_judgments = _require_list(query["judgments"], f"gold query {query_id}.judgments")
        raw_groups = _require_list(query["groups"], f"gold query {query_id}.groups")

        judgments: Dict[str, Mapping[str, Any]] = {}
        for index, raw_judgment in enumerate(raw_judgments):
            judgment = _require_mapping(raw_judgment, f"gold query {query_id}.judgments[{index}]")
            passage_id = _require_nonempty_id(
                judgment.get("passage_id"), f"gold query {query_id}.judgments[{index}].passage_id"
            )
            if passage_id in judgments:
                _fail(f"duplicate judgment passage_id {passage_id} in query {query_id}")
            if passage_id not in manifest_passages:
                _fail(f"gold judgment references unknown passage_id {passage_id}")

            degree = judgment.get("relevance_degree")
            if degree not in RELEVANCE_DEGREES:
                _fail(f"invalid relevance_degree in query {query_id} passage {passage_id}")
            role = judgment.get("role")
            if role not in ROLES:
                _fail(f"invalid role in query {query_id} passage {passage_id}")
            binary = judgment.get("binary_relevant")
            gain = judgment.get("gain")

            if degree == "UNKNOWN":
                if binary is not None or gain is not None or role != "UNKNOWN":
                    _fail(
                        f"UNKNOWN judgment must have null binary_relevant/gain and role UNKNOWN: {query_id}/{passage_id}"
                    )
            else:
                if not isinstance(binary, bool):
                    _fail(f"resolved judgment binary_relevant must be boolean: {query_id}/{passage_id}")
                if not _is_int(gain) or gain < 0:
                    _fail(f"resolved judgment gain must be non-negative integer: {query_id}/{passage_id}")
                if binary and gain <= 0:
                    _fail(f"binary_relevant=true requires positive gain: {query_id}/{passage_id}")
                if not binary and gain != 0:
                    _fail(f"binary_relevant=false requires gain 0: {query_id}/{passage_id}")
            judgments[passage_id] = judgment

        groups: Dict[str, Mapping[str, Any]] = {}
        for index, raw_group in enumerate(raw_groups):
            group = _require_mapping(raw_group, f"gold query {query_id}.groups[{index}]")
            group_id = _require_nonempty_id(group.get("group_id"), f"gold query {query_id}.groups[{index}].group_id")
            if group_id in groups:
                _fail(f"duplicate group_id {group_id} within query {query_id}")
            kind = group.get("group_kind")
            if kind not in GROUP_KINDS:
                _fail(f"invalid group_kind for {query_id}/{group_id}")
            passage_ids = _require_list(group.get("passage_ids"), f"gold query {query_id}.group {group_id}.passage_ids")
            if not passage_ids:
                _fail(f"group {query_id}/{group_id} passage_ids must be non-empty")
            seen_members: Set[str] = set()
            for member in passage_ids:
                member_id = _require_nonempty_id(member, f"gold query {query_id}.group {group_id} member")
                if member_id in seen_members:
                    _fail(f"duplicate group member {member_id} in {query_id}/{group_id}")
                if member_id not in manifest_passages:
                    _fail(f"group {query_id}/{group_id} references unknown passage_id {member_id}")
                seen_members.add(member_id)
            groups[group_id] = group

        validated[query_id] = {"judgments": judgments, "groups": groups}
    return qrels_mode, ndcg_flag, validated


def _validate_run(
    run: Mapping[str, Any],
    manifest_queries: Mapping[str, Mapping[str, Any]],
    manifest_passages: Mapping[str, Mapping[str, Any]],
) -> Tuple[int, Dict[str, List[Mapping[str, Any]]]]:
    k = run.get("k")
    if not _is_int(k) or k <= 0:
        _fail("ranked run k must be a positive integer")

    raw_queries = _require_list(run.get("queries"), "ranked run.queries")
    run_queries = _unique_records(raw_queries, "query_id", "ranked run.queries")
    if set(run_queries) != set(manifest_queries):
        _fail("ranked run query-ID set must exactly match manifest")

    validated: Dict[str, List[Mapping[str, Any]]] = {}
    for query_id, query in run_queries.items():
        hits = _require_list(query.get("hits"), f"ranked run query {query_id}.hits")
        if len(hits) > k:
            _fail(f"ranked run query {query_id} has more than K hits")

        by_rank: Dict[int, Mapping[str, Any]] = {}
        seen_passages: Set[str] = set()
        for index, raw_hit in enumerate(hits):
            hit = _require_mapping(raw_hit, f"ranked run query {query_id}.hits[{index}]")
            rank = hit.get("rank")
            if not _is_int(rank):
                _fail(f"rank must be an integer in query {query_id}")
            if rank in by_rank:
                _fail(f"duplicate rank {rank} in query {query_id}")
            passage_id = _require_nonempty_id(hit.get("passage_id"), f"ranked hit passage_id in query {query_id}")
            if passage_id in seen_passages:
                _fail(f"duplicate ranked passage_id {passage_id} in query {query_id}")
            if passage_id not in manifest_passages:
                _fail(f"ranked hit references unknown passage_id {passage_id}")
            by_rank[rank] = hit
            seen_passages.add(passage_id)

        expected = list(range(1, len(hits) + 1))
        if sorted(by_rank) != expected:
            _fail(f"ranks in query {query_id} must be exact contiguous integers 1..N")
        validated[query_id] = [by_rank[rank] for rank in expected]
    return k, validated


def _mean_defined(values: Iterable[Optional[float]]) -> Optional[float]:
    defined = [value for value in values if value is not None]
    if not defined:
        return None
    return sum(defined) / len(defined)


def _dcg(gains: Sequence[int]) -> float:
    return sum((2 ** gain - 1) / math.log2(rank + 1) for rank, gain in enumerate(gains, start=1))


def evaluate(manifest: Mapping[str, Any], hidden_gold: Mapping[str, Any], ranked_run: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate all artifacts and return the exact successful result object."""

    manifest = _require_mapping(manifest, "manifest")
    hidden_gold = _require_mapping(hidden_gold, "hidden gold")
    ranked_run = _require_mapping(ranked_run, "ranked run")

    _validate_required_identities(manifest, hidden_gold, ranked_run)
    manifest_queries, _, manifest_passages = _validate_manifest(manifest)
    qrels_mode, top_ndcg_flag, gold_queries = _validate_gold(
        hidden_gold, manifest_queries, manifest_passages
    )
    k, run_queries = _validate_run(ranked_run, manifest_queries, manifest_passages)

    per_query: Dict[str, Dict[str, Optional[float]]] = {}
    eligible_by_query: Dict[str, bool] = {}

    for query_id in sorted(manifest_queries):
        judgments: Dict[str, Mapping[str, Any]] = gold_queries[query_id]["judgments"]
        groups: Dict[str, Mapping[str, Any]] = gold_queries[query_id]["groups"]
        hits = run_queries[query_id]
        retrieved = [hit["passage_id"] for hit in hits]
        retrieved_set = set(retrieved)

        positive = {pid for pid, row in judgments.items() if row.get("binary_relevant") is True}
        support = {
            pid
            for pid, row in judgments.items()
            if row.get("binary_relevant") is True and row.get("role") == "SUPPORT"
        }
        counter = {
            pid
            for pid, row in judgments.items()
            if row.get("binary_relevant") is True and row.get("role") == "COUNTEREVIDENCE"
        }

        hit_at_k: Optional[float] = None if not positive else int(bool(retrieved_set & positive))
        evidence_recall: Optional[float] = None if not support else len(retrieved_set & support) / len(support)
        counter_recall: Optional[float] = None if not counter else len(retrieved_set & counter) / len(counter)

        has_unknown = any(row.get("relevance_degree") == "UNKNOWN" for row in judgments.values())
        positive_gain_levels = {row["gain"] for row in judgments.values() if row.get("gain") is not None and row["gain"] > 0}
        ndcg_eligible = bool(
            top_ndcg_flag
            and qrels_mode == "complete_relevant_set"
            and not has_unknown
            and len(positive_gain_levels) >= 2
        )
        eligible_by_query[query_id] = ndcg_eligible

        ndcg: Optional[float]
        if ndcg_eligible:
            observed_gains = []
            for passage_id in retrieved:
                row = judgments.get(passage_id)
                gain = row.get("gain") if row is not None else 0
                observed_gains.append(gain if gain is not None else 0)
            ideal_gains = sorted(
                (row["gain"] for row in judgments.values() if row.get("gain") is not None),
                reverse=True,
            )[:k]
            ideal = _dcg(ideal_gains)
            ndcg = _dcg(observed_gains) / ideal
        else:
            ndcg = None

        group_coverage: Optional[float]
        if not groups:
            group_coverage = None
        else:
            satisfied = 0
            for group in groups.values():
                members = set(group["passage_ids"])
                if group["group_kind"] == "JOINTLY_REQUIRED":
                    covered = members.issubset(retrieved_set)
                else:
                    covered = bool(members & retrieved_set)
                satisfied += int(covered)
            group_coverage = satisfied / len(groups)

        if not retrieved:
            judgment_coverage = 1.0
            resolved_coverage = 1.0
        else:
            judgment_coverage = sum(1 for pid in retrieved if pid in judgments) / len(retrieved)
            resolved_coverage = sum(
                1
                for pid in retrieved
                if pid in judgments and judgments[pid].get("binary_relevant") is not None
            ) / len(retrieved)

        per_query[query_id] = {
            "hit_at_k": hit_at_k,
            "evidence_recall_at_k": evidence_recall,
            "counterevidence_recall_at_k": counter_recall,
            "ndcg_at_k": ndcg,
            "joint_group_coverage_at_k": group_coverage,
            "judgment_coverage_at_k": judgment_coverage,
            "resolved_judgment_coverage_at_k": resolved_coverage,
        }

    aggregate = {
        name: _mean_defined(per_query[qid][name] for qid in sorted(per_query))
        for name in METRIC_NAMES
    }

    result = {
        "status": "ok",
        "k": k,
        "qrels_mode": qrels_mode,
        "metric_interpretation": "point_estimate" if qrels_mode == "complete_relevant_set" else "lower_bound",
        "ndcg_eligible": any(eligible_by_query.values()),
        "ndcg_eligible_by_query": eligible_by_query,
        "aggregate": aggregate,
        "per_query": per_query,
    }
    return result


def _canonicalize_gold(value: Any, context: Optional[str] = None) -> Any:
    if isinstance(value, Mapping):
        obj = {key: _canonicalize_gold(subvalue, key) for key, subvalue in value.items()}
        if "queries" in obj and isinstance(obj["queries"], list):
            obj["queries"] = sorted(obj["queries"], key=lambda row: row["query_id"])
        if "judgments" in obj and isinstance(obj["judgments"], list):
            obj["judgments"] = sorted(obj["judgments"], key=lambda row: row["passage_id"])
        if "groups" in obj and isinstance(obj["groups"], list):
            obj["groups"] = sorted(obj["groups"], key=lambda row: row["group_id"])
        if "passage_ids" in obj and isinstance(obj["passage_ids"], list):
            obj["passage_ids"] = sorted(obj["passage_ids"])
        return obj
    if isinstance(value, list):
        return [_canonicalize_gold(item, context) for item in value]
    return value


def canonical_hidden_gold_bytes(hidden_gold: Mapping[str, Any]) -> bytes:
    """Return canonical-json-v1 bytes for a hidden-gold object."""

    hidden_gold = _require_mapping(hidden_gold, "hidden gold")
    canonical = _canonicalize_gold(copy.deepcopy(hidden_gold))
    text = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text.encode("utf-8")


def hidden_gold_sha256(hidden_gold: Mapping[str, Any]) -> str:
    """Return SHA-256 hex commitment over canonical-json-v1 bytes."""

    return hashlib.sha256(canonical_hidden_gold_bytes(hidden_gold)).hexdigest()


def verify_hidden_gold_commitment(hidden_gold: Mapping[str, Any], expected_sha256: str) -> bool:
    """Verify a canonical hidden-gold SHA-256 commitment."""

    if not isinstance(expected_sha256, str):
        return False
    return hmac.compare_digest(hidden_gold_sha256(hidden_gold), expected_sha256.lower())
