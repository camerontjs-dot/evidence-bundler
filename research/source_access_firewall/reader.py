from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pyarrow as pa
import pyarrow.parquet as pq

READER_VERSION = "source-access-firewall/0.1.0"
REGISTRY_PATH = Path(__file__).with_name("field_registry.json")


class AccessFirewallError(RuntimeError):
    def __init__(self, code: str, message: str, receipt: Mapping[str, Any] | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.receipt = dict(receipt or {})


@dataclass(frozen=True)
class FilePlan:
    ordinal: int
    path: Path
    sha256: str
    byte_size: int
    descriptor: tuple[tuple[str, str, bool], ...]
    schema_hash: str
    resolved: tuple[str, ...]
    forbidden_present: tuple[str, ...]
    unknown_present: tuple[str, ...]


@dataclass(frozen=True)
class AccessResult:
    batches_by_file: tuple[tuple[pa.RecordBatch, ...], ...]
    receipt: Mapping[str, Any]


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _json_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _normalize(value: str) -> str:
    return value.strip().lower()


def _validate_registry(registry: Mapping[str, Any]) -> None:
    artifact_types = registry.get("artifact_types")
    forbidden = registry.get("forbidden_canonical_fields")
    aliases = registry.get("forbidden_aliases", {})
    if not isinstance(artifact_types, dict) or not artifact_types:
        raise AccessFirewallError("EMPTY_ALLOWLIST", "artifact allow-list registry is empty")
    if not isinstance(forbidden, list) or not forbidden:
        raise AccessFirewallError("EMPTY_FORBIDDEN_REGISTRY", "forbidden registry is empty")
    if not isinstance(aliases, dict):
        raise AccessFirewallError("MALFORMED_FORBIDDEN_ALIASES", "aliases must be an object")
    for artifact_type, contract in artifact_types.items():
        mapping = contract.get("allowed_logical_to_physical") if isinstance(contract, dict) else None
        required = contract.get("required_logical_fields") if isinstance(contract, dict) else None
        if not isinstance(mapping, dict) or not mapping:
            raise AccessFirewallError("EMPTY_ALLOWLIST", f"{artifact_type} allow-list is empty")
        if not isinstance(required, list) or not required:
            raise AccessFirewallError("EMPTY_REQUIRED_FIELDS", f"{artifact_type} required fields are empty")
        missing = sorted(set(required) - set(mapping))
        if missing:
            raise AccessFirewallError("REQUIRED_FIELD_NOT_ALLOWED", str(missing))
        for logical, physical in mapping.items():
            if not isinstance(logical, str) or not logical or not isinstance(physical, list) or not physical:
                raise AccessFirewallError("MALFORMED_ALLOWLIST", f"{artifact_type}:{logical}")
            if any(not isinstance(item, str) or not item for item in physical):
                raise AccessFirewallError("MALFORMED_ALLOWLIST", f"{artifact_type}:{logical}")


def _forbidden_indexes(registry: Mapping[str, Any]) -> tuple[set[str], dict[str, str]]:
    canonical = {_normalize(str(x)) for x in registry["forbidden_canonical_fields"]}
    aliases = {_normalize(str(k)): _normalize(str(v)) for k, v in registry.get("forbidden_aliases", {}).items()}
    return canonical, aliases


def _classify_forbidden(path: str, registry: Mapping[str, Any]) -> str | None:
    canonical, aliases = _forbidden_indexes(registry)
    normalized = _normalize(path)
    leaf = normalized.rsplit(".", 1)[-1]
    for candidate in (normalized, leaf):
        if candidate in canonical:
            return candidate
        if candidate in aliases:
            return aliases[candidate]
    return None


def _field_paths(fields: Iterable[pa.Field], prefix: str = "") -> list[str]:
    fields = list(fields)
    names = [field.name for field in fields]
    if len(names) != len(set(names)):
        raise AccessFirewallError("MALFORMED_SCHEMA", f"duplicate field under {prefix or '$'}")
    paths: list[str] = []
    for field in fields:
        path = f"{prefix}.{field.name}" if prefix else field.name
        if pa.types.is_struct(field.type):
            paths.extend(_field_paths(field.type, path))
        else:
            paths.append(path)
    return paths


def _schema_descriptor(schema: pa.Schema) -> tuple[tuple[str, str, bool], ...]:
    descriptor: list[tuple[str, str, bool]] = []

    def walk(fields: Iterable[pa.Field], prefix: str = "") -> None:
        fields = list(fields)
        names = [field.name for field in fields]
        if len(names) != len(set(names)):
            raise AccessFirewallError("MALFORMED_SCHEMA", f"duplicate field under {prefix or '$'}")
        for field in fields:
            path = f"{prefix}.{field.name}" if prefix else field.name
            if pa.types.is_struct(field.type):
                walk(field.type, path)
            else:
                descriptor.append((path, str(field.type), bool(field.nullable)))

    walk(schema)
    return tuple(descriptor)


def _contract(registry: Mapping[str, Any], artifact_type: str) -> Mapping[str, Any]:
    try:
        return registry["artifact_types"][artifact_type]
    except KeyError as exc:
        raise AccessFirewallError("UNKNOWN_ARTIFACT_TYPE", artifact_type) from exc


def _validate_request(
    requested: Sequence[str] | None,
    contract: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> tuple[str, ...]:
    if requested is None:
        raise AccessFirewallError("COLUMNS_NONE_FORBIDDEN", "columns must be explicit")
    requested = tuple(str(x) for x in requested)
    if not requested:
        raise AccessFirewallError("EMPTY_REQUEST", "at least one field is required")
    if len(requested) != len(set(requested)):
        raise AccessFirewallError("DUPLICATE_REQUESTED_FIELD", "duplicate requested field")
    if any("*" in item for item in requested):
        raise AccessFirewallError("WILDCARD_FORBIDDEN", "wildcard requests are prohibited")
    if any(_classify_forbidden(item, registry) is not None for item in requested):
        raise AccessFirewallError("FORBIDDEN_FIELD_REQUESTED", "forbidden field requested")
    mapping = contract["allowed_logical_to_physical"]
    undeclared = [item for item in requested if item not in mapping]
    if undeclared:
        raise AccessFirewallError("UNDECLARED_LOGICAL_FIELD", str(undeclared))
    missing_required = [item for item in contract["required_logical_fields"] if item not in requested]
    if missing_required:
        raise AccessFirewallError("REQUIRED_FIELD_NOT_REQUESTED", str(missing_required))
    return requested


def _allowed_physical(contract: Mapping[str, Any]) -> set[str]:
    return {item for values in contract["allowed_logical_to_physical"].values() for item in values}


def _resolve_schema(
    schema: pa.Schema,
    requested: Sequence[str],
    contract: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[tuple[str, str, bool], ...]]:
    leaf_paths = tuple(_field_paths(schema))
    present = set(leaf_paths)
    mapping = contract["allowed_logical_to_physical"]

    def matches_for(logical: str) -> list[str]:
        return [
            candidate
            for candidate in mapping[logical]
            if candidate in present or any(path.startswith(candidate + ".") for path in leaf_paths)
        ]

    for logical in contract["required_logical_fields"]:
        matches = matches_for(logical)
        if not matches:
            raise AccessFirewallError("MISSING_REQUIRED_FIELD", logical)
        if len(matches) > 1:
            raise AccessFirewallError("AMBIGUOUS_PHYSICAL_FIELD", f"{logical}:{matches}")

    resolved: list[str] = []
    for logical in requested:
        matches = matches_for(logical)
        if not matches:
            raise AccessFirewallError("REQUESTED_FIELD_ABSENT", logical)
        if len(matches) > 1:
            raise AccessFirewallError("AMBIGUOUS_PHYSICAL_FIELD", f"{logical}:{matches}")
        chosen = matches[0]
        if any(path.startswith(chosen + ".") for path in leaf_paths):
            raise AccessFirewallError("PARENT_PROJECTION_UNSAFE", chosen)
        if _classify_forbidden(chosen, registry) is not None:
            raise AccessFirewallError("ALLOWLIST_FORBIDDEN_COLLISION", chosen)
        resolved.append(chosen)

    forbidden = tuple(sorted(path for path in leaf_paths if _classify_forbidden(path, registry) is not None))
    allowed = _allowed_physical(contract)
    unknown = tuple(sorted(path for path in leaf_paths if path not in allowed and path not in forbidden))
    return tuple(resolved), forbidden, unknown, _schema_descriptor(schema)


def _open_parquet_file(path: Path) -> pq.ParquetFile:
    return pq.ParquetFile(path)


def _runtime() -> dict[str, str]:
    try:
        arrow = importlib.metadata.version("pyarrow")
    except importlib.metadata.PackageNotFoundError:
        arrow = getattr(pa, "__version__", "unknown")
    return {"python": platform.python_version(), "pyarrow": arrow}


def _base_receipt(
    artifact_id: str,
    artifact_type: str,
    requested: Sequence[str] | None,
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "receipt_version": "1.0.0",
        "reader_version": READER_VERSION,
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "registry_version": registry.get("registry_version"),
        "requested_logical_fields": None if requested is None else list(requested),
        "source_artifacts": [],
        "schema_hash": None,
        "resolved_physical_columns": [],
        "returned_columns": [],
        "explicitly_forbidden_columns_present": [],
        "unknown_columns_present": [],
        "forbidden_column_requested": bool(requested and any(_classify_forbidden(x, registry) for x in requested)),
        "forbidden_columns_deserialized": False,
        "physical_read_calls": [],
        "projection_guarantee": {
            "schema_surface": "pyarrow.parquet.read_schema",
            "read_surface": "pyarrow.parquet.ParquetFile.iter_batches",
            "explicit_columns_required": True,
            "use_pandas_metadata": False,
            "unprojected_fallback_present": False
        },
        "runtime": _runtime(),
        "reader_source_sha256": _sha256_file(Path(__file__)),
        "result": "PENDING",
        "failure_code": None
    }


def _emit(path: Path, receipt: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _prepare(
    paths: Sequence[Path],
    requested: Sequence[str],
    contract: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> tuple[FilePlan, ...]:
    plans: list[FilePlan] = []
    for ordinal, raw_path in enumerate(paths):
        path = Path(raw_path)
        if not path.is_file():
            raise AccessFirewallError("SOURCE_NOT_FILE", str(path))
        artifact_hash = _sha256_file(path)
        try:
            schema = pq.read_schema(path)
        except Exception as exc:
            raise AccessFirewallError("SCHEMA_INSPECTION_FAILED", type(exc).__name__) from exc
        resolved, forbidden, unknown, descriptor = _resolve_schema(schema, requested, contract, registry)
        plans.append(
            FilePlan(
                ordinal=ordinal,
                path=path,
                sha256=artifact_hash,
                byte_size=path.stat().st_size,
                descriptor=descriptor,
                schema_hash=_json_hash(descriptor),
                resolved=resolved,
                forbidden_present=forbidden,
                unknown_present=unknown,
            )
        )
    return tuple(plans)


def read_projected(
    *,
    artifact_id: str,
    artifact_type: str,
    paths: Sequence[Path],
    requested_logical_fields: Sequence[str] | None,
    receipt_path: Path,
    batch_size: int = 4096,
    registry: Mapping[str, Any] | None = None,
) -> AccessResult:
    """Fail closed unless row materialization uses an explicit safe Parquet projection."""
    active_registry = dict(registry or load_registry())
    receipt = _base_receipt(artifact_id, artifact_type, requested_logical_fields, active_registry)
    try:
        _validate_registry(active_registry)
        contract = _contract(active_registry, artifact_type)
        requested = _validate_request(requested_logical_fields, contract, active_registry)
        if not paths:
            raise AccessFirewallError("EMPTY_SOURCE_SET", "no Parquet files supplied")
        if batch_size <= 0:
            raise AccessFirewallError("INVALID_BATCH_SIZE", str(batch_size))

        # Every file is schema-preflighted before the first row batch is materialized.
        plans = _prepare(paths, requested, contract, active_registry)
        receipt["source_artifacts"] = [
            {"ordinal": p.ordinal, "name": p.path.name, "sha256": p.sha256, "bytes": p.byte_size, "schema_hash": p.schema_hash}
            for p in plans
        ]
        receipt["schema_hash"] = _json_hash([p.descriptor for p in plans])
        receipt["resolved_physical_columns"] = [{"ordinal": p.ordinal, "columns": list(p.resolved)} for p in plans]
        receipt["explicitly_forbidden_columns_present"] = [{"ordinal": p.ordinal, "columns": list(p.forbidden_present)} for p in plans]
        receipt["unknown_columns_present"] = [{"ordinal": p.ordinal, "columns": list(p.unknown_present)} for p in plans]

        batches_by_file: list[tuple[pa.RecordBatch, ...]] = []
        returned: list[dict[str, Any]] = []
        for plan in plans:
            columns = list(plan.resolved)
            if not columns:
                raise AccessFirewallError("EMPTY_PHYSICAL_PROJECTION", "zero columns")
            call = {
                "ordinal": plan.ordinal,
                "api": "ParquetFile.iter_batches",
                "columns_argument": columns,
                "use_pandas_metadata": False,
                "batch_size": batch_size,
                "returned_batch_columns": []
            }
            receipt["physical_read_calls"].append(call)
            parquet_file = _open_parquet_file(plan.path)
            file_batches: list[pa.RecordBatch] = []
            try:
                iterator = parquet_file.iter_batches(
                    batch_size=batch_size,
                    columns=columns,
                    use_pandas_metadata=False,
                )
                for batch in iterator:
                    returned_paths = tuple(_field_paths(batch.schema))
                    call["returned_batch_columns"].append(list(returned_paths))
                    if set(returned_paths) != set(plan.resolved):
                        raise AccessFirewallError("RETURNED_COLUMN_MISMATCH", f"{plan.resolved}!={returned_paths}")
                    bad = [path for path in returned_paths if _classify_forbidden(path, active_registry) is not None]
                    if bad:
                        receipt["forbidden_columns_deserialized"] = True
                        raise AccessFirewallError("FORBIDDEN_COLUMN_DESERIALIZED", str(bad))
                    file_batches.append(batch)
            except AccessFirewallError:
                raise
            except Exception as exc:
                raise AccessFirewallError("PROJECTED_READ_FAILED", type(exc).__name__) from exc
            batches_by_file.append(tuple(file_batches))
            returned.append({"ordinal": plan.ordinal, "columns": sorted({x for batch in file_batches for x in _field_paths(batch.schema)})})

        receipt["returned_columns"] = returned
        receipt["forbidden_columns_deserialized"] = False
        receipt["result"] = "SUCCESS"
        _emit(receipt_path, receipt)
        return AccessResult(tuple(batches_by_file), receipt)
    except AccessFirewallError as exc:
        receipt["result"] = "FAIL_CLOSED"
        receipt["failure_code"] = exc.code
        _emit(receipt_path, receipt)
        exc.receipt = dict(receipt)
        raise
    except Exception as exc:
        receipt["result"] = "FAIL_CLOSED"
        receipt["failure_code"] = "UNEXPECTED_READER_FAILURE"
        _emit(receipt_path, receipt)
        raise AccessFirewallError("UNEXPECTED_READER_FAILURE", type(exc).__name__, receipt) from exc
