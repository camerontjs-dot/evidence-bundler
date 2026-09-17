from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from evidence_bundler.ingest import chunk_source_documents
from evidence_bundler.models.document import ChunkSpec
from evidence_bundler.v1.builder import _source_documents, build_package
from evidence_bundler.v1.package import V1Config
from evidence_bundler.v1.retrieval import query_bm25

EXPECTED_POOL_RAW_SHA256 = "4171d50b53374ef67fd877ac9f0ada5d1998b0de43993be8540ff9ea053b84f6"
EXPECTED_CLAIMS_RAW_SHA256 = "0e142d3bace270f9c7d45c7c35f3b1e17ab06156ed936681c98ccdaf39f6e15d"
EXPECTED_SOURCES_RAW_SHA256 = "943a68853863b1479fb1a9621fca1075ba832fe6fb77bdc2d9084f84013d8e4c"
EXPECTED_SELECTOR_SHA256 = "e83e6305008a0f7a264cde2167bff80ce6399f03d34ebce10376f106c52cec6c"
EXPECTED_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
EXPECTED_MODEL_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
EXPECTED_CONFIG_SHA256 = "sha256:5b10d0c29794e80d6876a99e26bcf6ec6a27a4c5165aee78054a6bc32759f4bc"

ARM_BINDING = {
    "ARM_A": "bm25_top3",
    "ARM_B": "semantic_top3",
    "ARM_C": "typed_top3",
    "ARM_D": "typed_without_evidence_posture",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def index_lanes(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload.get("lanes")
    if not isinstance(rows, list):
        raise RuntimeError("payload.lanes must be a list")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        lane_id = str(row["lane_id"])
        if lane_id in out:
            raise RuntimeError(f"duplicate lane: {lane_id}")
        out[lane_id] = dict(row)
    return out


def verify_frozen_files(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    pools_path = root / "AUTHORITATIVE_CANDIDATE_POOLS.json"
    claims_path = root / "FROZEN_CLAIMS_PROFILES.json"
    sources_path = root / "SOURCE_FIXTURES_V2.json"
    expected = [
        (pools_path, EXPECTED_POOL_RAW_SHA256),
        (claims_path, EXPECTED_CLAIMS_RAW_SHA256),
        (sources_path, EXPECTED_SOURCES_RAW_SHA256),
    ]
    for path, digest in expected:
        actual = sha256_file(path)
        if actual != digest:
            raise RuntimeError(f"frozen input hash mismatch for {path.name}: {actual}")
    return (
        json.loads(pools_path.read_text(encoding="utf-8")),
        json.loads(claims_path.read_text(encoding="utf-8")),
        json.loads(sources_path.read_text(encoding="utf-8")),
    )


def recover_target_input(
    fresh_root: Path,
    target_root: Path,
    mode: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    pools, claims_payload, sources_payload = verify_frozen_files(fresh_root)

    selector_path = target_root / "research/eb_typed_selector_rc0/selector.py"
    scorer_path = target_root / "research/eb_typed_selector_rc0/score_frozen_pool.py"
    if sha256_file(selector_path) != EXPECTED_SELECTOR_SHA256:
        raise RuntimeError("selector source hash mismatch")
    selector = load_module(selector_path, "rc1_frozen_selector")
    scorer = load_module(scorer_path, "rc1_frozen_scorer")
    if scorer.GENERIC_MODEL != EXPECTED_MODEL or scorer.GENERIC_REVISION != EXPECTED_MODEL_REVISION:
        raise RuntimeError("semantic scorer model/revision drift")

    helper_path = fresh_root / "authoritative_first_stage.py"
    helper = load_module(helper_path, "rc1_authoritative_first_stage")
    claims = helper.validate_claims_profiles(claims_payload)
    sources = helper.validate_sources(sources_payload, claims)
    pool_by_lane = index_lanes(pools)

    config = V1Config(candidate_depth=10, retained_k=3)
    if config.identity != EXPECTED_CONFIG_SHA256:
        raise RuntimeError("integration config identity drift")

    tokenizer, model = scorer.load_model()
    materialized: list[dict[str, Any]] = []
    score_receipt: list[dict[str, Any]] = []

    for lane_id in sorted(pool_by_lane):
        frozen = pool_by_lane[lane_id]
        claim_row = claims[lane_id]
        claim = str(claim_row["claim"])
        if claim != frozen["claim"] or claim_row["profile"] != frozen["profile"]:
            raise RuntimeError(f"{lane_id}: frozen claim/profile mismatch")

        contract_a = helper.make_contract_a(lane_id, claim, sources[lane_id])
        package = build_package(contract_a=contract_a, config=config, admission=None)
        if package["package_sha256"] != frozen["native_package_sha256"]:
            raise RuntimeError(f"{lane_id}: native package identity mismatch")

        native = sorted(package["candidates"], key=lambda row: int(row["nomination_rank"]))
        frozen_candidates = list(frozen["candidates"])
        if len(native) != 10 or len(frozen_candidates) != 10:
            raise RuntimeError(f"{lane_id}: expected exact depth 10")

        documents = _source_documents(contract_a)
        chunks = chunk_source_documents(
            documents,
            ChunkSpec(
                max_chars=config.chunk_max_chars,
                overlap_chars=config.chunk_overlap_chars,
            ),
        )
        hits = query_bm25(claim, chunks, top_k=10)
        if len(hits) != 10:
            raise RuntimeError(f"{lane_id}: score recovery did not return 10 hits")

        candidates: list[dict[str, Any]] = []
        recovered_scores: list[dict[str, Any]] = []
        for idx, (frozen_row, native_row, hit) in enumerate(
            zip(frozen_candidates, native, hits, strict=True), start=1
        ):
            exact_pairs = {
                "rank": (int(frozen_row["rank"]), idx),
                "candidate_id": (str(frozen_row["candidate_id"]), str(native_row["passage_id"])),
                "source_id": (str(frozen_row["source_id"]), str(hit.chunk.source_id)),
                "char_start": (int(frozen_row["char_start"]), int(hit.chunk.char_start)),
                "char_end": (int(frozen_row["char_end"]), int(hit.chunk.char_end)),
                "text": (str(frozen_row["text"]), str(hit.chunk.text)),
            }
            for field, (left, right) in exact_pairs.items():
                if left != right:
                    raise RuntimeError(f"{lane_id}/rank{idx}: frozen {field} mismatch")
            if int(native_row["nomination_rank"]) != idx:
                raise RuntimeError(f"{lane_id}/rank{idx}: native rank mismatch")
            if str(native_row["passage_sha256"]) != str(frozen_row["passage_sha256"]):
                raise RuntimeError(f"{lane_id}/rank{idx}: passage hash mismatch")

            metadata: dict[str, Any] = {}
            if mode == "irrelevant-metadata":
                metadata["rc1_irrelevant_metadata_control"] = "constant-ignored-value"

            candidates.append(
                {
                    "evidence_id": str(frozen_row["candidate_id"]),
                    "text": str(frozen_row["text"]),
                    "rank": int(frozen_row["rank"]),
                    "bm25_score": float(hit.score),
                    "semantic_score": scorer.semantic_score(
                        tokenizer, model, claim, str(frozen_row["text"])
                    ),
                    "metadata": metadata,
                }
            )
            recovered_scores.append(
                {
                    "candidate_id": str(frozen_row["candidate_id"]),
                    "rank": int(frozen_row["rank"]),
                    "bm25_score": float(hit.score),
                }
            )

        if mode == "permuted":
            candidates = list(reversed(candidates))

        materialized.append(
            {
                "proposition_id": lane_id,
                "proposition_text": claim,
                "claim_profile": dict(frozen["profile"]),
                "candidates": candidates,
            }
        )
        score_receipt.append(
            {
                "lane_id": lane_id,
                "native_package_sha256": frozen["native_package_sha256"],
                "recovered_scores": recovered_scores,
            }
        )

    arm_rows = {arm: [] for arm in ARM_BINDING}
    for lane in materialized:
        result = selector.run_lane(lane)
        lane_id = str(result["proposition_id"])
        for arm, target_name in ARM_BINDING.items():
            selected = [str(x) for x in result["arms"][target_name]]
            if len(selected) > 3 or len(selected) != len(set(selected)):
                raise RuntimeError(f"{arm}/{lane_id}: invalid selected cardinality")
            pool_ids = {str(c["evidence_id"]) for c in lane["candidates"]}
            if not set(selected) <= pool_ids:
                raise RuntimeError(f"{arm}/{lane_id}: selection outside frozen pool")
            arm_rows[arm].append(
                {"lane_id": lane_id, "selected_candidate_ids": selected}
            )

    replay = {
        "schema": "eb-typed-selector-rc1-blind-arm-replay-v1",
        "candidate_pools_raw_sha256": EXPECTED_POOL_RAW_SHA256,
        "arms": arm_rows,
    }
    score_info = {
        "schema": "eb-typed-selector-rc1-score-recovery-receipt-v1",
        "classification": "POST_REVEAL_MECHANICAL_ADAPTER_ONLY",
        "candidate_pools_raw_sha256": EXPECTED_POOL_RAW_SHA256,
        "selector_sha256": EXPECTED_SELECTOR_SHA256,
        "semantic_model": EXPECTED_MODEL,
        "semantic_model_revision": EXPECTED_MODEL_REVISION,
        "integration_config_sha256": EXPECTED_CONFIG_SHA256,
        "all_frozen_candidate_id_rank_text_hash_checks_pass": True,
        "lanes": score_receipt,
    }
    return replay, score_info


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh-root", required=True)
    parser.add_argument("--target-root", required=True)
    parser.add_argument(
        "--mode",
        choices=["baseline", "permuted", "irrelevant-metadata"],
        default="baseline",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--score-receipt")
    args = parser.parse_args()

    replay, score_info = recover_target_input(
        Path(args.fresh_root), Path(args.target_root), args.mode
    )
    Path(args.output).write_text(canonical_json(replay) + "\n", encoding="utf-8")
    if args.score_receipt:
        Path(args.score_receipt).write_text(
            canonical_json(score_info) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
