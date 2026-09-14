# Codex Serialization Harness RC0 — Supervisor Handoff V2

This is a mechanical synthetic qualification only.

Evidence Bundler RC1 PR #74 remains paused and must not be touched.

## Preserved first attempt

Execution 01 is frozen at commit `54a6e05b10250842d97deb6c77cd5d23aa6fb42a` with execution ID `20260914T153828Z-dd52a2d5`.

It stopped because the harness validator incorrectly treated an ordinary Codex status `agent_message` as a second final result. See `DEVIATION-EXECUTION-01-TRACE-CLASSIFIER.md`.

Do not delete, rewrite, reuse, or count any Execution 01 child toward qualification.

## V2 corrected apparatus

The corrected validator permits ordinary non-result status messages but requires exactly one fully valid result-shaped agent message. The unique result must be the last agent message and must exactly match `--output-last-message`.

A second result-shaped message, malformed result-shaped message, result not last, forbidden command, duplicate JSON key, missing/extra ID, wrong label, or wrong reviewer identity remains a hard failure.

## Execution

Use a fresh clean temporary worktree at the current remote branch:

`research-infra/codex-serialization-harness-rc0-20260914`

Run first:

`python3 research/codex_serialization_harness_rc0/run_harness.py --self-test-only`

If it passes, run exactly:

`python3 research/codex_serialization_harness_rc0/run_harness.py`

Qualification still requires a complete fresh `12 / 12` run. Do not retry or replace an individual failed child.

Whatever terminal status occurs, preserve the new execution directory exactly, commit only that generated execution directory, push to the same harness branch, and stop.

Do not resume RC1, rerun any RC1 reviewer, consolidate references, run the RC1 evaluator, change retrieval/selection, merge, release, tag, or promote anything.

Return only the frozen harness execution fields requested by the operator.
