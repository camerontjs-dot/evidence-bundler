# Root-generation prerequisite qualification RC2

## Objective / decision

Determine whether the exact RC1 prerequisite apparatus can establish the frozen five-file profile surface and bounded custody verification when the single runtime authority variable that blocked RC1 is changed from service version 0.34.4 to 0.35.1.

A supported result is `SUPPORTED_FOR_GENERATION_EXECUTION` for this exact 0.35.1 runtime only. It is not evidence that generation capability succeeds.

## Predecessor evidence

RC1 is preserved in Evidence Bundler PR #126.

- terminal head: `6d86f145e5e32e72bbd491573d8117f3adb8faba`
- frozen source commit: `ac948782db183bd209f0907cdd7c6e04d13bf15a`
- source tree: `76e46e3c95b04f501e0d56904de95dc2e24dc6f8`
- terminal disposition: `BLOCKED_AUTHORITY`
- required service version: `0.34.4`
- observed service version after stop: `0.35.1`
- writer attempt consumed: no
- custody attempt consumed: no

RC1 reached no writer POST and produced no profile, semantic, generation, weak-system, review, or tally output.

## Controlled substitution

Change exactly:

`service_version: 0.34.4 -> 0.35.1`

in:

- `BOOTSTRAP-MANIFEST.json`
- `WRITER-TRANSPORT.json`

The following RC1 source artifacts are reused byte-for-byte:

- `AUTHORING-RUBRIC.json`
- `PROFILE-SURFACE.json`
- `PROFILE-WRITER-TASK.md`
- `CUSTODY-SCHEMA.json`
- `LAUNCH-STATUS.json`
- `run_writer.py`
- `check_execution.py`
- `validate_setup.py`

The internal `rc1` schema labels in these reused apparatus bytes are intentionally retained. They identify the unchanged apparatus format, not the successor experiment number.

A dedicated successor validator must compare the immutable RC1 source commit to RC2 and prove that the two runtime files equal the RC1 bytes after only the exact service-version substitution above.

No claim is made in advance that the service version is behaviorally irrelevant. The experiment controls it explicitly.

## Runtime authority

Pinned RC2 writer runtime:

- destination: `http://127.0.0.1:11434/api/generate`
- service version: `0.35.1`
- model: `qwen3.5:9b`
- service-reported digest: `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`

All frozen request options and the exact five-file response schema remain unchanged from RC1.

If the live runtime no longer matches this authority before POST, stop `BLOCKED_AUTHORITY`; do not retarget the candidate.

## Boundary

CONTEXT-FREE REQUIRED.

The one allowed writer sees only the same four bootstrap source files and actual runtime facts constructed by the frozen launcher.

Do not expose predecessor PR narrative, predecessor outputs, cases, oracle, metamorphic material, reviewer calibration, weak systems, private PR #124 material, project/conversation memory, or target/evaluator results to the writer.

Frozen `run_writer.py` remains the only authorized launcher.

## Attempt budget

- profile writer: 1
- external custody verification/check: 1
- semantic calibration: 0
- target generation: 0
- deterministic weak generators: 0
- decisive review: 0
- tally: 0

The attempt is consumed only when the frozen launcher sends the writer POST. There is no rerun, replacement model, parameter change, repair, or adjudication inside RC2.

## Acceptance / stopping

Use the unchanged RC1 terminal logic:

- `SUPPORTED_FOR_GENERATION_EXECUTION`
- `BLOCKED_PROFILE_CONFIGURATION`
- `BLOCKED_CUSTODY_VERIFICATION`
- `BLOCKED_AUTHORITY`
- `CONTAMINATED`
- `INCONCLUSIVE`

Stop on the first terminal state.

Even if RC2 is supported, do not run semantic calibration or any generation case. Generation capability remains UNKNOWN.

## Required record

Preserve exact setup identities, successor-comparison evidence, runtime preflight, native request/response if the POST occurs, extracted profile hashes, custody receipt/check, attempt consumption, failures/deviations, bounded disposition, explicit non-claims, and exact next authorized boundary.

No merge, release, production promotion, private population construction, corpus access, retrieval, passage review, or generation execution is authorized.
