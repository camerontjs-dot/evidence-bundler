# Contract B Evidence-Package Recoverability RC1 — Preregistration

## Classification

Research-only Evidence Bundler / Contract B evidence-package characterization.

This is not a retrieval-quality experiment, not a CAL semantic experiment, not a Contract B amendment, and not a production promotion task.

## Frozen starting point

- Evidence Bundler research base: `dd4fb2b89f351fbdcd8b08e48dd9d7d1f10c2d05`
- Contract B 1.2 authority: `c314e53bd91c0736aa4370a364673b069aceb43e`
- Existing RC0 qualification cohort and explicit admission fixtures are reused unchanged.
- Existing retrieval/admission runtime receipt remains the richer producer-side evidence-world record.

## Question

Does the current canonical Contract B 1.2 evidence package preserve enough information for an independent B-only consumer to reconstruct the material evidence-world history expected from an inspection-ready regulated evidence package?

The test is deliberately narrower than claiming regulatory compliance. It asks whether the current artifact preserves and exposes the evidence history and limitations that EB already knows.

## B-only recoverability criteria

A Contract B-only reader should be able to recover, without access to the EB runtime receipt:

1. canonical claim identities and texts;
2. canonical source identities and source metadata;
3. canonical passage identities, text, hashes, source linkage, and representation coordinates;
4. proposition lineage carried by the factual-context extension;
5. every retained nomination identity and its retrieval metadata;
6. every retained review/admission decision, including `accepted`, `rejected`, and `needs-review`;
7. per-claim aperture scope and declared limitations;
8. integrity state sufficient to detect unsealed byte mutation;
9. enough history to reconstruct the complete pre-retention candidate identity set known to EB.

Criterion 9 is intentionally stronger than the current Contract B 1.2 specification. It represents the candidate regulated evidence-package expectation under test, not an assertion that Contract B already promises it.

## Primary falsifier

The regulated evidence-package recoverability hypothesis is falsified if a material evidence-world fact known to EB cannot be reconstructed from Contract B alone.

The predeclared high-risk discriminator is pre-retention candidate identity. The RC0 EB runtime receipt preserves a `candidate_pool`, while current Contract B history is constructed from retained nominations. If B exposes only candidate counts but not dropped candidate identities, classify that as an evidence-package information gap rather than a Contract B schema violation.

## Secondary mutation checks

Starting from a valid generated Contract B bundle:

- mutate extension bytes without resealing: whole-bundle validation must fail;
- remove a history link while leaving count checks unchanged: factual-context validation must fail;
- duplicate a history link identity: factual-context validation must fail;
- insert a prohibited proposition-specific field inside nomination metadata: factual-context validation must fail;
- encode `unknown` with a non-null value: model validation must fail;
- change nomination-only score metadata while keeping admission fixed: the audit/retrieval record must change, while the admitted-evidence projection must remain unchanged.

These mutations test integrity and separation. They do not establish completeness of the evidence package.

## Interpretation

Possible dispositions:

- `SUPPORTED_WITHIN_TESTED_APERTURE`: all nine recoverability criteria pass and all mutation checks behave as preregistered.
- `PARTIAL_RECOVERABILITY`: retained/final evidence history is faithfully recoverable, but one or more material producer-known facts are absent from Contract B.
- `INVALID_APPARATUS`: the experiment cannot validly construct or inspect the frozen Contract B object.

A `PARTIAL_RECOVERABILITY` result does not imply Contract B 1.2 violates its current specification. It means the current specification is narrower than the candidate regulated evidence-package role tested here.

## Non-actions

No production source changes. No retrieval tuning. No CAL call. No Contract B schema change. No merge, release, tag, or promotion.
