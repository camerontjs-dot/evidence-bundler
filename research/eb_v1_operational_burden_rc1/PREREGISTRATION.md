# Evidence Bundler V1 — Task-Aligned Operational Burden RC1

Status: **PREREGISTERED — REFERENCE AND TEST REVIEWS NOT YET RUN**

## Purpose

Resolve the construct-validity failure preserved in PR #73 without rerunning retrieval.

RC0 attempted to score a semantic-materiality task against predecessor `required` / `known_non_required_or_distractor` burden labels. Those constructs were not equivalent. RC1 removes that translation.

The bounded question is:

> When reviewers apply one lane-relative operational keep/drop rubric to the exact frozen `5/3` and `10/7` retained evidence worlds, does the larger `10/7` context degrade reproducible keep/drop decisions on the relationships shared by both profiles?

This is a model-review operational-stability study. It is not a retrieval rerun, human-time study, production qualification, or V1 promotion.

## Live authority at successor start

- repository: `camerontjs-dot/evidence-bundler`
- protected `main`: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- frozen V1 implementation: `c4e3f97ec8f0bd36180954c3aa382418925bf947`
- convergence record: PR #60, product disposition `NOT_READY`
- K=7 gold-completion record: PR #72, terminal `FALSIFIED`
- RC0 record: PR #73, terminal `APPARATUS_INVALID`
- PR #73 terminal head observed before RC1 setup: `dd3aa6fbb19f77895131224319dd26d02a2bae39`
- predecessor K=7 run: `34649326414`
- predecessor artifact: `10282804289`
- predecessor artifact digest: `sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`

The predecessor artifact is the only retrieval output authorized in RC1.

## Frozen arms

Two neutral arms are derived mechanically from the predecessor artifact:

- one arm contains exactly the retained proposition-passage relationships from frozen `5/3`;
- one arm contains exactly the retained proposition-passage relationships from frozen `10/7`.

Arm-to-profile mapping is supervisor-only. Semantic reviewers must not be told profile identity, K, rank, score, prior admission state, predecessor burden labels, prior gold, PR history, expected results, or the other arm.

Within each lane, passage order and lane order are deterministically shuffled. Opaque lane and relation IDs are arm-specific.

## One task-aligned operational rubric

Every semantic reviewer, reference or test, uses the same four labels and the same packet content for that arm.

### `KEEP_DISTINCT`

Retain the passage because, given the other passages in the same lane, it contributes distinct evidentiary information materially useful for assessing the exact proposition. Distinct support, refutation, qualification, limitation, or necessary contextual evidence can qualify.

### `DROP_REDUNDANT`

The passage bears materially on the proposition, but its evidentiary contribution is fully duplicated or subsumed by another passage in the same lane. Dropping it loses no distinct evidentiary contribution.

### `DROP_DISTRACTOR`

The passage does not provide a proposition-relevant evidentiary contribution to the review record. This includes unrelated entities or conditions, lexical/numeric decoys, operational details that do not bear on the proposition, hypothetical/rejected/unverified mentions that do not themselves contribute usable evidence, and other noncontributory material.

### `UNRESOLVED`

The authorized proposition, lane context, and passage text are insufficient to classify the relationship safely. Do not infer hidden entity bindings or provenance facts that are not present in the packet.

These labels are lane-relative. The same semantic passage may legitimately be `KEEP_DISTINCT` in a smaller lane and `DROP_REDUNDANT` in a larger lane if added evidence makes its contribution redundant.

## Stage 1 — independent task-aligned reference

RC1 does **not** inherit predecessor burden labels as the answer key.

For each arm, launch three fresh isolated semantic reference reviewers. Six reference executions total.

Each reference reviewer receives only:

- that arm's blind packet; and
- the frozen operational rubric.

Reference reviewers may not inspect GitHub, CAL Pipeline history, predecessor labels/gold, RC0 outputs, the other arm, another reference reviewer, or expected outcomes.

For each relationship, consolidate the three labels mechanically:

- if at least two reviewers return the same non-`UNRESOLVED` label, that label becomes the arm-specific reference;
- otherwise the arm-specific reference is `UNRESOLVED`.

This includes cases where `UNRESOLVED` is the plurality/majority or where three different labels are returned.

The full raw reference outputs and consolidated arm-specific references must be frozen in a git commit before Stage 2 starts.

No human or supervisor semantic relabeling is allowed.

## Stage 2 — fresh operational test review

After the Stage 1 reference commit is frozen, launch two **new** fresh isolated semantic test reviewers per arm. Four test executions total.

No Stage 2 reviewer may be a resumed Stage 1 context.

Each receives only the same arm packet and same operational rubric. They may not inspect the Stage 1 reference, another reviewer, the other arm, GitHub, prior results, or expected outcomes.

## Primary matched endpoint

The frozen profiles share exactly 54 semantic proposition-passage relationships.

The primary scored cohort is the intersection of shared relationships whose **arm-specific Stage 1 reference is non-`UNRESOLVED` in both arms**.

Coverage guard:

- at least 49 of 54 shared relationships (>=90%) must be scoreable; and
- every one of the 18 normative proposition lanes must contribute at least one scoreable matched relationship.

If either guard fails, primary disposition is `INCONCLUSIVE` regardless of directional metrics. This prevents a no-harm result created by silently dropping difficult relationships.

Map operational labels to the binary action:

- `KEEP_DISTINCT` -> `KEEP`
- `DROP_REDUNDANT` -> `DROP`
- `DROP_DISTRACTOR` -> `DROP`
- reviewer `UNRESOLVED` remains `UNRESOLVED`

For each arm, across its two Stage 2 reviewers on the exact scoreable matched cohort, compute:

- pooled false-keep count: reference `DROP`, reviewer `KEEP`;
- pooled false-drop count: reference `KEEP`, reviewer `DROP`;
- pooled reviewer-unresolved count;
- inter-reviewer action-disagreement count, where mapped outputs differ among `KEEP`, `DROP`, `UNRESOLVED`.

### Directional rule

`NO_OBSERVED_OPERATIONAL_DECISION_HARM` iff the larger frozen arm is not worse than the smaller arm on **any** of:

- pooled false-keep;
- pooled false-drop;
- pooled reviewer-unresolved;
- inter-reviewer action disagreement.

`OPERATIONAL_DECISION_HARM_OBSERVED` iff the larger arm is worse on one or more primary counts.

No tolerance margin or metric weighting may be introduced after results are visible.

## Secondary endpoints

Report without changing the primary rule:

1. arm-specific reference counts for all four labels;
2. reference-resolution counts and any relationships unresolved in either arm;
3. exact four-way label accuracy and disagreement in Stage 2;
4. relationships whose arm-specific reference changes between profiles, including `KEEP_DISTINCT <-> DROP_REDUNDANT` context effects;
5. larger-arm-only 42 relationships: reference label distribution and Stage 2 keep/drop accuracy where reference is resolved;
6. deterministic exposure metrics already frozen by construction: relationship count, unique physical passage count, presented characters/tokens, and lane count.

These are descriptive and diagnostic. They do not change the primary disposition.

## Reference/evaluator independence boundary

The same Codex supervisor process may orchestrate files, subprocesses, validation, commits, and pushes because continuity is useful for mechanics.

It must not perform semantic classification itself or rewrite child judgments.

All semantic reference and test judgments must come from new ephemeral child contexts with the exact allowlisted packet + rubric aperture.

## Apparatus checks

Before accepting any child output, mechanically verify:

- expected schema;
- exact packet canonical hash;
- exact relation-ID set and count;
- allowed labels only;
- unique reviewer ID within RC1;
- explicit fresh-context / independence assertions;
- no exposure to other arm or other reviewer outputs.

Trace receipts must show only the authorized packet and rubric being read. Any child that accesses forbidden information invalidates that child execution; do not silently substitute or relabel it.

## Terminal dispositions

Use one primary research disposition:

### `SUPPORTED FOR PROMOTION`

Use only if:

- all required Stage 1 and Stage 2 executions pass aperture/identity checks;
- Stage 1 is frozen before Stage 2;
- coverage guards pass;
- primary result is `NO_OBSERVED_OPERATIONAL_DECISION_HARM`;
- no scientific apparatus defect changes the meaning of the test.

Meaning: on this frozen synthetic cohort and model-review apparatus, the larger `10/7` context did not produce worse matched keep/drop decision quality under the task-aligned operational rubric. This authorizes only a separate V1 policy/disposition review. It does not itself overturn PR #72, set the production default, merge, release, tag, or promote V1.

### `FALSIFIED`

Use if the apparatus is valid, coverage guards pass, and the primary result is `OPERATIONAL_DECISION_HARM_OBSERVED`.

Meaning: the larger review context worsened at least one preregistered matched operational-decision count. Fixed-K widening remains rejected on this decision-quality criterion.

### `INCONCLUSIVE`

Use if required executions/independence are missing, coverage guards fail, or a scientific apparatus defect prevents the frozen question from being answered safely.

If an apparatus defect causes this disposition, preserve `APPARATUS_INVALID` as an experiment-specific conclusion/deviation, not as a replacement primary disposition.

### `SUPERSEDED`

Use only if this experiment is formally superseded before terminal evaluation by a new preregistered experiment. Do not use it to hide a completed negative or invalid result.

## Interpretation boundary

Even `SUPPORTED FOR PROMOTION` establishes only bounded model-review stability on this frozen cohort. It does not establish:

- acceptable human wall-clock review cost;
- external-corpus retrieval quality;
- universal robustness to distractors;
- human reviewer performance;
- CAL semantic correctness;
- a production retrieval default;
- V1 release readiness.

## Stop boundary

After the terminal RC1 record is frozen, stop.

Do not automatically test K=8, another fixed K, selector/reranker changes, query rewriting, semantic retrieval, threshold changes, production defaults, merge, release, tag, or V1 promotion.
