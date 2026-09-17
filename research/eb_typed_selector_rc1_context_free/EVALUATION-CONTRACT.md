# EB Typed Selector RC1 — Decisive Evaluation Contract

## Purpose

Evaluate four frozen post-reveal arms on the exact same 30 fresh depth-10 candidate pools at the same maximum selection budget of 3.

The evaluator is authored and frozen **before** the arm implementations are revealed.

Use opaque arm keys during prereveal authoring:

- `ARM_A`
- `ARM_B`
- `ARM_C`
- `ARM_D`

The post-freeze reveal packet will bind those keys to concrete implementations. The evaluator must not change after that binding is known.

## Input invariants

For every lane and every arm:

- candidate pool identity/hash is identical;
- exactly the same claim/profile input is used;
- maximum selected items = 3;
- duplicate candidate IDs are forbidden;
- selected IDs must be members of the frozen top-10 pool;
- no arm may alter first-stage retrieval or candidate ordering/history;
- gold must not be read by selection execution.

Any violation is `BLOCKED_APPARATUS` for the decisive run unless the preregistered protocol explicitly classifies it as a terminal target failure.

## Primary metrics

### 1. Required lane coverage

For positive lanes, count a lane covered only when every frozen `REQUIRED` group is represented by at least one selected candidate.

Report:

- covered positive lanes / eligible positive lanes;
- absolute lane-count difference for every pair of arms;
- per-category coverage.

### 2. Useful-item recall@3

Treat `REQUIRED` and `USEFUL_DISTINCT` as useful items, with redundant variants collapsed to their frozen redundancy/required group where applicable.

Report useful groups retained divided by useful groups available in the top-10 pool.

### 3. Unsafe/misleading retention

Count selected candidates labeled `UNSAFE_OR_MISLEADING`.

Report total, lanes affected, and per-category count.

### 4. Non-useful burden

Count selected candidates labeled `DISTRACTOR`, `REDUNDANT`, or `UNSAFE_OR_MISLEADING`.

Report total across all 30 lanes and per-lane mean.

## Secondary metrics

Report, without promoting them into hidden success criteria:

- `USEFUL_DISTINCT` item retention;
- `REDUNDANT` retention;
- category-10 selected burden when no candidate is useful;
- mean original retrieval rank of selected useful items;
- deep-useful rescue count for useful items originally ranked 4-10;
- ordinary-easy-lane coverage;
- complementary-coverage success;
- per-category arm deltas;
- selection overlap/Jaccard between arms;
- exact replay identity.

## Predeclared decisive comparison

The principal scientific comparison is the frozen candidate arm versus the semantic comparison arm after the post-freeze binding is revealed.

The rank-only arm is a baseline/control. The weak arm is an attribution/evaluator-discrimination control.

Do not select a different principal comparator after seeing results.

## Support gate

A result may receive `SUPPORTED FOR PROMOTION` only when **all** of the following hold on the frozen fresh cohort:

1. candidate arm required-lane coverage exceeds semantic-arm coverage by **at least 3 positive lanes**;
2. candidate arm useful-item recall@3 exceeds semantic-arm recall by **at least 0.08 absolute**;
3. candidate arm selects **no more `UNSAFE_OR_MISLEADING` items** than the semantic arm;
4. candidate arm non-useful burden is no worse than semantic by more than **3 selections total** across the 90 available selection slots;
5. on the 3 ordinary-straightforward lanes, candidate coverage is no worse than the better of rank-only and semantic by more than **1 lane**;
6. the weak arm does **not** independently clear the same primary improvement gate in a way that makes the claimed mechanism non-discriminating; specifically, at least one must be true:
   - candidate exceeds weak arm by at least **2 positive lanes** in required-lane coverage; or
   - candidate exceeds weak arm by at least **0.05 absolute** useful-item recall;
7. all deterministic replay and metamorphic/system gates pass;
8. no prereveal contamination or material post-freeze scientific change occurred.

These thresholds are frozen before target reveal and may not be relaxed after outcomes are known.

## Falsification gate

Use `FALSIFIED` when any of the following occurs on a valid decisive run:

- candidate arm required-lane coverage is worse than semantic by **3 or more positive lanes**;
- candidate arm useful-item recall@3 is worse than semantic by **0.08 or more absolute**;
- candidate arm selects more than **2 additional `UNSAFE_OR_MISLEADING` items** versus semantic;
- candidate arm loses all 3 ordinary-straightforward lanes while rank-only or semantic covers at least 2;
- a target-owned deterministic/system property fails repeatedly on exact replay;
- the candidate requires forbidden access to gold, CAL verdicts, or first-stage mutation to execute.

## Inconclusive gate

Use `INCONCLUSIVE` when the decisive run is valid but neither the support nor falsification gate is met, including when:

- candidate improves over semantic but below the preregistered effect size;
- candidate and weak arm are too close to attribute the claimed added machinery;
- safety/burden is mixed but below the falsification threshold;
- too many lanes were preregistered out of primary scoring to retain the intended discriminating power;
- an unexpected evaluator limitation prevents a strong mechanism claim without invalidating the observations.

## Apparatus terminal state

Use `BLOCKED_APPARATUS` rather than a scientific disposition when:

- candidate pool hashes differ between arms;
- evaluator/gold bytes changed after reveal;
- gold was opened by the execution lane before arm output freeze;
- the post-reveal adapter contains case-specific logic, gold-dependent logic, or target modifications;
- exact target/scorer identity cannot be verified;
- an execution failure prevents the preregistered metrics from being computed.

## Metamorphic/system gates

Before opening gold, require:

1. byte-identical arm output on exact replay;
2. candidate input-order permutation leaves selected identities unchanged for every deterministic arm;
3. irrelevant metadata mutation does not change the frozen candidate arm selection when that metadata is outside the target input contract;
4. no arm selects duplicate IDs;
5. no arm selects more than 3 candidates;
6. all selections are members of the frozen depth-10 pool;
7. exact first-stage pool hash is preserved across arms;
8. selection output contains no gold class/reason fields;
9. selection runner has no read dependency on the sealed-gold path/ref;
10. post-reveal adapter/source hashes are recorded before evaluation.

A metamorphic test should be designed to fail if a runner accidentally sorts by input order, reads irrelevant metadata, exceeds K, or uses gold labels. Preserve the failing control if one occurs.

## Reporting discipline

Report observations separately from inference.

A research disposition applies only to the bounded question tested by this cohort and frozen selector identity. It does not establish universal evidence completeness, source truth, CAL semantic correctness, or a production retrieval default.
