from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from evidence_bundler import __version__
from evidence_bundler.production_v1.cli import cli
from evidence_bundler.production_v1.execution import (
    CLI_SURFACE_VERSION,
    SLICE_ID,
    inspect_record,
)
from evidence_bundler.v1.contract_a import compute_handoff_sha256
from evidence_bundler.v1.contract_b import (
    CONTRACT_B_PRODUCTION_LOCK,
    INTEGRATION_CONFIG_SHA256,
    INTEGRATION_PROFILE_ID,
)


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
        "handoff_id": "handoff-production-v1-cli-test",
        "producer": {"producer_id": "test", "producer_version": "1"},
        "work": {"work_id": "work-production-v1-cli-test"},
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


ROOT = Path(__file__).resolve().parents[1]
PACKAGED_CARRIER = (
    ROOT
    / "src"
    / "evidence_bundler"
    / "production_v1"
    / "data"
    / "contract_b_compatibility_carrier.json"
)
PROMOTION_CARRIER = ROOT / "config" / "eb_v1_slice" / "contract_b_compatibility_carrier.json"


def _write_contract_a(path: Path) -> None:
    path.write_text(
        json.dumps(_contract_a(), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def test_packaged_carrier_is_exact_frozen_promotion_carrier() -> None:
    assert PACKAGED_CARRIER.read_bytes() == PROMOTION_CARRIER.read_bytes()


def test_inspect_record_pins_exact_qualified_profile_and_contracts() -> None:
    record = inspect_record()
    assert record["cli"] == "evidence-bundler-v1"
    assert record["cli_surface_version"] == CLI_SURFACE_VERSION == "1"
    assert record["slice_id"] == SLICE_ID == "eb-v1-slice-1"
    assert record["package_version"] == __version__ == "0.2.0"
    assert record["profile_id"] == INTEGRATION_PROFILE_ID == "eb-v1-integration-10x3-rc0"
    assert record["config_sha256"] == INTEGRATION_CONFIG_SHA256
    assert record["config"]["candidate_depth"] == 10
    assert record["config"]["retained_k"] == 3
    assert record["contract_a_authority"]["version"] == "2.0.0"
    assert record["contract_b_authority"] == {
        "version": "1.2.0",
        "production_lock": CONTRACT_B_PRODUCTION_LOCK,
    }


def test_cli_version_reports_versioned_v1_slice() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.output == "evidence-bundler-v1, version 0.2.0 (EB V1 Slice 1)\n"


def test_cli_inspect_json_is_deterministic() -> None:
    runner = CliRunner()
    first = runner.invoke(cli, ["inspect", "--json"])
    second = runner.invoke(cli, ["inspect", "--json"])
    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first.output == second.output
    assert json.loads(first.output) == inspect_record()


def test_cli_run_defaults_to_packaged_frozen_carrier(tmp_path: Path) -> None:
    runner = CliRunner()
    contract_a = tmp_path / "contract_a.json"
    _write_contract_a(contract_a)

    first = tmp_path / "first"
    second = tmp_path / "second"
    first_result = runner.invoke(
        cli,
        ["run", str(contract_a), "--out-dir", str(first)],
    )
    second_result = runner.invoke(
        cli,
        ["run", str(contract_a), "--out-dir", str(second)],
    )
    assert first_result.exit_code == 0, first_result.output
    assert second_result.exit_code == 0, second_result.output

    first_summary = json.loads(first_result.output)
    second_summary = json.loads(second_result.output)
    assert first_summary["slice_id"] == "eb-v1-slice-1"
    assert first_summary["profile_id"] == "eb-v1-integration-10x3-rc0"
    assert first_summary["native_package_sha256"] == second_summary["native_package_sha256"]
    assert first_summary["contract_b_bundle_hash"] == second_summary["contract_b_bundle_hash"]
    assert (first / "contract_b" / "CONTRACT_VERSION").read_text(encoding="utf-8") == "1.2.0\n"


def test_cli_run_refuses_nonempty_output(tmp_path: Path) -> None:
    runner = CliRunner()
    contract_a = tmp_path / "contract_a.json"
    _write_contract_a(contract_a)
    out_dir = tmp_path / "occupied"
    out_dir.mkdir()
    (out_dir / "sentinel").write_text("keep", encoding="utf-8")

    result = runner.invoke(cli, ["run", str(contract_a), "--out-dir", str(out_dir)])
    assert result.exit_code != 0
    assert "refusing non-empty output directory" in result.output
    assert (out_dir / "sentinel").read_text(encoding="utf-8") == "keep"
