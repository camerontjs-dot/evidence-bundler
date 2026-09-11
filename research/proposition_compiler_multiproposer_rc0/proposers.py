from __future__ import annotations

import hashlib
import json
import re
from typing import Iterable

PROFILE_ID = "pc-evaluator-rc1-binding-v1"

VERBS = {
    "reviewed", "review", "reviews", "approved", "approve", "approves",
    "acquired", "acquire", "acquires", "notified", "notify", "notifies",
    "logged", "log", "logs", "stored", "store", "stores", "cached", "cache", "caches",
    "recorded", "record", "records", "inspected", "inspect", "inspects", "retested", "retest", "retests",
    "sealed", "seal", "seals", "labeled", "labelled", "label", "labels", "encrypted", "encrypt", "encrypts",
    "authenticated", "authenticate", "authenticates", "reduced", "reduce", "reduces", "increased", "increase", "increases",
    "decreased", "decrease", "decreases", "caused", "cause", "causes", "filed", "file", "files",
    "signed", "sign", "signs", "sent", "send", "sends", "shipped", "ship", "ships", "delivered", "deliver", "delivers",
    "transferred", "transfer", "transfers", "sold", "sell", "sells", "bought", "buy", "buys", "preceded", "precede", "precedes",
    "followed", "follow", "follows", "examined", "examine", "examines", "measured", "measure", "measures", "archived", "archive", "archives",
    "processed", "process", "processes", "scanned", "scan", "scans", "restarted", "restart", "restarts", "started", "start", "starts",
    "stopped", "stop", "stops", "sounded", "sound", "sounds", "failed", "fail", "fails", "passed", "pass", "passes",
    "recovered", "recover", "recovers", "rose", "rise", "rises", "fell", "fall", "falls", "changed", "change", "changes",
    "dimmed", "dim", "dims", "arrived", "arrive", "arrives", "departed", "depart", "departs",
}
MODALS = {"may", "might", "must", "should", "can", "could", "will", "would"}
AUX = {"did", "is", "was", "are", "were", "be"}
PRONOUNS = {"it", "they", "he", "she", "them", "him", "her"}
SHARED_PREFIX = re.compile(
    r"^(?P<prefix>(?:During|Among|At|In|If|Except for|According to)\s+[^,]+),\s*(?P<body>.+)$",
    re.I,
)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).strip()


def strip_period(text: str) -> str:
    return norm(text).rstrip(".")


def sentence(text: str) -> str:
    text = norm(text).rstrip(".")
    return text + "."


def tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9%'-]+", text)


def has_predicate(text: str) -> bool:
    low = [t.lower() for t in tokens(text)]
    if any(t in VERBS for t in low):
        return True
    if any(t in {"faster", "slower", "higher", "lower", "greater", "less", "cheaper", "larger", "smaller"} for t in low):
        return True
    return bool(re.search(r"\b(?:is|was|are|were)\s+(?:not\s+)?(?:encrypted|authenticated|compliant|ready|active|inactive|sealed|labeled|below|above)\b", text, re.I))


def first_predicate_index(text: str) -> int | None:
    ts = tokens(text)
    low = [t.lower() for t in ts]
    for i, t in enumerate(low):
        if t in MODALS and i + 1 < len(low):
            return i
        if t in VERBS:
            return i
        if t in AUX and i + 1 < len(low):
            return i
    return None


def subject_prefix(text: str) -> str | None:
    idx = first_predicate_index(text)
    if idx is None or idx <= 0:
        return None
    return " ".join(tokens(text)[:idx])


def right_has_explicit_subject(text: str) -> bool:
    idx = first_predicate_index(text)
    return idx is not None and idx > 0


def right_starts_predicate(text: str) -> bool:
    ts = tokens(text)
    if not ts:
        return False
    first = ts[0].lower()
    if first in VERBS or first in MODALS or first == "did":
        return True
    if first in {"is", "was", "are", "were"}:
        return True
    return False


def split_candidates(body: str) -> list[tuple[str, str]]:
    body = strip_period(body)
    out: list[tuple[str, str]] = []
    for m in re.finditer(r"\s+and\s+", body, re.I):
        left = body[: m.start()].strip(" ,")
        right = body[m.end() :].strip(" ,")
        if left and right:
            out.append((left, right))
    return out


def choose_surface_split(body: str, *, shared_subject_only: bool = False, full_clauses_only: bool = False) -> tuple[str, str] | None:
    options = split_candidates(body)
    for left, right in options:
        if not has_predicate(left):
            continue
        if full_clauses_only:
            if has_predicate(right) and right_has_explicit_subject(right):
                return left, right
            continue
        if shared_subject_only:
            if right_starts_predicate(right) and not right_has_explicit_subject(right):
                return left, right
            continue
        if has_predicate(right) or right_starts_predicate(right):
            return left, right
    return None


def apply_prefix(prefix: str | None, clause: str) -> str:
    if not prefix:
        return sentence(clause)
    return sentence(f"{prefix}, {strip_period(clause)}")


def make_candidate(root: dict, proposer: str, variant: str, children: list[str]) -> dict:
    return {
        "case_id": f"{root['root_id']}::{proposer}::{variant}",
        "root_id": root["root_id"],
        "root_text": root["root_text"],
        "context_text": root.get("context_text", ""),
        "profile_id": PROFILE_ID,
        "candidate_state": "DECLARED",
        "operator": "all_of",
        "children": [
            {"child_id": f"{root['root_id']}::{proposer}::{variant}::c{i+1}", "text": sentence(text)}
            for i, text in enumerate(children)
        ],
        "proposal_meta": {"proposer": proposer, "variant": variant},
    }


def dedupe(candidates: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for c in candidates:
        sig = json.dumps([x["text"] for x in c["children"]], ensure_ascii=False, separators=(",", ":"))
        if sig in seen:
            continue
        seen.add(sig)
        out.append(c)
    return out


def proposer_p1(root: dict) -> list[dict]:
    """Conservative surface splitter: shared-subject coordination only."""
    text = strip_period(root["root_text"])
    prefix = None
    body = text
    m = SHARED_PREFIX.match(text)
    if m:
        prefix, body = m.group("prefix"), m.group("body")
    split = choose_surface_split(body, shared_subject_only=True)
    if not split:
        return []
    left, right = split
    subj = subject_prefix(left)
    if not subj:
        return []
    right_full = f"{subj} {right}"
    return [make_candidate(root, "P1", "shared-subject", [apply_prefix(prefix, left), apply_prefix(prefix, right_full)])]


def proposer_p2(root: dict) -> list[dict]:
    """Relation-guided splitter: two explicit proposition clauses."""
    text = strip_period(root["root_text"])
    prefix = None
    body = text
    m = SHARED_PREFIX.match(text)
    if m:
        prefix, body = m.group("prefix"), m.group("body")
    split = choose_surface_split(body, full_clauses_only=True)
    if not split:
        return []
    left, right = split
    first = tokens(right)[0].lower() if tokens(right) else ""
    if first in PRONOUNS:
        return []
    return [make_candidate(root, "P2", "explicit-clauses", [apply_prefix(prefix, left), apply_prefix(prefix, right)])]


def _context_unique_referent(context: str) -> str | None:
    m = re.search(r"\bonly\s+(?:the\s+)?([A-Za-z][A-Za-z0-9 -]*?)(?:\s+was|\s+is|\s+remained|\s+stayed|\s+continued)\b", context, re.I)
    return norm(m.group(1)) if m else None


def _expand_ellipsis(left: str, right: str) -> str | None:
    m = re.match(r"^(.+?)\s+did\s+too$", strip_period(right), re.I)
    if not m:
        return None
    new_subj = norm(m.group(1))
    idx = first_predicate_index(left)
    if idx is None:
        return None
    ts = tokens(left)
    inherited = " ".join(ts[idx:])
    return f"{new_subj} {inherited}"


def proposer_p3(root: dict) -> list[dict]:
    """Specialist alternative proposer for reference, ellipsis, and scope stress variants."""
    text = strip_period(root["root_text"])
    prefix = None
    body = text
    m = SHARED_PREFIX.match(text)
    if m:
        prefix, body = m.group("prefix"), m.group("body")

    outs: list[dict] = []
    for left, right in split_candidates(body):
        if not has_predicate(left):
            continue
        subj = subject_prefix(left)
        variants: list[tuple[str, list[str]]] = []

        ell = _expand_ellipsis(left, right)
        if ell:
            variants.append(("ellipsis-expanded", [apply_prefix(prefix, left), apply_prefix(prefix, ell)]))

        ts = tokens(right)
        if ts and ts[0].lower() in PRONOUNS and has_predicate(right):
            variants.append(("reference-preserving", [apply_prefix(prefix, left), apply_prefix(prefix, right)]))
            ref = _context_unique_referent(root.get("context_text", ""))
            if ref:
                rest = " ".join(ts[1:])
                variants.append(("reference-explicit", [apply_prefix(prefix, left), apply_prefix(prefix, f"{ref} {rest}")]))

        if prefix and subj and right_starts_predicate(right) and not right_has_explicit_subject(right):
            variants.append(("scope-left-only", [apply_prefix(prefix, left), sentence(f"{subj} {right}")]))
            variants.append(("scope-right-only", [sentence(left), apply_prefix(prefix, f"{subj} {right}")]))

        for name, children in variants:
            outs.append(make_candidate(root, "P3", name, children))
    return dedupe(outs)


PROPOSERS = {"P1": proposer_p1, "P2": proposer_p2, "P3": proposer_p3}


def proposal_snapshot(root: dict) -> dict[str, list[dict]]:
    return {name: fn(root) for name, fn in PROPOSERS.items()}


def snapshot_hash(snapshot: dict) -> str:
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
