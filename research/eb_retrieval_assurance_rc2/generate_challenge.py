#!/usr/bin/env python3
"""Deterministically generate the independent EB Retrieval Assurance RC2 challenge.

This generator is benchmark-construction apparatus. It does not import Evidence Bundler,
inspect EB output, or use Contract-A decomposition. Runtime inputs and evaluator-only gold
are physically separated in the generated package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
from pathlib import Path
from typing import Any

GENERATOR_NAME = "eb-retrieval-assurance-rc2-generator"
GENERATOR_VERSION = "1.0.0"
BENCHMARK_NAME = "eb-retrieval-assurance-rc2-v1"
BENCHMARK_VERSION = "1.0.0"
DEFAULT_SEED = 161803
FIXED_GENERATED_AT = "2026-08-28T00:00:00Z"

FAMILIES = {
    "R01": "LOW_OVERLAP_RELEVANCE",
    "R02": "COUNTEREVIDENCE_LEXICAL_TRAP",
    "R03": "QUALIFIER_JOINT_PAIR",
    "R04": "EXCEPTION_JOINT_PAIR",
    "R05": "MULTI_SOURCE_COMPOSITION",
    "R06": "DISTRACTOR_HEAVY_BOUNDED_K",
    "R07": "APERTURE_BOUNDARY_HONESTY",
    "R08": "PROVENANCE_TWIN",
    "R09": "NO_ANSWER_HARD_NEGATIVES",
}

NAMES_A = [
    "Alder", "Boreal", "Cinder", "Dune", "Ember", "Frost", "Grove", "Harbor",
    "Ivory", "Juniper", "Kestrel", "Lumen", "Morrow", "Nacre", "Oriole", "Pine",
    "Quartz", "Rill", "Sable", "Tern", "Umber", "Vale", "Willow", "Xylo",
    "Yarrow", "Zephyr", "Amber", "Birch", "Cobalt", "Drift", "Elm", "Flint",
]
NAMES_B = [
    "relay", "rack", "ledger", "gate", "cell", "cabinet", "line", "station",
    "archive", "panel", "queue", "loop", "bay", "bench", "channel", "bridge",
]

QUERY_DECISIVE_PAIRS = [
    ("inspection every 30 days", "a monthly check"),
    ("backup activation before transfer", "standby startup ahead of handoff"),
    ("shipment quarantine for 48 hours", "two-day lot isolation"),
    ("record retention for seven years", "archive preservation for eighty-four months"),
    ("sensor calibration before use", "instrument adjustment prior to operation"),
    ("access review each quarter", "permission recertification four times per year"),
    ("release approval by a second reviewer", "independent verifier sign-off before dispatch"),
    ("temperature hold for 20 minutes", "thermal dwell lasting one third of an hour"),
    ("seal verification before closure", "closure may occur only after integrity confirmation"),
    ("inventory reconciliation each week", "stock balances must be matched every seven days"),
    ("maintenance authorization in advance", "service work requires prior work-order clearance"),
    ("exception review before restart", "operations resume only after deviation disposition"),
]


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hash(root: Path, exclusions: set[str] | None = None) -> str:
    exclusions = exclusions or set()
    rows: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel in exclusions:
            continue
        rows.append(f"{file_sha(path)}  {rel}\n")
    return hashlib.sha256("".join(rows).encode("utf-8")).hexdigest()


def topic_name(index: int) -> str:
    return f"{NAMES_A[index % len(NAMES_A)]} {NAMES_B[(index // len(NAMES_A)) % len(NAMES_B)]}"


def add_passage(passages: list[dict[str, Any]], source_id: str, passage_id: str, text: str, source_order: int, passage_order: int) -> None:
    passages.append({
        "source_id": source_id,
        "passage_id": passage_id,
        "text": text,
        "source_order": source_order,
        "passage_order": passage_order,
    })


def gold_row(case_id: str, n: int, source_id: str, passage_id: str, cls: str, decisive: bool, joint: str | None = None) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "annotation_id": f"{case_id}-A{n:02d}",
        "source_id": source_id,
        "passage_id": passage_id,
        "relevance_class": cls,
        "decisive": decisive,
        "joint_group_id": joint,
    }


def make_case(family: str, split: str, ordinal: int, global_index: int, rng: random.Random) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    case_id = f"RC2-{split.upper()}-{family}-{ordinal:03d}"
    topic = topic_name(global_index)
    q_phrase, d_phrase = QUERY_DECISIVE_PAIRS[global_index % len(QUERY_DECISIVE_PAIRS)]
    token = f"protocol {100 + global_index}"
    passages: list[dict[str, Any]] = []
    gold: list[dict[str, Any]] = []
    source_ids: list[str] = []
    k = 3
    expected_answerability = "answerable"

    def src(suffix: str) -> str:
        sid = f"SRC-{split[0].upper()}-{family}-{ordinal:03d}-{suffix}"
        if sid not in source_ids:
            source_ids.append(sid)
        return sid

    if family == "R01":
        s1, s2 = src("A"), src("B")
        add_passage(passages, s1, f"{case_id}-P01", f"Current instruction for the {topic}: technicians must perform {d_phrase}. This requirement is effective for routine operation.", 2, 1)
        add_passage(passages, s2, f"{case_id}-P02", f"Retired draft for the {topic}: {q_phrase} was proposed under {token}, but the draft never became effective.", 1, 1)
        add_passage(passages, s2, f"{case_id}-P03", f"Training example: the phrase '{q_phrase}' is used only in a classroom scenario for the {topic}.", 1, 2)
        gold += [gold_row(case_id, 1, s1, f"{case_id}-P01", "decisive_support", True), gold_row(case_id, 2, s2, f"{case_id}-P02", "hard_negative", False), gold_row(case_id, 3, s2, f"{case_id}-P03", "hard_negative", False)]
        claim = f"The {topic} requires {q_phrase}."
        k = 2
    elif family == "R02":
        s1, s2 = src("A"), src("B")
        claim = f"The {topic} permits release without a second review under {token}."
        add_passage(passages, s1, f"{case_id}-P01", f"For the {topic}, no item may leave hold status until an independent verifier signs off before dispatch. This rule applies under {token}.", 2, 1)
        add_passage(passages, s2, f"{case_id}-P02", f"Simulation exercise for {token}: 'release without a second review' is allowed during training only and has no operational effect for the {topic}.", 1, 1)
        add_passage(passages, s2, f"{case_id}-P03", f"Glossary note: release, second review, and {token} are common search terms in the {topic} training archive.", 1, 2)
        gold += [gold_row(case_id, 1, s1, f"{case_id}-P01", "decisive_counterevidence", True), gold_row(case_id, 2, s2, f"{case_id}-P02", "hard_negative", False), gold_row(case_id, 3, s2, f"{case_id}-P03", "hard_negative", False)]
        k = 2
    elif family == "R03":
        s1, s2 = src("A"), src("B")
        joint = f"{case_id}-J1"
        claim = f"After a successful scan, the {topic} automatically accepts transfer under {token}."
        add_passage(passages, s1, f"{case_id}-P01", f"A valid read advances the {topic} package into the handoff queue under {token}.", 2, 1)
        add_passage(passages, s1, f"{case_id}-P02", f"That automatic step applies only to domestic lots. Export lots remain held for manual clearance.", 2, 2)
        add_passage(passages, s2, f"{case_id}-P03", f"Training card: successful scan automatically accepts transfer for the {topic}; this card omits scope qualifications and is not controlling.", 1, 1)
        gold += [gold_row(case_id, 1, s1, f"{case_id}-P01", "decisive_support", True, joint), gold_row(case_id, 2, s1, f"{case_id}-P02", "decisive_qualifier", True, joint), gold_row(case_id, 3, s2, f"{case_id}-P03", "hard_negative", False)]
        k = 2
    elif family == "R04":
        s1, s2 = src("A"), src("B")
        joint = f"{case_id}-J1"
        claim = f"The {topic} may remain open during maintenance under {token}."
        add_passage(passages, s1, f"{case_id}-P01", f"Service mode allows the {topic} enclosure to stay unlatched while approved work is underway under {token}.", 2, 1)
        add_passage(passages, s1, f"{case_id}-P02", f"Exception: when hazardous inventory is present, the enclosure must remain secured even during service mode.", 2, 2)
        add_passage(passages, s2, f"{case_id}-P03", f"Maintenance quick card for {token}: the {topic} may remain open during maintenance. The card is abbreviated and non-controlling.", 1, 1)
        gold += [gold_row(case_id, 1, s1, f"{case_id}-P01", "decisive_support", True, joint), gold_row(case_id, 2, s1, f"{case_id}-P02", "decisive_exception", True, joint), gold_row(case_id, 3, s2, f"{case_id}-P03", "hard_negative", False)]
        k = 2
    elif family == "R05":
        s1, s2, s3, s4 = src("A"), src("B"), src("C"), src("D")
        joint = f"{case_id}-J1"
        claim = f"The {topic} item is eligible for release today under {token}."
        add_passage(passages, s1, f"{case_id}-P01", f"Dispatch authorization under {token} requires both a current verification record and absence of an active hold for the {topic}.", 2, 1)
        add_passage(passages, s2, f"{case_id}-P02", f"Today's verification log records the required check as complete for the {topic}.", 3, 1)
        add_passage(passages, s3, f"{case_id}-P03", f"The active-hold register shows the {topic} hold flag cleared this morning.", 4, 1)
        add_passage(passages, s4, f"{case_id}-P04", f"Draft memo: the {topic} is eligible for release today under {token}; approval wording is illustrative only.", 1, 1)
        gold += [gold_row(case_id, 1, s1, f"{case_id}-P01", "decisive_support", True, joint), gold_row(case_id, 2, s2, f"{case_id}-P02", "decisive_support", True, joint), gold_row(case_id, 3, s3, f"{case_id}-P03", "decisive_support", True, joint), gold_row(case_id, 4, s4, f"{case_id}-P04", "hard_negative", False)]
        k = 3
    elif family == "R06":
        s1 = src("A")
        decoy_sources = [src(chr(ord("B") + i)) for i in range(6)]
        claim = f"The {topic} requires witness confirmation before start under {token}."
        add_passage(passages, s1, f"{case_id}-P01", f"Operation of the {topic} may begin only after a second person records independent acknowledgment under {token}.", 7, 1)
        gold.append(gold_row(case_id, 1, s1, f"{case_id}-P01", "decisive_support", True))
        for i, sid in enumerate(decoy_sources, 2):
            text = f"Archived training draft {i-1}: witness confirmation before start is required for the {topic} under {token}. This draft is obsolete and not controlling."
            add_passage(passages, sid, f"{case_id}-P{i:02d}", text, i-1, 1)
            gold.append(gold_row(case_id, i, sid, f"{case_id}-P{i:02d}", "hard_negative", False))
        k = 3
    elif family == "R07":
        s1, s2, s3 = src("A"), src("B"), src("C")
        claim = f"The {topic} requires {q_phrase} under {token}."
        add_passage(passages, s1, f"{case_id}-P01", f"Current instruction for the {topic}: technicians must perform {d_phrase} under {token}.", 3, 1)
        add_passage(passages, s2, f"{case_id}-P02", f"Bounded archive note: {q_phrase} appears in an obsolete proposal for the {topic} under {token}.", 1, 1)
        add_passage(passages, s3, f"{case_id}-P03", f"Bounded archive glossary for {token} lists the phrase {q_phrase} for the {topic}.", 2, 1)
        gold += [gold_row(case_id, 1, s1, f"{case_id}-P01", "decisive_support", True), gold_row(case_id, 2, s2, f"{case_id}-P02", "hard_negative", False), gold_row(case_id, 3, s3, f"{case_id}-P03", "hard_negative", False)]
        source_ids = [s2, s3]
        expected_answerability = "not_answerable_within_aperture"
        k = 2
    elif family == "R08":
        s1, s2 = src("A"), src("B")
        twin_a = f"{topic} North"
        twin_b = f"{topic} South"
        claim = f"For {twin_a}, {q_phrase} applies under {token}."
        decisive = f"At {twin_a}, the controlling instruction requires {d_phrase} under {token}."
        decoy = f"At {twin_b}, the controlling instruction requires {d_phrase} under {token}."
        add_passage(passages, s2, f"{case_id}-P02", decoy, 1, 1)
        add_passage(passages, s1, f"{case_id}-P01", decisive, 2, 1)
        gold += [gold_row(case_id, 1, s1, f"{case_id}-P01", "decisive_support", True), gold_row(case_id, 2, s2, f"{case_id}-P02", "hard_negative", False)]
        k = 1
    elif family == "R09":
        s1, s2, s3 = src("A"), src("B"), src("C")
        claim = f"The {topic} permits emergency bypass of {q_phrase} under {token}."
        for i, sid in enumerate((s1, s2, s3), 1):
            text = f"Reference {i} for the {topic}: emergency bypass, {q_phrase}, and {token} are discussed only as index terms; no operational authorization is stated."
            add_passage(passages, sid, f"{case_id}-P{i:02d}", text, i, 1)
            gold.append(gold_row(case_id, i, sid, f"{case_id}-P{i:02d}", "hard_negative", False))
        expected_answerability = "no_answer_in_full_aperture"
        k = 3
    else:
        raise ValueError(family)

    subset_id = f"AP-{case_id}"
    subset = {
        "subset_id": subset_id,
        "source_ids": source_ids,
        "scope_kind": "bounded" if family == "R07" else "full_case_aperture",
    }
    case = {
        "case_id": case_id,
        "split": split,
        "family": family,
        "family_name": FAMILIES[family],
        "claim_text": claim,
        "accessible_subset_id": subset_id,
        "runtime_config": {"maximum_passages": k},
        "expected_answerability": expected_answerability,
    }
    return case, passages, gold, subset


def generate(output: Path, seed: int, splits: set[str], generator_source_commit: str | None) -> dict[str, Any]:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    rng = random.Random(seed)
    all_passages: list[dict[str, Any]] = []
    all_subsets: list[dict[str, Any]] = []
    split_cases: dict[str, list[dict[str, Any]]] = {"dev": [], "sealed": []}
    split_gold: dict[str, list[dict[str, Any]]] = {"dev": [], "sealed": []}
    counts = {"dev": 2, "sealed": 8}
    global_index = 0
    for split in ("dev", "sealed"):
        if split not in splits:
            continue
        for family in sorted(FAMILIES):
            for ordinal in range(1, counts[split] + 1):
                case, passages, gold, subset = make_case(family, split, ordinal, global_index, rng)
                global_index += 1
                split_cases[split].append(case)
                split_gold[split].extend(gold)
                all_passages.extend(passages)
                all_subsets.append(subset)

    all_passages.sort(key=lambda p: (p["source_id"], p["passage_order"], p["passage_id"]))
    dump_jsonl(output / "runtime" / "passages.jsonl", all_passages)
    dump_json(output / "runtime" / "apertures.json", {"subsets": sorted(all_subsets, key=lambda x: x["subset_id"])})
    for split in ("dev", "sealed"):
        if split in splits:
            dump_jsonl(output / "runtime" / f"{split}_cases.jsonl", split_cases[split])
            dump_jsonl(output / "evaluator_only" / f"{split}_gold.jsonl", split_gold[split])

    source_path = Path(__file__).resolve()
    source_sha = file_sha(source_path)
    manifest = {
        "benchmark_name": BENCHMARK_NAME,
        "benchmark_version": BENCHMARK_VERSION,
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION, "source_sha256": source_sha, "source_commit": generator_source_commit},
        "seed": seed,
        "generated_at": FIXED_GENERATED_AT,
        "splits_generated": sorted(splits),
        "families": FAMILIES,
        "counts": {
            "passages": len(all_passages),
            "dev_cases": len(split_cases["dev"]) if "dev" in splits else 0,
            "sealed_cases": len(split_cases["sealed"]) if "sealed" in splits else 0,
            "subsets": len(all_subsets),
        },
        "construction_boundaries": {
            "uses_evidence_bundler_output": False,
            "uses_contract_a_decomposition": False,
            "runtime_gold_separated": True,
        },
    }
    dump_json(output / "manifest.json", manifest)

    exclusions = {"SHA256SUMS", "freeze_receipt.json"}
    rows = []
    for path in sorted(p for p in output.rglob("*") if p.is_file()):
        rel = path.relative_to(output).as_posix()
        if rel in exclusions:
            continue
        rows.append(f"{file_sha(path)}  {rel}\n")
    (output / "SHA256SUMS").write_text("".join(rows), encoding="utf-8")
    receipt = {
        "benchmark_name": BENCHMARK_NAME,
        "benchmark_version": BENCHMARK_VERSION,
        "tree_sha256": tree_hash(output, exclusions),
        "sha256sums_sha256": file_sha(output / "SHA256SUMS"),
        "generator_source_sha256": source_sha,
        "generator_source_commit": generator_source_commit,
        "seed": seed,
        "generated_at": FIXED_GENERATED_AT,
    }
    dump_json(output / "freeze_receipt.json", receipt)
    return receipt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--splits", choices=["dev", "sealed", "all"], default="all")
    ap.add_argument("--generator-source-commit", default=None)
    args = ap.parse_args()
    splits = {"dev", "sealed"} if args.splits == "all" else {args.splits}
    receipt = generate(args.output, args.seed, splits, args.generator_source_commit)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
