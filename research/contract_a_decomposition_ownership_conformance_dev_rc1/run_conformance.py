from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pydantic import ValidationError

from claim_audit_lab.contracts.cb_models import CBClaim
from claim_audit_lab.contracts.bundle_loader import BundleContents
from claim_audit_lab.contracts.factual_context import (
    ContractBFactualContext,
    _semantic_context,
    _validate_extension,
    canonical_bytes,
)

SNAPSHOT_SHA256 = "8dbedd537c024c4a624f21abd5fa11536ddfe558000f3a9366584c30c045e31c"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_hash(value: Any) -> str:
    payload = (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()
    return _sha256_bytes(payload)


def _load_snapshot(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if _sha256_bytes(raw) != SNAPSHOT_SHA256:
        raise RuntimeError("fixed retrieval snapshot hash mismatch")
    return json.loads(raw)


def _base_claim(claim_id: str, claim_text: str) -> CBClaim:
    return CBClaim.model_validate(
        {
            "claim_id": claim_id,
            "bundle_id": "research-shadow-bundle",
            "schema_version": "1.2.0",
            "claim_text": claim_text,
            "claim_type": "extracted_claim",
            "workflow_condition": "baseline",
            "task_id": "contract-a-decomposition-ownership-dev-rc1",
            "scaffold_support_status": "uncertain",
            "scaffold_claim_strength": 0.5,
            "scaffold_extraction_fidelity": 1.0,
            "scaffold_counterevidence_found": False,
            "scaffold_downgraded": False,
            "evidence_passages": [],
            "counterevidence_passages": [],
            "audit": {},
        }
    )


@dataclass(frozen=True)
class ShadowBundle:
    claims: list[CBClaim]
    source_profiles: dict[str, Any]
    passages: dict[str, list[Any]]


def _shadow_bundle(snapshot: dict[str, Any], claims: list[CBClaim]) -> ShadowBundle:
    passages: dict[str, list[Any]] = {}
    source_profiles: dict[str, Any] = {}
    for hit in snapshot["hits"]:
        source_id = str(hit["source_id"])
        source_profiles[source_id] = SimpleNamespace(source_id=source_id)
        passages.setdefault(source_id, []).append(
            SimpleNamespace(
                source_id=source_id,
                passage_id=str(hit["paragraph_id"]),
            )
        )
    return ShadowBundle(
        claims=claims,
        source_profiles=source_profiles,
        passages=passages,
    )


def _history_rows(
    snapshot: dict[str, Any],
    *,
    representation: str,
    mutation: bool,
) -> list[dict[str, Any]]:
    children = sorted(snapshot["children"], key=lambda row: int(row["sequence"]))
    first_child = str(children[0]["child_id"])
    rows: list[dict[str, Any]] = []
    for index, hit in enumerate(snapshot["hits"], start=1):
        query_hit = hit["query_hits"][0]
        actual_child = str(query_hit["child_id"])
        represented_child = first_child if mutation else actual_child
        canonical_claim_id = (
            str(snapshot["original_claim_id"])
            if representation == "query_lineage"
            else represented_child
        )
        rows.append(
            {
                "link_id": f"history-{index:02d}",
                "claim_id": canonical_claim_id,
                "passage_id": str(hit["paragraph_id"]),
                "nomination": {
                    "method": "semantic",
                    "decomposition_id": snapshot["decomposition_id"],
                    "child_id": represented_child,
                    "query_id": (
                        f"{snapshot['decomposition_id']}:{represented_child}"
                    ),
                    "query_text": next(
                        child["text"]
                        for child in children
                        if child["child_id"] == represented_child
                    ),
                    "rank": query_hit["rank"],
                    "score": query_hit["score"],
                    "mutation": mutation,
                },
                "review": {
                    "decision": "accepted",
                    "reviewer": "research-shadow",
                },
            }
        )
    return rows


def _claim_contexts(
    snapshot: dict[str, Any],
    *,
    representation: str,
) -> list[dict[str, Any]]:
    if representation == "query_lineage":
        return [
            {
                "claim_id": snapshot["original_claim_id"],
                "origin": {
                    "state": "known",
                    "value": {
                        "representation": "query_lineage",
                        "decomposition_id": snapshot["decomposition_id"],
                    },
                },
                "atomicity": {
                    "state": "known",
                    "value": "composite",
                },
            }
        ]

    rows = [
        {
            "claim_id": snapshot["original_claim_id"],
            "origin": {
                "state": "known",
                "value": {
                    "representation": "parent",
                    "decomposition_id": snapshot["decomposition_id"],
                },
            },
            "atomicity": {
                "state": "known",
                "value": "composite",
            },
        }
    ]
    for child in snapshot["children"]:
        rows.append(
            {
                "claim_id": child["child_id"],
                "origin": {
                    "state": "known",
                    "value": {
                        "representation": "first_class_child",
                        "parent_claim_id": snapshot["original_claim_id"],
                        "decomposition_id": snapshot["decomposition_id"],
                        "sequence": child["sequence"],
                    },
                },
                "atomicity": {
                    "state": "known",
                    "value": "atomic-child",
                },
            }
        )
    return rows


def _extension(
    snapshot: dict[str, Any],
    *,
    representation: str,
    mutation: bool,
) -> ContractBFactualContext:
    history = _history_rows(
        snapshot,
        representation=representation,
        mutation=mutation,
    )
    claim_ids = sorted({row["claim_id"] for row in history})
    counts = []
    for claim_id in claim_ids:
        count = sum(1 for row in history if row["claim_id"] == claim_id)
        counts.append(
            {
                "claim_id": claim_id,
                "candidate": count,
                "reviewed": count,
                "admitted": count,
            }
        )
    return ContractBFactualContext.model_validate(
        {
            "schema": "contract-b-factual-context-v1",
            "history_complete": True,
            "claims": _claim_contexts(snapshot, representation=representation),
            "sources": [],
            "passages": [
                {
                    "passage_id": hit["paragraph_id"],
                    "anchors": [
                        {
                            "type": "research_paragraph_identity",
                            "value": {
                                "source_id": hit["source_id"],
                                "paragraph_index": hit["paragraph_index"],
                            },
                        }
                    ],
                }
                for hit in snapshot["hits"]
            ],
            "history": history,
            "history_count_checks": counts,
            "aperture": [
                {
                    "claim_id": claim_id,
                    "search_scope": {
                        "fixed_retrieval_snapshot_sha256": SNAPSHOT_SHA256,
                        "retriever": snapshot["retriever"],
                        "budget_regime": snapshot["budget_regime"],
                    },
                    "outcome": {"state": "unknown", "value": None},
                    "limitations": [
                        "No proposition-specific completeness conclusion is asserted."
                    ],
                }
                for claim_id in claim_ids
            ],
        }
    )


def _claims_for_representation(
    snapshot: dict[str, Any],
    representation: str,
) -> list[CBClaim]:
    parent = _base_claim(
        str(snapshot["original_claim_id"]),
        str(snapshot["original_claim_text"]),
    )
    if representation == "query_lineage":
        return [parent]
    children = [
        _base_claim(str(child["child_id"]), str(child["text"]))
        for child in sorted(snapshot["children"], key=lambda row: int(row["sequence"]))
    ]
    return [parent, *children]


def _child_coverage_from_history(
    extension: ContractBFactualContext,
    child_ids: list[str],
) -> dict[str, int]:
    counts = {child_id: 0 for child_id in child_ids}
    for link in extension.history:
        child_id = link.nomination.get("child_id")
        if child_id in counts and link.review["decision"] == "accepted":
            counts[child_id] += 1
    return counts


def _child_coverage_from_semantic_context(
    context: dict[str, Any],
    child_ids: list[str],
) -> dict[str, int]:
    by_claim = {row["claim_id"]: row for row in context["claims"]}
    return {
        child_id: len(by_claim.get(child_id, {}).get("admitted_passages", []))
        for child_id in child_ids
    }


def run(snapshot_path: Path) -> dict[str, Any]:
    snapshot = _load_snapshot(snapshot_path)
    child_ids = [
        str(row["child_id"])
        for row in sorted(snapshot["children"], key=lambda row: int(row["sequence"]))
    ]
    passage_union = sorted(str(hit["paragraph_id"]) for hit in snapshot["hits"])

    strict_model_rejects_inline_propositions = False
    try:
        payload = _base_claim(
            str(snapshot["original_claim_id"]),
            str(snapshot["original_claim_text"]),
        ).model_dump(mode="json")
        payload["propositions"] = [
            {"child_id": child["child_id"], "text": child["text"]}
            for child in snapshot["children"]
        ]
        CBClaim.model_validate(payload)
    except ValidationError:
        strict_model_rejects_inline_propositions = True

    arms: dict[str, Any] = {}
    for representation in ("query_lineage", "proposition_lineage"):
        claims = _claims_for_representation(snapshot, representation)
        bundle = _shadow_bundle(snapshot, claims)
        actual_ext = _extension(
            snapshot,
            representation=representation,
            mutation=False,
        )
        mutated_ext = _extension(
            snapshot,
            representation=representation,
            mutation=True,
        )
        _validate_extension(bundle, actual_ext)
        _validate_extension(bundle, mutated_ext)

        actual_context = _semantic_context(bundle, actual_ext)
        mutated_context = _semantic_context(bundle, mutated_ext)
        actual_context_hash = _canonical_hash(actual_context)
        mutated_context_hash = _canonical_hash(mutated_context)

        actual_history_coverage = _child_coverage_from_history(actual_ext, child_ids)
        mutated_history_coverage = _child_coverage_from_history(mutated_ext, child_ids)
        actual_semantic_coverage = _child_coverage_from_semantic_context(
            actual_context,
            child_ids,
        )
        mutated_semantic_coverage = _child_coverage_from_semantic_context(
            mutated_context,
            child_ids,
        )

        arms[representation] = {
            "canonical_claim_ids": sorted(claim.claim_id for claim in claims),
            "canonical_claim_count": len(claims),
            "passage_union": passage_union,
            "passage_union_sha256": _canonical_hash(passage_union),
            "actual_extension_sha256": _sha256_bytes(canonical_bytes(actual_ext)),
            "mutated_extension_sha256": _sha256_bytes(canonical_bytes(mutated_ext)),
            "actual_intake_child_coverage": actual_history_coverage,
            "mutated_intake_child_coverage": mutated_history_coverage,
            "actual_semantic_child_coverage": actual_semantic_coverage,
            "mutated_semantic_child_coverage": mutated_semantic_coverage,
            "actual_semantic_context_sha256": actual_context_hash,
            "mutated_semantic_context_sha256": mutated_context_hash,
            "semantic_context_collision": actual_context_hash == mutated_context_hash,
            "semantic_context": actual_context,
            "mutated_semantic_context": mutated_context,
        }

    query_arm = arms["query_lineage"]
    proposition_arm = arms["proposition_lineage"]

    if query_arm["actual_intake_child_coverage"] != {
        child_ids[0]: 6,
        child_ids[1]: 6,
    }:
        raise RuntimeError("unexpected frozen actual child coverage")
    if query_arm["mutated_intake_child_coverage"] != {
        child_ids[0]: 12,
        child_ids[1]: 0,
    }:
        raise RuntimeError("mutation did not create intended child-coverage counterfactual")
    if not query_arm["semantic_context_collision"]:
        raise RuntimeError("query-lineage critical collision falsifier did not occur")
    if proposition_arm["semantic_context_collision"]:
        raise RuntimeError("proposition-lineage failed to distinguish attribution mutation")
    if not strict_model_rejects_inline_propositions:
        raise RuntimeError("current strict Contract-B claim unexpectedly accepts propositions field")
    if query_arm["passage_union_sha256"] != proposition_arm["passage_union_sha256"]:
        raise RuntimeError("retrieved passage union changed between representations")

    return {
        "schema_version": "1.0",
        "experiment": "contract-a-decomposition-ownership-conformance-dev-rc1",
        "snapshot_sha256": SNAPSHOT_SHA256,
        "original_claim_id": snapshot["original_claim_id"],
        "child_ids": child_ids,
        "strict_contract_b_claim_rejects_inline_propositions": (
            strict_model_rejects_inline_propositions
        ),
        "fixed_passage_union_count": len(passage_union),
        "fixed_passage_union_sha256": query_arm["passage_union_sha256"],
        "query_lineage_collision_observed": query_arm["semantic_context_collision"],
        "proposition_lineage_distinguishes_mutation": (
            not proposition_arm["semantic_context_collision"]
        ),
        "arms": arms,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "snapshot_sha256": result["snapshot_sha256"],
                "strict_contract_b_claim_rejects_inline_propositions": result[
                    "strict_contract_b_claim_rejects_inline_propositions"
                ],
                "fixed_passage_union_count": result["fixed_passage_union_count"],
                "query_lineage_collision_observed": result[
                    "query_lineage_collision_observed"
                ],
                "proposition_lineage_distinguishes_mutation": result[
                    "proposition_lineage_distinguishes_mutation"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
