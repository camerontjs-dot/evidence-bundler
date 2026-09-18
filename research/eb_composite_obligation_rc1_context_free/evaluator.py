from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

BUDGET = 3


class EvaluationError(RuntimeError):
    pass


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


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationError(message)


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
        "required_selected": sum(
            int(row["required_selected"])
            for row in rows
        ),
        "unsafe": sum(int(row["unsafe"]) for row in rows),
        "non_useful": sum(
            int(row["non_useful"])
            for row in rows
        ),
    }


def evaluate(
    fresh_input: dict[str, Any],
    selections: dict[str, Any],
    gold: dict[str, Any],
) -> dict[str, Any]:
    fresh_by_case = {
        str(case["case_id"]): case
        for case in fresh_input["cases"]
    }
    gold_by_case = {
        str(case["case_id"]): case
        for case in gold["cases"]
    }
    ensure(
        set(fresh_by_case) == set(gold_by_case),
        "fresh/gold case set mismatch",
    )

    arms = selections.get("arms")
    ensure(isinstance(arms, dict) and arms, "selections must contain arms")

    per_arm: dict[str, list[dict[str, Any]]] = {}
    for arm_id, arm_rows in arms.items():
        ensure(
            isinstance(arm_rows, list)
            and len(arm_rows) == len(fresh_by_case),
            f"{arm_id}: expected one row per case",
        )
        arm_by_case = {
            str(row["case_id"]): row
            for row in arm_rows
        }
        ensure(
            set(arm_by_case) == set(fresh_by_case),
            f"{arm_id}: case set mismatch",
        )

        evaluated: list[dict[str, Any]] = []
        for case_id in sorted(fresh_by_case):
            fresh_case = fresh_by_case[case_id]
            gold_case = gold_by_case[case_id]
            selected_ids = list(
                map(
                    str,
                    arm_by_case[case_id]["selected_candidate_ids"],
                )
            )
            ensure(
                len(selected_ids) == BUDGET,
                f"{arm_id}/{case_id}: K must be {BUDGET}",
            )
            ensure(
                len(selected_ids) == len(set(selected_ids)),
                f"{arm_id}/{case_id}: duplicate selected ID",
            )
            pool_ids = {
                str(row["candidate_id"])
                for row in fresh_case["candidates"]
            }
            ensure(
                set(selected_ids) <= pool_ids,
                f"{arm_id}/{case_id}: out-of-pool selection",
            )

            gold_map = {
                str(row["candidate_id"]): row
                for row in gold_case["candidates"]
            }
            child_ids = {
                str(row["child_id"])
                for row in fresh_case["children"]
            }
            required_children: set[str] = set()
            classes: list[str] = []
            for candidate_id in selected_ids:
                row = gold_map[candidate_id]
                gold_class = str(row["gold_class"])
                classes.append(gold_class)
                if gold_class == "REQUIRED":
                    required_children.update(
                        map(str, row["required_for"])
                    )

            evaluated.append(
                {
                    "case_id": case_id,
                    "category": fresh_case["category"],
                    "selected_candidate_ids": selected_ids,
                    "complete_parent_coverage": (
                        child_ids <= required_children
                    ),
                    "required_children_covered": len(
                        child_ids & required_children
                    ),
                    "required_selected": sum(
                        value == "REQUIRED"
                        for value in classes
                    ),
                    "unsafe": sum(
                        value == "UNSAFE_OR_MISLEADING"
                        for value in classes
                    ),
                    "non_useful": sum(
                        value
                        in {
                            "REDUNDANT",
                            "DISTRACTOR",
                            "UNSAFE_OR_MISLEADING",
                        }
                        for value in classes
                    ),
                }
            )
        per_arm[str(arm_id)] = evaluated

    categories = sorted(
        {
            str(case["category"])
            for case in fresh_input["cases"]
        }
    )
    summaries: dict[str, Any] = {}
    for arm_id, rows in per_arm.items():
        summaries[arm_id] = {
            "ALL": aggregate(rows)
        }
        for category in categories:
            summaries[arm_id][category] = aggregate(
                [
                    row
                    for row in rows
                    if row["category"] == category
                ]
            )

    output = {
        "schema": "eb-composite-obligation-rc1-evaluation",
        "classification": "FRESH_CONTEXT_FREE_FIXED_POOL_EVALUATION",
        "fresh_input_internal_sha256": fresh_input.get(
            "fresh_input_sha256"
        ),
        "gold_internal_sha256": gold.get("gold_sha256"),
        "selection_internal_sha256": selections.get(
            "selections_sha256"
        ),
        "arm_ids": sorted(per_arm),
        "summaries": summaries,
        "per_arm": per_arm,
    }
    output["evaluation_sha256"] = sha256_json(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh-input", required=True)
    parser.add_argument("--selections", required=True)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    fresh = load_json(args.fresh_input)
    selections = load_json(args.selections)
    gold = load_json(args.gold)

    ensure(
        selections.get("fresh_input_sha256")
        in {
            sha256_file(args.fresh_input),
            fresh.get("fresh_input_sha256"),
        },
        "selection fresh-input binding mismatch",
    )
    ensure(
        gold.get("source_fresh_input_sha256")
        in {
            sha256_file(args.fresh_input),
            fresh.get("fresh_input_sha256"),
        },
        "gold fresh-input binding mismatch",
    )

    output = evaluate(fresh, selections, gold)
    Path(args.out).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "evaluation_sha256": output["evaluation_sha256"],
                "arm_ids": output["arm_ids"],
                "summaries": output["summaries"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
