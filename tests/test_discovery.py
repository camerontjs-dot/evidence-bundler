"""Tests for explicit project path discovery and resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from evidence_bundler.contracts.discovery import (
    resolve_apparatus_contracts_root,
    resolve_claim_audit_lab_root,
)


def test_resolve_claim_audit_lab_root_explicit(tmp_path: Path) -> None:
    # Explicit CLI arg that exists
    d1 = tmp_path / "cal_explicit"
    d1.mkdir()
    resolved = resolve_claim_audit_lab_root(explicit_path=d1)
    assert resolved == d1.resolve()

    # Explicit CLI arg that does not exist
    d2 = tmp_path / "cal_missing"
    with pytest.raises(FileNotFoundError) as exc_info:
        resolve_claim_audit_lab_root(explicit_path=d2)
    assert "Explicit Claim Audit Lab root path does not exist" in str(exc_info.value)


def test_resolve_claim_audit_lab_root_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Env var that exists
    d1 = tmp_path / "cal_env"
    d1.mkdir()
    monkeypatch.setenv("CLAIM_AUDIT_LAB_ROOT", str(d1))
    resolved = resolve_claim_audit_lab_root()
    assert resolved == d1.resolve()

    # Env var that does not exist
    monkeypatch.setenv("CLAIM_AUDIT_LAB_ROOT", str(tmp_path / "missing"))
    with pytest.raises(FileNotFoundError) as exc_info:
        resolve_claim_audit_lab_root()
    assert (
        "CLAIM_AUDIT_LAB_ROOT environment variable path does not exist"
        in str(exc_info.value)
    )


def test_resolve_apparatus_contracts_root_explicit(tmp_path: Path) -> None:
    # Explicit parameter that exists
    d1 = tmp_path / "ac_explicit"
    d1.mkdir()
    resolved = resolve_apparatus_contracts_root(explicit_path=d1)
    assert resolved == d1.resolve()

    # Explicit parameter that does not exist
    d2 = tmp_path / "ac_missing"
    with pytest.raises(FileNotFoundError) as exc_info:
        resolve_apparatus_contracts_root(explicit_path=d2)
    assert "Explicit Apparatus Contracts root path does not exist" in str(exc_info.value)


def test_resolve_apparatus_contracts_root_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Env var that exists
    d1 = tmp_path / "ac_env"
    d1.mkdir()
    monkeypatch.setenv("APPARATUS_CONTRACTS_ROOT", str(d1))
    resolved = resolve_apparatus_contracts_root()
    assert resolved == d1.resolve()

    # Env var that does not exist
    monkeypatch.setenv("APPARATUS_CONTRACTS_ROOT", str(tmp_path / "missing"))
    with pytest.raises(FileNotFoundError) as exc_info:
        resolve_apparatus_contracts_root()
    assert (
        "APPARATUS_CONTRACTS_ROOT environment variable path does not exist"
        in str(exc_info.value)
    )


def test_resolve_cal_root_deterministic_error(monkeypatch: pytest.MonkeyPatch) -> None:
    # Remove env var
    monkeypatch.delenv("CLAIM_AUDIT_LAB_ROOT", raising=False)

    # We point __file__ search logic away from valid siblings by mock or we just
    # check the list of searched paths. We can temporarily mock Path.exists to return False.
    original_exists = Path.exists
    def mock_exists(self: Path) -> bool:
        # Prevent finding the actual siblings in the repo
        if "claim-audit-lab" in str(self):
            return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", mock_exists)
    with pytest.raises(FileNotFoundError) as exc_info:
        resolve_claim_audit_lab_root()

    err_str = str(exc_info.value)
    assert "Could not resolve Claim Audit Lab root. Checked locations:" in err_str
    assert "claim-audit-lab" in err_str

