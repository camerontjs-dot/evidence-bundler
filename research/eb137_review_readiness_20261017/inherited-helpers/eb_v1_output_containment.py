"""Qualify one installed EB V1 candidate, including its authorized review surface."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import importlib.metadata
import json
import os
import runpy
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

BASE = "08ca896debd6d16fa21be2f178ed7cbe62395d00"
VERSION = "0.3.0.dev0"
CONTRACT_B = "c314e53bd91c0736aa4370a364673b069aceb43e"
CAL = "64b6c7702696c851057c1cf0b2c105b1c81db543"
PROBE_SHA256 = "70f18e7c57e3ac6b0e90b358c621a8dd0be44f6fb1ccf69a19d3d6df3eaee52a"
FROZEN_PATHS = (
    "src/evidence_bundler/v1/__init__.py",
    "src/evidence_bundler/v1/__main__.py",
    "src/evidence_bundler/v1/builder.py",
    "src/evidence_bundler/v1/retrieval.py",
    "src/evidence_bundler/v1/package.py",
    "src/evidence_bundler/v1/contract_a.py",
    "src/evidence_bundler/production_v1/__init__.py",
    "src/evidence_bundler/contracts",
    "src/evidence_bundler/models",
    "schema",
    "config/eb_v1_slice",
    "src/evidence_bundler/production_v1/data",
)
REVIEW_SURFACE = (
    "src/evidence_bundler/production_v1/cli.py",
    "src/evidence_bundler/production_v1/execution.py",
    "src/evidence_bundler/production_v1/review_cycle.py",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def blob(root: Path, spec: str) -> str | None:
    try:
        return git(root, "rev-parse", spec)
    except subprocess.CalledProcessError:
        return None


def verify_probe(path: Path) -> None:
    require(digest(path) == PROBE_SHA256, "independent frozen probe bytes changed")


def identity(args: argparse.Namespace) -> None:
    root = args.checkout.resolve()
    head = git(root, "rev-parse", "HEAD")
    require(head == args.expected_head, "checkout is not the exact event head")
    git(root, "diff", "--exit-code", "HEAD")
    frozen = {}
    for path in FROZEN_PATHS:
        before = git(root, "rev-parse", f"{BASE}:{path}")
        after = git(root, "rev-parse", f"{head}:{path}")
        require(before == after, f"frozen authority changed: {path}")
        git(root, "diff", "--exit-code", "HEAD", "--", path)
        frozen[path] = before

    review_surface = {}
    for path in REVIEW_SURFACE:
        head_blob = blob(root, f"{head}:{path}")
        base_blob = blob(root, f"{BASE}:{path}")
        require(head_blob is not None, f"review surface missing: {path}")
        require(head_blob != base_blob, f"review surface did not change: {path}")
        review_surface[path] = {"base": base_blob, "head": head_blob}

    before_project = tomllib.loads(git(root, "show", f"{BASE}:pyproject.toml"))
    current_project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    before_project["project"]["version"] = VERSION
    require(current_project == before_project, "pyproject changes exceed the version correction")
    version_module = ast.parse((root / "src/evidence_bundler/__init__.py").read_text())
    versions = [
        ast.literal_eval(node.value)
        for node in version_module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        )
    ]
    require(versions == [VERSION], "package version does not identify the correction")
    verify_probe(args.probe)

    authorities = {}
    for name, path, expected in (
        ("contract_b", args.apparatus, CONTRACT_B),
        ("cal", args.cal, CAL),
    ):
        if path is not None:
            require(git(path, "rev-parse", "HEAD") == expected, f"{name} checkout drift")
            authorities[name] = {
                "commit": expected,
                "tree": git(path, "rev-parse", "HEAD^{tree}"),
            }
    if args.apparatus is not None:
        pin = (args.apparatus / "schema/.contract-version").read_text().strip()
        require(pin == "1.2.0", "canonical Contract B version drift")

    record = {
        "schema": "eb-v1-output-containment-subject-v1",
        "candidate_commit": head,
        "candidate_tree": git(root, "rev-parse", "HEAD^{tree}"),
        "corrected_from_commit": BASE,
        "package_version": VERSION,
        "frozen_authorities": frozen,
        "review_surface": review_surface,
        "review_surface_note": (
            "cli.py, execution.py, and review_cycle.py are the authorized review-cycle "
            "difference from 08ca896. Retrieval, package, Contract A, Contract B "
            "projection, schema, and carrier bytes stay frozen."
        ),
        "dependency_metadata_unchanged": True,
        "probe_sha256": PROBE_SHA256,
        "external_authorities": authorities,
        "changed_paths": git(root, "diff", "--name-only", BASE, head).splitlines(),
        "qualification_scope": (
            "Integrated reviewed-workflow candidate qualification; predecessor receipts "
            "remain historical."
        ),
    }
    write_json(args.output, record)
    print(json.dumps(record, indent=2, sort_keys=True))


def clean_environment() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    return env


def invoke(command: list[str], log: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
        env=clean_environment(),
    )
    log.parent.mkdir(parents=True, exist_ok=True)
    log.with_suffix(".stdout.txt").write_text(result.stdout, encoding="utf-8")
    log.with_suffix(".stderr.txt").write_text(result.stderr, encoding="utf-8")
    require(result.returncode == 0, f"{command[0]} exited {result.returncode}: {result.stderr}")
    return result


def runtime_record(checkout: Path) -> dict[str, Any]:
    checkout = checkout.resolve()
    prefix = Path(sys.prefix).resolve()
    require(sys.prefix != sys.base_prefix, "installed checks require an isolated virtualenv")
    require(not Path.cwd().resolve().is_relative_to(checkout), "execution cwd is in the checkout")
    require(
        not any(Path(path).resolve().is_relative_to(checkout) for path in sys.path if path),
        "checkout appears on the installed process import path",
    )
    modules = {}
    for name in ("evidence_bundler", "claim_audit_lab", "validators"):
        module = importlib.import_module(name)
        origin = Path(module.__file__).resolve()
        require(origin.is_relative_to(prefix), f"{name} was not imported from the isolated venv")
        modules[name] = origin.relative_to(prefix).as_posix()
    require(importlib.metadata.version("evidence-bundler") == VERSION, "wrong wheel version")
    require(importlib.import_module("evidence_bundler").__version__ == VERSION, "version drift")
    cfg = (prefix / "pyvenv.cfg").read_text(encoding="utf-8").lower()
    require("include-system-site-packages = false" in cfg, "venv inherits system packages")
    direct = importlib.metadata.distribution("evidence-bundler").read_text("direct_url.json")
    require(direct is not None, "installed wheel origin is unavailable")
    require(
        "archive_info" in json.loads(direct),
        "Evidence Bundler was not installed from an archive",
    )
    require(not json.loads(direct).get("dir_info", {}).get("editable"), "editable install detected")
    return {
        "python": sys.version,
        "module_origins_relative_to_venv": modules,
        "isolated_venv": True,
        "outside_checkout": True,
        "versions": {
            name: importlib.metadata.version(name)
            for name in (
                "evidence-bundler",
                "claim-audit-lab",
                "apparatus-contracts",
                "sentence-transformers",
                "torch",
                "faiss-cpu",
            )
        },
    }


def probe(args: argparse.Namespace) -> None:
    runtime = runtime_record(args.checkout)
    verify_probe(args.probe)
    require(not args.output.exists(), "probe output must be a fresh path")
    invoke([sys.executable, "-I", str(args.probe), str(args.output)], args.output.parent / "probe")
    rows = json.loads((args.output / "results.json").read_text(encoding="utf-8"))
    expected = {"claim_traversal", "source_traversal", "absolute_claim", "absolute_source"}
    require(len(rows) == 4 and {row["case"] for row in rows} == expected, "probe case drift")
    failures = []
    for row in rows:
        target = Path(row["outside_target"])
        safe = (
            row["exit_code"] != 0
            and row["outside_output"] is True
            and row["sentinel_overwritten"] is False
            and row["sentinel_before"] == row["sentinel_after"]
            and row["native_written"] is False
            and row["receipt_written"] is False
            and target.resolve().is_relative_to(args.output.resolve())
            and "sha256:" + digest(target) == row["sentinel_before"]
        )
        if not safe:
            failures.append(row["case"])
    record = {
        "schema": "eb-v1-installed-containment-replay-v1",
        "runtime": runtime,
        "probe_sha256": PROBE_SHA256,
        "case_count": len(rows),
        "failed_cases": failures,
        "passed": not failures,
    }
    write_json(args.output.parent / "containment-check.json", record)
    require(not failures, f"installed containment failures: {failures}")
    print(json.dumps(record, indent=2, sort_keys=True))


def bundle(args: argparse.Namespace) -> None:
    runtime = runtime_record(args.checkout)
    verify_probe(args.probe)
    args.output.mkdir(parents=True, exist_ok=False)
    cli = str(Path(sys.executable).parent / "evidence-bundler-v1")
    inspect = json.loads(invoke([cli, "inspect", "--json"], args.output / "inspect").stdout)
    require(inspect["package_version"] == VERSION, "inspect version drift")
    require(inspect["profile_id"] == "eb-v1-integration-10x3-rc0", "profile drift")
    require(inspect["config"]["candidate_depth"] == 10, "candidate depth drift")
    require(inspect["config"]["retained_k"] == 3, "retained-k drift")
    require(inspect["contract_b_authority"]["production_lock"] == CONTRACT_B, "Contract B drift")
    invoke([cli, "--version"], args.output / "version")

    wire = runpy.run_path(str(args.probe))["wire"]("claim-safe", "source-safe")
    input_path = args.output / "contract_a.json"
    write_json(input_path, wire)
    initial = args.output / "unreviewed"
    invoke([cli, "run", str(input_path), "--out-dir", str(initial)], args.output / "initial")
    native = json.loads((initial / "native_eb_v1_package.json").read_text(encoding="utf-8"))
    retained = [row for row in native["candidates"] if row["selection_state"] == "retained"]
    require(bool(retained), "positive control emitted no retained candidate")
    review_record = json.loads(
        (initial / "review_record.json").read_text(encoding="utf-8")
    )
    require(review_record["decisions"], "review template contains no retained decisions")
    for row in review_record["decisions"]:
        row["decision"] = "accepted"
        row["reason"] = "Qualification control: retained passage is accepted for boundary testing."
    review_path = args.output / "review.json"
    write_json(review_path, review_record)
    reviewed = args.output / "reviewed"
    invoke(
        [cli, "run", str(input_path), "--out-dir", str(reviewed), "--review", str(review_path)],
        args.output / "reviewed-run",
    )
    require(
        (reviewed / "applied_review_record.json").is_file(),
        "bound review was not preserved",
    )
    require(
        not (reviewed / "review_record.json").exists(),
        "applied run emitted a new review template",
    )

    stale = json.loads(json.dumps(review_record))
    stale["bindings"]["input_sha256"] = "sha256:" + "ab" * 32
    stale_path = args.output / "stale-review.json"
    write_json(stale_path, stale)
    stale_out = args.output / "stale-refused"
    stale_result = subprocess.run(
        [cli, "run", str(input_path), "--out-dir", str(stale_out), "--review", str(stale_path)],
        text=True,
        capture_output=True,
        check=False,
        env=clean_environment(),
    )
    (args.output / "stale-review.stdout.txt").write_text(stale_result.stdout, encoding="utf-8")
    (args.output / "stale-review.stderr.txt").write_text(stale_result.stderr, encoding="utf-8")
    require(stale_result.returncode != 0, "stale bound review unexpectedly succeeded")
    require(
        "refusing stale review" in stale_result.stderr + stale_result.stdout,
        "wrong stale-review refusal",
    )
    require(not stale_out.exists(), "stale review wrote output before refusal")

    emitted = reviewed / "contract_b"
    canonical = importlib.import_module("validators.verify_contract_integrity")
    report = canonical.verify(emitted, against_pin="1.2.0")
    canonical_record = {
        "passed": report.passed,
        "errors": report.errors,
        "checked_files": report.checked_files,
        "authority_commit": CONTRACT_B,
    }
    write_json(args.output / "canonical-validation.json", canonical_record)

    consumer = importlib.import_module("claim_audit_lab.contracts.factual_context")
    view = consumer.load_contract_b_intake(emitted, deviations_dir=args.output / "cal-deviations")
    require(view.extension_state == "present", "CAL did not consume the factual extension")
    require(
        view.intake_ledger is not None and view.semantic_context is not None,
        "CAL views absent",
    )
    actual = {
        (claim["claim_id"], passage["passage_id"])
        for claim in view.semantic_context["claims"]
        for passage in claim["admitted_passages"]
    }
    expected = {(row["proposition_id"], row["passage_id"]) for row in retained}
    cal_record = {
        "authority_commit": CAL,
        "extension_state": view.extension_state,
        "admitted_pairs": sorted(actual),
        "expected_admitted_pairs": sorted(expected),
        "passed": actual == expected,
    }
    write_json(args.output / "cal-intake.json", cal_record)
    write_json(args.output / "runtime.json", runtime)
    require(report.passed, f"canonical Contract B validation failed: {report.errors}")
    require(
        "extensions/contract-b-factual-context-v1.json" in report.checked_files,
        "canonical validator did not check the extension",
    )
    require(actual == expected, "CAL admitted passage identities differ from the explicit control")

    tampered = args.output / "tampered-contract-b"
    shutil.copytree(emitted, tampered)
    passage = sorted(tampered.glob("evidence/*/passages/*.yaml"))[0]
    relative = passage.relative_to(tampered)
    before_hash = digest(emitted / relative)
    yaml = importlib.import_module("yaml")
    payload = yaml.safe_load(passage.read_text(encoding="utf-8"))
    payload["passage_text"] += " TAMPERED NEGATIVE CONTROL."
    passage.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    negative_report = canonical.verify(tampered, against_pin="1.2.0")
    negative: dict[str, Any] = {
        "tampered_path": relative.as_posix(),
        "original_file_sha256": before_hash,
        "tampered_file_sha256": digest(passage),
        "valid_bundle_preserved": digest(emitted / relative) == before_hash,
        "canonical_rejected": not negative_report.passed,
        "canonical_errors": negative_report.errors,
        "cal_intake_returned": False,
        "cal_rejected": False,
    }
    try:
        consumer.load_contract_b_intake(
            tampered,
            deviations_dir=args.output / "tampered-cal-deviations",
        )
        negative["cal_intake_returned"] = True
    except consumer.BundleIntegrityError as exc:
        negative["cal_rejected"] = True
        negative["cal_error_type"] = type(exc).__name__
        negative["cal_error"] = str(exc)
    write_json(args.output / "tampered-passage-check.json", negative)
    require(negative["valid_bundle_preserved"], "negative control modified the valid bundle")
    require(negative["canonical_rejected"], "canonical validator accepted tampered passage bytes")
    require(negative["cal_rejected"], "CAL returned an intake view for tampered passage bytes")
    print(
        json.dumps(
            {"canonical": canonical_record, "cal": cal_record, "tampered_passage": negative},
            indent=2,
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    subject = subparsers.add_parser("identity")
    subject.add_argument("--checkout", type=Path, required=True)
    subject.add_argument("--expected-head", required=True)
    subject.add_argument("--probe", type=Path, required=True)
    subject.add_argument("--output", type=Path, required=True)
    subject.add_argument("--apparatus", type=Path)
    subject.add_argument("--cal", type=Path)
    subject.set_defaults(run=identity)
    for name, function in (("probe", probe), ("bundle", bundle)):
        installed = subparsers.add_parser(name)
        installed.add_argument("--checkout", type=Path, required=True)
        installed.add_argument("--probe", type=Path, required=True)
        installed.add_argument("--output", type=Path, required=True)
        installed.set_defaults(run=function)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
