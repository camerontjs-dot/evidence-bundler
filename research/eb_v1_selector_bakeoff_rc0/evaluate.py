#!/usr/bin/env python3
import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

EXPECTED_ARTIFACT_SHA256 = "3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d"


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    digest.update(Path(path).read_bytes())
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-zip", required=True)
    parser.add_argument("--selections", required=True)
    parser.add_argument("--operational-binding", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if sha256(args.artifact_zip) != EXPECTED_ARTIFACT_SHA256:
        raise SystemExit("artifact digest mismatch")

    selection = json.load(open(args.selections, encoding="utf-8"))
    binding = json.load(open(args.operational_binding, encoding="utf-8"))
    canonical_selection = (
        json.dumps(selection, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    selection_digest = hashlib.sha256(canonical_selection).hexdigest()

    with zipfile.ZipFile(args.artifact_zip) as archive:
        burden = json.loads(archive.read("artifacts/k7/KNOWN_DISTRACTOR_BURDEN.json"))
        treatment = json.loads(archive.read("artifacts/k7/TREATMENT_10_7_RECEIPT.json"))

    required = {
        (lane["proposition_id"], row["evidence_id"])
        for lane in burden["lanes"]
        for row in lane["relationships"]
        if row["classification"] == "required"
    }
    if len(required) != 22:
        raise SystemExit("required gold count mismatch")

    pool = {
        (row["proposition_id"], row["evidence_id"])
        for case in treatment["cases"]
        for row in case["raw_retrieval"]
    }

    labels = {}
    for row in binding["non_drop_bindings"]:
        proposition_id, evidence_id = row["semantic_key"].split("|", 1)
        labels[(proposition_id, evidence_id)] = row["label"]
    for item in pool:
        labels.setdefault(item, "DROP_DISTRACTOR")

    if Counter(labels.values()) != Counter(binding["authority"]["expected_label_counts"]):
        raise SystemExit("operational label count mismatch")

    c05_contextual = {
        ("C05_JOINT:child:1", "C05-P3"),
        ("C05_JOINT:child:2", "C05-P3"),
    }

    arms = {}
    for name, records in selection["arms"].items():
        chosen = {
            (record["proposition_id"], evidence_id)
            for record in records
            for evidence_id in record["selected"]
        }
        if not chosen <= pool:
            raise SystemExit(name + " selects outside pool")

        fully_covered = sum(
            all(
                (lane["proposition_id"], row["evidence_id"]) in chosen
                for row in lane["relationships"]
                if row["classification"] == "required"
            )
            for lane in burden["lanes"]
        )
        label_counts = Counter(labels[item] for item in chosen)
        arms[name] = {
            "retained_relationships": len(chosen),
            "qualification_required_kept": len(chosen & required),
            "qualification_required_total": 22,
            "qualification_required_recall": len(chosen & required) / 22,
            "qualification_fully_covered_lanes": fully_covered,
            "qualification_nonrequired_selected": len(chosen - required),
            "operational_keep_kept": label_counts["KEEP_DISTINCT"],
            "operational_keep_total": 19,
            "operational_keep_recall": label_counts["KEEP_DISTINCT"] / 19,
            "operational_drop_redundant_selected": label_counts["DROP_REDUNDANT"],
            "operational_drop_distractor_selected": label_counts["DROP_DISTRACTOR"],
            "operational_unresolved_selected": label_counts["UNRESOLVED"],
            "c05_contextual_keep_survival": len(chosen & c05_contextual),
            "missed_qualification_required": sorted(
                "|".join(item) for item in required - chosen
            ),
            "missed_operational_keep": sorted(
                "|".join(item)
                for item, label in labels.items()
                if label == "KEEP_DISTINCT" and item not in chosen
            ),
        }

    facilities = [arms[f"facility_alpha_{alpha:.2f}"] for alpha in (0.25, 0.50, 0.75)]
    baseline = arms["fixed_k3"]
    strong = sum(
        row["qualification_required_recall"] > baseline["qualification_required_recall"]
        and row["operational_keep_recall"] >= baseline["operational_keep_recall"]
        and row["c05_contextual_keep_survival"] == 2
        for row in facilities
    ) >= 2
    disposition = (
        "SETWISE_STRONG_SIGNAL" if strong else "SETWISE_NOT_JUSTIFIED_ON_FROZEN_POOL"
    )

    gap = arms["largest_relative_gap_cap3"]
    construct_tension = (
        gap["operational_keep_recall"] == baseline["operational_keep_recall"]
        and gap["retained_relationships"] < baseline["retained_relationships"]
        and gap["qualification_required_recall"] < baseline["qualification_required_recall"]
    )

    output = {
        "schema": "eb-v1-selector-bakeoff-rc0-evaluation-v1",
        "selection_sha256": "sha256:" + selection_digest,
        "artifact_sha256": "sha256:" + EXPECTED_ARTIFACT_SHA256,
        "primary_disposition": disposition,
        "construct_tension_observed": construct_tension,
        "arms": arms,
        "nonclaims": [
            "Frozen-pool screening only.",
            "No selector is production-qualified.",
            "Qualification-required and operational KEEP_DISTINCT remain separate constructs.",
        ],
    }
    out = Path(args.out)
    out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PRIMARY_DISPOSITION=" + disposition)
    print("CONSTRUCT_TENSION_OBSERVED=" + str(construct_tension).lower())
    print("RESULT_SHA256=" + sha256(out))


if __name__ == "__main__":
    main()
