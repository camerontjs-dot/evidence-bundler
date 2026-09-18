# EB Gate Specialty Selector RC1 — Evaluation Contract

## Purpose

Evaluate five frozen post-reveal selection arms on the exact same 36 fresh depth-10 candidate pools, with the same frozen Claim Gate profiles, semantic scores, and maximum budget of 3.

The evaluator is authored and frozen before arm identities are revealed.

Use opaque arm keys only:

- `ARM_A`
- `ARM_B`
- `ARM_C`
- `ARM_D`
- `ARM_E`

The evaluator must not change after arm binding.

## Input invariants

For every lane and arm:

- same claim and Claim Gate profile identity;
- same candidate-pool identity/hash;
- same frozen semantic scores;
- maximum 3 selected candidates;
- no duplicate IDs;
- every selected ID belongs to the frozen top-10 pool;
- no first-stage retrieval mutation;
- no gold access during selection execution.

A violation is `BLOCKED_APPARATUS` unless it is explicitly a repeated target-owned deterministic failure covered by the falsification rules.

## Primary scoring populations

Report metrics for:

1. all 36 lanes;
2. the 30 specialty lanes, categories 1–5;
3. each specialty category separately;
4. the 6 anti-tautology lanes;
5. the 6 no-specialty controls.

The **principal scientific population is the 30 specialty lanes**.

## Primary metrics

### Required-lane coverage

A positive lane is covered only when every frozen `REQUIRED` group is represented.

Report covered/eligible lanes and pairwise lane-count deltas.

### Useful-group recall@3

Collapse required/redundant variants by frozen required/redundancy group as appropriate.

Report useful groups retained / useful groups available.

### Unsafe/misleading retention

Count selected `UNSAFE_OR_MISLEADING` candidates.

Report total and lanes affected.

### Non-useful burden

Count selected `DISTRACTOR`, `REDUNDANT`, and `UNSAFE_OR_MISLEADING` candidates.

## Secondary metrics

Report without creating hidden success criteria:

- deep useful rescue from original retrieval ranks 4–10;
- mean original rank of selected useful evidence;
- `USEFUL_DISTINCT` retention;
- redundant retention;
- no-clear-suitable burden;
- complementary-group coverage;
- per-category metrics;
- per-lane selected classes;
- pairwise selection Jaccard;
- exact replay identity.

## Post-freeze arm roles

After valid prereveal freeze, bind the opaque arms exactly once to:

- rank-only top-3 control;
- semantic-only top-3 control;
- generic-union specialty control;
- non-true/complement specialty control;
- frozen claim-specific specialty candidate.

The evaluator source remains unchanged after binding.

## Decisive comparisons

The principal comparisons are:

1. frozen candidate vs semantic-only;
2. frozen candidate vs generic-union specialty control;
3. frozen candidate vs complement specialty control.

Rank-only is a baseline, not a principal attribution comparator.

## Support gate

A valid fresh run may receive `SUPPORTED FOR PROMOTION` only if **all** conditions hold:

1. on the 30 specialty lanes, candidate useful-group recall exceeds semantic-only by at least **0.08 absolute**;
2. candidate required-lane coverage is no worse than semantic-only by more than **1 positive lane**;
3. candidate selects **no more unsafe/misleading items** than semantic-only on the 30 specialty lanes;
4. candidate non-useful burden is no worse than semantic-only by more than **2 selections total** on the specialty lanes;
5. candidate demonstrates specificity beyond generic union, with candidate required-lane coverage no worse than generic union by more than 1 lane and at least one of:
   - useful-group recall exceeds generic union by at least **0.05 absolute**, or
   - unsafe retention is at least **2 items lower** than generic union;
6. candidate useful-group recall exceeds complement control by at least **0.08 absolute** on specialty lanes;
7. on the 6 anti-tautology lanes, candidate unsafe retention is no worse than semantic-only by more than **1 item**, and candidate useful recall is not worse than semantic-only by more than **0.05 absolute**;
8. on all 6 no-specialty controls, candidate selected identities are **exactly identical** to semantic-only;
9. all deterministic replay, permutation, irrelevant-metadata, pool-membership, K-budget, hash, and no-gold-dependency gates pass;
10. no prereveal contamination or material post-freeze scientific change occurred.

Meeting this gate supports only the bounded fresh specialty-selection mechanism. It does not authorize production deployment.

## Falsification gate

Use `FALSIFIED` on a valid run when any of the following holds:

- candidate useful-group recall on specialty lanes is worse than semantic-only by **0.08 or more**;
- candidate required-lane coverage is worse than semantic-only by **3 or more positive lanes**;
- candidate retains more than **2 additional unsafe/misleading items** versus semantic-only on specialty lanes;
- generic union exceeds candidate by at least **0.08 useful-recall absolute** while retaining no more than 2 additional unsafe items;
- complement control exceeds candidate by at least **0.08 useful-recall absolute**;
- candidate causes more than **2 additional unsafe selections** versus semantic-only across the anti-tautology category;
- candidate fails exact no-op identity on a no-specialty control under repeated deterministic execution;
- a target-owned replay/permutation/budget/pool-membership property fails repeatedly;
- execution requires gold access, downstream CAL state, or first-stage retrieval mutation.

## Inconclusive gate

Use `INCONCLUSIVE` when the run is valid but neither support nor falsification is met.

This includes:

- candidate improves semantic-only but does not separate from generic union;
- candidate separates from complement but effect size is below support threshold;
- safety and usefulness trade off without crossing falsification thresholds;
- specialty categories disagree materially and no bounded general mechanism is supported;
- preregistered exclusions reduce the primary population enough to weaken attribution.

## Apparatus terminal state

Use `BLOCKED_APPARATUS` when:

- candidate-pool or semantic-score hashes differ across arms;
- evaluator/gold bytes change after reveal;
- gold is opened before arm-output freeze;
- exact target identity cannot be verified;
- post-reveal adapter contains case-specific or gold-dependent logic;
- execution failure prevents the preregistered metrics from being computed.

## Metamorphic/system gates before gold reveal

Require:

1. exact byte-identical replay for every arm;
2. candidate input-order permutation invariance;
3. irrelevant metadata mutation invariance for fields outside each arm's input contract;
4. max K=3;
5. no duplicates;
6. all selections in frozen top-10 pool;
7. exact candidate-pool hash preserved;
8. exact semantic-score hash preserved;
9. arm outputs contain no gold class/reason data;
10. runner has no dependency on the sealed-gold ref/path;
11. adapter and arm-source hashes are frozen before execution;
12. candidate no-specialty cases are exact semantic no-ops.

## Reporting discipline

Report observed metrics separately from inference.

A disposition applies only to this frozen candidate identity and fresh cohort. It does not establish source truth, retrieval completeness, CAL semantic correctness, or a production default.
