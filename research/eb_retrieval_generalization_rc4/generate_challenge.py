#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SEED = 173205
BENCHMARK = "eb-retrieval-low-overlap-rc4-v1"
K = 5
PASSAGES_PER_CASE = 10
CONSTRUCTION_FAMILIES = (
    "policy",
    "procedure",
    "technical_explanatory",
    "incident",
    "faq_dialogue",
    "catalog_register",
    "multi_sentence_narrative",
    "conditional_declarative_summary",
)

# Fresh semantic scenarios. Each row is (entity, claim, decisive semantic sentence).
# L01-L04 decisive wording is deliberately low-overlap. C01 is deliberately high-overlap
# counterevidence so exact production BM25 has an independently testable positive surface.
SCENARIOS: dict[str, list[tuple[str, str, str]]] = {
    "L01": [
        ("Avenquo", "Avenquo sends a warning automatically when a storage room becomes too humid.", "At Avenquo, crossing the moisture ceiling causes an unattended notification."),
        ("Briskel", "Briskel removes remote access as soon as a contractor engagement ends.", "Briskel disables off-site credentials at the moment an external worker's assignment terminates."),
        ("Cadrivo", "Cadrivo keeps inspection images for two years after an inspection closes.", "Cadrivo preserves visual inspection records for twenty-four months following closure."),
        ("Delsun", "Delsun switches to reserve cooling when the primary chiller stops.", "Loss of the active chiller causes Delsun to place the standby thermal circuit in service."),
        ("Eltara", "Eltara blocks shipment when the seal record is missing.", "A consignment at Eltara remains on hold whenever no closure-integrity record is available."),
        ("Froven", "Froven recalibrates its torque sensor every four months.", "The Froven torque transducer undergoes metrological adjustment on a one-third-year cadence."),
        ("Gilmere", "Gilmere archives completed incident files for six years.", "Closed event dossiers at Gilmere remain retained for seventy-two months."),
        ("Halqen", "Halqen routes a failed identity check to manual review.", "An unsuccessful identity verification sends the Halqen request into human adjudication."),
    ],
    "L02": [
        ("Irvasto", "Irvasto releases a maintenance ticket only after isolation is verified and the supervisor signs off.", "At Irvasto, either unverified isolation or absent supervisory sign-off keeps the work item open."),
        ("Junex", "Junex starts a restore only if the backup checksum matches and the encryption key is available.", "Junex cannot begin recovery while either integrity verification fails or the required cryptographic key is unavailable."),
        ("Kablis", "Kablis publishes a report only when the reviewer approves it and every required appendix is present.", "A missing approval or any absent mandatory attachment is sufficient to keep a Kablis report unpublished."),
        ("Lomera", "Lomera enables a device only after calibration passes and the self-test succeeds.", "The Lomera unit remains disabled whenever either calibration or internal verification has not succeeded."),
        ("Meptrin", "Meptrin pays a supplier only after receipt is confirmed and the invoice matches the order.", "Meptrin withholds payment if delivery is unconfirmed or if invoice and purchase-order details disagree."),
        ("Norqua", "Norqua closes a deviation only when the cause is documented and all actions are complete.", "A Norqua deviation remains open if causal documentation is missing or any corrective task is unfinished."),
        ("Ostel", "Ostel activates an account only if identity proofing passes and a manager approves the request.", "Ostel keeps the account inactive whenever proof of identity fails or managerial authorization is absent."),
        ("Pruven", "Pruven accepts an import only when all mandatory fields exist and the schema revision is supported.", "Pruven rejects the import if any required field is absent or the declared schema release is unsupported."),
    ],
    "L03": [
        ("Qeldar", "Qeldar prevents one operator from approving the same change they submitted.", "Qeldar enforces separation between the requester and the person who authorizes that request."),
        ("Rismek", "Rismek stops packaging when the line camera loses focus.", "A loss of image sharpness causes the Rismek packing line to enter a halted state."),
        ("Savorin", "Savorin hides draft records from the monthly compliance total.", "Unfinalized entries are omitted from Savorin's periodic compliance aggregation."),
        ("Trelqua", "Trelqua locks a user after seven failed login attempts.", "Seven consecutive authentication failures cause Trelqua to disable further sign-in for that account."),
        ("Umbrik", "Umbrik diverts damaged containers to a manual inspection lane.", "Compromised packages are sent by Umbrik into the human examination queue."),
        ("Velmora", "Velmora drops telemetry messages that fail integrity checking.", "Velmora discards sensor transmissions whose validation code does not verify."),
        ("Wexlin", "Wexlin reserves inventory before it confirms a customer order.", "Wexlin allocates stock ahead of issuing the order confirmation."),
        ("Xadren", "Xadren quarantines an uploaded file when malicious code is detected.", "Detection of malware causes Xadren to isolate the incoming artifact from normal processing."),
    ],
    "L04": [
        ("Yelmor", "Yelmor pauses a batch when a required environmental reading is absent.", "Yelmor keeps the lot from advancing whenever the environmental record has a required gap."),
        ("Zafrin", "Zafrin refuses a release when the electronic signature cannot be verified.", "An unverifiable digital attestation keeps the Zafrin item outside the released state."),
        ("Arquest", "Arquest switches database requests to a replica when the active node fails.", "Loss of the primary data node causes Arquest to redirect traffic toward its standby copy."),
        ("Brelko", "Brelko prevents an expired certificate from opening a remote session.", "A remote connection at Brelko is denied when its presented credential is past validity."),
        ("Cuvane", "Cuvane holds a return when fraud screening marks it high risk.", "A high-risk fraud outcome places the Cuvane return into a non-release review state."),
        ("Draxil", "Draxil removes cached records after forty minutes without access.", "Objects in the Draxil cache are evicted after two-thirds of an hour of inactivity."),
        ("Evorun", "Evorun rejects a sample when the subject identifier is absent.", "A specimen without a subject identity cannot enter Evorun processing."),
        ("Fenqua", "Fenqua repeats the sanitation cycle when the biological indicator is positive.", "Evidence of surviving organisms causes Fenqua to run the decontamination sequence again."),
    ],
    "C01": [
        ("Greslin", "Greslin permits unsigned packages to enter production.", "Greslin does not permit unsigned packages to enter production; unsigned packages are blocked."),
        ("Hovara", "Hovara allows an operator to erase audit events.", "Hovara does not allow an operator to erase audit events; audit events are append-only."),
        ("Ismere", "Ismere releases a lot before required laboratory results are complete.", "Ismere does not release a lot before required laboratory results are complete; release remains blocked."),
        ("Juxen", "Juxen permits external drives on controlled workstations.", "Juxen does not permit external drives on controlled workstations; external drives are prohibited."),
        ("Korlis", "Korlis keeps default administrator passwords enabled after installation.", "Korlis does not keep default administrator passwords enabled after installation; those passwords must be disabled."),
        ("Lumeq", "Lumeq allows a requester to approve their own expense claim.", "Lumeq does not allow a requester to approve their own expense claim; self-approval is forbidden."),
        ("Mardel", "Mardel accepts a shipment when its tamper seal is broken.", "Mardel does not accept a shipment when its tamper seal is broken; the shipment is rejected."),
        ("Nevrin", "Nevrin sends identified patient data to analytics without de-identification.", "Nevrin does not send identified patient data to analytics without de-identification; direct identifiers are removed first."),
    ],
}

# Eight intentionally heterogeneous, role-neutral cue profiles. Every role traverses
# every profile under the paired design; L04 explicitly exchanges the decisive and
# hard-negative profile between paired variants while semantic roles stay fixed.
CUE_PROFILES = [
    {"construction_family": "policy", "length_bin": "short", "sentence_position": "beginning", "punctuation": "plain", "identifier_pattern": "alpha_dash", "metadata_style": "sparse", "realization": "concise"},
    {"construction_family": "procedure", "length_bin": "medium", "sentence_position": "middle", "punctuation": "numbered", "identifier_pattern": "numeric_dash", "metadata_style": "dense", "realization": "verbose"},
    {"construction_family": "technical_explanatory", "length_bin": "long", "sentence_position": "end", "punctuation": "colon", "identifier_pattern": "dot_code", "metadata_style": "medium", "realization": "verbose"},
    {"construction_family": "incident", "length_bin": "medium", "sentence_position": "beginning", "punctuation": "semicolon", "identifier_pattern": "slash_code", "metadata_style": "sparse", "realization": "concise"},
    {"construction_family": "faq_dialogue", "length_bin": "short", "sentence_position": "middle", "punctuation": "qa", "identifier_pattern": "compact", "metadata_style": "medium", "realization": "concise"},
    {"construction_family": "catalog_register", "length_bin": "long", "sentence_position": "end", "punctuation": "pipe", "identifier_pattern": "registry", "metadata_style": "dense", "realization": "verbose"},
    {"construction_family": "multi_sentence_narrative", "length_bin": "long", "sentence_position": "middle", "punctuation": "narrative", "identifier_pattern": "alpha_numeric", "metadata_style": "sparse", "realization": "verbose"},
    {"construction_family": "conditional_declarative_summary", "length_bin": "medium", "sentence_position": "end", "punctuation": "conditional", "identifier_pattern": "mixed", "metadata_style": "dense", "realization": "concise"},
]

NEUTRAL_FILLER = [
    "The record was reviewed under the ordinary documentation cycle.",
    "This entry uses the same source boundary as the neighboring material.",
    "The note was retained for routine traceability and later reference.",
]


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def profile_for(family: str, scenario_index: int, variant: int, role: str, distractor_index: int | None = None) -> int:
    if role == "decisive":
        base = scenario_index
    elif role == "hard_negative":
        base = (scenario_index + 3) % 8
    else:
        assert distractor_index is not None
        base = (distractor_index + scenario_index) % 8
    if variant == 0:
        return base
    if family == "L04" and role in {"decisive", "hard_negative"}:
        return (scenario_index + 3) % 8 if role == "decisive" else scenario_index
    return (base + 4) % 8


def source_id(case_id: str, source_order: int, pattern: str) -> str:
    digest = hashlib.sha256(f"{case_id}:{source_order}".encode()).hexdigest()
    n = int(digest[:6], 16) % 900 + 100
    case_tag = hashlib.sha256(case_id.encode()).hexdigest()[:6]
    prefix = case_id.lower().replace("-", "")[:5]
    # Every identifier family retains a visibly different surface pattern while a
    # case-derived tag guarantees global provenance identity without encoding role.
    patterns = {
        "alpha_dash": f"src-{prefix}-{case_tag}-{chr(64 + source_order)}",
        "numeric_dash": f"doc-{n}-{case_tag}-{source_order}",
        "dot_code": f"REG.{n}.{case_tag}.{source_order}",
        "slash_code": f"rec/{prefix}/{case_tag}/{source_order}",
        "compact": f"D{n}{case_tag}{source_order}",
        "registry": f"register-{source_order:02d}-{n}-{case_tag}",
        "alpha_numeric": f"{prefix.upper()}{n}{case_tag.upper()}S{source_order}",
        "mixed": f"r-{n}.{prefix}-{case_tag}-{source_order}",
    }
    return patterns[pattern]


def metadata_for(case_id: str, profile: dict[str, str]) -> dict[str, str]:
    tag = hashlib.sha256(case_id.encode()).hexdigest()[:6]
    if profile["metadata_style"] == "sparse":
        return {"section": "general"}
    if profile["metadata_style"] == "medium":
        return {"section": "general", "record_tag": f"r{tag}"}
    return {"section": "general", "record_tag": f"r{tag}", "revision_note": "routine"}


def render_semantic(semantic_sentence: str, profile: dict[str, str]) -> str:
    construction = profile["construction_family"]
    before: list[str] = []
    after: list[str] = []
    filler_count = {"short": 0, "medium": 1, "long": 2}[profile["length_bin"]]
    fillers = NEUTRAL_FILLER[:filler_count]
    if profile["sentence_position"] == "beginning":
        after = fillers
    elif profile["sentence_position"] == "middle":
        before = fillers[:1]
        after = fillers[1:]
    else:
        before = fillers

    if construction == "policy":
        semantic = f"Policy statement: {semantic_sentence}"
    elif construction == "procedure":
        semantic = f"Procedure entry, step 2: {semantic_sentence}"
    elif construction == "technical_explanatory":
        semantic = f"Technical explanation: {semantic_sentence}"
    elif construction == "incident":
        semantic = f"Incident review recorded this operating statement: {semantic_sentence}"
    elif construction == "faq_dialogue":
        semantic = f"Question: What applies here? Answer: {semantic_sentence}"
    elif construction == "catalog_register":
        semantic = f"Register entry | topic=control | statement={semantic_sentence}"
    elif construction == "multi_sentence_narrative":
        semantic = f"During routine review, the team checked the relevant control. {semantic_sentence}"
    else:
        semantic = f"Conditional summary: under the stated condition, {semantic_sentence}"

    parts = before + [semantic] + after
    text = " ".join(parts)
    if profile["punctuation"] == "semicolon":
        text = text.replace(". ", "; ", 1)
    elif profile["punctuation"] == "numbered":
        text = "1) context recorded. 2) " + text
    elif profile["punctuation"] == "pipe":
        text = text.replace(" ", " | ", 3)
    elif profile["punctuation"] == "qa" and not text.startswith("Question:"):
        text = "Q: control? A: " + text
    return text


def hard_negative_sentence(entity: str, claim: str, scenario_index: int) -> str:
    q = claim.rstrip(".")
    templates = (
        f"A retired {entity} design memo contains the sentence '{q}'. The option described in that memo was never activated.",
        f"During a {entity} tabletop exercise, participants were instructed to assume '{q}' as a fictional scenario condition.",
        f"A {entity} supplier questionnaire reproduces the proposition '{q}' as an item for respondents to assess.",
        f"A {entity} configuration comparison quotes '{q}' under an alternative profile that is not the active profile.",
        f"A historical {entity} migration note records that staff once expected '{q}' before the current control set was installed.",
        f"A {entity} test fixture uses the literal string '{q}' as synthetic input for parser verification.",
        f"A rejected {entity} change request proposed '{q}' but the request was not adopted.",
        f"A {entity} troubleshooting transcript repeats '{q}' while documenting an operator report later determined to be mistaken.",
    )
    return templates[scenario_index % len(templates)]


def distractor_sentences(entity: str, claim: str) -> list[str]:
    # Runtime-visible distractors are ordinary declarative records rather than
    # uniformly labelled "no answer" text. This prevents a query-independent
    # answer-marker heuristic from locating the decisive passage by presentation.
    return [
        f"The {entity} control register assigns each active safeguard an owner and a scheduled review date.",
        f"The {entity} monitoring service records timestamps for environmental and system events.",
        f"The {entity} operator guide describes where routine status messages are displayed.",
        f"The {entity} archive preserves revision history for approved operating documents.",
        f"The {entity} dashboard reports current service health to authorized users.",
        f"The {entity} maintenance log records completed checks and technician initials.",
        f"The {entity} training catalog organizes modules by control area and staff role.",
        f"The {entity} support queue routes incident reports to the responsible service team.",
    ]


def c01_distractors(entity: str, claim: str) -> list[str]:
    return distractor_sentences(entity, claim)


def make_case(family: str, family_index: int, scenario_index: int, variant: int, spec: tuple[str, str, str]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    entity, claim, decisive_semantic = spec
    pair_id = f"{family}-S{scenario_index + 1:02d}"
    case_id = f"{pair_id}-{'A' if variant == 0 else 'B'}"
    subset_id = f"scope-{case_id.lower()}"
    global_scenario = family_index * 8 + scenario_index
    decisive_pos_a = (global_scenario % 10) + 1
    hard_pos_a = ((decisive_pos_a - 1 + 5) % 10) + 1
    if variant == 0:
        decisive_pos, hard_pos = decisive_pos_a, hard_pos_a
    else:
        decisive_pos, hard_pos = hard_pos_a, decisive_pos_a

    role_semantics: list[tuple[str, str]] = []
    role_semantics.append(("decisive", decisive_semantic))
    role_semantics.append(("hard_negative", hard_negative_sentence(entity, claim, scenario_index)))
    dists = c01_distractors(entity, claim) if family == "C01" else distractor_sentences(entity, claim)
    role_semantics.extend((f"distractor_{i + 1}", s) for i, s in enumerate(dists))

    occupied = {decisive_pos: 0, hard_pos: 1}
    remaining_positions = [p for p in range(1, 11) if p not in occupied]
    for idx, pos in enumerate(remaining_positions, start=2):
        occupied[pos] = idx

    passages: list[dict[str, Any]] = []
    hidden: dict[str, Any] = {}
    for global_pos in range(1, 11):
        role_idx = occupied[global_pos]
        role, semantic_sentence = role_semantics[role_idx]
        dist_index = role_idx - 2 if role_idx >= 2 else None
        pidx = profile_for(family, scenario_index, variant, role if role_idx < 2 else "distractor", dist_index)
        profile = dict(CUE_PROFILES[pidx])
        source_order = (global_pos - 1) // 2 + 1
        passage_order = (global_pos - 1) % 2 + 1
        sid = source_id(case_id, source_order, profile["identifier_pattern"])
        pid = f"{sid}#p{passage_order}"
        text = render_semantic(semantic_sentence, profile)
        passages.append({
            "case_id": case_id,
            "source_id": sid,
            "passage_id": pid,
            "source_order": source_order,
            "passage_order": passage_order,
            "text": text,
            "runtime_metadata": metadata_for(case_id, profile),
            "text_sha256": sha256_bytes(text.encode("utf-8")),
        })
        hidden[pid] = {
            "role": role,
            "semantic_sentence": semantic_sentence,
            "cue_profile_index": pidx,
            "cue_profile": profile,
            "global_position": global_pos,
            "source_order": source_order,
            "passage_order": passage_order,
        }

    decisive_pid = next(pid for pid, h in hidden.items() if h["role"] == "decisive")
    hard_pid = next(pid for pid, h in hidden.items() if h["role"] == "hard_negative")
    by_pid = {p["passage_id"]: p for p in passages}
    case = {
        "case_id": case_id,
        "pair_id": pair_id,
        "variant": "A" if variant == 0 else "B",
        "claim_text": claim,
        "accessible_subset_id": subset_id,
        "runtime_config": {"maximum_passages": K},
    }
    gold = {
        "case_id": case_id,
        "pair_id": pair_id,
        "variant": case["variant"],
        "family": family,
        "answerable": True,
        "entity_stem": entity,
        "decisive": [{"source_id": by_pid[decisive_pid]["source_id"], "passage_id": decisive_pid, "role": "counterevidence" if family == "C01" else "decisive"}],
        "hard_negatives": [{"source_id": by_pid[hard_pid]["source_id"], "passage_id": hard_pid}],
        "hidden_passage_annotations": hidden,
        "paired_surface_rule": "semantic_roles_fixed_cue_profiles_and_positions_exchanged",
    }
    return case, passages, gold


def build(root: Path) -> None:
    runtime = root / "runtime"
    evaluator_only = root / "evaluator_only"
    provenance = root / "provenance"
    for d in (runtime, evaluator_only, provenance):
        d.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, Any]] = []
    passages: list[dict[str, Any]] = []
    gold_rows: list[dict[str, Any]] = []
    scopes: dict[str, Any] = {}
    family_membership: dict[str, list[str]] = {f: [] for f in SCENARIOS}

    for family_index, family in enumerate(("L01", "L02", "L03", "L04", "C01")):
        specs = SCENARIOS[family]
        assert len(specs) == 8
        for scenario_index, spec in enumerate(specs):
            for variant in (0, 1):
                case, ps, gold = make_case(family, family_index, scenario_index, variant, spec)
                cases.append(case)
                passages.extend(ps)
                gold_rows.append(gold)
                family_membership[family].append(case["case_id"])
                scopes[case["accessible_subset_id"]] = {
                    "subset_id": case["accessible_subset_id"],
                    "case_id": case["case_id"],
                    "source_ids": sorted({p["source_id"] for p in ps}),
                    "passage_ids": [p["passage_id"] for p in sorted(ps, key=lambda r: (r["source_order"], r["passage_order"]))],
                }

    assert len(cases) == 80
    assert len(passages) == 800
    dump_jsonl(runtime / "sealed_cases.jsonl", cases)
    dump_jsonl(runtime / "passages.jsonl", passages)
    dump_json(runtime / "scopes.json", scopes)
    dump_jsonl(evaluator_only / "sealed_gold.jsonl", gold_rows)
    dump_json(evaluator_only / "family_membership.json", family_membership)

    receipt = {
        "benchmark": BENCHMARK,
        "generator_seed": SEED,
        "sealed_cases": len(cases),
        "passages": len(passages),
        "family_counts": {f: len(v) for f, v in family_membership.items()},
        "semantic_scenarios_per_family": 8,
        "surface_variants_per_scenario": 2,
        "maximum_passages": K,
        "passages_per_case": PASSAGES_PER_CASE,
        "construction_families": list(CONSTRUCTION_FAMILIES),
        "hybrid_sealed_exposed": False,
        "semantic_sealed_exposed": False,
        "candidate_output_used": False,
    }
    dump_json(provenance / "generator_receipt.json", receipt)

    readme = f"""# {BENCHMARK}\n\nFresh deterministic RC4 Research-Infrastructure object for PR #18.\n\n- seed: `{SEED}`\n- 80 sealed answerable cases: 16 each L01, L02, L03, L04, C01\n- each family: 8 semantic scenarios × 2 paired surface variants\n- 10 scoped passages per case; top-K budget 5\n- runtime material is physically separated from evaluator-only roles/cues\n- paired variants exchange surface/cue placement while preserving semantic identity\n- L04 explicitly exchanges decisive/hard-negative cue profiles while semantic roles remain fixed\n- no Hybrid or Semantic-only output is generated by construction\n\nThe object is not authorized for target exposure unless the separately frozen apparatus assurance passes all preregistered gates.\n"""
    (root / "README.md").write_text(readme, encoding="utf-8")

    tracked = [
        runtime / "sealed_cases.jsonl",
        runtime / "passages.jsonl",
        runtime / "scopes.json",
        evaluator_only / "sealed_gold.jsonl",
        evaluator_only / "family_membership.json",
        provenance / "generator_receipt.json",
    ]
    (root / "SHA256SUMS").write_text("".join(f"{sha256(p)}  {p.relative_to(root).as_posix()}\n" for p in tracked), encoding="utf-8")
    dump_json(root / "manifest.json", {
        "benchmark": BENCHMARK,
        "generator_seed": SEED,
        "sealed_cases": 80,
        "runtime_files": ["runtime/sealed_cases.jsonl", "runtime/passages.jsonl", "runtime/scopes.json"],
        "evaluator_only_files": ["evaluator_only/sealed_gold.jsonl", "evaluator_only/family_membership.json"],
        "provenance_files": ["provenance/generator_receipt.json"],
        "sha256sums": "SHA256SUMS",
        "runtime_gold_physical_separation": True,
        "hybrid_sealed_exposed": False,
        "semantic_sealed_exposed": False,
    })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-root", type=Path, required=True)
    args = ap.parse_args()
    build(args.output_root)


if __name__ == "__main__":
    main()
