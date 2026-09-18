from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import torch
from proposition_authoring.model import AuthoringRequest, SourceRepresentation
from proposition_authoring.preflight import run_paired_preflight
from proposition_authoring.shadow_models import TaskMetadata
from shadow_carrier import build_shadow_carrier, registry_field_ids, sha256_json
from transformers import AutoModelForSequenceClassification, AutoTokenizer

SEMANTIC_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
SEMANTIC_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
LOSS_CAPS = (0.02, 0.05, 0.10, 0.20, 1.00)

TOKEN_RE = re.compile(r"[A-Za-z0-9%µμ°./+'-]+")
NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?%?")
UNIT_RE = re.compile(
    r"\b(?:mg/L|µg/L|ug/L|ppm|dB|kHz|MW|kW|kg|mm|cm|m|L|hours?|minutes?|days?|"
    r"weeks?|months?|years?|cycles?|°C|C)\b",
    re.I,
)
NEG_RE = re.compile(r"\b(?:no|not|never|without|cannot|can't|does not|did not)\b", re.I)
MODAL_RE = re.compile(r"\b(?:may|might|could|can|would|should|must|will)\b", re.I)
ATTR_RE = re.compile(
    r"\b(?:according to|reports?|reported|states?|stated|says?|said|witness log|"
    r"certificate|certified|registrar)\b",
    re.I,
)
TEMP_RE = re.compile(
    r"\b(?:20\d{2}|19\d{2}|January|February|March|April|May|June|July|August|"
    r"September|October|November|December|week|month|year|day|hours?|minutes?)\b",
    re.I,
)
POSTURE_BAD = re.compile(
    r"\b(?:hypothetical|unverified|asked whether|no conclusion|example only|"
    r"template|proposal|specification calls for|acceptance targets?|"
    r"did not publish|not measured|was not measured|does not report|"
    r"omits?|missing|unspecified)\b",
    re.I,
)
MEASUREMENT_RE = re.compile(
    r"\b(?:measured|measurement|recorded|rate|mean|median|average|threshold|"
    r"yield|capacity|germination|depth|nitrate|lead|sulfur|runtime|wait time|"
    r"completion|produced|reached|retained|contained)\b",
    re.I,
)
EVENT_RE = re.compile(r"\b(?:log|record|audit|witness|incident|event)\b", re.I)
REGISTRY_RE = re.compile(
    r"\b(?:registry|inventory|certificate|certified|code|registrar|database)\b",
    re.I,
)
DECLARATION_RE = re.compile(
    r"\b(?:report states|states that|declaration|policy|code|manual|specification)\b",
    re.I,
)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokens(text: str) -> set[str]:
    return {tok.lower() for tok in TOKEN_RE.findall(text)}


def flatten_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, list | tuple | set):
        out: list[str] = []
        for item in value:
            out.extend(flatten_strings(item))
        return out
    if isinstance(value, dict):
        out = []
        for key in sorted(value):
            out.extend(flatten_strings(value[key]))
        return out
    return [str(value)]


def phrase_coverage(value: Any, text: str) -> float | None:
    phrases = [x.strip().lower() for x in flatten_strings(value) if x.strip()]
    phrases = [x for x in phrases if x not in {"unknown", "none", "false", "true"}]
    if not phrases:
        return None
    hay = text.lower()
    exact = sum(1 for phrase in phrases if phrase in hay)
    if exact:
        return exact / len(phrases)
    query = set()
    for phrase in phrases:
        query |= tokens(phrase)
    body = tokens(text)
    return len(query & body) / len(query) if query else None


def binary_feature_match(flag: bool | None, pattern: re.Pattern[str], text: str) -> float | None:
    if flag is None:
        return None
    observed = bool(pattern.search(text))
    return 1.0 if observed == flag else 0.0


def field_truthy(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    strings = [x.strip().lower() for x in flatten_strings(value)]
    if not strings or all(x in {"", "unknown", "none", "not_applicable"} for x in strings):
        return None
    if all(x in {"false", "no", "absent", "0"} for x in strings):
        return False
    return True


def number_signature(text: str) -> set[str]:
    return {x.lower() for x in NUMBER_RE.findall(text)} | {
        x.lower() for x in UNIT_RE.findall(text)
    }


def numeric_compatibility(claim: str, candidate: str) -> float | None:
    left = number_signature(claim)
    if not left:
        return None
    right = number_signature(candidate)
    return len(left & right) / len(left)


def candidate_forms(text: str) -> set[str]:
    forms = {"document_text"}
    if MEASUREMENT_RE.search(text) or NUMBER_RE.search(text):
        forms.add("measurement")
    if EVENT_RE.search(text):
        forms.add("event_record")
    if REGISTRY_RE.search(text):
        forms.add("registry_entry")
    if DECLARATION_RE.search(text):
        forms.add("authoritative_declaration")
    return forms


def form_compatibility(expected: Any, text: str) -> float | None:
    expected_forms = {
        x.strip().lower()
        for x in flatten_strings(expected)
        if x.strip() and x.strip().lower() != "unknown"
    }
    if not expected_forms:
        return None
    observed = candidate_forms(text)
    return len(expected_forms & observed) / len(expected_forms)


def semantic_model() -> tuple[Any, Any]:
    tokenizer = AutoTokenizer.from_pretrained(
        SEMANTIC_MODEL,
        revision=SEMANTIC_REVISION,
        trust_remote_code=False,
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        SEMANTIC_MODEL,
        revision=SEMANTIC_REVISION,
        trust_remote_code=False,
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


def load_lane_sources(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {str(row["lane_id"]): list(row["sources"]) for row in payload["lanes"]}


def gate_result(claim: str, lane_id: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    request = AuthoringRequest(
        handoff_id=f"eb-gate-pressure-{lane_id}",
        producer_id="eb-gate-pressure-dev-v0",
        producer_version="v0",
        work_id=f"gate-pressure-{lane_id}",
        root_id=lane_id,
        root_text=claim,
        sources=tuple(
            SourceRepresentation(
                source_id=str(row["source_id"]),
                media_type=str(row["media_type"]),
                content=str(row["content"]),
            )
            for row in sources
        ),
    )
    result = run_paired_preflight(
        request,
        claim_task=TaskMetadata(),
        evidence_task=TaskMetadata(corpus_scope=f"rc1-lane-{lane_id}"),
        source_metadata=(),
        implementation_identity="e29a165b682d060f5dc2a0f3c7d64a7f29b172b4",
    )
    return {
        "claim_profile": result.claim_profile,
        "evidence_world_profile": result.evidence_world_profile,
        "compatibility": result.compatibility,
        "feature_registry": result.feature_registry,
        "receipts": {
            "claim": result.claim_profile_receipt,
            "evidence": result.evidence_world_receipt,
            "compatibility": result.compatibility_receipt,
        },
    }


def observation(state: str, value: Any, basis: dict[str, Any]) -> dict[str, Any]:
    return {"state": state, "value": value, "basis": basis}


def gate_to_carrier_packet(
    lane_id: str,
    gate: dict[str, Any],
    registry_ids: set[str],
) -> dict[str, Any]:
    claim = gate["claim_profile"]
    evidence = gate["evidence_world_profile"]
    compat_rows = {
        str(row["field"]): row for row in gate["compatibility"].get("observations", [])
    }

    fields: dict[str, Any] = {}

    def put(field_id: str, value: Any, basis: str) -> None:
        if field_id not in registry_ids:
            return
        state = "unknown"
        if value not in (None, "unknown", [], {}):
            state = "known"
        fields[field_id] = observation(
            state,
            None if state == "unknown" else value,
            {"kind": "proposition_authoring_shadow", "basis": basis},
        )

    for name in (
        "claim_families",
        "entities",
        "relation_targets",
        "domain",
        "verification_world",
        "temporal_scope",
        "jurisdiction",
        "expected_evidence_forms",
        "context_dependence",
        "scope_ambiguity",
        "negation",
        "modality",
        "attribution",
    ):
        put(f"claim.{name}", claim.get(name), f"claim_profile.{name}")

    put("claim.claim_structure_shape", claim.get("claim_structure_shape"), "claim_profile")
    put("claim.context_supplied", None, "not available in this cohort")
    put("claim.context_required", None, "not qualified")
    put("claim.surface_coordination_present", None, "not materialized")
    put("claim.surface_scope_marker_present", None, "not materialized")

    put("evidence.source_identity", evidence.get("source_inventory"), "evidence_world_profile")
    put("evidence.content_identity", evidence.get("source_inventory"), "evidence_world_profile")
    put("evidence.provenance", evidence.get("source_inventory"), "evidence_world_profile")
    put("evidence.issuer", evidence.get("issuers"), "evidence_world_profile")
    put("evidence.source_role", evidence.get("source_roles"), "evidence_world_profile")
    put("evidence.authority_basis", evidence.get("source_inventory"), "evidence_world_profile")
    put("evidence.document_type", evidence.get("document_types"), "evidence_world_profile")
    put("evidence.evidence_form", evidence.get("evidence_forms"), "evidence_world_profile")
    put("evidence.temporal_coverage", evidence.get("temporal_coverage"), "evidence_world_profile")
    put(
        "evidence.jurisdictional_coverage",
        evidence.get("jurisdictional_coverage"),
        "evidence_world_profile",
    )
    put("evidence.version", evidence.get("source_inventory"), "evidence_world_profile")
    put("evidence.currency_state", evidence.get("currency_states"), "evidence_world_profile")
    put(
        "evidence.duplicate_source_groups",
        evidence.get("duplicate_source_groups"),
        "evidence_world_profile",
    )
    put(
        "evidence.conflict_observations",
        evidence.get("conflict_observations"),
        "evidence_world_profile",
    )
    put(
        "evidence.supersession_observations",
        evidence.get("supersession_observations"),
        "evidence_world_profile",
    )
    put("evidence.verification_world", evidence.get("verification_world"), "evidence_world_profile")
    put("evidence.corpus_scope", evidence.get("corpus_scope"), "evidence_world_profile")
    put(
        "evidence.completeness_state",
        evidence.get("completeness_state"),
        "evidence_world_profile",
    )
    put("evidence.known_gaps", evidence.get("known_gaps"), "evidence_world_profile")

    compat_map = {
        "evidence_forms": "preflight.evidence_forms",
        "missing_expected_evidence_forms": "preflight.missing_expected_evidence_forms",
        "temporal_scope": "preflight.temporal_scope",
        "jurisdiction": "preflight.jurisdiction",
        "verification_world": "preflight.verification_world",
        "corpus_aperture": "preflight.corpus_aperture",
        "corpus_completeness": "preflight.corpus_completeness",
        "known_gaps": "preflight.known_gaps",
    }
    for upstream, field_id in compat_map.items():
        row = compat_rows.get(upstream)
        put(field_id, row, f"preflight.{upstream}" if row else "missing")

    return {
        "schema": "eb-gate-shadow-observation-packet-v0",
        "case_id": lane_id,
        "upstream_identity": {
            "proposition_authoring_subject": "e29a165b682d060f5dc2a0f3c7d64a7f29b172b4",
            "claim_profile_sha256": claim.get("profile_sha256"),
            "evidence_profile_sha256": evidence.get("profile_sha256"),
            "compatibility_sha256": gate["compatibility"].get("compatibility_sha256"),
        },
        "fields": fields,
    }


def representation_summary(
    registry: dict[str, Any],
    packets: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for entry in registry["entries"]:
        field_id = str(entry["field_id"])
        values: list[str] = []
        known = 0
        for packet in packets.values():
            record = packet["fields"].get(field_id)
            if not record:
                continue
            if record["state"] == "known":
                known += 1
                values.append(canonical(record["value"]))
        rows.append(
            {
                "field_id": field_id,
                "layer": entry["layer"],
                "evidence_status": entry["evidence_status"],
                "cases_present": sum(field_id in p["fields"] for p in packets.values()),
                "cases_known": known,
                "unique_known_values": len(set(values)),
                "representation_disposition": (
                    "NONTRIVIAL"
                    if known and len(set(values)) > 1
                    else "CONSTANT"
                    if known
                    else "UNMATERIALIZED_OR_UNKNOWN"
                ),
            }
        )
    return {
        "field_count": len(rows),
        "nontrivial": sum(row["representation_disposition"] == "NONTRIVIAL" for row in rows),
        "constant": sum(row["representation_disposition"] == "CONSTANT" for row in rows),
        "unmaterialized_or_unknown": sum(
            row["representation_disposition"] == "UNMATERIALIZED_OR_UNKNOWN" for row in rows
        ),
        "fields": rows,
    }


def gate_family_scores(
    gate: dict[str, Any], claim: str, candidate_text: str
) -> dict[str, float | None]:
    profile = gate["claim_profile"]
    families = {str(x).lower() for x in profile.get("claim_families", [])}

    family_quantitative = None
    if "quantitative" in families or "comparative" in families:
        family_quantitative = numeric_compatibility(claim, candidate_text)

    return {
        "evidence_shape": form_compatibility(
            profile.get("expected_evidence_forms"), candidate_text
        ),
        "entities": phrase_coverage(profile.get("entities"), candidate_text),
        "relation_targets": phrase_coverage(profile.get("relation_targets"), candidate_text),
        "temporal": phrase_coverage(profile.get("temporal_scope"), candidate_text),
        "jurisdiction": phrase_coverage(profile.get("jurisdiction"), candidate_text),
        "quantitative_signature": family_quantitative,
        "negation": binary_feature_match(
            field_truthy(profile.get("negation")), NEG_RE, candidate_text
        ),
        "modality": binary_feature_match(
            field_truthy(profile.get("modality")), MODAL_RE, candidate_text
        ),
        "attribution": binary_feature_match(
            field_truthy(profile.get("attribution")), ATTR_RE, candidate_text
        ),
        "posture": 0.0 if POSTURE_BAD.search(candidate_text) else 1.0,
    }


def semantic_order(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda row: (-float(row["semantic_score"]), int(row["rank"]), str(row["candidate_id"])),
    )


def bounded_repair(
    ordered: list[dict[str, Any]],
    compat: dict[str, float | None],
    loss_cap: float,
) -> list[str]:
    selected = list(ordered[:3])
    outside = list(ordered[3:])
    if not selected or not outside:
        return [str(row["candidate_id"]) for row in selected]

    def comp(row: dict[str, Any]) -> float:
        value = compat.get(str(row["candidate_id"]))
        return -1.0 if value is None else float(value)

    victim = min(
        selected,
        key=lambda row: (comp(row), float(row["semantic_score"]), -int(row["rank"])),
    )
    challenger = max(
        outside,
        key=lambda row: (comp(row), float(row["semantic_score"]), -int(row["rank"])),
    )

    if comp(challenger) <= comp(victim):
        return [str(row["candidate_id"]) for row in selected]

    loss = float(victim["semantic_score"]) - float(challenger["semantic_score"])
    if loss > loss_cap + 1e-12:
        return [str(row["candidate_id"]) for row in selected]

    replaced = [row for row in selected if row is not victim] + [challenger]
    replaced = sorted(
        replaced,
        key=lambda row: (-float(row["semantic_score"]), int(row["rank"]), str(row["candidate_id"])),
    )
    return [str(row["candidate_id"]) for row in replaced]


def staged_repair(
    ordered: list[dict[str, Any]],
    family_scores: dict[str, dict[str, float | None]],
    families: list[str],
    loss_cap: float,
) -> list[str]:
    current_ids = [str(row["candidate_id"]) for row in ordered[:3]]
    by_id = {str(row["candidate_id"]): row for row in ordered}
    for family in families:
        current_set = set(current_ids)
        synthetic_order = [by_id[cid] for cid in current_ids] + [
            row for row in ordered if str(row["candidate_id"]) not in current_set
        ]
        current_ids = bounded_repair(synthetic_order, family_scores[family], loss_cap)
    return current_ids


def rotate_lane_ids(lane_ids: list[str]) -> dict[str, str]:
    ordered = sorted(lane_ids)
    return {
        lane_id: ordered[(index + 1) % len(ordered)]
        for index, lane_id in enumerate(ordered)
    }


def run() -> dict[str, Any]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--claims", required=True)
    parser.add_argument("--sources", required=True)
    parser.add_argument("--pools", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    claims = json.loads(Path(args.claims).read_text(encoding="utf-8"))
    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    pools = json.loads(Path(args.pools).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))

    registry_ids = set(registry_field_ids(registry))
    claims_by_lane = {str(row["lane_id"]): row for row in claims["lanes"]}
    sources_by_lane = load_lane_sources(sources)
    pools_by_lane = {str(row["lane_id"]): row for row in pools["lanes"]}

    lane_ids = sorted(claims_by_lane)
    if lane_ids != sorted(sources_by_lane) or lane_ids != sorted(pools_by_lane):
        raise RuntimeError("claim/source/pool lane identities do not match")

    tokenizer, model = semantic_model()

    gates: dict[str, dict[str, Any]] = {}
    carrier_packets: dict[str, dict[str, Any]] = {}
    carriers: dict[str, dict[str, Any]] = {}
    semantic_candidates: dict[str, list[dict[str, Any]]] = {}

    for lane_id in lane_ids:
        claim = str(claims_by_lane[lane_id]["claim"])
        gate = gate_result(claim, lane_id, sources_by_lane[lane_id])
        packet = gate_to_carrier_packet(lane_id, gate, registry_ids)
        requested = sorted(packet["fields"])
        carrier = build_shadow_carrier(
            registry=registry,
            packet=packet,
            requested_fields=requested,
        )

        materialized: list[dict[str, Any]] = []
        for candidate in pools_by_lane[lane_id]["candidates"]:
            row = dict(candidate)
            row["semantic_score"] = semantic_score(
                tokenizer,
                model,
                claim,
                str(candidate["text"]),
            )
            materialized.append(row)

        gates[lane_id] = gate
        carrier_packets[lane_id] = packet
        carriers[lane_id] = carrier
        semantic_candidates[lane_id] = semantic_order(materialized)

    representation = representation_summary(registry, carrier_packets)
    rotation = rotate_lane_ids(lane_ids)

    families = [
        "evidence_shape",
        "entities",
        "relation_targets",
        "temporal",
        "jurisdiction",
        "quantitative_signature",
        "negation",
        "modality",
        "attribution",
        "posture",
    ]
    staged = [
        "evidence_shape",
        "entities",
        "relation_targets",
        "quantitative_signature",
        "temporal",
        "jurisdiction",
    ]

    selections: dict[str, list[dict[str, Any]]] = defaultdict(list)
    family_availability: dict[str, Counter[str]] = {
        family: Counter() for family in families
    }

    for lane_id in lane_ids:
        ordered = semantic_candidates[lane_id]
        baseline = [str(row["candidate_id"]) for row in ordered[:3]]
        selections["baseline_no_gates_semantic_top3"].append(
            {"lane_id": lane_id, "selected_candidate_ids": baseline}
        )
        selections["placebo_gate_present_ignored"].append(
            {"lane_id": lane_id, "selected_candidate_ids": baseline}
        )

        correct_scores = {
            family: {
                str(row["candidate_id"]): gate_family_scores(
                    gates[lane_id],
                    str(claims_by_lane[lane_id]["claim"]),
                    str(row["text"]),
                )[family]
                for row in ordered
            }
            for family in families
        }
        wrong_gate = gates[rotation[lane_id]]
        wrong_scores = {
            family: {
                str(row["candidate_id"]): gate_family_scores(
                    wrong_gate,
                    str(claims_by_lane[lane_id]["claim"]),
                    str(row["text"]),
                )[family]
                for row in ordered
            }
            for family in families
        }

        for family in families:
            known = [v for v in correct_scores[family].values() if v is not None]
            family_availability[family]["lanes_with_known_candidate_scores"] += int(bool(known))
            family_availability[family]["lanes_with_candidate_discrimination"] += int(
                len(set(known)) > 1
            )
            for cap in LOSS_CAPS:
                label = f"{family}_correct_cap_{cap:.2f}"
                wrong_label = f"{family}_shuffled_cap_{cap:.2f}"
                selections[label].append(
                    {
                        "lane_id": lane_id,
                        "selected_candidate_ids": bounded_repair(
                            ordered, correct_scores[family], cap
                        ),
                    }
                )
                selections[wrong_label].append(
                    {
                        "lane_id": lane_id,
                        "selected_candidate_ids": bounded_repair(
                            ordered, wrong_scores[family], cap
                        ),
                    }
                )

        for cap in LOSS_CAPS:
            selections[f"staged_structural_correct_cap_{cap:.2f}"].append(
                {
                    "lane_id": lane_id,
                    "selected_candidate_ids": staged_repair(
                        ordered,
                        correct_scores,
                        staged,
                        cap,
                    ),
                }
            )
            selections[f"staged_structural_shuffled_cap_{cap:.2f}"].append(
                {
                    "lane_id": lane_id,
                    "selected_candidate_ids": staged_repair(
                        ordered,
                        wrong_scores,
                        staged,
                        cap,
                    ),
                }
            )

    if selections["baseline_no_gates_semantic_top3"] != selections["placebo_gate_present_ignored"]:
        raise AssertionError("placebo Gate-present control changed semantic baseline")

    output = {
        "schema": "eb-gate-field-pressure-dev-selections-v0",
        "classification": "EXPOSED_DEVELOPMENT_PRESSURE_ONLY",
        "authorities": {
            "proposition_authoring_subject": "e29a165b682d060f5dc2a0f3c7d64a7f29b172b4",
            "semantic_model": SEMANTIC_MODEL,
            "semantic_revision": SEMANTIC_REVISION,
            "claims_sha256": sha256_file(Path(args.claims)),
            "sources_sha256": sha256_file(Path(args.sources)),
            "pools_sha256": sha256_file(Path(args.pools)),
            "registry_sha256": sha256_file(Path(args.registry)),
        },
        "baseline": {
            "name": "baseline_no_gates_semantic_top3",
            "gate_fields_consumed": False,
            "gate_runtime_executed_for_baseline": False,
            "budget": 3,
        },
        "placebo_control": {
            "name": "placebo_gate_present_ignored",
            "must_equal_baseline": True,
            "observed_equal": True,
        },
        "representation_summary": representation,
        "family_availability": {
            family: dict(counter) for family, counter in family_availability.items()
        },
        "loss_caps": list(LOSS_CAPS),
        "shuffled_mapping": rotation,
        "selections": dict(sorted(selections.items())),
        "carrier_receipts": {
            lane_id: {
                "output_sha256": carriers[lane_id]["output_sha256"],
                "observations_sha256": carriers[lane_id]["observations_sha256"],
                "mask_sha256": carriers[lane_id]["mask_sha256"],
            }
            for lane_id in lane_ids
        },
        "nonclaims": [
            "the cohort is exposed development data and cannot qualify a successor",
            "no field is authorized for production or default EB use",
            "first-stage retrieval is unchanged",
            "gold is not consumed by this selection program",
        ],
    }
    output["output_sha256"] = sha256_json(output)
    Path(args.out).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(
        {
            "output_sha256": output["output_sha256"],
            "representation": representation,
            "arms": len(output["selections"]),
        },
        indent=2,
        sort_keys=True,
    ))
    return output


if __name__ == "__main__":
    run()
