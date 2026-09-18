# Composite Obligation RC1 — Evaluation Contract

## Classification

Preregistered fresh fixed-pool selector evaluation.

This contract is frozen before cohort authoring. It does not authorize production use.

## Opaque post-reveal arms

The prereveal evaluator accepts arbitrary opaque arm IDs. After a valid `READY_FOR_REVEAL` receipt, the execution lane binds exactly once:

- semantic top-3;
- composition/child-coverage control;
- subject-only control;
- expected-form-only control;
- frozen RC1 candidate;
- wrong-subject control;
- wrong-form control;
- wrong-subject + wrong-form control;
- reverse-order correct combination control.

All arms use the exact same fresh candidate pools and semantic scores, K=3, and no gold during selection.

## Primary metrics

Report for all 24 parents and each C1-C6 category:

- complete parent coverage: both child propositions have at least one selected `REQUIRED` candidate;
- required children covered / required children total;
- unsafe selections: selected `UNSAFE_OR_MISLEADING`;
- non-useful selections: selected `DISTRACTOR`, `UNSAFE_OR_MISLEADING`, or `REDUNDANT`;
- required selections;
- exact replay identity;
- selection changes versus semantic top-3.

## Fresh support gate for the combined candidate

A valid run supports the **combined composition + expected-form + subject** candidate for prototype freeze only if all are true:

1. Overall versus semantic top-3:
   - candidate gains at least **6 required children** out of 48;
   - candidate gains at least **4 complete parents** out of 24;
   - candidate unsafe selections are no higher than semantic by more than **1**.

2. Subject discrimination on C2 + C3 (8 parents / 16 children):
   - candidate required-child coverage is no worse than subject-only by more than **1 child**;
   - candidate unsafe is no worse than subject-only by more than **1**;
   - correct-subject candidate exceeds wrong-subject control by at least **4 required children**;
   - correct-subject candidate has at least **3 fewer unsafe selections** than wrong-subject control.

3. Evidence-form increment on C4 + C5 (8 parents / 16 children):
   - combined candidate exceeds subject-only by at least **2 required children** OR at least **1 complete parent**;
   - combined candidate unsafe is no worse than subject-only by more than **1**;
   - correct candidate exceeds wrong-form control by at least **2 required children**.

4. Mixed falsifier:
   - combined candidate exceeds wrong-subject + wrong-form control by at least **6 required children** overall.

5. C6 easy/no-op controls:
   - no loss of required-child coverage versus semantic;
   - no more than **1** additional unsafe selection.

6. Apparatus:
   - all selection arms replay exactly;
   - every selection is K=3, unique, and in-pool;
   - fresh-input and gold hashes match frozen receipts;
   - no prereveal contamination.

This disposition supports only a frozen research prototype candidate, not production deployment.

## Subject-only convergence path

If the full support gate fails only because condition 3 does not establish incremental evidence-form value, but subject discrimination and overall safety/coverage remain supported, use:

`SUPPORTED_SUBJECT_ONLY; COMBINED_FORM_INCREMENT_NOT_REPRODUCED`

Do not freeze the combined candidate. A smaller subject/composition candidate must be frozen and, if material, separately reproduced.

## Falsification

Use `FALSIFIED` on a valid run if any is true:

- candidate loses at least 4 required children versus semantic overall;
- candidate adds more than 4 unsafe selections versus semantic overall;
- wrong-subject control matches or exceeds correct candidate on both required coverage and safety in C2+C3;
- wrong-form control matches or exceeds correct candidate on both required coverage and safety in C4+C5;
- wrong-subject + wrong-form control matches the candidate within 1 required child overall;
- C6 controls lose 2 or more required children;
- target-owned replay, K, pool-membership, or determinism properties fail repeatedly.

## Inconclusive

Use `INCONCLUSIVE` when the run is valid but support, subject-only convergence, and falsification are all unmet.

## Apparatus terminal state

Use `BLOCKED_APPARATUS` for hash drift, malformed arm outputs, evaluator/gold mutation, inability to reproduce semantic scores, or gold exposure before selection freeze.

## Epistemic boundary

This experiment does not qualify:

- first-stage retrieval;
- subject extraction by ClaimGate or any other producer;
- CAL support/refute judgment;
- evidence completeness;
- production default behavior.
