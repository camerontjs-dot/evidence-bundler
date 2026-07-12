"""Deterministic hashing helpers for C-A intake and C-B bundle sealing.

Directory hashes are computed from sorted relative POSIX paths plus each file's
SHA-256 digest. This makes the hash independent of filesystem metadata.

Two C-B files carry self-referential hash fields. Before hashing
``audit_config.yaml``, ``config_hash`` is normalized to ``sha256:pending``.
Before hashing ``bundle_manifest.yaml``, ``bundle.bundle_hash`` is normalized
to ``sha256:pending``. ``SHA256SUMS`` is always excluded from tree hashes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from hashlib import sha256
from pathlib import Path
from typing import Any

from evidence_bundler.contracts.yaml_io import load_yaml, yaml_to_string
from evidence_bundler.models.common import PENDING_HASH

SHA256_PREFIX = "sha256:"


def sha256_hexdigest(data: bytes) -> str:
    """Return the SHA-256 hex digest for bytes."""
    return sha256(data).hexdigest()


def sha256_value(data: bytes) -> str:
    """Return a contract-shaped SHA-256 value for bytes."""
    return f"{SHA256_PREFIX}{sha256_hexdigest(data)}"


def hash_text(text: str) -> str:
    """Return a contract-shaped SHA-256 value for UTF-8 text."""
    return sha256_value(text.encode("utf-8"))


def hash_file(path: Path) -> str:
    """Return a contract-shaped SHA-256 value for a file's exact bytes."""
    return sha256_value(path.read_bytes())


def hash_file_hex(path: Path) -> str:
    """Return a raw SHA-256 hex digest for a file's exact bytes."""
    return sha256_hexdigest(path.read_bytes())


def strip_hash_prefix(value: str) -> str:
    """Return the raw hex part of a contract-shaped hash value."""
    if not value.startswith(SHA256_PREFIX):
        raise ValueError(f"Expected sha256: hash value, got {value!r}")
    return value.removeprefix(SHA256_PREFIX)


def iter_handoff_files(root: Path, *, exclude_names: Iterable[str] = ("SHA256SUMS",)) -> list[Path]:
    """Return sorted handoff files beneath root.

    Excludes names such as SHA256SUMS and root-level deviations/.
    """
    excluded = set(exclude_names)
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name in excluded:
            continue
        rel_parts = path.relative_to(root).parts
        if rel_parts and rel_parts[0] == "deviations":
            continue
        files.append(path)
    return sorted(files)


def compute_directory_hash(root: Path) -> str:
    """Hash a directory tree from sorted relative paths and file digests."""
    hasher = sha256()
    for path in iter_handoff_files(root, exclude_names=()):
        rel = path.relative_to(root).as_posix()
        digest = hash_file_hex(path)
        hasher.update(f"{rel}\0{digest}\n".encode())
    return f"{SHA256_PREFIX}{hasher.hexdigest()}"


def compute_corpus_hash(corpus_dir: Path) -> str:
    """Compute the C-A corpus_hash from the corpus/ directory tree only."""
    return compute_directory_hash(corpus_dir)


def write_sha256sums(root: Path) -> Path:
    """Write SHA256SUMS for every handoff file under root except SHA256SUMS itself."""
    lines = []
    for path in iter_handoff_files(root):
        rel = path.relative_to(root).as_posix()
        lines.append(f"{hash_file_hex(path)}  {rel}")
    sums_path = root / "SHA256SUMS"
    sums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sums_path


def verify_sha256sums(root: Path) -> list[str]:
    """Return mismatch messages for SHA256SUMS, or an empty list if it verifies."""
    sums_path = root / "SHA256SUMS"
    if not sums_path.exists():
        return ["SHA256SUMS file missing"]

    errors: list[str] = []
    expected_paths: set[str] = set()
    for line_number, line in enumerate(sums_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            expected_hash, rel = line.split(maxsplit=1)
        except ValueError:
            errors.append(f"SHA256SUMS line {line_number} is malformed")
            continue
        expected_paths.add(rel)
        target = root / rel
        if not target.exists():
            errors.append(f"SHA256SUMS references missing file: {rel}")
            continue
        actual_hash = hash_file_hex(target)
        if actual_hash != expected_hash:
            errors.append(f"SHA256SUMS mismatch for {rel}")

    actual_paths = {path.relative_to(root).as_posix() for path in iter_handoff_files(root)}
    missing_from_sums = sorted(actual_paths - expected_paths)
    if missing_from_sums:
        errors.append(f"SHA256SUMS missing entries: {', '.join(missing_from_sums)}")
    return errors


def normalized_yaml_hash(path: Path, normalizer: Callable[[dict[str, Any]], None]) -> str:
    """Hash a YAML file after applying an in-memory normalization."""
    data = load_yaml(path)
    normalizer(data)
    return hash_text(yaml_to_string(data))


def normalize_audit_config_hash(data: dict[str, Any]) -> None:
    """Normalize audit_config.config_hash before self-hashing."""
    data["config_hash"] = PENDING_HASH


def normalize_bundle_manifest_hash(data: dict[str, Any]) -> None:
    """Normalize bundle_manifest.bundle.bundle_hash before self-hashing."""
    bundle = data.get("bundle")
    if not isinstance(bundle, dict):
        raise ValueError("bundle_manifest.yaml missing bundle mapping")
    bundle["bundle_hash"] = PENDING_HASH


def hash_audit_config_file(path: Path) -> str:
    """Compute audit_config.yaml hash with config_hash normalized."""
    return normalized_yaml_hash(path, normalize_audit_config_hash)


def hash_bundle_manifest_file(path: Path) -> str:
    """Compute bundle_manifest.yaml hash with bundle_hash normalized."""
    return normalized_yaml_hash(path, normalize_bundle_manifest_hash)


def compute_bundle_tree_hash(bundle_dir: Path) -> str:
    """Compute C-B bundle_hash with self-referential fields normalized."""
    hasher = sha256()
    for path in iter_handoff_files(bundle_dir):
        rel = path.relative_to(bundle_dir).as_posix()
        if rel == "audit_config.yaml":
            digest = strip_hash_prefix(hash_audit_config_file(path))
        elif rel == "bundle_manifest.yaml":
            digest = strip_hash_prefix(hash_bundle_manifest_file(path))
        else:
            digest = hash_file_hex(path)
        hasher.update(f"{rel}\0{digest}\n".encode())
    return f"{SHA256_PREFIX}{hasher.hexdigest()}"
