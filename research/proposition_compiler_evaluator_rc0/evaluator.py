#!/usr/bin/env python3
"""Research-only Proposition Compiler Evaluator RC0.

This module implements a deliberately narrow, fail-closed rule/feature evaluator for
single propositions and explicit conjunctive all_of candidates. It is an apparatus
candidate under test, not semantic authority and not production code.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from typing import Any, Iterable

PROFILE_ID = "pc-evaluator-rc0-explicit-conjunction-v1"
DISPOSITIONS = {
    "ACCEPTABLE_WITHIN_PROFILE",
    "REJECT_UNSAFE",
    "INDETERMINATE",
    "INVALID_INPUT",
}
DIMENSIONS = (
    "STRUCTURAL_VALIDITY",
    "PROFILE_MEMBERSHIP",
    "ROOT_SUPPORTS_CHILDREN",
    "CHILDREN_RECONSTRUCT_ROOT",
    "OPERATOR_ATTACHMENT",
    "POLARITY_MODALITY",
    "REFERENCE_ARGUMENT_BINDING",
    "ASSERTION_TYPE",
    "RELATION_DIRECTION",
    "DUPLICATION",
    "AUDITABILITY",
    "UNDER_DECOMPOSITION",
    "OVER_DECOMPOSITION",
)
STATUS = {"PASS", "FAIL", "INDETERMINATE", "NOT_APPLICABLE"}

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "that", "this", "its", "it", "in",
    "at", "on", "for", "by", "with", "from", "as", "be", "is", "are", "was", "were",
}
MODALS = {"may", "might", "must", "should", "can", "could", "will", "would", "probably", "possibly", "certainly"}
NEGATORS = {"not", "never", "no", "none", "neither", "without"}
QUANTIFIERS = {"all", "some", "none", "most", "each", "every", "any", "at least", "at most", "more than", "less than"}
EMBEDDING_MARKERS = {
    "reported", "reports", "said", "says", "expects", "expected", "recommends", "recommended",
    "predicts", "predicted", "found", "finds", "according",
}
RELATION_MARKERS = {"before", "after", "caused", "causes", "associated", "jointly", "respectively", "than"}
VERB_HINTS = {
    "rose", "fell", "restart", "record", "records", "lifted", "stopped", "stop", "transmitting",
    "transmit", "dimmed", "dim", "encrypt", "encrypted", "transmit", "signed", "filed", "passed",
    "failed", "approved", "approve", "acquired", "uses", "use", "logged", "logs", "encrypts",
    "increased", "decreased", "reduced", "remained", "completed", "began", "begins", "reviewed",
    "review", "recommended", "recommends", "reported", "reports", "said", "says", "expects", "found",
    "caused", "causes", "associated", "occurred", "occurs", "replaced", "entered", "shut", "is", "are",
    "was", "were", "be", "file", "uses", "received", "deploy", "deployed", "reduce", "retest",
}


@dataclass(frozen=True)
class Finding:
    dimension: str
    status: str
    reason_code: str
    detail: str


def _norm(text: str) -> str:
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text.strip().lower())
    return text


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?|\d+(?:\.\d+)?|>=|<=|>|<", _norm(text))


def _content_tokens(text: str) -> set[str]:
    return {t for t in _tokens(text) if t not in STOPWORDS}


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _verb_count(text: str) -> int:
    toks = _tokens(text)
    count = 0
    for t in toks:
        if t in VERB_HINTS or (len(t) > 4 and t.endswith(("ed", "ing"))):
            count += 1
    return count


def _simple_root_clauses(root: str) -> list[str]:
    # Deliberately narrow: split only simple surface conjunctions. Profile gate prevents
    # treating every occurrence of "and" as Boolean conjunction.
    return [p.strip(" .") for p in re.split(r"\band\b", root, flags=re.I) if p.strip(" .")]


def _leading_scope(root: str) -> str | None:
    m = re.match(
        r"^\s*((?:during|among|at|in|if|according to)\b[^,]{1,80}),\s+",
        root,
        flags=re.I,
    )
    return m.group(1).strip() if m else None


def _ambiguous_or_out_of_profile(root: str) -> list[str]:
    n = _norm(root)
    reasons: list[str] = []
    if re.search(r"\bor\b", n):
        reasons.append("OUT_OF_PROFILE_DISJUNCTION")
    # Surface form "did not X and Y" with only one explicit negator is a preregistered
    # ambiguity probe unless authorized context resolves scope.
    if " did not " in f" {n} " and " and " in n and len(re.findall(r"\bnot\b", n)) == 1:
        reasons.append("AMBIGUOUS_NEGATION_SCOPE")
    if re.search(r"\bold\s+\w+\s+and\s+\w+", n):
        reasons.append("POTENTIAL_MODIFIER_ATTACHMENT_AMBIGUITY")
    return reasons


def _likely_boolean_conjunction(root: str) -> bool:
    n = _norm(root)
    if " and " not in n:
        return False
    if "jointly" in n and _verb_count(root) <= 1:
        return False
    if re.search(r"\bbetween\b.+\band\b", n) and _verb_count(root) <= 1:
        return False
    return _verb_count(root) >= 2


def _modal_set(text: str) -> set[str]:
    toks = set(_tokens(text))
    return toks & MODALS


def _negator_set(text: str) -> set[str]:
    return set(_tokens(text)) & NEGATORS


def _number_tokens(text: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:\.\d+)?\b|>=|<=|>|<", _norm(text)))


def _embedding_set(text: str) -> set[str]:
    return set(_tokens(text)) & EMBEDDING_MARKERS


def _relation_set(text: str) -> set[str]:
    return set(_tokens(text)) & RELATION_MARKERS


def _comparatives(text: str) -> set[tuple[str, str, str]]:
    # Controlled RC0 patterns, intentionally not universal semantic parsing.
    out: set[tuple[str, str, str]] = set()
    pattern = re.compile(
        r"\b([A-Za-z]+(?:\s+[A-Za-z])?)\s+is\s+"
        r"(faster|slower|cheaper|higher|lower|greater|less)\s+than\s+"
        r"([A-Za-z]+(?:\s+[A-Za-z])?)\b",
        flags=re.I,
    )
    for m in pattern.finditer(text):
        out.add(tuple(_norm(x) for x in m.groups()))
    return out


def _best_clause(child: str, root_clauses: list[str]) -> str | None:
    ct = _content_tokens(child)
    if not root_clauses:
        return None
    scored = [(len(ct & _content_tokens(c)), c) for c in root_clauses]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored and scored[0][0] > 0 else None


def _validate_input(candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("case_id", "root_id", "root_text", "profile_id", "candidate_state", "children"):
        if key not in candidate:
            errors.append(f"MISSING_{key.upper()}")
    if errors:
        return errors
    if candidate.get("profile_id") != PROFILE_ID:
        errors.append("UNSUPPORTED_PROFILE")
    state = candidate.get("candidate_state")
    if state not in {"NOT_NEEDED", "DECLARED", "ABSTAINED", "FAILED"}:
        errors.append("INVALID_CANDIDATE_STATE")
    children = candidate.get("children")
    if not isinstance(children, list):
        errors.append("CHILDREN_NOT_LIST")
        return errors
    if state == "DECLARED":
        if candidate.get("operator") != "all_of":
            errors.append("DECLARED_REQUIRES_ALL_OF")
        if len(children) < 2:
            errors.append("DECLARED_REQUIRES_TWO_CHILDREN")
    else:
        if children:
            errors.append("NON_DECLARED_MUST_NOT_HAVE_CHILDREN")
    seen: set[str] = set()
    for child in children:
        if not isinstance(child, dict) or not isinstance(child.get("child_id"), str) or not isinstance(child.get("text"), str):
            errors.append("INVALID_CHILD_SHAPE")
            continue
        if child["child_id"] in seen:
            errors.append("DUPLICATE_CHILD_ID")
        seen.add(child["child_id"])
        if not child["text"].strip():
            errors.append("EMPTY_CHILD_TEXT")
    return errors


def evaluate(candidate: dict[str, Any]) -> dict[str, Any]:
    findings: list[Finding] = []
    errors = _validate_input(candidate)
    if errors:
        for e in errors:
            findings.append(Finding("STRUCTURAL_VALIDITY", "FAIL", e, e))
        return _result(candidate, "INVALID_INPUT", findings)
    findings.append(Finding("STRUCTURAL_VALIDITY", "PASS", "VALID_SHAPE", "Input satisfies RC0 structural shape."))

    state = candidate["candidate_state"]
    root = candidate["root_text"]
    context = candidate.get("context_text", "") or ""
    children = candidate["children"]

    if state in {"ABSTAINED", "FAILED"}:
        findings.append(Finding("PROFILE_MEMBERSHIP", "INDETERMINATE", f"UPSTREAM_{state}", "Compiler did not supply an authoritative decomposition candidate."))
        return _result(candidate, "INDETERMINATE", findings)

    profile_reasons = _ambiguous_or_out_of_profile(root)
    if profile_reasons:
        for reason in profile_reasons:
            findings.append(Finding("PROFILE_MEMBERSHIP", "INDETERMINATE", reason, "Root exceeds the narrow unambiguous conjunctive RC0 profile."))
        return _result(candidate, "INDETERMINATE", findings)
    findings.append(Finding("PROFILE_MEMBERSHIP", "PASS", "IN_PROFILE", "No preregistered out-of-profile/ambiguity trigger fired."))

    if state == "NOT_NEEDED":
        if _likely_boolean_conjunction(root):
            findings.append(Finding("UNDER_DECOMPOSITION", "FAIL", "EXPLICIT_CONJUNCTION_NOT_DECOMPOSED", "Root contains a supported explicit top-level conjunction."))
            return _result(candidate, "REJECT_UNSAFE", findings)
        findings.append(Finding("UNDER_DECOMPOSITION", "PASS", "NO_SUPPORTED_SPLIT_REQUIRED", "No supported explicit top-level conjunction requires declaration."))
        return _result(candidate, "ACCEPTABLE_WITHIN_PROFILE", findings)

    # DECLARED
    texts = [c["text"] for c in children]
    norms = [_norm(t) for t in texts]

    if len(norms) != len(set(norms)):
        findings.append(Finding("DUPLICATION", "FAIL", "DUPLICATE_CHILD_TEXT", "Duplicate authoritative audit unit detected."))
    else:
        findings.append(Finding("DUPLICATION", "PASS", "NO_DUPLICATE_CHILD", "No exact normalized child duplicate detected."))

    # Auditability / propositionhood
    audit_fail = False
    for child in texts:
        toks = _tokens(child)
        if len(toks) < 3 or _verb_count(child) < 1 or _norm(child).startswith(("because ", "although ", "while ")):
            audit_fail = True
            findings.append(Finding("AUDITABILITY", "FAIL", "NON_PROPOSITIONAL_CHILD", f"Child not independently proposition-like: {child}"))
    if not audit_fail:
        findings.append(Finding("AUDITABILITY", "PASS", "CHILDREN_PROPOSITIONAL", "Each child is proposition-like within the narrow RC0 heuristic."))

    # Over/under decomposition heuristics
    under = False
    for child in texts:
        if _likely_boolean_conjunction(child):
            under = True
            findings.append(Finding("UNDER_DECOMPOSITION", "FAIL", "CHILD_RETAINS_SUPPORTED_CONJUNCTION", child))
    if not under:
        findings.append(Finding("UNDER_DECOMPOSITION", "PASS", "NO_RETAINED_SUPPORTED_CONJUNCTION", "No child retains an obvious supported conjunction."))
    if audit_fail:
        findings.append(Finding("OVER_DECOMPOSITION", "FAIL", "FRAGMENTATION_BELOW_PROPOSITION", "At least one child is non-propositional."))
    else:
        findings.append(Finding("OVER_DECOMPOSITION", "PASS", "NO_FRAGMENTATION_DEFECT", "No propositionhood-based over-decomposition defect detected."))

    root_tok = _content_tokens(root)
    ctx_tok = _content_tokens(context)
    child_union = set().union(*(_content_tokens(t) for t in texts)) if texts else set()
    additions = child_union - root_tok - ctx_tok
    if additions:
        findings.append(Finding("ROOT_SUPPORTS_CHILDREN", "FAIL", "UNLICENSED_CHILD_TOKENS", f"Child content not licensed by root/context: {sorted(additions)}"))
    else:
        findings.append(Finding("ROOT_SUPPORTS_CHILDREN", "PASS", "NO_LEXICAL_ADDITION", "No new content tokens outside root/context."))

    missing = root_tok - child_union
    # `jointly` is promotion-critical and should not disappear even if every event/entity token remains.
    if missing:
        findings.append(Finding("CHILDREN_RECONSTRUCT_ROOT", "FAIL", "ROOT_CONTENT_MISSING", f"Root content missing from children: {sorted(missing)}"))
    else:
        findings.append(Finding("CHILDREN_RECONSTRUCT_ROOT", "PASS", "ROOT_CONTENT_COVERED", "All tracked root content tokens occur in aggregate children."))

    scope = _leading_scope(root)
    if scope:
        scope_tokens = _content_tokens(scope)
        bad = [t for t in texts if not scope_tokens <= _content_tokens(t)]
        if bad:
            findings.append(Finding("OPERATOR_ATTACHMENT", "FAIL", "SHARED_SCOPE_NOT_PROPAGATED", f"Leading shared scope `{scope}` absent from {len(bad)} child(ren)."))
        else:
            findings.append(Finding("OPERATOR_ATTACHMENT", "PASS", "SHARED_SCOPE_PROPAGATED", f"Leading shared scope `{scope}` retained by all children."))
    else:
        findings.append(Finding("OPERATOR_ATTACHMENT", "NOT_APPLICABLE", "NO_LEADING_SHARED_SCOPE", "No supported leading shared-scope pattern detected."))

    clauses = _simple_root_clauses(root)
    modal_fail = False
    for child in texts:
        clause = _best_clause(child, clauses)
        if clause is None:
            continue
        cm = _modal_set(child)
        rm = _modal_set(clause)
        cn = _negator_set(child)
        rn = _negator_set(clause)
        if cm != rm or cn != rn:
            modal_fail = True
            findings.append(Finding("POLARITY_MODALITY", "FAIL", "CLAUSE_FORCE_CHANGED", f"Child force {sorted(cm | cn)} differs from aligned root clause {sorted(rm | rn)}."))
    if not modal_fail:
        findings.append(Finding("POLARITY_MODALITY", "PASS", "CLAUSE_FORCE_PRESERVED", "Tracked negation/modal force preserved against aligned root clauses."))

    root_comp = _comparatives(root)
    child_comp = set().union(*(_comparatives(t) for t in texts)) if texts else set()
    if root_comp or child_comp:
        if child_comp != root_comp:
            findings.append(Finding("REFERENCE_ARGUMENT_BINDING", "FAIL", "COMPARATIVE_ARGUMENT_CHANGE", f"Root comparatives={sorted(root_comp)} children={sorted(child_comp)}"))
            findings.append(Finding("RELATION_DIRECTION", "FAIL", "COMPARATIVE_DIRECTION_CHANGE", "Comparative relation/argument binding changed."))
        else:
            findings.append(Finding("REFERENCE_ARGUMENT_BINDING", "PASS", "COMPARATIVE_ARGUMENTS_PRESERVED", "Comparative argument bindings preserved."))
            findings.append(Finding("RELATION_DIRECTION", "PASS", "COMPARATIVE_DIRECTION_PRESERVED", "Comparative relations preserved."))
    else:
        root_rel = _relation_set(root)
        child_rel = set().union(*(_relation_set(t) for t in texts)) if texts else set()
        if root_rel != child_rel:
            findings.append(Finding("RELATION_DIRECTION", "FAIL", "RELATION_MARKER_CHANGE", f"Root relation markers={sorted(root_rel)} children={sorted(child_rel)}"))
        else:
            findings.append(Finding("RELATION_DIRECTION", "PASS", "RELATION_MARKERS_PRESERVED", "Tracked relation markers preserved."))
        findings.append(Finding("REFERENCE_ARGUMENT_BINDING", "NOT_APPLICABLE", "NO_CONTROLLED_COMPARATIVE_PATTERN", "No controlled comparison pattern was available for role check."))

    root_embed = _embedding_set(root)
    child_embed = set().union(*(_embedding_set(t) for t in texts)) if texts else set()
    if root_embed and not root_embed <= child_embed:
        findings.append(Finding("ASSERTION_TYPE", "FAIL", "EMBEDDING_OPERATOR_LOST", f"Root embedding markers {sorted(root_embed)} not preserved in children {sorted(child_embed)}."))
    else:
        findings.append(Finding("ASSERTION_TYPE", "PASS", "ASSERTION_TYPE_PRESERVED_OR_NOT_TRIGGERED", "No tracked embedding-operator loss detected."))

    # Quantitative/operator preservation beyond content-token coverage.
    if _number_tokens(root) != set().union(*(_number_tokens(t) for t in texts)):
        findings.append(Finding("ROOT_SUPPORTS_CHILDREN", "FAIL", "NUMERIC_OPERATOR_CHANGE", "Numeric/threshold token set changed."))

    # Collective-to-distributive guard for explicit marker.
    if "jointly" in _tokens(root) and "jointly" not in child_union:
        findings.append(Finding("REFERENCE_ARGUMENT_BINDING", "FAIL", "COLLECTIVE_RELATION_DISTRIBUTED", "Explicit collective marker `jointly` was lost during split."))

    hard_fail = any(f.status == "FAIL" and f.dimension != "STRUCTURAL_VALIDITY" for f in findings)
    semantic_indeterminate = any(f.status == "INDETERMINATE" for f in findings)
    disposition = "REJECT_UNSAFE" if hard_fail else ("INDETERMINATE" if semantic_indeterminate else "ACCEPTABLE_WITHIN_PROFILE")
    return _result(candidate, disposition, findings)


def _result(candidate: dict[str, Any], disposition: str, findings: Iterable[Finding]) -> dict[str, Any]:
    if disposition not in DISPOSITIONS:
        raise ValueError(disposition)
    serial = [asdict(f) for f in findings]
    out = {
        "schema_version": "pc-evaluator-result-rc0.1",
        "profile_id": candidate.get("profile_id"),
        "case_id": candidate.get("case_id"),
        "root_id": candidate.get("root_id"),
        "candidate_state": candidate.get("candidate_state"),
        "disposition": disposition,
        "findings": serial,
    }
    canonical_without_hash = _canonical(out)
    out["canonical_sha256"] = _sha256_text(canonical_without_hash)
    return out


def evaluate_jsonl(path: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                results.append(evaluate(json.loads(line)))
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_jsonl")
    parser.add_argument("output_jsonl")
    args = parser.parse_args()
    results = evaluate_jsonl(args.input_jsonl)
    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f:
        for result in results:
            f.write(_canonical(result) + "\n")
