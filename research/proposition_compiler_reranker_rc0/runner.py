from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

GENERIC_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
GENERIC_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
NLI_REVISION = "fa2804872c3b4bd748f38c0185cc85775361e735"


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9%'-]+", text.lower()))


def candidate_text(children: list[str]) -> str:
    return " AND ".join(f"({child.strip().rstrip('.')})" for child in children)


def paired_text(case: dict[str, Any], claim: str) -> str:
    context = str(case.get("context_text", "") or "").strip()
    if not context:
        return claim
    return f"Context: {context} Claim: {claim}"


def lexical_score(root: str, candidate: str) -> float:
    left = tokens(root)
    right = tokens(candidate)
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def load_model(model_name: str, revision: str):
    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, revision=revision, trust_remote_code=False
    )
    model.eval()
    return tokenizer, model


def generic_score(tokenizer: Any, model: Any, left: str, right: str) -> float:
    encoded = tokenizer(left, right, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = model(**encoded).logits
    if logits.shape[-1] != 1:
        raise RuntimeError(f"generic reranker expected one logit, got {tuple(logits.shape)}")
    return float(torch.sigmoid(logits[0, 0]).item())


def entailment_probability(tokenizer: Any, model: Any, premise: str, hypothesis: str) -> float:
    encoded = tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = model(**encoded).logits
    probs = torch.softmax(logits, dim=-1)[0]
    labels = {
        str(model.config.id2label.get(index, index)).lower(): float(value)
        for index, value in enumerate(probs.tolist())
    }
    keys = [key for key in labels if "entail" in key]
    if not keys:
        raise RuntimeError(f"NLI model has no entailment label: {labels}")
    return labels[keys[0]]


def score_case(
    case: dict[str, Any], generic: tuple[Any, Any], nli: tuple[Any, Any]
) -> dict[str, Any]:
    generic_tokenizer, generic_model = generic
    nli_tokenizer, nli_model = nli
    root = paired_text(case, str(case["root_text"]))
    rows = []
    for candidate in case["candidates"]:
        joined = candidate_text([str(x) for x in candidate["children"]])
        candidate_claim = paired_text(case, joined)
        forward = entailment_probability(nli_tokenizer, nli_model, root, candidate_claim)
        reverse = entailment_probability(nli_tokenizer, nli_model, candidate_claim, root)
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "mutation_family": candidate["mutation_family"],
                "children": candidate["children"],
                "scores": {
                    "B0_lexical": lexical_score(root, candidate_claim),
                    "R1_generic": generic_score(
                        generic_tokenizer, generic_model, root, candidate_claim
                    ),
                    "R2_bidirectional_nli": min(forward, reverse),
                },
                "nli_forward_entailment": forward,
                "nli_reverse_entailment": reverse,
            }
        )
    return {
        "root_id": case["root_id"],
        "family": case["family"],
        "candidate_count": len(rows),
        "candidates": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    cases = [
        json.loads(line)
        for line in Path(args.cases).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    generic = load_model(GENERIC_MODEL, GENERIC_REVISION)
    nli = load_model(NLI_MODEL, NLI_REVISION)
    rows = [score_case(case, generic, nli) for case in cases]
    result = {
        "schema_version": "pc-competing-hypothesis-rerank-rc0.1",
        "models": {
            "R1_generic": {"model": GENERIC_MODEL, "revision": GENERIC_REVISION},
            "R2_bidirectional_nli": {"model": NLI_MODEL, "revision": NLI_REVISION},
        },
        "rows": rows,
    }
    text = canon(result) + "\n"
    Path(args.output).write_text(text, encoding="utf-8")
    print(sha256_text(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
