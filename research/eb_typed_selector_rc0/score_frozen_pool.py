from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

GENERIC_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
GENERIC_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
EXPECTED_ARTIFACT_SHA256 = "3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d"


def load_selector():
    module_path = Path(__file__).with_name("selector.py")
    spec = importlib.util.spec_from_file_location("eb_typed_selector_rc0_selector", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load selector module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_model() -> tuple[Any, Any]:
    tokenizer = AutoTokenizer.from_pretrained(
        GENERIC_MODEL, revision=GENERIC_REVISION, trust_remote_code=False
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        GENERIC_MODEL, revision=GENERIC_REVISION, trust_remote_code=False
    )
    model.eval()
    return tokenizer, model


def semantic_score(tokenizer: Any, model: Any, claim: str, passage: str) -> float:
    encoded = tokenizer(claim, passage, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = model(**encoded).logits
    if logits.shape[-1] != 1:
        raise RuntimeError(f"expected one reranker logit, got {tuple(logits.shape)}")
    return float(torch.sigmoid(logits[0, 0]).item())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-zip", required=True)
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    artifact = Path(args.artifact_zip)
    if sha256_file(artifact) != EXPECTED_ARTIFACT_SHA256:
        raise SystemExit("artifact digest mismatch")

    profiles_payload = json.loads(Path(args.profiles).read_text(encoding="utf-8"))
    profiles = dict(profiles_payload["profiles"])
    with zipfile.ZipFile(artifact) as archive:
        receipt = json.loads(archive.read("artifacts/k7/TREATMENT_10_7_RECEIPT.json"))

    propositions: dict[str, str] = {}
    lanes: dict[str, list[dict[str, Any]]] = {}
    for case in receipt["cases"]:
        for target in case["primary_targets"]:
            propositions[str(target["proposition_id"])] = str(target["text"])
        for row in case["raw_retrieval"]:
            proposition_id = str(row["proposition_id"])
            if proposition_id in profiles:
                lanes.setdefault(proposition_id, []).append(dict(row))

    tokenizer, model = load_model()
    selector = load_selector()
    materialized = []
    for proposition_id in sorted(profiles):
        rows = sorted(
            lanes[proposition_id], key=lambda row: (int(row["rank"]), str(row["evidence_id"]))
        )
        claim = propositions[proposition_id]
        candidates = []
        for row in rows:
            candidates.append(
                {
                    "evidence_id": row["evidence_id"],
                    "text": row["text"],
                    "rank": row["rank"],
                    "bm25_score": row["score"],
                    "semantic_score": semantic_score(tokenizer, model, claim, str(row["text"])),
                    "metadata": {},
                }
            )
        materialized.append(
            {
                "proposition_id": proposition_id,
                "proposition_text": claim,
                "claim_profile": profiles[proposition_id],
                "candidates": candidates,
            }
        )

    result = {
        "schema": "eb-typed-selector-rc0-known-case-development-v1",
        "classification": "KNOWN_CASE_DEVELOPMENT_ONLY_NO_PROMOTION_AUTHORITY",
        "artifact_sha256": EXPECTED_ARTIFACT_SHA256,
        "semantic_model": {"name": GENERIC_MODEL, "revision": GENERIC_REVISION},
        "lanes": [selector.run_lane(lane) for lane in materialized],
        "nonclaims": [
            "The profiles are answer-aware development scaffolds.",
            "The output is not fresh evidence and cannot authorize selector promotion.",
            "No CAL output, SUPPORTS/REFUTES label, or downstream verdict is used by the scorer or selector.",
        ],
    }
    output = selector.canonical_json(result) + "\n"
    Path(args.output).write_text(output, encoding="utf-8")
    print(selector.sha256_text(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
