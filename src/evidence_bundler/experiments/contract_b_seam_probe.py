"""Shadow probe for the Evidence Bundler -> Contract B -> CAL seam.

This module is intentionally isolated from production models. It compares three
research projections of the same fixture:

- ``current_cb``: a current-C-B-shaped information projection;
- ``minimal_context``: evidence/provenance + factual context + admission/coverage;
- ``full_sidecar``: the minimal handoff plus downstream CAL research judgments.

The goal is to test information ownership, not to propose final field names.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

_VARIANTS = {"current_cb", "minimal_context", "full_sidecar"}
_AUDIT_JUDGMENT_KEYS = {
    "proposition_specific_relation",
    "semantic_validity",
    "temporal_applicability",
    "authority_applicability",
    "decision_participation",
    "completeness_conclusion",
    "verdict",
}
_ALLOWED_REVIEW_DECISIONS = {
    "accepted",
    "rejected",
    "needs-review",
    "insufficient-excerpt",
}


class SeamProbeError(ValueError):
    """Raised when the research seam fixture is internally inconsistent."""


def load_fixture(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SeamProbeError("Fixture root must be a mapping.")
    fixture: dict[str, Any] = raw
    validate_fixture(fixture)
    return fixture


def validate_fixture(fixture: Mapping[str, Any]) -> None:
    claim = _required_mapping(fixture, "claim", "fixture")
    claim_id = _required_str(claim, "claim_id", "claim")
    bundle = _required_mapping(fixture, "bundle", "fixture")
    if _required_str(bundle, "claim_id", "bundle") != claim_id:
        raise SeamProbeError("Bundle claim_id must match claim.claim_id.")

    sources = _index(_records(fixture, "sources"), "source_id")
    passages = _index(_records(fixture, "passages"), "passage_id")
    links = _index(_records(fixture, "links"), "link_id")

    fact_ids: set[str] = set()
    for source_id, source in sources.items():
        facts = source.get("context_facts", [])
        if not isinstance(facts, list):
            raise SeamProbeError(f"Source {source_id} context_facts must be a list.")
        for fact in facts:
            if not isinstance(fact, Mapping):
                raise SeamProbeError(f"Source {source_id} contains a non-mapping fact.")
            fact_id = _required_str(fact, "fact_id", f"source {source_id} fact")
            if fact_id in fact_ids:
                raise SeamProbeError(f"Duplicate fact_id: {fact_id}")
            fact_ids.add(fact_id)
            provenance = _required_mapping(fact, "provenance", f"fact {fact_id}")
            passage_id = _required_str(provenance, "passage_id", f"fact {fact_id}")
            if passage_id not in passages:
                raise SeamProbeError(f"Fact {fact_id} references unknown passage {passage_id}.")

    required = fixture.get("required_mechanical_fact_ids")
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise SeamProbeError("required_mechanical_fact_ids must be a list of strings.")
    missing_facts = sorted(set(required) - fact_ids)
    if missing_facts:
        raise SeamProbeError(f"Required mechanical facts are missing: {missing_facts}")

    links_by_passage: set[str] = set()
    accepted_count = 0
    reviewed_count = 0
    for link_id, link in links.items():
        if _required_str(link, "claim_id", f"link {link_id}") != claim_id:
            raise SeamProbeError(f"Link {link_id} references a different claim.")
        passage_id = _required_str(link, "passage_id", f"link {link_id}")
        if passage_id not in passages:
            raise SeamProbeError(f"Link {link_id} references unknown passage {passage_id}.")
        if passage_id in links_by_passage:
            raise SeamProbeError(f"Passage {passage_id} has multiple links in the fixture.")
        links_by_passage.add(passage_id)
        review = _required_mapping(link, "review", f"link {link_id}")
        decision = _required_str(review, "decision", f"link {link_id} review")
        if decision not in _ALLOWED_REVIEW_DECISIONS:
            raise SeamProbeError(f"Unknown review decision: {decision}")
        if decision != "needs-review":
            reviewed_count += 1
        if decision == "accepted":
            accepted_count += 1

    for passage_id, passage in passages.items():
        source_id = _required_str(passage, "source_id", f"passage {passage_id}")
        if source_id not in sources:
            raise SeamProbeError(f"Passage {passage_id} references unknown source {source_id}.")

    coverage = _required_mapping(fixture, "coverage", "fixture")
    if _required_str(coverage, "claim_id", "coverage") != claim_id:
        raise SeamProbeError("Coverage claim_id must match the fixture claim.")
    expected_counts = (len(links), reviewed_count, accepted_count)
    observed_counts = (
        _required_int(coverage, "candidate_count", "coverage"),
        _required_int(coverage, "reviewed_count", "coverage"),
        _required_int(coverage, "admitted_count", "coverage"),
    )
    if observed_counts != expected_counts:
        raise SeamProbeError(
            f"Coverage counts are {observed_counts}, expected {expected_counts}."
        )

    sidecar = _required_mapping(fixture, "cal_research_sidecar", "fixture")
    assessments = sidecar.get("assessments")
    if not isinstance(assessments, list):
        raise SeamProbeError("cal_research_sidecar.assessments must be a list.")
    accepted_passages = {
        _required_str(link, "passage_id", "link")
        for link in links.values()
        if _review_decision(link) == "accepted"
    }
    assessed_passages = {
        _required_str(item, "passage_id", "CAL assessment")
        for item in assessments
        if isinstance(item, Mapping)
    }
    if accepted_passages != assessed_passages:
        raise SeamProbeError(
            "CAL sidecar assessments must cover exactly the accepted fixture passages."
        )


def build_handoff_variant(fixture: Mapping[str, Any], variant: str) -> dict[str, Any]:
    """Build one research handoff projection from the common frozen fixture."""
    validate_fixture(fixture)
    if variant not in _VARIANTS:
        raise SeamProbeError(f"Unknown handoff variant: {variant}")

    bundle = _required_mapping(fixture, "bundle", "fixture")
    claim = deepcopy(dict(_required_mapping(fixture, "claim", "fixture")))
    sources = _index(_records(fixture, "sources"), "source_id")
    passages = _index(_records(fixture, "passages"), "passage_id")
    links = _records(fixture, "links")

    accepted_passage_ids = sorted(
        _required_str(link, "passage_id", "link")
        for link in links
        if _review_decision(link) == "accepted"
    )

    if variant == "current_cb":
        return {
            "variant": variant,
            "bundle_id": _required_str(bundle, "bundle_id", "bundle"),
            "claim": claim,
            "evidence_passages": [
                {
                    "passage_id": passage_id,
                    "source_id": _required_str(
                        passages[passage_id], "source_id", f"passage {passage_id}"
                    ),
                    "text": _required_str(
                        passages[passage_id], "text", f"passage {passage_id}"
                    ),
                    "source_trust_level": sources[
                        _required_str(
                            passages[passage_id], "source_id", f"passage {passage_id}"
                        )
                    ].get("source_trust_level"),
                }
                for passage_id in accepted_passage_ids
            ],
        }

    minimal = {
        "variant": "minimal_context",
        "bundle_id": _required_str(bundle, "bundle_id", "bundle"),
        "claim": claim,
        "sources": [deepcopy(dict(sources[source_id])) for source_id in sorted(sources)],
        "passages": [
            deepcopy(dict(passages[passage_id])) for passage_id in sorted(passages)
        ],
        "links": [deepcopy(dict(link)) for link in links],
        "coverage": deepcopy(dict(_required_mapping(fixture, "coverage", "fixture"))),
    }
    if variant == "minimal_context":
        return minimal

    full = deepcopy(minimal)
    full["variant"] = "full_sidecar"
    full["cal_research_sidecar"] = deepcopy(
        dict(_required_mapping(fixture, "cal_research_sidecar", "fixture"))
    )
    return full


def build_cal_measurement_view(handoff: Mapping[str, Any]) -> dict[str, Any]:
    """Project the minimal handoff into a pre-assessment CAL-facing evidence view.

    The view keeps admitted evidence, evidence-world context facts, anchors, and
    coverage facts. Retrieval rank/score/role, reviewer identity/notes, rejected
    candidates, and proposition-specific CAL judgments are excluded.
    """
    if handoff.get("variant") not in {"minimal_context", "full_sidecar"}:
        raise SeamProbeError("CAL measurement view requires a minimal-context handoff.")

    sources = _index(_mapping_records(handoff, "sources"), "source_id")
    passages = _index(_mapping_records(handoff, "passages"), "passage_id")
    links = _mapping_records(handoff, "links")

    admitted_ids = sorted(
        _required_str(link, "passage_id", "link")
        for link in links
        if _review_decision(link) == "accepted"
    )
    admitted_source_ids = sorted(
        {
            _required_str(passages[passage_id], "source_id", f"passage {passage_id}")
            for passage_id in admitted_ids
        }
    )

    return {
        "bundle_id": handoff.get("bundle_id"),
        "claim": deepcopy(dict(_required_mapping(handoff, "claim", "handoff"))),
        "sources": [
            {
                "source_id": source_id,
                "title": sources[source_id].get("title"),
                "source_type": sources[source_id].get("source_type"),
                "content_hash": sources[source_id].get("content_hash"),
                "context_facts": deepcopy(sources[source_id].get("context_facts", [])),
            }
            for source_id in admitted_source_ids
        ],
        "admitted_passages": [
            {
                "passage_id": passage_id,
                "source_id": passages[passage_id].get("source_id"),
                "text": passages[passage_id].get("text"),
                "passage_hash": passages[passage_id].get("passage_hash"),
                "anchors": deepcopy(passages[passage_id].get("anchors", [])),
            }
            for passage_id in admitted_ids
        ],
        "coverage": deepcopy(dict(_required_mapping(handoff, "coverage", "handoff"))),
    }


def canonical_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def handoff_hash(fixture: Mapping[str, Any], variant: str = "minimal_context") -> str:
    return canonical_hash(build_handoff_variant(fixture, variant))


def cal_measurement_view_hash(fixture: Mapping[str, Any]) -> str:
    handoff = build_handoff_variant(fixture, "minimal_context")
    return canonical_hash(build_cal_measurement_view(handoff))


def collect_fact_ids(payload: Mapping[str, Any]) -> set[str]:
    """Return provenance-bound factual-context IDs present in a handoff projection."""
    result: set[str] = set()
    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list):
        return result
    for source in raw_sources:
        if not isinstance(source, Mapping):
            continue
        facts = source.get("context_facts", [])
        if not isinstance(facts, list):
            continue
        for fact in facts:
            if isinstance(fact, Mapping) and isinstance(fact.get("fact_id"), str):
                result.add(fact["fact_id"])
    return result


def find_audit_judgment_keys(payload: Any) -> set[str]:
    """Find downstream proposition-specific judgment keys recursively."""
    found: set[str] = set()
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if key in _AUDIT_JUDGMENT_KEYS:
                found.add(str(key))
            found.update(find_audit_judgment_keys(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(find_audit_judgment_keys(item))
    return found


def mutate_downstream_assessments(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Perturb CAL-only judgments while leaving evidence-world facts untouched."""
    mutated: dict[str, Any] = deepcopy(dict(fixture))
    sidecar = mutated.get("cal_research_sidecar")
    if not isinstance(sidecar, dict):
        raise SeamProbeError("Fixture CAL sidecar must be mutable in probe copy.")
    assessments = sidecar.get("assessments")
    if not isinstance(assessments, list):
        raise SeamProbeError("Fixture CAL assessments must be a list.")
    for index, assessment in enumerate(assessments):
        if not isinstance(assessment, dict):
            raise SeamProbeError("CAL assessment entries must be mappings.")
        assessment["proposition_specific_relation"] = f"mutated_relation_{index}"
        assessment["semantic_validity"] = f"mutated_validity_{index}"
        assessment["temporal_applicability"] = f"mutated_temporal_{index}"
        assessment["authority_applicability"] = f"mutated_authority_{index}"
        assessment["decision_participation"] = not bool(
            assessment.get("decision_participation")
        )
    aperture = sidecar.get("aperture_assessment")
    if isinstance(aperture, dict):
        aperture["completeness_conclusion"] = "mutated_completeness"
    sidecar["verdict"] = "mutated_verdict"
    return mutated


def mutate_nomination_metadata(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Perturb nomination provenance without changing admission or evidence content."""
    mutated: dict[str, Any] = deepcopy(dict(fixture))
    links = mutated.get("links")
    if not isinstance(links, list):
        raise SeamProbeError("Fixture links must be a list.")
    for index, link in enumerate(links, start=1):
        if not isinstance(link, dict):
            raise SeamProbeError("Fixture links must be mutable mappings.")
        nomination = link.get("nomination")
        if not isinstance(nomination, dict):
            raise SeamProbeError("Every link needs nomination metadata.")
        nomination["rank"] = 1000 + index
        nomination["scores"] = {"mutated": index / 100}
        nomination["hypothesized_role"] = f"mutated_candidate_{index}"
    return mutated


def mutate_mechanical_fact(
    fixture: Mapping[str, Any], fact_id: str, new_value: Any
) -> dict[str, Any]:
    """Change exactly one factual-context value in a probe copy."""
    mutated: dict[str, Any] = deepcopy(dict(fixture))
    sources = mutated.get("sources")
    if not isinstance(sources, list):
        raise SeamProbeError("Fixture sources must be a list.")
    matches = 0
    for source in sources:
        if not isinstance(source, dict):
            continue
        facts = source.get("context_facts")
        if not isinstance(facts, list):
            continue
        for fact in facts:
            if isinstance(fact, dict) and fact.get("fact_id") == fact_id:
                fact["value"] = new_value
                matches += 1
    if matches != 1:
        raise SeamProbeError(f"Expected one fact {fact_id!r}, found {matches}.")
    return mutated


def _review_decision(link: Mapping[str, Any]) -> str:
    review = _required_mapping(link, "review", "link")
    return _required_str(review, "decision", "review")


def _records(root: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = root.get(key)
    if not isinstance(value, list):
        raise SeamProbeError(f"Field {key!r} must be a list.")
    result: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise SeamProbeError(f"{key}[{index}] must be a mapping.")
        result.append(item)
    return result


def _mapping_records(root: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    return _records(root, key)


def _index(
    records: list[Mapping[str, Any]], id_key: str
) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for record in records:
        record_id = _required_str(record, id_key, "record")
        if record_id in indexed:
            raise SeamProbeError(f"Duplicate {id_key}: {record_id}")
        indexed[record_id] = record
    return indexed


def _required_mapping(
    record: Mapping[str, Any], key: str, context: str
) -> Mapping[str, Any]:
    value = record.get(key)
    if not isinstance(value, Mapping):
        raise SeamProbeError(f"{context} field {key!r} must be a mapping.")
    return value


def _required_str(record: Mapping[str, Any], key: str, context: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise SeamProbeError(f"{context} field {key!r} must be a non-empty string.")
    return value


def _required_int(record: Mapping[str, Any], key: str, context: str) -> int:
    value = record.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SeamProbeError(f"{context} field {key!r} must be an integer.")
    return value


__all__ = [
    "SeamProbeError",
    "build_cal_measurement_view",
    "build_handoff_variant",
    "cal_measurement_view_hash",
    "canonical_hash",
    "collect_fact_ids",
    "find_audit_judgment_keys",
    "handoff_hash",
    "load_fixture",
    "mutate_downstream_assessments",
    "mutate_mechanical_fact",
    "mutate_nomination_metadata",
    "validate_fixture",
]
