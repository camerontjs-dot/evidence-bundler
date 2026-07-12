"""Run the Phase 4 Unit 1 BM25 handoff demo through installed CLIs only."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from evidence_bundler.contracts.discovery import resolve_claim_audit_lab_root

REPO_ROOT = Path(__file__).resolve().parents[1]
MAINFRAME_PROJECTS_ROOT = REPO_ROOT.parents[1]

DEMO_ROOT = REPO_ROOT / "examples" / "handoff-demo"
SCAFFOLD_RUN_DIR = DEMO_ROOT / "scaffold-run-bm25-handoff-demo"
OUTPUT_DIR = REPO_ROOT / "build" / "phase-4-unit1-handoff-demo"

EVIDENCE_BUNDLER_CLI = REPO_ROOT / ".venv" / "bin" / "evidence-bundler"


SUPPORTED_CLAIM_ID = "clm-supported"
WEAK_CLAIM_ID = "clm-weak"
NEEDS_REVIEW_CLAIM_ID = "clm-needs-review"

def main() -> None:
    args = _parse_args()
    cal_root = resolve_claim_audit_lab_root(args.claim_audit_root)
    claim_audit_cli = cal_root / ".venv" / "bin" / "claim-audit"

    _prepare_output_dir(OUTPUT_DIR, force=args.force)
    _assert_cli(EVIDENCE_BUNDLER_CLI)
    _assert_cli(claim_audit_cli)

    paths = _DemoPaths.from_output_dir(OUTPUT_DIR)
    _run_pipeline(paths, claim_audit_cli=claim_audit_cli, cal_root=cal_root)
    summary = _build_summary(paths)
    _assert_summary(summary)
    _write_summary(summary, paths)
    print(f"Handoff summary written: {paths.summary_md}")
    print(f"Handoff summary JSON written: {paths.summary_json}")



def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and recreate build/phase-4-unit1-handoff-demo.",
    )
    parser.add_argument(
        "--claim-audit-root",
        type=Path,
        help="Explicit path to the Claim Audit Lab root directory.",
    )

    return parser.parse_args()


def _prepare_output_dir(path: Path, *, force: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not force:
            raise SystemExit(
                f"Output directory is not empty: {path}. Re-run with --force to replace it."
            )
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _assert_cli(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Required CLI not found: {path}")


class _DemoPaths:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.draft = root / "draft-bundle"
        self.retrieval_report = root / "retrieval-report.md"
        self.review_annotations = root / "review_annotations.yaml"
        self.excerpt_refinement = root / "excerpt_refinement.yaml"
        self.final = root / "final-bundle"
        self.finalize_provenance = root / "final-bundle_finalize_provenance.yaml"
        self.coverage_md = root / "coverage-report.md"
        self.coverage_json = root / "coverage-report.json"
        self.audited_dir = root / "cal-audited"
        self.summary_md = root / "handoff_summary.md"
        self.summary_json = root / "handoff_summary.json"

    @classmethod
    def from_output_dir(cls, root: Path) -> _DemoPaths:
        return cls(root)

    @property
    def audited_bundle(self) -> Path:
        return self.audited_dir / f"{self.final.name}-audited"


def _run_pipeline(paths: _DemoPaths, *, claim_audit_cli: Path, cal_root: Path) -> None:
    _run([EVIDENCE_BUNDLER_CLI, "verify-intake", SCAFFOLD_RUN_DIR], cwd=REPO_ROOT)
    _run(
        [
            EVIDENCE_BUNDLER_CLI,
            "build-bundle",
            SCAFFOLD_RUN_DIR,
            "--output",
            paths.draft,
            "--method",
            "bm25",
            "--top-k",
            "1",
            "--child-top-k",
            "5",
            "--report-out",
            paths.retrieval_report,
        ],
        cwd=REPO_ROOT,
    )
    _run(
        [
            EVIDENCE_BUNDLER_CLI,
            "review",
            "init",
            paths.draft,
            "--output",
            paths.review_annotations,
            "--reviewer",
            "phase-4-unit1-synthetic-reviewer",
        ],
        cwd=REPO_ROOT,
    )
    for claim_id, decision in (
        (None, "rejected"),
        (SUPPORTED_CLAIM_ID, "accepted"),
        (WEAK_CLAIM_ID, "insufficient-excerpt"),
        (NEEDS_REVIEW_CLAIM_ID, "needs-review"),
    ):
        cmd = [
            EVIDENCE_BUNDLER_CLI,
            "review",
            "batch",
            paths.draft,
            "--annotations",
            paths.review_annotations,
            "--decision",
            decision,
        ]
        if claim_id is not None:
            cmd.extend(["--claim-id", claim_id])
        _run(cmd, cwd=REPO_ROOT)

    _run(
        [
            EVIDENCE_BUNDLER_CLI,
            "refine-excerpts",
            paths.draft,
            "--annotations",
            paths.review_annotations,
            "--output",
            paths.excerpt_refinement,
        ],
        cwd=REPO_ROOT,
    )
    _run(
        [
            EVIDENCE_BUNDLER_CLI,
            "finalize-bundle",
            paths.draft,
            "--annotations",
            paths.review_annotations,
            "--refinement",
            paths.excerpt_refinement,
            "--output",
            paths.final,
            "--provenance-output",
            paths.finalize_provenance,
        ],
        cwd=REPO_ROOT,
    )
    _run(
        [
            EVIDENCE_BUNDLER_CLI,
            "coverage-report",
            paths.draft,
            "--annotations",
            paths.review_annotations,
            "--refinement",
            paths.excerpt_refinement,
            "--final-bundle",
            paths.final,
            "--provenance",
            paths.finalize_provenance,
            "--markdown-out",
            paths.coverage_md,
            "--json-out",
            paths.coverage_json,
        ],
        cwd=REPO_ROOT,
    )
    _run(
        [
            claim_audit_cli,
            "audit-bundle",
            paths.final,
            "--out-dir",
            paths.audited_dir,
        ],
        cwd=cal_root,
    )



def _run(command: list[object], *, cwd: Path) -> None:
    printable = " ".join(str(part) for part in command)
    print(f"$ {printable}")
    result = subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _build_summary(paths: _DemoPaths) -> dict[str, Any]:
    final_manifest = _load_yaml(paths.final / "bundle_manifest.yaml")
    audited_manifest = _load_yaml(paths.audited_bundle / "bundle_manifest.yaml")
    provenance = _load_yaml(paths.finalize_provenance)
    coverage = json.loads(paths.coverage_json.read_text(encoding="utf-8"))

    final_claims = _load_claims(paths.final)
    audited_claims = _load_claims(paths.audited_bundle)
    final_passages = _passage_identity(paths.final)
    audited_passages = _passage_identity(paths.audited_bundle)
    final_claim_passages = _claim_passage_identity(final_claims)
    audited_claim_passages = _claim_passage_identity(audited_claims)

    verdicts = {
        claim_id: claim["audit"].get("audit_support_verdict")
        for claim_id, claim in audited_claims.items()
        if claim.get("claim_type") == "extracted_claim"
    }
    audit_run_ids = {
        claim_id: claim["audit"].get("audit_run_id")
        for claim_id, claim in audited_claims.items()
        if claim.get("claim_type") == "extracted_claim"
    }

    return {
        "schema_version": "phase-4-unit1-handoff-summary-v1",
        "report_generated_at_utc": _utc_now(),
        "paths": {
            "scaffold_run_dir": _rel(SCAFFOLD_RUN_DIR),
            "draft_bundle": _rel(paths.draft),
            "final_bundle": _rel(paths.final),
            "audited_bundle": _rel(paths.audited_bundle),
            "coverage_markdown": _rel(paths.coverage_md),
            "coverage_json": _rel(paths.coverage_json),
        },
        "anchor_hash_chain": {
            "draft_bundle_hash": provenance["draft_bundle_hash"],
            "review_annotations_hash": provenance["annotation_hash"],
            "excerpt_refinement_hash": provenance["refinement_hash"],
            "final_bundle_hash": provenance["final_bundle_hash"],
        },
        "final_bundle": {
            "bundle_id": final_manifest["bundle_id"],
            "bundle_hash": final_manifest["bundle"]["bundle_hash"],
            "reviewer_sign_off_required": final_manifest["reviewer_sign_off"]["required"],
            "reviewer_sign_off_signed_by": final_manifest["reviewer_sign_off"]["signed_by"],
            "reviewer_sign_off_signature_timestamp_utc": final_manifest["reviewer_sign_off"][
                "signature_timestamp_utc"
            ],
            "reviewer_sign_off_signature_notes": final_manifest["reviewer_sign_off"][
                "signature_notes"
            ],
        },
        "coverage": {
            "inconsistency_count": len(coverage.get("inconsistencies", [])),
            "inconsistencies": coverage.get("inconsistencies", []),
        },
        "audited_bundle": {
            "path": _rel(paths.audited_bundle),
            "reviewer_sign_off_required": audited_manifest["reviewer_sign_off"]["required"],
            "audited_verdicts": verdicts,
            "audit_run_ids": audit_run_ids,
        },
        "provenance_assertions": {
            "source_run_id_byte_identical": final_manifest["source_run_id"]
            == audited_manifest["source_run_id"],
            "source_corpus_hash_byte_identical": final_manifest["source_corpus_hash"]
            == audited_manifest["source_corpus_hash"],
            "evidence_builder_config_hash_byte_identical": final_manifest["evidence_builder"][
                "config_hash"
            ]
            == audited_manifest["evidence_builder"]["config_hash"],
            "passage_records_byte_identical": final_passages == audited_passages,
            "claim_passage_refs_byte_identical": final_claim_passages == audited_claim_passages,
            "all_audited_claims_have_audit_run_id": all(audit_run_ids.values()),
        },
        "passage_records": final_passages,
        "claim_passage_refs": final_claim_passages,
    }


def _assert_summary(summary: dict[str, Any]) -> None:
    errors: list[str] = []
    verdicts = summary["audited_bundle"]["audited_verdicts"]
    assertions = summary["provenance_assertions"]
    final_bundle = summary["final_bundle"]

    if summary["coverage"]["inconsistency_count"] != 0:
        errors.append("coverage inconsistencies must be zero")
    if final_bundle["reviewer_sign_off_required"] is not True:
        errors.append("final bundle reviewer_sign_off.required must be true")
    if summary["audited_bundle"]["reviewer_sign_off_required"] is not True:
        errors.append("audited bundle reviewer_sign_off.required must be true")
    for field in (
        "reviewer_sign_off_signed_by",
        "reviewer_sign_off_signature_timestamp_utc",
        "reviewer_sign_off_signature_notes",
    ):
        if final_bundle[field] is not None:
            errors.append(f"final bundle {field} must stay null")
    if verdicts.get(SUPPORTED_CLAIM_ID) != "supported":
        errors.append(f"{SUPPORTED_CLAIM_ID} must audit as supported")
    if verdicts.get(WEAK_CLAIM_ID) not in {"needs_source", "unsupported"}:
        errors.append(f"{WEAK_CLAIM_ID} must audit as needs_source or unsupported")
    if NEEDS_REVIEW_CLAIM_ID not in verdicts or verdicts[NEEDS_REVIEW_CLAIM_ID] is None:
        errors.append(f"{NEEDS_REVIEW_CLAIM_ID} must have an audited verdict")
    for key, value in assertions.items():
        if value is not True:
            errors.append(f"provenance assertion failed: {key}")

    if errors:
        raise SystemExit("Phase 4 Unit 1 handoff assertions failed:\n- " + "\n- ".join(errors))


def _write_summary(summary: dict[str, Any], paths: _DemoPaths) -> None:
    paths.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    paths.summary_md.write_text(_render_summary_markdown(summary), encoding="utf-8")


def _render_summary_markdown(summary: dict[str, Any]) -> str:
    verdict_lines = [
        f"- `{claim_id}`: `{verdict}`"
        for claim_id, verdict in sorted(summary["audited_bundle"]["audited_verdicts"].items())
    ]
    assertion_lines = [
        f"- `{key}`: `{value}`"
        for key, value in sorted(summary["provenance_assertions"].items())
    ]
    return "\n".join(
        [
            "# Phase 4 Unit 1 Handoff Summary",
            "",
            (
                "This is a synthetic engineering handoff demo. Bundler passages are "
                "retrieval nominations until Claim Audit Lab audits the final C-B copy."
            ),
            "",
            "## Final Bundle",
            "",
            f"- Bundle id: `{summary['final_bundle']['bundle_id']}`",
            f"- Bundle hash: `{summary['final_bundle']['bundle_hash']}`",
            (
                "- Reviewer sign-off required: "
                f"`{summary['final_bundle']['reviewer_sign_off_required']}`"
            ),
            "",
            "## Anchor Hash Chain",
            "",
            *[
                f"- {key}: `{value}`"
                for key, value in summary["anchor_hash_chain"].items()
            ],
            "",
            "## Coverage",
            "",
            f"- Inconsistency count: `{summary['coverage']['inconsistency_count']}`",
            "",
            "## CAL Audited Verdicts",
            "",
            *verdict_lines,
            "",
            "## Provenance Assertions",
            "",
            *assertion_lines,
            "",
            f"Audited bundle: `{summary['audited_bundle']['path']}`",
            "",
        ]
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return data


def _load_claims(bundle_dir: Path) -> dict[str, dict[str, Any]]:
    claims: dict[str, dict[str, Any]] = {}
    for path in sorted((bundle_dir / "claims").glob("*.yaml")):
        data = _load_yaml(path)
        claims[str(data["claim_id"])] = data
    return claims


def _passage_identity(bundle_dir: Path) -> list[dict[str, str]]:
    identities: list[dict[str, str]] = []
    for path in sorted((bundle_dir / "evidence").glob("*/passages/*.yaml")):
        data = _load_yaml(path)
        identities.append(
            {
                "source_id": str(data["source_id"]),
                "passage_id": str(data["passage_id"]),
                "passage_hash": str(data["passage_hash"]),
            }
        )
    return identities


def _claim_passage_identity(claims: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    identities: list[dict[str, str]] = []
    for claim_id, claim in sorted(claims.items()):
        for field in ("evidence_passages", "counterevidence_passages"):
            for passage in claim.get(field, []):
                identities.append(
                    {
                        "claim_id": claim_id,
                        "field": field,
                        "source_id": str(passage["source_id"]),
                        "passage_id": str(passage["passage_id"]),
                        "passage_hash": str(passage["passage_hash"]),
                    }
                )
    return identities


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(MAINFRAME_PROJECTS_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())



def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
