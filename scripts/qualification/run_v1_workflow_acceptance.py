#!/usr/bin/env python3
"""Synthetic operator-workflow test apparatus; no product snapshot-binding guarantee."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "research/eb_v1_workflow_acceptance_20261004"
NATIVE = "native_eb_v1_package.json"
STATES = {"accepted", "rejected", "needs-review"}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canon(value, newline=False):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")
    return data + b"\n" if newline else data


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path):
    return sha(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")
    with path.open("xb") as stream:
        stream.write(data)


def safe(root, relative):
    path = root / relative
    need(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
         f"unsafe relative path: {relative}")
    need(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
         f"escaped path: {relative}")
    return path


def inside_checkout(path):
    directory = path
    while not directory.exists():
        directory = directory.parent
    result = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True, check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def hashes(root):
    return {p.relative_to(root).as_posix(): file_sha(p)
            for p in sorted(root.rglob("*")) if p.is_file()}


def verify_kit(kit):
    freeze = read(kit / "FREEZE.json")
    members = freeze["files"]
    need(len(members) == 15 and len({m["path"] for m in members}) == 15, "kit member count")
    for member in members:
        path = safe(kit, member["path"])
        need(file_sha(path) == member["sha256"] and path.stat().st_size == member["bytes"],
             f"kit changed: {member['path']}")
    need(set(hashes(kit)) == {m["path"] for m in members} | {"FREEZE.json", "SHA256SUMS"},
         "kit contains missing/extra files")
    need(sha(canon({"schema": "eb-synthetic-operator-kit-closure-v1", "files": members}))
         == freeze["closure_sha256"], "kit closure mismatch")
    need(file_sha(kit / "SHA256SUMS") == freeze["sha256sums_sha256"], "kit checksums changed")
    for field, name in [("design_sha256", "DESIGN.json"), ("manifest_sha256", "MANIFEST.json"),
                        ("expected_opportunities_sha256", "EXPECTED-OPPORTUNITIES.json")]:
        need(file_sha(kit / name) == freeze[field], f"kit binding mismatch: {name}")
    return freeze


def invoke(cli, arguments, run, log):
    env = dict(os.environ, PYTHONNOUSERSITE="1")
    env.pop("PYTHONPATH", None)
    started = time.monotonic()
    try:
        result = subprocess.run([cli, *arguments], cwd=run, env=env, capture_output=True,
                                timeout=120, check=False)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code = exc.stdout or b"", exc.stderr or b"", 124
    write(log.with_suffix(".stdout.txt"), stdout)
    write(log.with_suffix(".stderr.txt"), stderr)
    write(log.with_suffix(".json"), {"command": [cli, *arguments], "returncode": code,
          "elapsed_seconds": round(time.monotonic() - started, 6),
          "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr)})
    need(code == 0, f"CLI failed ({code}); preserved {log}.json")
    return stdout


def retained(package):
    rows = [r for r in package["candidates"] if r["selection_state"] == "retained"]
    pairs = [(r["proposition_id"], r["passage_id"]) for r in rows]
    need(len(pairs) == len(set(pairs)), "duplicate retained pair")
    return rows


def check_outputs(directory, input_value):
    package = read(directory / NATIVE)
    payload = {k: v for k, v in package.items() if k != "package_sha256"}
    need(sha(canon(payload, True)) == package["package_sha256"], "native intrinsic hash")
    need(package["contract_a"] == input_value, "native input snapshot changed")
    sources = {s["source_id"]: s for s in input_value["sources"]}
    for row in package["candidates"]:
        source = sources[row["source_id"]]
        need(sha(source["content"].encode()) == source["content_sha256"]
             == row["source_content_sha256"], "source hash binding")
        start, end = row["char_start"], row["char_end"]
        need(type(start) is type(end) is int and 0 <= start <= end <= len(source["content"]),
             "passage span domain")
        need(source["content"][start:end] == row["text"]
             and sha(row["text"].encode()) == row["passage_sha256"], "passage text/span/hash")
    receipt = read(directory / "projection_receipt.json")
    need(receipt["native_package_sha256"] == package["package_sha256"], "projection native binding")
    need(sha(canon({k: v for k, v in receipt.items() if k != "receipt_sha256"}, True))
         == receipt["receipt_sha256"], "projection receipt hash")
    bundle = directory / "contract_b"
    need((bundle / "CONTRACT_VERSION").read_text().strip() == "1.2.0", "Contract B version")
    expected = {}
    for line in (bundle / "SHA256SUMS").read_text().splitlines():
        digest, rel = line.split(maxsplit=1)
        need(rel not in expected, "duplicate Contract B checksum path")
        expected[rel] = "sha256:" + digest
        need(file_sha(safe(bundle, rel)) == expected[rel], f"Contract B checksum: {rel}")
    actual = {k: v for k, v in hashes(bundle).items()
              if Path(k).name != "SHA256SUMS" and not k.startswith("deviations/")}
    need(actual == expected, "Contract B checksum coverage")
    return package


def review_packet(case_id, package, bindings):
    lines = [f"# Operator review: {case_id}", "", "Apparatus packet; no evaluation oracle.",
             "", "Bindings: " + json.dumps(bindings, sort_keys=True), "",
             "Root: " + package["contract_a"]["root_proposition"]["text"], ""]
    for target in package["primary_targets"]:
        lines += [f"## {target['proposition_id']}", "", target["text"], ""]
        rows = [r for r in retained(package) if r["proposition_id"] == target["proposition_id"]]
        if not rows:
            lines += ["No retained candidate for this target. Record the gap.", ""]
        for row in rows:
            fields = {k: row[k] for k in ("passage_id", "source_id", "char_start", "char_end",
                                          "source_content_sha256", "passage_sha256")}
            lines += [json.dumps(fields, sort_keys=True), "",
                      *["> " + line for line in row["text"].splitlines()], ""]
    return ("\n".join(lines) + "\n").encode("utf-8")


def prepare(args, run, stage):
    kit = args.kit.resolve()
    freeze = verify_kit(kit)
    cli = str(Path(shutil.which(args.cli) or args.cli).resolve())
    need(Path(cli).is_file(), "installed CLI not found")
    inspected = invoke(cli, ["inspect", "--json"], run, run / "logs/inspect")
    json.loads(inspected)
    state = {"schema": "eb-workflow-prepare-v1", "kit": str(kit),
             "kit_freeze_sha256": file_sha(kit / "FREEZE.json"),
             "kit_closure": freeze["closure_sha256"], "helper_sha256": file_sha(Path(__file__)),
             "cli": cli, "cli_sha256": file_sha(Path(cli)),
             "operator_declared_subject": args.subject, "inspect_sha256": sha(inspected),
             "apparatus_bindings_only": True, "cases": []}
    manifest = read(kit / "MANIFEST.json")
    need([c["case_id"] for c in manifest["cases"]] == [f"p{i:02d}" for i in range(1, 9)],
         "expected eight ordered fixture cases")
    for case in manifest["cases"]:
        cid = case["case_id"]
        input_path = run / f"inputs/{cid}.contract-a.json"
        write(input_path, safe(kit, case["path"]).read_bytes())
        destination = run / f"unreviewed/{cid}"
        invoke(cli, ["run", str(input_path), "--out-dir", str(destination)], run,
               run / f"logs/{cid}-unreviewed")
        package = check_outputs(destination, read(input_path))
        need(all(r["admission_state"] == "needs-review" for r in retained(package)),
             "unreviewed retained row was already admitted/rejected")
        bindings = {"input_sha256": file_sha(input_path),
                    "native_file_sha256": file_sha(destination / NATIVE),
                    "native_package_sha256": package["package_sha256"],
                    "inspect_sha256": sha(inspected)}
        packet_path = run / f"review-packets/{cid}.md"
        write(packet_path, review_packet(cid, package, bindings))
        bindings["review_packet_sha256"] = file_sha(packet_path)
        review = {"schema": "eb-workflow-review-v1", "case_id": cid, "bindings": bindings,
                  "reviewer": "", "elapsed_seconds": None, "manual_friction": "",
                  "coverage_notes": {t["proposition_id"]: "" for t in package["primary_targets"]},
                  "decisions": [{"proposition_id": r["proposition_id"],
                                 "passage_id": r["passage_id"], "decision": "needs-review",
                                 "reason": ""} for r in retained(package)]}
        write(run / f"reviews/{cid}.json", review)
        entry = {"case_id": cid, "bindings": bindings, "unreviewed_files": hashes(destination)}
        state["cases"].append(entry)
    write(run / "PREPARED.json", state)
    print(f"Prepared {len(state['cases'])} cases; fill reviews/*.json before replay.")


def check_review(review, entry, package):
    need(set(review) == {"schema", "case_id", "bindings", "reviewer", "elapsed_seconds",
                         "manual_friction", "coverage_notes", "decisions"}, "review field shape")
    need(review["schema"] == "eb-workflow-review-v1" and review["case_id"] == entry["case_id"],
         "review case/schema binding")
    need(review["bindings"] == entry["bindings"], "review snapshot binding changed")
    for key in ("reviewer", "manual_friction"):
        need(isinstance(review[key], str) and review[key].strip(), f"blank {key}")
    elapsed = review["elapsed_seconds"]
    need(type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0, "review time")
    notes = review["coverage_notes"]
    need(set(notes) == {t["proposition_id"] for t in package["primary_targets"]}, "target notes")
    need(all(isinstance(n, str) and n.strip() for n in notes.values()), "blank coverage rationale")
    decisions = {}
    for row in review["decisions"]:
        need(set(row) == {"proposition_id", "passage_id", "decision", "reason"}, "review row shape")
        pair = (row["proposition_id"], row["passage_id"])
        need(pair not in decisions and row["decision"] in STATES, "duplicate/illegal decision")
        need(isinstance(row["reason"], str) and row["reason"].strip(), "blank review rationale")
        decisions[pair] = row["decision"]
    need(set(decisions) == {(r["proposition_id"], r["passage_id"]) for r in retained(package)},
         "review pairs must exactly cover the original retained pair set")
    return decisions


def checked_state(run):
    state = read(run / "PREPARED.json")
    kit = Path(state["kit"])
    verify_kit(kit)
    need(file_sha(kit / "FREEZE.json") == state["kit_freeze_sha256"], "kit freeze changed")
    need(file_sha(Path(__file__)) == state["helper_sha256"], "helper changed after prepare")
    need(file_sha(run / "logs/inspect.stdout.txt") == state["inspect_sha256"], "inspect changed")
    for entry in state["cases"]:
        cid, binding = entry["case_id"], entry["bindings"]
        need(file_sha(run / f"inputs/{cid}.contract-a.json") == binding["input_sha256"], "input")
        need(hashes(run / f"unreviewed/{cid}") == entry["unreviewed_files"], "unreviewed drift")
        packet = run / f"review-packets/{cid}.md"
        need(file_sha(packet) == binding["review_packet_sha256"], "packet changed")
    return state


def coverage(package, review):
    targets = {}
    for target in package["primary_targets"]:
        rows = [r for r in retained(package) if r["proposition_id"] == target["proposition_id"]]
        counts = {s: sum(r["admission_state"] == s for r in rows) for s in sorted(STATES)}
        targets[target["proposition_id"]] = {**counts, "retained": len(rows),
            "gap": counts["accepted"] == 0,
            "manual_note": review["coverage_notes"][target["proposition_id"]]}
    return {"case_id": review["case_id"], "apparatus_summary_only": True, "targets": targets,
            "all_of": package["contract_a"]["decomposition"]["state"] == "declared",
            "all_targets_have_admitted_evidence": all(not t["gap"] for t in targets.values()),
            "manual_friction": review["manual_friction"],
            "elapsed_seconds": review["elapsed_seconds"]}


def check_replay(before, after, decisions):
    expected = deepcopy(before)
    for row in retained(expected):
        row["admission_state"] = decisions[(row["proposition_id"], row["passage_id"])]
    need({k: v for k, v in expected.items() if k != "package_sha256"}
         == {k: v for k, v in after.items() if k != "package_sha256"}, "non-admission replay drift")


def replay(args, run, stage):
    state = checked_state(run)
    validated = []
    for entry in state["cases"]:
        cid = entry["case_id"]
        package = read(run / f"unreviewed/{cid}/{NATIVE}")
        review = read(run / f"reviews/{cid}.json")
        decisions = check_review(review, entry, package)
        validated.append((cid, package, review, decisions))
    need(file_sha(Path(state["cli"])) == state["cli_sha256"], "CLI executable changed")
    inspected = invoke(state["cli"], ["inspect", "--json"], run, stage / "inspect")
    need(sha(inspected) == state["inspect_sha256"], "live inspect binding changed")
    for cid, _, _, _ in validated:
        write(stage / f"reviews/{cid}.json", (run / f"reviews/{cid}.json").read_bytes())
    write(stage / "REVIEW-FREEZE.json", {"prepared_sha256": file_sha(run / "PREPARED.json"),
          "review_hashes": hashes(stage / "reviews"),
          "frozen_at_utc": datetime.now(UTC).isoformat(),
          "apparatus_bindings_only": True})
    summaries = []
    for cid, before, review, decisions in validated:
        admission = {"schema": "evidence-bundler-admission-v1", "decisions": [
            {"proposition_id": pair[0], "passage_id": pair[1], "decision": decision}
            for pair, decision in sorted(decisions.items())]}
        path = stage / f"admissions/{cid}.json"
        write(path, admission)
        destination = stage / f"outputs/{cid}"
        input_path = run / f"inputs/{cid}.contract-a.json"
        invoke(state["cli"], ["run", str(input_path), "--out-dir", str(destination),
               "--admission", str(path)], run, stage / f"logs/{cid}")
        after = check_outputs(destination, read(input_path))
        check_replay(before, after, decisions)
        summaries.append(coverage(after, review))
    write(stage / "COVERAGE.json", {"cases": summaries,
          "meaning": "Helper-created counts and manual notes; no semantic truth or EB UI."})
    write(stage / "RESULT.json", {"status": "REPLAY_COMPLETE",
          "output_hashes": hashes(stage / "outputs"),
          "coverage_sha256": file_sha(stage / "COVERAGE.json"),
          "contract_b_checks": "File checksum coverage and receipt hash/native binding only; "
          "accepted-link semantics require the separate canonical consumer check.",
          "review_freeze_sha256": file_sha(stage / "REVIEW-FREEZE.json")})
    print("Reviews frozen and replayed; evaluate is now available.")


def gate(counts, expected):
    positive = {t: counts.get(t, 0) > 0 for t in expected["mandatory_adequate_targets"]}
    gaps = {t: counts.get(t, 0) == 0 for t in expected["mandatory_gap_targets"]}
    return {"passed": all(positive.values()) and all(gaps.values()),
            "positives": positive, "gaps": gaps}


def evaluate(args, run, stage):
    state = checked_state(run)
    frozen = read(run / "replay/REVIEW-FREEZE.json")
    result = read(run / "replay/RESULT.json")
    need(file_sha(run / "PREPARED.json") == frozen["prepared_sha256"], "prepared state changed")
    need(hashes(run / "replay/reviews") == frozen["review_hashes"]
         == hashes(run / "reviews"), "reviews changed after freeze")
    need(file_sha(run / "replay/REVIEW-FREEZE.json") == result["review_freeze_sha256"], "freeze")
    need(hashes(run / "replay/outputs") == result["output_hashes"], "reviewed outputs changed")
    need(file_sha(run / "replay/COVERAGE.json") == result["coverage_sha256"], "coverage changed")
    summary = read(run / "replay/COVERAGE.json")
    expected = read(Path(state["kit"]) / "EXPECTED-OPPORTUNITIES.json")
    counts = {t: row["accepted"] for c in summary["cases"] for t, row in c["targets"].items()}
    outcome = gate(counts, expected)
    cases = {c["case_id"]: c for c in summary["cases"]}
    parent_ok = (cases["p03"]["all_targets_have_admitted_evidence"]
                 and not cases["p06"]["all_targets_have_admitted_evidence"])
    # Fabricated evaluator controls, not extra product/reviewer executions.
    reject = gate({t: 0 for t in counts}, expected)
    accept = gate({t: int(t != "clm-p08") for t in counts}, expected)
    need(not reject["passed"] and not accept["passed"], "weak evaluator control passed")
    passed = outcome["passed"] and parent_ok
    disposition = ("PASS" if passed else "FAIL") + "_SYNTHETIC_OPERATOR_ACCEPTANCE"
    write(stage / "RESULT.json", {"disposition": disposition, "kit_closure": state["kit_closure"],
          "gate": outcome, "parent_boundaries": bool(parent_ok),
          "limitation_observation": cases["p07"],
          "fabricated_gate_controls": {"always_reject": reject, "always_accept": accept},
          "review_freeze_sha256": result["review_freeze_sha256"],
          "limits": "Mechanical gate over frozen human/agent judgments; no independent semantic "
          "validation, population estimate or product snapshot-binding guarantee."})
    print(disposition)
    return 0 if passed else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "replay", "evaluate"):
        command = commands.add_parser(name, help={"prepare": "Run inputs and make review files.",
            "replay": "Freeze complete bound reviews and replay exact admissions.",
            "evaluate": "Check frozen reviews/replays against synthetic opportunities."}[name])
        command.add_argument("--run-dir", type=Path, required=True, help="Run outside a checkout.")
        if name == "prepare":
            command.add_argument("--kit", type=Path, default=KIT)
            command.add_argument("--cli", default="evidence-bundler-v1", help="Installed CLI.")
            command.add_argument("--subject", required=True, help="Declared exact commit/wheel.")
    args = parser.parse_args()
    run = args.run_dir.resolve()
    stage = run if args.command == "prepare" else run / args.command
    created = False
    try:
        need(not inside_checkout(run), "run inside checkout")
        stage.mkdir(parents=True, exist_ok=False)
        created = True
        return globals()[args.command](args, run, stage) or 0
    except Exception as exc:
        if created:
            write(stage / "FIRST-FAILURE.json", {"phase": args.command, "error": str(exc),
                  "at_utc": datetime.now(UTC).isoformat(), "retry": "Not performed; keep run."})
        print(f"{args.command} stopped: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
