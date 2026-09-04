"""Production writer for the optional Contract-B v1.2 factual-context extension.

The extension references canonical C-B claim/source/passage records; it does not
duplicate their existing payloads or make proposition-specific CAL judgments.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from evidence_bundler.contracts.hashing import compute_bundle_tree_hash, write_sha256sums
from evidence_bundler.contracts.yaml_io import load_model_yaml, write_model_yaml
from evidence_bundler.models.cb import BundleManifest
from evidence_bundler.models.common import CONTRACT_VERSION, PENDING_HASH

if TYPE_CHECKING:
    from evidence_bundler.contracts.writer import BundleBuildResult

EXTENSION_PATH = Path("extensions/contract-b-factual-context-v1.json")
PROHIBITED_KEYS = frozenset(
    {
        "support",
        "refutation",
        "proposition_specific_relation",
        "semantic_validity",
        "temporal_applicability",
        "authority_applicability",
        "supplier_applicability",
        "completeness_conclusion",
        "decision_participation",
        "audit_support_verdict",
        "verdict",
        "abstention",
    }
)


class FactualContextError(ValueError):
    """Raised when an extension cannot be safely attached to a C-B bundle."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExplicitValue(_Strict):
    state: Literal["known", "unknown"]
    value: Any | None

    @model_validator(mode="after")
    def validate_state(self) -> ExplicitValue:
        if self.state == "known" and self.value is None:
            raise ValueError("known state requires a non-null value")
        if self.state == "unknown" and self.value is not None:
            raise ValueError("unknown state requires null value")
        return self


class ClaimContext(_Strict):
    claim_id: str = Field(min_length=1)
    origin: ExplicitValue
    atomicity: ExplicitValue


class ContextFact(_Strict):
    fact_id: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    value: Any
    assertion_mode: str = Field(min_length=1)
    provenance_passage_id: str = Field(min_length=1)


class SourceContext(_Strict):
    source_id: str = Field(min_length=1)
    context_facts: list[ContextFact] = Field(default_factory=list)


class Anchor(_Strict):
    type: str = Field(min_length=1)
    value: Any


class PassageContext(_Strict):
    passage_id: str = Field(min_length=1)
    anchors: list[Anchor] = Field(default_factory=list)


class HistoryLink(_Strict):
    link_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    passage_id: str = Field(min_length=1)
    nomination: dict[str, Any]
    review: dict[str, Any]

    @model_validator(mode="after")
    def validate_review(self) -> HistoryLink:
        if self.review.get("decision") not in {"accepted", "rejected", "needs-review"}:
            raise ValueError("review.decision must be accepted, rejected, or needs-review")
        return self


class HistoryCountCheck(_Strict):
    claim_id: str = Field(min_length=1)
    candidate: int = Field(ge=0)
    reviewed: int = Field(ge=0)
    admitted: int = Field(ge=0)


class ApertureObservation(_Strict):
    claim_id: str = Field(min_length=1)
    search_scope: dict[str, Any]
    outcome: ExplicitValue
    limitations: list[Any] = Field(default_factory=list)


class ContractBFactualContext(_Strict):
    schema: Literal["contract-b-factual-context-v1"] = (
        "contract-b-factual-context-v1"  # type: ignore[assignment]
    )
    history_complete: Literal[True] = True
    claims: list[ClaimContext] = Field(default_factory=list)
    sources: list[SourceContext] = Field(default_factory=list)
    passages: list[PassageContext] = Field(default_factory=list)
    history: list[HistoryLink] = Field(default_factory=list)
    history_count_checks: list[HistoryCountCheck] = Field(default_factory=list)
    aperture: list[ApertureObservation] = Field(default_factory=list)


def _json_key(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def normalized_object(extension: ContractBFactualContext) -> dict[str, Any]:
    data = extension.model_dump(mode="json")
    data["claims"] = sorted(data["claims"], key=lambda row: row["claim_id"])
    data["sources"] = sorted(data["sources"], key=lambda row: row["source_id"])
    for source in data["sources"]:
        source["context_facts"] = sorted(source["context_facts"], key=lambda row: row["fact_id"])
    data["passages"] = sorted(data["passages"], key=lambda row: row["passage_id"])
    for passage in data["passages"]:
        passage["anchors"] = sorted(
            passage["anchors"], key=lambda row: (row["type"], _json_key(row["value"]))
        )
    data["history"] = sorted(data["history"], key=lambda row: row["link_id"])
    data["history_count_checks"] = sorted(
        data["history_count_checks"], key=lambda row: row["claim_id"]
    )
    data["aperture"] = sorted(data["aperture"], key=lambda row: row["claim_id"])
    for aperture in data["aperture"]:
        aperture["limitations"] = sorted(aperture["limitations"], key=_json_key)
    return data


def canonical_bytes(extension: ContractBFactualContext) -> bytes:
    return (
        json.dumps(
            normalized_object(extension),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _walk_prohibited(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in PROHIBITED_KEYS:
                errors.append(f"prohibited proposition-specific field: {child_path}")
            errors.extend(_walk_prohibited(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_walk_prohibited(child, f"{path}[{index}]"))
    return errors


def _duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def _read_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise FactualContextError(f"expected mapping in {path}")
    return data


def _bundle_ids(bundle_dir: Path) -> tuple[set[str], set[str], set[str]]:
    claim_ids = {
        str(_read_mapping(path)["claim_id"]) for path in (bundle_dir / "claims").glob("*.yaml")
    }
    source_ids: set[str] = set()
    passage_ids: set[str] = set()
    for source_dir in (path for path in (bundle_dir / "evidence").iterdir() if path.is_dir()):
        source_ids.add(source_dir.name)
        passages_dir = source_dir / "passages"
        if passages_dir.is_dir():
            for path in passages_dir.glob("*.yaml"):
                passage_ids.add(str(_read_mapping(path)["passage_id"]))
    return claim_ids, source_ids, passage_ids


def validate_for_bundle(bundle_dir: Path, extension: ContractBFactualContext) -> list[str]:
    errors = _walk_prohibited(extension.model_dump(mode="json"))
    claim_ids, source_ids, passage_ids = _bundle_ids(bundle_dir)

    groups = {
        "claim_id": [row.claim_id for row in extension.claims],
        "source_id": [row.source_id for row in extension.sources],
        "passage_id": [row.passage_id for row in extension.passages],
        "link_id": [row.link_id for row in extension.history],
        "history_count_check.claim_id": [row.claim_id for row in extension.history_count_checks],
        "aperture.claim_id": [row.claim_id for row in extension.aperture],
    }
    for label, values in groups.items():
        duplicate = _duplicates(values)
        if duplicate:
            errors.append(f"duplicate {label}: {', '.join(duplicate)}")

    for claim in extension.claims:
        if claim.claim_id not in claim_ids:
            errors.append(f"unknown canonical claim reference: {claim.claim_id}")
    for source in extension.sources:
        if source.source_id not in source_ids:
            errors.append(f"unknown canonical source reference: {source.source_id}")
        facts = _duplicates([fact.fact_id for fact in source.context_facts])
        if facts:
            errors.append(f"duplicate fact_id in source {source.source_id}: {', '.join(facts)}")
        for fact in source.context_facts:
            if fact.provenance_passage_id not in passage_ids:
                errors.append(f"unknown provenance passage reference: {fact.provenance_passage_id}")
    for passage in extension.passages:
        if passage.passage_id not in passage_ids:
            errors.append(f"unknown canonical passage reference: {passage.passage_id}")
    for link in extension.history:
        if link.claim_id not in claim_ids:
            errors.append(f"unknown history claim reference: {link.claim_id}")
        if link.passage_id not in passage_ids:
            errors.append(f"unknown history passage reference: {link.passage_id}")
    for aperture in extension.aperture:
        if aperture.claim_id not in claim_ids:
            errors.append(f"unknown aperture claim reference: {aperture.claim_id}")

    derived: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for link in extension.history:
        row = derived[link.claim_id]
        row[0] += 1
        decision = link.review["decision"]
        if decision != "needs-review":
            row[1] += 1
        if decision == "accepted":
            row[2] += 1
    for check in extension.history_count_checks:
        actual = (check.candidate, check.reviewed, check.admitted)
        expected = tuple(derived.get(check.claim_id, [0, 0, 0]))
        if actual != expected:
            errors.append(
                "history count mismatch for "
                f"{check.claim_id}: supplied={actual}, derived={expected}"
            )
    return errors


def _reseal(bundle_dir: Path) -> None:
    manifest_path = bundle_dir / "bundle_manifest.yaml"
    manifest = load_model_yaml(BundleManifest, manifest_path)
    manifest = manifest.model_copy(
        update={"bundle": manifest.bundle.model_copy(update={"bundle_hash": PENDING_HASH})}
    )
    write_model_yaml(manifest, manifest_path)
    manifest = manifest.model_copy(
        update={
            "bundle": manifest.bundle.model_copy(
                update={"bundle_hash": compute_bundle_tree_hash(bundle_dir)}
            )
        }
    )
    write_model_yaml(manifest, manifest_path)
    write_sha256sums(bundle_dir)


def attach_factual_context(bundle_dir: Path, extension: ContractBFactualContext) -> Path:
    """Attach, validate, and integrity-seal the promoted optional extension."""
    bundle_dir = bundle_dir.resolve()
    version_path = bundle_dir / "CONTRACT_VERSION"
    if not version_path.exists() or version_path.read_text(encoding="utf-8").strip() != "1.2.0":
        raise FactualContextError("factual-context extension requires a Contract B 1.2.0 bundle")
    if CONTRACT_VERSION != "1.2.0":
        raise FactualContextError(f"producer pin is {CONTRACT_VERSION!r}, expected '1.2.0'")
    errors = validate_for_bundle(bundle_dir, extension)
    if errors:
        raise FactualContextError("; ".join(errors))
    target = bundle_dir / EXTENSION_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical_bytes(extension))
    _reseal(bundle_dir)
    return target


def build_fixture_bundle_with_factual_context(
    scaffold_run_dir: Path,
    output_dir: Path,
    extension: ContractBFactualContext,
) -> BundleBuildResult:
    """Build through the real fixture producer, attach the extension, and revalidate."""
    from evidence_bundler.contracts.writer import (  # local import avoids a module cycle
        BundleBuildResult,
        BundleWriterError,
        build_fixture_bundle,
        validate_bundle_tree,
    )

    result = build_fixture_bundle(scaffold_run_dir, output_dir)
    attach_factual_context(result.bundle_dir, extension)
    errors = validate_bundle_tree(result.bundle_dir)
    if errors:
        raise BundleWriterError("; ".join(errors))
    manifest = load_model_yaml(BundleManifest, result.bundle_dir / "bundle_manifest.yaml")
    return BundleBuildResult(bundle_dir=result.bundle_dir, manifest=manifest)


__all__ = [
    "Anchor",
    "ApertureObservation",
    "ClaimContext",
    "ContextFact",
    "ContractBFactualContext",
    "ExplicitValue",
    "FactualContextError",
    "HistoryCountCheck",
    "HistoryLink",
    "PassageContext",
    "SourceContext",
    "attach_factual_context",
    "build_fixture_bundle_with_factual_context",
    "canonical_bytes",
    "normalized_object",
    "validate_for_bundle",
]
