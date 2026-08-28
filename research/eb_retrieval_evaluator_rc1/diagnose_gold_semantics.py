from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def identity(row: dict[str, Any]) -> tuple[str, str]:
    return (row["source_id"], row["passage_id"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = read_jsonl(args.benchmark_root / "gold" / "dev_relevance.jsonl")
    rows += read_jsonl(args.benchmark_root / "gold" / "test_relevance.jsonl")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["case_id"]].append(row)

    candidate_counts = Counter()
    included_classes = Counter()
    excluded_classes = Counter()
    summary_inconsistent: list[str] = []
    gold_id_without_row: dict[str, list[list[str]]] = {}
    candidate_mismatches: dict[str, list[str]] = defaultdict(list)
    family_candidate_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for case_id, case_rows in sorted(grouped.items()):
        first = case_rows[0]
        summary_sources = tuple(sorted(set(first.get("gold_source_ids", []))))
        summary_passages = tuple(sorted(set(first.get("gold_passage_ids", []))))
        for row in case_rows[1:]:
            if tuple(sorted(set(row.get("gold_source_ids", [])))) != summary_sources:
                summary_inconsistent.append(f"{case_id}: gold_source_ids vary across rows")
            if tuple(sorted(set(row.get("gold_passage_ids", [])))) != summary_passages:
                summary_inconsistent.append(f"{case_id}: gold_passage_ids vary across rows")

        summary_pairs = {
            identity(row)
            for row in case_rows
            if row["source_id"] in summary_sources and row["passage_id"] in summary_passages
        }
        orphan_pairs = [
            [source_id, passage_id]
            for source_id in summary_sources
            for passage_id in summary_passages
            if not any(
                row["source_id"] == source_id and row["passage_id"] == passage_id
                for row in case_rows
            )
        ]
        # Cartesian orphan pairs are only diagnostic. The authoritative pair candidates below
        # always come from actual row identities.
        if summary_sources or summary_passages:
            represented_sources = {source for source, _ in summary_pairs}
            represented_passages = {passage for _, passage in summary_pairs}
            missing = []
            for source_id in sorted(set(summary_sources) - represented_sources):
                missing.append([source_id, "<no-row-for-source>"])
            for passage_id in sorted(set(summary_passages) - represented_passages):
                missing.append(["<no-row-for-passage>", passage_id])
            if missing:
                gold_id_without_row[case_id] = missing

        decisive = {identity(row) for row in case_rows if row.get("decisive") is True}
        non_hard_negative = {
            identity(row)
            for row in case_rows
            if row.get("relevance_class") != "hard_negative"
        }
        decisive_plus_material = {
            identity(row)
            for row in case_rows
            if row.get("decisive") is True or row.get("relevance_class") == "material_context"
        }
        non_negative_non_control = {
            identity(row)
            for row in case_rows
            if row.get("relevance_class") != "hard_negative"
            and row.get("evaluator_only_negative_control") is not True
        }
        candidates = {
            "decisive_only": decisive,
            "all_non_hard_negative": non_hard_negative,
            "decisive_plus_material_context": decisive_plus_material,
            "non_hard_negative_non_control": non_negative_non_control,
        }
        family = first["challenge_family"]
        for name, candidate in candidates.items():
            if candidate == summary_pairs:
                candidate_counts[name] += 1
                family_candidate_counts[family][name] += 1
            else:
                candidate_mismatches[name].append(case_id)

        for row in case_rows:
            if identity(row) in summary_pairs:
                included_classes[str(row.get("relevance_class"))] += 1
            else:
                excluded_classes[str(row.get("relevance_class"))] += 1

    report = {
        "case_count": len(grouped),
        "annotation_count": len(rows),
        "summary_arrays_consistent_within_case": not summary_inconsistent,
        "summary_inconsistencies": summary_inconsistent,
        "gold_ids_without_matching_row_identity": gold_id_without_row,
        "candidate_exact_match_case_counts": dict(sorted(candidate_counts.items())),
        "candidate_mismatch_case_counts": {
            name: len(case_ids) for name, case_ids in sorted(candidate_mismatches.items())
        },
        "candidate_mismatch_case_ids": {
            name: case_ids for name, case_ids in sorted(candidate_mismatches.items())
        },
        "family_candidate_exact_match_counts": {
            family: dict(sorted(counts.items()))
            for family, counts in sorted(family_candidate_counts.items())
        },
        "row_relevance_classes_in_case_gold": dict(sorted(included_classes.items())),
        "row_relevance_classes_outside_case_gold": dict(sorted(excluded_classes.items())),
        "interpretation_tested": (
            "case-level gold source/passage arrays are compared against row identities; "
            "candidate exact matches are descriptive artifact facts, not generator intent"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical(report))
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
