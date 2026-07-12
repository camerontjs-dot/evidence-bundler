"""Safe YAML helpers for contract artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar, cast

import yaml
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

YAML_DUMP_KWARGS: dict[str, Any] = {
    "allow_unicode": True,
    "default_flow_style": False,
    "indent": 2,
    "sort_keys": False,
}


def yaml_to_string(data: dict[str, Any]) -> str:
    """Serialize JSON-safe data deterministically without Python object tags."""
    return cast(str, yaml.safe_dump(data, **YAML_DUMP_KWARGS))



def dump_yaml(data: dict[str, Any], path: Path) -> None:
    """Write JSON-safe data to YAML using safe serialization only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml_to_string(data), encoding="utf-8")


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping with PyYAML safe_load."""
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {path}")
    return data


def model_to_yaml_dict(model: BaseModel, *, exclude_none: bool = False) -> dict[str, Any]:
    """Convert a Pydantic model to JSON-safe primitives before YAML serialization."""
    data = model.model_dump(mode="json", exclude_none=exclude_none)
    if not isinstance(data, dict):
        raise TypeError("Expected Pydantic model to dump to a mapping")
    return data


def write_model_yaml(model: BaseModel, path: Path, *, exclude_none: bool = False) -> None:
    """Write a Pydantic model through JSON-safe serialization."""
    dump_yaml(model_to_yaml_dict(model, exclude_none=exclude_none), path)


def load_model_yaml(model_type: type[T], path: Path) -> T:
    """Load a YAML mapping and validate it as a Pydantic model."""
    return model_type.model_validate(load_yaml(path))

