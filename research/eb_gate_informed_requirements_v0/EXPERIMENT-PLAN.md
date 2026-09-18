# Experiment sequence

## Purpose

Test the smallest causal question first.

The first question is not:

> Can Gate metadata make retrieval better?

It is:

> Does a qualified evidence-shape requirement contain useful selection information beyond semantic relevance on an identical frozen candidate pool?

If not, first-stage Gate-informed retrieval is not justified.

## Stage 0 - prerequisite upstream authority

Do not execute a decisive Gate-informed EB experiment until the tested upstream fields have explicit authority compatible with EB hint use.

At minimum the experiment must bind exact identities for:

- evidence-shape requirement field;
- candidate evidence-form characterization field or EB-owned equivalent;
- any decomposition/child binding used;
- qualification records supporting `QUALIFIED_HINT`.

Current shadow results are design evidence, not causal authority.

## Stage 1 - postmortem on RC1

Use the now-exposed RC1 cohort only for retrospective mechanism analysis.

Questions:

1. Which lanes did semantic-only cover that RC1 typed selection lost?
2. Which score/signal displaced the useful candidate?
3. Which four unsafe selections were removed by evidence posture?
4. Would a pure evidence-form coverage repair have acted in those lanes?

This stage may generate hypotheses. It cannot qualify a successor because the cohort is exposed.

## Stage 2 - frozen-pool evidence-shape experiment

### Fixed objects

Hold constant:

- exact claims/propositions;
- exact depth-10 candidate pools and candidate ordering;
- exact semantic model/revision/runtime;
- K=3;
- candidate characterization mechanism;
- Gate hint artifacts;
- gold;
- evaluator;
- thresholds.

Do not rerun or modify first-stage retrieval.

### Primary arms

#### Arm A - semantic incumbent

Top 3 by frozen semantic relevance.

#### Arm B - semantic + correct evidence-shape coverage

Start from the semantic incumbent and apply only the frozen bounded coverage-repair rule using the correct qualified requirement.

#### Arm C - semantic + claim-family-only control

Tests whether coarse claim family explains the effect without the richer evidence-shape expression.

#### Arm D - semantic + wrong/shuffled requirement control

Bind a valid but intentionally mismatched requirement from another eligible lane under a frozen permutation.

This is the key causal control.

If Arm B and Arm D improve similarly, evidence-shape correctness has not been established as the cause.

### Optional independent arm

A semantic + random-diversity or form-diversity arm may be useful to distinguish specific requirement coverage from generic diversification.

Do not add it if it materially complicates the primary four-arm experiment.

## Metrics

Primary:

- required evidence-group/lane coverage at K=3;
- useful distinct recall at K=3;
- unsafe/misleading retention;
- non-useful burden.

Secondary:

- number of substitutions from the semantic incumbent;
- semantic rank/score loss per substitution;
- requirement targets covered;
- false coverage, where form matches but gold usefulness does not;
- no-clear-suitable behavior;
- easy-case regression;
- decomposition child coverage where applicable.

## Support burden

Do not freeze exact numeric thresholds on this design branch.

The later preregistration should require all of the following in some explicit form:

1. Arm B improves required coverage over Arm A by a meaningful preregistered margin.
2. Arm B does not materially reduce useful recall.
3. Arm B does not materially increase unsafe retention or non-useful burden.
4. Arm B outperforms Arm D, proving correct requirements matter.
5. Arm B outperforms or meaningfully differs from the coarse family control where the richer expression claims added information.
6. Easy cases do not regress materially.
7. Replay and metamorphic gates pass.

## Direct falsifiers

A decisive experiment should falsify the causal hypothesis if any preregistered condition establishes one of these mechanisms:

- correct requirements perform no better than shuffled/wrong requirements;
- coverage repair worsens useful evidence retention beyond the allowed bound;
- candidate form labels systematically reward form-matching but useless evidence;
- unknown requirements are frequently needed for gains;
- the effect disappears when semantic relevance is held fixed;
- implementation requires case-specific rules or gold-relative logic.

## Required metamorphic tests

Before gold reveal:

- exact replay;
- candidate input-order invariance;
- irrelevant metadata invariance;
- requirement-expression serialization invariance;
- equivalent `any_of` child-order invariance;
- duplicate requirement-node rejection or canonical collapse;
- unknown requirement produces exact semantic-baseline behavior;
- optional-only requirement cannot force substitution;
- shuffled-control mapping is frozen and reproducible;
- no gold/CAL/downstream verdict field is present in selector inputs.

## Stage 3 - evidence-posture experiment

Run separately from evidence-shape coverage if the first experiment supports the requirement signal.

Question:

> Can evidence posture reduce unsafe retention without harming semantic/requirement coverage?

Compare:

- semantic + supported requirement coverage;
- same + posture;
- same + posture ablation or deliberately weakened posture control.

Do not reuse RC1's simple regex implementation as automatically authoritative merely because it reduced four unsafe selections in RC1.

## Stage 4 - first-stage retrieval experiment

Eligible only after Stage 2 supports the evidence-shape signal.

Hold a fresh corpus and Gate hint set fixed, then compare first-stage retrieval with and without EB-generated evidence-shape retrieval intents.

Possible arms:

- current exact-proposition retrieval;
- current retrieval + EB-generated multi-intent retrieval;
- shuffled/wrong requirement retrieval-intent control.

Primary question:

> Does the correct requirement increase useful evidence availability in the depth-N pool, not merely rearrange already-available candidates?

Measure:

- required/useful evidence present by depth N;
- first useful rank;
- evidence-form coverage by depth N;
- distractor burden;
- source breadth/redundancy;
- deterministic replay;
- wrong-requirement control.

Do not tune K, candidate depth, query generator, or evidence-shape compiler after fresh-gold exposure.

## Stage 5 - integration consideration

Only after independent support for:

1. upstream Gate hint authority;
2. candidate characterization;
3. fixed-pool coverage effect;
4. first-stage effect, if used;
5. safety/posture effect, if used;

may a successor EB integration candidate be considered.

The smallest justified promotion is preferred. A supported selector-stage hint does not automatically authorize first-stage retrieval steering.
