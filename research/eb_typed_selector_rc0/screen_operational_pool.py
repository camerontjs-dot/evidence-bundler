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
EXPECTED_LANES = 18
EXPECTED_RELATIONSHIPS = 96


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


def cobalt_keys(relation_map: dict[str, Any]) -> set[str]:
    keys = {
        str(row["semantic_key"])
        for row in relation_map["matched_relationships"]
    }
    keys.update(
        str(row["semantic_key"])
        for row in relation_map["larger_arm_only_relationships"]
    )
    if len(keys) != EXPECTED_RELATIONSHIPS:
        raise RuntimeError(f"expected {EXPECTED_RELATIONSHIPS} cobalt keys, got {len(keys)}")
    return keys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-zip", required=True)
    parser.add_argument("--relation-map", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    artifact = Path(args.artifact_zip)
    if sha256_file(artifact) != EXPECTED_ARTIFACT_SHA256:
        raise SystemExit("artifact digest mismatch")

    relation_map = json.loads(Path(args.relation_map).read_text(encoding="utf-8"))
    allowed = cobalt_keys(relation_map)
    with zipfile.ZipFile(artifact) as archive:
        receipt = json.loads(archive.read("artifacts/k7/TREATMENT_10_7_RECEIPT.json"))

    propositions: dict[str, str] = {}
    raw_by_lane: dict[str, list[dict[str, Any]]] = {}
    for case in receipt["cases"]:
        for target in case["primary_targets"]:
            propositions[str(target["proposition_id"])] = str(target["text"])
        for row in case["raw_retrieval"]:
            proposition_id = str(row["proposition_id"])
            semantic_key = f"{proposition_id}|{row['evidence_id']}"
            if semantic_key in allowed:
                raw_by_lane.setdefault(proposition_id, []).append(dict(row))

    if len(raw_by_lane) != EXPECTED_LANES:
        raise RuntimeError(f"expected {EXPECTED_LANES} lanes, got {len(raw_by_lane)}")
    if sum(len(rows) for rows in raw_by_lane.values()) != EXPECTED_RELATIONSHIPS:
        raise RuntimeError("operational relationship count mismatch")

    tokenizer, model = load_model()
    selector = load_selector()
    lanes = []
    for proposition_id in sorted(raw_by_lane):
        claim = propositions[proposition_id]
        rows = sorted(
            raw_by_lane[proposition_id],
            key=lambda row: (int(row["rank"]), str(row["evidence_id"])),
        )
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
        lane = {
            "proposition_id": proposition_id,
            "proposition_text": claim,
            "claim_profile": {
                "requires_direct_evidence": True,
                "concepts": [],
            },
            "candidates": candidates,
        }
        lane_result = selector.run_lane(lane)
        lanes.append(
            {
                "proposition_id": proposition_id,
                "candidate_count": len(candidates),
                "arms": {
                    name: selected
                    for name, selected in lane_result["arms"].items()
                    if name
                    in {
                        "bm25_top3",
                        "semantic_top3",
                        "typed_top3",
                        "typed_without_evidence_posture",
                    }
                },
            }
        )

    result = {
        "schema": "eb-typed-selector-rc0-operational-pool-screen-v1",
        "classification": "RETROSPECTIVE_DEVELOPMENT_SELECTION_ONLY",
        "artifact_sha256": EXPECTED_ARTIFACT_SHA256,
        "semantic_model": {"name": GENERIC_MODEL, "revision": GENERIC_REVISION},
        "profile": {
            "requires_direct_evidence": True,
            "concepts": [],
            "classification": "GENERIC_NON_ANSWER_AWARE_DEVELOPMENT_PROFILE",
        },
        "operational_universe": {
            "lanes": EXPECTED_LANES,
            "relationships": EXPECTED_RELATIONSHIPS,
        },
        "lanes": lanes,
        "nonclaims": [
            "This screen is retrospective development evidence only.",
            "The generic profile is not ClaimGate or EvidenceGate authority.",
            "No operational labels are opened or consumed during selection.",
        ],
    }
    text = selector.canonical_json(result) + "\n"
    Path(args.output).write_text(text, encoding="utf-8")
    print(selector.sha256_text(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
