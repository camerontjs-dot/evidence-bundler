from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

TOKEN_RE = re.compile(r"[A-Za-z0-9%'-]+")
NON_DIRECT_EVIDENCE_PATTERNS = (
    ("rejected", re.compile(r"\brejected (?:hypothesis|claim|proposal|statement)\b", re.I)),
    ("unverified", re.compile(r"\bunverified\b", re.I)),
    (
        "unresolved_question",
        re.compile(r"\basked whether\b|\bno conclusion(?: was)? recorded\b|\bno conclusion\b", re.I),
    ),
    ("hypothetical", re.compile(r"\bhypothetical\b", re.I)),
    (
        "example_or_template",
        re.compile(r"\bexample only\b|\bas an example\b|\btemplate\b.*\bexample\b", re.I),
    ),
    (
        "explicit_non_result",
        re.compile(
            r"\bnot (?:an? |the )?(?:measured )?(?:efficiency|result|measurement)\b"
            r"|\bnot (?:removal )?efficiency\b"
            r"|\bnot as (?:a )?measured (?:efficiency|result|measurement)\b",
            re.I,
        ),
    ),
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def token_set(text: str) -> set[str]:
    return set(tokens(text))


def jaccard(left: str, right: str) -> float:
    a = token_set(left)
    b = token_set(right)
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def local_span_recall(claim: str, candidate: str) -> float:
    query = set(tokens(claim))
    body = tokens(candidate)
    if not query or not body:
        return 0.0
    width = min(len(body), max(12, len(query) * 2))
    best = 0.0
    for start in range(0, max(1, len(body) - width + 1)):
        window = set(body[start : start + width])
        best = max(best, len(query & window) / len(query))
    return best


def phrase_coverage(text: str, terms: Iterable[str]) -> float | None:
    normalized = text.lower()
    term_list = [term.strip().lower() for term in terms if term.strip()]
    if not term_list:
        return None
    hits = sum(1 for term in term_list if term in normalized)
    return hits / len(term_list)


def evidence_posture(text: str) -> tuple[str, float]:
    for label, pattern in NON_DIRECT_EVIDENCE_PATTERNS:
        if pattern.search(text):
            return f"non_direct:{label}", 0.0
    return "direct_or_unmarked_assertion", 1.0


def weighted_mean(pairs: Iterable[tuple[float | None, float]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for value, weight in pairs:
        if value is None:
            continue
        numerator += value * weight
        denominator += weight
    return numerator / denominator if denominator else None


@dataclass(frozen=True)
class Candidate:
    evidence_id: str
    text: str
    rank: int
    bm25_score: float
    semantic_score: float | None
    metadata: dict[str, Any]


def normalize_bm25(rows: list[Candidate]) -> dict[str, float]:
    if not rows:
        return {}
    maximum = max(row.bm25_score for row in rows)
    if maximum <= 0:
        return {row.evidence_id: 0.0 for row in rows}
    return {row.evidence_id: row.bm25_score / maximum for row in rows}


def characterize(
    proposition_text: str,
    profile: dict[str, Any],
    rows: list[Candidate],
) -> list[dict[str, Any]]:
    bm25 = normalize_bm25(rows)
    concepts = list(profile.get("concepts", []))
    requires_direct_evidence = bool(profile.get("requires_direct_evidence", False))
    output: list[dict[str, Any]] = []
    for row in rows:
        concept_scores: dict[str, float | None] = {}
        weighted: list[tuple[float | None, float]] = []
        for concept in concepts:
            name = str(concept["name"])
            score = phrase_coverage(row.text, [str(x) for x in concept.get("terms", [])])
            concept_scores[name] = score
            weighted.append((score, float(concept.get("weight", 1.0))))

        evidence_form_expected = [str(x) for x in profile.get("evidence_forms", [])]
        evidence_form_observed = row.metadata.get("evidence_form")
        evidence_form_match: float | None
        if not evidence_form_expected or evidence_form_observed is None:
            evidence_form_match = None
        else:
            evidence_form_match = float(str(evidence_form_observed) in evidence_form_expected)

        source_roles = [str(x) for x in profile.get("source_roles", [])]
        observed_role = row.metadata.get("source_role")
        source_role_match: float | None
        if not source_roles or observed_role is None:
            source_role_match = None
        else:
            source_role_match = float(str(observed_role) in source_roles)

        posture_label, posture_value = evidence_posture(row.text)
        direct_evidence_match = posture_value if requires_direct_evidence else None

        profile_score = weighted_mean(
            [
                (weighted_mean(weighted), 0.7),
                (evidence_form_match, 0.2),
                (source_role_match, 0.1),
            ]
        )
        unknowns = []
        if row.semantic_score is None:
            unknowns.append("semantic_score")
        if profile_score is None:
            unknowns.append("profile_compatibility")
        if evidence_form_expected and evidence_form_observed is None:
            unknowns.append("evidence_form")
        if source_roles and observed_role is None:
            unknowns.append("source_role")

        output.append(
            {
                "evidence_id": row.evidence_id,
                "rank": row.rank,
                "bm25_score": row.bm25_score,
                "signals": {
                    "bm25_normalized": bm25[row.evidence_id],
                    "whole_claim_overlap": jaccard(proposition_text, row.text),
                    "local_span_recall": local_span_recall(proposition_text, row.text),
                    "semantic_relevance": row.semantic_score,
                    "profile_compatibility": profile_score,
                    "concept_coverage": concept_scores,
                    "evidence_form_match": evidence_form_match,
                    "source_role_match": source_role_match,
                    "evidence_posture": posture_label,
                    "direct_evidence_match": direct_evidence_match,
                },
                "unknowns": unknowns,
            }
        )
    return output


def candidate_base_utility(row: dict[str, Any], ablate: set[str] | None = None) -> float:
    ablate = ablate or set()
    s = row["signals"]
    weighted = []
    if "semantic" not in ablate:
        weighted.append((s["semantic_relevance"], 0.25))
    if "local_span" not in ablate:
        weighted.append((s["local_span_recall"], 0.10))
    if "profile" not in ablate:
        weighted.append((s["profile_compatibility"], 0.25))
    if "posture" not in ablate:
        weighted.append((s["direct_evidence_match"], 0.30))
    weighted.append((s["bm25_normalized"], 0.10))
    value = weighted_mean(weighted)
    return 0.0 if value is None else value


def concept_set_coverage(selected: list[dict[str, Any]]) -> float | None:
    names: set[str] = set()
    for row in selected:
        names.update(row["signals"]["concept_coverage"])
    if not names:
        return None
    scores = []
    for name in sorted(names):
        values = [row["signals"]["concept_coverage"].get(name) for row in selected]
        known = [float(value) for value in values if value is not None]
        if known:
            scores.append(max(known))
    return sum(scores) / len(scores) if scores else None


def redundancy(selected: list[dict[str, Any]], by_id: dict[str, Candidate]) -> float:
    if len(selected) < 2:
        return 0.0
    values = []
    for i in range(len(selected)):
        for j in range(i + 1, len(selected)):
            values.append(
                jaccard(
                    by_id[selected[i]["evidence_id"]].text,
                    by_id[selected[j]["evidence_id"]].text,
                )
            )
    return sum(values) / len(values) if values else 0.0


def set_utility(
    selected: list[dict[str, Any]],
    by_id: dict[str, Candidate],
    ablate: set[str] | None = None,
) -> float:
    if not selected:
        return 0.0
    base = sum(candidate_base_utility(row, ablate) for row in selected) / len(selected)
    coverage = None if ablate and "profile" in ablate else concept_set_coverage(selected)
    return (
        base
        + (0.15 * coverage if coverage is not None else 0.0)
        - 0.15 * redundancy(selected, by_id)
    )


def typed_select(
    characterized: list[dict[str, Any]],
    candidates: list[Candidate],
    budget: int = 3,
    ablate: set[str] | None = None,
) -> list[str]:
    by_id = {row.evidence_id: row for row in candidates}
    rows = sorted(characterized, key=lambda row: (row["rank"], row["evidence_id"]))
    selected: list[dict[str, Any]] = []
    while len(selected) < min(budget, len(rows)):
        best: tuple[float, int, str, dict[str, Any]] | None = None
        current = set_utility(selected, by_id, ablate)
        for row in rows:
            if row in selected:
                continue
            gain = set_utility(selected + [row], by_id, ablate) - current
            candidate_key = (gain, -int(row["rank"]), str(row["evidence_id"]), row)
            if best is None:
                best = candidate_key
                continue
            if gain > best[0] + 1e-12:
                best = candidate_key
            elif math.isclose(gain, best[0], abs_tol=1e-12):
                if int(row["rank"]) < -best[1] or (
                    int(row["rank"]) == -best[1] and str(row["evidence_id"]) < best[2]
                ):
                    best = candidate_key
        assert best is not None
        selected.append(best[3])
    return [str(row["evidence_id"]) for row in selected]


def semantic_select(candidates: list[Candidate], budget: int = 3) -> list[str]:
    ordered = sorted(
        candidates,
        key=lambda row: (
            -(row.semantic_score if row.semantic_score is not None else float("-inf")),
            row.rank,
            row.evidence_id,
        ),
    )
    return [row.evidence_id for row in ordered[:budget]]


def bm25_select(candidates: list[Candidate], budget: int = 3) -> list[str]:
    return [
        row.evidence_id
        for row in sorted(candidates, key=lambda row: (row.rank, row.evidence_id))[:budget]
    ]


def parse_candidate(value: dict[str, Any]) -> Candidate:
    semantic = value.get("semantic_score")
    return Candidate(
        evidence_id=str(value["evidence_id"]),
        text=str(value["text"]),
        rank=int(value["rank"]),
        bm25_score=float(value["bm25_score"]),
        semantic_score=None if semantic is None else float(semantic),
        metadata=dict(value.get("metadata", {})),
    )


def run_lane(lane: dict[str, Any]) -> dict[str, Any]:
    candidates = [parse_candidate(row) for row in lane["candidates"]]
    characterized = characterize(
        str(lane["proposition_text"]), dict(lane.get("claim_profile", {})), candidates
    )
    return {
        "proposition_id": lane["proposition_id"],
        "characterization": characterized,
        "arms": {
            "bm25_top3": bm25_select(candidates),
            "semantic_top3": semantic_select(candidates),
            "typed_top3": typed_select(characterized, candidates),
            "typed_without_profile": typed_select(
                characterized, candidates, ablate={"profile"}
            ),
            "typed_without_local_span": typed_select(
                characterized, candidates, ablate={"local_span"}
            ),
            "typed_without_semantic": typed_select(
                characterized, candidates, ablate={"semantic"}
            ),
            "typed_without_evidence_posture": typed_select(
                characterized, candidates, ablate={"posture"}
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = {
        "schema": "eb-typed-selector-rc0-output-v1",
        "classification": "DEVELOPMENT_ONLY_NO_PROMOTION_AUTHORITY",
        "lanes": [run_lane(lane) for lane in payload["lanes"]],
        "nonclaims": [
            "No SUPPORTS/REFUTES judgment is produced.",
            "No selector is qualified by this development output.",
            "Evidence posture is candidate-side discourse/evidence-form characterization, not truth or entailment authority.",
            "Unknown signals remain explicit and are omitted from weighted means rather than coerced to zero.",
        ],
    }
    text = canonical_json(result) + "\n"
    Path(args.output).write_text(text, encoding="utf-8")
    print(sha256_text(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
