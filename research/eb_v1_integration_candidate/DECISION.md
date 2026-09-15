# Decision: assemble Evidence Bundler V1 integration candidate at 10/3

## Decision

Use the exact frozen Evidence Bundler V1 implementation at `c4e3f97ec8f0bd36180954c3aa382418925bf947` with the exact Stage-A 10/3 configuration as the V1 integration candidate, while preserving the statement that no production retrieval default has been qualified.

Add only the smallest downstream machinery needed to project the immutable native V1 package through released Contract B 1.2 using an explicit compatibility carrier.

## Effective artifact

This Draft Research Infrastructure branch and its eventual locally qualified freeze commit. No merge/release/promotion is authorized by this record.

## Observed evidence

- PR #60 froze the maintained V1 architecture and implementation, passed maintained health/Contract-A/independent structural-consumer checks, and left retrieval-default qualification unresolved.
- PR #63 showed depth 10 exposes required evidence hidden by depth 5 and that K=7 can retain the preserved rank-7 item.
- PR #72 terminally falsified fixed 10/7 under the completed review/noise burden gate.
- PR #74 terminally falsified fixed 10/7 under its preregistered operational-instability decision rule.
- PR #77 found the tested facility-location selectors identical to K=3 on the primary frozen-pool endpoints and preserved the same deep misses.
- PR #53 preserved the A2/B1.2 negative interface counterexample: A2 does not own all required legacy B core fields.
- PR #54 demonstrated that a separate explicit compatibility carrier can satisfy the locked B1.2 boundary while remaining causally isolated from retrieval/admission and adding no CAL semantic authority.
- CAL's maintained B1.2 consumer requires audit-policy identity `cal-rules-v1.2.0`; the integration carrier pins that compatibility value explicitly.

## Inference

The smallest defensible V1 baseline is not another retrieval experiment. It is the already-frozen V1 machinery with candidate depth 10 for observability and retained K=3 for bounded review context, plus an explicit Contract B compatibility boundary.

The known K=3 deep-retention misses are observable limitations appropriate for test-to-learn pipeline use rather than evidence that V1 is uninterpretable.

## Alternatives considered

### Keep 5/3

Rejected for integration baseline because depth 5 can hide known required evidence entirely, preventing the pipeline trace from distinguishing candidate-pool loss from retention loss.

### Fixed 10/7

Rejected as V1 default by completed negative evidence in PRs #72 and #74 despite its ability to recover deeper evidence.

### Facility-location/set-wise selector

Not included because the tested bounded variants in PR #77 did not improve the frozen-pool result over K=3.

### Adaptive K / reranker / query rewrite / embeddings

Deferred. No tested successor has earned authority to displace the simpler baseline.

### Direct A2 -> B1.2 without carrier

Falsified by PR #53 because doing so requires inventing legacy fields that A2 deliberately does not own.

### Bypass Contract B and pass EB-private state to CAL

Rejected because it would test a different interface from the released B1.2 authority and the current CAL intake contract.

## What is not established

This decision does not establish retrieval completeness, optimal K, production retrieval quality, source trustworthiness, semantic support/refutation, CAL correctness, Contract C readiness, Decision readiness, or release readiness.

## Residual uncertainty

The frequency and operational significance of K=3 retention misses on realistic pipeline claims remains unknown. The relative value of proposition-relative materiality, local-span scoring, semantic reranking, or another compact selector also remains unknown.

## Reconsideration trigger

Reopen retrieval architecture only if the frozen 10/3 baseline produces enough reconstructable real-claim evidence to show that a specific failure class materially limits pipeline usefulness, or if a separately preregistered successor demonstrates a better bounded selector under comparable burden.

## Lineage

Primary Evidence Bundler records: PRs #60, #63, #72, #74, #76, #77, #78, #53 and #54.

Contract B released authority: `c314e53bd91c0736aa4370a364673b069aceb43e`.

CAL intake qualification subject: `4d1b8909f7e2e52c33cf99632be8565f2685f948`.
