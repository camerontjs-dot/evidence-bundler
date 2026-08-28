#!/usr/bin/env python3
"""Validate eb-challenge-corpus-v1 structure, spans, hashes, and leak boundaries."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from generate_eb_challenge_corpus import (
    ADJUDICATOR_ID,
    CORPUS_NAME,
    DECOMPOSITION_FAMILIES,
    FAMILY_NAMES,
    GOLD_RECORD_VERSION,
    RELEVANCE_CLASSES,
    TREE_HASH_EXCLUSIONS,
    file_tree_hash,
    sha256_file,
    sha256_text,
)


REQUIRED_FAMILIES = set(FAMILY_NAMES)
REQUIRED_SUBSETS = {
    "full",
    "ordinary_window",
    "bounded_missing_decisive",
    "stale_only",
    "distractor_heavy",
}
REQUIRED_TRANSFORMS = {
    "source_enumeration_permutation",
    "harmless_metadata_order_permutation",
    "duplicate_document_insertion",
    "paraphrased_duplicate_insertion",
    "paragraph_order_permutation",
}
DECISIVE_CLASSES = {
    "decisive_support",
    "decisive_contradiction",
    "decisive_qualifier",
    "decisive_exception",
}
QUALIFYING_CLASSES = {
    "decisive_contradiction",
    "decisive_qualifier",
    "decisive_exception",
}
RUNTIME_CASE_DISALLOWED_FIELDS = {
    "challenge_family",
    "challenge_family_name",
    "gold_source_ids",
    "gold_passage_ids",
    "relevance_class",
    "adjudication_rationale",
    "short_adjudication_rationale",
    "expected_ranking",
    "expected_output",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing JSONL file: {path.relative_to(path.parents[2])}")
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSONL at {path.name}:{line_number}: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"JSONL row is not an object at {path.name}:{line_number}")
            continue
        rows.append(value)
    return rows


def row_check(
    checks: list[dict[str, Any]],
    check_id: str,
    passed: int,
    failed: int,
    details: list[str] | None = None,
) -> None:
    checks.append(
        {
            "check_id": check_id,
            "status": "PASS" if failed == 0 else "FAIL",
            "pass_count": passed,
            "fail_count": failed,
            "details": (details or [])[:20],
        }
    )


def validate_corpus(root: Path, *, require_control_bindings: bool = True) -> dict[str, Any]:
    root = root.resolve()
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = root / "corpus_manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            raw_manifest = read_json(manifest_path)
            if isinstance(raw_manifest, dict):
                manifest = raw_manifest
            else:
                errors.append("corpus_manifest.json is not an object")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"cannot read corpus_manifest.json: {exc}")
    else:
        errors.append("missing corpus_manifest.json")
    row_check(
        checks,
        "manifest_present_and_parseable",
        1 if manifest else 0,
        0 if manifest else 1,
        [] if manifest else ["manifest missing or invalid"],
    )

    source_map: dict[str, dict[str, Any]] = {}
    passage_map: dict[str, dict[str, Any]] = {}
    source_content: dict[str, bytes] = {}
    source_check_pass = 0
    source_check_fail = 0
    source_errors: list[str] = []
    sources_root = root / "sources"
    if sources_root.exists():
        source_dirs = sorted(path for path in sources_root.iterdir() if path.is_dir())
    else:
        source_dirs = []
        source_errors.append("sources directory missing")
    for source_dir in source_dirs:
        metadata_path = source_dir / "metadata.json"
        content_path = source_dir / "content.txt"
        try:
            metadata = read_json(metadata_path)
            content = content_path.read_bytes()
        except (OSError, json.JSONDecodeError) as exc:
            source_check_fail += 1
            source_errors.append(f"{source_dir.name}: unreadable source: {exc}")
            continue
        sid = metadata.get("source_id")
        if not isinstance(sid, str) or not sid:
            source_check_fail += 1
            source_errors.append(f"{source_dir.name}: missing source_id")
            continue
        if sid in source_map:
            source_check_fail += 1
            source_errors.append(f"duplicate source_id: {sid}")
        if sid != source_dir.name:
            source_check_fail += 1
            source_errors.append(f"directory/source_id mismatch: {source_dir.name} != {sid}")
        source_map[sid] = metadata
        source_content[sid] = content
        if metadata.get("content_hash") == sha256_text(content.decode("utf-8")):
            source_check_pass += 1
        else:
            source_check_fail += 1
            source_errors.append(f"content hash mismatch: {sid}")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            source_check_fail += 1
            source_errors.append(f"content is not UTF-8: {sid}")
        passages = metadata.get("passages", [])
        if not isinstance(passages, list):
            source_check_fail += 1
            source_errors.append(f"passages is not a list: {sid}")
            continue
        for passage in passages:
            pid = passage.get("passage_id")
            start = passage.get("start_offset")
            end = passage.get("end_offset")
            if not isinstance(pid, str) or pid in passage_map:
                source_check_fail += 1
                source_errors.append(f"duplicate or missing passage_id in {sid}")
                continue
            passage_map[pid] = {"source_id": sid, "metadata": passage}
            if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start <= end <= len(content):
                source_check_fail += 1
                source_errors.append(f"invalid passage offsets: {sid}/{pid}")
                continue
            span = content[start:end]
            if sha256_text(span.decode("utf-8")) != passage.get("text_sha256"):
                source_check_fail += 1
                source_errors.append(f"passage text hash mismatch: {sid}/{pid}")
            else:
                source_check_pass += 1
            if passage.get("offset_unit") != "utf8_byte":
                source_check_fail += 1
                source_errors.append(f"unsupported passage offset unit: {sid}/{pid}")
        if metadata.get("passage_count") != len(passages):
            source_check_fail += 1
            source_errors.append(f"passage_count mismatch: {sid}")
    row_check(checks, "source_identity_hash_and_utf8_integrity", source_check_pass, source_check_fail, source_errors)

    source_ids = sorted(source_map)
    manifest_source_rows = manifest.get("sources", []) if isinstance(manifest, dict) else []
    manifest_source_ids = [
        row.get("source_id")
        for row in manifest_source_rows
        if isinstance(row, dict)
    ]
    manifest_source_lookup = {
        row.get("source_id"): row
        for row in manifest_source_rows
        if isinstance(row, dict) and row.get("source_id")
    }
    manifest_source_pass = 0
    manifest_source_fail = 0
    manifest_source_errors: list[str] = []
    if manifest_source_ids == sorted(manifest_source_ids):
        manifest_source_pass += 1
    else:
        manifest_source_fail += 1
        manifest_source_errors.append("manifest source enumeration is not sorted by stable source_id")
    if manifest_source_ids == source_ids:
        manifest_source_pass += 1
    else:
        manifest_source_fail += 1
        manifest_source_errors.append("manifest source IDs differ from source directories")
    for sid in source_ids:
        expected_hash = source_map[sid].get("content_hash")
        if manifest_source_lookup.get(sid, {}).get("content_hash") == expected_hash:
            manifest_source_pass += 1
        else:
            manifest_source_fail += 1
            manifest_source_errors.append(f"manifest source hash mismatch: {sid}")
        if re.fullmatch(r"src-[a-z0-9-]+", sid):
            manifest_source_pass += 1
        else:
            manifest_source_fail += 1
            manifest_source_errors.append(f"source ID is not a stable semantic key: {sid}")
    row_check(checks, "stable_source_identity_and_manifest_alignment", manifest_source_pass, manifest_source_fail, manifest_source_errors)

    cases: list[dict[str, Any]] = []
    case_errors: list[str] = []
    case_pass = 0
    case_fail = 0
    for split in ("dev", "test"):
        cases.extend(read_jsonl(root / "cases" / f"{split}_cases.jsonl", case_errors))
    case_ids = [row.get("case_id") for row in cases]
    if len(case_ids) == len(set(case_ids)):
        case_pass += 1
    else:
        case_fail += 1
        case_errors.append("duplicate case_id")
    for row in cases:
        unknown_fields = sorted(RUNTIME_CASE_DISALLOWED_FIELDS & set(row))
        if unknown_fields:
            case_fail += 1
            case_errors.append(f"runtime case {row.get('case_id')} leaks evaluator fields: {unknown_fields}")
        else:
            case_pass += 1
        if row.get("split") in {"dev", "test"} and row.get("original_claim_id") and row.get("accessible_subset_id"):
            case_pass += 1
        else:
            case_fail += 1
            case_errors.append(f"runtime case missing required fields: {row.get('case_id')}")
    row_check(checks, "runtime_case_identity_and_leakage_boundary", case_pass, case_fail, case_errors)
    case_map = {row.get("case_id"): row for row in cases}

    subsets: dict[str, dict[str, Any]] = {}
    aperture_path = root / "aperture" / "subsets.json"
    aperture_errors: list[str] = []
    aperture_pass = 0
    aperture_fail = 0
    try:
        aperture_data = read_json(aperture_path)
        subset_rows = aperture_data.get("subsets", []) if isinstance(aperture_data, dict) else []
    except (OSError, json.JSONDecodeError) as exc:
        subset_rows = []
        aperture_errors.append(f"cannot read aperture/subsets.json: {exc}")
    for subset in subset_rows:
        if not isinstance(subset, dict) or not subset.get("subset_id"):
            aperture_fail += 1
            aperture_errors.append("invalid subset row")
            continue
        subset_id = subset["subset_id"]
        if subset_id in subsets:
            aperture_fail += 1
            aperture_errors.append(f"duplicate subset_id: {subset_id}")
        subsets[subset_id] = subset
        listed = subset.get("source_ids", [])
        unknown = sorted(set(listed) - set(source_ids))
        if unknown:
            aperture_fail += 1
            aperture_errors.append(f"{subset_id} references missing sources: {unknown}")
        else:
            aperture_pass += 1
        if subset.get("immutable") is True:
            aperture_pass += 1
        else:
            aperture_fail += 1
            aperture_errors.append(f"{subset_id} is not marked immutable")
        if subset.get("source_list_sha256") == sha256_text("\n".join(sorted(listed)) + "\n"):
            aperture_pass += 1
        else:
            aperture_fail += 1
            aperture_errors.append(f"{subset_id} source-list hash mismatch")
    missing_subsets = sorted(REQUIRED_SUBSETS - set(subsets))
    if missing_subsets:
        aperture_fail += 1
        aperture_errors.append(f"missing required aperture subsets: {missing_subsets}")
    else:
        aperture_pass += 1
    row_check(checks, "aperture_subset_integrity", aperture_pass, aperture_fail, aperture_errors)

    gold_rows: list[dict[str, Any]] = []
    gold_errors: list[str] = []
    for split in ("dev", "test"):
        gold_rows.extend(read_jsonl(root / "gold" / f"{split}_relevance.jsonl", gold_errors))
    gold_pass = 0
    gold_fail = 0
    annotation_ids: set[str] = set()
    rows_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in gold_rows:
        aid = row.get("annotation_id")
        if not aid or aid in annotation_ids:
            gold_fail += 1
            gold_errors.append(f"duplicate or missing annotation_id: {aid}")
        else:
            annotation_ids.add(aid)
            gold_pass += 1
        case_id = row.get("case_id")
        rows_by_case[case_id].append(row)
        case = case_map.get(case_id)
        if case is None:
            gold_fail += 1
            gold_errors.append(f"gold row references missing case: {case_id}")
            continue
        if row.get("split") == case.get("split") and row.get("original_claim_id") == case.get("original_claim_id"):
            gold_pass += 1
        else:
            gold_fail += 1
            gold_errors.append(f"gold/case lineage mismatch: {case_id}")
        relevance = row.get("relevance_class")
        if relevance not in RELEVANCE_CLASSES:
            gold_fail += 1
            gold_errors.append(f"invalid relevance class at {aid}: {relevance}")
        else:
            gold_pass += 1
        sid = row.get("source_id")
        pid = row.get("passage_id")
        if sid not in source_map or pid not in passage_map or passage_map.get(pid, {}).get("source_id") != sid:
            gold_fail += 1
            gold_errors.append(f"gold row references missing/mismatched source or passage: {aid}")
            continue
        content = source_content[sid]
        start = row.get("exact_start_offset")
        end = row.get("exact_end_offset")
        if isinstance(start, int) and isinstance(end, int) and 0 <= start <= end <= len(content):
            recovered = content[start:end].decode("utf-8")
            if recovered == row.get("span_text"):
                gold_pass += 1
            else:
                gold_fail += 1
                gold_errors.append(f"gold span text mismatch: {aid}")
        else:
            gold_fail += 1
            gold_errors.append(f"invalid gold offsets: {aid}")
        if row.get("relevance_class") == "hard_negative" and row.get("decisive") is False:
            gold_pass += 1
        elif row.get("relevance_class") in DECISIVE_CLASSES and row.get("decisive") is True:
            gold_pass += 1
        elif row.get("relevance_class") == "material_context" and row.get("decisive") is False:
            gold_pass += 1
        else:
            gold_fail += 1
            gold_errors.append(f"decisive flag inconsistent with relevance class: {aid}")
        subset = subsets.get(row.get("accessible_subset_id"), {})
        accessible = sid in subset.get("source_ids", [])
        if accessible == row.get("in_accessible_subset") and (
            row.get("evidence_visibility") == ("accessible" if accessible else "full_only")
        ):
            gold_pass += 1
        else:
            gold_fail += 1
            gold_errors.append(f"aperture visibility mismatch: {aid}")
        if row.get("jointly_required") and not row.get("joint_group_id"):
            gold_fail += 1
            gold_errors.append(f"joint evidence missing group identity: {aid}")
        else:
            gold_pass += 1
        if row.get("gold_record_version") == GOLD_RECORD_VERSION and row.get("generator_adjudicator_identity") == ADJUDICATOR_ID:
            gold_pass += 1
        else:
            gold_fail += 1
            gold_errors.append(f"gold provenance mismatch: {aid}")
    row_check(checks, "gold_reference_span_and_label_integrity", gold_pass, gold_fail, gold_errors)

    case_gold_pass = 0
    case_gold_fail = 0
    case_gold_errors: list[str] = []
    base_answerability: dict[str, set[bool]] = defaultdict(set)
    base_families: dict[str, set[str]] = defaultdict(set)
    base_qualifying: dict[str, bool] = defaultdict(bool)
    hard_negative_bases: set[str] = set()
    full_only_cases: set[str] = set()
    for case_id, rows in rows_by_case.items():
        case = case_map.get(case_id)
        if case is None:
            continue
        relevant_source_sets = {
            tuple(row.get("gold_source_ids", []))
            for row in rows
        }
        relevant_passage_sets = {
            tuple(row.get("gold_passage_ids", []))
            for row in rows
        }
        if len(relevant_source_sets) == 1 and len(relevant_passage_sets) == 1:
            case_gold_pass += 1
        else:
            case_gold_fail += 1
            case_gold_errors.append(f"inconsistent case-level gold arrays: {case_id}")
        for row in rows:
            base_id = row.get("original_claim_id")
            base_answerability[base_id].add(bool(row.get("answerable_in_full_corpus")))
            base_families[base_id].add(row.get("challenge_family"))
            if row.get("relevance_class") == "hard_negative":
                hard_negative_bases.add(base_id)
            if row.get("relevance_class") in QUALIFYING_CLASSES:
                base_qualifying[base_id] = True
            if row.get("decisive") and row.get("evidence_visibility") == "full_only":
                full_only_cases.add(case_id)
        answerable = bool(next(iter(base_answerability[case["original_claim_id"]])))
        is_negative_control = case.get("variant_id") == "A3"
        has_decisive = any(row.get("decisive") is True for row in rows)
        has_material = any(
            row.get("relevance_class") in DECISIVE_CLASSES | {"material_context"}
            for row in rows
        )
        if not answerable and has_decisive:
            case_gold_fail += 1
            case_gold_errors.append(f"no-answer case has decisive gold passage: {case_id}")
        elif answerable and not is_negative_control and not has_material:
            case_gold_fail += 1
            case_gold_errors.append(f"answerable case has no gold material evidence: {case_id}")
        else:
            case_gold_pass += 1
    if set(case_map) == set(rows_by_case):
        case_gold_pass += 1
    else:
        case_gold_fail += 1
        case_gold_errors.append("runtime cases and gold cases differ")
    for case_id, rows in rows_by_case.items():
        if not rows:
            continue
        base_id = rows[0].get("original_claim_id")
        if base_id not in hard_negative_bases:
            case_gold_fail += 1
            case_gold_errors.append(f"base claim has no hard negative: {base_id}")
        else:
            case_gold_pass += 1
    row_check(checks, "case_answerability_and_hard_negative_rules", case_gold_pass, case_gold_fail, case_gold_errors)

    decompositions: list[dict[str, Any]] = []
    decomposition_errors: list[str] = []
    for split in ("dev", "test"):
        decompositions.extend(read_jsonl(root / "decompositions" / f"{split}_decompositions.jsonl", decomposition_errors))
    decomp_pass = 0
    decomp_fail = 0
    decomp_ids: set[str] = set()
    decomp_by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in decompositions:
        did = row.get("decomposition_id")
        parent = row.get("original_claim_id")
        if not did or did in decomp_ids:
            decomp_fail += 1
            decomposition_errors.append(f"duplicate/missing decomposition_id: {did}")
        else:
            decomp_ids.add(did)
            decomp_pass += 1
        if parent in base_families:
            decomp_by_parent[parent].append(row)
            decomp_pass += 1
        else:
            decomp_fail += 1
            decomposition_errors.append(f"decomposition references missing parent: {parent}")
        if row.get("variant_id") == "A3":
            if row.get("evaluator_only_negative_control") is True and row.get("preserves_parent_meaning") is False:
                decomp_pass += 1
            else:
                decomp_fail += 1
                decomposition_errors.append(f"A3 is not marked as evaluator-only drift control: {did}")
        elif row.get("variant_id") in {"A0", "A1", "A2", "A4"}:
            decomp_pass += 1
        else:
            decomp_fail += 1
            decomposition_errors.append(f"unknown decomposition variant: {did}")
        if any(source_id in json.dumps(row) for source_id in source_ids):
            decomp_fail += 1
            decomposition_errors.append(f"decomposition leaks a source identifier: {did}")
        else:
            decomp_pass += 1
    for parent, rows in decomp_by_parent.items():
        variants = {row.get("variant_id") for row in rows}
        if variants == {"A0", "A1", "A2", "A3", "A4"} and len(rows) == 5:
            decomp_pass += 1
        else:
            decomp_fail += 1
            decomposition_errors.append(f"parent {parent} does not have exactly A0-A4")
    if len(decomp_by_parent) >= 24:
        decomp_pass += 1
    else:
        decomp_fail += 1
        decomposition_errors.append(f"only {len(decomp_by_parent)} decomposition-sensitive parents")
    for case in cases:
        if case.get("decomposition_id") is None:
            if case.get("original_claim_id") in decomp_by_parent:
                decomp_fail += 1
                decomposition_errors.append(f"decomposition parent A0 case lacks decomposition_id: {case.get('case_id')}")
            else:
                decomp_pass += 1
        elif case.get("decomposition_id") not in decomp_ids:
            decomp_fail += 1
            decomposition_errors.append(f"case references missing decomposition: {case.get('case_id')}")
        else:
            decomp_pass += 1
    row_check(checks, "decomposition_lineage_and_variant_integrity", decomp_pass, decomp_fail, decomposition_errors)

    family_pass = 0
    family_fail = 0
    family_errors: list[str] = []
    base_claim_count = len(base_families)
    family_counts = Counter(next(iter(families)) for families in base_families.values() if len(families) == 1)
    if base_claim_count >= 48:
        family_pass += 1
    else:
        family_fail += 1
        family_errors.append(f"only {base_claim_count} base claims")
    if set(family_counts) >= REQUIRED_FAMILIES:
        family_pass += 1
    else:
        family_fail += 1
        family_errors.append(f"missing challenge families: {sorted(REQUIRED_FAMILIES - set(family_counts))}")
    for family in sorted(REQUIRED_FAMILIES):
        if family_counts[family] >= 4:
            family_pass += 1
        else:
            family_fail += 1
            family_errors.append(f"{family} has only {family_counts[family]} base claims")
    unanswerable = {
        base_id
        for base_id, answerability in base_answerability.items()
        if answerability == {False}
    }
    answerable = {
        base_id
        for base_id, answerability in base_answerability.items()
        if answerability == {True}
    }
    if len(unanswerable) >= 8:
        family_pass += 1
    else:
        family_fail += 1
        family_errors.append(f"only {len(unanswerable)} full-corpus no-answer base claims")
    qualifying = answerable & {base_id for base_id, yes in base_qualifying.items() if yes}
    if len(qualifying) >= math.ceil(len(answerable) / 2):
        family_pass += 1
    else:
        family_fail += 1
        family_errors.append(f"only {len(qualifying)}/{len(answerable)} answerable bases have contradiction/qualifier/exception evidence")
    if len(full_only_cases) >= 8:
        family_pass += 1
    else:
        family_fail += 1
        family_errors.append(f"only {len(full_only_cases)} aperture-boundary cases")
    row_check(checks, "challenge_family_and_answerability_minimums", family_pass, family_fail, family_errors)

    split_counts = Counter(row.get("split") for row in cases)
    split_pass = 0
    split_fail = 0
    split_errors: list[str] = []
    total_cases = len(cases)
    dev_ratio = split_counts["dev"] / total_cases if total_cases else 0.0
    if 0.20 <= dev_ratio <= 0.30 and split_counts["dev"] and split_counts["test"]:
        split_pass += 1
    else:
        split_fail += 1
        split_errors.append(f"case split ratio is dev={split_counts['dev']}, test={split_counts['test']}")
    if split_counts["dev"] + split_counts["test"] == total_cases:
        split_pass += 1
    else:
        split_fail += 1
        split_errors.append("unexpected case split value")
    row_check(checks, "frozen_development_and_sealed_test_split", split_pass, split_fail, split_errors)

    leakage_pass = 0
    leakage_fail = 0
    leakage_errors: list[str] = []
    forbidden_tokens = set(source_ids) | set(passage_map)
    forbidden_tokens |= set(FAMILY_NAMES) | set(REQUIRED_FAMILIES)
    forbidden_tokens |= {row.get("case_id") for row in gold_rows if row.get("case_id")}
    forbidden_tokens |= RELEVANCE_CLASSES
    forbidden_tokens.add(ADJUDICATOR_ID)
    for sid, content in source_content.items():
        text = content.decode("utf-8")
        found = sorted(token for token in forbidden_tokens if token and token in text)
        if found:
            leakage_fail += 1
            leakage_errors.append(f"source content leaks evaluator tokens in {sid}: {found[:8]}")
        else:
            leakage_pass += 1
    row_check(checks, "source_content_gold_id_and_label_leakage_guard", leakage_pass, leakage_fail, leakage_errors)

    transform_pass = 0
    transform_fail = 0
    transform_errors: list[str] = []
    transform_path = root / "transforms" / "transform_manifest.json"
    transform_rows: list[dict[str, Any]] = []
    try:
        transform_data = read_json(transform_path)
        transform_rows = transform_data.get("transformations", []) if isinstance(transform_data, dict) else []
    except (OSError, json.JSONDecodeError) as exc:
        transform_errors.append(f"cannot read transform manifest: {exc}")
    transform_types = {row.get("transformation_type") for row in transform_rows}
    if transform_types == REQUIRED_TRANSFORMS:
        transform_pass += 1
    else:
        transform_fail += 1
        transform_errors.append(f"transform types differ: {sorted(transform_types)}")
    for row in transform_rows:
        view_path = root / row.get("view_path", "")
        if view_path.exists() and row.get("gold_data_included") is False:
            transform_pass += 1
        else:
            transform_fail += 1
            transform_errors.append(f"invalid transform view or gold boundary: {row.get('transformation_id')}")
        view_manifest_path = view_path / "view_manifest.json"
        if view_manifest_path.exists():
            try:
                view_manifest = read_json(view_manifest_path)
                if view_manifest.get("gold_data_included") is False:
                    transform_pass += 1
                else:
                    transform_fail += 1
                    transform_errors.append(f"view manifest includes gold data: {row.get('transformation_id')}")
            except (OSError, json.JSONDecodeError) as exc:
                transform_fail += 1
                transform_errors.append(f"invalid view manifest: {row.get('transformation_id')}: {exc}")
    row_check(checks, "metamorphic_transform_views_and_gold_boundary", transform_pass, transform_fail, transform_errors)

    metamorphic_pass = 0
    metamorphic_fail = 0
    metamorphic_errors: list[str] = []
    enum_view = root / "transforms/views/transform-source-enumeration-permutation-v1"
    enum_order_path = enum_view / "source_enumeration.json"
    if enum_order_path.exists():
        enum_order = read_json(enum_order_path).get("source_ids_in_view_order", [])
        view_ids = sorted(path.name for path in (enum_view / "sources").iterdir() if path.is_dir())
        if set(enum_order) == set(source_ids) and enum_order != source_ids:
            metamorphic_pass += 1
        else:
            metamorphic_fail += 1
            metamorphic_errors.append("enumeration permutation is not a distinct permutation")
        for sid in source_ids:
            view_meta = enum_view / "sources" / sid / "metadata.json"
            if view_meta.exists() and read_json(view_meta).get("content_hash") == source_map[sid].get("content_hash"):
                metamorphic_pass += 1
            else:
                metamorphic_fail += 1
                metamorphic_errors.append(f"enumeration view changed source identity/hash: {sid}")
        if set(view_ids) == set(source_ids):
            metamorphic_pass += 1
        else:
            metamorphic_fail += 1
            metamorphic_errors.append("enumeration view source directories differ")
    else:
        metamorphic_fail += 1
        metamorphic_errors.append("missing enumeration view order")
    meta_view = root / "transforms/views/transform-harmless-metadata-order-permutation-v1"
    if (meta_view / "metadata_order.json").exists():
        changed_metadata = 0
        for sid in source_ids:
            source_meta = (meta_view / "sources" / sid / "metadata.json").read_text(encoding="utf-8")
            canonical_meta = (root / "sources" / sid / "metadata.json").read_text(encoding="utf-8")
            if json.loads(source_meta).get("content_hash") == source_map[sid].get("content_hash") and source_meta != canonical_meta:
                changed_metadata += 1
        if changed_metadata == len(source_ids):
            metamorphic_pass += 1
        else:
            metamorphic_fail += 1
            metamorphic_errors.append(f"metadata-order view changed {changed_metadata}/{len(source_ids)} source metadata files")
    else:
        metamorphic_fail += 1
        metamorphic_errors.append("missing metadata-order view")
    duplicate_view = root / "transforms/views/transform-duplicate-document-insertion-v1"
    duplicate_source = duplicate_view / "sources/src-transform-duplicate-canonical"
    if duplicate_source.exists():
        duplicate_meta = read_json(duplicate_source / "metadata.json")
        origin = duplicate_meta.get("derived_from_source_id")
        if origin in source_map and duplicate_meta.get("content_hash") == source_map[origin].get("content_hash"):
            metamorphic_pass += 1
        else:
            metamorphic_fail += 1
            metamorphic_errors.append("duplicate transform is not byte-identical to its origin")
    else:
        metamorphic_fail += 1
        metamorphic_errors.append("missing duplicate insertion source")
    paraphrase_source = root / "transforms/views/transform-paraphrased-duplicate-insertion-v1/sources/src-transform-paraphrase-quillmark"
    if paraphrase_source.exists():
        paraphrase_meta = read_json(paraphrase_source / "metadata.json")
        if paraphrase_meta.get("content_hash") != source_map.get("src-quillmark-current", {}).get("content_hash"):
            metamorphic_pass += 1
        else:
            metamorphic_fail += 1
            metamorphic_errors.append("paraphrased duplicate did not change content hash")
    else:
        metamorphic_fail += 1
        metamorphic_errors.append("missing paraphrased duplicate source")
    paragraph_view = root / "transforms/views/transform-paragraph-order-permutation-v1"
    mapping_path = paragraph_view / "semantic_anchor_mapping.json"
    if mapping_path.exists():
        mapping = read_json(mapping_path)
        if set(mapping) == set(source_ids):
            metamorphic_pass += 1
        else:
            metamorphic_fail += 1
            metamorphic_errors.append("paragraph permutation mapping does not cover canonical sources")
        for sid in source_ids:
            canonical_pids = {row["passage_id"] for row in source_map[sid].get("passages", [])}
            mapped_pids = set(mapping.get(sid, {}))
            if canonical_pids == mapped_pids:
                metamorphic_pass += 1
            else:
                metamorphic_fail += 1
                metamorphic_errors.append(f"paragraph permutation lost semantic anchors: {sid}")
    else:
        metamorphic_fail += 1
        metamorphic_errors.append("missing paragraph permutation mapping")
    row_check(checks, "metamorphic_identity_and_anchor_invariance", metamorphic_pass, metamorphic_fail, metamorphic_errors)

    count_pass = 0
    count_fail = 0
    count_errors: list[str] = []
    actual_passages = sum(len(metadata.get("passages", [])) for metadata in source_map.values())
    if len(source_map) >= 60:
        count_pass += 1
    else:
        count_fail += 1
        count_errors.append(f"only {len(source_map)} source documents")
    if 600 <= actual_passages <= 1200:
        count_pass += 1
    else:
        count_fail += 1
        count_errors.append(f"passage count outside range: {actual_passages}")
    manifest_counts = manifest.get("counts", {})
    expected_actual = {
        "source_documents": len(source_map),
        "passages": actual_passages,
        "cases": len(cases),
        "base_claims": len(base_families),
        "decomposition_records": len(decompositions),
        "unanswerable_base_claims": len(unanswerable),
        "aperture_boundary_cases": len(full_only_cases),
        "aperture_boundary_decisive_annotation_count": sum(
            1
            for rows in rows_by_case.values()
            for row in rows
            if row.get("challenge_family") == "F12"
            and row.get("decisive") is True
            and row.get("evidence_visibility") == "full_only"
        ),
    }
    for key, actual in expected_actual.items():
        if manifest_counts.get(key) == actual:
            count_pass += 1
        else:
            count_fail += 1
            count_errors.append(f"manifest count mismatch {key}: {manifest_counts.get(key)} != {actual}")
    row_check(checks, "minimum_size_and_manifest_counts", count_pass, count_fail, count_errors)

    hash_pass = 0
    hash_fail = 0
    hash_errors: list[str] = []
    computed_tree_hash = file_tree_hash(root)
    if manifest.get("overall_corpus_tree_sha256") == computed_tree_hash:
        hash_pass += 1
    else:
        hash_fail += 1
        hash_errors.append(f"overall tree hash mismatch: {manifest.get('overall_corpus_tree_sha256')} != {computed_tree_hash}")
    expected_config_hash = sha256_text(json.dumps(manifest.get("generator_configuration", {}), sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    if manifest.get("generator_configuration_hash") == expected_config_hash:
        hash_pass += 1
    else:
        hash_fail += 1
        hash_errors.append("generator configuration hash mismatch")
    for relative, expected_hash in manifest.get("gold_file_hashes", {}).items():
        path = root / relative
        if path.exists() and sha256_file(path) == expected_hash:
            hash_pass += 1
        else:
            hash_fail += 1
            hash_errors.append(f"gold file hash mismatch: {relative}")
    for relative, expected_hash in manifest.get("decomposition_file_hashes", {}).items():
        path = root / relative
        if path.exists() and sha256_file(path) == expected_hash:
            hash_pass += 1
        else:
            hash_fail += 1
            hash_errors.append(f"decomposition file hash mismatch: {relative}")
    if require_control_bindings:
        report_path = root / "validation/corpus_validation_report.json"
        receipt_path = root / "validation/freeze_receipt.json"
        if report_path.exists() and manifest.get("validation_report_sha256") == sha256_file(report_path):
            hash_pass += 1
        else:
            hash_fail += 1
            hash_errors.append("validation report hash binding mismatch")
        if receipt_path.exists() and manifest.get("freeze_receipt_sha256") == sha256_file(receipt_path):
            hash_pass += 1
        else:
            hash_fail += 1
            hash_errors.append("freeze receipt hash binding mismatch")
    row_check(checks, "hash_bindings_and_deterministic_tree", hash_pass, hash_fail, hash_errors)

    sums_pass = 0
    sums_fail = 0
    sums_errors: list[str] = []
    sums_path = root / "SHA256SUMS"
    if sums_path.exists():
        listed: dict[str, str] = {}
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split("  ", 1)
            if len(parts) != 2:
                sums_fail += 1
                sums_errors.append(f"malformed SHA256SUMS line: {line}")
                continue
            listed[parts[1]] = parts[0]
        for relative, expected in listed.items():
            path = root / relative
            if path.exists() and sha256_file(path) == expected:
                sums_pass += 1
            else:
                sums_fail += 1
                sums_errors.append(f"SHA256SUMS mismatch: {relative}")
        expected_files = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.relative_to(root).as_posix() != "SHA256SUMS"
        }
        missing = sorted(expected_files - set(listed))
        if missing:
            sums_fail += 1
            sums_errors.append(f"SHA256SUMS omits files: {missing[:10]}")
        else:
            sums_pass += 1
    else:
        sums_fail += 1
        sums_errors.append("missing SHA256SUMS")
    row_check(checks, "sha256sums_receipt_integrity", sums_pass, sums_fail, sums_errors)

    overall_status = "PASS" if not errors and all(check["status"] == "PASS" for check in checks) else "FAIL"
    report = {
        "schema_version": "1.0",
        "report_type": "corpus_validation_report",
        "corpus_name": manifest.get("corpus_name", CORPUS_NAME),
        "corpus_version": manifest.get("corpus_version"),
        "overall_status": overall_status,
        "require_control_bindings": require_control_bindings,
        "overall_corpus_tree_sha256": computed_tree_hash,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "validation_summary": {
            "check_count": len(checks),
            "passed_checks": sum(check["status"] == "PASS" for check in checks),
            "failed_checks": sum(check["status"] == "FAIL" for check in checks),
        },
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--json", action="store_true", help="print the machine-readable report")
    parser.add_argument("--write-report", action="store_true", help="write validation/corpus_validation_report.json")
    parser.add_argument("--allow-unbound-control-files", action="store_true")
    args = parser.parse_args(argv)
    report = validate_corpus(
        args.corpus.resolve(),
        require_control_bindings=not args.allow_unbound_control_files,
    )
    if args.write_report:
        path = args.corpus.resolve() / "validation/corpus_validation_report.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
