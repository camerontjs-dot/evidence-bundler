"""Shared test fixtures for Evidence Bundler."""

from __future__ import annotations

from pathlib import Path
from shutil import copytree

import pytest


@pytest.fixture(scope="session")
def fixture_scaffold_run_dir() -> Path:
    """Committed minimal C-A scaffold-run fixture."""
    return Path(__file__).parent / "fixtures" / "scaffold-run-minimal"


@pytest.fixture()
def scaffold_run_tmp(fixture_scaffold_run_dir: Path, tmp_path: Path) -> Path:
    """Writable copy of the committed scaffold-run fixture."""
    destination = tmp_path / "scaffold-run-minimal"
    copytree(fixture_scaffold_run_dir, destination)
    return destination


@pytest.fixture(scope="session")
def mixed_scaffold_run_dir() -> Path:
    """Committed C-A fixture with Markdown and plain-text sources."""
    return Path(__file__).parent / "fixtures" / "scaffold-run-mixed-formats"


@pytest.fixture()
def mixed_scaffold_run_tmp(mixed_scaffold_run_dir: Path, tmp_path: Path) -> Path:
    """Writable copy of the mixed-format scaffold-run fixture."""
    destination = tmp_path / "scaffold-run-mixed-formats"
    copytree(mixed_scaffold_run_dir, destination)
    return destination


def assert_no_python_yaml_tags(root: Path) -> None:
    """Assert generated YAML is parser-portable and has no PyYAML object tags."""
    offenders = []
    for path in root.rglob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        if "!!python" in text:
            offenders.append(path.relative_to(root).as_posix())
    assert offenders == []
