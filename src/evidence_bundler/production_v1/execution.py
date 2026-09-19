"""Execution wrapper for the qualified Evidence Bundler V1 production slice."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from evidence_bundler import __version__
from evidence_bundler.v1 import build_package, load_admission, load_contract_a, write_package
from evidence_bundler.v1.contract_b import (
    CONTRACT_B_PRODUCTION_LOCK,
    CONTRACT_B_VERSION,
    FROZEN_V1_IMPLEMENTATION_COMMIT,
    FROZEN_V1_IMPLEMENTATION_TREE,
    INTEGRATION_CONFIG,
    INTEGRATION_CONFIG_SHA256,
    INTEGRATION_PROFILE_ID,
    load_compatibility_carrier,
    project_contract_b,
    validate_compatibility_carrier,
)
from evidence_bundler.v1.package import hash_json

SLICE_ID = "eb-v1-slice-1"
CLI_SURFACE_VERSION = "1"
CONTRACT_A_VERSION = "2.0.0"
CONTRACT_A_RELEASE_COMMIT = "529c92b49a34d5c610618551a8737f019f9fa332"
CARRIER_RESOURCE = "data/contract_b_compatibility_carrier.json"


class ProductionV1Error(ValueError):
    """Raised when the production-shaped V1 wrapper cannot proceed safely."""


def _packaged_carrier() -> dict[str, Any]:
    resource = files("evidence_bundler.production_v1").joinpath(CARRIER_RESOURCE)
    try:
        value = json.loads(resource.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductionV1Error(f"invalid packaged compatibility carrier: {exc}") from exc
    return validate_compatibility_carrier(value)


def inspect_record() -> dict[str, Any]:
    """Return deterministic authority and profile information for the installed V1 CLI."""
    carrier = _packaged_carrier()
    return {
        "cli": "evidence-bundler-v1",
        "cli_surface_version": CLI_SURFACE_VERSION,
        "slice_id": SLICE_ID,
        "package_version": __version__,
        "profile_id": INTEGRATION_PROFILE_ID,
        "config_sha256": INTEGRATION_CONFIG_SHA256,
        "config": INTEGRATION_CONFIG.as_payload(),
        "frozen_v1_implementation": {
            "commit": FROZEN_V1_IMPLEMENTATION_COMMIT,
            "tree": FROZEN_V1_IMPLEMENTATION_TREE,
        },
        "contract_a_authority": {
            "version": CONTRACT_A_VERSION,
            "release_commit": CONTRACT_A_RELEASE_COMMIT,
        },
        "contract_b_authority": {
            "version": CONTRACT_B_VERSION,
            "production_lock": CONTRACT_B_PRODUCTION_LOCK,
        },
        "packaged_compatibility_carrier_sha256": hash_json(carrier),
    }


def run_contract_a(
    contract_a_path: Path,
    out_dir: Path,
    *,
    admission_path: Path | None = None,
    compatibility_carrier_path: Path | None = None,
) -> dict[str, Any]:
    """Run the exact qualified 10/3 V1 profile and emit released Contract B 1.2."""
    resolved_out = out_dir.resolve()
    if resolved_out.exists() and any(resolved_out.iterdir()):
        raise ProductionV1Error(f"refusing non-empty output directory: {resolved_out}")
    resolved_out.mkdir(parents=True, exist_ok=True)

    contract_a = load_contract_a(contract_a_path)
    admission = load_admission(admission_path)
    carrier = (
        load_compatibility_carrier(compatibility_carrier_path)
        if compatibility_carrier_path is not None
        else _packaged_carrier()
    )

    package = build_package(
        contract_a=contract_a,
        config=INTEGRATION_CONFIG,
        admission=admission,
    )
    native_path = resolved_out / "native_eb_v1_package.json"
    write_package(package, native_path)
    receipt = project_contract_b(
        package=package,
        compatibility_carrier=carrier,
        out_dir=resolved_out,
    )
    return {
        "slice_id": SLICE_ID,
        "profile_id": INTEGRATION_PROFILE_ID,
        "native_package": native_path.as_posix(),
        "native_package_sha256": package["package_sha256"],
        "contract_b_dir": (resolved_out / "contract_b").as_posix(),
        "contract_b_bundle_hash": receipt["bundle_hash"],
        "projection_receipt": (resolved_out / "projection_receipt.json").as_posix(),
        "projection_receipt_sha256": receipt["receipt_sha256"],
    }
