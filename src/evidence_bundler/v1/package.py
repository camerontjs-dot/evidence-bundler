"""Immutable Evidence Bundler V1 candidate package contract."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from evidence_bundler.v1.contract_a import (
    CONTRACT_A_RELEASE_COMMIT,
    CONTRACT_A_VALIDATOR_BLOB,
    CONTRACT_A_VERSION,
    HASH_RE,
    ContractAValidationError,
    primary_targets,
    validate_contract_a,
)
from evidence_bundler.v1.retrieval import BM25_B, BM25_K1, ENGINE_ID, TOKENIZER_ID

PACKAGE_SCHEMA = "evidence-bundler-v1-package-candidate-1"
PACKAGE_CONTRACT_VERSION = "v1-candidate-1"
ADMISSION_SCHEMA = "evidence-bundler-admission-v1"


class EvidencePackageValidationError(ValueError):
    """Raised when a V1 candidate package fails its maintained contract."""


@dataclass(frozen=True)
class V1Config:
    """Deterministic maintained V1 retrieval and selection configuration."""

    candidate_depth: int = 5
    retained_k: int = 3
    chunk_max_chars: int = 1800
    chunk_overlap_chars: int = 80
    root_diagnostic: bool = False
    retrieval_engine: str = ENGINE_ID
    tokenizer: str = TOKENIZER_ID
    bm25_k1: float = BM25_K1
    bm25_b: float = BM25_B
    source_scope_policy: str = "all_contract_a_sources"
    query_strategy: str = "exact_primary_target_text"

    def __post_init__(self) -> None:
        integer_values = (
            self.candidate_depth,
            self.retained_k,
            self.chunk_max_chars,
            self.chunk_overlap_chars,
        )
        if any(isinstance(value, bool) or not isinstance(value, int) for value in integer_values):
            raise ValueError("V1 integer configuration fields must be integers")
        if self.candidate_depth < 1 or self.retained_k < 1:
            raise ValueError("candidate_depth and retained_k must be >= 1")
        if self.retained_k > self.candidate_depth:
            raise ValueError("retained_k must be <= candidate_depth")
        if self.chunk_max_chars < 1 or self.chunk_overlap_chars < 0:
            raise ValueError("invalid chunk bounds")
        if self.chunk_overlap_chars >= self.chunk_max_chars:
            raise ValueError("chunk_overlap_chars must be smaller than chunk_max_chars")
        if self.retrieval_engine != ENGINE_ID or self.tokenizer != TOKENIZER_ID:
            raise ValueError("unsupported V1 retrieval engine or tokenizer")
        if self.bm25_k1 != BM25_K1 or self.bm25_b != BM25_B:
            raise ValueError("V1 BM25 parameters are pinned at k1=1.5 and b=0.75")
        if self.source_scope_policy != "all_contract_a_sources":
            raise ValueError("V1 source scope must be all_contract_a_sources")
        if self.query_strategy != "exact_primary_target_text":
            raise ValueError("V1 query strategy must be exact_primary_target_text")

    def as_payload(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def identity(self) -> str:
        return hash_json(self.as_payload())


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def hash_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def hash_text(value: str) -> str:
    return hash_bytes(value.encode("utf-8"))


def hash_json(value: Any) -> str:
    return hash_bytes(canonical_json_bytes(value))


def query_identity(
    *,
    contract_a_sha256: str,
    proposition_id: str,
    text_sha256: str,
    retrieval_lane: str,
    config_sha256: str,
) -> str:
    digest = hash_json(
        {
            "contract_a_sha256": contract_a_sha256,
            "proposition_id": proposition_id,
            "text_sha256": text_sha256,
            "retrieval_lane": retrieval_lane,
            "config_sha256": config_sha256,
        }
    ).removeprefix("sha256:")
    return "query:" + digest[:32]


def retrieval_identity(query_id: str) -> str:
    digest = hash_json({"query_id": query_id, "engine": ENGINE_ID}).removeprefix("sha256:")
    return "retrieval:" + digest[:32]


def passage_identity(
    *,
    source_id: str,
    source_content_sha256: str,
    char_start: int,
    char_end: int,
    passage_sha256: str,
) -> str:
    digest = hash_json(
        {
            "source_id": source_id,
            "source_content_sha256": source_content_sha256,
            "char_start": char_start,
            "char_end": char_end,
            "passage_sha256": passage_sha256,
        }
    ).removeprefix("sha256:")
    return "passage:" + digest[:32]


def compute_package_sha256(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("package_sha256", None)
    return hash_json(payload)


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidencePackageValidationError(f"{path} must be an object")
    return value


def _array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvidencePackageValidationError(f"{path} must be an array")
    return value


def _exact(value: Any, keys: set[str], path: str) -> dict[str, Any]:
    row = _object(value, path)
    if set(row) != keys:
        raise EvidencePackageValidationError(
            f"{path} key mismatch: expected={sorted(keys)}, actual={sorted(row)}"
        )
    return row


def _nonblank(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidencePackageValidationError(f"{path} must be a nonblank string")
    return value


def _sha(value: Any, path: str) -> str:
    if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
        raise EvidencePackageValidationError(f"{path} must be lowercase sha256:<64 hex>")
    return value


def _config(value: Any) -> V1Config:
    keys = set(V1Config.__dataclass_fields__)
    row = _exact(value, keys, "$.config")
    integer_fields = {"candidate_depth", "retained_k", "chunk_max_chars", "chunk_overlap_chars"}
    for field in integer_fields:
        if isinstance(row[field], bool) or not isinstance(row[field], int):
            raise EvidencePackageValidationError(f"$.config.{field} must be an integer")
    if not isinstance(row["root_diagnostic"], bool):
        raise EvidencePackageValidationError("$.config.root_diagnostic must be boolean")
    try:
        return V1Config(**row)
    except (TypeError, ValueError) as exc:
        raise EvidencePackageValidationError(f"invalid $.config: {exc}") from exc


def load_admission(path: Path | None) -> dict[tuple[str, str], str]:
    """Load explicit retained-candidate review decisions."""
    if path is None:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidencePackageValidationError(f"invalid admission JSON: {exc}") from exc
    root = _exact(value, {"schema", "decisions"}, "admission")
    if root["schema"] != ADMISSION_SCHEMA:
        raise EvidencePackageValidationError(f"admission schema must equal {ADMISSION_SCHEMA!r}")
    decisions: dict[tuple[str, str], str] = {}
    for index, raw in enumerate(_array(root["decisions"], "admission.decisions")):
        path_label = f"admission.decisions[{index}]"
        row = _exact(raw, {"proposition_id", "passage_id", "decision"}, path_label)
        key = (
            _nonblank(row["proposition_id"], f"{path_label}.proposition_id"),
            _nonblank(row["passage_id"], f"{path_label}.passage_id"),
        )
        if row["decision"] not in {"accepted", "rejected", "needs-review"}:
            raise EvidencePackageValidationError(f"{path_label}.decision is invalid")
        if key in decisions:
            raise EvidencePackageValidationError(f"duplicate admission decision for {key!r}")
        decisions[key] = str(row["decision"])
    return decisions


def write_package(value: dict[str, Any], path: Path) -> None:
    validate_package(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(canonical_json_bytes(value))
    temporary.replace(path)


def load_package(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=lambda token: (_ for _ in ()).throw(
                EvidencePackageValidationError(f"non-finite JSON value is forbidden: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidencePackageValidationError(f"invalid package JSON: {exc}") from exc
    return validate_package(value)


def _validate_passage(
    row: dict[str, Any],
    *,
    path: str,
    sources: dict[str, dict[str, Any]],
) -> None:
    source_id = _nonblank(row["source_id"], f"{path}.source_id")
    if source_id not in sources:
        raise EvidencePackageValidationError(f"{path} references unknown source")
    source = sources[source_id]
    if row["source_content_sha256"] != source["content_sha256"]:
        raise EvidencePackageValidationError(f"{path}.source_content_sha256 mismatch")
    start, end = row["char_start"], row["char_end"]
    if (
        isinstance(start, bool)
        or not isinstance(start, int)
        or isinstance(end, bool)
        or not isinstance(end, int)
        or start < 0
        or end <= start
        or end > len(source["content"])
    ):
        raise EvidencePackageValidationError(f"{path} has invalid source offsets")
    text = _nonblank(row["text"], f"{path}.text")
    if source["content"][start:end] != text:
        raise EvidencePackageValidationError(f"{path}.text does not match source bytes at offsets")
    passage_sha = _sha(row["passage_sha256"], f"{path}.passage_sha256")
    if passage_sha != hash_text(text):
        raise EvidencePackageValidationError(f"{path}.passage_sha256 mismatch")
    expected_id = passage_identity(
        source_id=source_id,
        source_content_sha256=str(source["content_sha256"]),
        char_start=start,
        char_end=end,
        passage_sha256=passage_sha,
    )
    if row["passage_id"] != expected_id:
        raise EvidencePackageValidationError(f"{path}.passage_id content binding mismatch")


def validate_package(value: Any) -> dict[str, Any]:
    """Validate the exact maintained EB V1 candidate package contract."""
    top = {
        "schema",
        "contract_version",
        "producer",
        "contract_a_authority",
        "contract_a",
        "config",
        "config_sha256",
        "execution_state",
        "primary_targets",
        "retrieval_plans",
        "retrieval_executions",
        "candidates",
        "diagnostics",
        "package_sha256",
    }
    root = _exact(value, top, "$")
    if root["schema"] != PACKAGE_SCHEMA or root["contract_version"] != PACKAGE_CONTRACT_VERSION:
        raise EvidencePackageValidationError("unsupported V1 package schema/version")

    producer = _exact(root["producer"], {"producer_id", "producer_version"}, "$.producer")
    _nonblank(producer["producer_id"], "$.producer.producer_id")
    _nonblank(producer["producer_version"], "$.producer.producer_version")

    authority = _exact(
        root["contract_a_authority"],
        {"contract_version", "release_commit", "validator_blob"},
        "$.contract_a_authority",
    )
    if authority != {
        "contract_version": CONTRACT_A_VERSION,
        "release_commit": CONTRACT_A_RELEASE_COMMIT,
        "validator_blob": CONTRACT_A_VALIDATOR_BLOB,
    }:
        raise EvidencePackageValidationError("Contract A authority identity mismatch")

    try:
        contract_a = validate_contract_a(root["contract_a"])
        expected_targets = [dict(target) for target in primary_targets(contract_a)]
    except ContractAValidationError as exc:
        raise EvidencePackageValidationError(f"invalid embedded Contract A: {exc}") from exc
    source_rows = contract_a["sources"]
    sources = {str(row["source_id"]): row for row in source_rows}
    source_ids = sorted(sources)

    config = _config(root["config"])
    if root["config_sha256"] != config.identity:
        raise EvidencePackageValidationError("$.config_sha256 mismatch")
    targets = _array(root["primary_targets"], "$.primary_targets")
    if targets != expected_targets:
        raise EvidencePackageValidationError(
            "$.primary_targets must derive exactly from embedded Contract A"
        )
    targets_by_id = {str(row["proposition_id"]): row for row in targets}

    plans = _array(root["retrieval_plans"], "$.retrieval_plans")
    if len(plans) != len(targets):
        raise EvidencePackageValidationError("one retrieval plan is required per primary target")
    plans_by_id: dict[str, dict[str, Any]] = {}
    propositions_seen: set[str] = set()
    plan_keys = {
        "retrieval_id",
        "query_id",
        "proposition_id",
        "retrieval_lane",
        "query_text_sha256",
        "requested_source_ids",
        "intended_retrieval_ids",
    }
    for index, raw in enumerate(plans):
        path = f"$.retrieval_plans[{index}]"
        plan = _exact(raw, plan_keys, path)
        proposition_id = _nonblank(plan["proposition_id"], f"{path}.proposition_id")
        if proposition_id not in targets_by_id or proposition_id in propositions_seen:
            raise EvidencePackageValidationError(f"{path} has invalid/duplicate proposition")
        propositions_seen.add(proposition_id)
        target = targets_by_id[proposition_id]
        lane = "declared_child" if target["role"] == "declared_child" else "root"
        if plan["retrieval_lane"] != lane or plan["query_text_sha256"] != target["text_sha256"]:
            raise EvidencePackageValidationError(f"{path} target/lane mismatch")
        query_id = query_identity(
            contract_a_sha256=str(contract_a["handoff_sha256"]),
            proposition_id=proposition_id,
            text_sha256=str(target["text_sha256"]),
            retrieval_lane=lane,
            config_sha256=config.identity,
        )
        retrieval_id = retrieval_identity(query_id)
        if plan["query_id"] != query_id or plan["retrieval_id"] != retrieval_id:
            raise EvidencePackageValidationError(f"{path} content-derived identity mismatch")
        if plan["requested_source_ids"] != source_ids:
            raise EvidencePackageValidationError(f"{path} source scope mismatch")
        if plan["intended_retrieval_ids"] != [retrieval_id]:
            raise EvidencePackageValidationError(f"{path} intended retrieval mismatch")
        plans_by_id[retrieval_id] = plan

    executions = _array(root["retrieval_executions"], "$.retrieval_executions")
    if len(executions) != len(plans):
        raise EvidencePackageValidationError("one execution is required per retrieval plan")
    execution_keys = {
        "retrieval_id",
        "status",
        "searched_source_ids",
        "returned_source_ids",
        "returned_count",
        "candidate_depth_limit",
        "candidate_depth_hit",
        "aperture_state",
    }
    executions_by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(executions):
        path = f"$.retrieval_executions[{index}]"
        execution = _exact(raw, execution_keys, path)
        retrieval_id = _nonblank(execution["retrieval_id"], f"{path}.retrieval_id")
        if retrieval_id not in plans_by_id or retrieval_id in executions_by_id:
            raise EvidencePackageValidationError(f"{path} has invalid/duplicate retrieval_id")
        count = execution["returned_count"]
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or not 0 <= count <= config.candidate_depth
        ):
            raise EvidencePackageValidationError(f"{path}.returned_count is invalid")
        if execution["candidate_depth_limit"] != config.candidate_depth:
            raise EvidencePackageValidationError(f"{path}.candidate_depth_limit mismatch")
        if not isinstance(execution["candidate_depth_hit"], bool):
            raise EvidencePackageValidationError(f"{path}.candidate_depth_hit must be boolean")
        if execution["status"] == "not_run":
            expected = ([], [], 0, False, "not_run")
            actual = (
                execution["searched_source_ids"],
                execution["returned_source_ids"],
                count,
                execution["candidate_depth_hit"],
                execution["aperture_state"],
            )
            if actual != expected:
                raise EvidencePackageValidationError(f"{path} malformed not_run execution")
        elif execution["status"] == "completed":
            if execution["searched_source_ids"] != source_ids:
                raise EvidencePackageValidationError(f"{path} searched source scope mismatch")
            hit = count == config.candidate_depth
            aperture = "bounded_at_limit" if hit else "bounded_under_limit"
            if execution["candidate_depth_hit"] != hit or execution["aperture_state"] != aperture:
                raise EvidencePackageValidationError(f"{path} aperture derivation mismatch")
        else:
            raise EvidencePackageValidationError(f"{path}.status is invalid")
        executions_by_id[retrieval_id] = execution

    candidates = _array(root["candidates"], "$.candidates")
    candidate_keys = {
        "retrieval_id",
        "query_id",
        "proposition_id",
        "retrieval_lane",
        "passage_id",
        "source_id",
        "source_content_sha256",
        "char_start",
        "char_end",
        "passage_sha256",
        "text",
        "nomination_rank",
        "selection_state",
        "admission_state",
    }
    ranks: dict[str, list[int]] = {retrieval_id: [] for retrieval_id in plans_by_id}
    returned_sources: dict[str, set[str]] = {retrieval_id: set() for retrieval_id in plans_by_id}
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(candidates):
        path = f"$.candidates[{index}]"
        candidate = _exact(raw, candidate_keys, path)
        retrieval_id = _nonblank(candidate["retrieval_id"], f"{path}.retrieval_id")
        if (
            retrieval_id not in plans_by_id
            or executions_by_id[retrieval_id]["status"] != "completed"
        ):
            raise EvidencePackageValidationError(f"{path} references an unavailable retrieval")
        plan = plans_by_id[retrieval_id]
        if (
            candidate["query_id"] != plan["query_id"]
            or candidate["proposition_id"] != plan["proposition_id"]
            or candidate["retrieval_lane"] != plan["retrieval_lane"]
        ):
            raise EvidencePackageValidationError(f"{path} plan identity mismatch")
        _validate_passage(candidate, path=path, sources=sources)
        coordinate = (retrieval_id, str(candidate["passage_id"]))
        if coordinate in seen:
            raise EvidencePackageValidationError(f"duplicate candidate coordinate {coordinate!r}")
        seen.add(coordinate)
        rank = candidate["nomination_rank"]
        if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
            raise EvidencePackageValidationError(f"{path}.nomination_rank is invalid")
        expected_selection = "retained" if rank <= config.retained_k else "not_retained"
        if candidate["selection_state"] != expected_selection:
            raise EvidencePackageValidationError(f"{path}.selection_state mismatch")
        if expected_selection == "retained":
            if candidate["admission_state"] not in {"accepted", "rejected", "needs-review"}:
                raise EvidencePackageValidationError(f"{path}.admission_state is invalid")
        elif candidate["admission_state"] != "not_applicable":
            raise EvidencePackageValidationError(f"{path}.admission_state must be not_applicable")
        ranks[retrieval_id].append(rank)
        returned_sources[retrieval_id].add(str(candidate["source_id"]))

    for retrieval_id, execution in executions_by_id.items():
        expected_ranks = list(range(1, execution["returned_count"] + 1))
        if sorted(ranks[retrieval_id]) != expected_ranks:
            raise EvidencePackageValidationError(
                f"candidate rank/count mismatch for {retrieval_id}"
            )
        if sorted(returned_sources[retrieval_id]) != execution["returned_source_ids"]:
            raise EvidencePackageValidationError(f"returned source mismatch for {retrieval_id}")

    statuses = [str(execution["status"]) for execution in executions]
    expected_execution_state = (
        "not_run"
        if all(status == "not_run" for status in statuses)
        else "complete"
        if all(status == "completed" for status in statuses)
        else "partial"
    )
    if root["execution_state"] != expected_execution_state:
        raise EvidencePackageValidationError("$.execution_state mismatch")

    diagnostics = _exact(root["diagnostics"], {"root_retrieval"}, "$.diagnostics")
    root_diagnostic = diagnostics["root_retrieval"]
    if root_diagnostic is None:
        if config.root_diagnostic:
            raise EvidencePackageValidationError("root diagnostic is enabled but absent")
    else:
        if not config.root_diagnostic:
            raise EvidencePackageValidationError("root diagnostic is present but disabled")
        diagnostic_keys = {
            "normative",
            "retrieval_lane",
            "retrieval_id",
            "query_id",
            "proposition_id",
            "query_text_sha256",
            "requested_source_ids",
            "searched_source_ids",
            "returned_count",
            "candidate_depth_limit",
            "candidate_depth_hit",
            "candidates",
        }
        diagnostic = _exact(root_diagnostic, diagnostic_keys, "$.diagnostics.root_retrieval")
        root_proposition = contract_a["root_proposition"]
        diagnostic_query_id = query_identity(
            contract_a_sha256=str(contract_a["handoff_sha256"]),
            proposition_id=str(root_proposition["proposition_id"]),
            text_sha256=str(root_proposition["text_sha256"]),
            retrieval_lane="diagnostic_root_rescue",
            config_sha256=config.identity,
        )
        diagnostic_candidates = _array(diagnostic["candidates"], "root diagnostic candidates")
        expected_head = {
            "normative": False,
            "retrieval_lane": "diagnostic_root_rescue",
            "retrieval_id": retrieval_identity(diagnostic_query_id),
            "query_id": diagnostic_query_id,
            "proposition_id": root_proposition["proposition_id"],
            "query_text_sha256": root_proposition["text_sha256"],
            "requested_source_ids": source_ids,
            "searched_source_ids": source_ids,
            "returned_count": len(diagnostic_candidates),
            "candidate_depth_limit": config.candidate_depth,
            "candidate_depth_hit": len(diagnostic_candidates) == config.candidate_depth,
        }
        for key, expected in expected_head.items():
            if diagnostic[key] != expected:
                raise EvidencePackageValidationError(f"root diagnostic {key} mismatch")
        if len(diagnostic_candidates) > config.candidate_depth:
            raise EvidencePackageValidationError("root diagnostic exceeds candidate depth")
        diagnostic_candidate_keys = {
            "passage_id",
            "source_id",
            "source_content_sha256",
            "char_start",
            "char_end",
            "passage_sha256",
            "text",
            "nomination_rank",
        }
        for index, raw in enumerate(diagnostic_candidates):
            path = f"$.diagnostics.root_retrieval.candidates[{index}]"
            candidate = _exact(raw, diagnostic_candidate_keys, path)
            _validate_passage(candidate, path=path, sources=sources)
            if candidate["nomination_rank"] != index + 1:
                raise EvidencePackageValidationError(f"{path}.nomination_rank mismatch")

    supplied_package_sha = _sha(root["package_sha256"], "$.package_sha256")
    expected_package_sha = compute_package_sha256(root)
    if supplied_package_sha != expected_package_sha:
        raise EvidencePackageValidationError(
            "$.package_sha256 mismatch: "
            f"supplied={supplied_package_sha}, expected={expected_package_sha}"
        )
    return root
