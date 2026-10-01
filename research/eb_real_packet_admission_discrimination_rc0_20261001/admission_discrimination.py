#!/usr/bin/env python3
"""Research-only apparatus for EB real-packet admission discrimination RC0.

This module never changes Evidence Bundler runtime behavior. It freezes an existing
V1 package, prepares a rank-blinded private review packet, evaluates two separate
review artifacts against preregistered controls, and verifies that an explicit
admission replay changes admission state only.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_FREEZE = "eb-real-packet-admission-freeze-rc0-v1"
SCHEMA_MAPPING = "eb-real-packet-admission-mapping-rc0-v1"
SCHEMA_REVIEW_PACKET = "eb-real-packet-admission-review-packet-rc0-v1"
SCHEMA_REVIEW = "eb-real-packet-admission-review-rc0-v1"
SCHEMA_SUMMARY = "eb-real-packet-admission-summary-rc0-v1"
SCHEMA_REPLAY = "eb-real-packet-admission-replay-rc0-v1"
ADMISSION_SCHEMA = "evidence-bundler-admission-v1"

EB_SUBJECT = "08ca896debd6d16fa21be2f178ed7cbe62395d00"
EB_VERSION = "0.2.0"
EXPECTED_PACKAGE_SHA256 = (
    "sha256:8240ca5845b883068c1c9ba6a02e415989fb8d5162664024936d02e677bbd791"
)
EXPECTED_CONTRACT_A_HANDOFF_SHA256 = (
    "sha256:b59ba3b35d2b1d8b0378ac277703cd4a8867ec1e88b8ea34be577df0c3eeb843"
)
EXPECTED_CANDIDATES = 20
EXPECTED_RETAINED = 6
EXPECTED_ACCEPTED = 0

DECISIONS = {"accepted", "rejected", "needs-review"}
REASONS_BY_DECISION = {
    "accepted": {"on_target_adequate"},
    "rejected": {"wrong_target", "insufficient_context"},
    "needs-review": {"uncertain"},
}


class ApparatusError(ValueError):
    """Raised when a frozen research artifact fails closed."""


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


def hash_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def hash_json(value: Any) -> str:
    return hash_bytes(canonical_json_bytes(value))


def hash_file(path: Path) -> str:
    return hash_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApparatusError(f"invalid JSON at {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def package_content_sha256(package: dict[str, Any]) -> str:
    payload = copy.deepcopy(package)
    payload.pop("package_sha256", None)
    return hash_json(payload)


def _validate_baseline_package(package: dict[str, Any]) -> list[dict[str, Any]]:
    if package.get("package_sha256") != EXPECTED_PACKAGE_SHA256:
        raise ApparatusError(
            "baseline package identity mismatch: "
            f"expected {EXPECTED_PACKAGE_SHA256}, got {package.get('package_sha256')!r}"
        )
    if package_content_sha256(package) != EXPECTED_PACKAGE_SHA256:
        raise ApparatusError("baseline package bytes do not reproduce package_sha256")

    producer = package.get("producer")
    if not isinstance(producer, dict) or producer.get("producer_version") != EB_VERSION:
        raise ApparatusError(f"baseline producer_version must equal {EB_VERSION!r}")

    contract_a = package.get("contract_a")
    if (
        not isinstance(contract_a, dict)
        or contract_a.get("handoff_sha256") != EXPECTED_CONTRACT_A_HANDOFF_SHA256
    ):
        raise ApparatusError("baseline Contract A handoff identity mismatch")

    candidates = package.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != EXPECTED_CANDIDATES:
        raise ApparatusError(
            f"baseline must contain exactly {EXPECTED_CANDIDATES} candidates"
        )
    retained = [row for row in candidates if row.get("selection_state") == "retained"]
    if len(retained) != EXPECTED_RETAINED:
        raise ApparatusError(
            f"baseline must contain exactly {EXPECTED_RETAINED} retained candidates"
        )
    accepted = [row for row in retained if row.get("admission_state") == "accepted"]
    if len(accepted) != EXPECTED_ACCEPTED:
        raise ApparatusError(
            f"baseline must contain exactly {EXPECTED_ACCEPTED} accepted candidates"
        )
    if any(row.get("admission_state") != "needs-review" for row in retained):
        raise ApparatusError("all retained baseline candidates must be needs-review")
    return retained


def _coordinate_sort_key(row: dict[str, Any]) -> str:
    return hash_json(
        {
            "proposition_id": row["proposition_id"],
            "passage_id": row["passage_id"],
        }
    )


def freeze(package_path: Path, out_dir: Path) -> dict[str, Any]:
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ApparatusError(f"refusing non-empty freeze output directory: {out_dir}")
    package = load_json(package_path)
    if not isinstance(package, dict):
        raise ApparatusError("baseline package must be a JSON object")
    retained = _validate_baseline_package(package)

    targets = {
        str(row["proposition_id"]): str(row["text"])
        for row in package.get("primary_targets", [])
        if isinstance(row, dict)
    }
    if len(targets) != 2:
        raise ApparatusError("RC0 expects exactly two frozen primary targets")

    ordered = sorted(retained, key=_coordinate_sort_key)
    mapping_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    for index, row in enumerate(ordered, start=1):
        proposition_id = str(row["proposition_id"])
        if proposition_id not in targets:
            raise ApparatusError(f"retained candidate has unknown target {proposition_id!r}")
        alias = f"candidate-{index:02d}"
        mapping_rows.append(
            {
                "candidate_alias": alias,
                "proposition_id": proposition_id,
                "passage_id": str(row["passage_id"]),
                "nomination_rank": int(row["nomination_rank"]),
            }
        )
        review_rows.append(
            {
                "candidate_alias": alias,
                "proposition_text": targets[proposition_id],
                "passage_text": str(row["text"]),
            }
        )

    mapping = {
        "schema": SCHEMA_MAPPING,
        "eb_subject": EB_SUBJECT,
        "baseline_package_sha256": EXPECTED_PACKAGE_SHA256,
        "rows": mapping_rows,
    }
    review_packet = {
        "schema": SCHEMA_REVIEW_PACKET,
        "rubric": {
            "accepted": (
                "The passage is materially about the proposition and contains enough "
                "local context for a downstream semantic auditor to assess the "
                "proposition from this passage."
            ),
            "rejected": (
                "The passage is clearly the wrong target or lacks enough local context "
                "to be meaningfully assessed downstream."
            ),
            "needs-review": "The rubric cannot be applied confidently from the packet alone.",
            "nonclaims": [
                "accepted does not mean supports",
                "accepted does not mean refutes",
                "accepted does not mean true",
                "accepted does not establish source authority or applicability",
            ],
        },
        "rows": review_rows,
    }

    mapping_path = out_dir / "PRIVATE-MAPPING.json"
    packet_path = out_dir / "PRIVATE-REVIEW-PACKET.json"
    write_json(mapping_path, mapping)
    write_json(packet_path, review_packet)

    retained_projection = [
        {
            "proposition_id": row["proposition_id"],
            "passage_id": row["passage_id"],
            "nomination_rank": row["nomination_rank"],
        }
        for row in mapping_rows
    ]
    receipt = {
        "schema": SCHEMA_FREEZE,
        "status": "FROZEN_FOR_SEPARATE_REVIEW",
        "eb_subject": EB_SUBJECT,
        "eb_version": EB_VERSION,
        "baseline_package_sha256": EXPECTED_PACKAGE_SHA256,
        "contract_a_handoff_sha256": EXPECTED_CONTRACT_A_HANDOFF_SHA256,
        "candidate_count": EXPECTED_CANDIDATES,
        "retained_count": EXPECTED_RETAINED,
        "accepted_count": EXPECTED_ACCEPTED,
        "retained_set_sha256": hash_json(retained_projection),
        "private_mapping_sha256": hash_file(mapping_path),
        "private_review_packet_sha256": hash_file(packet_path),
        "review_packet_excludes": [
            "nomination_rank",
            "selection_state",
            "admission_state",
            "retrieval_score",
            "CAL output",
            "Decision output",
            "PR #119 result labels",
        ],
    }
    write_json(out_dir / "FREEZE-RECEIPT.PUBLIC.json", receipt)
    return receipt


def _load_and_validate_review(
    path: Path,
    *,
    packet_sha256: str,
    aliases: set[str],
) -> tuple[str, dict[str, tuple[str, str]]]:
    review = load_json(path)
    if not isinstance(review, dict) or review.get("schema") != SCHEMA_REVIEW:
        raise ApparatusError(f"{path} has wrong review schema")
    if review.get("review_packet_sha256") != packet_sha256:
        raise ApparatusError(f"{path} is not bound to the frozen review packet")
    reviewer = review.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ApparatusError(f"{path} reviewer must be nonblank")
    rows = review.get("decisions")
    if not isinstance(rows, list):
        raise ApparatusError(f"{path} decisions must be an array")

    decisions: dict[str, tuple[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "candidate_alias",
            "decision",
            "reason",
        }:
            raise ApparatusError(f"{path} has malformed decision row")
        alias = row["candidate_alias"]
        decision = row["decision"]
        reason = row["reason"]
        if alias not in aliases or alias in decisions:
            raise ApparatusError(f"{path} has unknown or duplicate alias {alias!r}")
        if decision not in DECISIONS:
            raise ApparatusError(f"{path} has invalid decision {decision!r}")
        if reason not in REASONS_BY_DECISION[decision]:
            raise ApparatusError(
                f"{path} reason {reason!r} is invalid for decision {decision!r}"
            )
        decisions[alias] = (decision, reason)

    if set(decisions) != aliases:
        missing = sorted(aliases - set(decisions))
        raise ApparatusError(f"{path} does not cover all frozen aliases: missing={missing}")
    return reviewer, decisions


def evaluate(
    freeze_path: Path,
    mapping_path: Path,
    packet_path: Path,
    review_paths: list[Path],
    summary_path: Path,
    admission_path: Path | None,
) -> dict[str, Any]:
    if len(review_paths) != 2:
        raise ApparatusError("RC0 requires exactly two separate primary review artifacts")

    receipt = load_json(freeze_path)
    mapping = load_json(mapping_path)
    packet = load_json(packet_path)
    if summary_path.exists():
        raise ApparatusError(f"refusing existing summary output: {summary_path}")
    if admission_path is not None and admission_path.exists():
        raise ApparatusError(f"refusing existing admission output: {admission_path}")

    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA_FREEZE:
        raise ApparatusError("invalid freeze receipt")
    if (
        receipt.get("eb_subject") != EB_SUBJECT
        or receipt.get("baseline_package_sha256") != EXPECTED_PACKAGE_SHA256
        or receipt.get("contract_a_handoff_sha256")
        != EXPECTED_CONTRACT_A_HANDOFF_SHA256
        or receipt.get("candidate_count") != EXPECTED_CANDIDATES
        or receipt.get("retained_count") != EXPECTED_RETAINED
        or receipt.get("accepted_count") != EXPECTED_ACCEPTED
    ):
        raise ApparatusError("freeze receipt authority/count mismatch")
    if not isinstance(mapping, dict) or mapping.get("schema") != SCHEMA_MAPPING:
        raise ApparatusError("invalid private mapping")
    if (
        mapping.get("eb_subject") != EB_SUBJECT
        or mapping.get("baseline_package_sha256") != EXPECTED_PACKAGE_SHA256
    ):
        raise ApparatusError("private mapping authority mismatch")
    if not isinstance(packet, dict) or packet.get("schema") != SCHEMA_REVIEW_PACKET:
        raise ApparatusError("invalid private review packet")
    if hash_file(mapping_path) != receipt.get("private_mapping_sha256"):
        raise ApparatusError("private mapping hash mismatch")
    if hash_file(packet_path) != receipt.get("private_review_packet_sha256"):
        raise ApparatusError("private review packet hash mismatch")

    rows = mapping.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_RETAINED:
        raise ApparatusError("mapping must contain exactly six retained rows")
    aliases = {str(row["candidate_alias"]) for row in rows}
    if len(aliases) != EXPECTED_RETAINED:
        raise ApparatusError("mapping aliases must be unique")
    retained_projection = [
        {
            "proposition_id": row["proposition_id"],
            "passage_id": row["passage_id"],
            "nomination_rank": row["nomination_rank"],
        }
        for row in rows
    ]
    if hash_json(retained_projection) != receipt.get("retained_set_sha256"):
        raise ApparatusError("private mapping retained-set binding mismatch")

    packet_rows = packet.get("rows")
    if not isinstance(packet_rows, list):
        raise ApparatusError("review packet rows must be an array")
    for row in packet_rows:
        if not isinstance(row, dict) or set(row) != {
            "candidate_alias",
            "proposition_text",
            "passage_text",
        }:
            raise ApparatusError("review packet leaked or omitted candidate fields")
    packet_aliases = {str(row.get("candidate_alias")) for row in packet_rows}
    if packet_aliases != aliases:
        raise ApparatusError("review packet aliases do not match mapping aliases")

    packet_sha256 = hash_file(packet_path)
    reviewer_names: list[str] = []
    review_maps: list[dict[str, tuple[str, str]]] = []
    review_hashes: list[str] = []
    for path in review_paths:
        reviewer, decisions = _load_and_validate_review(
            path,
            packet_sha256=packet_sha256,
            aliases=aliases,
        )
        reviewer_names.append(reviewer)
        review_maps.append(decisions)
        review_hashes.append(hash_file(path))
    if reviewer_names[0] == reviewer_names[1]:
        raise ApparatusError("primary reviewer identifiers must be distinct")

    disagreements = [
        alias
        for alias in sorted(aliases)
        if review_maps[0][alias] != review_maps[1][alias]
    ]
    consensus: dict[str, tuple[str, str]] = {}
    if not disagreements:
        consensus = dict(review_maps[0])

    accepted_aliases = (
        {
            alias
            for alias, (decision, _reason) in consensus.items()
            if decision == "accepted"
        }
        if consensus
        else set()
    )
    rank1_aliases = {
        str(row["candidate_alias"])
        for row in rows
        if int(row["nomination_rank"]) == 1
    }
    all_aliases = set(aliases)

    if disagreements:
        primary_disposition = "INCONCLUSIVE"
        research_state = "TERMINAL"
        bounded_result = "REVIEW_DISAGREEMENT"
    elif not accepted_aliases:
        primary_disposition = "FALSIFIED"
        research_state = "TERMINAL"
        bounded_result = "ADMISSION_ONLY_FALSIFIED_FOR_FROZEN_PACKET"
    elif accepted_aliases == all_aliases:
        primary_disposition = "INCONCLUSIVE"
        research_state = "TERMINAL"
        bounded_result = "NO_NEGATIVE_DISCRIMINATION_HEADROOM"
    elif accepted_aliases == rank1_aliases:
        primary_disposition = "INCONCLUSIVE"
        research_state = "TERMINAL"
        bounded_result = "RANK1_WEAK_CONTROL_NOT_DISCRIMINATED"
    else:
        primary_disposition = None
        research_state = "CONTINUE_TO_REPLAY"
        bounded_result = "POSITIVE_ADMISSION_REVIEW_GATE_PASSED"

    counts = {decision: 0 for decision in sorted(DECISIONS)}
    for decision, _reason in consensus.values():
        counts[decision] += 1

    summary = {
        "schema": SCHEMA_SUMMARY,
        "primary_disposition": primary_disposition,
        "research_state": research_state,
        "bounded_result": bounded_result,
        "eb_subject": EB_SUBJECT,
        "baseline_package_sha256": EXPECTED_PACKAGE_SHA256,
        "freeze_receipt_sha256": hash_file(freeze_path),
        "review_artifact_sha256": review_hashes,
        "reviewers_distinct": reviewer_names[0] != reviewer_names[1],
        "exact_review_agreement": len(disagreements) == 0,
        "review_disagreement_count": len(disagreements),
        "consensus_counts": counts,
        "mixed_accepted_nonaccepted": (
            bool(accepted_aliases) and accepted_aliases != all_aliases
            if consensus
            else False
        ),
        "weak_controls": {
            "no_admission_accepted_count": 0,
            "admit_all_would_match_consensus": (
                accepted_aliases == all_aliases if consensus else False
            ),
            "rank1_per_target_accepted_count": len(rank1_aliases),
            "rank1_would_match_consensus": (
                accepted_aliases == rank1_aliases if consensus else False
            ),
        },
        "cal_or_decision_output_used_in_gate": False,
        "contract_b_changed": False,
        "eb_runtime_changed": False,
        "nonclaims": [
            "one real packet does not establish generalization",
            (
                "review admission does not establish support, refutation, truth, "
                "authority, or applicability"
            ),
            "the review gate alone is not SUPPORTED FOR PROMOTION",
            "this result does not qualify automated admission",
            "this result does not promote PR #119 selector machinery",
        ],
    }

    if research_state == "CONTINUE_TO_REPLAY":
        if admission_path is None:
            raise ApparatusError("supported result requires --admission-out")
        mapping_by_alias = {str(row["candidate_alias"]): row for row in rows}
        admission = {
            "schema": ADMISSION_SCHEMA,
            "decisions": [
                {
                    "proposition_id": str(mapping_by_alias[alias]["proposition_id"]),
                    "passage_id": str(mapping_by_alias[alias]["passage_id"]),
                    "decision": consensus[alias][0],
                }
                for alias in sorted(aliases)
            ],
        }
        write_json(admission_path, admission)
        summary["admission_sha256"] = hash_file(admission_path)
        summary["admission_decision_count"] = len(admission["decisions"])
    else:
        summary["admission_sha256"] = None
        summary["admission_decision_count"] = 0

    write_json(summary_path, summary)
    return summary


def _normalized_without_admission(package: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(package)
    value.pop("package_sha256", None)
    for row in value.get("candidates", []):
        if row.get("selection_state") == "retained":
            row["admission_state"] = "needs-review"
    return value


def verify_replay(
    baseline_path: Path,
    run_one_path: Path,
    run_two_path: Path,
    admission_path: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    if receipt_path.exists():
        raise ApparatusError(f"refusing existing replay receipt: {receipt_path}")
    baseline = load_json(baseline_path)
    run_one = load_json(run_one_path)
    run_two = load_json(run_two_path)
    admission = load_json(admission_path)
    if not all(
        isinstance(value, dict) for value in (baseline, run_one, run_two, admission)
    ):
        raise ApparatusError("replay inputs must be JSON objects")
    _validate_baseline_package(baseline)

    for label, package in (("run_one", run_one), ("run_two", run_two)):
        if package_content_sha256(package) != package.get("package_sha256"):
            raise ApparatusError(f"{label} package_sha256 mismatch")
        if package.get("producer", {}).get("producer_version") != EB_VERSION:
            raise ApparatusError(f"{label} producer_version drift")
        if (
            package.get("contract_a", {}).get("handoff_sha256")
            != EXPECTED_CONTRACT_A_HANDOFF_SHA256
        ):
            raise ApparatusError(f"{label} Contract A identity drift")
        if _normalized_without_admission(package) != _normalized_without_admission(
            baseline
        ):
            raise ApparatusError(
                f"{label} changed state outside retained admission_state"
            )

    run_one_bytes = run_one_path.read_bytes()
    run_two_bytes = run_two_path.read_bytes()
    if run_one_bytes != canonical_json_bytes(run_one):
        raise ApparatusError("run_one is not canonical V1 package bytes")
    if run_two_bytes != canonical_json_bytes(run_two):
        raise ApparatusError("run_two is not canonical V1 package bytes")
    if run_one_bytes != run_two_bytes:
        raise ApparatusError("two admission replays are not raw-byte-identical")
    if run_one.get("package_sha256") == baseline.get("package_sha256"):
        raise ApparatusError("positive admission replay did not change package identity")

    if admission.get("schema") != ADMISSION_SCHEMA or not isinstance(
        admission.get("decisions"), list
    ):
        raise ApparatusError("invalid admission sidecar")
    expected: dict[tuple[str, str], str] = {}
    for index, row in enumerate(admission["decisions"]):
        if not isinstance(row, dict) or set(row) != {
            "proposition_id",
            "passage_id",
            "decision",
        }:
            raise ApparatusError(f"malformed admission decision at index {index}")
        key = (str(row["proposition_id"]), str(row["passage_id"]))
        decision = str(row["decision"])
        if decision not in DECISIONS:
            raise ApparatusError(f"invalid admission decision at index {index}")
        if key in expected:
            raise ApparatusError(f"duplicate admission coordinate: {key!r}")
        expected[key] = decision
    if not any(decision == "accepted" for decision in expected.values()):
        raise ApparatusError("positive replay sidecar must accept at least one candidate")
    if all(decision == "accepted" for decision in expected.values()):
        raise ApparatusError("positive replay sidecar must retain a nonaccepted candidate")
    observed = {
        (str(row["proposition_id"]), str(row["passage_id"])): str(
            row["admission_state"]
        )
        for row in run_one["candidates"]
        if row.get("selection_state") == "retained"
    }
    if expected != observed:
        raise ApparatusError(
            "replay admission states do not equal frozen sidecar decisions"
        )

    receipt = {
        "schema": SCHEMA_REPLAY,
        "status": "PASS",
        "eb_subject": EB_SUBJECT,
        "baseline_package_sha256": baseline["package_sha256"],
        "admission_sha256": hash_file(admission_path),
        "run_one_package_sha256": run_one["package_sha256"],
        "run_two_package_sha256": run_two["package_sha256"],
        "byte_identical_replay": True,
        "only_retained_admission_state_changed": True,
        "admission_states_equal_sidecar": True,
        "contract_b_validation": "REQUIRED_EXTERNALLY_BEFORE_TERMINAL_SUPPORT",
        "cal_semantics_checked": False,
    }
    write_json(receipt_path, receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    freeze_cmd = sub.add_parser("freeze")
    freeze_cmd.add_argument("--package", type=Path, required=True)
    freeze_cmd.add_argument("--out-dir", type=Path, required=True)

    evaluate_cmd = sub.add_parser("evaluate")
    evaluate_cmd.add_argument("--freeze", type=Path, required=True)
    evaluate_cmd.add_argument("--mapping", type=Path, required=True)
    evaluate_cmd.add_argument("--packet", type=Path, required=True)
    evaluate_cmd.add_argument("--review", type=Path, action="append", required=True)
    evaluate_cmd.add_argument("--summary-out", type=Path, required=True)
    evaluate_cmd.add_argument("--admission-out", type=Path, default=None)

    replay_cmd = sub.add_parser("verify-replay")
    replay_cmd.add_argument("--baseline", type=Path, required=True)
    replay_cmd.add_argument("--run-one", type=Path, required=True)
    replay_cmd.add_argument("--run-two", type=Path, required=True)
    replay_cmd.add_argument("--admission", type=Path, required=True)
    replay_cmd.add_argument("--receipt-out", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "freeze":
        freeze(args.package, args.out_dir)
    elif args.command == "evaluate":
        evaluate(
            args.freeze,
            args.mapping,
            args.packet,
            args.review,
            args.summary_out,
            args.admission_out,
        )
    else:
        verify_replay(
            args.baseline,
            args.run_one,
            args.run_two,
            args.admission,
            args.receipt_out,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
