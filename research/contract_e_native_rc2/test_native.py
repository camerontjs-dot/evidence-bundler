from copy import deepcopy
from pathlib import Path

import yaml

from research.contract_e_native_rc2.emit import source_access_descriptor

ROOT = Path(__file__).resolve().parents[2]


def metadata():
    return yaml.safe_load(
        (
            ROOT
            / "tests/fixtures/scaffold-run-minimal/corpus/src-001/metadata.yaml"
        ).read_text()
    )


def test_semantic_trust_mutation_does_not_launder_source_authority():
    base = metadata()
    changed = deepcopy(base)
    changed["trust_level"] = "untrusted"
    assert source_access_descriptor(base) == source_access_descriptor(changed)


def test_retrieval_semantics_do_not_change_source_authority_binding():
    base = metadata()
    changed = deepcopy(base)
    changed["retrieval"]["retrieval_rank"] = 999
    changed["retrieval"]["retrieval_query"] = "semantic laundering attempt"
    assert source_access_descriptor(base) == source_access_descriptor(changed)


def test_source_identity_mutation_changes_binding():
    base = metadata()
    changed = deepcopy(base)
    changed["content_hash"] = "sha256:" + "f" * 64
    assert source_access_descriptor(base) != source_access_descriptor(changed)


def test_descriptor_domain_is_not_evidence_truth():
    descriptor = source_access_descriptor(metadata())
    assert descriptor.authority_domain == "source_access"
    assert descriptor.operation == "source.read"
    assert "support" not in descriptor.authority_domain
