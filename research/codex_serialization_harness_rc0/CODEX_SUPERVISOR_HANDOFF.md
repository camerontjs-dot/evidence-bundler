# Codex Supervisor Handoff — Serialization Harness RC0

Role: mechanical execution supervisor only.

Repository:

`camerontjs-dot/evidence-bundler`

Branch:

`research-infra/codex-serialization-harness-rc0-20260914`

This harness is independent of paused RC1. Do not modify PR #74 or any RC1 worktree/output.

## Start

1. `git fetch origin`
2. Use a new clean temporary worktree exactly at the current remote harness branch.
3. Do not reset, stash, clean, delete, or alter any other worktree.
4. Read `research/codex_serialization_harness_rc0/PREREGISTRATION.md`.
5. Run the deterministic no-Codex control first:

   `python3 research/codex_serialization_harness_rc0/run_harness.py --self-test-only`

6. If that passes, run exactly:

   `python3 research/codex_serialization_harness_rc0/run_harness.py`

Do not edit the harness between self-test and execution.

## Execution boundary

This is synthetic harness qualification only.

Do not:

- inspect or modify paused RC1 reviewer outputs;
- rerun any RC1 reviewer;
- perform semantic review;
- change the 96 synthetic IDs, bucket mapping, run count, schema, validator, or qualification rule;
- retry an individual failed synthetic child;
- merge, release, tag, promote, or resume RC1.

## Freeze the execution record

The runner prints `EXECUTION_DIR=<path>`.

After it stops, whether `QUALIFIED` or not:

1. inspect only the generated `HARNESS_RESULT.json` and file inventory mechanically;
2. do not repair generated child output;
3. `git add` only the generated execution directory;
4. commit with:
   `research: freeze Codex serialization harness RC0 execution`
5. push to the same harness branch.

Do not modify the preregistered apparatus after execution begins.

## Report

Return:

- `HARNESS_EXECUTION_COMMIT=<sha>`
- `HARNESS_STATUS=<value>`
- `EXECUTION_ID=<value>`
- `COMPLETED_RUNS=<n>`
- `CODEX_VERSION=<value>`
- `SELFTEST_PASS=<true|false>`
- `RC1_RESUME_AUTHORIZED=no`

If status is not `QUALIFIED`, also return:

- `FAILING_STEP=<value>`
- `ERROR=<value>`

Stop there.
