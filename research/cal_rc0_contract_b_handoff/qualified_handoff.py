from __future__ import annotations

from pathlib import Path
from typing import Any

from evidence_bundler.contracts import factual_context as factual_context_module
from evidence_bundler.contracts.yaml_io import load_model_yaml
from evidence_bundler.models.cb import BundleManifest

from .build_handoff import build_all_contract_b as _build_all_contract_b


def dedupe_source_contexts(extension: Any) -> Any:
    """Normalize repeated source-context references without changing evidence identity."""
    seen: set[str] = set()
    sources = []
    for source in extension.sources:
        if source.source_id in seen:
            continue
        seen.add(source.source_id)
        sources.append(source)
    return extension.model_copy(update={"sources": sources})


def build_all_contract_b_qualified(
    *,
    cohort: dict[str, Any],
    receipt: dict[str, Any],
    profile: dict[str, Any],
    out_dir: Path,
) -> list[dict[str, Any]]:
    """Run the frozen RC0 B build with two narrow qualification normalizations.

    This wrapper does not modify retrieval, retention, admission, Contract A identity,
    or semantic fields. It only deduplicates factual-context source references by
    source_id before the released B 1.2 attachment validator and refreshes returned
    bundle hashes from the manifest after the extension reseals the tree.
    """
    original_attach = factual_context_module.attach_factual_context

    def normalized_attach(bundle_dir: Path, extension: Any) -> Path:
        return original_attach(bundle_dir, dedupe_source_contexts(extension))

    factual_context_module.attach_factual_context = normalized_attach
    try:
        results = _build_all_contract_b(
            cohort=cohort,
            receipt=receipt,
            profile=profile,
            out_dir=out_dir,
        )
    finally:
        factual_context_module.attach_factual_context = original_attach

    refreshed: list[dict[str, Any]] = []
    for result in results:
        row = dict(result)
        case_id = str(row["case_id"])
        manifest = load_model_yaml(
            BundleManifest,
            out_dir / "contract_b" / case_id / "bundle_manifest.yaml",
        )
        row["bundle_hash"] = manifest.bundle.bundle_hash
        refreshed.append(row)
    return refreshed


__all__ = ["build_all_contract_b_qualified", "dedupe_source_contexts"]
