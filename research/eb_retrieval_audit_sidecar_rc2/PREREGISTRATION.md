# EB Retrieval-Audit Sidecar RC2 Preregistration

## Classification

Draft Research Evidence. Evidence Bundler only.

This is a successor to Contract B evidence-package recoverability RC1. It does not amend Contract B, tune retrieval, call CAL, merge, release, tag, promote, or change production defaults.

## Frozen starting state

- Evidence Bundler predecessor head: `f5e257904bef731b5798233ad53caa709136c810`
- RC1 disposition: `PARTIAL_RECOVERABILITY`
- RC1 observed gap: Contract B preserved retained nomination/review history and candidate counts, but did not preserve identity-level pre-retention candidate history for any of the eight frozen cases.

## Question

Can the smallest optional EB retrieval-audit sidecar, kept outside canonical Contract B and integrity-bound to it by an outer evidence-package envelope, restore full pre-retention candidate/selection recoverability without changing Contract B bytes or semantic-use evidence?

## Candidate architecture under test

For each frozen EB case, produce three artifacts:

1. the unchanged canonical Contract B 1.2 bundle;
2. `EB_RETRIEVAL_AUDIT.json`, containing the complete observed pre-retention candidate trail and enough candidate passage identity/content to inspect what was considered;
3. `EB_EVIDENCE_PACKAGE_ENVELOPE.json`, binding the Contract B bundle identity/hash and canonical sidecar SHA-256 in one outer record.

The envelope establishes content-integrity/co-binding only. It does **not** establish signer identity, authenticity, non-repudiation, trusted time, or authorization.

## Sidecar minimum content

The sidecar must preserve:

- case identity;
- exact Contract B bundle ID/version/hash binding;
- retrieval profile hash;
- query identity, proposition identity, retrieval lane, and query text;
- every pre-retention candidate identity;
- source identity;
- candidate rank, score and score kind;
- whether each candidate survived retention;
- candidate passage text and SHA-256 for every observed candidate;
- source content SHA-256 where available from the supplied Contract A corpus;
- per-proposition candidate and retained counts;
- explicit `candidate_history_complete: true` scoped only to the observed EB runtime candidate history.

The sidecar must not contain authoritative support/refutation/verdict fields or downstream semantic judgments.

## Primary criteria

The candidate architecture is `SUPPORTED_WITHIN_TESTED_APERTURE` only if all eight frozen cases satisfy all of the following:

1. canonical Contract B validates;
2. Contract B bytes/hash are unchanged by sidecar packaging;
3. a B+sidecar independent structural reader reconstructs every runtime pre-retention candidate identity;
4. every candidate has inspectable passage identity/text/hash and source identity;
5. sidecar retained flags exactly match the EB runtime retained set;
6. retained identities in canonical Contract B exactly match sidecar retained identities;
7. Contract B admission/review state remains unchanged and is not duplicated as sidecar semantic authority;
8. Contract B aperture candidate counts agree with sidecar/runtime counts;
9. the envelope verifies exact Contract B bundle identity/hash and sidecar SHA-256;
10. all preregistered mutation tests behave as specified.

Failure of any recoverability criterion is `FALSIFIED_WITHIN_TESTED_APERTURE`. A broken baseline, malformed test fixture, or mutation evaluator that cannot discriminate its target is `INVALID_APPARATUS`.

## Preregistered mutations

1. **Sidecar byte tamper:** mutate candidate passage text without changing the envelope. Verification must fail on sidecar hash.
2. **Candidate omission with stale envelope:** remove one candidate without changing the envelope. Verification must fail.
3. **Candidate omission with refreshed envelope but stale internal counts:** refresh the sidecar digest in the envelope. Verification must still fail because sidecar completeness/count invariants disagree.
4. **Cross-case swap:** pair a valid sidecar+envelope from one case with another case's Contract B. Verification must fail on Contract B binding.
5. **Unsealed Contract B tamper:** mutate canonical Contract B bytes without resealing. Contract B validation and package verification must fail.
6. **Resealed Contract B mutation:** mutate and internally reseal Contract B while keeping the original outer envelope. Canonical B may validate, but package verification must fail because the bound B hash changed.
7. **Nomination-score-only change:** change only a sidecar retrieval score, regenerate the envelope, and verify that the package remains structurally valid while canonical Contract B bytes and admitted-evidence projection remain unchanged.

## Weight-bearing assumption

The main assumption is that complete pre-retention history belongs in an optional EB audit artifact rather than canonical Contract B. This experiment tests whether that separation is technically sufficient for recoverability and integrity. It does not establish that this is the correct long-term governance or contract design.

## Explicit nonclaims

No claim is made about retrieval quality, corpus completeness, evidence sufficiency, proposition truth, CAL semantics, authorization, authenticated provenance, or production readiness.