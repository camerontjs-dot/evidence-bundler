# Evidence Bundler V1 — Retention-Boundary Discriminator: K=7

Status: **PREREGISTERED — EXECUTION NOT YET RUN**

This record is frozen before successor execution. It defines one bounded retention experiment and does not amend Evidence Bundler PR #60, Claim Audit Lab PR #102, or the frozen Evidence Bundler V1 implementation.

## Research question

> Is retaining seven candidates per normative lane an acceptable bounded V1 remedy on the frozen qualification set, or does the additional retained review/noise burden make fixed-K widening unsuitable as the smallest V1 retention remedy?

The experiment does **not** ask whether rank 7 is mechanically included by `retained_k=7`; the predecessor already localized the preserved evidence to rank 7 under candidate depth 10.

## Frozen authorities

- repository: `camerontjs-dot/evidence-bundler`
- immutable V1 implementation: `c4e3f97ec8f0bd36180954c3aa382418925bf947`
- implementation tree: `1d254e38cb0e174635efc7687c2b0ab091aa52b3`
- research-branch base: live `main` at `c26fbd4bfc8ba5c2604a784af158594b59fcae37`; the workflow checks out the immutable V1 implementation separately
- predecessor convergence PR: `#60` — concluded evidence record, product disposition `NOT_READY`
- predecessor decisive run: `34608721684`
- predecessor artifact: `10267561504`
- predecessor artifact digest: `sha256:86283d446726f4c5d430d87bfec642427a099575b9f7e1de9835f74b2060b4f9`
- frozen EB eight-case fixture authority: `dd4fb2b89f351fbdcd8b08e48dd9d7d1f10c2d05`
- frozen CAL preserved decoy authority: `7a46d61585f868a2e904f870528f605fb06772ea`
- released Contract A commit: `529c92b49a34d5c610618551a8737f019f9fa332`
- released Contract A validator blob: `42e5f5b3bf38d677445e9d01ea130ba604e53409`

The later PR #60 documentation head is not implementation authority.

## Frozen predecessor observations

Do not reinterpret or overwrite these results:

- `5/3`: `RET-AP-P6` absent from candidate pool.
- `10/3`: `RET-AP-P6` present at natural rank 7, lost at retention.
- `10/6`: `RET-AP-P6` present at natural rank 7, lost at retention.
- frozen `5/3` cohort summary: 9 cases, 18 normative lanes, 54 retained proposition-passage relationships.

## Experimental treatment

Run exactly one successor treatment:

```text
candidate_depth = 10
retained_k = 7
```

A same-run `5/3` reproduction is permitted only as baseline and apparatus-consistency control.

Forbidden in this experiment: any other K, any other candidate depth, grid search, reranking, semantic retrieval, query rewriting, MMR/diversity, adaptive or threshold selection, root rescue, decomposition change, model tuning/training, CAL semantics, or V1 source mutation.

## Frozen cohort

Use exactly:

1. the eight cases under `research/cal_rc0_contract_b_handoff/fixtures/cases/` at EB research head `dd4fb2b...`;
2. the exact `RETRIEVAL_APERTURE` case under `pipeline/cal_rc0/data_campaign/retrieval_aperture/` at CAL head `7a46d615...`.

Expected identity: 9 cases, 18 normative lanes. Any mismatch is `APPARATUS_INVALID`.

No corpus bytes, propositions, Contract A declarations, decomposition, chunking, evaluator gold, or admission fixtures may be changed.

## Gold firewall

Runtime retrieval/retention execution must not consume evaluator relevance gold.

Execution order is fixed:

1. verify exact implementation and frozen fixture authorities;
2. load case and admission/runtime inputs only;
3. execute and freeze baseline `5/3` candidate ordering, raw scores, package outputs and retention states;
4. execute and freeze treatment `10/7` candidate ordering, raw scores, package outputs and retention states;
5. write pre-gold runtime snapshots;
6. only then load evaluator gold and perform required-evidence and burden classification;
7. never alter rankings, retention, admission, corpus state, or package state after gold is opened.

The result receipt must record that gold was opened only after runtime snapshots were serialized.

## Primary causal requirements

### A. Preserved defect crosses retention boundary

In the exact decoy case, `RET-AP-P6` must remain naturally produced in the candidate pool at its unmodified rank and be `retained` under `10/7`. It may not be special-cased, reordered, or manually admitted.

### B. No required-evidence regression

Compare each required evidence item's first missing stage against frozen `5/3`.

Stage order from earliest to latest:

`candidate_pool -> retention -> admission -> present`

No required item may move to an earlier stage under treatment.

### C. Structural invariants

Only retention configuration may differ intentionally. Preserve Contract A/proposition authority, normative lane identity, query derivation, candidate ordering, raw scores for the same candidate-depth-10 execution, source and passage identity, passage bytes/hash/offsets, candidate aperture, package validation, nomination state, admission semantics, semantic-authority prohibition, and root-diagnostic policy.

No support/refutation/verdict field may appear. BM25 score remains diagnostic only and must not be added to the V1 package contract.

### D. Review-burden gate

#### Baseline consistency

Baseline reproduction must equal exactly:

- 18 normative lanes;
- 54 retained proposition-passage relationships.

Otherwise stop as `APPARATUS_INVALID`.

#### Hard total-retention ceiling

`10/7` must retain no more than 108 proposition-passage relationships.

#### Per-lane burden

For each normative lane record baseline count, treatment count, delta and seven-position saturation. Report mean, median and maximum delta, plus saturated-lane count and proportion.

Saturation alone is diagnostic.

#### Known non-required / distractor burden

Use frozen gold only where it supplies sufficient classification authority. Each retained relationship is classified as:

- `required`;
- `known_non_required_or_distractor`;
- `unresolved_not_safely_classifiable`.

Absence from sparse gold is never itself evidence of irrelevance.

A lane is `KNOWN_DISTRACTOR_DOMINATED` only if classification coverage is sufficient for the lane and at least 80% of its retained relationships are known non-required/distractor.

Burden gate fails if more than 50% of fully adjudicable normative lanes are `KNOWN_DISTRACTOR_DOMINATED`.

If the frozen gold cannot support the required classification coverage, terminal disposition is `INCONCLUSIVE_GOLD_COVERAGE`; unknowns must not be converted to distractors.

#### Physical-passage burden

Report total retained proposition-passage relationships, total unique physical retained passages, per-case unique physical passage count, and the difference between physical deduplication and proposition-relative review relationships. Physical deduplication must not erase proposition-specific review cost.

#### Efficiency diagnostic

Report without universal threshold:

- additional retained relationships versus `5/3`;
- additional known non-required/distractor relationships;
- newly recovered required relationships;
- added relationships per newly recovered required relationship.

## Admission boundary

Admission behavior remains frozen. A required passage that moves from retention failure to admission failure demonstrates crossing the retention boundary but does not imply semantic acceptance. No admission repair and no CAL semantic execution are permitted.

## Required outputs

The frozen result set must contain at minimum:

- `PREREGISTRATION.md`
- `RETENTION_BOUNDARY_RESULT.json`
- `BASELINE_5_3_RECEIPT.json`
- `TREATMENT_10_7_RECEIPT.json`
- `CANDIDATE_ORDERING_COMPARISON.json`
- `REQUIRED_EVIDENCE_STAGE_COMPARISON.json`
- `REVIEW_BURDEN.json`
- `KNOWN_DISTRACTOR_BURDEN.json`
- `STRUCTURAL_INVARIANTS.json`
- `RESULTS.md`
- `SHA256SUMS`

## Terminal dispositions

Exactly one must be emitted:

- `K7_NOT_FALSIFIED_AS_SMALLEST_BOUNDED_REMEDY`
- `FIXED_K_WIDENING_REJECTED_ON_QUALIFICATION_SET`
- `K7_RETENTION_REMEDY_FALSIFIED`
- `INCONCLUSIVE_GOLD_COVERAGE`
- `APPARATUS_INVALID`

`K7_NOT_FALSIFIED_AS_SMALLEST_BOUNDED_REMEDY` means only that `10/7` was not falsified as the smallest fixed-K retention remedy on this frozen qualification set. It does not qualify a production V1 default.

## Governance and stop boundary

This successor is a Draft Research PR only. PR #60 remains the completed convergence record and Evidence Bundler V1 remains `NOT_READY`. Passing does not authorize promotion. Failing does not authorize automatic selector redesign.

After the exact `10/7` result is frozen and one terminal disposition is recorded, stop. No K=8, selector experiment, threshold tuning, BM25 change, CAL semantics, production-default mutation, or PR #60 amendment is authorized.