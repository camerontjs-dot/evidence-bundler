from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

CAPS = ("0.01", "0.03", "0.05", "0.10")
BUDGET = 3

ARM_NAMES = (
    "semantic_top3",
    "child_coverage",
    "subject_only",
    "wrong_subject_only",
    "form_only",
    "wrong_form_only",
    "subject_then_form",
    "form_then_subject",
    "strict_subject_and_form",
    "correct_subject_then_wrong_form",
    "wrong_subject_then_correct_form",
    "wrong_subject_then_wrong_form",
    "strict_correct_subject_wrong_form",
    "strict_wrong_subject_correct_form",
    "strict_wrong_subject_wrong_form",
    "subject_no_coverage",
    "form_no_coverage",
    "subject_then_form_no_coverage",
    "strict_subject_and_form_no_coverage",
)


def canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def semantic_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            -float(row["best_score"]),
            str(row["candidate_id"]),
        ),
    )


def exact_contains(value: str | None, text: str) -> float:
    if not value:
        return 0.0
    return float(value.lower() in text.lower())


def child_subject(child: dict[str, Any], *, wrong: bool) -> str | None:
    if wrong:
        return child.get("wrong_subject")
    return child.get("subject") or child.get("inherited_subject")


def subject_score(
    candidate: dict[str, Any],
    child: dict[str, Any],
    *,
    wrong: bool,
) -> float:
    return exact_contains(
        child_subject(child, wrong=wrong),
        str(candidate["text"]),
    )


def form_score(
    candidate: dict[str, Any],
    child: dict[str, Any],
    *,
    wrong: bool,
) -> float:
    target = child["wrong_form"] if wrong else child["expected_form"]
    return float(str(target) in {str(value) for value in candidate["forms"]})


def descriptor_score(
    candidate: dict[str, Any],
    child: dict[str, Any],
    field: str,
    *,
    wrong_subject: bool = False,
    wrong_form: bool = False,
) -> float:
    if field == "subject":
        return subject_score(candidate, child, wrong=wrong_subject)
    if field == "form":
        return form_score(candidate, child, wrong=wrong_form)
    if field == "strict_subject_and_form":
        subject = subject_score(candidate, child, wrong=wrong_subject)
        form = form_score(candidate, child, wrong=wrong_form)
        return float(subject == 1.0 and form == 1.0)
    raise ValueError(field)


def row_map(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["candidate_id"]): row
        for row in case["candidates"]
    }


def selected_rows(
    case: dict[str, Any],
    ids: list[str],
) -> list[dict[str, Any]]:
    by_id = row_map(case)
    return [by_id[str(candidate_id)] for candidate_id in ids]


def validate_selection(
    case: dict[str, Any],
    selected: list[dict[str, Any]],
) -> None:
    if len(selected) != BUDGET:
        raise RuntimeError(
            f"{case['case_id']}: expected K={BUDGET}, got {len(selected)}"
        )
    ids = [str(row["candidate_id"]) for row in selected]
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"{case['case_id']}: duplicate selection")
    pool = {str(row["candidate_id"]) for row in case["candidates"]}
    if not set(ids) <= pool:
        raise RuntimeError(f"{case['case_id']}: out-of-pool selection")


def repair(
    *,
    case: dict[str, Any],
    selected: list[dict[str, Any]],
    cap: float,
    field: str,
    wrong_subject: bool = False,
    wrong_form: bool = False,
    preserve_child_coverage: bool = True,
) -> list[dict[str, Any]]:
    current = semantic_order(list(selected))
    child_by_id = {
        str(child["child_id"]): child
        for child in case["children"]
    }

    for child_id in [
        str(child["child_id"])
        for child in case["children"]
    ]:
        child = child_by_id[child_id]
        owned = [
            row for row in current
            if str(row["best_child"]) == child_id
        ]
        outside = [
            row for row in case["candidates"]
            if row not in current
            and str(row["best_child"]) == child_id
        ]
        if not owned or not outside:
            continue

        def score(
            row: dict[str, Any],
            *,
            bound_child: dict[str, Any] = child,
        ) -> float:
            return descriptor_score(
                row,
                bound_child,
                field,
                wrong_subject=wrong_subject,
                wrong_form=wrong_form,
            )

        victim = min(
            owned,
            key=lambda row: (
                score(row),
                float(row["best_score"]),
                str(row["candidate_id"]),
            ),
        )
        challenger = max(
            outside,
            key=lambda row: (
                score(row),
                float(row["best_score"]),
                str(row["candidate_id"]),
            ),
        )

        if score(challenger) <= score(victim) + 1e-12:
            continue

        loss = (
            float(victim["best_score"])
            - float(challenger["best_score"])
        )
        if loss > cap + 1e-12:
            continue

        trial = [
            row for row in current
            if row is not victim
        ] + [challenger]

        if preserve_child_coverage:
            represented = {
                str(row["best_child"])
                for row in trial
            }
            if not set(child_by_id) <= represented:
                continue

        current = semantic_order(trial)

    validate_selection(case, current)
    return current


def sequence_repairs(
    *,
    case: dict[str, Any],
    selected: list[dict[str, Any]],
    cap: float,
    sequence: list[tuple[str, bool, bool]],
    preserve_child_coverage: bool,
) -> list[dict[str, Any]]:
    current = list(selected)
    for field, wrong_subject, wrong_form in sequence:
        current = repair(
            case=case,
            selected=current,
            cap=cap,
            field=field,
            wrong_subject=wrong_subject,
            wrong_form=wrong_form,
            preserve_child_coverage=preserve_child_coverage,
        )
    return current


def ids(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row["candidate_id"]) for row in rows]


def make_arms(
    case: dict[str, Any],
    cap_label: str,
) -> dict[str, list[str]]:
    cap = float(cap_label)
    frozen = case["arms"][cap_label]

    semantic = selected_rows(
        case,
        list(frozen["semantic_top3"]),
    )
    coverage = selected_rows(
        case,
        list(frozen["child_coverage"]),
    )
    validate_selection(case, semantic)
    validate_selection(case, coverage)

    subject = repair(
        case=case,
        selected=coverage,
        cap=cap,
        field="subject",
    )
    wrong_subject = repair(
        case=case,
        selected=coverage,
        cap=cap,
        field="subject",
        wrong_subject=True,
    )
    form = repair(
        case=case,
        selected=coverage,
        cap=cap,
        field="form",
    )
    wrong_form = repair(
        case=case,
        selected=coverage,
        cap=cap,
        field="form",
        wrong_form=True,
    )

    subject_then_form = sequence_repairs(
        case=case,
        selected=coverage,
        cap=cap,
        sequence=[
            ("subject", False, False),
            ("form", False, False),
        ],
        preserve_child_coverage=True,
    )
    form_then_subject = sequence_repairs(
        case=case,
        selected=coverage,
        cap=cap,
        sequence=[
            ("form", False, False),
            ("subject", False, False),
        ],
        preserve_child_coverage=True,
    )

    strict = repair(
        case=case,
        selected=coverage,
        cap=cap,
        field="strict_subject_and_form",
    )

    correct_subject_wrong_form = sequence_repairs(
        case=case,
        selected=coverage,
        cap=cap,
        sequence=[
            ("subject", False, False),
            ("form", False, True),
        ],
        preserve_child_coverage=True,
    )
    wrong_subject_correct_form = sequence_repairs(
        case=case,
        selected=coverage,
        cap=cap,
        sequence=[
            ("subject", True, False),
            ("form", False, False),
        ],
        preserve_child_coverage=True,
    )
    wrong_both = sequence_repairs(
        case=case,
        selected=coverage,
        cap=cap,
        sequence=[
            ("subject", True, False),
            ("form", False, True),
        ],
        preserve_child_coverage=True,
    )

    strict_correct_subject_wrong_form = repair(
        case=case,
        selected=coverage,
        cap=cap,
        field="strict_subject_and_form",
        wrong_form=True,
    )
    strict_wrong_subject_correct_form = repair(
        case=case,
        selected=coverage,
        cap=cap,
        field="strict_subject_and_form",
        wrong_subject=True,
    )
    strict_wrong_both = repair(
        case=case,
        selected=coverage,
        cap=cap,
        field="strict_subject_and_form",
        wrong_subject=True,
        wrong_form=True,
    )

    subject_no_coverage = repair(
        case=case,
        selected=semantic,
        cap=cap,
        field="subject",
        preserve_child_coverage=False,
    )
    form_no_coverage = repair(
        case=case,
        selected=semantic,
        cap=cap,
        field="form",
        preserve_child_coverage=False,
    )
    subject_form_no_coverage = sequence_repairs(
        case=case,
        selected=semantic,
        cap=cap,
        sequence=[
            ("subject", False, False),
            ("form", False, False),
        ],
        preserve_child_coverage=False,
    )
    strict_no_coverage = repair(
        case=case,
        selected=semantic,
        cap=cap,
        field="strict_subject_and_form",
        preserve_child_coverage=False,
    )

    result = {
        "semantic_top3": ids(semantic),
        "child_coverage": ids(coverage),
        "subject_only": ids(subject),
        "wrong_subject_only": ids(wrong_subject),
        "form_only": ids(form),
        "wrong_form_only": ids(wrong_form),
        "subject_then_form": ids(subject_then_form),
        "form_then_subject": ids(form_then_subject),
        "strict_subject_and_form": ids(strict),
        "correct_subject_then_wrong_form": ids(
            correct_subject_wrong_form
        ),
        "wrong_subject_then_correct_form": ids(
            wrong_subject_correct_form
        ),
        "wrong_subject_then_wrong_form": ids(wrong_both),
        "strict_correct_subject_wrong_form": ids(
            strict_correct_subject_wrong_form
        ),
        "strict_wrong_subject_correct_form": ids(
            strict_wrong_subject_correct_form
        ),
        "strict_wrong_subject_wrong_form": ids(
            strict_wrong_both
        ),
        "subject_no_coverage": ids(subject_no_coverage),
        "form_no_coverage": ids(form_no_coverage),
        "subject_then_form_no_coverage": ids(
            subject_form_no_coverage
        ),
        "strict_subject_and_form_no_coverage": ids(
            strict_no_coverage
        ),
    }
    if set(result) != set(ARM_NAMES):
        raise RuntimeError("arm set drift")
    return result


def select(v1: dict[str, Any]) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    for source_case in v1["cases"]:
        case = {
            "case_id": source_case["case_id"],
            "category": source_case["category"],
            "parent_text": source_case["parent_text"],
            "children": source_case["children"],
            "candidates": source_case["candidates"],
            "source_pool_sha256": sha256_json(
                source_case["candidates"]
            ),
            "arms": {},
        }
        for cap in CAPS:
            case["arms"][cap] = make_arms(
                source_case,
                cap,
            )
        cases.append(case)

    payload = {
        "schema": "eb-subject-form-interaction-v2-selections",
        "classification": (
            "EXPOSED_INTERACTION_PRESSURE_NOT_FRESH_QUALIFICATION"
        ),
        "v1_selection_sha256": sha256_json(v1),
        "caps": [float(cap) for cap in CAPS],
        "budget": BUDGET,
        "arms": list(ARM_NAMES),
        "case_count": len(cases),
        "cases": cases,
        "nonclaims": [
            "no semantic model was rerun",
            "no gold-bearing V1 source was required for selection",
            "candidate texts and semantic scores are inherited unchanged",
            "this is exposed interaction pressure only",
        ],
    }
    payload["output_sha256"] = sha256_json(payload)
    return payload


def load_v1_module(path: str | Path):
    spec = importlib.util.spec_from_file_location(
        "v1_targeted_stress_frozen",
        Path(path),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load V1 evaluator source")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def gold_index(v1_module: Any) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for case in v1_module.build_cases():
        out[str(case.case_id)] = {
            str(candidate.candidate_id): {
                "gold_class": str(candidate.gold_class),
                "required_for": [
                    str(value)
                    for value in candidate.required_for
                ],
            }
            for candidate in case.candidates
        }
    return out


def evaluate_arm(
    case: dict[str, Any],
    selected_ids: list[str],
    gold: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    child_ids = {
        str(child["child_id"])
        for child in case["children"]
    }
    required_covered: set[str] = set()
    classes: list[str] = []

    for candidate_id in selected_ids:
        row = gold[str(candidate_id)]
        required_covered.update(row["required_for"])
        classes.append(str(row["gold_class"]))

    return {
        "complete_parent_coverage": (
            child_ids <= required_covered
        ),
        "required_children_covered": len(required_covered),
        "unsafe": sum(
            value == "UNSAFE_OR_MISLEADING"
            for value in classes
        ),
        "non_useful": sum(
            value not in {"REQUIRED", "REDUNDANT"}
            for value in classes
        ),
        "required_selected": sum(
            value == "REQUIRED"
            for value in classes
        ),
        "selected_ids": list(selected_ids),
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "parents": len(rows),
        "complete_parent_coverage": sum(
            bool(row["complete_parent_coverage"])
            for row in rows
        ),
        "required_children_covered": sum(
            int(row["required_children_covered"])
            for row in rows
        ),
        "required_children_total": 2 * len(rows),
        "unsafe": sum(int(row["unsafe"]) for row in rows),
        "non_useful": sum(
            int(row["non_useful"])
            for row in rows
        ),
        "required_selected": sum(
            int(row["required_selected"])
            for row in rows
        ),
    }


def delta(
    left: dict[str, int],
    right: dict[str, int],
) -> dict[str, int]:
    return {
        key: int(left[key]) - int(right[key])
        for key in (
            "complete_parent_coverage",
            "required_children_covered",
            "unsafe",
            "non_useful",
            "required_selected",
        )
    }


def evaluate(
    selections: dict[str, Any],
    *,
    v1_module_path: str | Path,
) -> dict[str, Any]:
    v1_module = load_v1_module(v1_module_path)
    gold_by_case = gold_index(v1_module)

    per_case: list[dict[str, Any]] = []
    categories = sorted(
        {
            str(case["category"])
            for case in selections["cases"]
        }
    )

    for case in selections["cases"]:
        case_id = str(case["case_id"])
        gold = gold_by_case[case_id]
        cap_rows: dict[str, Any] = {}
        for cap in CAPS:
            arm_rows = {
                arm: evaluate_arm(
                    case,
                    list(case["arms"][cap][arm]),
                    gold,
                )
                for arm in ARM_NAMES
            }
            cap_rows[cap] = arm_rows
        per_case.append(
            {
                "case_id": case_id,
                "category": case["category"],
                "caps": cap_rows,
            }
        )

    summaries: dict[str, Any] = {}
    for cap in CAPS:
        summaries[cap] = {}
        for category in categories + ["ALL"]:
            subset = [
                row for row in per_case
                if category == "ALL"
                or row["category"] == category
            ]
            summaries[cap][category] = {
                arm: aggregate(
                    [
                        row["caps"][cap][arm]
                        for row in subset
                    ]
                )
                for arm in ARM_NAMES
            }

    primary_categories = {
        "subject": (
            "EXPLICIT_SUBJECT_CONFLICT",
            "INHERITED_SUBJECT_CONFLICT",
        ),
        "form": ("FORM_CONFLICT",),
        "starvation": ("STARVATION",),
    }

    interaction: dict[str, Any] = {}
    for cap in CAPS:
        all_rows = summaries[cap]["ALL"]
        interaction[cap] = {
            "subject_vs_coverage": delta(
                all_rows["subject_only"],
                all_rows["child_coverage"],
            ),
            "form_vs_coverage": delta(
                all_rows["form_only"],
                all_rows["child_coverage"],
            ),
            "subject_then_form_vs_subject": delta(
                all_rows["subject_then_form"],
                all_rows["subject_only"],
            ),
            "subject_then_form_vs_form": delta(
                all_rows["subject_then_form"],
                all_rows["form_only"],
            ),
            "form_then_subject_vs_subject_then_form": delta(
                all_rows["form_then_subject"],
                all_rows["subject_then_form"],
            ),
            "strict_vs_sequential": delta(
                all_rows["strict_subject_and_form"],
                all_rows["subject_then_form"],
            ),
            "combination_vs_mixed_wrong_subject": delta(
                all_rows["subject_then_form"],
                all_rows["wrong_subject_then_correct_form"],
            ),
            "combination_vs_mixed_wrong_form": delta(
                all_rows["subject_then_form"],
                all_rows["correct_subject_then_wrong_form"],
            ),
            "combination_vs_wrong_both": delta(
                all_rows["subject_then_form"],
                all_rows["wrong_subject_then_wrong_form"],
            ),
            "staged_vs_no_coverage": delta(
                all_rows["subject_then_form"],
                all_rows["subject_then_form_no_coverage"],
            ),
        }

    focused: dict[str, Any] = {}
    for cap in CAPS:
        focused[cap] = {}
        for label, group in primary_categories.items():
            arms = {}
            for arm in ARM_NAMES:
                rows: list[dict[str, Any]] = []
                for category in group:
                    rows.extend(
                        [
                            row["caps"][cap][arm]
                            for row in per_case
                            if row["category"] == category
                        ]
                    )
                arms[arm] = aggregate(rows)
            focused[cap][label] = arms

    output = {
        "schema": "eb-subject-form-interaction-v2-evaluation",
        "classification": (
            "EXPOSED_INTERACTION_PRESSURE_NOT_FRESH_QUALIFICATION"
        ),
        "selection_sha256": sha256_json(selections),
        "summaries": summaries,
        "focused": focused,
        "interaction_deltas": interaction,
        "per_case": per_case,
        "nonclaims": [
            "V2 reuses the V1 adversarial candidate world",
            "no fresh generalization claim is permitted",
            "correct-vs-wrong controls test causal field identity",
            "PR #111 remains the independent qualification path",
        ],
    }
    output["evaluation_sha256"] = sha256_json(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("select", "evaluate"),
        required=True,
    )
    parser.add_argument("--v1-selection")
    parser.add_argument("--selection-in")
    parser.add_argument("--selection-out")
    parser.add_argument("--v1-module")
    parser.add_argument("--evaluation-out")
    args = parser.parse_args()

    if args.mode == "select":
        if not args.v1_selection or not args.selection_out:
            raise SystemExit(
                "--v1-selection and --selection-out are required"
            )
        source = load_json(args.v1_selection)
        result = select(source)
        Path(args.selection_out).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "output_sha256": result["output_sha256"],
                    "case_count": result["case_count"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if (
        not args.selection_in
        or not args.v1_module
        or not args.evaluation_out
    ):
        raise SystemExit(
            "--selection-in, --v1-module, and "
            "--evaluation-out are required"
        )

    selections = load_json(args.selection_in)
    result = evaluate(
        selections,
        v1_module_path=args.v1_module,
    )
    Path(args.evaluation_out).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "evaluation_sha256": result["evaluation_sha256"],
                "interaction_deltas": result["interaction_deltas"],
                "focused": result["focused"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
