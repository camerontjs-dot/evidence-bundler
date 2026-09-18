from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

CAPS = ("0.01", "0.03", "0.05")
BUDGETS = (3, 6)
FAMILIES = (
    "child_coverage",
    "expected_form",
    "subject_child",
    "subject_inherited",
    "predicate_terms",
    "scope_literals",
    "claim_native_lexical",
    "form_plus_inherited_subject",
    "full_obligation",
)
SHUFFLE_FAMILIES = {
    "expected_form",
    "subject_inherited",
    "predicate_terms",
    "scope_literals",
    "claim_native_lexical",
    "full_obligation",
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def paragraph_rows(benchmark_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for content_path in sorted((benchmark_root / "sources").glob("*/content.txt")):
        source_id = content_path.parent.name
        text = content_path.read_text(encoding="utf-8")
        paragraphs = [
            part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()
        ]
        for index, paragraph in enumerate(paragraphs):
            rows.append(
                {
                    "source_id": source_id,
                    "paragraph_index": index,
                    "paragraph_id": f"{source_id}:paragraph:{index:03d}",
                    "text": paragraph,
                }
            )
    return rows


def gold_by_case(
    *,
    benchmark_root: Path,
    gold_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    paragraphs_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in paragraph_rows(benchmark_root):
        paragraphs_by_source[str(row["source_id"])].append(row)

    mapped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for gold in gold_rows:
        source_id = str(gold["source_id"])
        span = str(gold["span_text"])
        matches = [
            row for row in paragraphs_by_source[source_id]
            if span in str(row["text"])
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"gold span mapping must be unique: "
                f"{gold['annotation_id']} -> {len(matches)}"
            )
        enriched = dict(gold)
        enriched["paragraph_id"] = matches[0]["paragraph_id"]
        mapped[str(gold["case_id"])].append(enriched)
    return mapped


def ratio(num: int, den: int) -> float | None:
    return None if den == 0 else num / den


def evaluate_claim(
    *,
    selected_ids: list[str],
    pool: list[dict[str, Any]],
    gold_rows: list[dict[str, Any]],
    baseline_ids: list[str],
) -> dict[str, Any]:
    selected = set(selected_ids)
    baseline = set(baseline_ids)
    candidate_by_id = {str(row["paragraph_id"]): row for row in pool}

    decisive = [
        row for row in gold_rows
        if row.get("decisive") is True
        and row.get("in_accessible_subset") is True
    ]
    decisive_ids = {str(row["paragraph_id"]) for row in decisive}
    qualifier = [
        row for row in decisive
        if any(
            token in str(row.get("relevance_class", "")).lower()
            for token in ("qualifier", "exception", "conditional")
        )
    ]
    qualifier_ids = {str(row["paragraph_id"]) for row in qualifier}
    hard_negative_ids = {
        str(row["paragraph_id"])
        for row in gold_rows
        if str(row.get("relevance_class", "")).lower() == "hard_negative"
    }

    groups: dict[str, set[str]] = defaultdict(set)
    for row in decisive:
        if row.get("joint_group_id"):
            groups[str(row["joint_group_id"])].add(str(row["paragraph_id"]))
    complete_groups = sum(
        bool(members) and members <= selected for members in groups.values()
    )

    child_ids = sorted(
        {
            str(query_hit["child_id"])
            for candidate in pool
            for query_hit in candidate["query_hits"]
            if query_hit.get("child_id") is not None
        }
    )
    children_with_decisive: set[str] = set()
    for paragraph_id in selected & decisive_ids:
        candidate = candidate_by_id.get(paragraph_id)
        if candidate is None:
            continue
        for query_hit in candidate["query_hits"]:
            child_id = query_hit.get("child_id")
            if child_id is not None:
                children_with_decisive.add(str(child_id))

    union = selected | baseline
    jaccard = (
        None if not union else len(selected & baseline) / len(union)
    )
    return {
        "decisive_total": len(decisive_ids),
        "decisive_found": len(decisive_ids & selected),
        "qualifier_total": len(qualifier_ids),
        "qualifier_found": len(qualifier_ids & selected),
        "joint_group_total": len(groups),
        "joint_group_complete": complete_groups,
        "case_hit": None if not decisive_ids else bool(decisive_ids & selected),
        "retrieval_child_count": len(child_ids),
        "retrieval_children_with_decisive_hit": len(
            set(child_ids) & children_with_decisive
        ),
        "annotated_hard_negative_selected": len(
            hard_negative_ids & selected
        ),
        "deep_decisive_rescue_vs_semantic": len(
            (decisive_ids & selected) - baseline
        ),
        "decisive_lost_vs_semantic": len(
            (decisive_ids & baseline) - selected
        ),
        "jaccard_vs_semantic": jaccard,
        "selected_ids": selected_ids,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decisive_total = sum(row["decisive_total"] for row in rows)
    decisive_found = sum(row["decisive_found"] for row in rows)
    qualifier_total = sum(row["qualifier_total"] for row in rows)
    qualifier_found = sum(row["qualifier_found"] for row in rows)
    joint_total = sum(row["joint_group_total"] for row in rows)
    joint_complete = sum(row["joint_group_complete"] for row in rows)
    child_total = sum(row["retrieval_child_count"] for row in rows)
    child_found = sum(
        row["retrieval_children_with_decisive_hit"] for row in rows
    )
    hit_rows = [row for row in rows if row["case_hit"] is not None]
    jaccards = [
        float(row["jaccard_vs_semantic"])
        for row in rows
        if row["jaccard_vs_semantic"] is not None
    ]
    return {
        "claim_count": len(rows),
        "scored_claim_count": len(hit_rows),
        "case_hits": sum(bool(row["case_hit"]) for row in hit_rows),
        "case_hit_rate": ratio(
            sum(bool(row["case_hit"]) for row in hit_rows),
            len(hit_rows),
        ),
        "decisive_found": decisive_found,
        "decisive_total": decisive_total,
        "decisive_recall": ratio(decisive_found, decisive_total),
        "qualifier_found": qualifier_found,
        "qualifier_total": qualifier_total,
        "qualifier_recall": ratio(qualifier_found, qualifier_total),
        "joint_group_complete": joint_complete,
        "joint_group_total": joint_total,
        "joint_group_coverage": ratio(joint_complete, joint_total),
        "retrieval_children_with_decisive_hit": child_found,
        "retrieval_child_count": child_total,
        "retrieval_child_decisive_rate": ratio(child_found, child_total),
        "annotated_hard_negative_selected": sum(
            row["annotated_hard_negative_selected"] for row in rows
        ),
        "deep_decisive_rescue_vs_semantic": sum(
            row["deep_decisive_rescue_vs_semantic"] for row in rows
        ),
        "decisive_lost_vs_semantic": sum(
            row["decisive_lost_vs_semantic"] for row in rows
        ),
        "mean_jaccard_vs_semantic": (
            None if not jaccards else sum(jaccards) / len(jaccards)
        ),
    }


def delta(
    candidate: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, float | int | None]:
    def sub(key: str) -> float | int | None:
        left = candidate[key]
        right = reference[key]
        if left is None or right is None:
            return None
        return left - right

    return {
        "case_hit_rate": sub("case_hit_rate"),
        "decisive_recall": sub("decisive_recall"),
        "qualifier_recall": sub("qualifier_recall"),
        "joint_group_coverage": sub("joint_group_coverage"),
        "retrieval_child_decisive_rate": sub(
            "retrieval_child_decisive_rate"
        ),
        "annotated_hard_negative_selected": sub(
            "annotated_hard_negative_selected"
        ),
        "deep_decisive_rescue_vs_semantic": sub(
            "deep_decisive_rescue_vs_semantic"
        ),
        "decisive_lost_vs_semantic": sub(
            "decisive_lost_vs_semantic"
        ),
    }


def screen(
    correct: dict[str, Any],
    shuffled: dict[str, Any] | None,
    baseline: dict[str, Any],
) -> str:
    c = delta(correct, baseline)
    improves = any(
        value is not None and value > 1e-12
        for value in (
            c["decisive_recall"],
            c["joint_group_coverage"],
            c["retrieval_child_decisive_rate"],
            c["qualifier_recall"],
        )
    )
    harms = (
        (c["decisive_recall"] is not None and c["decisive_recall"] < -1e-12)
        or (
            c["joint_group_coverage"] is not None
            and c["joint_group_coverage"] < -1e-12
        )
    )
    if harms:
        return "HARMFUL_PRIMARY"
    if shuffled is None:
        return "PROMISING_VS_BASELINE" if improves else "NO_AGGREGATE_GAIN"

    cs = delta(correct, shuffled)
    beats_shuffle = any(
        value is not None and value > 1e-12
        for value in (
            cs["decisive_recall"],
            cs["joint_group_coverage"],
            cs["retrieval_child_decisive_rate"],
            cs["qualifier_recall"],
        )
    )
    if improves and beats_shuffle:
        return "PROMISING_CORRECT_OVER_SHUFFLED"
    if improves:
        return "GENERIC_OR_NONCAUSAL_GAIN"
    if all(
        value is None or abs(value) <= 1e-12
        for value in (
            cs["decisive_recall"],
            cs["joint_group_coverage"],
            cs["retrieval_child_decisive_rate"],
            cs["qualifier_recall"],
        )
    ):
        return "NO_CORRECT_SIGNAL_DISCRIMINATION"
    return "MIXED_OR_NULL"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selections", required=True)
    parser.add_argument("--benchmark-root", required=True)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    selections = load_json(args.selections)
    benchmark_root = Path(args.benchmark_root)
    gold_path = Path(args.gold)
    cases = load_jsonl(args.cases)
    mapped_gold = gold_by_case(
        benchmark_root=benchmark_root,
        gold_rows=load_jsonl(gold_path),
    )

    case_id_by_parent = {
        str(row["original_claim_id"]): str(row["case_id"])
        for row in cases
        if str(row["variant_id"]) == "A1"
    }
    claims = {
        str(row["original_claim_id"]): row
        for row in selections["claims"]
    }

    arm_names = sorted(
        {
            arm
            for claim in claims.values()
            for arm in claim["arms"]
        }
    )
    metrics_by_arm: dict[str, dict[str, Any]] = {}
    per_claim_by_arm: dict[str, list[dict[str, Any]]] = {}

    for arm in arm_names:
        budget_match = re.search(r"_k([36])(?:_|$)", arm)
        if budget_match is None:
            raise RuntimeError(f"cannot parse budget from arm {arm}")
        budget = int(budget_match.group(1))
        baseline_name = f"semantic_topk_k{budget}"

        rows: list[dict[str, Any]] = []
        for parent_id, claim in sorted(claims.items()):
            case_id = case_id_by_parent[parent_id]
            selected_ids = claim["arms"][arm]
            baseline_ids = claim["arms"][baseline_name]
            row = evaluate_claim(
                selected_ids=selected_ids,
                pool=claim["pool"],
                gold_rows=mapped_gold[case_id],
                baseline_ids=baseline_ids,
            )
            row["original_claim_id"] = parent_id
            rows.append(row)
        per_claim_by_arm[arm] = rows
        metrics_by_arm[arm] = aggregate(rows)

    summaries: list[dict[str, Any]] = []
    for budget in BUDGETS:
        baseline_name = f"semantic_topk_k{budget}"
        baseline = metrics_by_arm[baseline_name]
        for cap in CAPS:
            for family in FAMILIES:
                correct_name = f"{family}_correct_k{budget}_cap_{cap}"
                correct = metrics_by_arm[correct_name]
                shuffled_name = (
                    f"{family}_shuffled_k{budget}_cap_{cap}"
                    if family in SHUFFLE_FAMILIES
                    else None
                )
                shuffled = (
                    metrics_by_arm[shuffled_name]
                    if shuffled_name is not None
                    else None
                )
                summaries.append(
                    {
                        "budget": budget,
                        "loss_cap": float(cap),
                        "family": family,
                        "correct_arm": correct_name,
                        "shuffled_arm": shuffled_name,
                        "baseline": baseline,
                        "correct": correct,
                        "shuffled": shuffled,
                        "correct_vs_baseline": delta(correct, baseline),
                        "correct_vs_shuffled": (
                            None
                            if shuffled is None
                            else delta(correct, shuffled)
                        ),
                        "screen": screen(correct, shuffled, baseline),
                    }
                )

    top = sorted(
        (
            {
                "arm": arm,
                "metrics": metric,
                "budget": int(re.search(r"_k([36])(?:_|$)", arm).group(1)),
            }
            for arm, metric in metrics_by_arm.items()
            if not arm.startswith("semantic_topk_")
        ),
        key=lambda row: (
            -(
                row["metrics"]["joint_group_coverage"]
                if row["metrics"]["joint_group_coverage"] is not None
                else -1.0
            ),
            -(
                row["metrics"]["decisive_recall"]
                if row["metrics"]["decisive_recall"] is not None
                else -1.0
            ),
            -(
                row["metrics"]["retrieval_child_decisive_rate"]
                if row["metrics"]["retrieval_child_decisive_rate"] is not None
                else -1.0
            ),
            row["metrics"]["annotated_hard_negative_selected"],
            row["arm"],
        ),
    )

    output = {
        "schema": "eb-composite-evidence-obligations-dev-v0-evaluation",
        "classification": "EXPOSED_DEVELOPMENT_MECHANISM_DIAGNOSTIC",
        "selection_sha256": sha256_file(args.selections),
        "gold_sha256": sha256_file(gold_path),
        "claim_count": len(claims),
        "baselines": {
            f"k{budget}": metrics_by_arm[f"semantic_topk_k{budget}"]
            for budget in BUDGETS
        },
        "family_summaries": summaries,
        "top_arms": top[:30],
        "per_claim_by_arm": per_claim_by_arm,
        "nonclaims": [
            "exposed development evaluation only",
            "retrieval-child decisive rate is retrieval attribution, not semantic proof",
            "gold does not influence selection generation",
            "no Gate field receives authority from this study",
            "first-stage retrieval is unchanged",
        ],
    }
    output["evaluation_sha256"] = hashlib.sha256(
        json.dumps(output, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    Path(args.out).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "baselines": output["baselines"],
                "family_summaries": [
                    {
                        "budget": row["budget"],
                        "loss_cap": row["loss_cap"],
                        "family": row["family"],
                        "screen": row["screen"],
                        "correct_vs_baseline": row["correct_vs_baseline"],
                        "correct_vs_shuffled": row["correct_vs_shuffled"],
                    }
                    for row in summaries
                ],
                "top_arms": output["top_arms"][:15],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
