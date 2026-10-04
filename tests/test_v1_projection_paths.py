from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from test_v1_contract_b_projection import _carrier, _contract_a

from evidence_bundler.production_v1.cli import cli
from evidence_bundler.v1 import build_package
from evidence_bundler.v1.contract_a import compute_handoff_sha256, validate_contract_a
from evidence_bundler.v1.contract_b import (
    INTEGRATION_CONFIG,
    ContractBProjectionError,
    project_contract_b,
)


def _seal(value: dict[str, Any]) -> dict[str, Any]:
    value["handoff_sha256"] = compute_handoff_sha256(value)
    return validate_contract_a(value)


def _set_id(value: dict[str, Any], role: str, identifier: str) -> None:
    if role == "root":
        value["root_proposition"]["proposition_id"] = identifier
    elif role == "child":
        value["decomposition"]["children"][1]["proposition_id"] = identifier
    else:
        value["sources"][0]["source_id"] = identifier


@pytest.mark.parametrize("role", ["root", "child", "source"])
@pytest.mark.parametrize(
    "identifier",
    [
        "../../../victim",
        "a/b",
        "a\\b",
        "C:drive",
        "C:\\root",
        "\\root",
        " padded ",
        "line\nbreak",
        "nul\0byte",
        "control\x7f",
        "line\u2028break",
        "é" * 128,
    ],
)
def test_cli_refuses_projected_ids_before_creating_output(
    tmp_path: Path, role: str, identifier: str
) -> None:
    value = _contract_a()
    _set_id(value, role, identifier)
    # These remain valid A2 identities; this is a B projection restriction.
    _seal(value)
    source = tmp_path / "input.json"
    source.write_text(json.dumps(value), encoding="utf-8")
    victim = tmp_path / "victim.yaml"
    victim.write_bytes(b"pre-existing content\n")
    output = tmp_path / "new-parent" / "out"

    result = CliRunner().invoke(cli, ["run", str(source), "--out-dir", str(output)])

    assert result.exit_code != 0
    assert "Contract B path" in result.output
    assert "Traceback" not in result.output
    assert victim.read_bytes() == b"pre-existing content\n"
    assert not output.parent.exists()


@pytest.mark.parametrize("role", ["root", "source"])
def test_cli_refuses_absolute_ids_without_overwriting_sentinel(tmp_path: Path, role: str) -> None:
    value = _contract_a()
    destination = tmp_path / "outside"
    destination.mkdir()
    identifier = str(destination / "victim") if role == "root" else str(destination)
    victim = destination / ("victim.yaml" if role == "root" else "source_profile.yaml")
    victim.write_bytes(b"keep me\n")
    _set_id(value, role, identifier)
    source = tmp_path / "input.json"
    source.write_text(json.dumps(_seal(value)), encoding="utf-8")
    output = tmp_path / "out"

    result = CliRunner().invoke(cli, ["run", str(source), "--out-dir", str(output)])

    assert result.exit_code != 0
    assert victim.read_bytes() == b"keep me\n"
    assert not output.exists()


@pytest.mark.parametrize("role", ["claim", "source"])
@pytest.mark.parametrize("ids", [("Alpha", "alpha"), ("café", "cafe\u0301")])
def test_distinct_projected_ids_cannot_alias(
    tmp_path: Path, role: str, ids: tuple[str, str]
) -> None:
    value = _contract_a()
    if role == "claim":
        value["root_proposition"]["proposition_id"] = ids[0]
        value["decomposition"]["children"][0]["proposition_id"] = ids[1]
    else:
        value["sources"][0]["source_id"] = ids[0]
        value["sources"][1]["source_id"] = ids[1]
    package = build_package(contract_a=_seal(value), config=INTEGRATION_CONFIG)
    output = tmp_path / "out"

    with pytest.raises(ContractBProjectionError, match="aliases"):
        project_contract_b(package=package, compatibility_carrier=_carrier(), out_dir=output)

    assert not output.exists()


@pytest.mark.parametrize("identifier", [".", ".."])
def test_source_dot_directories_are_refused(tmp_path: Path, identifier: str) -> None:
    value = _contract_a()
    value["sources"][0]["source_id"] = identifier
    package = build_package(contract_a=_seal(value), config=INTEGRATION_CONFIG)
    output = tmp_path / "out"

    with pytest.raises(ContractBProjectionError, match="literal Contract B path"):
        project_contract_b(package=package, compatibility_carrier=_carrier(), out_dir=output)

    assert not output.exists()


@pytest.mark.parametrize("identifier", ["claim:alpha", "café", "a..b", "%2Fabsolute", "CON"])
def test_safe_ids_are_preserved_and_namespaces_remain_separate(
    tmp_path: Path, identifier: str
) -> None:
    value = _contract_a()
    value["decomposition"]["children"][0]["proposition_id"] = identifier
    value["sources"][0]["source_id"] = identifier
    package = build_package(contract_a=_seal(value), config=INTEGRATION_CONFIG)
    output = tmp_path / "out"

    receipt = project_contract_b(package=package, compatibility_carrier=_carrier(), out_dir=output)

    assert (output / "contract_b" / "claims" / f"{identifier}.yaml").is_file()
    assert (output / "contract_b" / "evidence" / identifier / "source_profile.yaml").is_file()
    assert receipt["receipt_sha256"]


@pytest.mark.parametrize("identifier", [".", ".."])
def test_claim_dot_ids_are_literal_filenames(tmp_path: Path, identifier: str) -> None:
    value = _contract_a()
    value["root_proposition"]["proposition_id"] = identifier
    package = build_package(contract_a=_seal(value), config=INTEGRATION_CONFIG)
    project_contract_b(package=package, compatibility_carrier=_carrier(), out_dir=tmp_path / "out")
    assert (tmp_path / "out" / "contract_b" / "claims" / f"{identifier}.yaml").is_file()


@pytest.mark.parametrize("linked_name", ["contract_b", "projection_receipt.json"])
def test_direct_projection_refuses_existing_output_symlinks(
    tmp_path: Path, linked_name: str
) -> None:
    package = build_package(contract_a=_contract_a(), config=INTEGRATION_CONFIG)
    outside = tmp_path / "outside"
    outside.mkdir()
    output = tmp_path / "out"
    output.mkdir()
    target = outside if linked_name == "contract_b" else outside / "not-yet-created.json"
    link = output / linked_name
    link.symlink_to(target, target_is_directory=linked_name == "contract_b")

    with pytest.raises(ContractBProjectionError, match="symbolic links"):
        project_contract_b(package=package, compatibility_carrier=_carrier(), out_dir=output)

    assert link.is_symlink()
    assert list(outside.iterdir()) == []
    assert list(output.iterdir()) == [link]
