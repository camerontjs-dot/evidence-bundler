# Evidence Bundler V1 — Operational Review Burden RC0

Status: **EXECUTED — TERMINAL `APPARATUS_INVALID`**

The preregistered procedure below is preserved as the pre-execution scientific plan. Terminal evidence is frozen in `RESULTS.md`, `TERMINAL_RESULT.json`, `RAW_MECHANICAL_EVALUATOR_RECONSTRUCTION.json`, and `DEVIATION-POSTREVIEW-CONSTRUCT-MISMATCH.md`.

## Purpose

Test the heaviest remaining assumption behind the fixed-K rejection recorded in PR #72:

> Does the higher distractor-dominance observed under the frozen `10/7` profile actually degrade independent proposition-relative evidence-admission decisions, compared with the frozen `5/3` profile, on the exact relationships shared by both profiles?

This is a bounded evaluator/consumer study. It does not rerun retrieval and does not reopen the PR #72 burden threshold.

## Live authority at successor start

- repository: `camerontjs-dot/evidence-bundler`
- protected `main`: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- frozen V1 implementation: `c4e3f97ec8f0bd36180954c3aa382418925bf947`
- convergence record: PR #60, product disposition `NOT_READY`
- K=7 gold-completion record: PR #72, terminal disposition `FALSIFIED`
- PR #72 terminal head at inspection: `22d83d9af465a026eb58ff64888267c4fce18619`
- predecessor K=7 run: `34649326414`
- predecessor artifact: `10282804289`
- predecessor artifact digest: `sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`

The predecessor artifact is the only retrieval output authorized in this study.

## Frozen arms

Two blind review arms are derived mechanically from the same predecessor artifact:

- one arm contains exactly the proposition-relative relationships retained under frozen `5/3`;
- one arm contains exactly the proposition-relative relationships retained under frozen `10/7`.

The reviewer packets must not disclose which arm is which, candidate depth, retained K, rank, BM25 score, runtime admission state, prior gold state, case identity, evidence identity, PR number, or expected result.

Within each lane, retained passage order is deterministically shuffled so retrieval rank is not exposed.

## Completed qualification answer authority

The hidden supervisor answer key is derived only from:

1. `KNOWN_DISTRACTOR_BURDEN.json` in predecessor artifact `10282804289`; and
2. PR #72's frozen terminal gold completion, which resolved every previously unresolved retained relationship as `KNOWN_NON_REQUIRED_OR_DISTRACTOR` with 27/27 exact independent-review agreement.

For this study the binary semantic target is therefore:

- predecessor classification `required` -> `MATERIAL_FOR_PROPOSITION`;
- predecessor classification `known_non_required_or_distractor` -> `NONMATERIAL_FOR_PROPOSITION`;
- predecessor `unresolved_not_safely_classifiable` -> `NONMATERIAL_FOR_PROPOSITION`, solely because PR #72 independently resolved those exact relationships that way.

No new gold judgments may be created in the supervisor context.

## Independent reviewers

Each blind arm must be reviewed by **two fresh isolated semantic reviewers**, for four fresh review executions total.

Each reviewer receives only:

- that arm's blind review packet; and
- `REVIEWER_RUBRIC.md`.

Reviewers may not inspect GitHub, CAL Pipeline history, PR #60/#63/#72, ranks, scores, prior labels, the other arm, another reviewer's output, or expected experiment outcomes.

A reviewer must classify every exposed proposition-passage relationship as exactly one of:

- `MATERIAL_FOR_PROPOSITION`
- `NONMATERIAL_FOR_PROPOSITION`
- `UNRESOLVED`

Reviewers are not asked to infer support/refutation polarity or a CAL verdict.

No third-review adjudication is used. Reviewer disagreement is an observed operational outcome and must not be erased.

## Primary matched endpoint

The primary comparison is restricted to the exact **54 proposition-relative relationships shared by both frozen profiles**.

This controls for answer difficulty and asks whether embedding the same relationships in the larger review context changes decision quality.

For each arm compute across the two independent reviewers:

- false-material count: gold `NONMATERIAL`, reviewer `MATERIAL`;
- false-nonmaterial count: gold `MATERIAL`, reviewer `NONMATERIAL`;
- unresolved count;
- total error count = false-material + false-nonmaterial;
- inter-reviewer disagreement count over the 54 shared relationships.

### Directional decision rule

`NO_OBSERVED_DECISION_QUALITY_HARM` iff the larger frozen arm is **not worse on any** of these matched primary counts:

- false-material count;
- false-nonmaterial count;
- unresolved count;
- inter-reviewer disagreement count.

`DECISION_QUALITY_HARM_OBSERVED` iff the larger arm is worse on one or more matched primary counts.

This is deliberately a directional bounded test. No post-hoc tolerance margin may be invented.

## Secondary treatment-only endpoint

For the relationships present only in the larger arm, report without changing the primary rule:

- count of gold material relationships;
- count of gold nonmaterial relationships;
- reviewer material recall on those added gold-material relationships;
- reviewer rejection accuracy on added gold-nonmaterial relationships;
- unresolved and disagreement counts.

This quantifies the additional evidence value and the additional semantic handling burden.

## Deterministic exposure metrics

Before review, freeze and report for each arm:

- proposition-relative relationship count;
- unique physical passage count;
- total passage characters and whitespace-token count as presented;
- unique physical passage characters and whitespace-token count;
- lane count.

These are descriptive workload/exposure measurements, not substitutes for human elapsed time.

**This experiment does not claim to measure human wall-clock review time.**

## Terminal research dispositions

Use exactly one:

### `SUPPORTED FOR PROMOTION`

Use only if:

- all four context-free reviewer outputs pass aperture/identity checks;
- the primary result is `NO_OBSERVED_DECISION_QUALITY_HARM`;
- no apparatus-invalidating deviation occurred.

Meaning: on this frozen cohort, the PR #72 distractor-dominance proxy did not predict worse blind admission decision quality on the matched relationships. This authorizes only a separate V1 policy/disposition review. It does not itself override PR #72, qualify K=7 as the production default, merge, release, tag, or promote.

The promoted claim is only `NO_OBSERVED_DECISION_QUALITY_HARM_IN_MATCHED_BLIND_REVIEW`; this disposition is **not** Evidence Bundler V1 promotion authorization.

### `FALSIFIED`

Use if the primary result is `DECISION_QUALITY_HARM_OBSERVED`.

Meaning: the larger review context produced worse matched decision quality on at least one preregistered primary count. Fixed-K widening remains rejected and no additional fixed-K test is authorized.

### `INCONCLUSIVE`

Use if reviewer independence cannot be established, required reviewer outputs are missing, or the study completes but the frozen evidence cannot support the requested comparison.

### `APPARATUS_INVALID`

Use for packet/answer-key identity mismatch, profile construction error, leaked forbidden fields, altered predecessor bytes, or evaluator defect that changes scientific meaning.

## Interpretation boundary

Even a `SUPPORTED FOR PROMOTION` result would establish only that **decision-quality harm was not observed in this bounded model-review study**. It would not establish:

- acceptable human wall-clock review cost;
- universal robustness to distractors;
- external-corpus retrieval quality;
- a production retrieval default;
- CAL semantic correctness;
- promotion or release readiness.

## Stop boundary

After the terminal result is frozen, stop.

Do not automatically test K=8, another fixed K, a selector, a reranker, query rewriting, semantic retrieval, threshold changes, production defaults, merge, release, tag, or promotion.
