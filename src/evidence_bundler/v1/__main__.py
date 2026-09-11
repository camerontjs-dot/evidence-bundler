"""Operator CLI for the Evidence Bundler V1 candidate package."""

from __future__ import annotations

import argparse
from pathlib import Path

from evidence_bundler.v1 import (
    V1Config,
    build_package,
    load_admission,
    load_contract_a,
    write_package,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m evidence_bundler.v1",
        description=(
            "Build one immutable Evidence Bundler V1 candidate package "
            "from released Contract A 2.0."
        ),
    )
    parser.add_argument("contract_a", type=Path, help="Contract A 2.0 JSON handoff")
    parser.add_argument("--output", type=Path, required=True, help="Output package JSON")
    parser.add_argument(
        "--admission",
        type=Path,
        default=None,
        help="Optional explicit retained-candidate admission JSON",
    )
    parser.add_argument("--candidate-depth", type=int, default=5)
    parser.add_argument("--retained-k", type=int, default=3)
    parser.add_argument("--chunk-max-chars", type=int, default=1800)
    parser.add_argument("--chunk-overlap-chars", type=int, default=80)
    parser.add_argument(
        "--not-run-target",
        action="append",
        default=[],
        help="Exact upstream proposition_id to mark not_run; repeatable",
    )
    parser.add_argument(
        "--root-diagnostic",
        action="store_true",
        help=(
            "Run a separately typed, non-normative root diagnostic lane "
            "for declared decompositions"
        ),
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    config = V1Config(
        candidate_depth=args.candidate_depth,
        retained_k=args.retained_k,
        chunk_max_chars=args.chunk_max_chars,
        chunk_overlap_chars=args.chunk_overlap_chars,
        root_diagnostic=args.root_diagnostic,
    )
    contract_a = load_contract_a(args.contract_a)
    admission = load_admission(args.admission)
    package = build_package(
        contract_a=contract_a,
        config=config,
        admission=admission,
        not_run_target_ids=set(args.not_run_target),
    )
    write_package(package, args.output)
    print(f"Wrote {args.output}")
    print(f"package_sha256={package['package_sha256']}")
    print(f"execution_state={package['execution_state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
