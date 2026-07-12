"""Phase 4 Unit 1 BM25 handoff demo tests."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from evidence_bundler.contracts.discovery import resolve_claim_audit_lab_root
from evidence_bundler.contracts.hashing import compute_bundle_tree_hash
from evidence_bundler.contracts.intake import verify_intake

REPO_ROOT = Path(__file__).resolve().parents[1]

try:
    CAL_ROOT: Path | None = resolve_claim_audit_lab_root()
    CAL_PYTHON: Path | None = CAL_ROOT / ".venv" / "bin" / "python"
except FileNotFoundError:
    CAL_ROOT = None
    CAL_PYTHON = None

RUNNER = REPO_ROOT / "scripts" / "run_phase_4_unit1_handoff_demo.py"
DEMO_SCAFFOLD_RUN = REPO_ROOT / "examples" / "handoff-demo" / "scaffold-run-bm25-handoff-demo"
DEMO_BUILD = REPO_ROOT / "build" / "phase-4-unit1-handoff-demo"


TIMESTAMP_KEYS = {
    "generated_at_utc",
    "build_timestamp_utc",
    "audited_at_utc",
    "frozen_at_utc",
    "report_generated_at_utc",
}
HASH_KEYS = {
    "audit_config_hash",
    "bundle_hash",
    "config_hash",
    "draft_bundle_hash",
    "excerpt_refinement_hash",
    "final_bundle_hash",
    "passage_hash",
    "refinement_hash",
    "review_annotations_hash",
    "source_corpus_hash",
    "validation_set_hash",
}
ID_KEYS = {
    "audit_run_id",
    "bundle_id",
    "draft_bundle_id",
    "final_bundle_id",
}


def test_phase4_demo_fixture_verifies_intake() -> None:
    result = verify_intake(DEMO_SCAFFOLD_RUN)

    assert result.valid, result.errors


@pytest.mark.skipif(CAL_ROOT is None, reason="Claim Audit Lab root not available")
def test_phase4_demo_runner_succeeds_and_writes_expected_summary() -> None:
    _run_demo("--force")

    summary = _load_json(DEMO_BUILD / "handoff_summary.json")
    final_bundle = DEMO_BUILD / "final-bundle"
    audited_bundle = DEMO_BUILD / "cal-audited" / "final-bundle-audited"

    assert summary["coverage"]["inconsistency_count"] == 0
    assert summary["final_bundle"]["reviewer_sign_off_required"] is True
    assert summary["audited_bundle"]["reviewer_sign_off_required"] is True
    assert summary["audited_bundle"]["audited_verdicts"]["clm-supported"] == "supported"
    assert summary["audited_bundle"]["audited_verdicts"]["clm-weak"] in {
        "needs_source",
        "unsupported",
    }
    assert summary["audited_bundle"]["audited_verdicts"]["clm-needs-review"]

    assertions = summary["provenance_assertions"]
    assert all(assertions.values())
    assert compute_bundle_tree_hash(final_bundle) == summary["final_bundle"]["bundle_hash"]
    _assert_cal_loader_reloads(final_bundle, audited_bundle)


@pytest.mark.skipif(CAL_ROOT is None, reason="Claim Audit Lab root not available")
def test_phase4_demo_runner_refuses_non_empty_output_without_force() -> None:
    _run_demo("--force")

    result = subprocess.run(
        [str(REPO_ROOT / ".venv" / "bin" / "python"), str(RUNNER)],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode != 0
    assert "Output directory is not empty" in result.stdout


@pytest.mark.skipif(CAL_ROOT is None, reason="Claim Audit Lab root not available")
def test_phase4_demo_runner_is_deterministic_after_normalizing_runtime_fields(
    tmp_path: Path,
) -> None:
    _run_demo("--force")
    first = tmp_path / "first"
    shutil.copytree(DEMO_BUILD, first)

    _run_demo("--force")
    second = tmp_path / "second"
    shutil.copytree(DEMO_BUILD, second)

    assert _normalized_tree(first) == _normalized_tree(second)


def _run_demo(*args: str) -> None:
    result = subprocess.run(
        [str(REPO_ROOT / ".venv" / "bin" / "python"), str(RUNNER), *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout


def _assert_cal_loader_reloads(final_bundle: Path, audited_bundle: Path) -> None:
    final_deviations = DEMO_BUILD / "deviations-final"
    audited_deviations = DEMO_BUILD / "deviations-audited"
    code = (
        "from pathlib import Path\n"
        "from claim_audit_lab.contracts.bundle_loader import load_bundle\n"
        f"load_bundle(Path({str(final_bundle)!r}), "
        f"deviations_dir=Path({str(final_deviations)!r}))\n"
        f"load_bundle(Path({str(audited_bundle)!r}), "
        f"deviations_dir=Path({str(audited_deviations)!r}))\n"
    )
    result = subprocess.run(
        [str(CAL_PYTHON), "-c", code],
        cwd=CAL_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout


def _normalized_tree(root: Path) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for path in sorted(file for file in root.rglob("*") if file.is_file()):
        rel = path.relative_to(root).as_posix()
        if path.suffix in {".yaml", ".yml"}:
            normalized[rel] = _normalize_data(yaml.safe_load(path.read_text(encoding="utf-8")))
        elif path.suffix == ".json":
            normalized[rel] = _normalize_data(json.loads(path.read_text(encoding="utf-8")))
        elif path.suffix == ".md":
            normalized[rel] = _normalize_text(path.read_text(encoding="utf-8"))
        else:
            normalized[rel] = _normalize_text(path.read_text(encoding="utf-8"))
    return normalized


def _normalize_data(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _volatile_placeholder(key, item)
            if _is_volatile_key(key)
            else _normalize_data(item)
            for key, item in sorted(value.items())
        }
    if isinstance(value, list):
        return [_normalize_data(item) for item in value]
    if isinstance(value, str):
        return _normalize_text(value)
    return value


def _is_volatile_key(key: str) -> bool:
    return key.endswith("_utc") or key in TIMESTAMP_KEYS or key in HASH_KEYS or key in ID_KEYS


def _volatile_placeholder(key: str, value: Any) -> str:
    if value is None:
        return "VOLATILE:null"
    return f"VOLATILE:{key}"


def _normalize_text(text: str) -> str:
    text = re.sub(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "TIMESTAMP", text)
    text = re.sub(r"sha256:[0-9a-f]{64}", "HASH", text)
    text = re.sub(r"\b[0-9a-f]{64}\b", "HASH", text)
    text = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "UUID",
        text,
    )
    text = re.sub(r"cal-audit-[0-9a-f-]{36}", "AUDIT-RUN-ID", text)
    return text


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data
