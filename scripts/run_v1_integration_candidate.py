"""Run the exact Evidence Bundler V1 10/3 integration candidate and project B1.2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidence_bundler.v1 import build_package, load_admission, load_contract_a, write_package
from evidence_bundler.v1.contract_b import (
    INTEGRATION_CONFIG,
    INTEGRATION_PROFILE_ID,
    load_compatibility_carrier,
    project_contract_b,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the exact Evidence Bundler V1 10/3 integration candidate native package "
            "and project it through the explicit released Contract B 1.2 compatibility boundary."
        )
    )
    parser.add_argument("contract_a", type=Path, help="Released Contract A 2.0 JSON handoff")
    parser.add_argument("--out-dir", type=Path, required=True, help="Fresh output directory")
    parser.add_argument(
        "--admission",
        type=Path,
        default=None,
        help="Optional explicit V1 retained-candidate admission JSON",
    )
    parser.add_argument(
        "--compatibility-carrier",
        type=Path,
        required=True,
        help="Explicit Contract B 1.2 legacy compatibility carrier JSON",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    out_dir = args.out_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"refusing non-empty output directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    contract_a = load_contract_a(args.contract_a)
    admission = load_admission(args.admission)
    carrier = load_compatibility_carrier(args.compatibility_carrier)

    package = build_package(
        contract_a=contract_a,
        config=INTEGRATION_CONFIG,
        admission=admission,
    )
    native_path = out_dir / "native_eb_v1_package.json"
    write_package(package, native_path)
    receipt = project_contract_b(
        package=package,
        compatibility_carrier=carrier,
        out_dir=out_dir,
    )

    summary = {
        "profile_id": INTEGRATION_PROFILE_ID,
        "native_package": native_path.as_posix(),
        "native_package_sha256": package["package_sha256"],
        "contract_b_dir": (out_dir / "contract_b").as_posix(),
        "contract_b_bundle_hash": receipt["bundle_hash"],
        "projection_receipt": (out_dir / "projection_receipt.json").as_posix(),
        "projection_receipt_sha256": receipt["receipt_sha256"],
    }
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
