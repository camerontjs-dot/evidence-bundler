# Root-generation prerequisite RC5 full-wire qualification

## Objective

Test the final prompt-binding explanation for the prerequisite profile-writing failures.

RC5 binds the complete machine-readable profile surface literally. It changes only PROFILE-WRITER-TASK.md and preserves the qualified RC3 runtime, transport, profile contract, checker, launcher, aperture and budgets.

## Authority

Protected main at setup:

`f605c158a83fa1e17664c14fdf5841e7215a6f27`

Predecessor RC4:

- PR #138 evidence head: `00e85597e219b56d369d7bc7f1cf99871e7bfe51`
- frozen candidate: `a82d95aa002b9f70e8f8bfab4128e93ede57aae3`
- source: `8071759950407200b40cfc82c4435209dfce1f67`
- disposition: `BLOCKED_PROFILE_CONFIGURATION`
- code: `PROFILE_EVALUATOR_CONFIG_MODES`

RC4 established that the review-schema literal keys can be produced correctly, while the evaluator config shape drifted.

## Controlled change

Only PROFILE-WRITER-TASK.md changes.

The task now binds:

1. exact PRIMARY-CONFIG.json values;
2. exact EVALUATOR-CONFIG.json values;
3. exact REVIEW-SCHEMA.json mode keys and arrays;
4. minimum prompt-length and evaluator-token requirements already enforced by the frozen checker.

## Frozen invariants

Byte-identical to qualified RC3 apparatus source `55c2940d6822a6c666441f61900b2cadcfbde046`:

- AUTHORING-RUBRIC.json
- PROFILE-SURFACE.json
- BOOTSTRAP-MANIFEST.json
- CUSTODY-SCHEMA.json
- WRITER-TRANSPORT.json
- LAUNCH-STATUS.json
- validate_setup.py
- check_execution.py
- run_writer.py

No runtime, model, digest, decoding option, response envelope, source aperture, checker, launcher or semantic-rule change is authorized.

## Final decision rule for this prompt-repair sequence

If the frozen checker passes:

`SUPPORTED_FOR_GENERATION_EXECUTION`

This closes the prerequisite profile/custody qualification successfully.

If the frozen checker returns any `PROFILE_CONFIGURATION` failure after the complete literal machine surface is bound:

`FALSIFIED_PROFILE_AUTHORING_RELIABILITY`

Stop. Do not create another prompt-repair successor for this model/runtime configuration.

Other structured terminal failures retain their frozen meanings and also stop this sequence unless a separately justified non-profile authority/custody successor is later authorized.

## Attempt budget

After exact-head dedicated and ordinary CI pass:

- writer: 1
- custody/check: 1
- semantic calibration: 0
- target generation: 0
- weak generators: 0
- decisive review: 0
- tally: 0

No retry after POST begins.

## Boundary

Setup must not invoke the writer.

Future execution is context-free and may use only the frozen launcher aperture.

No semantic calibration, root-generation cases, private PR #124 work, production mutation, merge, release or promotion is authorized.

Generation capability remains UNKNOWN until a separate generation experiment actually exercises it.
