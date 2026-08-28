from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

import evaluator as core

CORRECTION_ID = "deviation-07a-gold-summary-semantics"


def validate_gold_interpretation(
    cases: dict[str, dict[str, Any]],
    gold: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Validate the artifact-supported gold semantics discovered after run 33139749679.

    Across all 148 frozen cases, case-level gold_* arrays exactly equal row identities
    whose rows are decisive OR material_context. Hard negatives are outside those arrays.
    """
    errors: list[str] = []
    for case_id, case in cases.items():
        rows = gold.get(case_id, [])
        if not rows:
            errors.append(f"{case_id}: missing gold rows")
            continue
        scored_gold = [
            row
            for row in rows
            if row.get("decisive") is True or core._is_material_context(row)
        ]
        expected_sources = sorted({row["source_id"] for row in scored_gold})
        expected_passages = sorted({row["passage_id"] for row in scored_gold})
        for row in rows:
            summary_sources = sorted(set(row.get("gold_source_ids", [])))
            summary_passages = sorted(set(row.get("gold_passage_ids", [])))
            if summary_sources != expected_sources:
                errors.append(
                    f"{case_id}/{row.get('annotation_id')}: gold_source_ids "
                    f"{summary_sources} != decisive+material-context sources {expected_sources}"
                )
            if summary_passages != expected_passages:
                errors.append(
                    f"{case_id}/{row.get('annotation_id')}: gold_passage_ids "
                    f"{summary_passages} != decisive+material-context passages {expected_passages}"
                )
            if row.get("accessible_subset_id") != case.get("accessible_subset_id"):
                errors.append(
                    f"{case_id}/{row.get('annotation_id')}: accessible subset disagreement"
                )
        hard_negative_ids = {
            (row["source_id"], row["passage_id"])
            for row in rows
            if row.get("relevance_class") == "hard_negative"
        }
        scored_ids = {(row["source_id"], row["passage_id"]) for row in scored_gold}
        if hard_negative_ids & scored_ids:
            errors.append(f"{case_id}: hard-negative identity entered case-level scored gold")
    extra_cases = sorted(set(gold) - set(cases))
    if extra_cases:
        errors.append(f"gold contains unknown cases: {extra_cases}")
    if errors:
        raise core.EvaluatorError(
            "corrected gold interpretation validation failed:\n" + "\n".join(errors[:50])
        )
    return {
        "status": "PASS",
        "cases_checked": len(cases),
        "gold_cases_checked": len(gold),
        "interpretation": (
            "row-level decisive plus material_context annotations define case scored gold; "
            "case-level gold_* arrays are integrity summaries; hard negatives are excluded"
        ),
        "correction_id": CORRECTION_ID,
    }


def oracle_hits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Positive ceiling includes every accessible target scored by retrieval metrics."""
    hits: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if row.get("in_accessible_subset") is not True:
            continue
        if row.get("decisive") is not True and not core._is_material_context(row):
            continue
        identity = (row["source_id"], row["passage_id"])
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


_original_evaluate_case = core.evaluate_case


def evaluate_case(
    case: dict[str, Any],
    rows: list[dict[str, Any]],
    result: dict[str, Any],
    subsets: dict[str, dict[str, Any]],
    passage_index: dict[tuple[str, str], dict[str, Any]],
    anchor_reverse: dict[tuple[str, int, int, str], str],
) -> dict[str, Any]:
    metrics = _original_evaluate_case(
        case, rows, result, subsets, passage_index, anchor_reverse
    )
    k = int(case["runtime_config"]["maximum_passages"])
    hits = result.get("hits") if isinstance(result.get("hits"), list) else []
    bounded_identities = {
        identity
        for identity in (
            core.canonical_hit_identity(hit, passage_index, anchor_reverse)
            for hit in hits[:k]
            if isinstance(hit, dict)
        )
        if identity is not None
    }
    material_ids = {
        (row["source_id"], row["passage_id"])
        for row in rows
        if row.get("in_accessible_subset") is True and core._is_material_context(row)
    }
    metrics["material_context_recall_at_k"] = core.ratio(
        len(material_ids & bounded_identities), len(material_ids)
    )
    return metrics


def mutation_sensitivity_control(root: Path) -> dict[str, Any]:
    cases = core.load_cases(root)
    gold = core.load_gold(root)
    validate_gold_interpretation(cases, gold)
    c1_results = core.make_control_results(root, "C1")
    baseline = core.evaluate_results(root, c1_results)
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

    scored_rows = [
        row
        for row in target_rows
        if row.get("decisive") is True or core._is_material_context(row)
    ]
    scored_passages = sorted({row["passage_id"] for row in scored_rows})
    scored_sources = sorted({row["source_id"] for row in scored_rows})
    for row in target_rows:
        row["gold_passage_ids"] = scored_passages
        row["gold_source_ids"] = scored_sources

    mutated_summary = core.evaluate_results(root, c1_results, mutated_gold=mutated)
    changed = core.sha256_json(baseline) != core.sha256_json(mutated_summary)
    return {
        "status": "PASS" if changed else "FAIL",
        "target_case_id": target_case_id,
        "old_passage_id": old_passage_id,
        "mutated_passage_id": new_passage_id,
        "baseline_summary_sha256": core.sha256_json(baseline),
        "mutated_summary_sha256": core.sha256_json(mutated_summary),
        "result_changed": changed,
        "correction_id": CORRECTION_ID,
    }


def install_correction() -> None:
    core.validate_gold_interpretation = validate_gold_interpretation
    core._oracle_hits = oracle_hits
    core.evaluate_case = evaluate_case
    core.mutation_sensitivity_control = mutation_sensitivity_control


def main() -> int:
    install_correction()
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

    record = core.assurance_record(args.benchmark_root)
    record["apparatus_correction"] = {
        "id": CORRECTION_ID,
        "reason": (
            "first preflight falsified decisive-only case gold interpretation; "
            "gold-only diagnostic showed decisive+material_context exact match in 148/148 cases"
        ),
        "acceptance_thresholds_changed": False,
        "real_eb_output_inspected": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_bytes = core.canonical_json_bytes(record)
    args.output.write_bytes(output_bytes)
    digest = core.sha256_bytes(output_bytes)
    print(
        core.json.dumps(
            {
                "output": str(args.output),
                "sha256": digest,
                "research_disposition": record["research_disposition"],
                "evaluator_assurance_level": record["evaluator_assurance_level"],
                "prompt2_authorized": record["prompt2_authorized"],
                "apparatus_correction": CORRECTION_ID,
            },
            sort_keys=True,
        )
    )
    return 0 if record["prompt2_authorized"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
