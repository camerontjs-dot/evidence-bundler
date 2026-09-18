from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from proposition_authoring.claim_profile import build_claim_profile
from proposition_authoring.model import AuthoringRequest

CAPS = (0.01, 0.03, 0.05)
BUDGETS = (3, 6)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "does", "during",
    "for", "from", "in", "is", "it", "may", "not", "of", "on", "only", "or",
    "remain", "remains", "required", "requires", "same", "stated", "that", "the",
    "this", "to", "when", "while", "with", "within",
}
GENERIC_TERMS = {
    "claim", "evidence", "document", "record", "report", "statement", "information",
}

BRANDED_ID_RE = re.compile(r"\b[A-Z][A-Za-z]+-\d+\b")
NUMBERED_OBJECT_RE = re.compile(
    r"\b(?:sample|valve|revision|version|unit|line|channel|rack|tray|sensor)\s+"
    r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\b",
    re.I,
)
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
REVISION_RE = re.compile(r"\b(?:revision|version)\s+\d+(?:\.\d+)?\b", re.I)
DURATION_RE = re.compile(
    r"\b\d+(?:\.\d+)?[- ]?(?:minute|minutes|hour|hours|day|days|second|seconds)\b",
    re.I,
)
MEASUREMENT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:degrees?\s*C|°C|psi|bar|kpa|mpa|%|percent)\b",
    re.I,
)
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")

EVENT_RE = re.compile(
    r"\b(?:log|logged|record|recorded|audit|witness|incident|event|scan|check|"
    r"signature|signed|match|movement|release)\b",
    re.I,
)
REGISTRY_RE = re.compile(
    r"\b(?:registry|register|registered|inventory|certificate|certified|database|"
    r"revision|version|effective|in force)\b",
    re.I,
)
DECLARATION_RE = re.compile(
    r"\b(?:states?|requires?|required|policy|manual|procedure|specification|sop|"
    r"declaration|approved|effective|in force)\b",
    re.I,
)
MEASUREMENT_TERM_RE = re.compile(
    r"\b(?:temperature|measured|measurement|value|threshold|below|above|exceed|"
    r"duration|hold|minutes?|degrees?)\b",
    re.I,
)
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def unique_preserving(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = normalize(value)
        if key and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def subject_anchors(text: str) -> list[str]:
    values = BRANDED_ID_RE.findall(text)
    values.extend(match.group(0) for match in NUMBERED_OBJECT_RE.finditer(text))
    return unique_preserving(values)


def scope_literals(text: str) -> list[str]:
    values: list[str] = []
    for pattern in (DATE_RE, REVISION_RE, DURATION_RE, MEASUREMENT_RE):
        values.extend(match.group(0) for match in pattern.finditer(text))
    return unique_preserving(values)


def predicate_terms(
    text: str,
    *,
    subjects: list[str],
    scopes: list[str],
) -> list[str]:
    excluded: set[str] = set()
    for span in subjects + scopes:
        excluded.update(token.lower() for token in WORD_RE.findall(span))
    terms = []
    for token in WORD_RE.findall(text):
        value = token.lower()
        if len(value) < 3:
            continue
        if value in STOPWORDS or value in GENERIC_TERMS or value in excluded:
            continue
        terms.append(value)
    return sorted(set(terms))


def profile_for(child_id: str, text: str) -> dict[str, Any]:
    request = AuthoringRequest(
        handoff_id=f"obligation-dev:{child_id}",
        producer_id="eb-composite-obligation-pressure-dev-v0",
        producer_version="0",
        work_id=f"work:{child_id}",
        root_id=child_id,
        root_text=text,
    )
    return build_claim_profile(request)


def descriptor(
    *,
    parent_id: str,
    parent_text: str,
    child: dict[str, Any],
) -> dict[str, Any]:
    child_id = str(child["child_id"])
    child_text = str(child["text"])
    child_subjects = subject_anchors(child_text)
    parent_subjects = subject_anchors(parent_text)
    inherited = [
        value
        for value in parent_subjects
        if normalize(value) not in {normalize(x) for x in child_subjects}
    ]
    scopes = scope_literals(child_text)
    parent_scopes = scope_literals(parent_text)
    inherited_scopes = [
        value
        for value in parent_scopes
        if normalize(value) not in {normalize(x) for x in scopes}
    ]
    terms = predicate_terms(
        child_text,
        subjects=child_subjects,
        scopes=scopes,
    )
    profile = profile_for(child_id, child_text)
    forms = [
        str(value)
        for value in profile.get("expected_evidence_forms", [])
        if str(value) not in {"unknown", "none", "not_applicable"}
    ]
    return {
        "parent_id": parent_id,
        "proposition_id": child_id,
        "sequence": int(child["sequence"]),
        "text": child_text,
        "expected_evidence_forms": sorted(set(forms)),
        "subject_anchors": child_subjects,
        "inherited_subject_anchors": inherited,
        "predicate_terms": terms,
        "scope_literals": scopes,
        "inherited_scope_literals": inherited_scopes,
        "provenance": {
            "expected_evidence_forms": "shadow_expected_form",
            "subject_anchors": "claim_native",
            "inherited_subject_anchors": "parent_inherited_claim_native",
            "predicate_terms": "claim_native",
            "scope_literals": "claim_native",
            "inherited_scope_literals": "parent_inherited_claim_native",
        },
        "profile_sha256": profile.get("profile_sha256"),
    }


def candidate_forms(text: str) -> set[str]:
    forms = {"document_text"}
    if EVENT_RE.search(text):
        forms.add("event_record")
    if REGISTRY_RE.search(text):
        forms.add("registry_entry")
    if DECLARATION_RE.search(text):
        forms.add("authoritative_declaration")
    if (
        (NUMBER_RE.search(text) or MEASUREMENT_RE.search(text))
        and MEASUREMENT_TERM_RE.search(text)
    ):
        forms.add("measurement")
    return forms


def fraction_substrings(values: list[str], text: str) -> float | None:
    if not values:
        return None
    target = normalize(text)
    matched = sum(normalize(value) in target for value in values)
    return matched / len(values)


def fraction_terms(values: list[str], text: str) -> float | None:
    if not values:
        return None
    observed = {token.lower() for token in WORD_RE.findall(text)}
    return len(set(values) & observed) / len(set(values))


def form_match(forms: list[str], text: str) -> float | None:
    if not forms:
        return None
    expected = set(forms)
    observed = candidate_forms(text)
    return len(expected & observed) / len(expected)


def child_presence(candidate: dict[str, Any], child_id: str) -> float:
    return float(
        any(str(row.get("child_id")) == child_id for row in candidate["query_hits"])
    )


def available_mean(values: list[float | None]) -> float | None:
    material = [float(value) for value in values if value is not None]
    if not material:
        return None
    return sum(material) / len(material)


def feature_score(
    candidate: dict[str, Any],
    child_id: str,
    desc: dict[str, Any],
    family: str,
) -> float | None:
    text = str(candidate["text"])
    form = form_match(desc["expected_evidence_forms"], text)
    child_subject = fraction_substrings(desc["subject_anchors"], text)
    inherited_subject = fraction_substrings(
        desc["subject_anchors"] + desc["inherited_subject_anchors"],
        text,
    )
    predicate = fraction_terms(desc["predicate_terms"], text)
    scope = fraction_substrings(
        desc["scope_literals"] + desc["inherited_scope_literals"],
        text,
    )
    presence = child_presence(candidate, child_id)

    if family == "child_coverage":
        return presence
    if family == "expected_form":
        return form
    if family == "subject_child":
        return child_subject
    if family == "subject_inherited":
        return inherited_subject
    if family == "predicate_terms":
        return predicate
    if family == "scope_literals":
        return scope
    if family == "claim_native_lexical":
        return available_mean([inherited_subject, predicate, scope])
    if family == "form_plus_inherited_subject":
        return available_mean([form, inherited_subject])
    if family == "full_obligation":
        return available_mean([presence, form, inherited_subject, predicate, scope])
    raise ValueError(f"unknown family: {family}")


def semantic_order(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda row: (
            -float(row["best_score"]),
            int(row["best_rank"]),
            str(row["paragraph_id"]),
        ),
    )


def repair_for_children(
    *,
    pool: list[dict[str, Any]],
    descriptors_by_child: dict[str, dict[str, Any]],
    descriptor_assignment: dict[str, dict[str, Any]],
    family: str,
    budget: int,
    loss_cap: float,
) -> list[str]:
    ordered = semantic_order(pool)
    selected = list(ordered[:budget])
    outside = list(ordered[budget:])

    for child_id in sorted(
        descriptors_by_child,
        key=lambda value: int(descriptors_by_child[value]["sequence"]),
    ):
        desc = descriptor_assignment[child_id]

        def score(
            row: dict[str, Any],
            *,
            bound_child_id: str = child_id,
            bound_desc: dict[str, Any] = desc,
        ) -> float:
            value = feature_score(row, bound_child_id, bound_desc, family)
            return -1.0 if value is None else float(value)

        if not outside:
            continue
        victim = min(
            selected,
            key=lambda row: (
                score(row),
                float(row["best_score"]),
                -int(row["best_rank"]),
                str(row["paragraph_id"]),
            ),
        )
        challenger = max(
            outside,
            key=lambda row: (
                score(row),
                float(row["best_score"]),
                -int(row["best_rank"]),
                str(row["paragraph_id"]),
            ),
        )
        if score(challenger) <= score(victim) + 1e-12:
            continue
        loss = float(victim["best_score"]) - float(challenger["best_score"])
        if loss > loss_cap + 1e-12:
            continue

        selected = [row for row in selected if row is not victim] + [challenger]
        outside = [row for row in outside if row is not challenger] + [victim]
        selected = semantic_order(selected)
        outside = semantic_order(outside)

    return [str(row["paragraph_id"]) for row in selected]


def rotate_descriptors(
    all_descriptors: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    ids = sorted(all_descriptors)
    return {
        child_id: all_descriptors[ids[(index + 1) % len(ids)]]
        for index, child_id in enumerate(ids)
    }


def run(
    *,
    raw_path: Path,
    decompositions_path: Path,
) -> dict[str, Any]:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    decompositions = load_jsonl(decompositions_path)
    a1_by_parent = {
        str(row["original_claim_id"]): row
        for row in decompositions
        if str(row["variant_id"]) == "A1"
    }

    descriptors: dict[str, dict[str, Any]] = {}
    descriptors_by_parent: dict[str, dict[str, dict[str, Any]]] = {}
    for parent_id, record in sorted(a1_by_parent.items()):
        parent_text = str(record["original_claim_text"])
        child_map: dict[str, dict[str, Any]] = {}
        for child in sorted(record["children"], key=lambda row: int(row["sequence"])):
            desc = descriptor(
                parent_id=parent_id,
                parent_text=parent_text,
                child=child,
            )
            child_id = str(child["child_id"])
            descriptors[child_id] = desc
            child_map[child_id] = desc
        descriptors_by_parent[parent_id] = child_map

    shuffled = rotate_descriptors(descriptors)
    families = (
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
    shuffle_families = {
        "expected_form",
        "subject_inherited",
        "predicate_terms",
        "scope_literals",
        "claim_native_lexical",
        "full_obligation",
    }

    claims_out: list[dict[str, Any]] = []
    arm_change_counts: Counter[str] = Counter()

    for claim in raw["claims"]:
        parent_id = str(claim["original_claim_id"])
        if parent_id not in descriptors_by_parent:
            continue

        semantic = claim["retrievers"]["semantic"]
        a1 = semantic["variants"]["A1"]
        pool = list(a1["equal_per_query_budget"]["hits"])
        pool_ids = [str(row["paragraph_id"]) for row in pool]
        if len(pool_ids) != len(set(pool_ids)):
            raise RuntimeError(f"{parent_id}: candidate pool contains duplicate IDs")

        child_desc = descriptors_by_parent[parent_id]
        correct_assignment = {child_id: desc for child_id, desc in child_desc.items()}
        shuffled_assignment = {
            child_id: shuffled[child_id] for child_id in child_desc
        }

        arms: dict[str, list[str]] = {}
        for budget in BUDGETS:
            baseline = [
                str(row["paragraph_id"]) for row in semantic_order(pool)[:budget]
            ]
            arms[f"semantic_topk_k{budget}"] = baseline

            for cap in CAPS:
                cap_label = f"{cap:.2f}"
                for family in families:
                    name = f"{family}_correct_k{budget}_cap_{cap_label}"
                    chosen = repair_for_children(
                        pool=pool,
                        descriptors_by_child=child_desc,
                        descriptor_assignment=correct_assignment,
                        family=family,
                        budget=budget,
                        loss_cap=cap,
                    )
                    arms[name] = chosen
                    arm_change_counts[name] += int(chosen != baseline)

                    if family in shuffle_families:
                        sname = f"{family}_shuffled_k{budget}_cap_{cap_label}"
                        schosen = repair_for_children(
                            pool=pool,
                            descriptors_by_child=child_desc,
                            descriptor_assignment=shuffled_assignment,
                            family=family,
                            budget=budget,
                            loss_cap=cap,
                        )
                        arms[sname] = schosen
                        arm_change_counts[sname] += int(schosen != baseline)

        claims_out.append(
            {
                "original_claim_id": parent_id,
                "original_claim_text": claim["original_claim_text"],
                "a1_decomposition_id": a1["decomposition_id"],
                "descriptors": child_desc,
                "pool": pool,
                "pool_sha256": sha256_json(pool),
                "equal_total_reference_ids": [
                    str(row["paragraph_id"])
                    for row in a1["equal_total_budget"]["hits"]
                ],
                "arms": {name: ids for name, ids in sorted(arms.items())},
            }
        )

    output = {
        "schema": "eb-composite-evidence-obligations-dev-v0-selections",
        "classification": "EXPOSED_DEVELOPMENT_MECHANISM_PRESSURE",
        "raw_sha256": sha256_file(raw_path),
        "decompositions_sha256": sha256_file(decompositions_path),
        "claim_profile_subject": "e29a165b682d060f5dc2a0f3c7d64a7f29b172b4",
        "caps": list(CAPS),
        "budgets": list(BUDGETS),
        "family_list": list(families),
        "shuffled_families": sorted(shuffle_families),
        "descriptor_count": len(descriptors),
        "claim_count": len(claims_out),
        "arm_change_claim_counts": dict(sorted(arm_change_counts.items())),
        "claims": claims_out,
        "nonclaims": [
            "exposed development study only",
            "selection program does not load relevance gold",
            "expected evidence forms remain shadow characterization",
            "candidate pool is frozen prior semantic retrieval output",
            "first-stage retrieval is not changed",
        ],
    }
    output["output_sha256"] = sha256_json(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--decompositions", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    result = run(
        raw_path=Path(args.raw),
        decompositions_path=Path(args.decompositions),
    )
    Path(args.out).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output_sha256": result["output_sha256"],
                "claim_count": result["claim_count"],
                "descriptor_count": result["descriptor_count"],
                "arm_change_claim_counts": result["arm_change_claim_counts"],
                "descriptors": {
                    claim["original_claim_id"]: claim["descriptors"]
                    for claim in result["claims"]
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
