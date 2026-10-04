"""Frozen, reusable installed-wheel probes of EB V1 output path effects only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import stat
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
A2_COMMIT = "529c92b49a34d5c610618551a8737f019f9fa332"
A2_VALIDATOR_BLOB = "42e5f5b3bf38d677445e9d01ea130ba604e53409"
BASELINE_COMMIT = "08ca896debd6d16fa21be2f178ed7cbe62395d00"
CASE_SPECS = [
    ("declared_root_traversal", "cli", "refuse"),
    ("declared_later_child_traversal", "cli", "refuse"),
    ("claim_case_alias", "cli", "portable_alias_refusal"),
    ("claim_nfc_alias", "cli", "portable_alias_refusal"),
    ("source_case_alias", "cli", "portable_alias_refusal"),
    ("source_nfc_alias", "cli", "portable_alias_refusal"),
    ("safe_unicode", "cli", "accept"),
    ("safe_ordinary_colons", "cli", "accept"),
    ("safe_percent_literals", "cli", "accept"),
    ("same_id_across_roles", "cli", "accept"),
    ("claim_dot", "cli", "accept"),
    ("claim_dotdot", "cli", "accept"),
    ("source_dot", "cli", "refuse"),
    ("source_dotdot", "cli", "refuse"),
    ("unprojected_path_source", "cli", "accept"),
    ("unsafe_nonretained_source", "cli", "refuse"),
    ("direct_empty_bundle_symlink", "api", "refuse"),
    ("direct_broken_receipt_symlink", "api", "refuse"),
    ("direct_existing_receipt_symlink", "api", "refuse"),
    ("direct_empty_bundle_directory", "api", "accept"),
    ("direct_empty_output_directory", "api", "accept"),
]


def sha(data: bytes | str) -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def save(path: Path, value: Any) -> None:
    path.write_bytes(canonical(value))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def snapshot(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}

    def visit(path: Path, label: str) -> None:
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            return
        if stat.S_ISLNK(mode):
            result[label] = {"kind": "symlink", "target": os.readlink(path)}
        elif stat.S_ISDIR(mode):
            result[label] = {"kind": "directory"}
            for entry in sorted(path.iterdir(), key=lambda item: item.name):
                visit(entry, entry.name if label == "." else label + "/" + entry.name)
        elif stat.S_ISREG(mode):
            data = path.read_bytes()
            result[label] = {"kind": "file", "bytes": len(data), "sha256": sha(data)}
        else:
            result[label] = {"kind": "other", "mode": mode}

    visit(root, ".")
    return result


def changes(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {name: {"before": before.get(name), "after": after.get(name)}
            for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)}


def wire(root_id: str = "claim-safe", source_ids: list[str] | None = None,
         child_ids: list[str] | None = None, unused_source: str | None = None) -> dict[str, Any]:
    root_text = "cobalt orchard protocol"
    sources = [{"source_id": ident, "media_type": "text/plain; charset=utf-8",
                "content": "cobalt orchard protocol synthetic record marker" + chr(97 + i)}
               for i, ident in enumerate(source_ids or ["source-safe"])]
    if unused_source is not None:
        sources.append({"source_id": unused_source, "media_type": "text/plain; charset=utf-8",
                        "content": "marigold petunia unrelated background"})
    for row in sources:
        row["content_sha256"] = "sha256:" + sha(row["content"])
    result = {"schema": "contract-a-wire-candidate-rc2", "handoff_id": "additional-path-probe",
              "producer": {"producer_id": "independent-output-probe", "producer_version": "1"},
              "work": {"work_id": "synthetic-output-effects-only"},
              "root_proposition": {"proposition_id": root_id, "text": root_text,
                                   "text_sha256": "sha256:" + sha(root_text)},
              "decomposition": {"state": "not_decomposed"}, "sources": sources}
    if child_ids is not None:
        children = []
        for index, ident in enumerate(child_ids, 1):
            text = root_text + " child " + str(index)
            children.append({"proposition_id": ident, "text": text,
                             "text_sha256": "sha256:" + sha(text), "sequence": index})
        result["decomposition"] = {"state": "declared", "decomposition_id": "declared-control",
                                   "operator": "all_of", "children": children}
    # Contract A's canonical hash excludes the trailing LF and its own hash field.
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False)
    result["handoff_sha256"] = "sha256:" + sha(payload)
    return result


def case_input(name: str) -> dict[str, Any]:
    if name == "declared_root_traversal":
        return wire("../../../outside/root-sentinel", child_ids=["child-1", "child-2"])
    if name == "declared_later_child_traversal":
        return wire(child_ids=["child-safe", "../../../outside/child-sentinel"])
    if name == "claim_case_alias":
        return wire(child_ids=["claim-Alpha", "claim-alpha"])
    if name == "claim_nfc_alias":
        return wire(child_ids=["claim-caf\u00e9", "claim-cafe\u0301"])
    if name == "source_case_alias":
        return wire(source_ids=["source-Alpha", "source-alpha"])
    if name == "source_nfc_alias":
        return wire(source_ids=["source-caf\u00e9", "source-cafe\u0301"])
    if name == "safe_unicode":
        return wire("主張-δ", ["資料-λ"])
    if name == "safe_ordinary_colons":
        return wire("claim:root", ["source:item"])
    if name == "safe_percent_literals":
        return wire("%2e%2e%2fclaim", ["%2e%2e%2fsource"])
    if name == "same_id_across_roles":
        return wire("shared-id", ["shared-id"])
    if name == "claim_dot":
        return wire(".")
    if name == "claim_dotdot":
        return wire("..")
    if name == "source_dot":
        return wire(source_ids=["."])
    if name == "source_dotdot":
        return wire(source_ids=[".."])
    if name == "unprojected_path_source":
        return wire(unused_source="../../../outside/unprojected-source")
    if name == "unsafe_nonretained_source":
        return wire(source_ids=["!safe-a", "!safe-b", "!safe-c",
                                "../../../outside/source-sentinel"])
    return wire()


def canonical_validator(contracts_root: Path) -> Any:
    blob = git(contracts_root, "rev-parse", A2_COMMIT + ":validators/contract_a_rc2.py")
    if blob != A2_VALIDATOR_BLOB:
        raise RuntimeError("canonical A2 validator blob mismatch")
    source = subprocess.check_output(["git", "-C", str(contracts_root), "show",
                                      A2_COMMIT + ":validators/contract_a_rc2.py"], text=True)
    scope = {"__name__": "exact_a2_probe_authority"}
    exec(compile(source, "<exact-canonical-A2-validator>", "exec"), scope)
    return scope["validate_candidate"]


def identity(sut_repo: Path) -> dict[str, Any]:
    import evidence_bundler
    installed_root = Path(evidence_bundler.__file__).resolve().parent
    source_root = sut_repo / "src" / "evidence_bundler"
    source = {p.relative_to(source_root).as_posix(): sha(p.read_bytes())
              for p in sorted(source_root.rglob("*.py"))}
    installed = {p.relative_to(installed_root).as_posix(): sha(p.read_bytes())
                 for p in sorted(installed_root.rglob("*.py"))}
    carrier_rel = "production_v1/data/contract_b_compatibility_carrier.json"
    source[carrier_rel] = sha((source_root / carrier_rel).read_bytes())
    installed[carrier_rel] = sha((installed_root / carrier_rel).read_bytes())
    mismatch = changes(source, installed)
    distribution = importlib.metadata.distribution("evidence-bundler")
    direct_url_text = distribution.read_text("direct_url.json")
    return {"commit": git(sut_repo, "rev-parse", "HEAD"),
            "tree": git(sut_repo, "rev-parse", "HEAD^{tree}"),
            "checkout_changes": git(sut_repo, "status", "--porcelain"),
            "sut_repo": str(sut_repo), "installed_root": str(installed_root),
            "package_version": importlib.metadata.version("evidence-bundler"),
            "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
            "source_sha256": source, "installed_sha256": installed,
            "installed_source_mismatches": mismatch,
            "installed_wheel_reference": json.loads(direct_url_text) if direct_url_text else None,
            "distributions": sorted(str(d.metadata["Name"]) + "==" + d.version
                                    for d in importlib.metadata.distributions())}


def host_names(base: Path) -> dict[str, Any]:
    root = base / "host-filename-observations"
    root.mkdir()
    records = {}
    for label, names in [("case", ("Alpha", "alpha")), ("canonical_unicode", ("caf\u00e9", "cafe\u0301"))]:
        directory = root / label
        directory.mkdir()
        (directory / names[0]).write_bytes(b"FIRST_NAME_CONTROL\n")
        try:
            with (directory / names[1]).open("xb") as handle:
                handle.write(b"SECOND_NAME_CONTROL\n")
            aliases = False
        except FileExistsError:
            aliases = True
        records[label] = {"names": names, "exclusive_second_name_collision": aliases,
                          "enumerated_names": sorted(p.name for p in directory.iterdir())}
    return records


def prepare(case: Path, name: str, run_root: Path) -> tuple[Path, Path]:
    outside = case / "outside"
    outside.mkdir()
    (outside / "guard.txt").write_bytes(b"PROBE_OWNED_GUARD_DO_NOT_CHANGE\n")
    out = case / "requested-output"
    if name in {"declared_root_traversal", "declared_later_child_traversal"}:
        sentinel = outside / ("root-sentinel.yaml" if name == "declared_root_traversal" else "child-sentinel.yaml")
        sentinel.write_bytes(b"PROBE_OWNED_CLAIM_SENTINEL\n")
        raw_id = case_input(name)["root_proposition"]["proposition_id"] if name == "declared_root_traversal" else case_input(name)["decomposition"]["children"][1]["proposition_id"]
        target = out / "contract_b" / "claims" / (raw_id + ".yaml")
        require(target.resolve() == sentinel.resolve() and target.resolve().is_relative_to(run_root),
                "claim probe target escaped its owned sentinel")
    if name == "unsafe_nonretained_source":
        source_dir = outside / "source-sentinel"
        source_dir.mkdir()
        (source_dir / "source_profile.yaml").write_bytes(b"PROBE_OWNED_SOURCE_SENTINEL\n")
        target = out / "contract_b" / "evidence" / "../../../outside/source-sentinel" / "source_profile.yaml"
        require(target.resolve() == (source_dir / "source_profile.yaml").resolve()
                and target.resolve().is_relative_to(run_root),
                "source probe target escaped its owned sentinel")
    if name.startswith("direct_"):
        out.mkdir()
    if name == "direct_empty_bundle_symlink":
        target = outside / "bundle-target"
        target.mkdir()
        require(target.resolve().is_relative_to(run_root), "bundle link target is not probe-owned")
        (out / "contract_b").symlink_to(target, target_is_directory=True)
    if name in {"direct_broken_receipt_symlink", "direct_existing_receipt_symlink"}:
        target = outside / "receipt-target.json"
        if name == "direct_existing_receipt_symlink":
            target.write_bytes(b"PROBE_OWNED_RECEIPT_SENTINEL\n")
        require(target.resolve().is_relative_to(run_root), "receipt link target is not probe-owned")
        (out / "projection_receipt.json").symlink_to(target)
    if name == "direct_empty_bundle_directory":
        (out / "contract_b").mkdir()
    return out, outside


def inspect_success(out: Path, expected: dict[str, Any], entry: str) -> dict[str, Any]:
    import yaml
    errors = []
    expected_claims = [expected["root_proposition"]["proposition_id"]]
    expected_claims += [row["proposition_id"] for row in expected["decomposition"].get("children", [])]
    expected_sources = [row["source_id"] for row in expected["sources"]
                        if row["content"].startswith("cobalt orchard protocol")]
    claims = []
    for path in (out / "contract_b" / "claims").glob("*.yaml"):
        obj = yaml.safe_load(path.read_text(encoding="utf-8"))
        claims.append(obj["claim_id"])
        if path.name != obj["claim_id"] + ".yaml":
            errors.append("claim filename/record identity mismatch")
    source_ids = []
    for path in (out / "contract_b" / "evidence").iterdir():
        if path.is_dir():
            obj = yaml.safe_load((path / "source_profile.yaml").read_text(encoding="utf-8"))
            source_ids.append(obj["source_id"])
            if path.name != obj["source_id"]:
                errors.append("source directory/record identity mismatch")
    if sorted(claims) != sorted(expected_claims):
        errors.append("projected claim IDs differ from exact input IDs")
    if sorted(source_ids) != sorted(expected_sources):
        errors.append("projected source IDs differ from nominated input IDs")
    extension = json.loads((out / "contract_b" / "extensions" / "contract-b-factual-context-v1.json").read_text())
    if sorted(row["claim_id"] for row in extension["claims"]) != sorted(expected_claims):
        errors.append("extension claim references differ from exact input IDs")
    if sorted(row["source_id"] for row in extension["sources"]) != sorted(expected_sources):
        errors.append("extension source references differ from nominated input IDs")
    if entry == "cli":
        native = json.loads((out / "native_eb_v1_package.json").read_text())
        if native["contract_a"] != expected:
            errors.append("native embedded Contract A was changed")
    receipt = json.loads((out / "projection_receipt.json").read_text())
    return {"errors": errors, "claim_ids": sorted(claims), "source_ids": sorted(source_ids),
            "receipt_sha256": receipt["receipt_sha256"]}


def worker(input_path: Path, out: Path) -> int:
    from importlib.resources import files
    from evidence_bundler.v1 import build_package
    from evidence_bundler.v1.contract_b import INTEGRATION_CONFIG, project_contract_b
    try:
        obj = json.loads(input_path.read_text(encoding="utf-8"))
        package = build_package(contract_a=obj, config=INTEGRATION_CONFIG)
        carrier = json.loads(files("evidence_bundler.production_v1").joinpath(
            "data/contract_b_compatibility_carrier.json").read_text(encoding="utf-8"))
        receipt = project_contract_b(package=package, compatibility_carrier=carrier, out_dir=out)
        print(json.dumps({"status": "returned", "receipt_sha256": receipt["receipt_sha256"]}))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "raised", "exception_type": type(exc).__name__, "error": str(exc)}))
        traceback.print_exc()
        return 1


def refusal_classification(entry: str, stdout: str, stderr: str) -> dict[str, Any]:
    if entry == "api":
        try:
            outcome = json.loads(stdout)
        except json.JSONDecodeError:
            outcome = {}
        recognized = (outcome.get("status") == "raised" and
                      outcome.get("exception_type") == "ContractBProjectionError")
        return {"recognized_projection_refusal": recognized, "api_outcome": outcome}
    click_lines = [line for line in stderr.splitlines() if line.startswith("Error: ")]
    path_words = re.compile(r"path|output|directory|filename|component|symlink|collision|represent", re.I)
    recognized = bool(click_lines) and any(path_words.search(line) for line in click_lines)
    return {"recognized_projection_refusal": recognized and "Traceback (most recent call last)" not in stderr,
            "cli_error_lines": click_lines,
            "classification_limit": "Click hides the underlying exception class; path/output wording is recorded."}


def run(args: argparse.Namespace) -> int:
    freeze_path = Path(args.freeze).resolve()
    frozen = json.loads(freeze_path.read_text())
    script = Path(__file__).resolve()
    design_path = freeze_path.parent / frozen["design_file"]
    if sha(script.read_bytes()) != frozen["script_sha256"] or sha(design_path.read_bytes()) != frozen["design_sha256"]:
        raise RuntimeError("script/design does not match pre-execution freeze")
    if [list(row) for row in CASE_SPECS] != frozen["cases"]:
        raise RuntimeError("case list does not match pre-execution freeze")
    supplied_base = Path(args.run_dir).absolute()
    if os.path.lexists(supplied_base):
        raise RuntimeError("refusing to reuse an existing run directory")
    base = supplied_base.resolve()
    require(base != freeze_path.parent and base.is_relative_to(freeze_path.parent),
            "run directory must be a new descendant of the frozen review directory")
    if os.path.lexists(base):
        raise RuntimeError("refusing to reuse an existing canonical run directory")
    base.mkdir(parents=True, exist_ok=False)
    runtime = identity(Path(args.sut_repo).resolve())
    save(base / "runtime.json", runtime)
    if runtime["installed_source_mismatches"]:
        raise RuntimeError("installed source does not match specified checkout; see runtime.json")
    validate_a2 = canonical_validator(Path(args.contracts_root).resolve())
    fs = host_names(base)
    save(base / "host-filesystem.json", fs)
    invocation = {"label": args.label, "started_at_utc": datetime.now(timezone.utc).isoformat(),
                  "arguments": vars(args), "design_freeze_sha256": sha(freeze_path.read_bytes()),
                  "script_sha256": frozen["script_sha256"], "design_sha256": frozen["design_sha256"]}
    save(base / "invocation.json", invocation)
    records = []
    (base / "cases").mkdir()
    env = dict(os.environ, PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1",
               TRANSFORMERS_OFFLINE="1", EVIDENCE_BUNDLER_RUN_RERANKER_SMOKE="0")
    env.pop("PYTHONPATH", None)
    for name, entry, expectation in CASE_SPECS:
        case = base / "cases" / name
        case.mkdir()
        obj = case_input(name)
        require(validate_a2(obj) is obj, "canonical A2 did not preserve synthetic input")
        input_path = case / "contract_a.json"
        save(input_path, obj)
        out, outside = prepare(case, name, base)
        before_out, before_outside = snapshot(out), snapshot(outside)
        command = ([str(Path(sys.executable).parent / "evidence-bundler-v1"), "run", str(input_path), "--out-dir", str(out)]
                   if entry == "cli" else [sys.executable, str(script), "_worker", str(input_path), str(out)])
        execution_problem = None
        try:
            result = subprocess.run(command, cwd=case, env=env, capture_output=True, text=True,
                                    errors="replace", timeout=60, check=False)
        except subprocess.TimeoutExpired as exc:
            execution_problem = "product process exceeded the frozen 60-second limit"
            captured_out = exc.stdout or b""
            captured_err = exc.stderr or b""
            result = subprocess.CompletedProcess(command, -999,
                captured_out.decode("utf-8", "replace") if isinstance(captured_out, bytes) else captured_out,
                captured_err.decode("utf-8", "replace") if isinstance(captured_err, bytes) else captured_err)
        except OSError as exc:
            execution_problem = "process launch failed: " + str(exc)
            result = subprocess.CompletedProcess(command, -998, "", execution_problem)
        (case / "stdout.txt").write_text(result.stdout, encoding="utf-8")
        (case / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        save(case / "process.json", {"command": command, "cwd": str(case), "exit_code": result.returncode})
        after_out, after_outside = snapshot(out), snapshot(outside)
        out_changes = changes(before_out, after_out)
        outside_changes = changes(before_outside, after_outside)
        classification = refusal_classification(entry, result.stdout, result.stderr)
        refuse_clean = (result.returncode != 0 and not out_changes and not outside_changes
                        and classification["recognized_projection_refusal"])
        observed_success = None
        if result.returncode == 0:
            try:
                observed_success = inspect_success(out, obj, entry)
            except Exception as exc:
                observed_success = {"errors": ["successful output could not be inspected"],
                                    "exception_type": type(exc).__name__, "error": str(exc),
                                    "traceback": traceback.format_exc()}
        literal_success = result.returncode == 0 and not outside_changes and not observed_success["errors"]
        passed = literal_success if expectation == "accept" else refuse_clean
        row = {"case": name, "entry": entry, "expectation": expectation,
               "required_property_pass": passed, "canonical_A2_accepts_unchanged": True,
               "execution_problem": execution_problem,
               "exit_code": result.returncode, "command": command, "cwd": str(case),
               "input_sha256": sha(input_path.read_bytes()),
               "output_before": before_out, "output_after": after_out, "output_changes": out_changes,
               "owned_outside_before": before_outside, "owned_outside_after": after_outside,
               "owned_outside_changes": outside_changes, "refused_without_mutation": refuse_clean,
               "refusal_classification": classification,
               "literal_success_without_outside_mutation": literal_success,
               "native_written": (out / "native_eb_v1_package.json").is_file(),
               "receipt_is_file": (out / "projection_receipt.json").is_file(),
               "successful_output_identity": observed_success}
        if expectation == "portable_alias_refusal":
            label = "case" if name.endswith("case_alias") else "canonical_unicode"
            row["host_pair_actually_aliases"] = fs[label]["exclusive_second_name_collision"]
            row["host_local_safety_pass"] = refuse_clean or literal_success
            row["interpretation_limit"] = "Portable-refusal policy scored separately; this is not a macOS observation."
        if name == "unsafe_nonretained_source" and row["native_written"]:
            native = json.loads((out / "native_eb_v1_package.json").read_text())
            row["unsafe_source_candidate_states"] = [
                {key: r[key] for key in ["source_id", "nomination_rank", "selection_state", "admission_state"]}
                for r in native["candidates"] if r["source_id"].startswith("../../../")]
            row["unsafe_source_rank_four_fixture_confirmed"] = row["unsafe_source_candidate_states"] == [{
                "source_id": "../../../outside/source-sentinel", "nomination_rank": 4,
                "selection_state": "not_retained", "admission_state": "not_applicable"}]
        save(case / "record.json", row)
        records.append(row)
        save(base / "results.json", records)
        print(json.dumps({"case": name, "pass": passed, "exit_code": result.returncode,
                          "output_changed": bool(out_changes), "outside_changed": bool(outside_changes)},
                         sort_keys=True), flush=True)
        if execution_problem:
            save(base / "stopped.json", {"case": name, "reason": execution_problem})
            save(base / "partial-file-manifest.json", snapshot(base))
            raise RuntimeError(execution_problem)
    summary = {"schema": "eb-v1-additional-path-probe-results-v1", "label": args.label,
               "finished_at_utc": datetime.now(timezone.utc).isoformat(), "sut_commit": runtime["commit"],
               "script_sha256": frozen["script_sha256"], "design_sha256": frozen["design_sha256"],
               "cases": len(records), "passed": sum(r["required_property_pass"] for r in records),
               "failed": [r["case"] for r in records if not r["required_property_pass"]],
               "outside_mutation_cases": [r["case"] for r in records if r["owned_outside_changes"]],
               "portable_policy_failures": [r["case"] for r in records if r["expectation"] == "portable_alias_refusal" and not r["required_property_pass"]],
               "results_sha256": sha((base / "results.json").read_bytes())}
    save(base / "summary.json", summary)
    save(base / "file-manifest.json", snapshot(base))
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("run")
    p.add_argument("--freeze", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--sut-repo", required=True)
    p.add_argument("--contracts-root", required=True)
    p.add_argument("--label", required=True)
    p = sub.add_parser("_worker")
    p.add_argument("input_path")
    p.add_argument("out_dir")
    args = parser.parse_args()
    return worker(Path(args.input_path), Path(args.out_dir)) if args.mode == "_worker" else run(args)


if __name__ == "__main__":
    raise SystemExit(main())
