#!/usr/bin/env python3
"""Build the frozen eb-challenge-corpus-v1 synthetic benchmark.

The generator is intentionally self-contained and deterministic. It creates a
fictional Neralis Compact document world from a seeded standard-library RNG;
it does not inspect, import, or adapt any Evidence Bundler output. Runtime
inputs and evaluator-only gold are written to physically separate roots.

This is a benchmark-construction tool, not a regulatory, compliance, or
software-validation tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
from collections import Counter, OrderedDict, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable


GENERATOR_NAME = "eb-challenge-corpus-generator"
GENERATOR_VERSION = "1.0.0"
CORPUS_NAME = "eb-challenge-corpus-v1"
CORPUS_VERSION = "1.0.0"
DEFAULT_SEED = 271828
DEFAULT_AS_OF = "2026-08-27"
FIXED_GENERATION_TIMESTAMP = "2026-08-27T00:00:00Z"
GOLD_RECORD_VERSION = "1.0"
ADJUDICATOR_ID = "synthetic-adjudicator-rulebook-1.0"
OFFSET_UNIT = "utf8_byte"

RELEVANCE_CLASSES = {
    "decisive_support",
    "decisive_contradiction",
    "decisive_qualifier",
    "decisive_exception",
    "material_context",
    "hard_negative",
    "irrelevant",
}

DECOMPOSITION_FAMILIES = {"F03", "F04", "F05", "F06", "F10", "F12"}

TREE_HASH_EXCLUSIONS = {
    "corpus_manifest.json",
    "SHA256SUMS",
    "validation/corpus_validation_report.json",
    "validation/freeze_receipt.json",
}


TOPIC_SEEDS = [
    {
        "slug": "rimebridge",
        "display": "Rimebridge rinse train",
        "system": "Rimebridge-7 rinse controller",
        "product": "Morrowglass cartridge",
        "facility": "Sable Yard",
        "prefix": "RBR",
        "parameter": "pre-use inspection window",
        "unit": "minutes",
    },
    {
        "slug": "quillmark",
        "display": "Quillmark seal ledger",
        "system": "Quillmark-3 seal ledger",
        "product": "Tansy fold pack",
        "facility": "Nettle Quay",
        "prefix": "QMK",
        "parameter": "second-look interval",
        "unit": "minutes",
    },
    {
        "slug": "cinderwell",
        "display": "Cinderwell thermal hold",
        "system": "Cinderwell-4 thermal cabinet",
        "product": "Emberleaf cassette",
        "facility": "Hearth Annex",
        "prefix": "CDW",
        "parameter": "hold temperature",
        "unit": "degrees C",
    },
    {
        "slug": "larkspur",
        "display": "Larkspur label sleeve",
        "system": "Larkspur-12 label press",
        "product": "Pale Finch vial sleeve",
        "facility": "Mica Court",
        "prefix": "LSP",
        "parameter": "scan tolerance",
        "unit": "millimetres",
    },
    {
        "slug": "micaarray",
        "display": "Mica sensor array",
        "system": "Mica-4 sensor array",
        "product": "Blue Thistle probe",
        "facility": "Loam House",
        "prefix": "MCA",
        "parameter": "witness scan window",
        "unit": "minutes",
    },
    {
        "slug": "amberbraid",
        "display": "Amberbraid supplier lot",
        "system": "Amberbraid receiving cell",
        "product": "Ochre filament spool",
        "facility": "Copper Gate",
        "prefix": "AMB",
        "parameter": "pedigree reconciliation window",
        "unit": "hours",
    },
    {
        "slug": "vellumcal",
        "display": "Vellum calibration bench",
        "system": "Vellum-8 calibration bench",
        "product": "Gossamer reference plate",
        "facility": "Reed Observatory",
        "prefix": "VLM",
        "parameter": "reference equilibration time",
        "unit": "hours",
    },
    {
        "slug": "brambleline",
        "display": "Bramble line clearance",
        "system": "Bramble-5 clearance rail",
        "product": "Juniper assembly",
        "facility": "Briar Hall",
        "prefix": "BRM",
        "parameter": "clearance review window",
        "unit": "hours",
    },
    {
        "slug": "morrowquay",
        "display": "Morrow quarantine rack",
        "system": "Morrow-2 quarantine rack",
        "product": "Siltstone lot",
        "facility": "Morrow Gate",
        "prefix": "MRQ",
        "parameter": "segregation clock",
        "unit": "hours",
    },
    {
        "slug": "oriolegate",
        "display": "Oriole batch gate",
        "system": "Oriole-6 batch gate",
        "product": "Cobalt reed batch",
        "facility": "Oriole Yard",
        "prefix": "ORL",
        "parameter": "release review interval",
        "unit": "hours",
    },
    {
        "slug": "blueglass",
        "display": "Blueglass supplier lot",
        "system": "Blueglass receiving cell",
        "product": "Slate filament spool",
        "facility": "West Lantern",
        "prefix": "BLG",
        "parameter": "pedigree reconciliation window",
        "unit": "hours",
    },
    {
        "slug": "wickarchive",
        "display": "Wick archive retrieval",
        "system": "Wick-9 archive relay",
        "product": "Cairn record bundle",
        "facility": "Quiet Stack",
        "prefix": "WCK",
        "parameter": "archive retention period",
        "unit": "days",
    },
]


FAMILY_PLANS = {
    "F01": [
        ("current", "sop"),
        ("support", "policy"),
        ("incident", "deviation_report"),
        ("faq", "faq"),
        ("record", "decision_record"),
    ],
    "F02": [
        ("current", "technical_specification"),
        ("support", "work_instruction"),
        ("incident", "supplier_bulletin"),
        ("faq", "knowledge_base_article"),
        ("record", "meeting_record"),
    ],
    "F03": [
        ("current", "sop"),
        ("support", "policy"),
        ("incident", "incident_report"),
        ("faq", "faq"),
        ("record", "change_control_notice"),
    ],
    "F04": [
        ("current", "technical_specification"),
        ("support", "sop"),
        ("incident", "validation_report"),
        ("faq", "supplier_bulletin"),
        ("record", "meeting_record"),
    ],
    "F05": [
        ("current", "sop"),
        ("prior", "sop"),
        ("draft", "sop"),
        ("incident", "incident_report"),
        ("faq", "faq"),
    ],
    "F06": [
        ("current", "policy"),
        ("support", "sop"),
        ("incident", "guidance_note"),
        ("faq", "deviation_report"),
        ("record", "decision_record"),
    ],
    "F07": [
        ("current", "sop"),
        ("support", "technical_specification"),
        ("incident", "incident_report"),
        ("faq", "knowledge_base_article"),
        ("record", "change_control_notice"),
    ],
    "F08": [
        ("current", "sop"),
        ("support", "policy"),
        ("incident", "faq"),
        ("faq", "meeting_record"),
        ("record", "background_note"),
    ],
    "F09": [
        ("current", "sop"),
        ("guide", "guidance_note"),
        ("incident", "validation_report"),
        ("faq", "faq"),
        ("record", "background_note"),
    ],
    "F10": [
        ("current", "sop"),
        ("support", "technical_specification"),
        ("incident", "meeting_record"),
        ("faq", "validation_report"),
        ("record", "faq"),
    ],
    "F11": [
        ("current", "policy"),
        ("support", "sop"),
        ("incident", "knowledge_base_article"),
        ("faq", "incident_report"),
        ("record", "meeting_record"),
    ],
    "F12": [
        ("current", "sop"),
        ("support", "technical_specification"),
        ("incident", "change_control_notice"),
        ("faq", "faq"),
        ("record", "decision_record"),
    ],
}


FAMILY_NAMES = {
    "F01": "LEXICALLY_OBVIOUS",
    "F02": "SYNONYM_PARAPHRASE",
    "F03": "NEGATION_POLARITY",
    "F04": "NUMERIC_THRESHOLD",
    "F05": "TEMPORAL_SUPERSESSION",
    "F06": "CONDITION_EXCEPTION",
    "F07": "HARD_LEXICAL_DISTRACTOR",
    "F08": "DUPLICATE_PARAPHRASE",
    "F09": "LONG_DOCUMENT_BURIED",
    "F10": "MULTI_PASSAGE_COMPOSITION",
    "F11": "NO_ANSWER",
    "F12": "APERTURE_BOUNDARY",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_text(path: Path, text: str) -> None:
    write_bytes(path, text.encode("utf-8"))


def write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    payload = json.dumps(value, indent=2, sort_keys=sort_keys, ensure_ascii=True) + "\n"
    write_text(path, payload)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    payload = "".join(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n" for row in rows)
    write_text(path, payload)


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"date must be YYYY-MM-DD: {value}") from exc


def derived_rng(seed: int, label: str) -> random.Random:
    material = sha256_text(f"{seed}:{label}")
    return random.Random(int(material[:16], 16))


def stable_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def source_id(topic_slug: str, role: str) -> str:
    return f"src-{stable_slug(topic_slug)}-{stable_slug(role)}"


def passage_id_for(source: str, paragraph_index: int) -> str:
    return f"pas-{sha256_text(source)[:12]}-{paragraph_index:03d}"


def generator_commit(project_root: Path) -> str | None:
    script_path = Path(__file__).resolve()
    try:
        relative_script = script_path.relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return None
    try:
        subprocess.run(
            ["git", "-C", str(project_root), "ls-files", "--error-unmatch", relative_script],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        # The project directory is commonly ignored in this workspace. Do not
        # present an unrelated repository HEAD as the generator's source ID.
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def generator_source_hash() -> str:
    return sha256_file(Path(__file__).resolve())


def file_tree_hash(root: Path) -> str:
    rows: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in TREE_HASH_EXCLUSIONS:
            continue
        rows.append(f"{relative}\t{sha256_file(path)}")
    return sha256_text("\n".join(rows) + "\n")


def build_topics(as_of: date, seed: int) -> dict[str, dict[str, Any]]:
    topics: dict[str, dict[str, Any]] = {}
    owner_pool = [
        "Cell Operations",
        "Records Stewardship",
        "Instrument Services",
        "Release Coordination",
        "Supplier Liaison",
        "Archive Services",
    ]
    scope_pool = [
        "the named product in the named facility",
        "sealed lots on the second shift",
        "units carrying the current work order",
        "records opened by the assigned owner",
        "the local release lane",
    ]
    condition_pool = [
        "the witness token is present",
        "the second sample is logged",
        "the tamper flag is clear",
        "the local mirror has synchronized",
        "the supervisor has acknowledged the event",
    ]
    for seed_row in TOPIC_SEEDS:
        rng = derived_rng(seed, f"topic:{seed_row['slug']}")
        current_minutes = rng.randint(14, 32)
        old_minutes = current_minutes + rng.choice([4, 5, 6])
        near_minutes = current_minutes + 1
        current_hours = rng.randint(4, 11)
        old_hours = current_hours + rng.choice([2, 3])
        near_hours = current_hours + 1
        current_days = rng.choice([14, 21, 28, 35, 42])
        old_days = current_days + rng.choice([7, 14])
        near_days = current_days + 1
        threshold_tenths = rng.randint(24, 68)
        threshold = f"{threshold_tenths / 10:.1f}"
        near_threshold = f"{(threshold_tenths + rng.choice([1, 2])) / 10:.1f}"
        drift_tenths = rng.randint(2, 8)
        drift_limit = f"{drift_tenths / 10:.1f}"
        yield_pct = rng.randint(87, 97)
        sample_count = rng.randint(5, 12)
        zone_count = rng.randint(3, 7)
        failed_attempts = rng.randint(3, 6)
        session_minutes = rng.choice([12, 15, 20, 25])
        rest_hours = rng.choice([2, 4, 6, 8])
        review_hours = rng.choice([6, 8, 12, 16])
        owner = rng.choice(owner_pool)
        reviewer = rng.choice([x for x in owner_pool if x != owner])
        scope = rng.choice(scope_pool)
        condition = rng.choice(condition_pool)
        asset_code = f"{seed_row['prefix']}-{rng.randint(104, 982)}"
        record_code = f"{seed_row['prefix']}-REC-{rng.randint(110, 899)}"
        lot_code = f"{seed_row['prefix']}-LOT-{rng.randint(120, 889)}"
        current_effective = as_of - timedelta(days=rng.randint(24, 96))
        prior_effective = current_effective - timedelta(days=rng.randint(310, 690))
        future_effective = as_of + timedelta(days=rng.randint(45, 160))
        incident_date = as_of - timedelta(days=rng.randint(3, 42))
        topics[seed_row["slug"]] = {
            **seed_row,
            "subject": seed_row["display"],
            "as_of": as_of.isoformat(),
            "asset_code": asset_code,
            "record_code": record_code,
            "lot_code": lot_code,
            "owner": owner,
            "reviewer": reviewer,
            "scope": scope,
            "condition": condition,
            "current_minutes": current_minutes,
            "old_minutes": old_minutes,
            "near_minutes": near_minutes,
            "current_hours": current_hours,
            "old_hours": old_hours,
            "near_hours": near_hours,
            "current_days": current_days,
            "old_days": old_days,
            "near_days": near_days,
            "threshold": threshold,
            "near_threshold": near_threshold,
            "drift_limit": drift_limit,
            "yield_pct": yield_pct,
            "near_yield_pct": max(1, yield_pct - 1),
            "sample_count": sample_count,
            "zone_count": zone_count,
            "failed_attempts": failed_attempts,
            "session_minutes": session_minutes,
            "rest_hours": rest_hours,
            "review_hours": review_hours,
            "current_effective": current_effective.isoformat(),
            "prior_effective": prior_effective.isoformat(),
            "future_effective": future_effective.isoformat(),
            "incident_date": incident_date.isoformat(),
            "review_date": (as_of + timedelta(days=rng.randint(18, 72))).isoformat(),
            "second_sample": rng.randint(2, 5),
            "badge_attempts": failed_attempts,
            "temporary_window": rng.choice([15, 20, 30, 45]),
            "archive_days": rng.choice([45, 60, 75, 90]),
            "handoff_code": f"{seed_row['prefix']}-H{rng.randint(10, 99)}",
            "operator_group": rng.choice(["the east cell", "the night cell", "the records desk", "the release desk"]),
            "condition_text": condition,
        }
    return topics


def evidence(
    role: str,
    anchor: str,
    text: str,
    relevance_class: str = "decisive_support",
    *,
    decisive: bool = True,
    jointly_required: bool = False,
    joint_group_id: str | None = None,
    rationale: str,
) -> dict[str, Any]:
    if relevance_class not in RELEVANCE_CLASSES:
        raise ValueError(f"unknown relevance class: {relevance_class}")
    return {
        "role": role,
        "anchor": anchor,
        "text": text,
        "relevance_class": relevance_class,
        "decisive": decisive,
        "jointly_required": jointly_required,
        "joint_group_id": joint_group_id,
        "rationale": rationale,
    }


def hard_negative(role: str, anchor: str, text: str) -> dict[str, Any]:
    return {"role": role, "anchor": anchor, "text": text}


def add_claim(
    claims: list[dict[str, Any]],
    *,
    family_id: str,
    local_index: int,
    topic_slug: str,
    original_claim_text: str,
    evidence_rows: list[dict[str, Any]],
    negative: dict[str, Any],
    answerable: bool = True,
    subset_id: str,
    decomp_parts: list[str] | None = None,
) -> None:
    claim_id = f"claim-{len(claims) + 1:03d}"
    claims.append(
        {
            "original_claim_id": claim_id,
            "local_index": local_index,
            "family_id": family_id,
            "topic_slug": topic_slug,
            "original_claim_text": original_claim_text,
            "evidence": evidence_rows,
            "hard_negative": negative,
            "answerable": answerable,
            "accessible_subset_id": subset_id,
            "decomp_sensitive": family_id in DECOMPOSITION_FAMILIES,
            "decomp_parts": decomp_parts,
        }
    )


def build_claims(topics: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []

    t = topics["rimebridge"]
    add_claim(
        claims,
        family_id="F01",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text=(
            f"The {t['system']} requires a {t['current_minutes']}-minute pre-use inspection "
            "before each run and a second-operator signature."
        ),
        evidence_rows=[
            evidence(
                "current",
                "f01-inspection",
                f"For every {t['subject']} run, operators perform a {t['current_minutes']}-minute pre-use inspection and obtain a second-operator signature before start.",
                rationale="The current operating SOP states both the inspection duration and the witness-signature step in one control paragraph.",
            )
        ],
        negative=hard_negative(
            "support",
            "f01-inspection-near",
            f"The adjacent rinse lane uses a {t['near_minutes']}-minute pre-use inspection and accepts the first operator's initial without a second signature.",
        ),
        subset_id="ordinary_window",
    )
    add_claim(
        claims,
        family_id="F01",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text=f"Rimebridge scan history is retained for {t['current_days']} days.",
        evidence_rows=[
            evidence(
                "current",
                "f01-retention",
                f"Rimebridge scan history remains available in the controlled register for {t['current_days']} days after the run closes.",
                rationale="The current SOP gives the retention duration directly.",
            )
        ],
        negative=hard_negative(
            "faq",
            "f01-retention-near",
            f"The quick-reference card mentions a {t['near_days']}-day display cache for Rimebridge scans; the cache is not the controlled register.",
        ),
        subset_id="ordinary_window",
    )
    add_claim(
        claims,
        family_id="F01",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text=f"The release owner for asset {t['asset_code']} is {t['owner']}.",
        evidence_rows=[
            evidence(
                "current",
                "f01-owner",
                f"Asset {t['asset_code']} is assigned to {t['owner']}; that group owns the release decision for the Rimebridge lane.",
                rationale="The assignment line names the owner and ties it to the release decision.",
            )
        ],
        negative=hard_negative(
            "support",
            "f01-owner-near",
            f"Asset {t['asset_code']} is serviced by {t['reviewer']}; service responsibility is not release ownership.",
        ),
        subset_id="ordinary_window",
    )
    add_claim(
        claims,
        family_id="F01",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text=f"The {t['system']} needs a witness token before its release latch can open.",
        evidence_rows=[
            evidence(
                "current",
                "f01-token",
                f"The release latch on {t['system']} remains closed until a witness token is attached to record {t['record_code']}.",
                rationale="The latch prerequisite is stated as an explicit precondition.",
            )
        ],
        negative=hard_negative(
            "incident",
            "f01-token-near",
            f"During the {t['incident_date']} observation, the witness token was checked after the latch cycle; the note describes an observation sequence rather than the release prerequisite.",
        ),
        subset_id="ordinary_window",
    )

    t = topics["quillmark"]
    add_claim(
        claims,
        family_id="F02",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text=f"The Quillmark ledger keeps scan history on file for {t['current_days']} days.",
        evidence_rows=[
            evidence(
                "faq",
                "f02-history",
                f"Scan histories are retained in the Quillmark register for {t['current_days']} days after closure.",
                rationale="The FAQ uses retention language rather than the claim's keep-on-file wording, but states the same duration.",
            )
        ],
        negative=hard_negative(
            "incident",
            "f02-history-near",
            f"The supplier note describes a {t['near_days']}-day local display cache for Quillmark scans, not the retained register history.",
        ),
        subset_id="ordinary_window",
    )
    add_claim(
        claims,
        family_id="F02",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text=f"A reviewer must perform the Quillmark second look within {t['current_minutes']} minutes.",
        evidence_rows=[
            evidence(
                "support",
                "f02-second-look",
                f"The second-look interval for a Quillmark seal is {t['current_minutes']} minutes from the first reading; the reviewer enters the result in the ledger.",
                rationale="Second look and recheck are paraphrases for the same review action and interval.",
            )
        ],
        negative=hard_negative(
            "current",
            "f02-second-look-near",
            f"The primary reading may be opened after {t['near_minutes']} minutes; that opening window is not the second-look interval.",
        ),
        subset_id="ordinary_window",
    )
    add_claim(
        claims,
        family_id="F02",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text="A broken Quillmark seal triggers a fresh package identifier.",
        evidence_rows=[
            evidence(
                "current",
                "f02-identity",
                "A broken seal triggers a fresh identity token for the package; the prior token is not reused.",
                rationale="Fresh identity token is the document's paraphrase of a regenerated package identifier.",
            )
        ],
        negative=hard_negative(
            "support",
            "f02-identity-near",
            "A readable seal keeps the existing package identity during a routine second look; this does not govern a broken seal.",
        ),
        subset_id="ordinary_window",
    )
    add_claim(
        claims,
        family_id="F02",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text="Offline Quillmark viewing is allowed only after the local mirror is synchronized.",
        evidence_rows=[
            evidence(
                "record",
                "f02-offline",
                "Offline viewing is permitted after the local mirror reports synchronization; unsynchronized mirrors remain read-blocked.",
                rationale="The meeting record expresses the synchronization prerequisite with different terminology.",
            )
        ],
        negative=hard_negative(
            "faq",
            "f02-offline-near",
            "A local draft can be viewed while synchronization is pending, but it is not an approved offline ledger mirror.",
        ),
        subset_id="full",
    )

    t = topics["cinderwell"]
    f03_parts = [
        f"The {t['system']} blocks reuse after a failed seal check",
        "a passed check does not by itself release a quarantined tray",
    ]
    add_claim(
        claims,
        family_id="F03",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text=f"{f03_parts[0]}, and {f03_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f03-reuse",
                f"The Cinderwell gate blocks reuse after a failed seal check; a passed check alone does not release a tray already marked quarantined.",
                "decisive_exception",
                rationale="The paragraph preserves the failure condition and the exception to simple pass-based release.",
            )
        ],
        negative=hard_negative(
            "support",
            "f03-reuse-near",
            "The training card says a passed seal check permits reuse; it is describing an unquarantined tray and omits the failed-check state.",
        ),
        subset_id="distractor_heavy",
        decomp_parts=f03_parts,
    )
    f03_parts = [
        f"The {t['system']} refuses a remote override when the witness token is absent",
        "it permits local review without that token",
    ]
    add_claim(
        claims,
        family_id="F03",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text=f"{f03_parts[0]}, and {f03_parts[1]}.",
        evidence_rows=[
            evidence(
                "incident",
                "f03-override",
                f"The remote override was refused when the witness token was absent, while local review remained available without that token.",
                "decisive_contradiction",
                rationale="The incident distinguishes the two polarity paths instead of treating token absence as a universal block.",
            )
        ],
        negative=hard_negative(
            "faq",
            "f03-override-near",
            "The FAQ states that a witness token permits an override; it does not say that token absence blocks local review.",
        ),
        subset_id="distractor_heavy",
        decomp_parts=f03_parts,
    )
    f03_parts = [
        "The Cinderwell ledger does not erase a rejected record",
        "it does not mark that record as released",
    ]
    add_claim(
        claims,
        family_id="F03",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text=f"{f03_parts[0]}, and {f03_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f03-record",
                "A rejected Cinderwell record remains visible and is not given a released state by the ledger.",
                "decisive_exception",
                rationale="The evidence covers both negative actions: no erasure and no release marking.",
            )
        ],
        negative=hard_negative(
            "record",
            "f03-record-near",
            "A training record may be archived after correction; that administrative archive is not erasure of a rejected production record.",
        ),
        subset_id="distractor_heavy",
        decomp_parts=f03_parts,
    )
    f03_parts = [
        "A Cinderwell tamper alert prevents automatic release",
        "the alert is cleared only after a supervisor acknowledgement",
    ]
    add_claim(
        claims,
        family_id="F03",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text=f"{f03_parts[0]}, and {f03_parts[1]}.",
        evidence_rows=[
            evidence(
                "support",
                "f03-tamper",
                "A tamper alert prevents automatic release and is cleared only after supervisor acknowledgement is recorded.",
                "decisive_exception",
                rationale="The qualifier only after makes acknowledgement a necessary release condition.",
            )
        ],
        negative=hard_negative(
            "incident",
            "f03-tamper-near",
            "A sensor alert was cleared by a technician during a diagnostic run; the note does not authorize clearing a release-blocking tamper alert.",
        ),
        subset_id="distractor_heavy",
        decomp_parts=f03_parts,
    )

    t = topics["larkspur"]
    f04_parts = [
        f"The {t['system']} release temperature remains at or below {t['threshold']} degrees C",
        f"it may not exceed that value during the {t['current_minutes']}-minute hold",
    ]
    add_claim(
        claims,
        family_id="F04",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text=f"{f04_parts[0]}, and {f04_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f04-temperature",
                f"The release temperature for {t['system']} is at or below {t['threshold']} degrees C throughout the {t['current_minutes']}-minute hold; any reading above {t['threshold']} stops release.",
                "decisive_qualifier",
                rationale="The exact threshold and the throughout-the-hold qualifier are both decisive.",
            )
        ],
        negative=hard_negative(
            "support",
            "f04-temperature-near",
            f"The adjacent thermal cabinet specification uses {t['near_threshold']} degrees C as its advisory alert; the advisory number is not the Larkspur release limit.",
        ),
        subset_id="distractor_heavy",
        decomp_parts=f04_parts,
    )
    f04_parts = [
        f"The validated Larkspur recovery yield is at least {t['yield_pct']} percent",
        f"the review sample contains {t['sample_count']} units",
    ]
    add_claim(
        claims,
        family_id="F04",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text=f"{f04_parts[0]}, and {f04_parts[1]}.",
        evidence_rows=[
            evidence(
                "incident",
                "f04-yield",
                f"The validation run accepted the Larkspur recovery at {t['yield_pct']} percent or better using a review sample of {t['sample_count']} units.",
                "decisive_qualifier",
                rationale="The report binds the percentage threshold to the stated sample size.",
            )
        ],
        negative=hard_negative(
            "faq",
            "f04-yield-near",
            f"The supplier card cites a {t['near_yield_pct']} percent planning yield; it is a forecast and uses no review sample.",
        ),
        subset_id="distractor_heavy",
        decomp_parts=f04_parts,
    )
    f04_parts = [
        f"The Larkspur calibration interval is {t['current_days']} days",
        f"it is not the {t['near_days']}-day reminder interval",
    ]
    add_claim(
        claims,
        family_id="F04",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text=f"{f04_parts[0]}, and {f04_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f04-calibration",
                f"Larkspur calibration is due every {t['current_days']} days; the {t['near_days']}-day reminder is an early notification and does not change the interval.",
                "decisive_qualifier",
                rationale="The evidence separates the required interval from a near-match reminder number.",
            )
        ],
        negative=hard_negative(
            "record",
            "f04-calibration-near",
            f"The meeting note records a {t['near_days']}-day planning cadence for staffing; planning cadence is not calibration interval.",
        ),
        subset_id="distractor_heavy",
        decomp_parts=f04_parts,
    )
    f04_parts = [
        f"The Larkspur label scan tolerance is plus or minus {t['drift_limit']} millimetres",
        "a lot is rejected outside that band",
    ]
    add_claim(
        claims,
        family_id="F04",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text=f"{f04_parts[0]}, and {f04_parts[1]}.",
        evidence_rows=[
            evidence(
                "support",
                "f04-tolerance",
                f"The label scan tolerance is plus or minus {t['drift_limit']} millimetres; a lot outside the band is rejected pending review.",
                "decisive_qualifier",
                rationale="The numeric band and the outside-the-band consequence form one acceptance rule.",
            )
        ],
        negative=hard_negative(
            "current",
            "f04-tolerance-near",
            f"A {t['near_threshold']}-millimetre engineering alert is logged for setup drift; it is not the Larkspur label acceptance band.",
        ),
        subset_id="distractor_heavy",
        decomp_parts=f04_parts,
    )

    t = topics["amberbraid"]
    f05_parts = [
        f"As of {t['as_of']}, revision 3.0 of the {t['system']} is in force",
        "the proposal in revision 4.0 is not effective",
    ]
    add_claim(
        claims,
        family_id="F05",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text=f"{f05_parts[0]}, while {f05_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f05-current",
                f"Revision 3.0 of the {t['system']} took effect on {t['current_effective']} and is the operating revision as of {t['as_of']}.",
                "decisive_support",
                rationale="The current revision's effective date and in-force state answer the time-bounded claim.",
            ),
            evidence(
                "draft",
                "f05-draft",
                f"Revision 4.0 is a proposal dated {t['review_date']}; it has no effective date and is not an operating instruction.",
                "decisive_qualifier",
                rationale="The draft status qualifies why the newer numbered document does not control.",
            ),
        ],
        negative=hard_negative(
            "faq",
            "f05-current-near",
            "The FAQ says that a higher revision number should be requested during review; it does not say that an un-effective proposal controls operations.",
        ),
        subset_id="full",
        decomp_parts=f05_parts,
    )
    f05_parts = [
        f"The in-force Amberbraid hold interval is {t['current_hours']} hours",
        f"it is not the {t['old_hours']}-hour interval in revision 2.0",
    ]
    add_claim(
        claims,
        family_id="F05",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text=f"{f05_parts[0]}, rather than {f05_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f05-interval-current",
                f"Revision 3.0 sets the Amberbraid receiving hold at {t['current_hours']} hours.",
                "decisive_support",
                rationale="The current revision supplies the in-force value.",
            ),
            evidence(
                "prior",
                "f05-interval-prior",
                f"Revision 2.0 used a {t['old_hours']}-hour receiving hold and is marked superseded by revision 3.0.",
                "material_context",
                decisive=False,
                rationale="The older value is useful context and a near-match, but its superseded status prevents it from answering the current-state question.",
            ),
        ],
        negative=hard_negative(
            "faq",
            "f05-interval-near",
            f"The FAQ repeats the historical {t['old_hours']}-hour interval as a training example and points readers to the current revision for live work.",
        ),
        subset_id="stale_only",
        decomp_parts=f05_parts,
    )
    f05_parts = [
        f"The draft Amberbraid receiving instruction cannot be used for release",
        f"it is scheduled for review after {t['future_effective']}",
    ]
    add_claim(
        claims,
        family_id="F05",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text=f"{f05_parts[0]} until {f05_parts[1]}.",
        evidence_rows=[
            evidence(
                "draft",
                "f05-future-draft",
                f"The draft receiving instruction is not for release use and is planned for review after {t['future_effective']}.",
                "decisive_exception",
                rationale="The draft's non-use rule and future review date make the temporal boundary explicit.",
            )
        ],
        negative=hard_negative(
            "prior",
            "f05-future-near",
            f"Revision 2.0 is a superseded instruction with an effective date of {t['prior_effective']}; it is not the future review date for the draft.",
        ),
        subset_id="full",
        decomp_parts=f05_parts,
    )
    f05_parts = [
        "A superseded Amberbraid revision remains historical context",
        "it does not authorize today's receiving operation",
    ]
    add_claim(
        claims,
        family_id="F05",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text=f"{f05_parts[0]}, but {f05_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f05-history",
                "The current receiving SOP may cite a superseded revision for history, but only the current effective revision authorizes today's operation.",
                "decisive_exception",
                rationale="The evidence distinguishes historical reference from operating authority.",
            ),
            evidence(
                "prior",
                "f05-history-prior",
                f"Revision 2.0 is retained for historical traceability and is marked superseded as of {t['current_effective']}.",
                "material_context",
                decisive=False,
                rationale="The prior record establishes the historical-context half without authorizing present work.",
            ),
        ],
        negative=hard_negative(
            "faq",
            "f05-history-near",
            "The FAQ recommends reading old revisions during training; the recommendation does not grant those revisions operating authority.",
        ),
        subset_id="full",
        decomp_parts=f05_parts,
    )

    t = topics["micaarray"]
    f06_parts = [
        f"The {t['system']} may enter release review only when the witness scan is complete",
        f"the second sample {t['second_sample']} is logged",
    ]
    add_claim(
        claims,
        family_id="F06",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text=f"{f06_parts[0]} and {f06_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f06-review-gate",
                f"Release review for {t['system']} opens only when the witness scan is complete and sample {t['second_sample']} is logged.",
                "decisive_exception",
                rationale="Only when makes both prerequisites necessary.",
            )
        ],
        negative=hard_negative(
            "faq",
            "f06-review-gate-near",
            "The quick guide says a completed witness scan starts preparation; it omits the second-sample prerequisite for release review.",
        ),
        subset_id="ordinary_window",
        decomp_parts=f06_parts,
    )
    f06_parts = [
        f"The Mica sensor array is exempt from the extended hold only for {t['scope']}",
        "all other lots retain the full hold",
    ]
    add_claim(
        claims,
        family_id="F06",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text=f"{f06_parts[0]}, and {f06_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f06-exemption",
                f"Only {t['scope']} may use the short Mica hold; all other lots retain the extended hold.",
                "decisive_exception",
                rationale="The exception is explicitly scoped and the default is preserved for all other lots.",
            )
        ],
        negative=hard_negative(
            "support",
            "f06-exemption-near",
            "A planning note calls every Mica lot a candidate for a short hold; candidate status is not an approved exemption.",
        ),
        subset_id="ordinary_window",
        decomp_parts=f06_parts,
    )
    f06_parts = [
        f"The Mica alarm bypass is permitted if and only if {t['condition_text']}",
        f"it expires after {t['temporary_window']} minutes",
    ]
    add_claim(
        claims,
        family_id="F06",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text=f"{f06_parts[0]}, and {f06_parts[1]}.",
        evidence_rows=[
            evidence(
                "incident",
                "f06-bypass",
                f"An alarm bypass is permitted if and only if {t['condition_text']}; the bypass expires after {t['temporary_window']} minutes.",
                "decisive_qualifier",
                rationale="If and only if and the expiry window are both material qualifiers.",
            )
        ],
        negative=hard_negative(
            "faq",
            "f06-bypass-near",
            "The FAQ says a bypass can be requested during maintenance; it does not state the prerequisite or the expiry window.",
        ),
        subset_id="full",
        decomp_parts=f06_parts,
    )
    f06_parts = [
        f"The Mica procedure applies to {t['scope']} unless the tamper flag is raised",
        "the exception requires a deviation record",
    ]
    add_claim(
        claims,
        family_id="F06",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text=f"{f06_parts[0]}, and {f06_parts[1]}.",
        evidence_rows=[
            evidence(
                "faq",
                "f06-scope",
                f"The procedure covers {t['scope']} unless the tamper flag is raised; that exception requires a deviation record.",
                "decisive_exception",
                rationale="The scope restriction and exception record requirement are stated together.",
            )
        ],
        negative=hard_negative(
            "record",
            "f06-scope-near",
            "The decision record discusses a tamper flag on a test fixture and does not change the Mica production procedure.",
        ),
        subset_id="full",
        decomp_parts=f06_parts,
    )

    t = topics["blueglass"]
    add_claim(
        claims,
        family_id="F07",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text="The Blueglass spool may be accepted only after its lot pedigree is reconciled.",
        evidence_rows=[
            evidence(
                "support",
                "f07-pedigree",
                "The receiving cell admits a Blueglass spool only after the chain-of-custody ledger has been reconciled to the supplier lot.",
                "decisive_exception",
                rationale="Chain-of-custody ledger is the source terminology for the claim's lot pedigree.",
            )
        ],
        negative=hard_negative(
            "current",
            "f07-pedigree-near",
            "The receiving SOP requires a package count before opening; package count does not establish lot pedigree.",
        ),
        subset_id="distractor_heavy",
    )
    add_claim(
        claims,
        family_id="F07",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text="A missing Blueglass spool certificate blocks receipt even when the packaging is undamaged.",
        evidence_rows=[
            evidence(
                "incident",
                "f07-certificate",
                "A Blueglass spool with undamaged packaging was held at receipt because its certificate was missing; packaging condition did not waive the certificate check.",
                "decisive_contradiction",
                rationale="The incident directly defeats the tempting packaging-based acceptance shortcut.",
            )
        ],
        negative=hard_negative(
            "support",
            "f07-certificate-near",
            "A supplier bulletin says intact packaging reduces visual inspection time; it does not waive the certificate check.",
        ),
        subset_id="distractor_heavy",
    )
    add_claim(
        claims,
        family_id="F07",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text=f"The {t['system']} sends incoming material to the segregation bay before inspection.",
        evidence_rows=[
            evidence(
                "current",
                "f07-segregation",
                f"Incoming {t['product']} is routed to the segregation bay before any acceptance inspection begins.",
                "decisive_support",
                rationale="Segregation bay is the source's less obvious term for the claim's quarantine destination.",
            )
        ],
        negative=hard_negative(
            "incident",
            "f07-segregation-near",
            "A resolved receipt incident mentions a quarantine shelf after inspection; the sequence is opposite to the incoming-material rule.",
        ),
        subset_id="distractor_heavy",
    )
    add_claim(
        claims,
        family_id="F07",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text="The Blueglass supplier change notice is advisory and cannot change the local acceptance limit.",
        evidence_rows=[
            evidence(
                "record",
                "f07-change",
                "Supplier change notices are advisory inputs; the local acceptance limit remains unchanged until a local change record is approved.",
                "decisive_exception",
                rationale="The decision record distinguishes an advisory supplier notice from an approved local limit change.",
            )
        ],
        negative=hard_negative(
            "incident",
            "f07-change-near",
            "A supplier bulletin proposes a new material grade; the bulletin is not a local acceptance authorization.",
        ),
        subset_id="distractor_heavy",
    )

    t = topics["vellumcal"]
    f08_fact = f"The Vellum reference plate must equilibrate for {t['rest_hours']} hours before use."
    add_claim(
        claims,
        family_id="F08",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text=f08_fact,
        evidence_rows=[
            evidence(
                "current",
                "f08-rest-current",
                f"The {t['product']} reference plate rests for {t['rest_hours']} hours before the Vellum bench may use it.",
                rationale="Current SOP wording states the equilibration requirement.",
            ),
            evidence(
                "faq",
                "f08-rest-faq",
                f"Before a Vellum run, let the reference plate settle for {t['rest_hours']} hours.",
                rationale="The FAQ paraphrases the same timing rule; it is duplicate coverage rather than an independent control.",
            ),
            evidence(
                "record",
                "f08-rest-record",
                f"The calibration meeting repeated the {t['rest_hours']}-hour reference-plate rest as the standing bench practice.",
                "material_context",
                decisive=False,
                rationale="The meeting record repeats the fact but does not independently establish the SOP requirement.",
            ),
        ],
        negative=hard_negative(
            "incident",
            "f08-rest-near",
            f"A diagnostic run used a {max(1, t['rest_hours'] - 1)}-hour wait while troubleshooting; the diagnostic wait is not the standing reference-plate rule.",
        ),
        subset_id="full",
    )
    f08_fact = f"Vellum calibration results expire after {t['current_days']} days unless the instrument remains sealed."
    add_claim(
        claims,
        family_id="F08",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text=f08_fact,
        evidence_rows=[
            evidence(
                "current",
                "f08-expiry-current",
                f"Vellum calibration results expire after {t['current_days']} days unless the bench instrument remains sealed.",
                rationale="Current SOP wording gives the expiry and the seal exception.",
            ),
            evidence(
                "faq",
                "f08-expiry-faq",
                f"Keep the instrument sealed to preserve a Vellum result for {t['current_days']} days.",
                "material_context",
                decisive=False,
                rationale="The FAQ paraphrase repeats the same fact without adding independent authority.",
            ),
        ],
        negative=hard_negative(
            "support",
            "f08-expiry-near",
            f"The policy's {t['near_days']}-day reminder is sent before calibration expiry; it is not the result lifetime.",
        ),
        subset_id="full",
    )
    add_claim(
        claims,
        family_id="F08",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text="The second Vellum calibration check confirms a result but is not an independent release authorization.",
        evidence_rows=[
            evidence(
                "current",
                "f08-confirm-current",
                "The second Vellum calibration check confirms the recorded result; it does not independently authorize release.",
                "decisive_qualifier",
                rationale="The current SOP defines the second check's limited role.",
            ),
            evidence(
                "record",
                "f08-confirm-record",
                "The bench decision record describes the second check as confirmation rather than a second release decision.",
                "material_context",
                decisive=False,
                rationale="The record repeats the distinction but is not an independent release authorization.",
            ),
        ],
        negative=hard_negative(
            "faq",
            "f08-confirm-near",
            "The FAQ calls the second check an additional assurance step; assurance language does not grant release authority.",
        ),
        subset_id="full",
    )
    add_claim(
        claims,
        family_id="F08",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text=f"The same plus or minus {t['drift_limit']}-millimetre drift limit appears in the Vellum SOP and technician FAQ.",
        evidence_rows=[
            evidence(
                "current",
                "f08-drift-current",
                f"The Vellum SOP records a plus or minus {t['drift_limit']}-millimetre drift limit for the reference plate.",
                rationale="The SOP supplies the exact drift limit.",
            ),
            evidence(
                "faq",
                "f08-drift-faq",
                f"The technician FAQ repeats the plus or minus {t['drift_limit']}-millimetre drift limit.",
                "material_context",
                decisive=False,
                rationale="The FAQ is a paraphrased repetition, not a second independent measurement.",
            ),
        ],
        negative=hard_negative(
            "incident",
            "f08-drift-near",
            f"A diagnostic note records a {t['near_threshold']}-unit alert for a different sensor; it is not the Vellum reference-plate drift limit.",
        ),
        subset_id="full",
    )

    t = topics["brambleline"]
    long_parts = [
        f"The {t['system']} line-clearance check requires {t['zone_count']} visual zones",
        "the batch cannot move until every zone is recorded",
    ]
    add_claim(
        claims,
        family_id="F09",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text=f"{long_parts[0]}, and {long_parts[1]}.",
        evidence_rows=[
            evidence(
                "guide",
                "f09-zones",
                f"The clearance review counts {t['zone_count']} visual zones for {t['system']}; the batch cannot move until every zone is recorded.",
                "decisive_support",
                rationale="The decisive zone count is intentionally placed in the long guidance document's buried procedure section.",
            )
        ],
        negative=hard_negative(
            "current",
            "f09-zones-near",
            f"The short SOP checklist displays {max(1, t['zone_count'] - 1)} zones on its training card; the guidance document governs the full clearance count.",
        ),
        subset_id="full",
        decomp_parts=long_parts,
    )
    long_parts = [
        "The first Bramble clearance photo is taken before the tool cart enters the bay",
        "it is not taken after entry",
    ]
    add_claim(
        claims,
        family_id="F09",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text=f"{long_parts[0]}, and {long_parts[1]}.",
        evidence_rows=[
            evidence(
                "guide",
                "f09-photo",
                "The first clearance photo is captured before the tool cart enters the bay; a photo taken after entry cannot serve as the first-clearance record.",
                "decisive_contradiction",
                rationale="The buried procedure step fixes the order and rejects the near-match sequence.",
            )
        ],
        negative=hard_negative(
            "incident",
            "f09-photo-near",
            "An incident photograph was taken after cart entry for investigation; investigation timing is not the first-clearance step.",
        ),
        subset_id="full",
        decomp_parts=long_parts,
    )
    long_parts = [
        f"A temporary Bramble clearance waiver lasts {t['temporary_window']} hours",
        "it must be countersigned before the line starts",
    ]
    add_claim(
        claims,
        family_id="F09",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text=f"{long_parts[0]}, and {long_parts[1]}.",
        evidence_rows=[
            evidence(
                "guide",
                "f09-waiver",
                f"A temporary clearance waiver lasts {t['temporary_window']} hours and must be countersigned before the line starts.",
                "decisive_qualifier",
                rationale="The duration and countersignature prerequisite are buried in separate sentences of the same procedure section.",
            )
        ],
        negative=hard_negative(
            "faq",
            "f09-waiver-near",
            f"The FAQ describes a {t['temporary_window'] + 1}-hour planning hold for staffing; planning hold and clearance waiver are different controls.",
        ),
        subset_id="full",
        decomp_parts=long_parts,
    )
    long_parts = [
        f"The Bramble clearance record is archived under the batch key for {t['archive_days']} days",
        "it is not filed under the tool-cart identifier",
    ]
    add_claim(
        claims,
        family_id="F09",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text=f"{long_parts[0]}, and {long_parts[1]}.",
        evidence_rows=[
            evidence(
                "guide",
                "f09-archive",
                f"Clearance records are archived under the batch key for {t['archive_days']} days; the tool-cart identifier is only a cross-reference.",
                "decisive_qualifier",
                rationale="The deep archive paragraph distinguishes primary filing key from cross-reference.",
            )
        ],
        negative=hard_negative(
            "record",
            "f09-archive-near",
            "The meeting record lists tool-cart identifiers for attendance tracking; attendance tracking is not the archive key.",
        ),
        subset_id="full",
        decomp_parts=long_parts,
    )

    t = topics["morrowquay"]
    f10_parts = [
        f"The {t['system']} quarantine release requires a temperature check below {t['threshold']} degrees C",
        "a signed identity match is required before movement",
    ]
    add_claim(
        claims,
        family_id="F10",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text=f"{f10_parts[0]}, and {f10_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f10-temp",
                f"Quarantine release begins with a Morrow temperature check below {t['threshold']} degrees C.",
                rationale="The SOP supplies the temperature half of the composed release rule.",
                jointly_required=True,
                joint_group_id="f10-release-01",
            ),
            evidence(
                "support",
                "f10-identity",
                "Movement is permitted only after the lot identity is matched and signed by the assigned reviewer.",
                "decisive_qualifier",
                rationale="The technical specification supplies the identity-signature half; both passages are required.",
                jointly_required=True,
                joint_group_id="f10-release-01",
            ),
        ],
        negative=hard_negative(
            "faq",
            "f10-release-near",
            f"The Morrow FAQ describes a {t['near_threshold']}-degree storage alert and a visual label check; neither completes the release composition.",
        ),
        subset_id="full",
        decomp_parts=f10_parts,
    )
    f10_parts = [
        "The Morrow quarantine clock begins at sample receipt",
        f"the escalation notice is sent after {t['current_hours']} hours",
    ]
    add_claim(
        claims,
        family_id="F10",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text=f"{f10_parts[0]}, and {f10_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f10-clock",
                "The quarantine clock starts when the sample is received into the rack.",
                rationale="The SOP supplies the clock start event.",
                jointly_required=True,
                joint_group_id="f10-clock-02",
            ),
            evidence(
                "incident",
                "f10-escalation",
                f"The escalation notice is sent after {t['current_hours']} hours on the quarantine clock.",
                "decisive_qualifier",
                rationale="The meeting record supplies the elapsed-time action; both passages are required.",
                jointly_required=True,
                joint_group_id="f10-clock-02",
            ),
        ],
        negative=hard_negative(
            "record",
            "f10-clock-near",
            f"The rack review note uses a {t['near_hours']}-hour planning reminder from shift start; it is not the sample-receipt clock.",
        ),
        subset_id="full",
        decomp_parts=f10_parts,
    )
    f10_parts = [
        f"The Morrow lot may be released only by {t['owner']}",
        f"the archive entry must carry {t['handoff_code']}",
    ]
    add_claim(
        claims,
        family_id="F10",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text=f"{f10_parts[0]}, and {f10_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f10-owner",
                f"Only {t['owner']} may release a Morrow lot from quarantine.",
                "decisive_qualifier",
                rationale="The SOP supplies the restricted release owner.",
                jointly_required=True,
                joint_group_id="f10-owner-03",
            ),
            evidence(
                "record",
                "f10-archive-code",
                f"The archive entry for a released Morrow lot carries handoff code {t['handoff_code']}.",
                rationale="The decision record supplies the required archive code; both passages are required.",
                jointly_required=True,
                joint_group_id="f10-owner-03",
            ),
        ],
        negative=hard_negative(
            "faq",
            "f10-owner-near",
            "The FAQ allows any trained operator to request review; requesting review is not releasing a quarantined lot.",
        ),
        subset_id="full",
        decomp_parts=f10_parts,
    )
    f10_parts = [
        "If the first Morrow check fails, the lot remains segregated",
        "only a completed second check can reopen review",
    ]
    add_claim(
        claims,
        family_id="F10",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text=f"{f10_parts[0]}, and {f10_parts[1]}.",
        evidence_rows=[
            evidence(
                "incident",
                "f10-failure",
                "A failed first check leaves the Morrow lot segregated pending follow-up.",
                "decisive_exception",
                rationale="The incident supplies the failure-state half.",
                jointly_required=True,
                joint_group_id="f10-failure-04",
            ),
            evidence(
                "current",
                "f10-second-check",
                "The review gate reopens only after a completed second check is recorded.",
                "decisive_qualifier",
                rationale="The SOP supplies the reopening prerequisite; both passages are required.",
                jointly_required=True,
                joint_group_id="f10-failure-04",
            ),
        ],
        negative=hard_negative(
            "support",
            "f10-failure-near",
            "The technical note permits a repeat measurement during troubleshooting; a repeat measurement is not a completed second release check.",
        ),
        subset_id="full",
        decomp_parts=f10_parts,
    )

    t = topics["oriolegate"]
    no_answer_claims = [
        (
            "The Oriole batch gate permits remote release after 22:00.",
            "f11-after-hours",
            "The Oriole after-hours card records a review request and a badge check, but it does not state whether remote release is permitted.",
        ),
        (
            "The Oriole gate automatically approves a batch when the witness token is missing.",
            "f11-missing-token",
            "The Oriole guide discusses a missing witness token during preparation; it does not state an automatic approval behavior.",
        ),
        (
            "Oriole release records are retained for exactly 11 years.",
            "f11-eleven-years",
            "The Oriole record note mentions a long retention review without naming an 11-year period.",
        ),
        (
            "An Oriole lot may be accepted without the second sample.",
            "f11-no-second-sample",
            "The Oriole sampling card describes the second sample but does not state whether acceptance without it is allowed.",
        ),
        (
            "The Oriole supplier is rated at tier 7.",
            "f11-tier-seven",
            "The supplier article lists a routine supplier review and a lot code, but no tier-7 rating.",
        ),
        (
            "The Oriole emergency path bypasses review entirely.",
            "f11-bypass",
            "The emergency article describes an escalation path and does not say whether review is bypassed.",
        ),
        (
            "Oriole package labels are required to be blue.",
            "f11-blue-label",
            "The label note refers to readable package markings and does not specify a blue color requirement.",
        ),
        (
            "The Oriole archive relay supports mobile offline signing.",
            "f11-mobile-signing",
            "The archive note mentions a mobile viewing request but does not state that offline signing is supported.",
        ),
    ]
    for local_index, (claim_text, anchor, negative_text) in enumerate(no_answer_claims, start=1):
        add_claim(
            claims,
            family_id="F11",
            local_index=local_index,
            topic_slug=t["slug"],
            original_claim_text=claim_text,
            evidence_rows=[],
            negative=hard_negative("faq", anchor, negative_text),
            answerable=False,
            subset_id="ordinary_window",
        )

    t = topics["wickarchive"]
    f12_parts = [
        f"The {t['system']} disables a badge after {t['failed_attempts']} failed attempts",
        f"the lockout lasts {t['session_minutes']} minutes",
    ]
    add_claim(
        claims,
        family_id="F12",
        local_index=1,
        topic_slug=t["slug"],
        original_claim_text=f"{f12_parts[0]}, and {f12_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f12-lockout",
                f"The Wick gateway disables a badge after {t['failed_attempts']} failed attempts and holds the lockout for {t['session_minutes']} minutes.",
                "decisive_support",
                rationale="The current access SOP contains the decisive lockout settings but is outside this case's searchable aperture.",
            )
        ],
        negative=hard_negative(
            "support",
            "f12-lockout-near",
            f"The gateway training card warns after {t['failed_attempts'] - 1} failed attempts and displays a {t['session_minutes'] + 5}-minute reminder; neither is the enforced lockout rule.",
        ),
        subset_id="bounded_missing_decisive",
        decomp_parts=f12_parts,
    )
    f12_parts = [
        f"The Wick archive export may be run only from {t['facility']}",
        "the export records the operator token",
    ]
    add_claim(
        claims,
        family_id="F12",
        local_index=2,
        topic_slug=t["slug"],
        original_claim_text=f"{f12_parts[0]}, and {f12_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f12-export",
                f"Archive export is permitted only from {t['facility']}; the export record includes the operator token.",
                "decisive_qualifier",
                rationale="The full corpus contains the location restriction and token-recording rule; the current document is omitted from the case aperture.",
            )
        ],
        negative=hard_negative(
            "faq",
            "f12-export-near",
            "The archive FAQ permits a preview from any workstation but says nothing about executing an export or recording the operator token.",
        ),
        subset_id="bounded_missing_decisive",
        decomp_parts=f12_parts,
    )
    f12_parts = [
        f"The Wick session key rotates every {t['session_minutes']} minutes",
        "it does not rotate during an active maintenance exemption",
    ]
    add_claim(
        claims,
        family_id="F12",
        local_index=3,
        topic_slug=t["slug"],
        original_claim_text=f"{f12_parts[0]}, unless {f12_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f12-rotation",
                f"The Wick gateway rotates its session key every {t['session_minutes']} minutes unless a maintenance exemption is active.",
                "decisive_exception",
                rationale="The full-corpus current SOP contains the interval and exception; the source is intentionally absent from the searchable subset.",
            )
        ],
        negative=hard_negative(
            "incident",
            "f12-rotation-near",
            f"A maintenance note records a {t['session_minutes'] + 3}-minute troubleshooting timer; it does not define session-key rotation.",
        ),
        subset_id="bounded_missing_decisive",
        decomp_parts=f12_parts,
    )
    f12_parts = [
        f"The Wick audit snapshot is retained for {t['archive_days']} days",
        "it is not copied to personal storage",
    ]
    add_claim(
        claims,
        family_id="F12",
        local_index=4,
        topic_slug=t["slug"],
        original_claim_text=f"{f12_parts[0]}, and {f12_parts[1]}.",
        evidence_rows=[
            evidence(
                "current",
                "f12-retention",
                f"Wick audit snapshots remain in the controlled archive for {t['archive_days']} days and are not copied to personal storage.",
                "decisive_exception",
                rationale="The full-corpus current policy contains both retention and prohibited-copy conditions; the policy is outside the aperture.",
            )
        ],
        negative=hard_negative(
            "record",
            "f12-retention-near",
            f"The archive meeting note uses a {t['archive_days'] + 5}-day working-copy reminder and does not govern personal-storage handling.",
        ),
        subset_id="bounded_missing_decisive",
        decomp_parts=f12_parts,
    )

    return claims


def human_doc_type(document_type: str) -> str:
    return document_type.replace("_", " ")


def role_metadata(
    *,
    family_id: str,
    role: str,
    topic: dict[str, Any],
    as_of: date,
) -> dict[str, Any]:
    if family_id == "F05" and role == "current":
        version = "3.0"
        status = "current"
        effective_date = topic["current_effective"]
        publication_date = topic["current_effective"]
    elif family_id == "F05" and role == "prior":
        version = "2.0"
        status = "superseded"
        effective_date = topic["prior_effective"]
        publication_date = topic["prior_effective"]
    elif family_id == "F05" and role == "draft":
        version = "4.0"
        status = "draft"
        effective_date = None
        publication_date = topic["review_date"]
    else:
        version = "1.0"
        status = "current" if role in {"current", "support", "faq", "guide"} else "final"
        effective_date = topic["current_effective"] if role in {"current", "support", "faq", "guide"} else None
        publication_date = topic["current_effective"] if role == "current" else (
            as_of - timedelta(days=14 + len(role) * 3)
        ).isoformat()
    return {
        "version": version,
        "status": status,
        "effective_date": effective_date,
        "publication_date": publication_date,
    }


def generic_paragraphs(
    *,
    family_id: str,
    role: str,
    document_type: str,
    topic: dict[str, Any],
    rng: random.Random,
) -> list[str]:
    label = human_doc_type(document_type)
    subject = topic["display"]
    common = [
        f"Purpose. This {label} defines the internal control for {subject} at {topic['facility']}. It is limited to the named asset and is not a universal rule.",
        f"Scope. The control applies to {topic['scope']}; unrelated assets use their own controlled instructions.",
        f"Ownership. {topic['owner']} owns the operational decision, while {topic['reviewer']} performs the independent review.",
        f"Identification. Asset {topic['asset_code']}, product {topic['product']}, and record series {topic['record_code']} are used to keep the local records distinct.",
        f"Routine. The {topic['operator_group']} checks the visible condition, records the observation, and routes exceptions to {topic['reviewer']}.",
        f"Records. Entries are made in the controlled register using lot reference {topic['lot_code']}; free-form personal copies are not the official record.",
        f"Training. A trained operator may perform the routine step only after the local work instruction has been read and acknowledged.",
        f"Deviation. A result outside the stated control is held for review and is not silently corrected in the original entry.",
        f"Review. The document owner reviews this {label} on {topic['review_date']} or sooner if the asset, supplier, or record path changes.",
        f"References. Cross-references point to internal document code {topic['handoff_code']} and remain subordinate to the effective instruction.",
        f"Administrative note. The Neralis Compact keeps this synthetic record for controlled-workflow exercises; it does not assert an external regulatory obligation.",
    ]
    style_extras = {
        "sop": [
            f"Procedure. The operator confirms the asset identity, performs the named step, and records the result before moving to the next step.",
            f"Acceptance. The result is accepted only when the stated parameter, record entry, and required review are all present.",
        ],
        "policy": [
            f"Decision rule. A request is admitted only when its scope and owner are visible in the register.",
            f"Exception rule. A local exception must state its reason, duration, and approving role.",
        ],
        "technical_specification": [
            f"Design intent. The {topic['system']} separates control settings from advisory indicators so a near-match value cannot be mistaken for an acceptance limit.",
            f"Interface. The system sends a record identifier to the controlled register after the operator confirms the step.",
        ],
        "work_instruction": [
            f"Operator sequence. The operator reads the asset identifier, checks the condition, and commits the result before closing the work screen.",
            f"Operator caution. Similar-looking fields belong to different steps and must not be copied across records.",
        ],
        "deviation_report": [
            f"Event summary. A simulated observation at {topic['facility']} was recorded on {topic['incident_date']} for review.",
            f"Disposition. The event record separates what was observed from what the owner later decided.",
        ],
        "incident_report": [
            f"Event summary. A simulated incident at {topic['facility']} was opened on {topic['incident_date']} without using patient or customer data.",
            f"Containment. The affected record remains visible while the owner confirms the disposition.",
        ],
        "supplier_bulletin": [
            f"Supplier note. A simulated supplier communication concerns {topic['product']} and is advisory until the local owner evaluates it.",
            f"Local action. Supplier language does not change the local control without a separate approved record.",
        ],
        "validation_report": [
            f"Method. The simulated validation run used a defined sample and recorded each observation against {topic['record_code']}.",
            f"Conclusion. The report distinguishes measured results from the operating rule that will be used afterward.",
        ],
        "guidance_note": [
            f"Orientation. This guidance note explains why the {topic['system']} procedure is ordered as written.",
            f"Boundary. Explanatory guidance does not replace the current operating record.",
        ],
        "knowledge_base_article": [
            f"Question. What should an operator do when a familiar field does not match the local record?",
            f"Answer. Pause the transaction, preserve the visible entry, and ask {topic['reviewer']} to resolve the scope.",
        ],
        "faq": [
            f"Question. Which record is authoritative for {topic['display']}?",
            f"Answer. Use the controlled record identified by {topic['record_code']}; a reminder card is not a replacement.",
        ],
        "decision_record": [
            f"Decision. The local group retained the control after reviewing a simulated workflow at {topic['facility']}.",
            f"Rationale. The decision preserves traceability and keeps advisory notes separate from operating instructions.",
        ],
        "meeting_record": [
            f"Agenda. The group reviewed {topic['display']}, record ownership, and the handling of a near-match value.",
            f"Outcome. The meeting note records a decision or question; it does not silently amend the operating document.",
        ],
        "change_control_notice": [
            f"Change note. A proposed change to {topic['system']} is tracked under {topic['handoff_code']}.",
            f"Activation. The proposal becomes operational only after the local owner records an effective decision.",
        ],
        "background_note": [
            f"Background. The {topic['display']} developed from a local workflow need at {topic['facility']}.",
            f"Context. This note provides orientation and is not a substitute for a controlled procedure.",
        ],
    }
    extras = style_extras.get(document_type, [])
    if document_type == "guidance_note" and role == "guide":
        extras.extend(
            [
                f"Context {index}. The {topic['system']} uses a staged review sequence so operators can distinguish preparation, observation, and disposition."
                for index in range(1, 17)
            ]
        )
    if role in {"incident", "record"}:
        rng.shuffle(common)
    selected = common + extras
    if role == "faq":
        selected = selected[:8]
    elif role == "record":
        selected = selected[:9]
    elif role == "incident":
        selected = selected[:10]
    return selected


def special_header(
    *,
    family_id: str,
    role: str,
    topic: dict[str, Any],
    metadata: dict[str, Any],
) -> str:
    title = metadata["title"]
    if family_id == "F05" and role == "current":
        return f"In-force note. {title} took effect on {metadata['effective_date']} and governs the operating lane as of {topic['as_of']}."
    if family_id == "F05" and role == "prior":
        return f"Historical note. {title} was effective on {metadata['effective_date']} and remains available for traceability after supersession."
    if family_id == "F05" and role == "draft":
        return f"Proposal note. {title} has no effective date and is not an operating instruction."
    if role == "incident":
        return f"Event note. This simulated record describes an observation on {topic['incident_date']} and separates observation from disposition."
    if role == "faq":
        return f"Quick answer. The {topic['display']} questions below use plain language but defer to the controlled record for live work."
    if role == "guide":
        return f"Explanatory note. The long-form guidance for {topic['display']} preserves the reason and sequence behind the local control."
    return f"Control summary. {title} identifies the local setting, owner, and record path before describing the routine."


def render_source(
    *,
    family_id: str,
    role: str,
    document_type: str,
    topic: dict[str, Any],
    as_of: date,
    seed: int,
    special_rows: list[tuple[str, str]],
) -> dict[str, Any]:
    sid = source_id(topic["slug"], role)
    metadata_values = role_metadata(family_id=family_id, role=role, topic=topic, as_of=as_of)
    code_rng = derived_rng(seed, f"source-code:{sid}")
    doc_code = f"{topic['prefix']}-{code_rng.choice(['SOP', 'POL', 'TSP', 'REC', 'VAL'])}-{code_rng.randint(101, 899)}"
    revision_suffix = ""
    if family_id == "F05":
        revision_suffix = f" revision {metadata_values['version']}"
    title = f"{topic['display']} {human_doc_type(document_type)}{revision_suffix}"
    rng = derived_rng(seed, f"source-body:{sid}")
    paragraphs = [
        f"{title}. Document code {doc_code}. Controlled internal record for the fictional Neralis Compact.",
        special_header(family_id=family_id, role=role, topic=topic, metadata={**metadata_values, "title": title}),
    ]
    generic = generic_paragraphs(
        family_id=family_id,
        role=role,
        document_type=document_type,
        topic=topic,
        rng=rng,
    )
    if role == "guide":
        paragraphs.extend(generic)
        paragraphs.extend(text for _, text in special_rows)
    else:
        insertion = 2
        paragraphs[insertion:insertion] = [text for _, text in special_rows]
        paragraphs.extend(generic)
    if family_id == "F05" and role == "prior":
        paragraphs.insert(
            2,
            f"Supersession note. Revision {metadata_values['version']} is retained for historical traceability and is not the current operating revision.",
        )
    if family_id == "F05" and role == "draft":
        paragraphs.insert(
            2,
            f"Draft control. Revision {metadata_values['version']} is a proposal only; it cannot authorize the receiving operation before an effective decision.",
        )
    if role == "guide":
        paragraphs.append(
            f"End note. The guidance closes with a reminder to consult the effective operating record for {topic['record_code']} before action."
        )
    else:
        paragraphs.append(
            f"Closeout. The record owner signs the review outcome and preserves the source entry under {topic['record_code']}."
        )

    source_text = "\n\n".join(paragraphs) + "\n"
    encoded = source_text.encode("utf-8")
    passage_rows: list[dict[str, Any]] = []
    anchor_to_passage: dict[str, dict[str, Any]] = {}
    cursor = 0
    special_by_text: dict[str, list[str]] = defaultdict(list)
    for anchor, text in special_rows:
        special_by_text[text].append(anchor)
    for index, paragraph in enumerate(paragraphs):
        paragraph_bytes = paragraph.encode("utf-8")
        start = cursor
        end = start + len(paragraph_bytes)
        pid = passage_id_for(sid, index)
        row = {
            "passage_id": pid,
            "paragraph_index": index,
            "start_offset": start,
            "end_offset": end,
            "offset_unit": OFFSET_UNIT,
            "text_sha256": sha256_bytes(paragraph_bytes),
        }
        passage_rows.append(row)
        for anchor in special_by_text.get(paragraph, []):
            anchor_to_passage[anchor] = {
                **row,
                "text": paragraph,
            }
        cursor = end + (2 if index < len(paragraphs) - 1 else 1)
    content_hash = sha256_bytes(encoded)
    metadata = {
        "schema_version": "1.0",
        "source_id": sid,
        "source_identity_basis": "stable-semantic-document-key",
        "logical_document_key": f"{topic['slug']}::{role}",
        "title": title,
        "document_type": document_type,
        "version": metadata_values["version"],
        "publication_date": metadata_values["publication_date"],
        "effective_date": metadata_values["effective_date"],
        "status": metadata_values["status"],
        "document_code": doc_code,
        "content_path": "content.txt",
        "content_encoding": "utf-8",
        "offset_unit": OFFSET_UNIT,
        "content_hash": content_hash,
        "passage_count": len(passage_rows),
        "passages": passage_rows,
    }
    return {
        "source_id": sid,
        "family_id": family_id,
        "topic_slug": topic["slug"],
        "role": role,
        "document_type": document_type,
        "title": title,
        "content_text": source_text,
        "content_bytes": encoded,
        "metadata": metadata,
        "passage_rows": passage_rows,
        "anchor_to_passage": anchor_to_passage,
        "paragraphs": paragraphs,
    }


def build_sources(
    *,
    topics: dict[str, dict[str, Any]],
    claims: list[dict[str, Any]],
    as_of: date,
    seed: int,
) -> dict[str, dict[str, Any]]:
    special_rows: dict[tuple[str, str], OrderedDict[str, str]] = defaultdict(OrderedDict)
    for claim in claims:
        topic_slug = claim["topic_slug"]
        for row in claim["evidence"]:
            key = (topic_slug, row["role"])
            prior = special_rows[key].get(row["anchor"])
            if prior is not None and prior != row["text"]:
                raise ValueError(f"conflicting evidence anchor {key} {row['anchor']}")
            special_rows[key][row["anchor"]] = row["text"]
        negative = claim["hard_negative"]
        key = (topic_slug, negative["role"])
        prior = special_rows[key].get(negative["anchor"])
        if prior is not None and prior != negative["text"]:
            raise ValueError(f"conflicting negative anchor {key} {negative['anchor']}")
        special_rows[key][negative["anchor"]] = negative["text"]

    family_topic_slugs = [
        "rimebridge",
        "quillmark",
        "cinderwell",
        "larkspur",
        "amberbraid",
        "micaarray",
        "blueglass",
        "vellumcal",
        "brambleline",
        "morrowquay",
        "oriolegate",
        "wickarchive",
    ]
    sources: dict[str, dict[str, Any]] = {}
    for family_id, role_plan in FAMILY_PLANS.items():
        topic_slug = family_topic_slugs[int(family_id[1:]) - 1]
        topic = topics[topic_slug]
        for role, document_type in role_plan:
            sid = source_id(topic["slug"], role)
            rows = list(special_rows[(topic["slug"], role)].items())
            source = render_source(
                family_id=family_id,
                role=role,
                document_type=document_type,
                topic=topic,
                as_of=as_of,
                seed=seed,
                special_rows=rows,
            )
            if sid in sources:
                raise ValueError(f"duplicate source id: {sid}")
            sources[sid] = source
    if len(sources) != 60:
        raise ValueError(f"expected 60 sources, built {len(sources)}")
    for claim in claims:
        topic = topics[claim["topic_slug"]]
        for row in claim["evidence"] + [claim["hard_negative"]]:
            sid = source_id(topic["slug"], row["role"])
            if sid not in sources:
                raise ValueError(f"claim points to unbuilt source {sid}")
            if row["anchor"] not in sources[sid]["anchor_to_passage"]:
                raise ValueError(f"claim anchor not rendered: {sid} {row['anchor']}")
    return sources


def variant_text_from_children(children: list[dict[str, str]], original: str) -> str:
    if not children:
        return original
    return " ".join(child["text"].strip() for child in children).strip()


def drift_variant_text(original: str) -> tuple[str, str]:
    transformations = [
        ("only when ", "", "drops a prerequisite"),
        ("if and only if ", "if ", "weakens a biconditional prerequisite"),
        ("unless ", "even when ", "reverses an exception condition"),
        (" does not ", " does ", "removes a negation"),
        (" not ", " ", "removes a negation"),
        ("must ", "may ", "weakens an obligation"),
        ("at least ", "about ", "weakens a threshold"),
        ("before ", "after ", "reverses a timeframe"),
        ("only ", "", "drops a scope restriction"),
    ]
    for old, new, reason in transformations:
        if old in original:
            return original.replace(old, new, 1), reason
    return original.rstrip(".") + " regardless of the stated condition.", "adds an unlicensed unconditional proposition"


def over_decompose(parts: list[str]) -> list[str]:
    children: list[str] = []
    for part in parts:
        words = part.strip().rstrip(".").split()
        if len(words) <= 4:
            children.append(part.strip().rstrip(".") + ".")
            continue
        chunk_size = max(3, (len(words) + 2) // 3)
        for start in range(0, len(words), chunk_size):
            fragment = " ".join(words[start : start + chunk_size]).strip()
            if fragment:
                children.append(fragment + ".")
    return children


def build_decomposition_variants(claim: dict[str, Any]) -> list[dict[str, Any]]:
    if not claim["decomp_sensitive"]:
        return [
            {
                "decomposition_id": None,
                "variant_id": "A0",
                "variant_text": claim["original_claim_text"],
                "children": [],
                "variant_description": "original claim only",
                "preserves_parent_meaning": True,
                "evaluator_only_negative_control": False,
            }
        ]
    parts = claim["decomp_parts"] or [claim["original_claim_text"]]
    a1_children = [
        {"child_id": f"{claim['original_claim_id']}-a1-{index:02d}", "sequence": index, "text": part.strip().rstrip(".") + "."}
        for index, part in enumerate(parts, start=1)
    ]
    if len(parts) == 2:
        a2_texts = [
            f"Within the stated scope, {parts[0].rstrip('.')}.",
            f"Within the same scope, {parts[1].rstrip('.')}.",
        ]
    else:
        a2_texts = [
            f"The first grouped condition is {parts[0].rstrip('.')}.",
            f"The remaining grouped condition is {' and '.join(part.rstrip('.') for part in parts[1:])}.",
        ]
    a2_children = [
        {"child_id": f"{claim['original_claim_id']}-a2-{index:02d}", "sequence": index, "text": text}
        for index, text in enumerate(a2_texts, start=1)
    ]
    drift_text, drift_reason = drift_variant_text(claim["original_claim_text"])
    a3_children = [
        {"child_id": f"{claim['original_claim_id']}-a3-01", "sequence": 1, "text": drift_text}
    ]
    a4_children = [
        {"child_id": f"{claim['original_claim_id']}-a4-{index:02d}", "sequence": index, "text": text}
        for index, text in enumerate(over_decompose(parts), start=1)
    ]
    variants = [
        {
            "decomposition_id": f"dec-{claim['original_claim_id']}-a0",
            "variant_id": "A0",
            "variant_text": claim["original_claim_text"],
            "children": [],
            "variant_description": "original claim only",
            "preserves_parent_meaning": True,
            "evaluator_only_negative_control": False,
        },
        {
            "decomposition_id": f"dec-{claim['original_claim_id']}-a1",
            "variant_id": "A1",
            "variant_text": variant_text_from_children(a1_children, claim["original_claim_text"]),
            "children": a1_children,
            "variant_description": "direct defensible decomposition preserving the parent propositions",
            "preserves_parent_meaning": True,
            "evaluator_only_negative_control": False,
        },
        {
            "decomposition_id": f"dec-{claim['original_claim_id']}-a2",
            "variant_id": "A2",
            "variant_text": variant_text_from_children(a2_children, claim["original_claim_text"]),
            "children": a2_children,
            "variant_description": "alternative legitimate grouping preserving scope and parent meaning",
            "preserves_parent_meaning": True,
            "evaluator_only_negative_control": False,
        },
        {
            "decomposition_id": f"dec-{claim['original_claim_id']}-a3",
            "variant_id": "A3",
            "variant_text": drift_text,
            "children": a3_children,
            "variant_description": "meaning-drift negative control",
            "preserves_parent_meaning": False,
            "evaluator_only_negative_control": True,
            "negative_control_reason": drift_reason,
        },
        {
            "decomposition_id": f"dec-{claim['original_claim_id']}-a4",
            "variant_id": "A4",
            "variant_text": variant_text_from_children(a4_children, claim["original_claim_text"]),
            "children": a4_children,
            "variant_description": "over-decomposition into excessively granular fragments",
            "preserves_parent_meaning": True,
            "evaluator_only_negative_control": False,
            "over_decomposition": True,
        },
    ]
    return variants


def split_for_claim(claim: dict[str, Any]) -> str:
    if claim["local_index"] == 1:
        return "dev"
    if claim["family_id"] == "F11" and claim["local_index"] == 5:
        return "dev"
    return "test"


def build_cases_and_decompositions(
    *,
    claims: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    cases: list[dict[str, Any]] = []
    decompositions: list[dict[str, Any]] = []
    variants_by_claim: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        split = split_for_claim(claim)
        variants = build_decomposition_variants(claim)
        variants_by_claim[claim["original_claim_id"]] = variants
        for variant in variants:
            case_id = f"case-{split}-{claim['original_claim_id']}-{variant['variant_id'].lower()}"
            case = {
                "schema_version": "1.0",
                "case_id": case_id,
                "split": split,
                "original_claim_id": claim["original_claim_id"],
                "original_claim_text": claim["original_claim_text"],
                "variant_id": variant["variant_id"],
                "decomposition_id": variant["decomposition_id"],
                "claim_text": variant["variant_text"],
                "propositions": variant["children"],
                "accessible_subset_id": claim["accessible_subset_id"],
                "runtime_config": {
                    "retrieval_mode": "ordinary",
                    "maximum_passages": 12,
                    "include_permitted_metadata": True,
                },
            }
            cases.append(case)
            if claim["decomp_sensitive"]:
                decomp = {
                    "schema_version": "1.0",
                    "decomposition_id": variant["decomposition_id"],
                    "original_claim_id": claim["original_claim_id"],
                    "original_claim_text": claim["original_claim_text"],
                    "variant_id": variant["variant_id"],
                    "variant_text": variant["variant_text"],
                    "children": variant["children"],
                    "variant_description": variant["variant_description"],
                    "preserves_parent_meaning": variant["preserves_parent_meaning"],
                    "evaluator_only_negative_control": variant["evaluator_only_negative_control"],
                    "generator_adjudicator_identity": ADJUDICATOR_ID,
                    "gold_record_version": GOLD_RECORD_VERSION,
                }
                if variant.get("negative_control_reason"):
                    decomp["negative_control_reason"] = variant["negative_control_reason"]
                if variant.get("over_decomposition"):
                    decomp["over_decomposition"] = True
                decompositions.append(decomp)
    return cases, decompositions, variants_by_claim


def build_aperture_subsets(
    *,
    topics: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    all_ids = sorted(sources)
    ordinary = [
        sid
        for sid, record in sorted(sources.items())
        if record["role"] not in {"prior", "draft"}
    ]
    f12_current = source_id(topics["wickarchive"]["slug"], "current")
    bounded_missing = [sid for sid in all_ids if sid != f12_current]
    f05_current = source_id(topics["amberbraid"]["slug"], "current")
    stale_only = [sid for sid in all_ids if sid != f05_current]
    subsets = {
        "full": {
            "subset_id": "full",
            "description": "All frozen source documents.",
            "source_ids": all_ids,
            "immutable": True,
        },
        "ordinary_window": {
            "subset_id": "ordinary_window",
            "description": "A representative bounded window with current, support, FAQ, guidance, decision, and background records.",
            "source_ids": sorted(ordinary),
            "immutable": True,
        },
        "bounded_missing_decisive": {
            "subset_id": "bounded_missing_decisive",
            "description": "The full source set except the designated current Wick archive policy.",
            "source_ids": sorted(bounded_missing),
            "immutable": True,
        },
        "stale_only": {
            "subset_id": "stale_only",
            "description": "A historical aperture that retains the Amberbraid prior revision and omits its current replacement.",
            "source_ids": sorted(stale_only),
            "immutable": True,
        },
        "distractor_heavy": {
            "subset_id": "distractor_heavy",
            "description": "A broad window containing the near-match incident, supplier, FAQ, and record distractors.",
            "source_ids": all_ids,
            "immutable": True,
        },
    }
    for subset in subsets.values():
        subset["source_count"] = len(subset["source_ids"])
        subset["source_list_sha256"] = sha256_text("\n".join(subset["source_ids"]) + "\n")
    return subsets


def gold_rows_for_cases(
    *,
    claims: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    variants_by_claim: dict[str, list[dict[str, Any]]],
    sources: dict[str, dict[str, Any]],
    subsets: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    claims_by_id = {claim["original_claim_id"]: claim for claim in claims}
    rows_by_split: dict[str, list[dict[str, Any]]] = {"dev": [], "test": []}
    for case in cases:
        claim = claims_by_id[case["original_claim_id"]]
        variant = next(
            item for item in variants_by_claim[claim["original_claim_id"]]
            if item["variant_id"] == case["variant_id"]
        )
        negative = claim["hard_negative"]
        relevant_source_ids: list[str] = []
        relevant_passage_ids: list[str] = []
        annotations: list[dict[str, Any]] = []
        if variant["variant_id"] != "A3":
            for item in claim["evidence"]:
                sid = source_id(claim["topic_slug"], item["role"])
                passage = sources[sid]["anchor_to_passage"][item["anchor"]]
                relevant_source_ids.append(sid)
                relevant_passage_ids.append(passage["passage_id"])
                accessible = sid in subsets[case["accessible_subset_id"]]["source_ids"]
                annotations.append(
                    {
                        "source_id": sid,
                        "passage_id": passage["passage_id"],
                        "start_offset": passage["start_offset"],
                        "end_offset": passage["end_offset"],
                        "offset_unit": OFFSET_UNIT,
                        "span_text": passage["text"],
                        "relevance_class": item["relevance_class"],
                        "decisive": item["decisive"],
                        "jointly_required": item["jointly_required"],
                        "joint_group_id": item["joint_group_id"],
                        "in_accessible_subset": accessible,
                        "evidence_visibility": "accessible" if accessible else "full_only",
                        "short_adjudication_rationale": item["rationale"],
                    }
                )
        negative_sid = source_id(claim["topic_slug"], negative["role"])
        negative_passage = sources[negative_sid]["anchor_to_passage"][negative["anchor"]]
        annotations.append(
            {
                "source_id": negative_sid,
                "passage_id": negative_passage["passage_id"],
                "start_offset": negative_passage["start_offset"],
                "end_offset": negative_passage["end_offset"],
                "offset_unit": OFFSET_UNIT,
                "span_text": negative_passage["text"],
                "relevance_class": "hard_negative",
                "decisive": False,
                "jointly_required": False,
                "joint_group_id": None,
                "in_accessible_subset": negative_sid in subsets[case["accessible_subset_id"]]["source_ids"],
                "evidence_visibility": "accessible" if negative_sid in subsets[case["accessible_subset_id"]]["source_ids"] else "full_only",
                "short_adjudication_rationale": "High-overlap or plausibly related material that does not resolve the tested claim.",
            }
        )
        for index, annotation in enumerate(annotations, start=1):
            row = {
                "schema_version": "1.0",
                "annotation_id": f"ann-{case['case_id']}-{index:02d}",
                "case_id": case["case_id"],
                "split": case["split"],
                "challenge_family": claim["family_id"],
                "challenge_family_name": FAMILY_NAMES[claim["family_id"]],
                "original_claim_id": claim["original_claim_id"],
                "original_claim_text": claim["original_claim_text"],
                "variant_id": case["variant_id"],
                "decomposition_id": case["decomposition_id"],
                "accessible_subset_id": case["accessible_subset_id"],
                "gold_source_ids": sorted(set(relevant_source_ids)),
                "gold_passage_ids": sorted(set(relevant_passage_ids)),
                "source_id": annotation["source_id"],
                "passage_id": annotation["passage_id"],
                "exact_start_offset": annotation["start_offset"],
                "exact_end_offset": annotation["end_offset"],
                "offset_unit": annotation["offset_unit"],
                "span_text": annotation["span_text"],
                "relevance_class": annotation["relevance_class"],
                "decisive": annotation["decisive"],
                "jointly_required": annotation["jointly_required"],
                "joint_group_id": annotation["joint_group_id"],
                "in_accessible_subset": annotation["in_accessible_subset"],
                "evidence_visibility": annotation["evidence_visibility"],
                "answerable_in_full_corpus": claim["answerable"],
                "evaluator_only_negative_control": variant["variant_id"] == "A3",
                "short_adjudication_rationale": annotation["short_adjudication_rationale"],
                "generator_adjudicator_identity": ADJUDICATOR_ID,
                "gold_record_version": GOLD_RECORD_VERSION,
            }
            rows_by_split[case["split"]].append(row)
    for split in rows_by_split:
        rows_by_split[split].sort(key=lambda row: (row["case_id"], row["annotation_id"]))
    return rows_by_split


def source_metadata_for_view(record: dict[str, Any], content_bytes: bytes, passages: list[dict[str, Any]]) -> dict[str, Any]:
    metadata = dict(record["metadata"])
    metadata["content_hash"] = sha256_bytes(content_bytes)
    metadata["passage_count"] = len(passages)
    metadata["passages"] = passages
    return metadata


def materialize_view_source(
    *,
    record: dict[str, Any],
    view_source_dir: Path,
    paragraphs: list[tuple[str, str]],
    preserve_passage_ids: bool,
    metadata_key_order: bool = False,
    override_source_id: str | None = None,
    override_title: str | None = None,
    origin_source_id: str | None = None,
) -> dict[str, Any]:
    source_name = override_source_id or record["source_id"]
    content_text = "\n\n".join(text for _, text in paragraphs) + "\n"
    content_bytes = content_text.encode("utf-8")
    passage_rows: list[dict[str, Any]] = []
    cursor = 0
    for index, (original_pid, text) in enumerate(paragraphs):
        paragraph_bytes = text.encode("utf-8")
        start = cursor
        end = start + len(paragraph_bytes)
        pid = original_pid if preserve_passage_ids else passage_id_for(source_name, index)
        passage_rows.append(
            {
                "passage_id": pid,
                "paragraph_index": index,
                "start_offset": start,
                "end_offset": end,
                "offset_unit": OFFSET_UNIT,
                "text_sha256": sha256_bytes(paragraph_bytes),
            }
        )
        cursor = end + (2 if index < len(paragraphs) - 1 else 1)
    metadata = source_metadata_for_view(record, content_bytes, passage_rows)
    metadata["source_id"] = source_name
    metadata["logical_document_key"] = f"transform::{source_name}"
    if override_title:
        metadata["title"] = override_title
    if origin_source_id:
        metadata["derived_from_source_id"] = origin_source_id
    view_source_dir.mkdir(parents=True, exist_ok=True)
    write_bytes(view_source_dir / "content.txt", content_bytes)
    write_json(view_source_dir / "metadata.json", metadata, sort_keys=not metadata_key_order)
    return {
        "source_id": source_name,
        "content_hash": metadata["content_hash"],
        "passages": passage_rows,
    }


def copy_canonical_view_source(record: dict[str, Any], view_source_dir: Path, *, metadata_key_order: bool = False) -> dict[str, Any]:
    paragraphs = [
        (
            passage["passage_id"],
            record["content_text"].encode("utf-8")[passage["start_offset"] : passage["end_offset"]].decode("utf-8"),
        )
        for passage in record["metadata"]["passages"]
    ]
    return materialize_view_source(
        record=record,
        view_source_dir=view_source_dir,
        paragraphs=paragraphs,
        preserve_passage_ids=True,
        metadata_key_order=metadata_key_order,
    )


def build_transforms(
    *,
    root: Path,
    sources: dict[str, dict[str, Any]],
    seed: int,
) -> list[dict[str, Any]]:
    transforms_root = root / "transforms" / "views"
    transforms_root.mkdir(parents=True, exist_ok=True)
    canonical_ids = sorted(sources)
    transform_specs = [
        ("transform-source-enumeration-permutation-v1", "source_enumeration_permutation"),
        ("transform-harmless-metadata-order-permutation-v1", "harmless_metadata_order_permutation"),
        ("transform-duplicate-document-insertion-v1", "duplicate_document_insertion"),
        ("transform-paraphrased-duplicate-insertion-v1", "paraphrased_duplicate_insertion"),
        ("transform-paragraph-order-permutation-v1", "paragraph_order_permutation"),
    ]
    transform_rows: list[dict[str, Any]] = []
    for transform_id, transform_type in transform_specs:
        view_root = transforms_root / transform_id
        view_root.mkdir(parents=True, exist_ok=True)
        view_ids = list(canonical_ids)
        rng = derived_rng(seed, f"transform:{transform_type}")
        rng.shuffle(view_ids)
        derived_files: list[str] = []
        source_hashes: dict[str, str] = {}
        if transform_type == "source_enumeration_permutation":
            for sid in canonical_ids:
                result = copy_canonical_view_source(sources[sid], view_root / "sources" / sid)
                source_hashes[sid] = result["content_hash"]
                derived_files.extend([f"sources/{sid}/content.txt", f"sources/{sid}/metadata.json"])
            write_json(view_root / "source_enumeration.json", {"source_ids_in_view_order": view_ids})
            derived_files.append("source_enumeration.json")
            derivation = "Copied canonical sources with a seeded enumeration order; source identities and bytes remain unchanged."
        elif transform_type == "harmless_metadata_order_permutation":
            for sid in canonical_ids:
                result = copy_canonical_view_source(
                    sources[sid],
                    view_root / "sources" / sid,
                    metadata_key_order=True,
                )
                source_hashes[sid] = result["content_hash"]
                derived_files.extend([f"sources/{sid}/content.txt", f"sources/{sid}/metadata.json"])
            write_json(view_root / "metadata_order.json", {"operation": "top-level metadata key order reversed; content bytes unchanged"})
            derived_files.append("metadata_order.json")
            derivation = "Re-serialized metadata with a different top-level key order; content hashes are expected to remain unchanged."
        elif transform_type == "duplicate_document_insertion":
            for sid in canonical_ids:
                result = copy_canonical_view_source(sources[sid], view_root / "sources" / sid)
                source_hashes[sid] = result["content_hash"]
                derived_files.extend([f"sources/{sid}/content.txt", f"sources/{sid}/metadata.json"])
            base_sid = canonical_ids[0]
            duplicate_sid = "src-transform-duplicate-canonical"
            result = copy_canonical_view_source(sources[base_sid], view_root / "sources" / duplicate_sid)
            duplicate_meta = json.loads((view_root / "sources" / duplicate_sid / "metadata.json").read_text(encoding="utf-8"))
            duplicate_meta["source_id"] = duplicate_sid
            duplicate_meta["logical_document_key"] = f"transform::duplicate::{base_sid}"
            duplicate_meta["title"] = f"Inserted duplicate of {duplicate_meta['title']}"
            duplicate_meta["derived_from_source_id"] = base_sid
            write_json(view_root / "sources" / duplicate_sid / "metadata.json", duplicate_meta)
            derived_files.extend([f"sources/{duplicate_sid}/content.txt", f"sources/{duplicate_sid}/metadata.json"])
            view_ids.append(duplicate_sid)
            write_json(view_root / "source_enumeration.json", {"source_ids_in_view_order": view_ids})
            derived_files.append("source_enumeration.json")
            derivation = f"Copied all canonical sources and inserted byte-identical document {duplicate_sid} derived from {base_sid}."
        elif transform_type == "paraphrased_duplicate_insertion":
            for sid in canonical_ids:
                result = copy_canonical_view_source(sources[sid], view_root / "sources" / sid)
                source_hashes[sid] = result["content_hash"]
                derived_files.extend([f"sources/{sid}/content.txt", f"sources/{sid}/metadata.json"])
            base_sid = "src-quillmark-current"
            base_record = sources[base_sid]
            original_paragraphs = [
                (
                    passage["passage_id"],
                    base_record["content_text"].encode("utf-8")[passage["start_offset"] : passage["end_offset"]].decode("utf-8"),
                )
                for passage in base_record["metadata"]["passages"]
            ]
            rewritten: list[tuple[str, str]] = []
            changed = False
            for pid, text in original_paragraphs:
                new_text = text
                if not changed:
                    for old, new in (
                        ("retained", "kept on file"),
                        ("record", "register entry"),
                        ("reviewer", "assigned reviewer"),
                    ):
                        if old in new_text:
                            new_text = new_text.replace(old, new, 1)
                            changed = True
                            break
                rewritten.append((pid, new_text))
            if not changed:
                rewritten[2] = (rewritten[2][0], rewritten[2][1] + " The same instruction is stated in alternate wording.")
            duplicate_sid = "src-transform-paraphrase-quillmark"
            result = materialize_view_source(
                record=base_record,
                view_source_dir=view_root / "sources" / duplicate_sid,
                paragraphs=rewritten,
                preserve_passage_ids=False,
                override_source_id=duplicate_sid,
                override_title=f"Paraphrased duplicate of {base_record['title']}",
                origin_source_id=base_sid,
            )
            derived_files.extend([f"sources/{duplicate_sid}/content.txt", f"sources/{duplicate_sid}/metadata.json"])
            view_ids.append(duplicate_sid)
            write_json(view_root / "source_enumeration.json", {"source_ids_in_view_order": view_ids})
            derived_files.append("source_enumeration.json")
            derivation = f"Copied all canonical sources and inserted {duplicate_sid} with one fixed synonym rewrite derived from {base_sid}."
        elif transform_type == "paragraph_order_permutation":
            for sid in canonical_ids:
                record = sources[sid]
                original_paragraphs = [
                    (
                        passage["passage_id"],
                        record["content_text"].encode("utf-8")[passage["start_offset"] : passage["end_offset"]].decode("utf-8"),
                    )
                    for passage in record["metadata"]["passages"]
                ]
                if len(original_paragraphs) > 3:
                    first = original_paragraphs[:2]
                    rest = original_paragraphs[2:]
                    local_rng = derived_rng(seed, f"paragraphs:{sid}")
                    local_rng.shuffle(rest)
                    ordered = first + rest
                else:
                    ordered = original_paragraphs
                result = materialize_view_source(
                    record=record,
                    view_source_dir=view_root / "sources" / sid,
                    paragraphs=ordered,
                    preserve_passage_ids=True,
                )
                source_hashes[sid] = result["content_hash"]
                derived_files.extend([f"sources/{sid}/content.txt", f"sources/{sid}/metadata.json"])
            mapping = {
                sid: {
                    passage["passage_id"]: {
                        "source_id": sid,
                        "new_start_offset": passage["start_offset"],
                        "new_end_offset": passage["end_offset"],
                    }
                    for passage in json.loads(
                        (view_root / "sources" / sid / "metadata.json").read_text(encoding="utf-8")
                    )["passages"]
                }
                for sid in canonical_ids
            }
            write_json(view_root / "semantic_anchor_mapping.json", mapping)
            derived_files.append("semantic_anchor_mapping.json")
            derivation = "Reordered paragraphs with passage identities preserved and a mapping from canonical semantic anchors to new offsets."
        else:
            raise AssertionError(transform_type)
        view_manifest = {
            "schema_version": "1.0",
            "view_id": transform_id,
            "transformation_type": transform_type,
            "derived_from": "canonical",
            "source_ids_in_view_order": view_ids,
            "canonical_source_count": len(canonical_ids),
            "source_content_hashes_for_unchanged_sources": source_hashes,
            "derivation": derivation,
            "gold_data_included": False,
        }
        write_json(view_root / "view_manifest.json", view_manifest)
        derived_files.append("view_manifest.json")
        view_hash = file_tree_hash(view_root)
        transform_rows.append(
            {
                "transformation_id": transform_id,
                "transformation_type": transform_type,
                "view_path": f"transforms/views/{transform_id}",
                "view_tree_sha256": view_hash,
                "derived_files": sorted(derived_files),
                "derivation": derivation,
                "gold_data_included": False,
            }
        )
    return transform_rows


def package_readme() -> str:
    return """# eb-challenge-corpus-v1

This package is a frozen, fully fictional technical/regulatory micro-world for
two separate experiments:

1. retrieval evaluation for an Evidence Bundler-like system; and
2. claim-decomposition evaluation using independently generated A0-A4
   variants.

It is not a regulatory requirement set, compliance opinion, software
qualification, validation record, or evidence about a real organization. All
organizations, systems, products, dates, thresholds, procedures, incidents,
and document histories are synthetic.

## Runtime and evaluator boundary

The retrieval runtime may receive only:

- source bytes and permitted source metadata under sources/;
- a case from cases/;
- the named source subset from aperture/subsets.json; and
- ordinary runtime configuration in the case.

The evaluator-only files under gold/ and the decomposition metadata under
decompositions/ must remain outside the runtime corpus. The runtime must not
be given challenge-family labels, relevance labels, gold source or passage
identifiers, adjudication rationales, expected rankings, or expected outputs.

corpus_manifest.json, SHA256SUMS, and validation/ are control and verification
artifacts, not retrieval hints. A clean runtime mount should explicitly
allowlist the runtime directories above.

## Frozen layout

sources/ contains 60 exact UTF-8 source representations with stable source
identity keys, SHA-256 content hashes, and deterministic paragraph spans.
cases/ contains 148 runtime cases: 37 development cases and 111 sealed-test
cases. The 52 base claims cover the twelve required challenge families; eight
are full-corpus no-answer controls. Twenty-four base claims have A0 through A4
decomposition variants.

The five immutable named apertures are full, ordinary_window,
bounded_missing_decisive, stale_only, and distractor_heavy.
transforms/ contains separately identified non-canonical metamorphic views.

## Reproduction

The generator is deterministic from the recorded seed, as-of date, fixed
generation timestamp, configuration hash, and generator source commit. The
canonical build command used for this version is:

    python3 scripts/generate_eb_challenge_corpus.py --output eb-challenge-corpus-v1 --seed 271828 --as-of 2026-08-27

The generator refuses to write into a non-empty directory unless --force is
explicitly supplied. Do not regenerate this frozen directory after the freeze
receipt; create a new corpus version for corrections.

## Interpretation boundary

Gold annotations are evaluator judgments about this synthetic package only.
They are not independent regulatory truth, and a passing construction check
does not establish retrieval accuracy, decomposition quality, or CAL
validation.
"""


def build_config(seed: int, as_of: str) -> dict[str, Any]:
    return {
        "generator_name": GENERATOR_NAME,
        "generator_version": GENERATOR_VERSION,
        "corpus_name": CORPUS_NAME,
        "corpus_version": CORPUS_VERSION,
        "seed": seed,
        "as_of": as_of,
        "fixed_generation_timestamp": FIXED_GENERATION_TIMESTAMP,
        "source_count": 60,
        "family_minimum_base_claims": 4,
        "target_base_claims": 52,
        "target_decomposition_sensitive_base_claims": 24,
        "split_rule": "first local claim in each family plus F11 local claim five are dev; all variants follow parent split",
        "tree_hash_exclusions": sorted(TREE_HASH_EXCLUSIONS),
        "decomposition_families": sorted(DECOMPOSITION_FAMILIES),
        "uses_llm": False,
        "observed_retrieval_output_dependency": False,
    }


def make_sha256sums(root: Path) -> None:
    rows: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative == "SHA256SUMS":
            continue
        rows.append(f"{sha256_file(path)}  {relative}")
    write_text(root / "SHA256SUMS", "\n".join(rows) + "\n")


def generate(
    *,
    output: Path,
    seed: int,
    as_of_str: str,
    force: bool = False,
) -> dict[str, Any]:
    if output.exists():
        if any(output.iterdir()):
            if not force:
                raise FileExistsError(
                    f"refusing non-empty output directory {output}; use --force only for an intentional new build"
                )
            shutil.rmtree(output)
        else:
            output.rmdir()
    output.mkdir(parents=True, exist_ok=False)
    as_of = parse_date(as_of_str)
    config = build_config(seed, as_of_str)
    config_hash = sha256_text(canonical_json(config))
    topics = build_topics(as_of, seed)
    claims = build_claims(topics)
    sources = build_sources(topics=topics, claims=claims, as_of=as_of, seed=seed)
    subsets = build_aperture_subsets(topics=topics, sources=sources)
    cases, decompositions, variants_by_claim = build_cases_and_decompositions(claims=claims)
    gold_rows = gold_rows_for_cases(
        claims=claims,
        cases=cases,
        variants_by_claim=variants_by_claim,
        sources=sources,
        subsets=subsets,
    )

    write_text(output / "README.md", package_readme())
    for sid, record in sorted(sources.items()):
        source_dir = output / "sources" / sid
        write_bytes(source_dir / "content.txt", record["content_bytes"])
        write_json(source_dir / "metadata.json", record["metadata"])

    write_json(output / "aperture" / "subsets.json", {
        "schema_version": "1.0",
        "corpus_name": CORPUS_NAME,
        "immutable": True,
        "subsets": [subsets[key] for key in sorted(subsets)],
    })

    claims_by_id = {claim["original_claim_id"]: claim for claim in claims}
    for split in ("dev", "test"):
        split_cases = [case for case in cases if case["split"] == split]
        split_cases.sort(key=lambda case: case["case_id"])
        write_jsonl(output / "cases" / f"{split}_cases.jsonl", split_cases)
        split_decompositions = [
            row
            for row in decompositions
            if split_for_claim(claims_by_id[row["original_claim_id"]]) == split
        ]
        split_decompositions.sort(key=lambda row: row["decomposition_id"])
        write_jsonl(output / "decompositions" / f"{split}_decompositions.jsonl", split_decompositions)
        split_gold = gold_rows[split]
        write_jsonl(output / "gold" / f"{split}_relevance.jsonl", split_gold)

    gold_file_names = [
        "gold/dev_relevance.jsonl",
        "gold/test_relevance.jsonl",
        "decompositions/dev_decompositions.jsonl",
        "decompositions/test_decompositions.jsonl",
    ]
    gold_manifest = {
        "schema_version": "1.0",
        "corpus_name": CORPUS_NAME,
        "evaluator_only": True,
        "gold_record_version": GOLD_RECORD_VERSION,
        "adjudicator_identity": ADJUDICATOR_ID,
        "files": {name: sha256_file(output / name) for name in gold_file_names},
        "case_annotation_counts": {
            split: len({row["case_id"] for row in gold_rows[split]})
            for split in ("dev", "test")
        },
        "annotation_row_counts": {split: len(gold_rows[split]) for split in ("dev", "test")},
        "notes": [
            "Gold source and passage identifiers are evaluator-only.",
            "A3 is an evaluator-only meaning-drift negative control and is not a parent-preserving decomposition.",
            "F12 full-corpus decisive annotations may be outside the case's accessible subset.",
        ],
    }
    write_json(output / "gold" / "gold_manifest.json", gold_manifest)

    transform_rows = build_transforms(root=output, sources=sources, seed=seed)
    write_json(output / "transforms" / "transform_manifest.json", {
        "schema_version": "1.0",
        "corpus_name": CORPUS_NAME,
        "canonical_tree_unchanged": True,
        "transformations": transform_rows,
    })

    payload_tree_hash = file_tree_hash(output)
    document_type_counts = Counter(record["document_type"] for record in sources.values())
    family_base_counts = Counter(claim["family_id"] for claim in claims)
    family_case_counts = Counter(
        claim["family_id"]
        for claim in claims
        for _variant in variants_by_claim[claim["original_claim_id"]]
    )
    split_base_counts = Counter(split_for_claim(claim) for claim in claims)
    split_case_counts = Counter(case["split"] for case in cases)
    aperture_boundary_decisive_annotation_count = sum(
        1
        for row in gold_rows["dev"] + gold_rows["test"]
        if row["challenge_family"] == "F12"
        and row["evidence_visibility"] == "full_only"
        and row["decisive"]
    )
    aperture_boundary_case_count = len(
        {
            row["case_id"]
            for row in gold_rows["dev"] + gold_rows["test"]
            if row["evidence_visibility"] == "full_only" and row["decisive"]
        }
    )
    manifest = {
        "schema_version": "1.0",
        "corpus_name": CORPUS_NAME,
        "corpus_version": CORPUS_VERSION,
        "purpose": "Independent synthetic benchmark for retrieval and claim-decomposition experiments.",
        "synthetic_world": {
            "name": "Neralis Compact",
            "fictional": True,
            "real_organization_data_used": False,
            "real_regulatory_requirement_claimed": False,
        },
        "generator": {
            "name": GENERATOR_NAME,
            "version": GENERATOR_VERSION,
            "source_commit": generator_commit(output.parent.parent.parent),
            "source_sha256": generator_source_hash(),
            "generator_config_hash": config_hash,
            "generator_prompt_hash": None,
            "uses_llm": False,
            "observed_retrieval_output_dependency": False,
        },
        "generation_timestamp": FIXED_GENERATION_TIMESTAMP,
        "generation_timestamp_policy": "Fixed canonical timestamp for byte reproducibility; the final freeze receipt records the same canonical build timestamp.",
        "seeds": {
            "master": seed,
            "derivation": "sha256(master_seed + ':' + labeled_stream)[:16] interpreted as an integer",
            "labeled_streams": ["topic", "source-code", "source-body", "transform"],
        },
        "generator_configuration": config,
        "generator_configuration_hash": config_hash,
        "counts": {
            "source_documents": len(sources),
            "passages": sum(len(record["passage_rows"]) for record in sources.values()),
            "base_claims": len(claims),
            "cases": len(cases),
            "decomposition_sensitive_base_claims": sum(1 for claim in claims if claim["decomp_sensitive"]),
            "decomposition_records": len(decompositions),
            "answerable_base_claims": sum(1 for claim in claims if claim["answerable"]),
            "unanswerable_base_claims": sum(1 for claim in claims if not claim["answerable"]),
            "aperture_boundary_cases": aperture_boundary_case_count,
            "aperture_boundary_decisive_annotation_count": aperture_boundary_decisive_annotation_count,
        },
        "challenge_family_base_claim_counts": dict(sorted(family_base_counts.items())),
        "challenge_family_case_counts": dict(sorted(family_case_counts.items())),
        "challenge_family_names": FAMILY_NAMES,
        "split_base_claim_counts": dict(sorted(split_base_counts.items())),
        "split_case_counts": dict(sorted(split_case_counts.items())),
        "document_type_counts": dict(sorted(document_type_counts.items())),
        "sources": [
            {
                "source_id": sid,
                "content_hash": record["metadata"]["content_hash"],
                "title": record["metadata"]["title"],
                "document_type": record["metadata"]["document_type"],
                "version": record["metadata"]["version"],
                "status": record["metadata"]["status"],
            }
            for sid, record in sorted(sources.items())
        ],
        "decomposition_ids": sorted(row["decomposition_id"] for row in decompositions),
        "aperture_subset_ids": sorted(subsets),
        "transformation_ids": sorted(row["transformation_id"] for row in transform_rows),
        "gold_file_hashes": {
            name: sha256_file(output / name)
            for name in [
                "gold/dev_relevance.jsonl",
                "gold/test_relevance.jsonl",
                "gold/gold_manifest.json",
            ]
        },
        "decomposition_file_hashes": {
            name: sha256_file(output / name)
            for name in [
                "decompositions/dev_decompositions.jsonl",
                "decompositions/test_decompositions.jsonl",
            ]
        },
        "validation_report_sha256": "",
        "freeze_receipt_sha256": "",
        "overall_corpus_tree_sha256": payload_tree_hash,
        "tree_hash_definition": {
            "algorithm": "sha256",
            "input": "sorted relative path + tab + file sha256, one row per file",
            "excluded_control_files": sorted(TREE_HASH_EXCLUSIONS),
            "purpose": "Avoid recursive self-hashing while keeping every payload, source, case, gold, and transform file covered.",
        },
        "runtime_allowlist": [
            "sources/**",
            "cases/dev_cases.jsonl",
            "cases/test_cases.jsonl",
            "aperture/subsets.json",
        ],
        "evaluator_only_roots": ["gold/**", "decompositions/**"],
    }
    write_json(output / "corpus_manifest.json", manifest)
    # Seed a provisional checksum receipt so the report can validate every
    # payload file before the report and final freeze receipt are added.
    make_sha256sums(output)

    try:
        from validate_eb_challenge_corpus import validate_corpus
    except ImportError:
        script_dir = Path(__file__).resolve().parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        from validate_eb_challenge_corpus import validate_corpus

    validation_report = validate_corpus(output, require_control_bindings=False)
    validation_report["generation_context"] = {
        "generator_name": GENERATOR_NAME,
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "as_of": as_of_str,
        "overall_corpus_tree_sha256": payload_tree_hash,
    }
    write_json(output / "validation" / "corpus_validation_report.json", validation_report)
    validation_hash = sha256_file(output / "validation/corpus_validation_report.json")

    freeze_receipt = {
        "schema_version": "1.0",
        "receipt_type": "corpus_freeze_receipt",
        "corpus_name": CORPUS_NAME,
        "corpus_version": CORPUS_VERSION,
        "overall_corpus_tree_sha256": payload_tree_hash,
        "generator_name": GENERATOR_NAME,
        "generator_version": GENERATOR_VERSION,
        "generator_source_commit": manifest["generator"]["source_commit"],
        "generator_source_sha256": manifest["generator"]["source_sha256"],
        "generator_config_hash": config_hash,
        "generator_prompt_hash": None,
        "seeds": manifest["seeds"],
        "as_of": as_of_str,
        "generation_timestamp": FIXED_GENERATION_TIMESTAMP,
        "validation_report_sha256": validation_hash,
        "development_case_count": split_case_counts["dev"],
        "sealed_test_case_count": split_case_counts["test"],
        "source_count": len(sources),
        "passage_count": sum(len(record["passage_rows"]) for record in sources.values()),
        "base_claim_count": len(claims),
        "aperture_boundary_case_count": aperture_boundary_case_count,
        "aperture_boundary_decisive_annotation_count": aperture_boundary_decisive_annotation_count,
        "challenge_family_distribution": dict(sorted(family_base_counts.items())),
        "validation_status_at_freeze": validation_report.get("overall_status"),
        "freeze_statement": "Do not modify this frozen corpus. Corrections require a new corpus version or an explicit deviation record.",
    }
    write_json(output / "validation" / "freeze_receipt.json", freeze_receipt)
    receipt_hash = sha256_file(output / "validation/freeze_receipt.json")

    manifest["validation_report_sha256"] = validation_hash
    manifest["freeze_receipt_sha256"] = receipt_hash
    write_json(output / "corpus_manifest.json", manifest)
    make_sha256sums(output)

    return {
        "manifest": manifest,
        "validation_report": validation_report,
        "freeze_receipt": freeze_receipt,
        "output": output,
    }


def default_output() -> Path:
    return Path(__file__).resolve().parents[1] / CORPUS_NAME


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=default_output())
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--as-of", default=DEFAULT_AS_OF)
    parser.add_argument("--force", action="store_true", help="replace an existing output directory intentionally")
    args = parser.parse_args(argv)
    try:
        result = generate(
            output=args.output.resolve(),
            seed=args.seed,
            as_of_str=args.as_of,
            force=args.force,
        )
    except Exception as exc:
        print(f"GENERATION FAILED: {exc}", file=sys.stderr)
        return 1
    manifest = result["manifest"]
    report = result["validation_report"]
    receipt = result["freeze_receipt"]
    print(json.dumps({
        "status": "PASS" if report.get("overall_status") == "PASS" else "FAIL",
        "output": str(result["output"]),
        "overall_corpus_tree_sha256": manifest["overall_corpus_tree_sha256"],
        "validation_report_sha256": manifest["validation_report_sha256"],
        "generator_version": GENERATOR_VERSION,
        "seed": args.seed,
        "as_of": args.as_of,
        "source_count": receipt["source_count"],
        "passage_count": receipt["passage_count"],
        "base_claim_count": receipt["base_claim_count"],
        "development_case_count": receipt["development_case_count"],
        "sealed_test_case_count": receipt["sealed_test_case_count"],
        "challenge_family_distribution": receipt["challenge_family_distribution"],
        "warnings": report.get("warnings", []),
    }, indent=2, sort_keys=True))
    return 0 if report.get("overall_status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
