# External Corpus Evaluator Independence and Blind-Handoff Prep

## Decision

Determine whether a later external-corpus retrieval pilot can use a fully explicit retrieval-evaluator contract, two separately implemented evaluators, fail-closed adversarial checks, and a cryptographically committed hidden-gold handoff without exposing scientific qrels to target execution.

## Boundary

This is Research Infrastructure. Only dummy/adversarial fixtures are used. No Evidence Bundler retriever is run. No scientific pilot relevance judgment is opened, copied, scored, or inferred.

## Acceptance

The infrastructure is ready for pilot integration only if:

1. the contract makes metric and edge-case semantics explicit;
2. evaluator A and evaluator B agree on all frozen dummy fixtures while sharing no evaluator implementation code;
3. fail-closed mutations are rejected rather than scored;
4. commitment verification is invariant to irrelevant serialization order and sensitive to semantic mutation;
5. the pre-reveal repository snapshot contains permitted inputs plus the commitment but no hidden gold or construction notes;
6. the revealed dummy gold verifies against the exact precommitted hash;
7. evaluator reproduction requires only the contract, public manifest, run, and revealed gold, not implementation-specific knowledge.

## Falsifiers

- material evaluator disagreement;
- implicit promotion-critical metric semantics;
- hidden gold reachable through the pre-reveal public repository snapshot;
- commitment mismatch after reveal;
- metric changes caused only by source order, irrelevant serialization order, or consistent stable-ID renaming;
- reproduction requiring evaluator-A internals.

## Independence meaning

The two evaluator programs must have separate validation, metric, and aggregation implementations and may not import one another or a shared evaluator helper. The contract and fixture data are their only shared semantic authority.

This task can test implementation independence. It does not claim independent organizational authorship or a separately credentialed human reviewer.
