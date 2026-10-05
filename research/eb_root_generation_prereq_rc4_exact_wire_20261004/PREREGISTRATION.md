# Root-generation prerequisite RC4 exact-wire qualification

## Objective

Test whether the RC3 profile-generation failure was caused by insufficient binding of the review-schema field names rather than inability to produce the required semantic surface.

RC4 changes only PROFILE-WRITER-TASK.md. It explicitly requires REVIEW-SCHEMA.json to use the exact machine keys already defined by PROFILE-SURFACE.json and forbids the aliases observed in RC2/RC3.

## Authority

Repository: camerontjs-dot/evidence-bundler.

Protected main at setup:

`f605c158a83fa1e17664c14fdf5841e7215a6f27`

Predecessor RC3:

- PR #130 final evidence head: `c4ae03e2f650a566dd04e933f654f194315f8c30`
- frozen candidate head: `0cb0dc9dffbf701759b55b066c32f5dd6041d5ba`
- source commit: `b5d379d23fe9d86f04c6fffda0b438097a55d25b`
- disposition: `BLOCKED_PROFILE_CONFIGURATION`
- checker code: `PROFILE_CALIBRATION_OUTPUT_MISSING`

Observed RC3 returned review-schema aliases:

- `input_fields`
- `output_fields`
- `decision_enum`
- `root_status_enum`

The returned content otherwise represented both modes and the intended enum values. This motivates a field-name-binding successor rather than another custody/checker change.

## Controlled change

Exactly one qualified apparatus input changes:

`PROFILE-WRITER-TASK.md`

The new task requires literal keys from `PROFILE-SURFACE.json`:

Calibration:
- `input`
- `output`
- `decision`

Decisive:
- `input`
- `output`
- `root_status`
- `decision`
- `checks`

It explicitly forbids aliases including `input_fields`, `output_fields`, `decision_enum`, `root_status_enum`, and `check_fields`.

## Frozen invariants

Reuse byte-for-byte from the qualified RC3 apparatus:

- `AUTHORING-RUBRIC.json`
- `PROFILE-SURFACE.json`
- `BOOTSTRAP-MANIFEST.json`
- `CUSTODY-SCHEMA.json`
- `WRITER-TRANSPORT.json`
- `LAUNCH-STATUS.json`
- `validate_setup.py`
- `check_execution.py`
- `run_writer.py`

No runtime, model, digest, request option, output envelope, aperture, checker, launcher, semantic rule or attempt-budget change is authorized.

## Future execution budget

After exact frozen candidate qualification:

- writer: 1
- custody/check: 1
- semantic calibration: 0
- target generation: 0
- weak generators: 0
- decisive review: 0
- tally: 0

No retry after POST begins.

## Competing explanations

H1: The writer can produce the required review surface when exact key names are explicitly bound.

H2: Even with exact key binding, the writer still fails the required surface, which would falsify the prompt-binding explanation for this model/runtime/task configuration.

H3: A different profile failure appears after the alias issue is removed, indicating the previous failure masked another defect.

## Acceptance

A future execution is supported for generation execution only if the frozen structured checker passes the complete five-file surface.

A future execution that returns the old aliases or otherwise misses the literal review wire stops `BLOCKED_PROFILE_CONFIGURATION`.

Any custody/transport failure uses the qualified structured categories.

## Boundary

Setup must not invoke the writer.

After exact-head dedicated CI and ordinary CI succeed, exactly one context-free writer/custody execution is authorized.

No semantic calibration, generation cases, private PR #124 work, production change, merge, release or promotion is authorized.

Generation capability remains UNKNOWN until a later separate generation experiment actually exercises it.
