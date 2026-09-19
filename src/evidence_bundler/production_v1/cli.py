"""Dedicated installed CLI for the qualified Evidence Bundler V1 slice."""

from __future__ import annotations

import json
from pathlib import Path

import click

from evidence_bundler import __version__
from evidence_bundler.production_v1.execution import (
    ProductionV1Error,
    inspect_record,
    run_contract_a,
)
from evidence_bundler.v1.contract_a import ContractAValidationError
from evidence_bundler.v1.contract_b import ContractBProjectionError
from evidence_bundler.v1.package import EvidencePackageValidationError


@click.group()
@click.version_option(
    version=f"{__version__} (EB V1 Slice 1)",
    prog_name="evidence-bundler-v1",
)
def cli() -> None:
    """Run the qualified EB V1 10/3 slice from Contract A 2.0 to Contract B 1.2."""


@cli.command("run")
@click.argument(
    "contract_a",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--out-dir",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="New or empty directory for the native V1 package and Contract B 1.2 bundle.",
)
@click.option(
    "--admission",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional explicit retained-candidate admission JSON.",
)
@click.option(
    "--compatibility-carrier",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional explicit carrier override. Defaults to the packaged frozen carrier.",
)
def run_command(
    contract_a: Path,
    out_dir: Path,
    admission: Path | None,
    compatibility_carrier: Path | None,
) -> None:
    """Run the exact qualified V1 profile and project released Contract B 1.2."""
    try:
        summary = run_contract_a(
            contract_a,
            out_dir,
            admission_path=admission,
            compatibility_carrier_path=compatibility_carrier,
        )
    except (
        ContractAValidationError,
        ContractBProjectionError,
        EvidencePackageValidationError,
        ProductionV1Error,
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(summary, sort_keys=True, indent=2))


@cli.command("inspect")
@click.option("--json", "json_output", is_flag=True, help="Emit deterministic JSON authority data.")
def inspect_command(json_output: bool) -> None:
    """Show the exact runtime, profile, and contract authority pinned by this CLI."""
    if not json_output:
        raise click.ClickException("inspect requires --json")
    click.echo(json.dumps(inspect_record(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    cli()
