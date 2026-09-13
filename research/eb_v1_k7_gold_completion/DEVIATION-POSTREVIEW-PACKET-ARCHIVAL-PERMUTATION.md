# Preserved deviation — reviewer packet archival permutation

Status: **non-scientific archival/apparatus defect, detected at reviewer-output ingestion**

## What happened

The operator supplied two independent reviewer outputs whose opaque item IDs matched the packet distributed in `eb-v1-k7-blind-review-packet.zip`, but did not match the then-current GitHub copy of `BLIND_ADJUDICATION_PACKET.json`.

Investigation established:

- the distributed ZIP packet raw SHA-256 is `0b8b3e9021a992bbcc810cce7c3d2293b881d4d9eb7db0d0e9b7e3cb4b211455`, exactly the raw packet hash frozen in the original preregistration before reviewer exposure;
- its canonical JSON SHA-256 is `4f50b1e385c48b6b15fc223f4700f0c104ce1633742887ced388fe6342420e9c`, exactly the canonical identity subsequently recorded in the PR and evaluator;
- the distributed packet contains exactly the frozen 27 unresolved proposition/passage relationships;
- each opaque item ID is correctly derived from the frozen proposition/evidence identity using `sha256("eb-v1-k7-adjudication-v1|<proposition_id>|<evidence_id>")[:16]`;
- the GitHub archival copy contained the same set of 27 opaque IDs and the same set of 27 semantic proposition/passage pairs, but the IDs had been permuted against the pairs during a connector serialization/repair sequence;
- the frozen evaluator would reject that bad GitHub copy because its canonical content does not match the frozen canonical packet hash;
- no reviewer saw the bad GitHub copy. Both reviewer receipts bind themselves to canonical packet SHA-256 `4f50b1e...` and were produced from the distributed ZIP.

## Disposition

The GitHub archival packet is restored to the exact reviewer-seen/preregistered ID-to-semantic mapping before terminal evaluation. This repair changes no reviewer-visible scientific object, no label, no retrieval output, no burden threshold, and no expected outcome.

The defect is preserved here rather than erased because evaluator/apparatus failures are themselves evidence.

This deviation does not authorize any retrieval rerun, K change, selector change, merge, release, tag, or promotion.
