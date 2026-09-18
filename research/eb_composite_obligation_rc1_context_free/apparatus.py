from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

CATEGORIES = tuple(f"C{i}" for i in range(1, 7))
GOLD_CLASSES = {
    "REQUIRED",
    "USEFUL_DISTINCT",
    "REDUNDANT",
    "DISTRACTOR",
    "UNSAFE_OR_MISLEADING",
    "UNRESOLVED",
}
INTENDED_FORMS = {
    "document_text",
    "authoritative_declaration",
    "event_record",
    "registry_entry",
    "measurement",
}
DESIGN_ROLES = {
    "target_subject_target_form",
    "target_subject_other_form",
    "other_subject_target_form",
    "other_subject_other_form",
    "neutral_distractor",
    "redundant_target",
}
ACTIONABLE_FORMS = {
    "authoritative_declaration",
    "event_record",
    "registry_entry",
    "measurement",
}
MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"
MODEL_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"


class ApparatusError(RuntimeError):
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


def write_json(path: str | Path, value: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ApparatusError(message)


def _validate_claim_case(case: dict[str, Any], category: str) -> None:
    expected_case_prefix = f"{category}-"
    case_id = str(case.get("case_id", ""))
    ensure(case_id.startswith(expected_case_prefix), f"bad case id: {case_id}")
    ensure(case.get("logic") == "all_of", f"{case_id}: logic must be all_of")
    parent = case.get("parent_text")
    ensure(isinstance(parent, str) and parent.strip(), f"{case_id}: parent_text")
    children = case.get("children")
    ensure(isinstance(children, list) and len(children) == 2, f"{case_id}: two children")
    seen: set[str] = set()
    parent_inherited = 0
    for index, child in enumerate(children):
        child_id = str(child.get("child_id", ""))
        suffix = "A" if index == 0 else "B"
        ensure(child_id == f"{case_id}-{suffix}", f"{case_id}: child id/order drift")
        ensure(child_id not in seen, f"{case_id}: duplicate child")
        seen.add(child_id)
        text = child.get("child_text")
        anchor = child.get("subject_anchor")
        source = child.get("subject_source")
        ensure(isinstance(text, str) and text.strip(), f"{child_id}: child_text")
        ensure(isinstance(anchor, str) and anchor.strip(), f"{child_id}: subject_anchor")
        ensure(source in {"child", "parent"}, f"{child_id}: subject_source")
        if source == "child":
            ensure(anchor in text, f"{child_id}: child subject not exact substring")
        else:
            ensure(anchor in parent, f"{child_id}: parent subject not exact substring")
            ensure(anchor not in text, f"{child_id}: inherited subject is not elliptical")
            parent_inherited += 1

    if category == "C2":
        ensure(
            all(child["subject_source"] == "child" for child in children),
            f"{case_id}: C2 requires explicit child subjects",
        )
    if category == "C3":
        ensure(parent_inherited >= 1, f"{case_id}: C3 requires inherited subject")


def combine_claims(parts: list[str], out: str) -> None:
    combined: list[dict[str, Any]] = []
    seen_cases: set[str] = set()
    seen_children: set[str] = set()

    for part_path in parts:
        part = load_json(part_path)
        category = str(part.get("category_id", ""))
        ensure(category in CATEGORIES, f"{part_path}: invalid category")
        cases = part.get("cases")
        ensure(isinstance(cases, list) and len(cases) == 4, f"{category}: expected four cases")
        for case in cases:
            _validate_claim_case(case, category)
            case_id = str(case["case_id"])
            ensure(case_id not in seen_cases, f"duplicate case {case_id}")
            seen_cases.add(case_id)
            for child in case["children"]:
                child_id = str(child["child_id"])
                ensure(child_id not in seen_children, f"duplicate child {child_id}")
                seen_children.add(child_id)
            row = dict(case)
            row["category"] = category
            combined.append(row)

    counts = Counter(row["category"] for row in combined)
    ensure(set(counts) == set(CATEGORIES), f"missing categories: {counts}")
    ensure(all(counts[cat] == 4 for cat in CATEGORIES), f"category imbalance: {counts}")
    ensure(len(combined) == 24, f"expected 24 cases, got {len(combined)}")
    ensure(len(seen_children) == 48, f"expected 48 children, got {len(seen_children)}")

    combined.sort(key=lambda row: row["case_id"])
    payload = {
        "schema": "eb-composite-obligation-rc1-claims",
        "classification": "FRESH_CONTEXT_FREE_CLAIMS",
        "case_count": len(combined),
        "child_count": len(seen_children),
        "cases": combined,
    }
    payload["claims_sha256"] = sha256_json(payload)
    write_json(out, payload)


def derive_descriptors(claims_path: str, out: str) -> None:
    from proposition_authoring.claim_profile import build_claim_profile
    from proposition_authoring.model import AuthoringRequest

    claims = load_json(claims_path)
    cases_out: list[dict[str, Any]] = []
    for case in claims["cases"]:
        case_out = {key: value for key, value in case.items() if key != "children"}
        children_out: list[dict[str, Any]] = []
        for child in case["children"]:
            child_id = str(child["child_id"])
            request = AuthoringRequest(
                handoff_id=f"fresh-rc1:{child_id}",
                producer_id="eb-composite-obligation-rc1-context-free",
                producer_version="1",
                work_id=f"fresh-rc1-work:{child_id}",
                root_id=child_id,
                root_text=str(child["child_text"]),
            )
            profile = build_claim_profile(request)
            forms = [
                str(value)
                for value in profile.get("expected_evidence_forms", [])
                if isinstance(value, (str, int, float))
            ]
            child_out = dict(child)
            child_out["expected_evidence_forms"] = forms
            child_out["claim_profile_sha256"] = profile.get("profile_sha256")
            child_out["claim_profile_claim_families"] = profile.get("claim_families")
            children_out.append(child_out)
        case_out["children"] = children_out
        cases_out.append(case_out)

    payload = {
        "schema": "eb-composite-obligation-rc1-claims-descriptors",
        "classification": "FRESH_CONTEXT_FREE_DESCRIPTORS",
        "source_claims_sha256": sha256_file(claims_path),
        "claim_profile_authority": "e29a165b682d060f5dc2a0f3c7d64a7f29b172b4",
        "cases": cases_out,
    }
    payload["descriptors_sha256"] = sha256_json(payload)
    write_json(out, payload)


def split_categories(input_path: str, out_dir: str) -> None:
    payload = load_json(input_path)
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    for category in CATEGORIES:
        cases = [row for row in payload["cases"] if row["category"] == category]
        ensure(len(cases) == 4, f"{category}: split expected four cases")
        write_json(
            root / f"{category}.json",
            {
                "schema": "eb-composite-obligation-rc1-category-descriptors",
                "category_id": category,
                "cases": cases,
            },
        )


def _validate_corpus_case(
    case: dict[str, Any],
    descriptor_case: dict[str, Any],
) -> None:
    case_id = str(case.get("case_id", ""))
    ensure(case_id == descriptor_case["case_id"], f"corpus case mismatch: {case_id}")
    candidates = case.get("candidates")
    ensure(isinstance(candidates, list) and len(candidates) == 10, f"{case_id}: exactly 10 candidates")
    target_subjects = {
        str(child["subject_anchor"])
        for child in descriptor_case["children"]
    }
    ids: set[str] = set()
    roles = Counter()
    for index, row in enumerate(candidates, start=1):
        candidate_id = str(row.get("candidate_id", ""))
        ensure(candidate_id == f"{case_id}-P{index:02d}", f"{case_id}: candidate id/order")
        ensure(candidate_id not in ids, f"{case_id}: duplicate candidate")
        ids.add(candidate_id)
        text = row.get("text")
        intended_form = row.get("intended_form")
        design_role = row.get("design_role")
        ensure(isinstance(text, str) and text.strip(), f"{candidate_id}: empty text")
        ensure(intended_form in INTENDED_FORMS, f"{candidate_id}: intended form")
        ensure(design_role in DESIGN_ROLES, f"{candidate_id}: design role")
        roles[design_role] += 1
        if design_role.startswith("target_subject"):
            ensure(
                any(subject in text for subject in target_subjects),
                f"{candidate_id}: target-subject role lacks frozen subject anchor",
            )

    category = str(descriptor_case["category"])
    if category in {"C2", "C3"}:
        ensure(
            roles["other_subject_target_form"] + roles["other_subject_other_form"] >= 2,
            f"{case_id}: insufficient wrong-subject geometry",
        )
    if category == "C4":
        ensure(
            roles["target_subject_other_form"] >= 2,
            f"{case_id}: insufficient wrong-form geometry",
        )
    if category == "C5":
        for role in (
            "target_subject_target_form",
            "target_subject_other_form",
            "other_subject_target_form",
            "other_subject_other_form",
        ):
            ensure(roles[role] >= 1, f"{case_id}: missing crossed role {role}")


def combine_corpus(parts: list[str], descriptors_path: str, out: str) -> None:
    descriptors = load_json(descriptors_path)
    descriptor_by_case = {
        str(case["case_id"]): case
        for case in descriptors["cases"]
    }
    combined: list[dict[str, Any]] = []
    seen_candidate_ids: set[str] = set()
    seen_cases: set[str] = set()

    for part_path in parts:
        part = load_json(part_path)
        category = str(part.get("category_id", ""))
        ensure(category in CATEGORIES, f"{part_path}: bad category")
        cases = part.get("cases")
        ensure(isinstance(cases, list) and len(cases) == 4, f"{category}: four corpus cases")
        for case in cases:
            case_id = str(case.get("case_id", ""))
            ensure(case_id in descriptor_by_case, f"unknown corpus case {case_id}")
            ensure(
                descriptor_by_case[case_id]["category"] == category,
                f"{case_id}: category drift",
            )
            ensure(case_id not in seen_cases, f"duplicate corpus case {case_id}")
            seen_cases.add(case_id)
            _validate_corpus_case(case, descriptor_by_case[case_id])
            for candidate in case["candidates"]:
                candidate_id = str(candidate["candidate_id"])
                ensure(
                    candidate_id not in seen_candidate_ids,
                    f"global duplicate candidate {candidate_id}",
                )
                seen_candidate_ids.add(candidate_id)
            row = dict(case)
            row["category"] = category
            combined.append(row)

    ensure(len(combined) == 24, f"expected 24 corpus cases, got {len(combined)}")
    ensure(len(seen_candidate_ids) == 240, f"expected 240 candidates, got {len(seen_candidate_ids)}")
    combined.sort(key=lambda row: row["case_id"])
    payload = {
        "schema": "eb-composite-obligation-rc1-corpus",
        "classification": "FRESH_CONTEXT_FREE_CORPUS",
        "source_descriptors_sha256": sha256_file(descriptors_path),
        "case_count": 24,
        "candidate_count": 240,
        "cases": combined,
    }
    payload["corpus_sha256"] = sha256_json(payload)
    write_json(out, payload)


def score_semantic(descriptors_path: str, corpus_path: str, out: str) -> None:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    descriptors = load_json(descriptors_path)
    corpus = load_json(corpus_path)
    descriptor_by_case = {
        str(case["case_id"]): case
        for case in descriptors["cases"]
    }
    corpus_by_case = {
        str(case["case_id"]): case
        for case in corpus["cases"]
    }

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        revision=MODEL_REVISION,
        trust_remote_code=False,
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        revision=MODEL_REVISION,
        trust_remote_code=False,
    )
    model.eval()

    def score(claim: str, passage: str) -> float:
        encoded = tokenizer(
            claim,
            passage,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        with torch.no_grad():
            logits = model(**encoded).logits
        ensure(logits.shape[-1] == 1, f"unexpected model logits {tuple(logits.shape)}")
        return float(torch.sigmoid(logits[0, 0]).item())

    cases_out: list[dict[str, Any]] = []
    for case_id in sorted(descriptor_by_case):
        desc = descriptor_by_case[case_id]
        corpus_case = corpus_by_case[case_id]
        children = [
            {
                "child_id": str(child["child_id"]),
                "child_text": str(child["child_text"]),
                "subject": str(child["subject_anchor"]),
                "subject_source": str(child["subject_source"]),
                "expected_evidence_forms": list(child["expected_evidence_forms"]),
                "claim_profile_sha256": child.get("claim_profile_sha256"),
            }
            for child in desc["children"]
        ]
        candidates: list[dict[str, Any]] = []
        for candidate in corpus_case["candidates"]:
            semantic_scores = {
                child["child_id"]: score(
                    child["child_text"],
                    str(candidate["text"]),
                )
                for child in children
            }
            candidates.append(
                {
                    "candidate_id": str(candidate["candidate_id"]),
                    "text": str(candidate["text"]),
                    "semantic_scores": semantic_scores,
                }
            )
        cases_out.append(
            {
                "case_id": case_id,
                "category": str(desc["category"]),
                "parent_text": str(desc["parent_text"]),
                "logic": "all_of",
                "children": children,
                "candidates": candidates,
            }
        )

    payload = {
        "schema": "eb-composite-obligation-rc1-fresh-input",
        "classification": "FRESH_CONTEXT_FREE_FIXED_POOL_INPUT",
        "source_descriptors_sha256": sha256_file(descriptors_path),
        "source_corpus_sha256": sha256_file(corpus_path),
        "semantic_model": {
            "name": MODEL_NAME,
            "revision": MODEL_REVISION,
            "transform": "sigmoid_one_logit",
            "max_length": 512,
        },
        "case_count": len(cases_out),
        "cases": cases_out,
    }
    payload["fresh_input_sha256"] = sha256_json(payload)
    write_json(out, payload)


def prepare_gold_inputs(fresh_input_path: str, out_dir: str) -> None:
    fresh = load_json(fresh_input_path)
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    for category in CATEGORIES:
        cases_out: list[dict[str, Any]] = []
        for case in fresh["cases"]:
            if case["category"] != category:
                continue
            cases_out.append(
                {
                    "case_id": case["case_id"],
                    "parent_text": case["parent_text"],
                    "children": [
                        {
                            "child_id": child["child_id"],
                            "child_text": child["child_text"],
                        }
                        for child in case["children"]
                    ],
                    "candidates": [
                        {
                            "candidate_id": candidate["candidate_id"],
                            "text": candidate["text"],
                        }
                        for candidate in case["candidates"]
                    ],
                }
            )
        ensure(len(cases_out) == 4, f"{category}: gold input split")
        write_json(
            root / f"{category}.json",
            {
                "schema": "eb-composite-obligation-rc1-sanitized-gold-input",
                "category_id": category,
                "cases": cases_out,
            },
        )


def combine_gold(parts: list[str], fresh_input_path: str, out: str) -> None:
    fresh = load_json(fresh_input_path)
    fresh_by_case = {
        str(case["case_id"]): case
        for case in fresh["cases"]
    }
    combined: list[dict[str, Any]] = []
    seen_cases: set[str] = set()
    unresolved = 0

    for part_path in parts:
        part = load_json(part_path)
        category = str(part.get("category_id", ""))
        ensure(category in CATEGORIES, f"{part_path}: invalid gold category")
        cases = part.get("cases")
        ensure(isinstance(cases, list) and len(cases) == 4, f"{category}: four gold cases")
        for case in cases:
            case_id = str(case.get("case_id", ""))
            ensure(case_id in fresh_by_case, f"unknown gold case {case_id}")
            ensure(fresh_by_case[case_id]["category"] == category, f"{case_id}: gold category drift")
            ensure(case_id not in seen_cases, f"duplicate gold case {case_id}")
            seen_cases.add(case_id)

            expected_ids = {
                str(candidate["candidate_id"])
                for candidate in fresh_by_case[case_id]["candidates"]
            }
            children = {
                str(child["child_id"])
                for child in fresh_by_case[case_id]["children"]
            }
            candidates = case.get("candidates")
            ensure(isinstance(candidates, list) and len(candidates) == 10, f"{case_id}: 10 gold candidates")
            observed_ids = {
                str(candidate.get("candidate_id", ""))
                for candidate in candidates
            }
            ensure(observed_ids == expected_ids, f"{case_id}: gold candidate ID mismatch")

            required_children: set[str] = set()
            for candidate in candidates:
                gold_class = str(candidate.get("gold_class", ""))
                ensure(gold_class in GOLD_CLASSES, f"{case_id}: invalid gold class")
                required_for = candidate.get("required_for")
                ensure(isinstance(required_for, list), f"{case_id}: required_for list")
                ensure(
                    set(map(str, required_for)) <= children,
                    f"{case_id}: unknown required_for child",
                )
                if gold_class == "REQUIRED":
                    ensure(required_for, f"{case_id}: REQUIRED without child")
                    required_children.update(map(str, required_for))
                if gold_class == "UNRESOLVED":
                    unresolved += 1
            ensure(
                required_children == children,
                f"{case_id}: each child needs at least one REQUIRED candidate; got {required_children}",
            )
            row = dict(case)
            row["category"] = category
            combined.append(row)

    ensure(len(combined) == 24, f"expected 24 gold cases, got {len(combined)}")
    ensure(unresolved == 0, f"UNRESOLVED candidates present: {unresolved}")
    combined.sort(key=lambda row: row["case_id"])
    payload = {
        "schema": "eb-composite-obligation-rc1-gold",
        "classification": "SEALED_FRESH_CONTEXT_FREE_GOLD",
        "source_fresh_input_sha256": sha256_file(fresh_input_path),
        "case_count": 24,
        "cases": combined,
    }
    payload["gold_sha256"] = sha256_json(payload)
    write_json(out, payload)


def eligibility(
    descriptors_path: str,
    corpus_path: str,
    fresh_input_path: str,
    gold_path: str,
    out: str,
) -> None:
    descriptors = load_json(descriptors_path)
    corpus = load_json(corpus_path)
    fresh = load_json(fresh_input_path)
    gold = load_json(gold_path)

    desc_by_case = {str(row["case_id"]): row for row in descriptors["cases"]}
    corpus_by_case = {str(row["case_id"]): row for row in corpus["cases"]}
    fresh_by_case = {str(row["case_id"]): row for row in fresh["cases"]}
    gold_by_case = {str(row["case_id"]): row for row in gold["cases"]}

    checks: dict[str, Any] = {}
    checks["case_count_24"] = len(fresh_by_case) == 24
    counts = Counter(row["category"] for row in fresh["cases"])
    checks["four_per_category"] = all(counts[category] == 4 for category in CATEGORIES)

    unsafe_parents = 0
    deep_required_parents = 0
    c1_starvation = 0
    actionable_c4_c5 = 0

    for case_id, fresh_case in fresh_by_case.items():
        gold_case = gold_by_case[case_id]
        gold_map = {
            str(row["candidate_id"]): row
            for row in gold_case["candidates"]
        }
        if any(row["gold_class"] == "UNSAFE_OR_MISLEADING" for row in gold_case["candidates"]):
            unsafe_parents += 1

        ordered = sorted(
            fresh_case["candidates"],
            key=lambda row: (
                -max(float(value) for value in row["semantic_scores"].values()),
                str(row["candidate_id"]),
            ),
        )
        ranks = {
            str(row["candidate_id"]): index
            for index, row in enumerate(ordered, start=1)
        }
        if any(
            row["gold_class"] == "REQUIRED"
            and ranks[str(row["candidate_id"])] >= 4
            for row in gold_case["candidates"]
        ):
            deep_required_parents += 1

        if fresh_case["category"] == "C1":
            top3 = ordered[:3]
            represented = {
                max(
                    row["semantic_scores"],
                    key=lambda child_id: (
                        float(row["semantic_scores"][child_id]),
                        child_id,
                    ),
                )
                for row in top3
            }
            if len(represented) < 2:
                c1_starvation += 1

        if fresh_case["category"] in {"C4", "C5"}:
            if any(
                set(map(str, child["expected_evidence_forms"])) & ACTIONABLE_FORMS
                for child in fresh_case["children"]
            ):
                actionable_c4_c5 += 1

        # Re-run construction geometry validation.
        _validate_corpus_case(corpus_by_case[case_id], desc_by_case[case_id])

    checks["unsafe_parents_at_least_12"] = unsafe_parents >= 12
    checks["deep_required_parents_at_least_8"] = deep_required_parents >= 8
    checks["c1_starvation_opportunity_at_least_2"] = c1_starvation >= 2
    checks["all_c4_c5_have_actionable_form"] = actionable_c4_c5 == 8
    checks["no_unresolved"] = all(
        row["gold_class"] != "UNRESOLVED"
        for case in gold["cases"]
        for row in case["candidates"]
    )

    passed = all(bool(value) for value in checks.values())
    payload = {
        "schema": "eb-composite-obligation-rc1-eligibility",
        "passed": passed,
        "checks": checks,
        "observations": {
            "category_counts": dict(sorted(counts.items())),
            "unsafe_parent_count": unsafe_parents,
            "deep_required_parent_count": deep_required_parents,
            "c1_starvation_opportunity_count": c1_starvation,
            "actionable_c4_c5_count": actionable_c4_c5,
        },
        "hashes": {
            "descriptors_sha256": sha256_file(descriptors_path),
            "corpus_sha256": sha256_file(corpus_path),
            "fresh_input_sha256": sha256_file(fresh_input_path),
            "gold_sha256": sha256_file(gold_path),
        },
    }
    write_json(out, payload)
    if not passed:
        raise ApparatusError(f"cohort eligibility failed: {checks}")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("combine-claims")
    p.add_argument("--parts", nargs="+", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("derive-descriptors")
    p.add_argument("--claims", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("split-categories")
    p.add_argument("--input", required=True)
    p.add_argument("--out-dir", required=True)

    p = sub.add_parser("combine-corpus")
    p.add_argument("--parts", nargs="+", required=True)
    p.add_argument("--descriptors", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("score")
    p.add_argument("--descriptors", required=True)
    p.add_argument("--corpus", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("prepare-gold")
    p.add_argument("--fresh-input", required=True)
    p.add_argument("--out-dir", required=True)

    p = sub.add_parser("combine-gold")
    p.add_argument("--parts", nargs="+", required=True)
    p.add_argument("--fresh-input", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("eligibility")
    p.add_argument("--descriptors", required=True)
    p.add_argument("--corpus", required=True)
    p.add_argument("--fresh-input", required=True)
    p.add_argument("--gold", required=True)
    p.add_argument("--out", required=True)

    args = parser.parse_args()
    if args.command == "combine-claims":
        combine_claims(args.parts, args.out)
    elif args.command == "derive-descriptors":
        derive_descriptors(args.claims, args.out)
    elif args.command == "split-categories":
        split_categories(args.input, args.out_dir)
    elif args.command == "combine-corpus":
        combine_corpus(args.parts, args.descriptors, args.out)
    elif args.command == "score":
        score_semantic(args.descriptors, args.corpus, args.out)
    elif args.command == "prepare-gold":
        prepare_gold_inputs(args.fresh_input, args.out_dir)
    elif args.command == "combine-gold":
        combine_gold(args.parts, args.fresh_input, args.out)
    elif args.command == "eligibility":
        eligibility(
            args.descriptors,
            args.corpus,
            args.fresh_input,
            args.gold,
            args.out,
        )
    else:
        raise AssertionError(args.command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
