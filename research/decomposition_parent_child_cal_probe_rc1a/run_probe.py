from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pydantic import ValidationError

from claim_audit_lab.auditor import audit_claims
from claim_audit_lab.classifiers import classify_claim_text
from claim_audit_lab.contracts.cb_models import CBClaim
from claim_audit_lab.contracts.factual_context import (
    ContractBFactualContext,
    _semantic_context,
    _validate_extension,
    canonical_bytes,
)
from claim_audit_lab.models import (
    AuditConfig,
    Claim,
    EvidenceBundle,
    EvidenceExcerpt,
    EvidenceSource,
)

UPSTREAM_RUN_ID = 33890894890
UPSTREAM_APPARATUS_SHA = "6de9d37140bc16301c151a3ca1b148f13df4c3f5"
UPSTREAM_RAW_SHA256 = "58bb4b1a9e93bd6147013a3787b06bb433d09f5aa51a040def520cc420c81707"
UPSTREAM_MANIFEST_SHA256 = "670ee91a4045bfd6cfc6f3d84ab0d2b979745d6d6bb55a9b2cbfd3006e2ff20e"
CAL_SHA = "32275a239b68af383a56bca843e28cbc1e343976"
CONTRACT_AUTHORITY_SHA = "c3563cff66d2c85dcbf575c693056e2d8e4563d4"
PRIMARY_RETRIEVER = "semantic"
BUDGET_MODES = ("equal_total", "equal_per_query")


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_upstream(artifact_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    raw_path = artifact_dir / "raw-retrieval.json"
    manifest_path = artifact_dir / "contract-a-fixtures" / "MANIFEST.json"
    if sha256_bytes(raw_path.read_bytes()) != UPSTREAM_RAW_SHA256:
        raise RuntimeError("RC1A raw retrieval digest mismatch")
    if sha256_bytes(manifest_path.read_bytes()) != UPSTREAM_MANIFEST_SHA256:
        raise RuntimeError("RC1A Contract A manifest digest mismatch")
    raw = _load_json(raw_path)
    manifest = _load_json(manifest_path)
    if raw.get("apparatus_sha") != UPSTREAM_APPARATUS_SHA:
        raise RuntimeError("RC1A apparatus SHA mismatch")
    if raw.get("experiment") != "decomposition-parent-child-complementarity-dev-rc1a":
        raise RuntimeError("unexpected RC1A experiment identity")
    if raw.get("fixture_manifest_sha256") != UPSTREAM_MANIFEST_SHA256:
        raise RuntimeError("raw retrieval does not bind expected Contract A manifest")
    return raw, manifest


def _assessment_view(assessment: Any) -> dict[str, Any]:
    return {
        "claim_id": assessment.claim.id,
        "claim_text": assessment.claim.text,
        "claim_type": assessment.claim.claim_type,
        "support_label": assessment.support_label,
        "risk_label": assessment.risk_label,
        "support_signal": assessment.support_signal,
        "candidate_evidence": [
            {
                "source_id": row.source_id,
                "excerpt_id": row.excerpt_id,
                "score": row.score,
                "source_reliability": row.source_reliability,
            }
            for row in assessment.candidate_evidence
        ],
        "counterevidence": [
            {
                "source_id": row.source_id,
                "excerpt_id": row.excerpt_id,
                "score": row.score,
                "source_reliability": row.source_reliability,
            }
            for row in assessment.counterevidence
        ],
        "rule_flags": [
            {
                "code": flag.code,
                "risk": flag.risk,
                "message": flag.message,
            }
            for flag in assessment.rule_flags
        ],
        "limitations": list(assessment.limitations),
    }


def _bundle_from_hits(hits: list[dict[str, Any]]) -> EvidenceBundle:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        by_source[str(hit["source_id"])].append(hit)
    return EvidenceBundle(
        sources=[
            EvidenceSource(
                id=source_id,
                title=source_id,
                source_type="unknown",
                reliability="unknown",
                excerpts=[
                    EvidenceExcerpt(
                        id=str(hit["paragraph_id"]),
                        text=str(hit["text"]),
                        notes="Frozen RC1A retrieval nomination supplied to research CAL probe.",
                    )
                    for hit in sorted(
                        rows, key=lambda row: str(row["paragraph_id"])
                    )
                ],
            )
            for source_id, rows in sorted(by_source.items())
        ]
    )


def _audit_one(
    *, proposition_id: str, text: str, hits: list[dict[str, Any]]
) -> dict[str, Any]:
    claim = Claim(
        id=proposition_id,
        text=text,
        claim_type=classify_claim_text(text),
        location=None,
    )
    assessments = audit_claims(
        [claim],
        _bundle_from_hits(hits),
        AuditConfig(),
    )
    if len(assessments) != 1:
        raise RuntimeError("CAL did not return exactly one assessment")
    result = _assessment_view(assessments[0])
    result["supplied_passage_ids"] = sorted(str(hit["paragraph_id"]) for hit in hits)
    result["supplied_passage_count"] = len(hits)
    return result


def _lane_hits(
    r2: dict[str, Any], *, proposition_id: str, retrieval_lane: str
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for hit in r2["hits"]:
        relationships = [
            rel
            for rel in hit["relationships"]
            if str(rel["proposition_id"]) == proposition_id
            and str(rel["retrieval_lane"]) == retrieval_lane
        ]
        if relationships:
            hits.append(hit)
    return hits


def _base_cb_claim(claim_id: str, claim_text: str) -> CBClaim:
    return CBClaim.model_validate(
        {
            "claim_id": claim_id,
            "bundle_id": "research-rc1a-cal-probe",
            "schema_version": "1.2.0",
            "claim_text": claim_text,
            "claim_type": "extracted_claim",
            "workflow_condition": "baseline",
            "task_id": "decomposition-parent-child-cal-probe-rc1a",
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


def _shadow_bundle(r2: dict[str, Any], claims: list[CBClaim]) -> ShadowBundle:
    source_profiles: dict[str, Any] = {}
    passages: dict[str, list[Any]] = defaultdict(list)
    for hit in r2["hits"]:
        source_id = str(hit["source_id"])
        source_profiles[source_id] = SimpleNamespace(source_id=source_id)
        passages[source_id].append(
            SimpleNamespace(
                source_id=source_id,
                passage_id=str(hit["paragraph_id"]),
            )
        )
    return ShadowBundle(
        claims=claims,
        source_profiles=source_profiles,
        passages=dict(passages),
    )


def _representability(
    *, fixture: dict[str, Any], r2: dict[str, Any], budget_mode: str
) -> dict[str, Any]:
    root = fixture["root_proposition"]
    children = sorted(
        fixture["decomposition"]["children"], key=lambda row: int(row["sequence"])
    )
    claims = [_base_cb_claim(str(root["proposition_id"]), str(root["text"]))]
    claims.extend(
        _base_cb_claim(str(child["proposition_id"]), str(child["text"]))
        for child in children
    )
    shadow = _shadow_bundle(r2, claims)

    inline_propositions_rejected = False
    try:
        payload = claims[0].model_dump(mode="json")
        payload["propositions"] = [
            {"proposition_id": child["proposition_id"], "text": child["text"]}
            for child in children
        ]
        CBClaim.model_validate(payload)
    except ValidationError:
        inline_propositions_rejected = True
    if not inline_propositions_rejected:
        raise RuntimeError("strict Contract B claim unexpectedly accepted inline propositions")

    claim_contexts = [
        {
            "claim_id": root["proposition_id"],
            "origin": {
                "state": "known",
                "value": {
                    "representation": "root",
                    "decomposition_id": fixture["decomposition"]["decomposition_id"],
                    "handoff_sha256": fixture["handoff_sha256"],
                    "proposition_role": "root",
                },
            },
            "atomicity": {"state": "known", "value": "composite"},
        }
    ]
    claim_contexts.extend(
        {
            "claim_id": child["proposition_id"],
            "origin": {
                "state": "known",
                "value": {
                    "representation": "first_class_child",
                    "parent_claim_id": root["proposition_id"],
                    "decomposition_id": fixture["decomposition"]["decomposition_id"],
                    "handoff_sha256": fixture["handoff_sha256"],
                    "proposition_role": "child",
                    "sequence": child["sequence"],
                },
            },
            "atomicity": {"state": "known", "value": "atomic-child"},
        }
        for child in children
    )

    history: list[dict[str, Any]] = []
    count_by_claim: dict[str, int] = defaultdict(int)
    link_index = 0
    for hit in r2["hits"]:
        for rel in hit["relationships"]:
            link_index += 1
            claim_id = str(rel["proposition_id"])
            count_by_claim[claim_id] += 1
            history.append(
                {
                    "link_id": f"rc1a-link-{link_index:04d}",
                    "claim_id": claim_id,
                    "passage_id": hit["paragraph_id"],
                    "nomination": {
                        "method": PRIMARY_RETRIEVER,
                        "budget_mode": budget_mode,
                        "proposition_id": claim_id,
                        "proposition_role": rel["proposition_role"],
                        "retrieval_lane": rel["retrieval_lane"],
                        "query_id": rel["query_id"],
                        "rank": rel["rank"],
                        "score": rel["score"],
                    },
                    "review": {
                        "decision": "needs-review",
                        "reviewer": "research-shadow-no-admission",
                    },
                }
            )

    claim_ids = [claim.claim_id for claim in claims]
    extension = ContractBFactualContext.model_validate(
        {
            "schema": "contract-b-factual-context-v1",
            "history_complete": True,
            "claims": claim_contexts,
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
                for hit in r2["hits"]
            ],
            "history": history,
            "history_count_checks": [
                {
                    "claim_id": claim_id,
                    "candidate": count_by_claim.get(claim_id, 0),
                    "reviewed": 0,
                    "admitted": 0,
                }
                for claim_id in claim_ids
            ],
            "aperture": [
                {
                    "claim_id": claim_id,
                    "search_scope": {
                        "upstream_run_id": UPSTREAM_RUN_ID,
                        "upstream_raw_sha256": UPSTREAM_RAW_SHA256,
                        "retriever": PRIMARY_RETRIEVER,
                        "budget_mode": budget_mode,
                    },
                    "outcome": {"state": "unknown", "value": None},
                    "limitations": [
                        "Retrieval nominations are not evidence-admission decisions."
                    ],
                }
                for claim_id in claim_ids
            ],
        }
    )
    _validate_extension(shadow, extension)
    semantic = _semantic_context(shadow, extension)
    admitted_counts = {
        str(row["claim_id"]): len(row["admitted_passages"])
        for row in semantic["claims"]
    }
    if any(admitted_counts.values()):
        raise RuntimeError("needs-review nomination leaked into CAL semantic context")
    return {
        "strict_contract_b_claim_accepts_distinct_root_and_children": True,
        "strict_contract_b_claim_rejects_inline_propositions": inline_propositions_rejected,
        "canonical_claim_ids": sorted(claim_ids),
        "extension_sha256": sha256_bytes(canonical_bytes(extension)),
        "history_link_count": len(history),
        "all_history_decisions": ["needs-review"],
        "semantic_context_admitted_counts": admitted_counts,
        "needs_review_is_semantically_unadmitted": True,
    }


def _changed(left: dict[str, Any], right: dict[str, Any]) -> bool:
    keys = ("support_label", "risk_label", "support_signal", "rule_flags")
    return any(left[key] != right[key] for key in keys)


def run_probe(*, artifact_dir: Path, output: Path) -> dict[str, Any]:
    raw, manifest = verify_upstream(artifact_dir)
    manifest_by_key = {
        (str(row["original_claim_id"]), str(row["strategy"])): row
        for row in manifest["records"]
    }
    per_treatment: list[dict[str, Any]] = []
    disagreement_counts: dict[str, int] = defaultdict(int)
    representability_checks = 0

    for case in raw["cases"]:
        claim_id = str(case["original_claim_id"])
        for strategy, strategy_row in sorted(case["strategies"].items()):
            if strategy_row["decomposition_state"] != "declared":
                continue
            manifest_row = manifest_by_key[(claim_id, strategy)]
            fixture = _load_json(
                artifact_dir / "contract-a-fixtures" / str(manifest_row["path"])
            )
            root = fixture["root_proposition"]
            children = sorted(
                fixture["decomposition"]["children"],
                key=lambda row: int(row["sequence"]),
            )
            for budget_mode in BUDGET_MODES:
                arms = strategy_row["retrievers"][PRIMARY_RETRIEVER][budget_mode]
                r2 = arms["R2"]
                r3 = arms["R3"]
                if r2 is None or r3 is None:
                    raise RuntimeError("declared treatment missing R2/R3")
                r2_ids = [str(hit["paragraph_id"]) for hit in r2["hits"]]
                r3_ids = [str(hit["paragraph_id"]) for hit in r3["hits"]]
                if r2_ids != r3_ids:
                    raise RuntimeError("R2/R3 physical passage identity invariant failed")

                representation = _representability(
                    fixture=fixture,
                    r2=r2,
                    budget_mode=budget_mode,
                )
                representability_checks += 1

                root_lane_hits = _lane_hits(
                    r2,
                    proposition_id=str(root["proposition_id"]),
                    retrieval_lane="root_lane",
                )
                c0 = _audit_one(
                    proposition_id=str(root["proposition_id"]),
                    text=str(root["text"]),
                    hits=root_lane_hits,
                )
                c3_root = _audit_one(
                    proposition_id=str(root["proposition_id"]),
                    text=str(root["text"]),
                    hits=r3["hits"],
                )

                child_results: list[dict[str, Any]] = []
                for child in children:
                    child_id = str(child["proposition_id"])
                    lane_hits = _lane_hits(
                        r2,
                        proposition_id=child_id,
                        retrieval_lane="child_lane",
                    )
                    c1 = _audit_one(
                        proposition_id=child_id,
                        text=str(child["text"]),
                        hits=lane_hits,
                    )
                    c3_child = _audit_one(
                        proposition_id=child_id,
                        text=str(child["text"]),
                        hits=r3["hits"],
                    )
                    child_changed = _changed(c1, c3_child)
                    if child_changed:
                        disagreement_counts["flattening_changes_child"] += 1
                    child_results.append(
                        {
                            "proposition_id": child_id,
                            "sequence": int(child["sequence"]),
                            "typed_child_lane": c1,
                            "flattened_union": c3_child,
                            "flattening_changes_assessment": child_changed,
                        }
                    )

                root_changed = _changed(c0, c3_root)
                if root_changed:
                    disagreement_counts["flattening_changes_root"] += 1
                typed_labels = [c0["support_label"]] + [
                    row["typed_child_lane"]["support_label"] for row in child_results
                ]
                if len(set(typed_labels)) > 1:
                    disagreement_counts["root_child_typed_label_disagreement"] += 1
                if not root_changed and not any(
                    row["flattening_changes_assessment"] for row in child_results
                ):
                    disagreement_counts["no_flattening_assessment_difference"] += 1

                per_treatment.append(
                    {
                        "original_claim_id": claim_id,
                        "strategy": strategy,
                        "budget_mode": budget_mode,
                        "decomposition_id": fixture["decomposition"]["decomposition_id"],
                        "handoff_sha256": fixture["handoff_sha256"],
                        "r2_r3_physical_passage_ids_identical": True,
                        "r2_physical_passage_count": len(r2_ids),
                        "representability": representation,
                        "C0_root_typed_lane": c0,
                        "C1_children_typed_lanes": child_results,
                        "C2_distinct_units_common_lineage": {
                            "root_proposition_id": root["proposition_id"],
                            "decomposition_id": fixture["decomposition"]["decomposition_id"],
                            "children": [
                                {
                                    "proposition_id": child["proposition_id"],
                                    "sequence": child["sequence"],
                                }
                                for child in children
                            ],
                            "aggregation_rule": None,
                        },
                        "C3_root_flattened_union": c3_root,
                        "flattening_changes_root_assessment": root_changed,
                    }
                )

    result = {
        "schema_version": "1.0",
        "experiment": "decomposition-parent-child-cal-probe-rc1a",
        "upstream": {
            "run_id": UPSTREAM_RUN_ID,
            "apparatus_sha": UPSTREAM_APPARATUS_SHA,
            "raw_retrieval_sha256": UPSTREAM_RAW_SHA256,
            "contract_a_manifest_sha256": UPSTREAM_MANIFEST_SHA256,
        },
        "consumer_authority": {
            "claim_audit_lab_sha": CAL_SHA,
            "apparatus_contracts_sha": CONTRACT_AUTHORITY_SHA,
        },
        "retriever": PRIMARY_RETRIEVER,
        "audit_config": AuditConfig().model_dump(mode="json"),
        "review_admission_boundary": (
            "RC1A retrieval nominations were supplied directly to the research CAL probe; "
            "they were not relabeled as admitted Contract B evidence."
        ),
        "representability_check_count": representability_checks,
        "treatment_budget_probe_count": len(per_treatment),
        "disagreement_counts": dict(sorted(disagreement_counts.items())),
        "per_treatment": per_treatment,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))
    return {
        "output_sha256": sha256_bytes(output.read_bytes()),
        "treatment_budget_probe_count": len(per_treatment),
        "representability_check_count": representability_checks,
        "disagreement_counts": result["disagreement_counts"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run_probe(artifact_dir=args.artifact_dir, output=args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
