"""Helpers for explicit external project discovery and path resolution."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_claim_audit_lab_root(explicit_path: Path | str | None = None) -> Path:
    """Resolve the Claim Audit Lab root directory based on precedence.

    Precedence:
    1. Explicit CLI argument
    2. CLAIM_AUDIT_LAB_ROOT environment variable
    3. Deterministic MainFrame sibling (../claim-audit-lab/workbench relative to project root)
    4. Deterministic legacy sibling (../claim-audit-lab relative to project root)
    """
    # parents[3] matches: src/evidence_bundler/contracts/discovery.py -> parents[3] is workbench
    repo_root = Path(__file__).resolve().parents[3]
    attempted: list[str] = []

    # 1. Explicit CLI argument
    if explicit_path is not None:
        path = Path(explicit_path).resolve()
        if path.exists() and path.is_dir():
            return path
        raise FileNotFoundError(
            f"Explicit Claim Audit Lab root path does not exist or is not a directory: {path}"
        )

    # 2. CLAIM_AUDIT_LAB_ROOT environment variable
    env_val = os.environ.get("CLAIM_AUDIT_LAB_ROOT")
    if env_val:
        path = Path(env_val).resolve()
        if path.exists() and path.is_dir():
            return path
        raise FileNotFoundError(
            "CLAIM_AUDIT_LAB_ROOT environment variable path does not exist "
            f"or is not a directory: {path}"
        )

    # 3. Deterministic MainFrame sibling
    mf_sibling = repo_root.parent.parent / "claim-audit-lab" / "workbench"
    attempted.append(str(mf_sibling))
    if mf_sibling.exists() and mf_sibling.is_dir():
        return mf_sibling

    # 4. Deterministic legacy sibling
    legacy_sibling = repo_root.parent / "claim-audit-lab"
    attempted.append(str(legacy_sibling))
    if legacy_sibling.exists() and legacy_sibling.is_dir():
        return legacy_sibling

    raise FileNotFoundError(
        "Could not resolve Claim Audit Lab root. Checked locations:\n"
        + "\n".join(f"- {loc}" for loc in attempted)
        + "\nTo resolve this, set the CLAIM_AUDIT_LAB_ROOT environment variable "
        "or pass --claim-audit-root."
    )


def resolve_apparatus_contracts_root(explicit_path: Path | str | None = None) -> Path:
    """Resolve the Apparatus Contracts root directory based on precedence.

    Precedence:
    1. Explicit path parameter (if any)
    2. APPARATUS_CONTRACTS_ROOT environment variable
    3. Deterministic MainFrame sibling (../apparatus-contracts relative to project root)
    4. Deterministic legacy sibling (../apparatus-contracts relative to project root)
    """
    repo_root = Path(__file__).resolve().parents[3]
    attempted: list[str] = []

    # 1. Explicit path
    if explicit_path is not None:
        path = Path(explicit_path).resolve()
        if path.exists() and path.is_dir():
            return path
        raise FileNotFoundError(
            f"Explicit Apparatus Contracts root path does not exist or is not a directory: {path}"
        )

    # 2. APPARATUS_CONTRACTS_ROOT environment variable
    env_val = os.environ.get("APPARATUS_CONTRACTS_ROOT")
    if env_val:
        path = Path(env_val).resolve()
        if path.exists() and path.is_dir():
            return path
        raise FileNotFoundError(
            "APPARATUS_CONTRACTS_ROOT environment variable path does not exist "
            f"or is not a directory: {path}"
        )


    # 3. Deterministic MainFrame sibling
    mf_sibling = repo_root.parent.parent / "apparatus-contracts"
    attempted.append(str(mf_sibling))
    if mf_sibling.exists() and mf_sibling.is_dir():
        return mf_sibling

    # 4. Deterministic legacy sibling
    legacy_sibling = repo_root.parent / "apparatus-contracts"
    attempted.append(str(legacy_sibling))
    if legacy_sibling.exists() and legacy_sibling.is_dir():
        return legacy_sibling

    raise FileNotFoundError(
        "Could not resolve Apparatus Contracts root. Checked locations:\n"
        + "\n".join(f"- {loc}" for loc in attempted)
        + "\nTo resolve this, set the APPARATUS_CONTRACTS_ROOT environment variable."
    )
