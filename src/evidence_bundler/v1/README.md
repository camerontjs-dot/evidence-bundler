# Evidence Bundler V1 candidate

Status: **convergence evidence complete; product disposition `NOT_READY`**.

This package is the maintained V1 candidate surface produced by the 2026-09-11 convergence pass. It is not a release, promotion, or claim that the current retrieval default is production-qualified.

The exact convergence decision and qualification receipts are recorded in `docs/V1-CONVERGENCE-DECISION-20260911.md`.

## Boundary

The candidate constructs one immutable, self-validating Evidence Bundler evidence-world package from released Contract A 2.0 input.

Its maintained boundary is:

`Contract A 2.0 -> exact normative proposition lanes -> deterministic BM25 nomination -> deterministic retention -> explicit admission -> immutable Evidence Bundler package`

Evidence Bundler does **not** assign proposition truth, support/refutation, CAL verdicts, semantic warrant, or downstream decision/authorization state.

For Contract A decomposition:

- `declared/all_of` creates one normative lane per exact declared child;
- `not_decomposed` creates one exact root lane;
- `unknown` and `failed` fail closed rather than being reinterpreted as `not_decomposed`;
- optional root retrieval for a declared decomposition is isolated as a non-normative diagnostic lane.

Nomination, retention, and admission are distinct durable states. Non-retained candidates remain represented through the configured candidate depth. `accepted`, `rejected`, and `needs-review` are evidence-world review states, not semantic polarity labels.

## Retrieval configuration

The maintained candidate uses deterministic in-repository Okapi BM25 with:

- `k1=1.5`;
- `b=0.75`;
- lowercase-word tokenization;
- exact primary-target text as the query;
- default `candidate_depth=5`;
- default `retained_k=3`;
- chunking `1800` characters with `80` character overlap.

The `5/3` values are implementation defaults only. The convergence discriminator did **not** qualify them, or the tested `10/3` and `10/6` successors, as a production V1 retrieval default. In the preserved lexical-decoy counterexample, true evidence entered the widened candidate pool at rank 7 and remained outside retention at the authorized `10/6` stopping boundary.

Raw BM25 score is intentionally not part of the V1 package contract. Retriever identity/configuration, rank, stage transitions, passage/source identity, aperture, and admission state are durable package facts. Qualification receipts may retain raw scores diagnostically.

## Operator surface

Build a package:

```bash
python -m evidence_bundler.v1 contract-a.json \
  --output evidence-world.json \
  [--admission admission.json] \
  [--candidate-depth 5] \
  [--retained-k 3] \
  [--root-diagnostic]
```

`--not-run-target <proposition_id>` may be repeated to represent an explicitly predeclared retrieval lane that was not run.

The optional admission document uses schema `evidence-bundler-admission-v1` and may assign `accepted`, `rejected`, or `needs-review` only to retained normative candidates.

## Qualification status

The frozen implementation at `c4e3f97ec8f0bd36180954c3aa382418925bf947` passed maintained Python 3.11/3.12 CI and bounded conformance against the released Contract A validator.

A separate stdlib-only consumer in Claim Audit Lab Draft PR #102 independently reconstructed proposition identity, normative lane, accepted evidence, source/passage bindings, aperture, and admission state from a V1 package while refusing injected semantic authority.

The remaining V1 blocker is retrieval-default qualification. Any successor retrieval experiment requires a separate bounded decision; it is not implicit continuation of this convergence PR.

## Nonclaims

This candidate does not establish universal/perfect recall, source truthworthiness, corpus completeness, CAL semantic correctness, authoritative automatic decomposition, root `all_of` semantic composition, Contract B successor promotion, Contract E authorization, or operational execution.
