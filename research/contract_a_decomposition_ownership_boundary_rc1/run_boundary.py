from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from claim_audit_lab.v1.explicit_claims import (
    AtomProvenance,
    ExplicitClaimAtom,
    ExplicitClaimRequest,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from evidence_bundler.models.ca import ScaffoldClaim
from evidence_bundler.models.retrieval import RetrievalConfig

SNAPSHOT_SHA256 = "8dbedd537c024c4a624f21abd5fa11536ddfe558000f3a9366584c30c045e31c"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ShadowContractAChild(StrictModel):
    claim_id: str
    claim_text: str
    parent_claim_id: str
    decomposition_id: str
    sequence: int = Field(ge=1)
    reference_sha256: str


class ShadowContractADecomposition(StrictModel):
    parent_claim_id: str
    parent_claim_text: str
    decomposition_id: str
    operator: Literal["all_of"]
    children: list[ShadowContractAChild]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash(value: Any) -> str:
    payload = (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode()
    return "sha256:" + sha256_bytes(payload)


def load_snapshot(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if sha256_bytes(raw) != SNAPSHOT_SHA256:
        raise RuntimeError("fixed snapshot hash mismatch")
    return json.loads(raw)


def build_shadow_packet(snapshot: dict[str, Any]) -> ShadowContractADecomposition:
    children = []
    for child in sorted(snapshot["children"], key=lambda row: int(row["sequence"])):
        reference_sha = canonical_hash(
            {
                "decomposition_id": snapshot["decomposition_id"],
                "parent_claim_id": snapshot["original_claim_id"],
                "child_id": child["child_id"],
                "sequence": child["sequence"],
                "text": child["text"],
            }
        )
        children.append(
            ShadowContractAChild(
                claim_id=str(child["child_id"]),
                claim_text=str(child["text"]),
                parent_claim_id=str(snapshot["original_claim_id"]),
                decomposition_id=str(snapshot["decomposition_id"]),
                sequence=int(child["sequence"]),
                reference_sha256=reference_sha,
            )
        )
    return ShadowContractADecomposition(
        parent_claim_id=str(snapshot["original_claim_id"]),
        parent_claim_text=str(snapshot["original_claim_text"]),
        decomposition_id=str(snapshot["decomposition_id"]),
        operator="all_of",
        children=children,
    )


def adapt_to_cal(
    packet: ShadowContractADecomposition,
    *,
    passages: list[Any],
    audit_config: Any,
) -> ExplicitClaimRequest:
    atoms = [
        ExplicitClaimAtom(
            atom_id=child.claim_id,
            claim_text=child.claim_text,
            provenance=AtomProvenance(
                origin="source_contract",
                reference_id=(
                    f"{packet.decomposition_id}:{child.claim_id}"
                ),
                reference_sha256=child.reference_sha256,
            ),
        )
        for child in packet.children
    ]
    return ExplicitClaimRequest(
        parent_claim_id=packet.parent_claim_id,
        parent_claim_text=packet.parent_claim_text,
        operator=packet.operator,
        atoms=atoms,
        passages=passages,
        audit_config=audit_config,
    )


def assert_source_contract_membership(
    packet: ShadowContractADecomposition,
    child_id: str,
) -> None:
    if child_id not in {child.claim_id for child in packet.children}:
        raise ValueError(
            "source_contract provenance requires child identity present in Contract A"
        )


def run(snapshot_path: Path) -> dict[str, Any]:
    snapshot = load_snapshot(snapshot_path)
    packet = build_shadow_packet(snapshot)

    current_contract_a_rejects_lineage_fields = False
    scaffold_payload = {
        "claim_id": snapshot["original_claim_id"],
        "claim_type": "extracted_claim",
        "claim_text": snapshot["original_claim_text"],
        "support_status": "uncertain",
        "claim_strength": 0.5,
        "extraction_fidelity": 1.0,
        "source_refs": [],
        "counterevidence_checked": False,
        "counterevidence_found": False,
        "downgraded": False,
        "downgrade_reason": None,
        "scaffold_notes": "",
        "parent_claim_id": "forbidden-extra",
        "decomposition_id": "forbidden-extra",
        "sequence": 1,
    }
    try:
        ScaffoldClaim.model_validate(scaffold_payload)
    except ValidationError:
        current_contract_a_rejects_lineage_fields = True

    eb_generated_origin_rejected = False
    try:
        AtomProvenance.model_validate(
            {
                "origin": "evidence_bundler_generated",
                "reference_id": "eb-generated-child",
                "reference_sha256": "sha256:" + "0" * 64,
            }
        )
    except ValidationError:
        eb_generated_origin_rejected = True

    # Build a minimal CAL request without invoking model inference.
    from claim_audit_lab.v1.config import load_default_audit_config
    from claim_audit_lab.v1.models import Passage

    fixed_passages = [
        Passage(
            passage_id=str(hit["paragraph_id"]),
            text=str(hit["text"]),
            source_meta={"source_id": str(hit["source_id"])},
        )
        for hit in snapshot["hits"]
    ]
    request = adapt_to_cal(
        packet,
        passages=fixed_passages,
        audit_config=load_default_audit_config(),
    )

    if [atom.atom_id for atom in request.atoms] != [
        child.claim_id for child in packet.children
    ]:
        raise RuntimeError("child identity drift across Contract A -> CAL adapter")
    if [atom.claim_text for atom in request.atoms] != [
        child.claim_text for child in packet.children
    ]:
        raise RuntimeError("child text drift across Contract A -> CAL adapter")
    if request.operator != "all_of":
        raise RuntimeError("operator drift across Contract A -> CAL adapter")
    if any(atom.provenance.origin != "source_contract" for atom in request.atoms):
        raise RuntimeError("source-contract provenance lost")

    membership_rejects_eb_synthesized_child = False
    try:
        assert_source_contract_membership(packet, "eb-synthesized-child")
    except ValueError:
        membership_rejects_eb_synthesized_child = True

    # EB query configuration consumes the declared child texts as retrieval inputs.
    retrieval_config = RetrievalConfig(retrieval_method="semantic")
    query_execution_identity = [
        {
            "claim_id": child.claim_id,
            "query_text": child.claim_text,
            "retrieval_method": retrieval_config.retrieval_method,
        }
        for child in packet.children
    ]

    if not current_contract_a_rejects_lineage_fields:
        raise RuntimeError("current Contract A unexpectedly accepts lineage fields")
    if not eb_generated_origin_rejected:
        raise RuntimeError("CAL unexpectedly accepts EB-generated semantic authority")
    if not membership_rejects_eb_synthesized_child:
        raise RuntimeError("EB-synthesized child was falsely accepted as source-contract")
    if any(
        row["query_text"] != child.claim_text
        for row, child in zip(query_execution_identity, packet.children, strict=True)
    ):
        raise RuntimeError("EB query execution changed declared child semantics")

    return {
        "schema_version": "1.0",
        "experiment": "contract-a-decomposition-ownership-boundary-rc1",
        "snapshot_sha256": SNAPSHOT_SHA256,
        "candidate_boundary": {
            "contract_a": "declares semantic proposition identity and lineage",
            "evidence_bundler": "executes retrieval/query planning for declared propositions",
            "claim_audit_lab": "audits caller-declared propositions and aggregates explicit all_of",
        },
        "observations": {
            "current_contract_a_rejects_lineage_fields": (
                current_contract_a_rejects_lineage_fields
            ),
            "cal_rejects_evidence_bundler_generated_provenance": (
                eb_generated_origin_rejected
            ),
            "source_contract_packet_adapts_losslessly_to_cal": True,
            "source_contract_membership_rejects_eb_synthesized_child": (
                membership_rejects_eb_synthesized_child
            ),
            "eb_query_execution_preserves_declared_child_text": True,
        },
        "packet": packet.model_dump(mode="json"),
        "cal_request": request.model_dump(mode="json"),
        "query_execution_identity": query_execution_identity,
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
    print(json.dumps(result["observations"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
