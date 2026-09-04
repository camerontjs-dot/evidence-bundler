from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
NLI_REVISION = "fa2804872c3b4bd748f38c0185cc85775361e735"
NEGATION = {"not", "no", "never", "neither", "nor", "cannot", "can't", "without"}
MODAL = {"must", "shall", "may", "should", "required", "requires", "cannot", "can", "permitted"}
CONDITION = {"if", "unless", "until", "before", "after", "during", "while", "except", "only"}
TEMPORAL = {"as of", "before", "after", "during", "until", "effective", "revision", "currently", "current"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9][A-Za-z0-9_.-]*", text.lower()))


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?\b", text))


def _markers(text: str, vocabulary: set[str]) -> set[str]:
    lower = text.lower()
    return {value for value in vocabulary if value in lower}


def _scope_tokens(text: str) -> set[str]:
    values = set(re.findall(r"\b(?:[A-Z][A-Za-z0-9-]*|[A-Za-z]+-\d+)\b", text))
    return {value for value in values if len(value) > 1}


def _retention(root: str, children: list[str]) -> dict[str, Any]:
    joined = " ".join(children)
    dimensions = {
        "numbers": (_numbers(root), _numbers(joined)),
        "negation": (_markers(root, NEGATION), _markers(joined, NEGATION)),
        "modal_deontic": (_markers(root, MODAL), _markers(joined, MODAL)),
        "condition_exception": (_markers(root, CONDITION), _markers(joined, CONDITION)),
        "temporal": (_markers(root, TEMPORAL), _markers(joined, TEMPORAL)),
        "scope_entities": (_scope_tokens(root), _scope_tokens(joined)),
    }
    result: dict[str, Any] = {}
    for name, (required, observed) in dimensions.items():
        result[name] = {
            "root_features": sorted(required),
            "child_features": sorted(observed),
            "missing": sorted(required - observed),
            "added": sorted(observed - required),
            "all_root_features_retained": required <= observed,
        }
    return result


def _redundancy(children: list[str]) -> dict[str, Any]:
    pairs: list[float] = []
    for left, right in itertools.combinations(children, 2):
        a, b = _tokens(left), _tokens(right)
        union = a | b
        pairs.append(len(a & b) / len(union) if union else 0.0)
    return {
        "pair_count": len(pairs),
        "mean_pairwise_token_jaccard": (sum(pairs) / len(pairs) if pairs else None),
        "max_pairwise_token_jaccard": (max(pairs) if pairs else None),
    }


def _entailment_probability(logits: torch.Tensor, model: Any) -> tuple[float, dict[str, float]]:
    probs = torch.softmax(logits, dim=-1)[0]
    labels = {
        str(model.config.id2label.get(index, index)).lower(): float(value)
        for index, value in enumerate(probs.tolist())
    }
    entail_keys = [key for key in labels if "entail" in key]
    if not entail_keys:
        raise RuntimeError(f"NLI config has no entailment label: {labels}")
    return labels[entail_keys[0]], labels


def _nli_pair(model: Any, tokenizer: Any, premise: str, hypothesis: str) -> dict[str, Any]:
    encoded = tokenizer(
        premise,
        hypothesis,
        return_tensors="pt",
        truncation=True,
        max_length=min(int(getattr(tokenizer, "model_max_length", 512)), 512),
    )
    with torch.no_grad():
        logits = model(**encoded).logits
    entailment, labels = _entailment_probability(logits, model)
    return {"entailment_probability": entailment, "label_probabilities": labels}


def run(
    *,
    fixture_dir: Path,
    expected_manifest_sha256: str,
    output: Path,
) -> dict[str, Any]:
    manifest_path = fixture_dir / "MANIFEST.json"
    if sha256_bytes(manifest_path.read_bytes()) != expected_manifest_sha256:
        raise RuntimeError("frozen fixture manifest digest mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    tokenizer = AutoTokenizer.from_pretrained(
        NLI_MODEL, revision=NLI_REVISION, trust_remote_code=False
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        NLI_MODEL, revision=NLI_REVISION, trust_remote_code=False
    )
    model.eval()

    rows: list[dict[str, Any]] = []
    strategy_children: dict[str, dict[str, list[str]]] = {}
    for record in manifest["records"]:
        obj = json.loads((fixture_dir / str(record["path"])).read_text(encoding="utf-8"))
        if obj["decomposition"]["state"] != "declared":
            rows.append(
                {
                    "original_claim_id": record["original_claim_id"],
                    "strategy": record["strategy"],
                    "decomposition_state": "failed",
                    "failure_reason": record.get("failure_reason"),
                    "assessment": "ABSTAINED_GENERATION",
                }
            )
            continue
        root = str(obj["root_proposition"]["text"])
        children = [
            str(child["text"])
            for child in sorted(
                obj["decomposition"]["children"], key=lambda row: int(row["sequence"])
            )
        ]
        conjunction = " AND ".join(f"({child})" for child in children)
        root_to_children = _nli_pair(model, tokenizer, root, conjunction)
        children_to_root = _nli_pair(model, tokenizer, conjunction, root)
        retention = _retention(root, children)
        missing_features = sorted(
            {
                feature
                for dimension in retention.values()
                for feature in dimension["missing"]
            }
        )
        bidirectional_min = min(
            float(root_to_children["entailment_probability"]),
            float(children_to_root["entailment_probability"]),
        )
        warnings: list[str] = []
        if missing_features:
            warnings.append("CRITICAL_ROOT_FEATURE_MISSING")
        if bidirectional_min < 0.5:
            warnings.append("LOW_BIDIRECTIONAL_NLI_ENTAILMENT")
        if any(len(_tokens(child)) < 3 for child in children):
            warnings.append("CHILD_LOW_AUDITABILITY_TOKEN_COUNT")
        strategy_children.setdefault(str(record["original_claim_id"]), {})[
            str(record["strategy"])
        ] = children
        rows.append(
            {
                "original_claim_id": record["original_claim_id"],
                "strategy": record["strategy"],
                "decomposition_state": "declared",
                "child_count": len(children),
                "root_to_children_nli": root_to_children,
                "children_to_root_nli": children_to_root,
                "bidirectional_min_entailment_probability": bidirectional_min,
                "critical_feature_retention": retention,
                "redundancy": _redundancy(children),
                "independent_auditability": {
                    "all_children_nonblank": all(bool(child.strip()) for child in children),
                    "all_children_at_least_three_tokens": all(
                        len(_tokens(child)) >= 3 for child in children
                    ),
                },
                "instrument_warnings": warnings,
                "assessment": "INSTRUMENT_WARNING" if warnings else "NO_INSTRUMENT_WARNING",
            }
        )

    disagreements: list[dict[str, Any]] = []
    for claim_id, strategies in sorted(strategy_children.items()):
        for left, right in itertools.combinations(sorted(strategies), 2):
            left_tokens = set().union(*(_tokens(text) for text in strategies[left]))
            right_tokens = set().union(*(_tokens(text) for text in strategies[right]))
            union = left_tokens | right_tokens
            disagreements.append(
                {
                    "original_claim_id": claim_id,
                    "left_strategy": left,
                    "right_strategy": right,
                    "aggregate_token_jaccard": (
                        len(left_tokens & right_tokens) / len(union) if union else None
                    ),
                    "exact_child_list_match": strategies[left] == strategies[right],
                }
            )

    result = {
        "schema_version": "1.0",
        "experiment": manifest["experiment"],
        "fixture_manifest_sha256": expected_manifest_sha256,
        "nli_model": NLI_MODEL,
        "nli_revision": NLI_REVISION,
        "instrument_threshold_note": (
            "0.5 bidirectional entailment is a preregistered warning threshold only; "
            "the NLI instrument does not confer Contract A authority."
        ),
        "rows": rows,
        "generator_disagreement": disagreements,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "declared_assessments": sum(row.get("decomposition_state") == "declared" for row in rows),
        "abstentions": sum(row.get("decomposition_state") == "failed" for row in rows),
        "instrument_warning_count": sum(row.get("assessment") == "INSTRUMENT_WARNING" for row in rows),
        "output_sha256": sha256_bytes(output.read_bytes()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-dir", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(
        fixture_dir=args.fixture_dir,
        expected_manifest_sha256=args.expected_manifest_sha256,
        output=args.output,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
