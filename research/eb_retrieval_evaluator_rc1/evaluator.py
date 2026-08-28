from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0"
EXPECTED_CORPUS_TREE_SHA256 = "eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8"
PARAGRAPH_TRANSFORM_ID = "transform-paragraph-order-permutation-v1"

THRESHOLDS = {
    "case_hit_at_k": 0.95,
    "decisive_annotation_recall_at_k": 0.90,
    "counterevidence_recall_at_k": 0.90,
    "qualifier_exception_recall_at_k": 0.90,
    "complete_joint_group_coverage_at_k": 0.90,
    "family_case_hit_at_k": 0.75,
    "family_decisive_annotation_recall_at_k": 0.70,
}

COUNTEREVIDENCE_CLASSES = {
    "decisive_counterevidence",
    "decisive_refutation",
    "decisive_contradiction",
}
QUALIFIER_EXCEPTION_CLASSES = {
    "decisive_qualifier",
    "decisive_exception",
}
MATERIAL_CONTEXT_CLASSES = {
    "material_context",
    "decisive_material_context",
}


class EvaluatorError(RuntimeError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvaluatorError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise EvaluatorError(f"{path}:{line_number}: row must be object")
            rows.append(value)
    return rows


def load_cases(root: Path) -> dict[str, dict[str, Any]]:
    case_rows = load_jsonl(root / "cases" / "dev_cases.jsonl") + load_jsonl(
        root / "cases" / "test_cases.jsonl"
    )
    cases: dict[str, dict[str, Any]] = {}
    for row in case_rows:
        case_id = row["case_id"]
        if case_id in cases:
            raise EvaluatorError(f"duplicate case_id: {case_id}")
        cases[case_id] = row
    return cases


def load_gold(root: Path) -> dict[str, list[dict[str, Any]]]:
    rows = load_jsonl(root / "gold" / "dev_relevance.jsonl") + load_jsonl(
        root / "gold" / "test_relevance.jsonl"
    )
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["case_id"]].append(row)
    return dict(grouped)


def load_subsets(root: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(root / "aperture" / "subsets.json")
    return {row["subset_id"]: row for row in payload["subsets"]}


def load_passages(
    root: Path,
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    by_identity: dict[tuple[str, str], dict[str, Any]] = {}
    by_source: dict[str, list[dict[str, Any]]] = {}
    sources_root = root / "sources"
    for source_dir in sorted(p for p in sources_root.iterdir() if p.is_dir()):
        source_id = source_dir.name
        metadata = load_json(source_dir / "metadata.json")
        content_bytes = (source_dir / "content.txt").read_bytes()
        rows: list[dict[str, Any]] = []
        for passage in metadata["passages"]:
            start = int(passage["start_offset"])
            end = int(passage["end_offset"])
            text = content_bytes[start:end].decode("utf-8")
            row = {
                "source_id": source_id,
                "passage_id": passage["passage_id"],
                "start_offset": start,
                "end_offset": end,
                "offset_unit": passage["offset_unit"],
                "paragraph_index": int(passage["paragraph_index"]),
                "text": text,
            }
            identity = (source_id, passage["passage_id"])
            if identity in by_identity:
                raise EvaluatorError(f"duplicate passage identity: {identity}")
            by_identity[identity] = row
            rows.append(row)
        by_source[source_id] = rows
    return by_identity, by_source


def load_anchor_reverse_mapping(root: Path) -> dict[tuple[str, int, int, str], str]:
    path = (
        root
        / "transforms"
        / "views"
        / PARAGRAPH_TRANSFORM_ID
        / "semantic_anchor_mapping.json"
    )
    payload = load_json(path)
    reverse: dict[tuple[str, int, int, str], str] = {}
    for source_id, passages in payload.items():
        for canonical_passage_id, mapping in passages.items():
            key = (
                source_id,
                int(mapping["new_start_offset"]),
                int(mapping["new_end_offset"]),
                "utf8_byte",
            )
            if key in reverse:
                raise EvaluatorError(f"duplicate transformed anchor: {key}")
            reverse[key] = canonical_passage_id
    return reverse


def verify_freeze_receipt(root: Path) -> dict[str, Any]:
    receipt = load_json(root / "validation" / "freeze_receipt.json")
    observed = receipt.get("overall_corpus_tree_sha256")
    if observed != EXPECTED_CORPUS_TREE_SHA256:
        raise EvaluatorError(
            "frozen corpus hash mismatch: "
            f"expected {EXPECTED_CORPUS_TREE_SHA256}, observed {observed}"
        )
    return receipt


def validate_gold_interpretation(
    cases: dict[str, dict[str, Any]],
    gold: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    errors: list[str] = []
    for case_id, case in cases.items():
        rows = gold.get(case_id, [])
        if not rows:
            errors.append(f"{case_id}: missing gold rows")
            continue
        decisive = [row for row in rows if row.get("decisive") is True]
        decisive_sources = sorted({row["source_id"] for row in decisive})
        decisive_passages = sorted({row["passage_id"] for row in decisive})
        for row in rows:
            summary_sources = sorted(set(row.get("gold_source_ids", [])))
            summary_passages = sorted(set(row.get("gold_passage_ids", [])))
            if summary_sources != decisive_sources:
                errors.append(
                    f"{case_id}/{row.get('annotation_id')}: gold_source_ids "
                    f"{summary_sources} != decisive row sources {decisive_sources}"
                )
            if summary_passages != decisive_passages:
                errors.append(
                    f"{case_id}/{row.get('annotation_id')}: gold_passage_ids "
                    f"{summary_passages} != decisive row passages {decisive_passages}"
                )
            if row.get("accessible_subset_id") != case.get("accessible_subset_id"):
                errors.append(
                    f"{case_id}/{row.get('annotation_id')}: accessible subset disagreement"
                )
    extra_cases = sorted(set(gold) - set(cases))
    if extra_cases:
        errors.append(f"gold contains unknown cases: {extra_cases}")
    if errors:
        raise EvaluatorError("gold interpretation validation failed:\n" + "\n".join(errors[:50]))
    return {
        "status": "PASS",
        "cases_checked": len(cases),
        "gold_cases_checked": len(gold),
        "interpretation": (
            "row-level decisive annotations authoritative; case-level gold_* integrity-only"
        ),
    }


def _validate_hit_shape(hit: dict[str, Any], expected_rank: int) -> list[str]:
    errors: list[str] = []
    if hit.get("rank") != expected_rank:
        errors.append(f"rank {hit.get('rank')} != ordered position {expected_rank}")
    if not isinstance(hit.get("source_id"), str) or not hit.get("source_id"):
        errors.append("missing source_id")
    passage_id = hit.get("passage_id")
    anchor = hit.get("anchor")
    if not passage_id and not isinstance(anchor, dict):
        errors.append("hit requires passage_id or anchor")
    if passage_id is not None and (not isinstance(passage_id, str) or not passage_id):
        errors.append("passage_id must be non-empty string or null")
    if anchor is not None:
        if not isinstance(anchor, dict):
            errors.append("anchor must be object or null")
        else:
            for key in ("start_offset", "end_offset", "offset_unit"):
                if key not in anchor:
                    errors.append(f"anchor missing {key}")
    return errors


def validate_result_shape(
    result: dict[str, Any],
    case: dict[str, Any],
    known_subset_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 1.0")
    if result.get("case_id") != case["case_id"]:
        errors.append("case_id mismatch")
    hits = result.get("hits")
    if not isinstance(hits, list):
        errors.append("hits must be array")
        hits = []
    for index, hit in enumerate(hits, 1):
        if not isinstance(hit, dict):
            errors.append(f"hit {index} is not an object")
            continue
        errors.extend(f"hit {index}: {message}" for message in _validate_hit_shape(hit, index))
    scope = result.get("search_scope")
    if not isinstance(scope, dict):
        errors.append("search_scope must be object")
    else:
        actual_subset = scope.get("actual_searchable_subset_id")
        if actual_subset not in known_subset_ids:
            errors.append(f"unknown actual_searchable_subset_id: {actual_subset}")
        observed_scope = scope.get("observed_scope")
        if not isinstance(observed_scope, dict):
            errors.append("observed_scope must be object")
        elif observed_scope.get("subset_id") != actual_subset:
            errors.append("observed_scope.subset_id must equal actual_searchable_subset_id")
    claim = result.get("completeness_claim")
    if not isinstance(claim, dict) or claim.get("status") not in {
        "unknown",
        "not_established",
        "bounded_only",
        "full_corpus",
        "comprehensive",
    }:
        errors.append("invalid completeness_claim.status")
    run_identity = result.get("run_identity")
    if not isinstance(run_identity, dict):
        errors.append("run_identity must be object")
    else:
        for key in ("retriever_id", "configuration_id", "run_id"):
            if not isinstance(run_identity.get(key), str) or not run_identity.get(key):
                errors.append(f"run_identity.{key} missing")
    return errors


def canonical_hit_identity(
    hit: dict[str, Any],
    passage_index: dict[tuple[str, str], dict[str, Any]],
    anchor_reverse: dict[tuple[str, int, int, str], str],
) -> tuple[str, str] | None:
    source_id = hit.get("source_id")
    passage_id = hit.get("passage_id")
    if isinstance(source_id, str) and isinstance(passage_id, str) and passage_id:
        if (source_id, passage_id) in passage_index:
            return (source_id, passage_id)
        return None
    anchor = hit.get("anchor")
    if not isinstance(source_id, str) or not isinstance(anchor, dict):
        return None
    try:
        start = int(anchor["start_offset"])
        end = int(anchor["end_offset"])
        unit = str(anchor["offset_unit"])
    except (KeyError, TypeError, ValueError):
        return None
    transform_id = anchor.get("transform_id")
    if transform_id is not None:
        if transform_id != PARAGRAPH_TRANSFORM_ID:
            return None
        mapped = anchor_reverse.get((source_id, start, end, unit))
        if mapped is None:
            return None
        return (source_id, mapped) if (source_id, mapped) in passage_index else None
    for (candidate_source, candidate_passage), row in passage_index.items():
        if candidate_source != source_id:
            continue
        if (
            row["start_offset"] == start
            and row["end_offset"] == end
            and row["offset_unit"] == unit
        ):
            return (source_id, candidate_passage)
    return None


def _annotation_identity(row: dict[str, Any]) -> tuple[str, str]:
    return (row["source_id"], row["passage_id"])


def _is_counterevidence(row: dict[str, Any]) -> bool:
    value = str(row.get("relevance_class", ""))
    return value in COUNTEREVIDENCE_CLASSES or any(
        token in value for token in ("counterevidence", "refutation", "contradiction")
    )


def _is_qualifier_exception(row: dict[str, Any]) -> bool:
    value = str(row.get("relevance_class", ""))
    return value in QUALIFIER_EXCEPTION_CLASSES or any(
        token in value for token in ("qualifier", "exception")
    )


def _is_material_context(row: dict[str, Any]) -> bool:
    value = str(row.get("relevance_class", ""))
    return value in MATERIAL_CONTEXT_CLASSES or "material_context" in value


def ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def _scope_record(subset: dict[str, Any]) -> dict[str, Any]:
    ids = list(subset["source_ids"])
    return {
        "subset_id": subset["subset_id"],
        "source_count": len(ids),
        "source_ids_sha256": sha256_json(sorted(ids)),
    }


def evaluate_case(
    case: dict[str, Any],
    rows: list[dict[str, Any]],
    result: dict[str, Any],
    subsets: dict[str, dict[str, Any]],
    passage_index: dict[tuple[str, str], dict[str, Any]],
    anchor_reverse: dict[tuple[str, int, int, str], str],
) -> dict[str, Any]:
    shape_errors = validate_result_shape(result, case, set(subsets))
    k = int(case["runtime_config"]["maximum_passages"])
    hits = result.get("hits") if isinstance(result.get("hits"), list) else []
    bounded_hits = hits[:k]
    actual_subset = result.get("search_scope", {}).get("actual_searchable_subset_id")
    subset_source_ids = set(subsets.get(actual_subset, {}).get("source_ids", []))

    canonical_hits: list[tuple[str, str] | None] = []
    provenance_invalid = 0
    out_of_scope = 0
    for hit in hits:
        identity = (
            canonical_hit_identity(hit, passage_index, anchor_reverse)
            if isinstance(hit, dict)
            else None
        )
        canonical_hits.append(identity)
        if identity is None:
            provenance_invalid += 1
        elif identity[0] not in subset_source_ids:
            out_of_scope += 1

    bounded_identities = canonical_hits[:k]
    bounded_identity_set = {item for item in bounded_identities if item is not None}
    all_identity_set = {item for item in canonical_hits if item is not None}

    decisive_rows = [row for row in rows if row.get("decisive") is True]
    accessible_decisive = [
        row for row in decisive_rows if row.get("in_accessible_subset") is True
    ]
    accessible_decisive_ids = {_annotation_identity(row) for row in accessible_decisive}
    decisive_hits = accessible_decisive_ids & bounded_identity_set

    first_decisive_rank: int | None = None
    for rank, identity in enumerate(bounded_identities, 1):
        if identity in accessible_decisive_ids:
            first_decisive_rank = rank
            break

    hard_negative_ids = {
        _annotation_identity(row)
        for row in rows
        if row.get("relevance_class") == "hard_negative"
    }
    hard_negative_ranks = [
        rank
        for rank, identity in enumerate(bounded_identities, 1)
        if identity in hard_negative_ids
    ]
    hard_before_first = sum(
        1
        for rank in hard_negative_ranks
        if first_decisive_rank is None or rank < first_decisive_rank
    )

    counter_rows = [row for row in accessible_decisive if _is_counterevidence(row)]
    qual_rows = [row for row in accessible_decisive if _is_qualifier_exception(row)]
    material_rows = [row for row in accessible_decisive if _is_material_context(row)]

    joint_groups: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for row in accessible_decisive:
        if row.get("jointly_required") is True and row.get("joint_group_id"):
            joint_groups[str(row["joint_group_id"])].add(_annotation_identity(row))
    joint_complete = 0
    joint_partial = 0
    joint_none = 0
    joint_detail: dict[str, str] = {}
    for group_id, members in sorted(joint_groups.items()):
        matched = members & bounded_identity_set
        if matched == members and members:
            joint_complete += 1
            joint_detail[group_id] = "complete"
        elif matched:
            joint_partial += 1
            joint_detail[group_id] = "partial"
        else:
            joint_none += 1
            joint_detail[group_id] = "none"

    completeness_status = result.get("completeness_claim", {}).get("status")
    false_completeness = actual_subset != "full" and completeness_status in {
        "full_corpus",
        "comprehensive",
    }
    configured_scope_mismatch = actual_subset != case.get("accessible_subset_id")
    expected_scope = _scope_record(subsets[actual_subset]) if actual_subset in subsets else None
    observed_scope = result.get("search_scope", {}).get("observed_scope")
    scope_fact_mismatch = expected_scope is None or observed_scope != expected_scope

    counter_ids = {_annotation_identity(row) for row in counter_rows}
    qual_ids = {_annotation_identity(row) for row in qual_rows}
    material_ids = {_annotation_identity(row) for row in material_rows}

    return {
        "case_id": case["case_id"],
        "family": rows[0]["challenge_family"] if rows else "UNKNOWN",
        "family_name": rows[0].get("challenge_family_name") if rows else None,
        "maximum_passages": k,
        "returned_hit_count": len(hits),
        "bounded_hit_count": len(bounded_hits),
        "budget_violation": len(hits) > k,
        "shape_errors": shape_errors,
        "provenance_invalid_hit_count": provenance_invalid,
        "out_of_scope_hit_count": out_of_scope,
        "accessible_decisive_annotation_count": len(accessible_decisive_ids),
        "accessible_decisive_hit": bool(decisive_hits) if accessible_decisive_ids else None,
        "decisive_annotations_hit_count": len(decisive_hits),
        "decisive_annotation_recall_at_k": ratio(
            len(decisive_hits), len(accessible_decisive_ids)
        ),
        "unbounded_decisive_annotation_recall": ratio(
            len(accessible_decisive_ids & all_identity_set), len(accessible_decisive_ids)
        ),
        "first_decisive_rank": first_decisive_rank,
        "first_decisive_reciprocal_rank": (
            None if first_decisive_rank is None else 1.0 / first_decisive_rank
        ),
        "counterevidence_recall_at_k": ratio(
            len(counter_ids & bounded_identity_set), len(counter_ids)
        ),
        "qualifier_exception_recall_at_k": ratio(
            len(qual_ids & bounded_identity_set), len(qual_ids)
        ),
        "material_context_recall_at_k": ratio(
            len(material_ids & bounded_identity_set), len(material_ids)
        ),
        "joint_group_count": len(joint_groups),
        "joint_group_complete_count": joint_complete,
        "joint_group_partial_count": joint_partial,
        "joint_group_none_count": joint_none,
        "joint_group_detail": joint_detail,
        "hard_negative_before_first_decisive": hard_before_first,
        "hard_negative_count_at_k": sum(
            1 for identity in bounded_identities if identity in hard_negative_ids
        ),
        "hard_negative_proportion_at_k": ratio(
            sum(1 for identity in bounded_identities if identity in hard_negative_ids),
            len(bounded_hits),
        ),
        "actual_searchable_subset_id": actual_subset,
        "observed_scope": observed_scope,
        "completeness_claim": result.get("completeness_claim"),
        "false_completeness_claim": false_completeness,
        "configured_scope_mismatch": configured_scope_mismatch,
        "scope_fact_mismatch": scope_fact_mismatch,
    }


def _mean_applicable(values: Iterable[float | None]) -> float | None:
    usable = [float(value) for value in values if value is not None]
    return None if not usable else sum(usable) / len(usable)


def _aggregate_case_metrics(case_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    applicable_hit = [
        row for row in case_metrics if row["accessible_decisive_hit"] is not None
    ]
    decisive_num = sum(row["decisive_annotations_hit_count"] for row in case_metrics)
    decisive_den = sum(row["accessible_decisive_annotation_count"] for row in case_metrics)
    joint_den = sum(row["joint_group_count"] for row in case_metrics)
    joint_num = sum(row["joint_group_complete_count"] for row in case_metrics)
    first_ranks = sorted(
        row["first_decisive_rank"]
        for row in case_metrics
        if row["first_decisive_rank"] is not None
    )
    return {
        "case_count": len(case_metrics),
        "applicable_decisive_case_count": len(applicable_hit),
        "case_hit_at_k": ratio(
            sum(1 for row in applicable_hit if row["accessible_decisive_hit"]),
            len(applicable_hit),
        ),
        "decisive_annotation_recall_at_k": ratio(decisive_num, decisive_den),
        "counterevidence_recall_at_k": _mean_applicable(
            row["counterevidence_recall_at_k"] for row in case_metrics
        ),
        "qualifier_exception_recall_at_k": _mean_applicable(
            row["qualifier_exception_recall_at_k"] for row in case_metrics
        ),
        "material_context_recall_at_k": _mean_applicable(
            row["material_context_recall_at_k"] for row in case_metrics
        ),
        "complete_joint_group_coverage_at_k": ratio(joint_num, joint_den),
        "partial_joint_group_count": sum(
            row["joint_group_partial_count"] for row in case_metrics
        ),
        "first_decisive_mean_reciprocal_rank": _mean_applicable(
            row["first_decisive_reciprocal_rank"] for row in case_metrics
        ),
        "first_decisive_rank_distribution": first_ranks,
        "hard_negative_before_first_decisive_total": sum(
            row["hard_negative_before_first_decisive"] for row in case_metrics
        ),
        "hard_negative_proportion_at_k": ratio(
            sum(row["hard_negative_count_at_k"] for row in case_metrics),
            sum(row["bounded_hit_count"] for row in case_metrics),
        ),
        "budget_violation_count": sum(
            1 for row in case_metrics if row["budget_violation"]
        ),
        "shape_error_count": sum(len(row["shape_errors"]) for row in case_metrics),
        "provenance_invalid_hit_count": sum(
            row["provenance_invalid_hit_count"] for row in case_metrics
        ),
        "out_of_scope_hit_count": sum(
            row["out_of_scope_hit_count"] for row in case_metrics
        ),
        "false_completeness_claim_count": sum(
            1 for row in case_metrics if row["false_completeness_claim"]
        ),
        "configured_scope_mismatch_count": sum(
            1 for row in case_metrics if row["configured_scope_mismatch"]
        ),
        "scope_fact_mismatch_count": sum(
            1 for row in case_metrics if row["scope_fact_mismatch"]
        ),
    }


def qualify_summary(summary: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    overall = summary["overall"]
    if not summary.get("family_reporting_complete"):
        failures.append("critical:family_reporting_incomplete")
    for name in (
        "shape_error_count",
        "budget_violation_count",
        "provenance_invalid_hit_count",
        "false_completeness_claim_count",
        "out_of_scope_hit_count",
        "configured_scope_mismatch_count",
        "scope_fact_mismatch_count",
    ):
        if overall[name] != 0:
            failures.append(f"critical:{name}={overall[name]}")
    for metric, threshold in (
        ("case_hit_at_k", THRESHOLDS["case_hit_at_k"]),
        (
            "decisive_annotation_recall_at_k",
            THRESHOLDS["decisive_annotation_recall_at_k"],
        ),
        ("counterevidence_recall_at_k", THRESHOLDS["counterevidence_recall_at_k"]),
        (
            "qualifier_exception_recall_at_k",
            THRESHOLDS["qualifier_exception_recall_at_k"],
        ),
        (
            "complete_joint_group_coverage_at_k",
            THRESHOLDS["complete_joint_group_coverage_at_k"],
        ),
    ):
        value = overall[metric]
        if value is not None and value < threshold:
            failures.append(f"coverage:{metric}={value:.6f}<{threshold:.6f}")
    for family_id, family in sorted(summary["families"].items()):
        hit = family["case_hit_at_k"]
        recall = family["decisive_annotation_recall_at_k"]
        if hit is not None and hit < THRESHOLDS["family_case_hit_at_k"]:
            failures.append(
                f"family:{family_id}:case_hit_at_k={hit:.6f}"
                f"<{THRESHOLDS['family_case_hit_at_k']:.6f}"
            )
        if recall is not None and recall < THRESHOLDS[
            "family_decisive_annotation_recall_at_k"
        ]:
            failures.append(
                f"family:{family_id}:decisive_annotation_recall_at_k={recall:.6f}"
                f"<{THRESHOLDS['family_decisive_annotation_recall_at_k']:.6f}"
            )
    return (not failures, failures)


def evaluate_results(
    root: Path,
    results: list[dict[str, Any]],
    *,
    mutated_gold: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    verify_freeze_receipt(root)
    cases = load_cases(root)
    gold = mutated_gold if mutated_gold is not None else load_gold(root)
    gold_validation = validate_gold_interpretation(cases, gold)
    subsets = load_subsets(root)
    passage_index, _ = load_passages(root)
    anchor_reverse = load_anchor_reverse_mapping(root)

    result_by_case: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for result in results:
        case_id = result.get("case_id")
        if case_id in result_by_case:
            duplicates.append(str(case_id))
        result_by_case[str(case_id)] = result
    missing = sorted(set(cases) - set(result_by_case))
    extra = sorted(set(result_by_case) - set(cases))
    if duplicates or missing or extra:
        raise EvaluatorError(
            f"result case set mismatch duplicates={duplicates} missing={missing} extra={extra}"
        )

    case_metrics = [
        evaluate_case(
            cases[case_id],
            gold[case_id],
            result_by_case[case_id],
            subsets,
            passage_index,
            anchor_reverse,
        )
        for case_id in sorted(cases)
    ]
    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_metrics:
        families[row["family"]].append(row)
    family_summary = {
        family_id: _aggregate_case_metrics(rows)
        for family_id, rows in sorted(families.items())
    }
    expected_families = {f"F{n:02d}" for n in range(1, 13)}
    family_reporting_complete = set(family_summary) == expected_families
    summary = {
        "schema_version": "1.0",
        "evaluator_id": "eb-retrieval-evaluator-assurance-rc1",
        "corpus_tree_sha256": EXPECTED_CORPUS_TREE_SHA256,
        "gold_interpretation_validation": gold_validation,
        "thresholds": deepcopy(THRESHOLDS),
        "overall": _aggregate_case_metrics(case_metrics),
        "families": family_summary,
        "family_reporting_complete": family_reporting_complete,
        "case_metrics": case_metrics,
    }
    qualified, failures = qualify_summary(summary)
    summary["qualified_retrieval_assurance_pass"] = qualified
    summary["qualification_failures"] = failures
    return summary


def _result(
    case: dict[str, Any],
    hits: list[dict[str, Any]],
    subset: dict[str, Any],
    retriever_id: str,
    completeness_status: str,
) -> dict[str, Any]:
    normalized_hits: list[dict[str, Any]] = []
    for rank, hit in enumerate(hits, 1):
        normalized_hits.append(
            {
                "source_id": hit["source_id"],
                "passage_id": hit.get("passage_id"),
                "anchor": hit.get("anchor"),
                "rank": rank,
                "score": hit.get("score"),
                "text": hit.get("text"),
            }
        )
    return {
        "schema_version": "1.0",
        "case_id": case["case_id"],
        "hits": normalized_hits,
        "search_scope": {
            "actual_searchable_subset_id": subset["subset_id"],
            "observed_scope": _scope_record(subset),
        },
        "completeness_claim": {
            "status": completeness_status,
            "basis": "synthetic-control",
        },
        "run_identity": {
            "retriever_id": retriever_id,
            "configuration_id": "rc1-fixed",
            "run_id": f"{retriever_id}:{case['case_id']}",
        },
    }


def _accessible_decisive(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("decisive") is True and row.get("in_accessible_subset") is True
    ]


def _oracle_hits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in _accessible_decisive(rows):
        identity = _annotation_identity(row)
        if identity in seen:
            continue
        seen.add(identity)
        hits.append(
            {
                "source_id": row["source_id"],
                "passage_id": row["passage_id"],
                "text": row.get("span_text"),
                "score": 1.0,
            }
        )
    return hits


TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:\.[0-9]+)?")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "does",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_RE.findall(text)
        if token.lower() not in STOPWORDS and len(token) > 1
    }


def _lexical_hits(
    case: dict[str, Any],
    subset: dict[str, Any],
    by_source: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    query = _tokens(case["claim_text"])
    scored: list[tuple[float, str, int, dict[str, Any]]] = []
    for source_id in subset["source_ids"]:
        for passage in by_source[source_id]:
            passage_tokens = _tokens(passage["text"])
            overlap = len(query & passage_tokens)
            score = overlap / max(1, len(query))
            scored.append((-score, source_id, passage["paragraph_index"], passage))
    scored.sort(key=lambda row: (row[0], row[1], row[2], row[3]["passage_id"]))
    k = int(case["runtime_config"]["maximum_passages"])
    return [
        {
            "source_id": passage["source_id"],
            "passage_id": passage["passage_id"],
            "text": passage["text"],
            "score": -negative_score,
        }
        for negative_score, _, _, passage in scored[:k]
    ]


def _source_order_hits(
    case: dict[str, Any],
    subset: dict[str, Any],
    by_source: dict[str, list[dict[str, Any]]],
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id in sorted(subset["source_ids"]):
        for passage in sorted(
            by_source[source_id], key=lambda row: row["paragraph_index"]
        ):
            rows.append(
                {
                    "source_id": source_id,
                    "passage_id": passage["passage_id"],
                    "text": passage["text"],
                    "score": None,
                }
            )
    if limit is None:
        limit = int(case["runtime_config"]["maximum_passages"])
    return rows[:limit]


def _hard_negative_hits(
    case: dict[str, Any],
    gold_rows: list[dict[str, Any]],
    subset: dict[str, Any],
    by_source: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    k = int(case["runtime_config"]["maximum_passages"])
    allowed = set(subset["source_ids"])
    ordered: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in gold_rows:
        identity = _annotation_identity(row)
        if row.get("relevance_class") != "hard_negative" or row["source_id"] not in allowed:
            continue
        if identity in seen:
            continue
        seen.add(identity)
        passage = next(
            item
            for item in by_source[row["source_id"]]
            if item["passage_id"] == row["passage_id"]
        )
        ordered.append(
            {
                "source_id": row["source_id"],
                "passage_id": row["passage_id"],
                "text": passage["text"],
                "score": 1.0,
            }
        )
    for hit in _source_order_hits(case, subset, by_source, limit=10_000):
        identity = (hit["source_id"], hit["passage_id"])
        if identity not in seen:
            seen.add(identity)
            ordered.append(hit)
        if len(ordered) >= k:
            break
    return ordered[:k]


def make_control_results(root: Path, control_id: str) -> list[dict[str, Any]]:
    cases = load_cases(root)
    gold = load_gold(root)
    validate_gold_interpretation(cases, gold)
    subsets = load_subsets(root)
    _, by_source = load_passages(root)
    outputs: list[dict[str, Any]] = []

    for case_id in sorted(cases):
        case = cases[case_id]
        rows = gold[case_id]
        subset = subsets[case["accessible_subset_id"]]
        k = int(case["runtime_config"]["maximum_passages"])
        completeness = "full_corpus" if subset["subset_id"] == "full" else "unknown"

        if control_id == "C0":
            hits: list[dict[str, Any]] = []
        elif control_id == "C1":
            hits = _oracle_hits(rows)[:k]
        elif control_id == "C2":
            hits = _source_order_hits(case, subset, by_source)
        elif control_id == "C3":
            hits = _lexical_hits(case, subset, by_source)
        elif control_id == "C4":
            hits = _source_order_hits(case, subset, by_source, limit=10_000)
        elif control_id == "C5":
            hits = []
            for row in _oracle_hits(rows)[:k]:
                hits.append(
                    {
                        "source_id": row["source_id"] + "-CORRUPT",
                        "passage_id": row["passage_id"],
                        "text": row.get("text"),
                        "score": row.get("score"),
                    }
                )
        elif control_id == "C6":
            hits = _oracle_hits(rows)[:k]
            completeness = "comprehensive"
        elif control_id == "C7":
            hits = _oracle_hits(rows)[:k]
            completeness = "unknown"
        elif control_id == "C8":
            hits = _hard_negative_hits(case, rows, subset, by_source)
        else:
            raise EvaluatorError(f"unknown control: {control_id}")

        outputs.append(_result(case, hits, subset, control_id, completeness))
    return outputs


def run_controls(root: Path) -> dict[str, Any]:
    verify_freeze_receipt(root)
    cases = load_cases(root)
    gold = load_gold(root)
    gold_validation = validate_gold_interpretation(cases, gold)
    control_summaries: dict[str, Any] = {}
    for control_id in [f"C{n}" for n in range(9)]:
        results = make_control_results(root, control_id)
        summary = evaluate_results(root, results)
        control_summaries[control_id] = {
            "result_set_sha256": sha256_json(results),
            "summary": summary,
            "summary_sha256": sha256_json(summary),
        }

    expectations = {
        "C0_fails_coverage": not control_summaries["C0"]["summary"][
            "qualified_retrieval_assurance_pass"
        ],
        "C1_qualified_positive_ceiling": control_summaries["C1"]["summary"][
            "qualified_retrieval_assurance_pass"
        ],
        "C2_not_qualified": not control_summaries["C2"]["summary"][
            "qualified_retrieval_assurance_pass"
        ],
        "C4_not_qualified": not control_summaries["C4"]["summary"][
            "qualified_retrieval_assurance_pass"
        ],
        "C4_budget_gate_fires": control_summaries["C4"]["summary"]["overall"][
            "budget_violation_count"
        ]
        > 0,
        "C5_not_qualified": not control_summaries["C5"]["summary"][
            "qualified_retrieval_assurance_pass"
        ],
        "C5_no_valid_decisive_credit": control_summaries["C5"]["summary"]["overall"][
            "decisive_annotation_recall_at_k"
        ]
        == 0.0,
        "C6_not_qualified": not control_summaries["C6"]["summary"][
            "qualified_retrieval_assurance_pass"
        ],
        "C6_false_completeness_detected": control_summaries["C6"]["summary"][
            "overall"
        ]["false_completeness_claim_count"]
        > 0,
        "C7_no_false_completeness_failure": control_summaries["C7"]["summary"][
            "overall"
        ]["false_completeness_claim_count"]
        == 0,
        "C7_qualified_honest_bounded": control_summaries["C7"]["summary"][
            "qualified_retrieval_assurance_pass"
        ],
        "C8_worse_than_oracle_recall": (
            control_summaries["C8"]["summary"]["overall"][
                "decisive_annotation_recall_at_k"
            ]
            or 0.0
        )
        < (
            control_summaries["C1"]["summary"]["overall"][
                "decisive_annotation_recall_at_k"
            ]
            or 0.0
        ),
    }
    expectations["C3_observed_qualified_pass"] = control_summaries["C3"]["summary"][
        "qualified_retrieval_assurance_pass"
    ]

    return {
        "schema_version": "1.0",
        "evaluator_id": "eb-retrieval-evaluator-assurance-rc1",
        "corpus_tree_sha256": EXPECTED_CORPUS_TREE_SHA256,
        "gold_interpretation_validation": gold_validation,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
        },
        "threshold_configuration_sha256": sha256_json(THRESHOLDS),
        "controls": control_summaries,
        "expectations": expectations,
    }


def mutation_sensitivity_control(root: Path) -> dict[str, Any]:
    cases = load_cases(root)
    gold = load_gold(root)
    validate_gold_interpretation(cases, gold)
    c1_results = make_control_results(root, "C1")
    baseline = evaluate_results(root, c1_results)
    mutated = deepcopy(gold)

    target_case_id = next(
        case_id
        for case_id in sorted(mutated)
        if any(
            row.get("decisive") is True and row.get("in_accessible_subset") is True
            for row in mutated[case_id]
        )
    )
    target_rows = mutated[target_case_id]
    target_row = next(
        row
        for row in target_rows
        if row.get("decisive") is True and row.get("in_accessible_subset") is True
    )
    old_passage_id = target_row["passage_id"]
    new_passage_id = old_passage_id + "-MUTATED"
    target_row["passage_id"] = new_passage_id
    decisive_passages = sorted(
        {row["passage_id"] for row in target_rows if row.get("decisive") is True}
    )
    decisive_sources = sorted(
        {row["source_id"] for row in target_rows if row.get("decisive") is True}
    )
    for row in target_rows:
        row["gold_passage_ids"] = decisive_passages
        row["gold_source_ids"] = decisive_sources

    mutated_summary = evaluate_results(root, c1_results, mutated_gold=mutated)
    changed = sha256_json(baseline) != sha256_json(mutated_summary)
    return {
        "status": "PASS" if changed else "FAIL",
        "target_case_id": target_case_id,
        "old_passage_id": old_passage_id,
        "mutated_passage_id": new_passage_id,
        "baseline_summary_sha256": sha256_json(baseline),
        "mutated_summary_sha256": sha256_json(mutated_summary),
        "result_changed": changed,
    }


def metamorphic_controls(root: Path) -> dict[str, Any]:
    cases = load_cases(root)
    gold = load_gold(root)
    subsets = load_subsets(root)
    passage_index, _ = load_passages(root)
    anchor_reverse = load_anchor_reverse_mapping(root)

    oracle = make_control_results(root, "C1")
    canonical = evaluate_results(root, oracle)
    canonical_hash = sha256_json(canonical)

    source_view = (
        root
        / "transforms"
        / "views"
        / "transform-source-enumeration-permutation-v1"
        / "view_manifest.json"
    )
    metadata_view = (
        root
        / "transforms"
        / "views"
        / "transform-harmless-metadata-order-permutation-v1"
        / "view_manifest.json"
    )
    if not source_view.is_file() or not metadata_view.is_file():
        raise EvaluatorError("required frozen transform view manifest missing")

    source_permutation = evaluate_results(root, deepcopy(oracle))
    metadata_permutation = evaluate_results(root, deepcopy(oracle))

    target_result = next(result for result in deepcopy(oracle) if result["hits"])
    target_case = cases[target_result["case_id"]]
    target_rows = gold[target_result["case_id"]]

    duplicate_result = deepcopy(target_result)
    duplicate_result["hits"].insert(1, deepcopy(duplicate_result["hits"][0]))
    for index, hit in enumerate(duplicate_result["hits"], 1):
        hit["rank"] = index
    duplicate_case_metric = evaluate_case(
        target_case,
        target_rows,
        duplicate_result,
        subsets,
        passage_index,
        anchor_reverse,
    )
    original_case_metric = evaluate_case(
        target_case,
        target_rows,
        target_result,
        subsets,
        passage_index,
        anchor_reverse,
    )

    paraphrase_result = deepcopy(target_result)
    fake = deepcopy(paraphrase_result["hits"][0])
    fake["source_id"] = fake["source_id"] + "-PARAPHRASE-DUP"
    fake["passage_id"] = fake["passage_id"] + "-PARAPHRASE-DUP"
    fake["text"] = "Paraphrased duplicate text that is not a frozen gold identity."
    paraphrase_result["hits"].insert(1, fake)
    for index, hit in enumerate(paraphrase_result["hits"], 1):
        hit["rank"] = index
    paraphrase_case_metric = evaluate_case(
        target_case,
        target_rows,
        paraphrase_result,
        subsets,
        passage_index,
        anchor_reverse,
    )

    transformed_source = None
    transformed_passage_id = None
    transformed_anchor = None
    stale_anchor = None
    transformed_case = None
    transformed_rows = None
    for case_id in sorted(cases):
        for row in gold[case_id]:
            if row.get("decisive") is not True or row.get("in_accessible_subset") is not True:
                continue
            identity = (row["source_id"], row["passage_id"])
            passage = passage_index.get(identity)
            if passage is None:
                continue
            candidates = [
                key
                for key, passage_id in anchor_reverse.items()
                if key[0] == row["source_id"] and passage_id == row["passage_id"]
            ]
            if not candidates:
                continue
            key = candidates[0]
            if (key[1], key[2]) == (passage["start_offset"], passage["end_offset"]):
                continue
            transformed_source = row["source_id"]
            transformed_passage_id = row["passage_id"]
            transformed_anchor = {
                "start_offset": key[1],
                "end_offset": key[2],
                "offset_unit": key[3],
                "transform_id": PARAGRAPH_TRANSFORM_ID,
            }
            stale_anchor = {
                "start_offset": passage["start_offset"],
                "end_offset": passage["end_offset"],
                "offset_unit": passage["offset_unit"],
                "transform_id": PARAGRAPH_TRANSFORM_ID,
            }
            transformed_case = cases[case_id]
            transformed_rows = gold[case_id]
            break
        if transformed_case is not None:
            break
    if transformed_case is None or transformed_rows is None:
        raise EvaluatorError("no paragraph-order transformed decisive anchor found")

    subset = subsets[transformed_case["accessible_subset_id"]]
    mapped_result = _result(
        transformed_case,
        [
            {
                "source_id": transformed_source,
                "passage_id": None,
                "anchor": transformed_anchor,
            }
        ],
        subset,
        "metamorphic-mapped-anchor",
        "unknown",
    )
    stale_result = _result(
        transformed_case,
        [
            {
                "source_id": transformed_source,
                "passage_id": None,
                "anchor": stale_anchor,
            }
        ],
        subset,
        "metamorphic-stale-anchor",
        "unknown",
    )
    mapped_metric = evaluate_case(
        transformed_case,
        transformed_rows,
        mapped_result,
        subsets,
        passage_index,
        anchor_reverse,
    )
    stale_metric = evaluate_case(
        transformed_case,
        transformed_rows,
        stale_result,
        subsets,
        passage_index,
        anchor_reverse,
    )

    return {
        "source_enumeration_view_present": source_view.is_file(),
        "harmless_metadata_order_view_present": metadata_view.is_file(),
        "source_enumeration_permutation_invariant": sha256_json(source_permutation)
        == canonical_hash,
        "harmless_metadata_order_invariant": sha256_json(metadata_permutation)
        == canonical_hash,
        "duplicate_insertion_does_not_increase_decisive_credit": duplicate_case_metric[
            "decisive_annotations_hit_count"
        ]
        == original_case_metric["decisive_annotations_hit_count"],
        "paraphrased_duplicate_does_not_increase_decisive_credit": paraphrase_case_metric[
            "decisive_annotations_hit_count"
        ]
        == original_case_metric["decisive_annotations_hit_count"],
        "paragraph_transform_mapping_recovers_gold_identity": mapped_metric[
            "decisive_annotations_hit_count"
        ]
        >= 1,
        "paragraph_transform_stale_offsets_rejected": stale_metric[
            "decisive_annotations_hit_count"
        ]
        == 0
        and stale_metric["provenance_invalid_hit_count"] >= 1,
        "paragraph_transform_target": {
            "case_id": transformed_case["case_id"],
            "source_id": transformed_source,
            "passage_id": transformed_passage_id,
        },
    }


def assurance_record(root: Path) -> dict[str, Any]:
    controls_first = run_controls(root)
    controls_second = run_controls(root)
    first_bytes = canonical_json_bytes(controls_first)
    second_bytes = canonical_json_bytes(controls_second)
    deterministic = first_bytes == second_bytes
    metamorphic = metamorphic_controls(root)
    mutation = mutation_sensitivity_control(root)

    required_expectations = [
        "C0_fails_coverage",
        "C1_qualified_positive_ceiling",
        "C2_not_qualified",
        "C4_not_qualified",
        "C4_budget_gate_fires",
        "C5_not_qualified",
        "C5_no_valid_decisive_credit",
        "C6_not_qualified",
        "C6_false_completeness_detected",
        "C7_no_false_completeness_failure",
        "C7_qualified_honest_bounded",
        "C8_worse_than_oracle_recall",
    ]
    controls_ok = all(
        controls_first["expectations"][name] for name in required_expectations
    )
    metamorphic_ok = all(
        value
        for key, value in metamorphic.items()
        if key != "paragraph_transform_target"
    )
    mutation_ok = mutation["status"] == "PASS"

    if not deterministic:
        disposition = "INCONCLUSIVE"
        assurance_level = "E1"
        prompt2_authorized = False
        stop_reason = "deterministic evaluator output was not reproducible"
    elif not controls_ok:
        disposition = "INCONCLUSIVE"
        assurance_level = "E1"
        prompt2_authorized = False
        stop_reason = "one or more preregistered critical synthetic controls failed"
    elif not metamorphic_ok or not mutation_ok:
        disposition = "INCONCLUSIVE"
        assurance_level = "E1"
        prompt2_authorized = False
        stop_reason = "sensitivity/invariance validation did not pass"
    elif controls_first["expectations"]["C3_observed_qualified_pass"]:
        disposition = "INCONCLUSIVE"
        assurance_level = "E2"
        prompt2_authorized = False
        stop_reason = (
            "the preregistered lexical-only weak retriever obtained a qualified pass; "
            "benchmark/evaluator discrimination is insufficiently established"
        )
    else:
        disposition = "SUPPORTED FOR PROMOTION"
        assurance_level = "E3"
        prompt2_authorized = True
        stop_reason = None

    return {
        "schema_version": "1.0",
        "decision": (
            "fitness of EB retrieval evaluator RC1 for later frozen benchmark measurement"
        ),
        "research_disposition": disposition,
        "evaluator_assurance_level": assurance_level,
        "prompt2_authorized": prompt2_authorized,
        "stop_reason": stop_reason,
        "corpus_tree_sha256": EXPECTED_CORPUS_TREE_SHA256,
        "threshold_configuration": deepcopy(THRESHOLDS),
        "threshold_configuration_sha256": sha256_json(THRESHOLDS),
        "determinism": {
            "canonical_identical": deterministic,
            "run_1_sha256": sha256_bytes(first_bytes),
            "run_2_sha256": sha256_bytes(second_bytes),
        },
        "control_expectations": controls_first["expectations"],
        "controls": controls_first["controls"],
        "metamorphic": metamorphic,
        "mutation_sensitivity": mutation,
        "limitations": [
            (
                "generator_source_commit is null; independent regeneration from committed "
                "generator source is not established"
            ),
            "gold is synthetic adjudicator output, not independent regulatory truth",
            "no independent evaluator implementation/cross-check was performed in RC1",
            (
                "thresholds are preregistered engineering tolerances, not empirically "
                "calibrated safety limits"
            ),
            "real Evidence Bundler retrieval behavior was not inspected or executed",
        ],
        "what_not_established": [
            "real Evidence Bundler retrieval quality",
            "corpus completeness or external representativeness",
            "source authority or legitimacy",
            "CAL semantic evaluator correctness",
            "claim decomposition correctness",
            "production readiness of any retrieval change",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark-root",
        type=Path,
        default=Path("benchmarks/eb-challenge-corpus-v1"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/eb-retrieval-evaluator-rc1/assurance.json"),
    )
    args = parser.parse_args()

    record = assurance_record(args.benchmark_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_bytes = canonical_json_bytes(record)
    args.output.write_bytes(output_bytes)
    digest = sha256_bytes(output_bytes)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "sha256": digest,
                "research_disposition": record["research_disposition"],
                "evaluator_assurance_level": record["evaluator_assurance_level"],
                "prompt2_authorized": record["prompt2_authorized"],
            },
            sort_keys=True,
        )
    )
    return 0 if record["prompt2_authorized"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
