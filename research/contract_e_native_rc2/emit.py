"""Research-only Contract E native descriptor emission for Evidence Bundler."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json

import yaml

from evidence_bundler.contracts.writer import build_fixture_bundle


@dataclass(frozen=True)
class Descriptor:
    participant: str
    actor: str
    operation: str
    target_class: str
    target_id: str
    current_hash: str
    authority_domain: str


def source_access_descriptor(metadata: dict) -> Descriptor:
    return Descriptor(
        participant="evidence-bundler",
        actor="evidence-bundler",
        operation="source.read",
        target_class="source_material",
        target_id=metadata["bibliographic"]["url"],
        current_hash=metadata["content_hash"],
        authority_domain="source_access",
    )


def evidence_admission_descriptor(bundle_dir: Path) -> Descriptor:
    manifest = yaml.safe_load((bundle_dir / "bundle_manifest.yaml").read_text())
    claim = yaml.safe_load(next((bundle_dir / "claims").glob("*.yaml")).read_text())
    passage_ref = claim["evidence_passages"][0]
    passage = yaml.safe_load(
        (bundle_dir / "evidence" / passage_ref["source_id"] / "passages" / f"{passage_ref['passage_id']}.yaml").read_text()
    )
    return Descriptor(
        participant="evidence-bundler",
        actor="evidence-bundler",
        operation="evidence.admit_passage",
        target_class="evidence_passage",
        target_id=f"{manifest['bundle_id']}::{passage['source_id']}::{passage['passage_id']}",
        current_hash=passage["passage_hash"],
        authority_domain="evidence_admission",
    )


def emit(repo: Path, out: Path) -> None:
    fixture = repo / "tests/fixtures/scaffold-run-minimal"
    metadata = yaml.safe_load((fixture / "corpus/src-001/metadata.yaml").read_text())
    bundle_dir = out.parent / "bundle"
    build_fixture_bundle(fixture, bundle_dir)
    payload = {
        "schema": "contract-e-native-descriptor-rc2",
        "descriptors": [
            asdict(source_access_descriptor(metadata)),
            asdict(evidence_admission_descriptor(bundle_dir)),
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    emit(repo, repo / "artifacts/contract-e-native-rc2/descriptors.json")
