#!/usr/bin/env python3
"""Run RC1 fresh fixtures through the exact pinned Evidence Bundler V1 first stage.

This apparatus is prereveal-only. It never imports selector code, gold, CAL, or
any downstream verdict system. It must execute with camerontjs-dot/evidence-bundler
checked out and installed at the exact pinned integration-candidate commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from evidence_bundler.v1 import build_package
from evidence_bundler.v1.contract_a import compute_handoff_sha256
from evidence_bundler.v1.package import V1Config

PINNED_EB_COMMIT = "4e1f6fe00e7c350b28f52bfea14f1f8988847884"
PINNED_V1_IMPLEMENTATION = "c4e3f97ec8f0bd36180954c3aa382418925bf947"
INTEGRATION_CONFIG_SHA256 = "sha256:5b10d0c29794e80d6876a99e26bcf6ec6a27a4c5165aee78054a6bc32759f4bc"
EXPECTED_CLAIMS_PROFILES_SHA256 = "sha256:0e142d3bace270f9c7d45c7c35f3b1e17ab06156ed936681c98ccdaf39f6e15d"
SOURCE_SCHEMA = "eb-typed-selector-rc1-successor-source-fixtures-v1"
POOL_SCHEMA = "eb-typed-selector-rc1-authoritative-candidate-pools-v1"
RECEIPT_SCHEMA = "eb-typed-selector-rc1-authoritative-first-stage-receipt-v1"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_obj(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_claims_profiles(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict) or not isinstance(value.get("lanes"), list):
        raise SystemExit("claims/profiles must contain lanes[]")
    if sha256_obj(value) != EXPECTED_CLAIMS_PROFILES_SHA256:
        raise SystemExit("frozen claims/profiles canonical SHA-256 mismatch")
    lanes: dict[str, dict[str, Any]] = {}
    for row in value["lanes"]:
        lane_id = str(row["lane_id"])
        if lane_id in lanes:
            raise SystemExit(f"duplicate claim lane: {lane_id}")
        if not str(row.get("claim", "")).strip():
            raise SystemExit(f"blank claim: {lane_id}")
        if not isinstance(row.get("profile"), dict):
            raise SystemExit(f"missing profile: {lane_id}")
        lanes[lane_id] = row
    if len(lanes) != 30:
        raise SystemExit(f"expected exactly 30 frozen claims, got {len(lanes)}")
    return lanes


def validate_sources(value: Any, claims: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    if not isinstance(value, dict) or value.get("schema") != SOURCE_SCHEMA:
        raise SystemExit(f"source fixtures schema must equal {SOURCE_SCHEMA}")
    if value.get("claims_profiles_sha256") != EXPECTED_CLAIMS_PROFILES_SHA256:
        raise SystemExit("source fixtures claims_profiles_sha256 mismatch")
    rows = value.get("lanes")
    if not isinstance(rows, list):
        raise SystemExit("source fixtures lanes must be an array")
    by_lane: dict[str, list[dict[str, str]]] = {}
    for lane in rows:
        lane_id = str(lane.get("lane_id", ""))
        if lane_id not in claims:
            raise SystemExit(f"unknown source-fixture lane: {lane_id}")
        if lane_id in by_lane:
            raise SystemExit(f"duplicate source-fixture lane: {lane_id}")
        sources = lane.get("sources")
        if not isinstance(sources, list) or not 12 <= len(sources) <= 20:
            raise SystemExit(f"{lane_id}: require 12-20 source passages")
        normalized: list[dict[str, str]] = []
        ids: set[str] = set()
        for source in sources:
            if set(source) != {"source_id", "media_type", "content"}:
                raise SystemExit(f"{lane_id}: source must contain source_id/media_type/content only")
            source_id = str(source["source_id"])
            media_type = str(source["media_type"])
            content = str(source["content"])
            if not source_id or source_id in ids:
                raise SystemExit(f"{lane_id}: source ids must be nonblank and unique")
            if media_type not in {"text/plain; charset=utf-8", "text/markdown; charset=utf-8"}:
                raise SystemExit(f"{lane_id}/{source_id}: unsupported media_type")
            if not content.strip():
                raise SystemExit(f"{lane_id}/{source_id}: blank content")
            # One short source per authored passage keeps the pinned chunking behavior
            # explicit and prevents accidental multi-chunk corpus construction.
            if len(content) > 1700:
                raise SystemExit(f"{lane_id}/{source_id}: content exceeds 1700 chars")
            ids.add(source_id)
            normalized.append({"source_id": source_id, "media_type": media_type, "content": content})
        by_lane[lane_id] = normalized
    if set(by_lane) != set(claims):
        missing = sorted(set(claims) - set(by_lane))
        extra = sorted(set(by_lane) - set(claims))
        raise SystemExit(f"source-fixture lane mismatch missing={missing} extra={extra}")
    return by_lane


def make_contract_a(lane_id: str, claim: str, sources: list[dict[str, str]]) -> dict[str, Any]:
    proposition_id = f"RC1-{lane_id}"
    contract: dict[str, Any] = {
        "schema": "contract-a-wire-candidate-rc2",
        "handoff_id": f"eb-typed-selector-rc1-successor-{lane_id}",
        "producer": {
            "producer_id": "eb-typed-selector-rc1-context-free-author",
            "producer_version": "1",
        },
        "work": {"work_id": f"eb-typed-selector-rc1-{lane_id}"},
        "root_proposition": {
            "proposition_id": proposition_id,
            "text": claim,
            "text_sha256": sha256_text(claim),
        },
        "decomposition": {"state": "not_decomposed"},
        "sources": [
            {
                "source_id": row["source_id"],
                "media_type": row["media_type"],
                "content": row["content"],
                "content_sha256": sha256_text(row["content"]),
            }
            for row in sources
        ],
        "handoff_sha256": "sha256:" + "0" * 64,
    }
    contract["handoff_sha256"] = compute_handoff_sha256(contract)
    return contract


def run_once(
    claims_payload: dict[str, Any],
    source_payload: dict[str, Any],
    contract_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    claims = validate_claims_profiles(claims_payload)
    sources = validate_sources(source_payload, claims)
    config = V1Config(candidate_depth=10, retained_k=3)
    if config.identity != INTEGRATION_CONFIG_SHA256:
        raise SystemExit("pinned integration config identity drift")

    pool_lanes: list[dict[str, Any]] = []
    lane_receipts: list[dict[str, Any]] = []
    contract_dir.mkdir(parents=True, exist_ok=True)

    for lane_id in sorted(claims):
        claim_row = claims[lane_id]
        contract_a = make_contract_a(lane_id, str(claim_row["claim"]), sources[lane_id])
        contract_path = contract_dir / f"{lane_id}.contract-a.json"
        contract_path.write_bytes(canonical_bytes(contract_a) + b"\n")

        package_a = build_package(contract_a=contract_a, config=config, admission=None)
        package_b = build_package(contract_a=contract_a, config=config, admission=None)
        if package_a != package_b or package_a["package_sha256"] != package_b["package_sha256"]:
            raise SystemExit(f"{lane_id}: exact pinned first-stage replay mismatch")
        if package_a["config_sha256"] != INTEGRATION_CONFIG_SHA256:
            raise SystemExit(f"{lane_id}: integration config identity mismatch")
        executions = package_a["retrieval_executions"]
        if len(executions) != 1 or executions[0]["status"] != "completed":
            raise SystemExit(f"{lane_id}: expected one completed retrieval execution")
        if executions[0]["candidate_depth_limit"] != 10 or not executions[0]["candidate_depth_hit"]:
            raise SystemExit(f"{lane_id}: exact depth-10 pool not established")
        candidates = sorted(package_a["candidates"], key=lambda row: int(row["nomination_rank"]))
        if len(candidates) != 10:
            raise SystemExit(f"{lane_id}: expected 10 candidates, got {len(candidates)}")
        ids = [str(row["passage_id"]) for row in candidates]
        if len(ids) != len(set(ids)):
            raise SystemExit(f"{lane_id}: duplicate candidate passage identity")

        pool_lanes.append(
            {
                "lane_id": lane_id,
                "category": int(claim_row["category"]),
                "claim": str(claim_row["claim"]),
                "profile": claim_row["profile"],
                "contract_a_handoff_sha256": contract_a["handoff_sha256"],
                "native_package_sha256": package_a["package_sha256"],
                "candidates": [
                    {
                        "candidate_id": str(row["passage_id"]),
                        "source_id": str(row["source_id"]),
                        "char_start": int(row["char_start"]),
                        "char_end": int(row["char_end"]),
                        "passage_sha256": str(row["passage_sha256"]),
                        "text": str(row["text"]),
                        "rank": int(row["nomination_rank"]),
                        "first_stage_selection_state": str(row["selection_state"]),
                    }
                    for row in candidates
                ],
            }
        )
        lane_receipts.append(
            {
                "lane_id": lane_id,
                "contract_a_sha256": contract_a["handoff_sha256"],
                "native_package_sha256": package_a["package_sha256"],
                "candidate_count": 10,
                "candidate_depth_hit": True,
                "exact_replay": True,
            }
        )

    pools = {
        "schema": POOL_SCHEMA,
        "classification": "PREREVEAL_NON_GOLD_AUTHORITATIVE_FIRST_STAGE_OUTPUT",
        "pinned_eb_commit": PINNED_EB_COMMIT,
        "pinned_v1_implementation": PINNED_V1_IMPLEMENTATION,
        "integration_config_sha256": INTEGRATION_CONFIG_SHA256,
        "claims_profiles_sha256": sha256_obj(claims_payload),
        "source_fixtures_sha256": sha256_obj(source_payload),
        "lanes": pool_lanes,
        "nonclaims": [
            "No candidate usefulness or gold label is produced.",
            "No selector arm is executed.",
            "No CAL or downstream verdict system is called.",
        ],
    }
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "AUTHORITATIVE_FIRST_STAGE_COMPLETE",
        "pinned_eb_commit": PINNED_EB_COMMIT,
        "pinned_v1_implementation": PINNED_V1_IMPLEMENTATION,
        "integration_config_sha256": INTEGRATION_CONFIG_SHA256,
        "claims_profiles_sha256": sha256_obj(claims_payload),
        "source_fixtures_sha256": sha256_obj(source_payload),
        "candidate_pools_sha256": sha256_obj(pools),
        "lane_count": len(pool_lanes),
        "all_lanes_depth_10": True,
        "all_lanes_exact_replay": True,
        "lanes": lane_receipts,
    }
    return pools, receipt


def self_test() -> None:
    claim = "The Solis bench test measured output at 14.2 units after 20 minutes."
    claims = {
        "authoring_order_note": "synthetic apparatus smoke only",
        "lanes": [
            {
                "lane_id": f"L{i:03d}",
                "category": ((i - 1) // 3) + 1,
                "claim": claim.replace("Solis", f"Solis-{i:02d}"),
                "profile": {
                    "requires_direct_evidence": True,
                    "concepts": [{"name": "measurement", "terms": ["14.2 units"], "weight": 1.0}],
                    "evidence_forms": [],
                    "source_roles": [],
                },
            }
            for i in range(1, 31)
        ],
    }
    # Self-test intentionally bypasses the frozen-claims hash check while exercising
    # the exact pinned build_package machinery and 10/3 configuration.
    config = V1Config(candidate_depth=10, retained_k=3)
    assert config.identity == INTEGRATION_CONFIG_SHA256
    for i in range(1, 4):
        text_claim = claim.replace("Solis", f"Smoke-{i}")
        sources = [
            {
                "source_id": f"SMOKE-{i}-S{j:02d}",
                "media_type": "text/plain; charset=utf-8",
                "content": (
                    f"Smoke-{i} record {j}. The bench test context mentions output and timing. "
                    + ("Measured output was 14.2 units after 20 minutes." if j == 8 else f"Control note value was {j}.0 units.")
                ),
            }
            for j in range(1, 13)
        ]
        contract = make_contract_a(f"SMOKE-{i}", text_claim, sources)
        first = build_package(contract_a=contract, config=config, admission=None)
        second = build_package(contract_a=contract, config=config, admission=None)
        assert first == second
        assert len(first["candidates"]) == 10
        assert first["retrieval_executions"][0]["candidate_depth_hit"] is True
    print("AUTHORITATIVE_FIRST_STAGE_SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claims-profiles", type=Path)
    parser.add_argument("--source-fixtures", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.claims_profiles is None or args.source_fixtures is None or args.out_dir is None:
        parser.error("--claims-profiles, --source-fixtures, and --out-dir are required")
    claims_payload = read_json(args.claims_profiles)
    source_payload = read_json(args.source_fixtures)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    contract_dir = args.out_dir / "contract_a"
    pools, receipt = run_once(claims_payload, source_payload, contract_dir)
    (args.out_dir / "CANDIDATE_POOLS_AUTHORITATIVE.json").write_bytes(canonical_bytes(pools) + b"\n")
    (args.out_dir / "FIRST_STAGE_RECEIPT.json").write_bytes(canonical_bytes(receipt) + b"\n")
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
