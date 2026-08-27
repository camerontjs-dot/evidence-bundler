"""Probe the Annex 22 schema-spike fixture without changing the production contract.

Retrieval nomination metadata is retained in the prototype for provenance, but it must
not appear in the CAL-facing view. Human review controls admission only; CAL remains
responsible for semantic entailment/contradiction judgments.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

_ALLOWED_REVIEW_DECISIONS = {
    "accepted",
    "rejected",
    "needs-review",
    "insufficient-excerpt",
}
_ALLOWED_COVERAGE_OUTCOMES = {
    "admitted",
    "no_candidates",
    "all_rejected",
    "partial_review",
}


class ShapeProbeError(ValueError):
    """Raised when the exploratory Annex 22 fixture is internally inconsistent."""


def load_prototype(path: Path) -> dict[str, Any]:
    """Load and validate the one-file Annex 22 shape prototype."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ShapeProbeError("Prototype root must be a mapping.")
    bundle: dict[str, Any] = raw
    validate_prototype(bundle)
    return bundle


def validate_prototype(bundle: Mapping[str, Any]) -> None:
    """Validate identities, references, review counts, and coverage-state semantics."""
    claims = _index_records(_records(bundle, "claims"), "claim_id")
    passages = _index_records(_records(bundle, "passages"), "passage_id")
    sources = _index_records(_records(bundle, "sources"), "source_id")
    links = _index_records(_records(bundle, "links"), "link_id")
    coverage = _index_records(_records(bundle, "coverage"), "claim_id")

    if set(coverage) != set(claims):
        missing = sorted(set(claims) - set(coverage))
        extra = sorted(set(coverage) - set(claims))
        raise ShapeProbeError(f"Coverage/claim mismatch: missing={missing}, extra={extra}")

    links_by_claim: dict[str, list[Mapping[str, Any]]] = {claim_id: [] for claim_id in claims}
    for link_id, link in links.items():
        claim_id = _required_str(link, "claim_id", f"link {link_id}")
        passage_id = _required_str(link, "passage_id", f"link {link_id}")
        if claim_id not in claims:
            raise ShapeProbeError(f"Link {link_id} references unknown claim {claim_id}.")
        if passage_id not in passages:
            raise ShapeProbeError(f"Link {link_id} references unknown passage {passage_id}.")
        review = _required_mapping(link, "review", f"link {link_id}")
        decision = _required_str(review, "decision", f"link {link_id} review")
        if decision not in _ALLOWED_REVIEW_DECISIONS:
            raise ShapeProbeError(f"Link {link_id} has unknown review decision {decision!r}.")
        links_by_claim[claim_id].append(link)

    for passage_id, passage in passages.items():
        source_id = _required_str(passage, "source_id", f"passage {passage_id}")
        if source_id not in sources:
            raise ShapeProbeError(
                f"Passage {passage_id} references unknown source {source_id}."
            )

    for claim_id, record in coverage.items():
        candidate_links = links_by_claim[claim_id]
        reviewed_links = [
            link for link in candidate_links if _review_decision(link) != "needs-review"
        ]
        admitted_links = [
            link for link in candidate_links if _review_decision(link) == "accepted"
        ]
        expected = (len(candidate_links), len(reviewed_links), len(admitted_links))
        observed = (
            _required_int(record, "candidate_count", f"coverage {claim_id}"),
            _required_int(record, "reviewed_count", f"coverage {claim_id}"),
            _required_int(record, "admitted_count", f"coverage {claim_id}"),
        )
        if observed != expected:
            raise ShapeProbeError(
                f"Coverage counts for {claim_id} are {observed}, expected {expected}."
            )
        outcome = _required_str(record, "outcome", f"coverage {claim_id}")
        if outcome not in _ALLOWED_COVERAGE_OUTCOMES:
            raise ShapeProbeError(f"Coverage {claim_id} has unknown outcome {outcome!r}.")
        _validate_outcome(claim_id, outcome, *observed)


def build_blinded_cal_view(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Return an audit-facing view with nomination hypotheses mechanically removed.

    Source identity/status survives because it constrains evidence eligibility and provenance.
    Retrieval scores/ranks/roles, review notes, scaffold labels, and CAL result placeholders do
    not survive. Human review affects only which passages are admitted.
    """
    validate_prototype(bundle)
    claims = _index_records(_records(bundle, "claims"), "claim_id")
    passages = _index_records(_records(bundle, "passages"), "passage_id")
    sources = _index_records(_records(bundle, "sources"), "source_id")
    coverage = _index_records(_records(bundle, "coverage"), "claim_id")

    admitted_by_claim: dict[str, list[str]] = {claim_id: [] for claim_id in claims}
    for link in _records(bundle, "links"):
        if _review_decision(link) != "accepted":
            continue
        claim_id = _required_str(link, "claim_id", "link")
        passage_id = _required_str(link, "passage_id", "link")
        admitted_by_claim[claim_id].append(passage_id)

    cal_claims: list[dict[str, Any]] = []
    for claim_id in sorted(claims):
        claim = claims[claim_id]
        passage_ids = sorted(set(admitted_by_claim[claim_id]))
        cal_claims.append(
            {
                "claim_id": claim_id,
                "claim_text": _required_str(claim, "claim_text", f"claim {claim_id}"),
                "passages": [
                    _cal_passage_view(passages[passage_id]) for passage_id in passage_ids
                ],
                "coverage": _cal_coverage_view(coverage[claim_id]),
            }
        )

    bundle_meta = _required_mapping(bundle, "bundle", "prototype")
    return {
        "bundle_id": _required_str(bundle_meta, "bundle_id", "bundle"),
        "sources": [_cal_source_view(sources[source_id]) for source_id in sorted(sources)],
        "claims": cal_claims,
    }


def cal_view_hash(bundle: Mapping[str, Any]) -> str:
    """Hash the canonical JSON representation of the blinded audit-facing view."""
    payload = json.dumps(
        build_blinded_cal_view(bundle),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def mutate_nomination_hypotheses(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy with nomination roles, ranks, and scores deliberately perturbed."""
    mutated: dict[str, Any] = deepcopy(dict(bundle))
    raw_links = mutated.get("links")
    if not isinstance(raw_links, list):
        raise ShapeProbeError("Prototype field 'links' must be a list.")
    for index, raw_link in enumerate(raw_links, start=1):
        if not isinstance(raw_link, dict):
            raise ShapeProbeError("Every link must be a mutable mapping in the probe copy.")
        nomination = raw_link.get("nomination")
        if not isinstance(nomination, dict):
            raise ShapeProbeError("Every link must have mutable nomination metadata.")
        nomination["hypothesized_role"] = f"deliberately_changed_role_{index}"
        nomination["rank"] = 10_000 + index
        nomination["scores"] = {"fusion": round(index / 1000, 6)}
    return mutated


def reconstruct_provenance(
    bundle: Mapping[str, Any], claim_id: str, passage_id: str
) -> dict[str, Any]:
    """Reconstruct the provenance path for one admitted claim-passage pair."""
    validate_prototype(bundle)
    claims = _index_records(_records(bundle, "claims"), "claim_id")
    passages = _index_records(_records(bundle, "passages"), "passage_id")
    sources = _index_records(_records(bundle, "sources"), "source_id")

    claim = claims.get(claim_id)
    passage = passages.get(passage_id)
    if claim is None or passage is None:
        raise ShapeProbeError(f"Unknown claim/passage pair: {claim_id}/{passage_id}")

    matching_links = [
        link
        for link in _records(bundle, "links")
        if link.get("claim_id") == claim_id
        and link.get("passage_id") == passage_id
        and _review_decision(link) == "accepted"
    ]
    if len(matching_links) != 1:
        raise ShapeProbeError(
            f"Expected one admitted link for {claim_id}/{passage_id}; "
            f"found {len(matching_links)}."
        )

    source_id = _required_str(passage, "source_id", f"passage {passage_id}")
    source = sources[source_id]
    extraction = _required_mapping(source, "extraction", f"source {source_id}")
    return {
        "claim": {
            "claim_id": claim_id,
            "claim_text": _required_str(claim, "claim_text", f"claim {claim_id}"),
        },
        "link": {"link_id": _required_str(matching_links[0], "link_id", "link")},
        "passage": {
            "passage_id": passage_id,
            "passage_hash": _required_str(
                passage, "passage_hash", f"passage {passage_id}"
            ),
            "anchors": deepcopy(passage.get("anchors", [])),
        },
        "source": {
            "source_id": source_id,
            "document_status": source.get("document_status"),
            "content_hash": source.get("content_hash"),
            "representation_id": extraction.get("representation_id"),
            "extracted_text_hash": extraction.get("extracted_text_hash"),
        },
    }


def _cal_source_view(source: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _required_str(source, "source_id", "source")
    return {
        "source_id": source_id,
        "title": source.get("title"),
        "source_type": source.get("source_type"),
        "publisher": source.get("publisher"),
        "document_status": source.get("document_status"),
        "status_date": source.get("status_date"),
        "jurisdiction": source.get("jurisdiction"),
        "version_label": source.get("version_label"),
        "content_hash": source.get("content_hash"),
    }


def _cal_passage_view(passage: Mapping[str, Any]) -> dict[str, Any]:
    passage_id = _required_str(passage, "passage_id", "passage")
    return {
        "passage_id": passage_id,
        "source_id": _required_str(passage, "source_id", f"passage {passage_id}"),
        "text": _required_str(passage, "text", f"passage {passage_id}"),
        "passage_hash": _required_str(
            passage, "passage_hash", f"passage {passage_id}"
        ),
        "anchors": deepcopy(passage.get("anchors", [])),
    }


def _cal_coverage_view(record: Mapping[str, Any]) -> dict[str, Any]:
    claim_id = _required_str(record, "claim_id", "coverage")
    return {
        "outcome": _required_str(record, "outcome", f"coverage {claim_id}"),
        "candidate_count": _required_int(record, "candidate_count", f"coverage {claim_id}"),
        "reviewed_count": _required_int(record, "reviewed_count", f"coverage {claim_id}"),
        "admitted_count": _required_int(record, "admitted_count", f"coverage {claim_id}"),
        "search_scope": deepcopy(record.get("search_scope", {})),
        "limitations": deepcopy(record.get("limitations", [])),
    }


def _validate_outcome(
    claim_id: str,
    outcome: str,
    candidate_count: int,
    reviewed_count: int,
    admitted_count: int,
) -> None:
    valid = False
    if outcome == "no_candidates":
        valid = candidate_count == reviewed_count == admitted_count == 0
    elif outcome == "all_rejected":
        valid = candidate_count > 0 and reviewed_count == candidate_count and admitted_count == 0
    elif outcome == "partial_review":
        valid = candidate_count > reviewed_count
    elif outcome == "admitted":
        valid = admitted_count > 0
    if not valid:
        raise ShapeProbeError(
            f"Coverage outcome {outcome!r} is inconsistent for claim {claim_id}: "
            f"candidates={candidate_count}, reviewed={reviewed_count}, admitted={admitted_count}."
        )


def _review_decision(link: Mapping[str, Any]) -> str:
    review = _required_mapping(link, "review", "link")
    return _required_str(review, "decision", "review")


def _records(bundle: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = bundle.get(key)
    if not isinstance(value, list):
        raise ShapeProbeError(f"Prototype field {key!r} must be a list.")
    records: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ShapeProbeError(f"{key}[{index}] must be a mapping.")
        records.append(item)
    return records


def _index_records(
    records: list[Mapping[str, Any]], id_key: str
) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for record in records:
        record_id = _required_str(record, id_key, "record")
        if record_id in indexed:
            raise ShapeProbeError(f"Duplicate {id_key}: {record_id}")
        indexed[record_id] = record
    return indexed


def _required_mapping(
    record: Mapping[str, Any], key: str, context: str
) -> Mapping[str, Any]:
    value = record.get(key)
    if not isinstance(value, Mapping):
        raise ShapeProbeError(f"{context} field {key!r} must be a mapping.")
    return value


def _required_str(record: Mapping[str, Any], key: str, context: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ShapeProbeError(f"{context} field {key!r} must be a non-empty string.")
    return value


def _required_int(record: Mapping[str, Any], key: str, context: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ShapeProbeError(f"{context} field {key!r} must be an integer.")
    return value


__all__ = [
    "ShapeProbeError",
    "build_blinded_cal_view",
    "cal_view_hash",
    "load_prototype",
    "mutate_nomination_hypotheses",
    "reconstruct_provenance",
    "validate_prototype",
]
