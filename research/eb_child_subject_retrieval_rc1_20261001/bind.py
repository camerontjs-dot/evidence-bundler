"""Append-only preparation gate; never runs retrieval or semantic reviewers."""

from __future__ import annotations

import argparse
import datetime
import importlib.metadata
import sys
from pathlib import Path

from study import (
    HERE,
    BoundaryError,
    canonical,
    check_corpus,
    check_subjects,
    claim_index,
    digest,
    exact,
    fresh_directory,
    load,
    require,
    write_new,
)

STAGES = ["CLAIMS", "SUBJECTS", "CORPUS", "PRE-RETRIEVAL"]


def make_contracts(claims: dict, corpus: dict) -> dict:
    """Transport already-declared claims into A2; no claim or subject production."""
    claim_index(claims)
    check_corpus(claims, corpus)
    sources = {p["packet_id"]: p["sources"] for p in corpus["packets"]}
    contracts = {}
    for packet in claims["packets"]:
        for parent in packet["parents"]:
            contract = {
                "schema": "contract-a-wire-candidate-rc2",
                "handoff_id": parent["parent_id"],
                "producer": {
                    "producer_id": "frozen-research-declarations",
                    "producer_version": "rc1",
                },
                "work": {"work_id": packet["packet_id"]},
                "root_proposition": {
                    "proposition_id": parent["parent_id"],
                    "text": parent["text"],
                    "text_sha256": digest(parent["text"].encode()),
                },
                "decomposition": {
                    "state": "declared",
                    "operator": "all_of",
                    "decomposition_id": parent["parent_id"] + "/all_of",
                    "children": [
                        {
                            "proposition_id": c["child_id"],
                            "text": c["text"],
                            "text_sha256": digest(c["text"].encode()),
                            "sequence": c["sequence"],
                        }
                        for c in parent["children"]
                    ],
                },
                "sources": sources[packet["packet_id"]],
            }
            contract["handoff_sha256"] = digest(canonical(contract))
            contracts[parent["parent_id"]] = contract
    return contracts


def verify_chain(root: Path, count: int) -> list[dict]:
    previous = None
    receipts = []
    for ordinal, stage in enumerate(STAGES[:count], 1):
        path = root / f"{ordinal:02d}-{stage}.PUBLIC.json"
        receipt = load(path)
        require(
            receipt["stage"] == stage
            and receipt["ordinal"] == ordinal
            and receipt["previous_receipt_raw_sha256"] == previous,
            "stage chain mismatch",
        )
        for filename, expected in receipt["files_raw_sha256"].items():
            require(Path(filename).name == filename, "receipt path escape")
            file = root / filename
            require(
                not file.is_symlink() and digest(file.read_bytes()) == expected,
                "frozen input byte drift",
            )
        previous = digest(path.read_bytes())
        receipts.append(receipt)
    return receipts


def snapshot(root: Path, stage: str, files: dict[str, bytes]) -> dict:
    ordinal = STAGES.index(stage) + 1
    receipts = verify_chain(root, ordinal - 1)
    require(not (root / f"{ordinal:02d}-{stage}.PUBLIC.json").exists(), "stage already frozen")
    require(
        all(not (root / name).exists() and Path(name).name == name for name in files),
        "stale/invalid snapshot output",
    )
    hashes = {}
    for filename, data in files.items():
        with (root / filename).open("xb") as stream:
            stream.write(data)
        (root / filename).chmod(0o400)
        hashes[filename] = digest(data)
    receipt = {
        "schema": "eb-child-subject-stage-v1",
        "stage": stage,
        "ordinal": ordinal,
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "previous_receipt_raw_sha256": digest(
            (root / f"{ordinal - 1:02d}-{STAGES[ordinal - 2]}.PUBLIC.json").read_bytes()
        )
        if receipts
        else None,
        "files_raw_sha256": hashes,
        "scientific_execution": "NOT_RUN",
        "semantic_freshness_proved_by_this_gate": False,
    }
    write_new(root / f"{ordinal:02d}-{stage}.PUBLIC.json", receipt)
    return receipt


def check_runtime(model_dir: Path) -> dict:
    model = load(HERE / "MODEL.json")
    require(
        f"{sys.version_info.major}.{sys.version_info.minor}" == model["python_minor"],
        "unsupported/unfrozen Python runtime",
    )
    versions = {}
    for name, expected in model["expected_versions"].items():
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise BoundaryError(f"engine dependency unavailable: {name}") from exc
        require(versions[name] == expected, f"runtime version drift: {name}")
    for filename, expected in model["raw_files"].items():
        require(
            digest((model_dir / filename).read_bytes()) == expected, f"model file drift: {filename}"
        )
    allowed = set(model["raw_files"]) | {"README.md"}
    require(
        {str(p.relative_to(model_dir)) for p in model_dir.rglob("*") if p.is_file()} <= allowed,
        "unfrozen extra model files",
    )
    return {
        "python_version": sys.version.split()[0],
        "python_executable_raw_sha256": digest(Path(sys.executable).resolve().read_bytes()),
        "versions": versions,
        "model_raw_files": model["raw_files"],
        "runtime_execution_qualification": "NOT_RUN; direct identity preflight only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["claims", "subjects", "corpus", "seal"])
    parser.add_argument("--freeze-dir", required=True, type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--custody", type=Path)
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--execution-authority", type=Path)
    args = parser.parse_args()
    try:
        if args.stage == "claims":
            require(args.input is not None, "claims input required")
            claim_index(load(args.input))
            fresh_directory(args.freeze_dir)
            snapshot(args.freeze_dir, "CLAIMS", {"CLAIMS.PRIVATE.json": args.input.read_bytes()})
        elif args.stage == "subjects":
            verify_chain(args.freeze_dir, 1)
            require(args.input is not None, "subject declarations required")
            check_subjects(load(args.freeze_dir / "CLAIMS.PRIVATE.json"), load(args.input))
            snapshot(
                args.freeze_dir, "SUBJECTS", {"SUBJECTS.PRIVATE.json": args.input.read_bytes()}
            )
        elif args.stage == "corpus":
            verify_chain(args.freeze_dir, 2)
            require(args.input is not None and args.custody is not None, "corpus/custody required")
            custody = load(args.custody)
            exact(
                custody,
                {
                    "authority_reference",
                    "declared_by",
                    "fidelity_authority_reference",
                    "historical_overlap_checked",
                    "outcomes_used_for_tuning",
                    "claim_before_corpus_access_receipt_raw_sha256",
                    "inventory_selection_receipt_raw_sha256",
                },
                "custody",
            )
            require(
                custody["historical_overlap_checked"] is True
                and custody["outcomes_used_for_tuning"] is False,
                "ineligible/exposed population",
            )
            for field in [
                "authority_reference",
                "declared_by",
                "fidelity_authority_reference",
                "claim_before_corpus_access_receipt_raw_sha256",
                "inventory_selection_receipt_raw_sha256",
            ]:
                require(
                    isinstance(custody[field], str) and bool(custody[field].strip()),
                    "direct custody evidence missing",
                )
            check_corpus(load(args.freeze_dir / "CLAIMS.PRIVATE.json"), load(args.input))
            contracts = make_contracts(
                load(args.freeze_dir / "CLAIMS.PRIVATE.json"), load(args.input)
            )
            snapshot(
                args.freeze_dir,
                "CORPUS",
                {
                    "CORPUS.PRIVATE.json": args.input.read_bytes(),
                    "CUSTODY.PRIVATE.json": args.custody.read_bytes(),
                    "CONTRACT-A.PRIVATE.json": canonical(contracts),
                },
            )
        else:
            verify_chain(args.freeze_dir, 3)
            require(
                args.model_dir is not None and args.execution_authority is not None,
                "separate execution authority/runtime/reviewer-profile binding required",
            )
            authority = load(args.execution_authority)
            exact(
                authority,
                {
                    "human_authorization_reference",
                    "candidate_source_commit",
                    "candidate_source_tree",
                    "rubric_raw_sha256",
                    "policy_raw_sha256",
                    "reviewer_profile_raw_sha256",
                    "evaluator_controls_raw_sha256",
                    "retrieval_attempt_budget",
                    "decisive_review_destination_authorized",
                },
                "execution authority",
            )
            require(
                authority["human_authorization_reference"].startswith("https://github.com/"),
                "human execution authority reference missing",
            )
            require(authority["retrieval_attempt_budget"] == 2, "attempt budget drift")
            for key, filename in [
                ("rubric_raw_sha256", "RUBRIC.json"),
                ("policy_raw_sha256", "SPEC.json"),
                ("evaluator_controls_raw_sha256", "CONTROLS.json"),
            ]:
                require(
                    authority[key] == digest((HERE / filename).read_bytes()), "frozen policy drift"
                )
            runtime = check_runtime(args.model_dir)
            snapshot(
                args.freeze_dir,
                "PRE-RETRIEVAL",
                {
                    "RUNTIME.PRIVATE.json": canonical(runtime),
                    "EXECUTION-AUTHORITY.PRIVATE.json": args.execution_authority.read_bytes(),
                },
            )
        print('{"state":"PREPARATION_BOUNDARY_REACHED","scientific_result":"NOT_RUN"}')
        return 0
    except (BoundaryError, OSError, TypeError, KeyError) as exc:
        print(canonical({"state": "BLOCKED", "error": str(exc)}).decode())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
