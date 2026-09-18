from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")
ARMS = (
    "semantic_top3",
    "child_coverage",
    "subject_only",
    "form_only",
    "rc1_candidate",
    "reverse_order",
    "wrong_subject",
    "wrong_form",
    "wrong_both",
)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_selector(path: str | Path):
    spec = importlib.util.spec_from_file_location("frozen_rc1_selector", Path(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load selector")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def payload_for(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "parent_id": str(case["case_id"]),
        "children": [
            {
                "child_id": str(ch["child_id"]),
                "subject": ch.get("subject"),
                "expected_evidence_forms": list(ch.get("expected_evidence_forms", [])),
            }
            for ch in case["children"]
        ],
        "candidates": [
            {
                "candidate_id": str(row["candidate_id"]),
                "text": str(row["text"]),
                "semantic_scores": {
                    str(k): float(v) for k, v in row["semantic_scores"].items()
                },
            }
            for row in case["candidates"]
        ],
    }


def corpus_index(corpus: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(case["case_id"]): case for case in corpus["cases"]}


def wrong_subjects(case: dict[str, Any], corpus_case: dict[str, Any]) -> dict[str, str]:
    by_id = {str(row["candidate_id"]): row for row in corpus_case["candidates"]}
    out: dict[str, str] = {}
    for child in case["children"]:
        child_id = str(child["child_id"])
        target = str(child.get("subject") or "")
        target_tokens = TOKEN_RE.findall(target)
        best: tuple[float, str, int, str] | None = None
        if target_tokens:
            for candidate in case["candidates"]:
                meta = by_id[str(candidate["candidate_id"])]
                if not str(meta.get("design_role", "")).startswith("other_subject"):
                    continue
                tokens = TOKEN_RE.findall(str(candidate["text"]))
                n = len(target_tokens)
                for pos in range(0, max(0, len(tokens) - n + 1)):
                    window = " ".join(tokens[pos:pos+n])
                    if window.casefold() == target.casefold():
                        continue
                    ratio = difflib.SequenceMatcher(
                        None, target.casefold(), window.casefold()
                    ).ratio()
                    key = (ratio, str(candidate["candidate_id"]), -pos, window)
                    if best is None or key > best:
                        best = key
        out[child_id] = best[3] if best is not None else "__NO_MATCH_WRONG_SUBJECT__"
    return out


def wrong_forms(
    case: dict[str, Any],
    corpus_case: dict[str, Any],
    selector: Any,
) -> dict[str, str]:
    meta = {str(row["candidate_id"]): row for row in corpus_case["candidates"]}
    rows, children = selector._decorate(payload_for(case))
    fallback = [
        "authoritative_declaration",
        "event_record",
        "registry_entry",
        "measurement",
    ]
    out: dict[str, str] = {}
    for child_id, child in children.items():
        choices = []
        for row in rows:
            m = meta[str(row["candidate_id"])]
            intended = str(m.get("intended_form", "")).strip().lower()
            if (
                row["best_child"] == child_id
                and m.get("design_role") == "target_subject_other_form"
                and intended in selector.SUPPORTED_FORMS
                and intended not in child["expected_forms"]
            ):
                choices.append((float(row["best_score"]), str(row["candidate_id"]), intended))
        if choices:
            choices.sort(key=lambda x: (-x[0], x[1]))
            out[child_id] = choices[0][2]
            continue
        out[child_id] = next(
            form for form in fallback if form not in child["expected_forms"]
        )
    return out


def run_stages(
    selector: Any,
    payload: dict[str, Any],
    stages: tuple[str, ...],
) -> list[str]:
    selector._validate(payload)
    rows, children = selector._decorate(payload)
    ordered = selector._semantic_order(rows)
    selected = ordered[: selector.BUDGET]
    if "coverage" in stages:
        selected, _ = selector._coverage_repair(ordered, selected, list(children))
    for stage in stages:
        if stage in {"form", "subject"}:
            selected, _ = selector._repair_stage(
                rows=ordered,
                selected=selected,
                children=children,
                stage=stage,
            )
    return [str(row["candidate_id"]) for row in selected]


def mutate_payload(
    payload: dict[str, Any],
    *,
    wrong_subject: dict[str, str] | None = None,
    wrong_form: dict[str, str] | None = None,
) -> dict[str, Any]:
    value = json.loads(json.dumps(payload))
    for child in value["children"]:
        cid = str(child["child_id"])
        if wrong_subject is not None:
            child["subject"] = wrong_subject[cid]
        if wrong_form is not None:
            child["expected_evidence_forms"] = [wrong_form[cid]]
    return value


def select_all(
    fresh: dict[str, Any],
    corpus: dict[str, Any],
    selector: Any,
) -> dict[str, Any]:
    cidx = corpus_index(corpus)
    arms = {arm: [] for arm in ARMS}
    controls = {}
    for case in fresh["cases"]:
        cid = str(case["case_id"])
        payload = payload_for(case)
        wrong_subj = wrong_subjects(case, cidx[cid])
        wrong_form = wrong_forms(case, cidx[cid], selector)
        controls[cid] = {"wrong_subject": wrong_subj, "wrong_form": wrong_form}

        exact = selector.select(payload)
        selections = {
            "semantic_top3": run_stages(selector, payload, ()),
            "child_coverage": run_stages(selector, payload, ("coverage",)),
            "subject_only": run_stages(selector, payload, ("coverage", "subject")),
            "form_only": run_stages(selector, payload, ("coverage", "form")),
            "rc1_candidate": list(exact["selected_candidate_ids"]),
            "reverse_order": run_stages(selector, payload, ("coverage", "subject", "form")),
            "wrong_subject": run_stages(
                selector,
                mutate_payload(payload, wrong_subject=wrong_subj),
                ("coverage", "form", "subject"),
            ),
            "wrong_form": run_stages(
                selector,
                mutate_payload(payload, wrong_form=wrong_form),
                ("coverage", "form", "subject"),
            ),
            "wrong_both": run_stages(
                selector,
                mutate_payload(payload, wrong_subject=wrong_subj, wrong_form=wrong_form),
                ("coverage", "form", "subject"),
            ),
        }
        for arm, ids in selections.items():
            if len(ids) != selector.BUDGET or len(set(ids)) != selector.BUDGET:
                raise RuntimeError(f"{cid}/{arm}: invalid K")
            arms[arm].append({"case_id": cid, "selected_candidate_ids": ids})

    out = {
        "schema": "eb-obligation-selector-rc1-fresh-selections",
        "fresh_input_sha256": fresh["fresh_input_sha256"],
        "selector_budget": selector.BUDGET,
        "selector_semantic_loss_cap": selector.SEMANTIC_LOSS_CAP,
        "arms": arms,
        "negative_control_bindings": controls,
    }
    out["selections_sha256"] = sha256_json(out)
    return out


def grouped(summary_rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "parents": len(summary_rows),
        "complete_parent_coverage": sum(bool(x["complete_parent_coverage"]) for x in summary_rows),
        "required_children_covered": sum(int(x["required_children_covered"]) for x in summary_rows),
        "required_children_total": 2 * len(summary_rows),
        "unsafe": sum(int(x["unsafe"]) for x in summary_rows),
        "non_useful": sum(int(x["non_useful"]) for x in summary_rows),
        "required_selected": sum(int(x["required_selected"]) for x in summary_rows),
    }


def disposition(evaluation: dict[str, Any]) -> dict[str, Any]:
    summaries = evaluation["summaries"]
    per_arm = evaluation["per_arm"]

    def allm(arm: str) -> dict[str, int]:
        return summaries[arm]["ALL"]

    def group(arm: str, cats: set[str]) -> dict[str, int]:
        return grouped([x for x in per_arm[arm] if x["category"] in cats])

    sem = allm("semantic_top3")
    cand = allm("rc1_candidate")
    subj = allm("subject_only")
    wrong_both = allm("wrong_both")
    cand_subject = group("rc1_candidate", {"C2", "C3"})
    subj_subject = group("subject_only", {"C2", "C3"})
    wrong_subject = group("wrong_subject", {"C2", "C3"})
    cand_form = group("rc1_candidate", {"C4", "C5"})
    subj_form = group("subject_only", {"C4", "C5"})
    wrong_form = group("wrong_form", {"C4", "C5"})
    cand_c6 = group("rc1_candidate", {"C6"})
    sem_c6 = group("semantic_top3", {"C6"})

    support = {
        "overall_required_gain_ge_6": cand["required_children_covered"] - sem["required_children_covered"] >= 6,
        "overall_complete_gain_ge_4": cand["complete_parent_coverage"] - sem["complete_parent_coverage"] >= 4,
        "overall_unsafe_delta_le_1": cand["unsafe"] - sem["unsafe"] <= 1,
        "subject_vs_subject_only_required_not_worse_by_gt1": cand_subject["required_children_covered"] >= subj_subject["required_children_covered"] - 1,
        "subject_vs_subject_only_unsafe_not_worse_by_gt1": cand_subject["unsafe"] <= subj_subject["unsafe"] + 1,
        "correct_vs_wrong_subject_required_gain_ge_4": cand_subject["required_children_covered"] - wrong_subject["required_children_covered"] >= 4,
        "correct_vs_wrong_subject_unsafe_improvement_ge_3": wrong_subject["unsafe"] - cand_subject["unsafe"] >= 3,
        "form_increment": (
            cand_form["required_children_covered"] - subj_form["required_children_covered"] >= 2
            or cand_form["complete_parent_coverage"] - subj_form["complete_parent_coverage"] >= 1
        ),
        "form_unsafe_not_worse_by_gt1": cand_form["unsafe"] <= subj_form["unsafe"] + 1,
        "correct_vs_wrong_form_required_gain_ge_2": cand_form["required_children_covered"] - wrong_form["required_children_covered"] >= 2,
        "correct_vs_wrong_both_required_gain_ge_6": cand["required_children_covered"] - wrong_both["required_children_covered"] >= 6,
        "c6_required_no_loss": cand_c6["required_children_covered"] >= sem_c6["required_children_covered"],
        "c6_unsafe_delta_le_1": cand_c6["unsafe"] - sem_c6["unsafe"] <= 1,
    }

    falsifiers = {
        "candidate_loses_ge_4_required_vs_semantic": sem["required_children_covered"] - cand["required_children_covered"] >= 4,
        "candidate_adds_gt_4_unsafe_vs_semantic": cand["unsafe"] - sem["unsafe"] > 4,
        "wrong_subject_matches_or_beats_on_required_and_safety": (
            wrong_subject["required_children_covered"] >= cand_subject["required_children_covered"]
            and wrong_subject["unsafe"] <= cand_subject["unsafe"]
        ),
        "wrong_form_matches_or_beats_on_required_and_safety": (
            wrong_form["required_children_covered"] >= cand_form["required_children_covered"]
            and wrong_form["unsafe"] <= cand_form["unsafe"]
        ),
        "wrong_both_within_1_required_overall": abs(
            wrong_both["required_children_covered"] - cand["required_children_covered"]
        ) <= 1,
        "c6_loses_ge_2_required": sem_c6["required_children_covered"] - cand_c6["required_children_covered"] >= 2,
    }

    if all(support.values()):
        status = "SUPPORTED_COMBINED_RC1_FOR_FROZEN_RESEARCH_PROTOTYPE"
    elif any(falsifiers.values()):
        status = "FALSIFIED"
    else:
        subject_support = (
            cand_subject["required_children_covered"] >= subj_subject["required_children_covered"] - 1
            and wrong_subject["required_children_covered"] <= cand_subject["required_children_covered"] - 4
            and wrong_subject["unsafe"] >= cand_subject["unsafe"] + 3
        )
        form_only_failure = (
            not support["form_increment"]
            or not support["correct_vs_wrong_form_required_gain_ge_2"]
        )
        if subject_support and form_only_failure:
            status = "SUPPORTED_SUBJECT_ONLY; COMBINED_FORM_INCREMENT_NOT_REPRODUCED"
        else:
            status = "INCONCLUSIVE"

    return {
        "status": status,
        "support_checks": support,
        "falsifiers": falsifiers,
        "metrics": {
            "semantic_all": sem,
            "candidate_all": cand,
            "subject_only_all": subj,
            "wrong_both_all": wrong_both,
            "candidate_subject_C2_C3": cand_subject,
            "subject_only_C2_C3": subj_subject,
            "wrong_subject_C2_C3": wrong_subject,
            "candidate_form_C4_C5": cand_form,
            "subject_only_C4_C5": subj_form,
            "wrong_form_C4_C5": wrong_form,
            "candidate_C6": cand_c6,
            "semantic_C6": sem_c6,
        },
    }


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("select")
    s.add_argument("--fresh", required=True)
    s.add_argument("--corpus", required=True)
    s.add_argument("--selector", required=True)
    s.add_argument("--out", required=True)

    d = sub.add_parser("disposition")
    d.add_argument("--evaluation", required=True)
    d.add_argument("--out", required=True)

    args = p.parse_args()
    if args.cmd == "select":
        out = select_all(load_json(args.fresh), load_json(args.corpus), load_selector(args.selector))
    else:
        out = disposition(load_json(args.evaluation))
    Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
