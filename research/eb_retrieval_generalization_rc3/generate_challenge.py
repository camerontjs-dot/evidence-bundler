#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

SEED = 141421
BENCHMARK = "eb-retrieval-low-overlap-rc3-v1"
K = 5
PASSAGES_PER_CASE = 9

L01 = [
    ("Vardessa", "Vardessa backup power starts automatically when utility power is lost.", "Upon a mains interruption, Vardessa's standby supply self-activates without operator action."),
    ("Kelthorn", "Kelthorn keeps customer records for seven years after an account closes.", "Archived client files remain preserved for eighty-four months following termination of the relationship at Kelthorn."),
    ("Orivane", "Orivane sends an alarm automatically when refrigerated storage gets too warm.", "A rise beyond the cold-room thermal limit causes Orivane to issue an unattended alert."),
    ("Pellorin", "Pellorin removes a user's access immediately after the user is terminated.", "Employment separation at Pellorin triggers same-event revocation of the departing person's credentials."),
    ("Tamsurel", "Tamsurel blocks a batch from release when a sterility result is pending.", "Lots at Tamsurel remain quarantined until microbial-release testing has produced a final result."),
    ("Dorevix", "Dorevix changes encryption keys every ninety days.", "Cryptographic material at Dorevix is rotated on a three-month cadence."),
    ("Marneth", "Marneth switches database traffic to the standby server when the primary server fails.", "Loss of the active database node causes Marneth to redirect requests to its replica automatically."),
    ("Quessira", "Quessira recalibrates the pressure sensor once every six months.", "The pressure transducer at Quessira undergoes calibration on a semiannual interval."),
    ("Ravennor", "Ravennor stops a shipment when the temperature logger shows an excursion.", "A recorded cold-chain deviation places the Ravennor consignment on hold before dispatch."),
    ("Selcora", "Selcora prevents administrators from changing old audit log entries.", "Historical event records in Selcora are append-only even for privileged operators."),
    ("Uldaryn", "Uldaryn repeats the decontamination cycle if the biological indicator is positive.", "Detection of surviving organisms causes Uldaryn to rerun the sanitation sequence."),
    ("Bexalon", "Bexalon continues measuring flow if one of its two flow sensors fails.", "Either transducer can sustain Bexalon's flow measurement when its paired sensor is unavailable."),
    ("Cyrentha", "Cyrentha requires two approvals before an invoice over fifty thousand dollars is paid.", "Payments above the 50,000-dollar threshold at Cyrentha need authorization from two separate approvers."),
    ("Fendrel", "Fendrel rejects a specimen if the patient identifier is missing.", "Samples lacking a subject ID are not accepted for processing by Fendrel."),
    ("Gavaris", "Gavaris sends emergency notifications to both the on-call engineer and the site manager.", "An emergency page from Gavaris is delivered to the duty engineer together with the facility manager."),
    ("Hesperon", "Hesperon can restore data to a point no more than fifteen minutes before a failure.", "Hesperon's recovery-point objective limits recoverable data loss to a quarter hour."),
]

L02 = [
    ("Ilyrion", "Ilyrion unlocks the unit only after both the temperature test and the pressure test pass.", "Release remains inhibited while either thermal verification or pressure verification is outstanding at Ilyrion; access is enabled only when neither remains outstanding."),
    ("Jorvessa", "Jorvessa archives a report only if the reviewer signs it and the checksum matches.", "At Jorvessa, an unsigned review or a checksum mismatch is sufficient to prevent a report from entering the archive."),
    ("Kestivar", "Kestivar starts the backup pump when either the main pump stops or line pressure falls below the limit.", "The standby pump at Kestivar stays idle only while the primary pump is running and line pressure remains above its minimum."),
    ("Lunareth", "Lunareth releases a shipment only when the seal is intact and the receiving temperature is in range.", "A broken seal or an out-of-range receipt temperature blocks shipment release at Lunareth."),
    ("Meridax", "Meridax closes an incident only after the owner documents the cause and completes every corrective action.", "At Meridax, an incident remains open if either causal documentation is absent or any corrective action is unfinished."),
    ("Narethis", "Narethis permits remote login only when the user has a valid certificate and multifactor authentication succeeds.", "Remote access at Narethis is denied whenever the presented certificate is invalid or the second authentication factor fails."),
    ("Ossaryn", "Ossaryn marks a device ready only after calibration and self-test both succeed.", "Any failed calibration or unsuccessful self-test keeps the Ossaryn device out of the ready state."),
    ("Praevon", "Praevon escalates an alert if it remains unacknowledged for ten minutes or if severity becomes critical.", "An alert avoids escalation at Praevon only when it is acknowledged within ten minutes and never reaches critical severity."),
    ("Quoralis", "Quoralis accepts a supplier only when the audit is current and no critical finding remains open.", "An expired audit or any unresolved critical finding prevents supplier acceptance at Quoralis."),
    ("Rethovia", "Rethovia writes a backup only after the snapshot completes and replication is confirmed.", "Rethovia does not commit a backup while either snapshot creation or replication confirmation is incomplete."),
    ("Sorellan", "Sorellan starts production only if the line clearance is complete and the correct label roll is loaded.", "Production at Sorellan remains blocked by either unfinished line clearance or an incorrect labeling roll."),
    ("Tervaine", "Tervaine releases a user account only after identity proofing passes and the manager approves the request.", "Failure of identity proofing or absence of managerial approval prevents account activation at Tervaine."),
    ("Ulvarin", "Ulvarin accepts a data import only when every required column is present and the schema version is supported.", "A missing mandatory field or an unsupported schema revision causes Ulvarin to reject the import."),
    ("Vesparra", "Vesparra stops the reactor if temperature exceeds the limit or cooling flow is lost.", "The Vesparra reactor continues operating only while temperature stays within bounds and cooling flow remains available."),
    ("Wendovar", "Wendovar pays a refund only after the return is received and fraud screening clears.", "At Wendovar, either an unreceived return or an uncleared fraud screen is enough to withhold the refund."),
    ("Xantrel", "Xantrel publishes a model only if validation passes and the approval record is complete.", "A validation failure or an incomplete approval record prevents model publication at Xantrel."),
]

L03 = [
    ("Yorvane", "Yorvane's production gateway blocks outbound traffic to unknown domains.", "The live Yorvane gateway denies egress toward destinations absent from its approved-domain registry."),
    ("Zelcaryn", "Zelcaryn's current dispenser stops filling when bottle weight reaches the target.", "In the active Zelcaryn line, attaining the prescribed mass terminates product delivery into the container."),
    ("Avernis", "Avernis's production scheduler prevents two maintenance jobs from using the same machine at once.", "The deployed Avernis planner enforces exclusive equipment occupancy across overlapping maintenance work."),
    ("Brontara", "Brontara's live portal hides patient records from users outside the assigned care team.", "The operational Brontara interface withholds a subject chart from personnel not belonging to that subject's care group."),
    ("Corveth", "Corveth's active controller shuts the valve when downstream pressure exceeds the trip point.", "The in-service Corveth controller closes the valve after downstream pressure crosses the configured high-pressure threshold."),
    ("Delyntra", "Delyntra's production pipeline rejects files whose digital signature is invalid.", "The deployed Delyntra ingestion path refuses artifacts that fail cryptographic signature verification."),
    ("Esmorin", "Esmorin's live inventory service reserves stock before confirming an order.", "The operational Esmorin service allocates inventory prior to issuing order confirmation."),
    ("Falaris", "Falaris's current billing service rounds tax only after calculating tax on the full invoice.", "The active Falaris billing path computes levy on the aggregate invoice amount before applying monetary rounding."),
    ("Gorvessa", "Gorvessa's production monitor suppresses duplicate alerts for five minutes.", "The live Gorvessa monitor coalesces repeated notifications within a five-minute deduplication window."),
    ("Hadrinel", "Hadrinel's active access service locks an account after five failed sign-in attempts.", "The deployed Hadrinel service disables login once five consecutive authentication failures have accumulated."),
    ("Iskavera", "Iskavera's production sorter sends damaged parcels to the manual inspection lane.", "The operating Iskavera sorter diverts compromised packages into the human-review queue."),
    ("Javorel", "Javorel's current reporting service omits draft records from monthly totals.", "The active Javorel reporting path excludes unfinalized entries when aggregating the monthly figures."),
    ("Kyradis", "Kyradis's production cache removes entries after thirty minutes without access.", "The live Kyradis cache evicts objects following a half hour of inactivity."),
    ("Lethoran", "Lethoran's active scanner quarantines an upload when malware is detected.", "The deployed Lethoran scanner isolates an uploaded artifact after malicious code is found."),
    ("Mavressa", "Mavressa's production workflow sends rejected requests back to the original requester.", "The live Mavressa workflow routes a declined submission back to the person who initiated it."),
    ("Nyralon", "Nyralon's current telemetry service drops sensor messages that fail checksum validation.", "The operational Nyralon telemetry path discards readings whose integrity check does not verify."),
]

C01 = [
    ("Obereth", "Obereth permits external USB drives on production workstations.", "Obereth prohibits external USB drives on production workstations."),
    ("Pryvane", "Pryvane allows operators to bypass the second approval for emergency changes.", "Pryvane does not allow operators to bypass the second approval for emergency changes."),
    ("Quendris", "Quendris retains deleted customer data indefinitely.", "Quendris deletes retained customer data after the documented retention period; indefinite retention is forbidden."),
    ("Rovessa", "Rovessa accepts shipments when the tamper seal is broken.", "Rovessa rejects shipments when the tamper seal is broken."),
    ("Sylaren", "Sylaren keeps default administrator passwords enabled after installation.", "Sylaren requires default administrator passwords to be disabled during installation."),
    ("Torenza", "Torenza releases a batch before required laboratory results are complete.", "Torenza forbids batch release until all required laboratory results are complete."),
    ("Uverin", "Uverin permits unencrypted backups to leave the secure network.", "Uverin blocks unencrypted backups from leaving the secure network."),
    ("Valdessa", "Valdessa allows a user to approve their own expense claim.", "Valdessa prevents a user from approving their own expense claim."),
    ("Weyrith", "Weyrith continues processing after the emergency stop is pressed.", "Weyrith stops processing when the emergency stop is pressed."),
    ("Xoralen", "Xoralen treats a failed checksum as a valid file.", "Xoralen rejects a file when checksum validation fails."),
    ("Yavessa", "Yavessa sends patient data to analytics without removing direct identifiers.", "Yavessa removes direct identifiers before patient data is sent to analytics."),
    ("Zorveth", "Zorveth permits contractors to keep access after their engagement ends.", "Zorveth revokes contractor access when the engagement ends."),
    ("Aldorin", "Aldorin ignores a temperature alarm during refrigerated transport.", "Aldorin places refrigerated transport on hold when a temperature alarm occurs."),
    ("Brynessa", "Brynessa allows unsigned software packages into production.", "Brynessa blocks software packages from production unless their signature verifies."),
    ("Caldrex", "Caldrex permits database administrators to erase audit events.", "Caldrex prevents database administrators from erasing audit events."),
    ("Dovaril", "Dovaril ships an order even when fraud screening marks it high risk.", "Dovaril holds an order when fraud screening marks it high risk."),
]


def dump_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lexical_decoys(entity: str, query: str, family: str) -> list[str]:
    # Five naturally distinct but query-heavy contexts. These are intentionally not
    # evidence for the live proposition: they concern training, test rigs, indices,
    # review forms, or historical prototypes.
    core = query.rstrip(".")
    return [
        f"The {entity} training simulator includes a scenario stating that {core.lower()} during the exercise; simulator behavior is not the production system.",
        f"A {entity} acceptance-test worksheet asks auditors to verify whether {core.lower()}; the worksheet records a test question, not the observed production behavior.",
        f"The {entity} documentation index contains an entry titled '{core}'; the index entry does not state the live system outcome.",
        f"A {entity} maintenance checklist repeats the requirement that {core.lower()} but contains no execution result for the operating system.",
        f"An archived {entity} prototype note says {core.lower()}; the note is explicitly superseded and does not describe the current production implementation.",
    ]


def c01_distractors(entity: str, claim: str) -> list[str]:
    subject = " ".join(claim.rstrip(".").split()[1:])
    return [
        f"The {entity} policy glossary defines terms used in the statement about {subject} but does not grant or deny the permission.",
        f"A {entity} training slide asks whether {subject}; the slide contains no policy answer.",
        f"The {entity} audit plan samples controls related to {subject} without stating the control outcome.",
        f"A {entity} change ticket references {subject} as a review topic but does not change the governing policy.",
        f"The {entity} support guide explains how to report questions about {subject} and contains no authorization rule.",
        f"A {entity} historical index lists documents about {subject} but provides no current policy text.",
        f"The {entity} review queue includes an item concerning {subject}; queue membership is not a policy decision.",
        f"A {entity} monitoring dashboard counts events related to {subject} without establishing whether the behavior is permitted.",
    ]


def make_case(family: str, index: int, entity: str, query: str, decisive_text: str, rng: random.Random) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    case_id = f"{family}-{index:02d}"
    source_id = f"src-{family.lower()}-{index:02d}-{entity.lower()}"
    subset_id = f"scope-{case_id.lower()}"

    if family in {"L01", "L02", "L03"}:
        decoys = lexical_decoys(entity, query, family)
        # The first five positions are query-heavy lexical decoys, so first-N at
        # K=5 cannot recover the decisive evidence. Within that protected prefix,
        # the designated hard negative is shuffled deterministically. The decisive
        # paraphrase is independently shuffled across positions 6-9 to avoid a
        # benchmark-wide fixed-rank cue while preserving the first-N falsifier.
        hard_text = decoys[0]
        prefix = decoys[:5]
        rng.shuffle(prefix)
        tail = [
            f"The {entity} service inventory lists the component as active in production but does not describe the queried behavior.",
            f"The {entity} release record identifies the current deployment and contains no statement resolving this claim.",
            decisive_text,
            f"The {entity} incident register contains no event that independently resolves the queried proposition.",
        ]
        rng.shuffle(tail)
        texts = prefix + tail
        decisive_order = texts.index(decisive_text) + 1
        hard_order = texts.index(hard_text) + 1
        role = "support"
    else:
        # Counterevidence is deliberately lexically accessible so the exact BM25
        # baseline can establish a meaningful retention floor for the later hybrid run.
        distractors = c01_distractors(entity, query)
        texts = [distractors[0], decisive_text] + distractors[1:8]
        decisive_order = 2
        hard_order = 1
        role = "counterevidence"

    passages: list[dict[str, Any]] = []
    source_text = "\n\n".join(texts)
    cursor = 0
    for order, text in enumerate(texts, 1):
        passage_id = f"{case_id.lower()}-p{order:02d}"
        start = source_text.index(text, cursor)
        end = start + len(text)
        cursor = end
        passages.append({
            "source_id": source_id,
            "passage_id": passage_id,
            "source_order": index,
            "passage_order": order,
            "source_path": f"runtime/sources.jsonl#{source_id}",
            "char_start": start,
            "char_end": end,
            "text": text,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        })

    decisive = passages[decisive_order - 1]
    hard = passages[hard_order - 1]
    case = {
        "case_id": case_id,
        "claim_text": query,
        "accessible_subset_id": subset_id,
        "runtime_config": {"maximum_passages": K},
    }
    gold = {
        "case_id": case_id,
        "family": family,
        "answerable": True,
        "entity_stem": entity,
        "decisive": [{"source_id": source_id, "passage_id": decisive["passage_id"], "role": role}],
        "hard_negatives": [{"source_id": source_id, "passage_id": hard["passage_id"]}],
        "construction": {
            "decisive_passage_order": decisive_order,
            "hard_negative_passage_order": hard_order,
            "seed": SEED,
        },
    }
    return case, passages, gold


def build(root: Path) -> None:
    rng = random.Random(SEED)
    runtime = root / "runtime"
    gold_dir = root / "evaluator_only"
    prov = root / "provenance"
    for p in (runtime, gold_dir, prov):
        p.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, Any]] = []
    passages: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    gold_rows: list[dict[str, Any]] = []
    scopes: dict[str, Any] = {}

    families = (("L01", L01), ("L02", L02), ("L03", L03), ("C01", C01))
    for family, specs in families:
        assert len(specs) == 16
        for i, (entity, query, decisive) in enumerate(specs, 1):
            case, ps, gold = make_case(family, i, entity, query, decisive, rng)
            cases.append(case)
            passages.extend(ps)
            sources.append({"source_id": ps[0]["source_id"], "text": "\n\n".join(p["text"] for p in ps)})
            scopes[case["accessible_subset_id"]] = {
                "subset_id": case["accessible_subset_id"],
                "source_ids": [ps[0]["source_id"]],
            }
            gold_rows.append(gold)

    dump_jsonl(runtime / "sealed_cases.jsonl", cases)
    dump_jsonl(runtime / "passages.jsonl", passages)
    dump_jsonl(runtime / "sources.jsonl", sources)
    dump_json(runtime / "scopes.json", scopes)
    dump_jsonl(gold_dir / "sealed_gold.jsonl", gold_rows)

    receipt = {
        "benchmark": BENCHMARK,
        "generator_seed": SEED,
        "sealed_cases": len(cases),
        "passages": len(passages),
        "family_counts": {fam: sum(1 for g in gold_rows if g["family"] == fam) for fam in ("L01", "L02", "L03", "C01")},
        "maximum_passages": K,
        "passages_per_case": PASSAGES_PER_CASE,
        "hybrid_sealed_exposed": False,
        "semantic_sealed_exposed": False,
    }
    dump_json(prov / "generator_receipt.json", receipt)
    readme = """# EB Retrieval Low-Overlap RC3 v1

Fresh sealed Research-Infrastructure benchmark for the bounded PR #15 low-overlap retrieval question.

- deterministic generator seed: `141421`
- exactly 64 answerable sealed cases
- 16 each: L01 terminology substitution, L02 compositional paraphrase, L03 lexical-decoy low-overlap, C01 fresh counterevidence retention
- `maximum_passages = 5`
- retriever-visible runtime material is physically separated from evaluator-only family/gold identities
- no Hybrid or Semantic-only sealed output is generated by this benchmark or its apparatus workflow

The scientific object is frozen by the RC3 apparatus freeze manifest before the first sealed BM25/lexical control run.
"""
    (root / "README.md").write_text(readme, encoding="utf-8")

    tracked = [
        runtime / "sealed_cases.jsonl",
        runtime / "passages.jsonl",
        runtime / "sources.jsonl",
        runtime / "scopes.json",
        gold_dir / "sealed_gold.jsonl",
        prov / "generator_receipt.json",
    ]
    sums = "".join(f"{sha256(p)}  {p.relative_to(root).as_posix()}\n" for p in tracked)
    (root / "SHA256SUMS").write_text(sums, encoding="utf-8")
    manifest = {
        "benchmark": BENCHMARK,
        "generator_seed": SEED,
        "sealed_cases": 64,
        "runtime_files": ["runtime/sealed_cases.jsonl", "runtime/passages.jsonl", "runtime/sources.jsonl", "runtime/scopes.json"],
        "evaluator_only_files": ["evaluator_only/sealed_gold.jsonl"],
        "provenance_files": ["provenance/generator_receipt.json"],
        "sha256sums": "SHA256SUMS",
        "runtime_gold_physical_separation": True,
    }
    dump_json(root / "manifest.json", manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    build(args.output_root)


if __name__ == "__main__":
    main()
