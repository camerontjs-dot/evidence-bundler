from __future__ import annotations

import argparse, hashlib, importlib.util, json, re, sys
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

PROFILE_ID = "pc-evaluator-rc1-binding-v1"
NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
NLI_REVISION = "fa2804872c3b4bd748f38c0185cc85775361e735"
FLOOR = 0.90
CLUSTER_MARGIN = 0.05

THRESHOLD_RE = re.compile(r"\b(at least|at most|more than|less than)\b", re.I)
MODAL_RE = re.compile(r"\b(may|might|must|should|can|could|will|would)\b", re.I)
PRON_RE = re.compile(r"\b(it|they|them|he|she|him|her)\b", re.I)
DISJ_RE = re.compile(r"\b(?:or|and/or)\b", re.I)
SHARED_PREFIX_RE = re.compile(
    r"^(?P<prefix>(?:during|among|at|in|if|except for|according to|under|within|for)\s+[^,]{1,100}),\s*(?P<body>.+)$",
    re.I,
)


def canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip().rstrip("."))


def load_authority(path: str):
    spec = importlib.util.spec_from_file_location("frozen_rc1_authority_fusion", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen authority")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_nli():
    tok = AutoTokenizer.from_pretrained(NLI_MODEL, revision=NLI_REVISION, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL, revision=NLI_REVISION, trust_remote_code=False)
    model.eval()
    return tok, model


def entailment_probability(tok, model, premise: str, hypothesis: str) -> float:
    enc = tok(premise, hypothesis, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = model(**enc).logits
    probs = torch.softmax(logits, dim=-1)[0]
    labels = {str(model.config.id2label.get(i, i)).lower(): float(v) for i, v in enumerate(probs.tolist())}
    keys = [k for k in labels if "entail" in k]
    if not keys:
        raise RuntimeError(f"no entailment label: {labels}")
    return labels[keys[0]]


def candidate_text(children: list[str]) -> str:
    return " AND ".join(f"({x.strip().rstrip('.')})" for x in children)


def paired(context: str, claim: str) -> str:
    context = context.strip()
    return claim if not context else f"Context: {context} Claim: {claim}"


def authority_candidate(case: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": candidate["candidate_id"],
        "root_id": case["root_id"],
        "root_text": case["root_text"],
        "context_text": case.get("context_text", "") or "",
        "profile_id": PROFILE_ID,
        "candidate_state": "DECLARED",
        "operator": "all_of",
        "children": [
            {"child_id": f"{candidate['candidate_id']}::c{i+1}", "text": str(text)}
            for i, text in enumerate(candidate["children"])
        ],
    }


def cluster_key(authority, clean: dict[str, Any]) -> str:
    frames = []
    for child in clean["children"]:
        parsed = authority.parse_child(child["text"], clean.get("context_text", "") or "")
        if parsed.status != "ok" or len(parsed.frames) != 1:
            raise RuntimeError("accepted candidate did not reparse to one frame")
        frames.append(parsed.frames[0].key())
    return sha_text(canon(sorted(frames)))


def threshold_ops(text: str) -> tuple[str, ...]:
    return tuple(sorted(x.lower() for x in THRESHOLD_RE.findall(text)))


def modal_ops(text: str) -> tuple[str, ...]:
    return tuple(sorted(x.lower() for x in MODAL_RE.findall(text)))


def neg_count(text: str) -> int:
    return len(re.findall(r"\b(?:not|never|no)\b", text, re.I))


def context_unique_reference(context: str) -> bool:
    return bool(re.search(r"\bonly\s+(?:the\s+)?[A-Za-z][A-Za-z0-9 -]*?(?:\s+was|\s+is|\s+remained|\s+stayed|\s+continued)\b", context, re.I))


def root_hazards(case: dict[str, Any]) -> list[str]:
    root = case["root_text"]
    context = case.get("context_text", "") or ""
    out = []
    if DISJ_RE.search(root):
        out.append("DISJUNCTIVE_ROOT")
    if re.search(r"\b(?:did\s+not|does\s+not|do\s+not|not)\b.+\band\b", root, re.I) and neg_count(root) == 1:
        out.append("NEGATION_SCOPE_AMBIGUITY")
    if PRON_RE.search(root) and not context_unique_reference(context):
        out.append("UNRESOLVED_REFERENCE_RISK")
    return out


def candidate_hazards(case: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    root = case["root_text"]
    joined = " ".join(str(x) for x in candidate["children"])
    out = []
    if threshold_ops(root) != threshold_ops(joined):
        out.append("THRESHOLD_OPERATOR_MISMATCH")
    if modal_ops(root) != modal_ops(joined):
        out.append("MODAL_MISMATCH")
    if neg_count(root) != neg_count(joined):
        out.append("NEGATION_MISMATCH")
    m = SHARED_PREFIX_RE.match(root.strip().rstrip("."))
    if m:
        prefix = norm(m.group("prefix"))
        missing = [i for i, child in enumerate(candidate["children"]) if prefix not in norm(str(child))]
        if missing:
            out.append("SHARED_SCOPE_NOT_PRESERVED_ALL_CHILDREN")
    return out


def score_case(authority, nli, case: dict[str, Any]) -> dict[str, Any]:
    tok, model = nli
    context = case.get("context_text", "") or ""
    root_claim = paired(context, case["root_text"])
    root_h = root_hazards(case)
    rows = []
    for candidate in case["candidates"]:
        children = [str(x) for x in candidate["children"]]
        claim = paired(context, candidate_text(children))
        fwd = entailment_probability(tok, model, root_claim, claim)
        rev = entailment_probability(tok, model, claim, root_claim)
        nli_score = min(fwd, rev)
        clean = authority_candidate(case, candidate)
        auth = authority.evaluate(clean)
        row = {
            "candidate_id": candidate["candidate_id"],
            "children": children,
            "source_lane": candidate.get("source_lane", "unspecified"),
            "authority_disposition": auth["disposition"],
            "authority_sha256": auth["canonical_sha256"],
            "candidate_hazards": candidate_hazards(case, candidate),
            "nli_forward": fwd,
            "nli_reverse": rev,
            "nli_score": nli_score,
        }
        if auth["disposition"] == "ACCEPTABLE_WITHIN_PROFILE":
            row["semantic_cluster"] = cluster_key(authority, clean)
        rows.append(row)

    auth_clusters: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        if r["authority_disposition"] == "ACCEPTABLE_WITHIN_PROFILE":
            auth_clusters.setdefault(r["semantic_cluster"], []).append(r)
    if len(auth_clusters) == 1:
        only = next(iter(auth_clusters.values()))
        a0_selected = sorted(only, key=lambda x: (-x["nli_score"], x["candidate_id"]))[0]["candidate_id"]
        a0_state = "SELECT"
    else:
        a0_selected = None
        a0_state = "ABSTAIN"

    if root_h:
        a1_selected = None
        a1_state = "ABSTAIN"
        a1_reason = "ROOT_HAZARD"
    else:
        survivors = [r for r in rows if r["authority_disposition"] == "ACCEPTABLE_WITHIN_PROFILE" and not r["candidate_hazards"]]
        clusters: dict[str, list[dict[str, Any]]] = {}
        for r in survivors:
            clusters.setdefault(r["semantic_cluster"], []).append(r)
        if not clusters:
            a1_selected = None; a1_state = "ABSTAIN"; a1_reason = "NO_AUTHORITY_HAZARD_CLEAN_CANDIDATE"
        elif len(clusters) == 1:
            only = next(iter(clusters.values()))
            best = sorted(only, key=lambda x: (-x["nli_score"], x["candidate_id"]))[0]
            a1_selected = best["candidate_id"]; a1_state = "SELECT"; a1_reason = "UNIQUE_AUTHORITY_CLUSTER"
        else:
            ranked_clusters = []
            for key, members in clusters.items():
                best = sorted(members, key=lambda x: (-x["nli_score"], x["candidate_id"]))[0]
                ranked_clusters.append((best["nli_score"], key, best))
            ranked_clusters.sort(key=lambda x: (-x[0], x[1]))
            top_score, _, top = ranked_clusters[0]
            second_score = ranked_clusters[1][0]
            margin = top_score - second_score
            if top_score >= FLOOR and margin >= CLUSTER_MARGIN:
                a1_selected = top["candidate_id"]; a1_state = "SELECT"; a1_reason = "RERANKER_BREAKS_AUTHORITY_COMPATIBLE_CLUSTER_TIE"
            else:
                a1_selected = None; a1_state = "ABSTAIN"; a1_reason = "MULTIPLE_AUTHORITY_CLUSTERS_LOW_MARGIN"

    return {
        "root_id": case["root_id"],
        "family": case.get("family", "unknown"),
        "root_hazards": root_h,
        "systems": {
            "A0_AUTHORITY_ONLY": {"state": a0_state, "selected": a0_selected, "authority_cluster_count": len(auth_clusters)},
            "A1_FUSION": {"state": a1_state, "selected": a1_selected, "reason": a1_reason},
        },
        "candidates": rows,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--authority", required=True)
    p.add_argument("--cases", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    authority = load_authority(a.authority)
    nli = load_nli()
    cases = [json.loads(x) for x in Path(a.cases).read_text(encoding="utf-8").splitlines() if x.strip()]
    result = {
        "schema_version": "pc-authority-fusion-rc0.1",
        "nli_model": {"name": NLI_MODEL, "revision": NLI_REVISION},
        "resolver": {"floor": FLOOR, "cluster_margin": CLUSTER_MARGIN},
        "rows": [score_case(authority, nli, c) for c in cases],
    }
    text = canon(result) + "\n"
    Path(a.output).write_text(text, encoding="utf-8")
    print(sha_text(text))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
