from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
from hashlib import sha256
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

SUBJECT_SHA = "08ca896debd6d16fa21be2f178ed7cbe62395d00"
EXPECTED_VERSION = "0.2.0"
EXPECTED_VERSION_LINE = "evidence-bundler-v1, version 0.2.0 (EB V1 Slice 1)"
EXPECTED_PROFILE = "eb-v1-integration-10x3-rc0"
EXPECTED_CONTRACT_B = "1.2.0"
EXPECTED_CONTRACT_B_LOCK = "c314e53bd91c0736aa4370a364673b069aceb43e"

SUBJECT_ROOT = Path(os.environ["SUBJECT_ROOT"]).resolve()

from evidence_bundler.v1 import build_package  # noqa: E402
from evidence_bundler.v1.contract_a import compute_handoff_sha256  # noqa: E402
from evidence_bundler.v1.contract_b import INTEGRATION_CONFIG  # noqa: E402
from evidence_bundler.v1.package import ADMISSION_SCHEMA  # noqa: E402


def _hash_text(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _contract_a() -> dict[str, Any]:
    root_text = "Alpha beta gamma delta and omega theta are both documented."
    child_one = "alpha beta gamma delta"
    child_two = "omega theta"
    source_texts = [
        "alpha appears in calibration note A.",
        "alpha appears in calibration note B.",
        "beta appears in calibration note A.",
        "beta appears in calibration note B.",
        "gamma appears in calibration note A.",
        "gamma appears in calibration note B.",
        "delta appears in calibration note A.",
        "delta appears in calibration note B.",
        "omega theta appears together in source nine.",
        "omega theta appears together in source ten.",
        "unrelated cobalt orchard material.",
        "unrelated marine quartz material.",
    ]
    value: dict[str, Any] = {
        "schema": "contract-a-wire-candidate-rc2",
        "handoff_id": "handoff-v1-pressure",
        "producer": {"producer_id": "pressure-harness", "producer_version": "1"},
        "work": {"work_id": "work-v1-pressure"},
        "root_proposition": {
            "proposition_id": "ROOT",
            "text": root_text,
            "text_sha256": _hash_text(root_text),
        },
        "decomposition": {
            "state": "declared",
            "decomposition_id": "D1",
            "operator": "all_of",
            "children": [
                {
                    "proposition_id": "C1",
                    "text": child_one,
                    "text_sha256": _hash_text(child_one),
                    "sequence": 1,
                },
                {
                    "proposition_id": "C2",
                    "text": child_two,
                    "text_sha256": _hash_text(child_two),
                    "sequence": 2,
                },
            ],
        },
        "sources": [
            {
                "source_id": f"S{index:02d}",
                "media_type": "text/plain; charset=utf-8",
                "content": text,
                "content_sha256": _hash_text(text),
            }
            for index, text in enumerate(source_texts, start=1)
        ],
        "handoff_sha256": "sha256:" + "0" * 64,
    }
    value["handoff_sha256"] = compute_handoff_sha256(value)
    return value

CLI = shutil.which("evidence-bundler-v1")
LEGACY_CLI = shutil.which("evidence-bundler")
if CLI is None:
    raise SystemExit("installed evidence-bundler-v1 entry point not found")
if LEGACY_CLI is None:
    raise SystemExit("legacy evidence-bundler entry point not found")


def canonical_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def run_cli(args: list[str], *, cwd: Path, expect_ok: bool) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [CLI, *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if expect_ok and proc.returncode != 0:
        raise AssertionError(f"CLI unexpectedly failed: {args}\n{proc.stdout}")
    if not expect_ok and proc.returncode == 0:
        raise AssertionError(f"negative control unexpectedly succeeded: {args}\n{proc.stdout}")
    return proc


def assert_no_artifacts(path: Path) -> None:
    if not path.exists():
        return
    files = [p for p in path.rglob("*") if p.is_file()]
    if files:
        raise AssertionError(f"rejected invocation leaked artifacts: {files}")


def tree_bytes(path: Path) -> dict[str, bytes]:
    return {
        p.relative_to(path).as_posix(): p.read_bytes()
        for p in sorted(path.rglob("*"))
        if p.is_file()
    }


def installed_pressure() -> None:
    if importlib.metadata.version("evidence-bundler") != EXPECTED_VERSION:
        raise AssertionError("wheel metadata version mismatch")

    with tempfile.TemporaryDirectory(prefix="eb-v1-pressure-") as temp:
        root = Path(temp)
        cwd = root / "unrelated-cwd"
        cwd.mkdir()

        version = run_cli(["--version"], cwd=cwd, expect_ok=True)
        if version.stdout.strip() != EXPECTED_VERSION_LINE:
            raise AssertionError(f"unexpected version output: {version.stdout!r}")

        inspect1 = run_cli(["inspect", "--json"], cwd=cwd, expect_ok=True)
        inspect2 = run_cli(["inspect", "--json"], cwd=cwd, expect_ok=True)
        if inspect1.stdout != inspect2.stdout:
            raise AssertionError("inspect output is not byte deterministic")
        authority = json.loads(inspect1.stdout)
        assert authority["package_version"] == EXPECTED_VERSION
        assert authority["profile_id"] == EXPECTED_PROFILE
        assert authority["contract_b_authority"] == {
            "version": EXPECTED_CONTRACT_B,
            "production_lock": EXPECTED_CONTRACT_B_LOCK,
        }

        missing_flag = run_cli(["inspect"], cwd=cwd, expect_ok=False)
        if "inspect requires --json" not in missing_flag.stdout:
            raise AssertionError("inspect fail-closed message changed unexpectedly")

        legacy = subprocess.run(
            [LEGACY_CLI, "--help"],
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if legacy.returncode != 0:
            raise AssertionError(f"legacy CLI no longer starts:\n{legacy.stdout}")

        contract = _contract_a()
        contract_a1 = root / "input-a" / "CONTRACT_A.json"
        contract_a2 = root / "relocated-input" / "same-bytes.json"
        canonical_write(contract_a1, contract)
        contract_a2.parent.mkdir(parents=True)
        shutil.copy2(contract_a1, contract_a2)

        out1 = root / "run-1"
        out2 = root / "run-2"
        out3 = root / "run-relocated-input"
        run_cli(["run", str(contract_a1), "--out-dir", str(out1)], cwd=cwd, expect_ok=True)
        run_cli(["run", str(contract_a1), "--out-dir", str(out2)], cwd=cwd, expect_ok=True)
        run_cli(["run", str(contract_a2), "--out-dir", str(out3)], cwd=cwd, expect_ok=True)
        if tree_bytes(out1) != tree_bytes(out2):
            raise AssertionError("same-input replay emitted different artifact bytes")
        if tree_bytes(out1) != tree_bytes(out3):
            raise AssertionError("input-path relocation changed artifact bytes")

        native = json.loads((out1 / "native_eb_v1_package.json").read_text(encoding="utf-8"))
        assert native["producer"]["producer_version"] == EXPECTED_VERSION
        manifest = yaml.safe_load(
            (out1 / "contract_b" / "bundle_manifest.yaml").read_text(encoding="utf-8")
        )
        assert manifest["evidence_builder"]["version"] == EXPECTED_VERSION

        sentinel_dir = root / "occupied"
        sentinel_dir.mkdir()
        sentinel = sentinel_dir / "sentinel.txt"
        sentinel.write_text("do-not-touch", encoding="utf-8")
        run_cli(
            ["run", str(contract_a1), "--out-dir", str(sentinel_dir)],
            cwd=cwd,
            expect_ok=False,
        )
        assert sentinel.read_text(encoding="utf-8") == "do-not-touch"
        assert sorted(p.name for p in sentinel_dir.iterdir()) == ["sentinel.txt"]

        tampered_contract = deepcopy(contract)
        tampered_contract["sources"][0]["content"] += " TAMPER"
        tampered_path = root / "tampered-contract-a.json"
        canonical_write(tampered_path, tampered_contract)
        tampered_out = root / "tampered-contract-out"
        run_cli(
            ["run", str(tampered_path), "--out-dir", str(tampered_out)],
            cwd=cwd,
            expect_ok=False,
        )
        assert_no_artifacts(tampered_out)

        malformed_admission = root / "bad-admission.json"
        malformed_admission.write_text("{not-json\n", encoding="utf-8")
        bad_adm_out = root / "bad-admission-out"
        run_cli(
            [
                "run",
                str(contract_a1),
                "--admission",
                str(malformed_admission),
                "--out-dir",
                str(bad_adm_out),
            ],
            cwd=cwd,
            expect_ok=False,
        )
        assert_no_artifacts(bad_adm_out)

        wrong_schema = root / "wrong-admission-schema.json"
        canonical_write(wrong_schema, {"schema": "wrong", "decisions": []})
        wrong_schema_out = root / "wrong-schema-out"
        run_cli(
            [
                "run",
                str(contract_a1),
                "--admission",
                str(wrong_schema),
                "--out-dir",
                str(wrong_schema_out),
            ],
            cwd=cwd,
            expect_ok=False,
        )
        assert_no_artifacts(wrong_schema_out)

        initial = build_package(contract_a=contract, config=INTEGRATION_CONFIG)
        retained = next(row for row in initial["candidates"] if row["selection_state"] == "retained")
        nonretained = next(
            row for row in initial["candidates"] if row["selection_state"] == "not_retained"
        )
        valid_admission = root / "valid-admission.json"
        canonical_write(
            valid_admission,
            {
                "schema": ADMISSION_SCHEMA,
                "decisions": [
                    {
                        "proposition_id": retained["proposition_id"],
                        "passage_id": retained["passage_id"],
                        "decision": "accepted",
                    }
                ],
            },
        )
        admitted_out = root / "admitted-out"
        run_cli(
            [
                "run",
                str(contract_a1),
                "--admission",
                str(valid_admission),
                "--out-dir",
                str(admitted_out),
            ],
            cwd=cwd,
            expect_ok=True,
        )
        admitted_native = json.loads(
            (admitted_out / "native_eb_v1_package.json").read_text(encoding="utf-8")
        )
        addressed = [
            row
            for row in admitted_native["candidates"]
            if row["proposition_id"] == retained["proposition_id"]
            and row["passage_id"] == retained["passage_id"]
        ]
        assert len(addressed) == 1
        assert addressed[0]["admission_state"] == "accepted"

        invalid_target = root / "nonretained-admission.json"
        canonical_write(
            invalid_target,
            {
                "schema": ADMISSION_SCHEMA,
                "decisions": [
                    {
                        "proposition_id": nonretained["proposition_id"],
                        "passage_id": nonretained["passage_id"],
                        "decision": "accepted",
                    }
                ],
            },
        )
        invalid_target_out = root / "nonretained-admission-out"
        run_cli(
            [
                "run",
                str(contract_a1),
                "--admission",
                str(invalid_target),
                "--out-dir",
                str(invalid_target_out),
            ],
            cwd=cwd,
            expect_ok=False,
        )
        assert_no_artifacts(invalid_target_out)

        malformed_carrier = root / "malformed-carrier.json"
        malformed_carrier.write_text("{broken", encoding="utf-8")
        malformed_carrier_out = root / "malformed-carrier-out"
        run_cli(
            [
                "run",
                str(contract_a1),
                "--compatibility-carrier",
                str(malformed_carrier),
                "--out-dir",
                str(malformed_carrier_out),
            ],
            cwd=cwd,
            expect_ok=False,
        )
        assert_no_artifacts(malformed_carrier_out)

        frozen_carrier = json.loads(
            (
                SUBJECT_ROOT
                / "config"
                / "eb_v1_slice"
                / "contract_b_compatibility_carrier.json"
            ).read_text(encoding="utf-8")
        )
        weakened_carrier = deepcopy(frozen_carrier)
        weakened_carrier["authority"]["semantic_use_authorized"] = True
        weakened_path = root / "weakened-carrier.json"
        canonical_write(weakened_path, weakened_carrier)
        weakened_out = root / "weakened-carrier-out"
        run_cli(
            [
                "run",
                str(contract_a1),
                "--compatibility-carrier",
                str(weakened_path),
                "--out-dir",
                str(weakened_out),
            ],
            cwd=cwd,
            expect_ok=False,
        )
        assert_no_artifacts(weakened_out)

        # A completed directory must also be protected against accidental reuse.
        rerun = run_cli(
            ["run", str(contract_a1), "--out-dir", str(out1)],
            cwd=cwd,
            expect_ok=False,
        )
        if "refusing non-empty output directory" not in rerun.stdout:
            raise AssertionError("completed-run directory reuse did not fail at the expected boundary")

    print("INSTALLED_PRESSURE_PASS")


def _canonical_apparatus_validate(bundle: Path) -> None:
    apparatus = Path(os.environ["APPARATUS_ROOT"]).resolve()
    sys.path.insert(0, str(apparatus))
    from validators.contract_b_factual_context import load_extension

    claim_ids = {p.stem for p in (bundle / "claims").glob("*.yaml")}
    source_ids = {p.name for p in (bundle / "evidence").iterdir() if p.is_dir()}
    passage_ids = {
        p.stem
        for source in (bundle / "evidence").iterdir()
        if source.is_dir()
        for p in (source / "passages").glob("*.yaml")
    }
    load_extension(
        bundle / "extensions" / "contract-b-factual-context-v1.json",
        claim_ids=claim_ids,
        source_ids=source_ids,
        passage_ids=passage_ids,
    )


def expect_exception(fn: Any, label: str) -> None:
    try:
        fn()
    except Exception:
        return
    raise AssertionError(f"negative control unexpectedly accepted: {label}")


def cross_repository_pressure() -> None:
    from claim_audit_lab.contracts.factual_context import load_contract_b_intake

    with tempfile.TemporaryDirectory(prefix="eb-v1-cross-pressure-") as temp:
        root = Path(temp)
        cwd = root / "outside-repositories"
        cwd.mkdir()
        contract_path = root / "CONTRACT_A.json"
        canonical_write(contract_path, _contract_a())
        out = root / "clean"
        run_cli(["run", str(contract_path), "--out-dir", str(out)], cwd=cwd, expect_ok=True)
        bundle = out / "contract_b"

        _canonical_apparatus_validate(bundle)
        view = load_contract_b_intake(bundle, deviations_dir=root / "clean-deviations")
        assert view.extension_state == "present"
        assert view.intake_ledger is not None
        assert view.semantic_context is not None

        malformed_extension_bundle = root / "mutated-extension"
        shutil.copytree(bundle, malformed_extension_bundle)
        extension_path = (
            malformed_extension_bundle
            / "extensions"
            / "contract-b-factual-context-v1.json"
        )
        extension = json.loads(extension_path.read_text(encoding="utf-8"))
        del extension["history_count_checks"]
        canonical_write(extension_path, extension)
        expect_exception(
            lambda: _canonical_apparatus_validate(malformed_extension_bundle),
            "Apparatus accepted extension missing history_count_checks",
        )
        expect_exception(
            lambda: load_contract_b_intake(
                malformed_extension_bundle,
                deviations_dir=root / "mutated-extension-deviations",
            ),
            "CAL accepted extension missing history_count_checks",
        )

        wrong_version_bundle = root / "wrong-contract-version"
        shutil.copytree(bundle, wrong_version_bundle)
        (wrong_version_bundle / "CONTRACT_VERSION").write_text("9.9.9\n", encoding="utf-8")
        expect_exception(
            lambda: load_contract_b_intake(
                wrong_version_bundle,
                deviations_dir=root / "wrong-version-deviations",
            ),
            "CAL accepted factual-context extension under wrong Contract B version",
        )

        prohibited_bundle = root / "prohibited-semantic-field"
        shutil.copytree(bundle, prohibited_bundle)
        prohibited_extension_path = (
            prohibited_bundle / "extensions" / "contract-b-factual-context-v1.json"
        )
        prohibited = json.loads(prohibited_extension_path.read_text(encoding="utf-8"))
        prohibited["support"] = True
        canonical_write(prohibited_extension_path, prohibited)
        expect_exception(
            lambda: _canonical_apparatus_validate(prohibited_bundle),
            "Apparatus accepted proposition-specific semantic field",
        )
        expect_exception(
            lambda: load_contract_b_intake(
                prohibited_bundle,
                deviations_dir=root / "prohibited-deviations",
            ),
            "CAL accepted proposition-specific semantic field",
        )

    print("CROSS_REPOSITORY_PRESSURE_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["installed", "cross"], required=True)
    args = parser.parse_args()
    if args.mode == "installed":
        installed_pressure()
    else:
        cross_repository_pressure()


if __name__ == "__main__":
    main()
