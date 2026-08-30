# Producer-Native Authority Descriptor RC2 — Evidence Bundler

## OBSERVED

Accepted head: `45702fc80f529654d4745760b071132131d3a509`.

Accepted push run: `33321329523`. Accepted PR run: `33321331085`.

Artifact: `9734965892`, digest `sha256:d840710374c574b7f75973725f9f3b5f28e6de41a80f8384748e2ee932b4450c`.

Evidence Bundler natively emitted two research-only authority descriptors:

- `source.read` over exact source URL/content hash in domain `source_access`;
- `evidence.admit_passage` over exact bundle/source/passage identity and passage hash in domain `evidence_admission`.

Trust-level and retrieval rank/query mutations did not alter the source-access authority binding. Source content-hash substitution did alter it.

## INFERENCE

Evidence Bundler can expose authority-sensitive identity bindings without treating retrieval/trust semantics as authority.

## UNKNOWN

This does not establish production access/admission policy, receipt topology, or that all Evidence Bundler stages satisfy the same interface.

## DISPOSITION

SUPPORTED as producer-native research evidence. No production promotion.
