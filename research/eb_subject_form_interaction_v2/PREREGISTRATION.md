# Subject × Evidence-Form Interaction V2 — Preregistration

## Classification

Exposed interaction pressure over an immutable candidate world.

This study reuses the exact non-gold selections/candidate diagnostics frozen before evaluation in V1:

- V1 selection freeze commit: `392a9c713558a6952947a3e4074be3957c648021`
- V1 selection file SHA-256: `869e1fc98847bf9eeff17f89f69da658f37adb835cdff516636cfc8ad0c37016`
- V1 result: Draft PR #113

No semantic model is rerun. Candidate text, per-child semantic scores, best-child attribution, parent/child descriptors, K=3, and tested caps remain frozen.

This is not fresh qualification and cannot replace context-free PR #111.

## Questions

1. Does exact claim-native subject identity continue to help under stronger interaction controls?
2. Does expected evidence form continue to help when subject identity is held fixed?
3. Does combining subject identity and expected evidence form outperform either signal alone?
4. Is any combination gain robust to operation order?
5. Do mixed wrong-field controls falsify the combination?

## Frozen populations

Use all 24 V1 parents, with primary reporting for:

- `EXPLICIT_SUBJECT_CONFLICT`
- `INHERITED_SUBJECT_CONFLICT`
- `FORM_CONFLICT`
- `STARVATION`

Secondary reporting:
- `SCOPE_CONFLICT`
- `NO_STARVATION_CONTROL`
- all 24 parents.

## Starting points

For every cap `0.01, 0.03, 0.05, 0.10`, preserve the exact V1:

- `semantic_top3`
- `child_coverage`

No V1 selection is recomputed.

## New arms

### Single-field controls

Starting from exact V1 child coverage:

- `subject_only`
- `wrong_subject_only`
- `form_only`
- `wrong_form_only`

### Combination arms

Starting from exact V1 child coverage:

- `subject_then_form`
- `form_then_subject`
- `strict_subject_and_form`

Mixed falsifiers:

- `correct_subject_then_wrong_form`
- `wrong_subject_then_correct_form`
- `wrong_subject_then_wrong_form`
- `strict_correct_subject_wrong_form`
- `strict_wrong_subject_correct_form`
- `strict_wrong_subject_wrong_form`

### Coverage-ablation arms

Starting from exact semantic top-3 instead of child coverage:

- `subject_no_coverage`
- `form_no_coverage`
- `subject_then_form_no_coverage`
- `strict_subject_and_form_no_coverage`

These test whether explicit child-coverage staging is necessary once subject/form obligations are available.

## Repair semantics

Reuse V1's bounded within-child replacement idea.

For one field:

- candidate must be semantically attributed to the same child;
- challenger must strictly improve the tested descriptor match;
- semantic-score loss must be <= frozen cap;
- K remains 3;
- no duplicate/out-of-pool selection.

Sequential combination applies the exact same repair twice in the named order.

Strict subject-and-form uses a binary joint match:

`1` only if the candidate matches both the child subject binding and expected evidence form, otherwise `0`.

A strict arm makes at most one bounded replacement per child.

## Subject identity

Correct subject is exactly:

- explicit child-native subject when present; otherwise
- parent-inherited subject already frozen in V1.

Wrong subject is the exact V1 preregistered sibling alternative.

No evidence-derived entity may be introduced.

## Evidence form

Correct form is the exact V1 expected form.

Wrong form is the exact V1 preregistered alternative.

No source, passage, answer, support/refute, query, or verdict state is used.

## Evaluation

Selections freeze before V1 deterministic fixture gold is reopened.

Primary metrics:

- complete parent coverage;
- required children covered;
- unsafe selections;
- non-useful selections;
- required selections;
- exact replay.

## Interaction interpretation

### Subject survives pressure if

On explicit + inherited subject populations:

- correct subject beats wrong subject on required-child coverage and/or unsafe retention;
- no material regression relative to child coverage.

### Form survives pressure if

On FORM_CONFLICT:

- correct form beats wrong form;
- correct form improves or safely preserves required-child coverage relative to child coverage.

### Combination has added value if

At one or more preregistered caps:

- a correct combination arm improves required-child or complete-parent coverage over **both** subject-only and form-only, or materially reduces unsafe selections without losing required coverage;
- mixed wrong controls do not reproduce the gain;
- subject→form and form→subject do not materially contradict each other.

If combination equals subject-only everywhere, record `NO_INCREMENTAL_FORM_VALUE_OVER_SUBJECT`.

If combination equals form-only everywhere, record `NO_INCREMENTAL_SUBJECT_VALUE_OVER_FORM`.

If strict joint underperforms sequential combination, retain that as evidence that obligation fields should remain separable rather than compiled into one conjunctive gate.

### Coverage staging

If no-coverage combination arms match or beat their child-coverage counterparts without safety loss, explicit coverage staging may be redundant.

If coverage-staged arms dominate, keep composition as a separate layer.

## Falsifiers

- wrong subject reproduces correct-subject performance;
- wrong form reproduces correct-form performance;
- mixed wrong combination reproduces correct combination;
- combination harms required coverage without offsetting safety gain;
- operation order causes materially opposite conclusions;
- any selection escapes frozen candidate pool or K=3;
- any gold-bearing V1 source is opened before V2 selections freeze.

## Nonclaims

This study is exposed and reuses a designed adversarial candidate world. It establishes mechanism behavior and interaction structure only, not population prevalence or fresh generalization.
