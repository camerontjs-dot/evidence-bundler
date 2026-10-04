# Root-generation prerequisite RC3 apparatus qualification

## Objective

Determine whether a corrected prerequisite checker/launcher successor preserves the RC2 scientific and transport boundary while replacing only the falsified failure-classification mechanism.

No writer call is authorized by this experiment.

## Authority

Pinned predecessors:

- RC2 PR #127 terminal head: `534f6801998d96c72783fa1895d6a404dec7ec1a`
- RC2 frozen source: `e850d812036d0eca2ab1c79185bf871a9636684a`
- RC2 source tree: `2a115eca48d0ec2e4896b98280d2d4b1fcb4439d`
- RC2 terminal checker witness: `FAIL / 'output'`
- failure-classifier PR #128 evidence head: `9da73dc3a9d4d413a55dce6ce48f9774d0a9ec07`
- classifier disposition: `SUPPORTED_FOR_APPARATUS_SUCCESSOR`

GitHub and immutable artifacts remain authoritative.

## Frozen invariants from RC2

Reuse byte-for-byte:

- `AUTHORING-RUBRIC.json`
- `PROFILE-SURFACE.json`
- `PROFILE-WRITER-TASK.md`
- `BOOTSTRAP-MANIFEST.json`
- `CUSTODY-SCHEMA.json`
- `WRITER-TRANSPORT.json`
- `LAUNCH-STATUS.json`
- `validate_setup.py`

Only the diagnostic integration may change:

- `check_execution.py`
- `run_writer.py`

Plus research-infrastructure qualification files and workflow.

## Required structured policy

Checker failure categories:

- `PROFILE_CONFIGURATION -> BLOCKED_PROFILE_CONFIGURATION`
- `CUSTODY_VERIFICATION -> BLOCKED_CUSTODY_VERIFICATION`
- `CONTAMINATION -> CONTAMINATED`
- `APPARATUS_ERROR -> INCONCLUSIVE`

Unexpected exceptions must map to `APPARATUS_ERROR / APPARATUS_UNEXPECTED_EXCEPTION / INCONCLUSIVE`.

The launcher must consume the structured checker disposition directly. It must not classify by substring matching.

## Offline integration pressure

Use synthetic fixtures only. Cover at least:

- valid baseline PASS;
- missing `calibration.output`;
- missing `decisive.output`;
- wrong decision enum;
- malformed review JSON;
- primary/evaluator config drift;
- missing uncertainty token;
- missing profile file;
- request/response hash mismatch;
- incomplete/truncated response;
- runtime digest mismatch;
- profile hash mismatch;
- forbidden source;
- raw unexpected `KeyError("output")`.

For each checker FAIL, verify the launcher integration preserves the exact structured disposition and code.

Weak controls:
- RC2 message-substring classifier;
- everything-custody.

## Acceptance

Support requires:

1. exact RC2 invariants are byte-identical;
2. only checker/launcher diagnostic integration differs among executable predecessor apparatus;
3. setup validation passes unchanged;
4. integrated frozen mutation matrix passes exactly;
5. two offline runs are byte-identical;
6. raw unexpected exceptions become `INCONCLUSIVE`, never custody;
7. RC2-style heuristic and everything-custody controls fail the intended boundaries;
8. no network/model call occurs;
9. dedicated Python 3.11/3.12 CI passes;
10. production and predecessor bytes remain unchanged.

## Terminal dispositions

- `SUPPORTED_FOR_PREREQUISITE_EXECUTION_CANDIDATE`
- `FALSIFIED`
- `INCONCLUSIVE`
- `BLOCKED`

A supported result authorizes only construction/freeze of a separate context-free execution candidate. It does not itself authorize the writer POST.

## Boundary

No model/API/network generation, no RC2 rerun, no semantic calibration, no generation cases, no private PR #124 material, no production changes, merge, release or promotion.
