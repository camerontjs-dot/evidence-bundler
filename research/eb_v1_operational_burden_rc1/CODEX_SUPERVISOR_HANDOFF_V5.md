# Evidence Bundler V1 RC1 V5 — Codex Supervisor Handoff

This is the explicit post-exposure continuation of RC1 using the serialization mechanism qualified by PR #75.

Preserve all V1-V4 RC1 worktrees, outputs, traces, deviations, and failed artifacts exactly as they are. Do not clean, delete, reset, rewrite, deduplicate, repair, or reuse them.

V5 requires a completely fresh Stage-1 cohort. No V4 reviewer output counts toward V5.

## Setup

1. Run `git fetch origin`.
2. Create a new clean temporary worktree exactly at `origin/research/eb-v1-operational-burden-rc1-20260913`.
3. Confirm HEAD exactly matches the current remote branch.
4. Read `POSTEXPOSURE-CORRECTION-SERIALIZATION-V5.md` and `APPARATUS_MANIFEST_V5.json`.

## Execute

Run exactly:

`python3 research/eb_v1_operational_burden_rc1/run_rc1_with_codex_v5.py`

Do not run V1, V2, V3, or V4 launchers.

Do not manually alter child outputs, replace a failed reviewer, selectively retry one child, change packet/rubric/schema/reference/evaluator logic, or continue after a runner failure.

The V5 runner must use the qualified serialization validator from exact harness commit `1240671474b0f2cf638338bbcfd7ba0fc98e7322`, verify exact `codex-cli 0.154.0`, pass the V5 mechanical self-test, launch six entirely fresh Stage-1 reference reviewers, freeze/push the resulting reference before Stage 2, then launch four entirely fresh test reviewers and evaluate under the already-frozen RC1 decision rule.

## Stop boundary

Do not merge, release, tag, promote Evidence Bundler V1, change retrieval or retention defaults, test another K, introduce a selector/reranker, or begin another experiment.

If V5 succeeds, report only:

- `EXECUTION_ID=<value>`
- `REFERENCE_FREEZE_COMMIT=<sha>`
- `FINAL_COMMIT=<sha>`
- `PRIMARY_DISPOSITION=<value>`
- `PRIMARY_CONCLUSION=<value>`
- `ALL_TEN_FRESH_REVIEWERS_COMPLETED_SUCCESSFULLY=yes`

If V5 fails, stop and report only:

- `RC1_V5_EXECUTION_FAILED`
- `ERROR=<exact error>`
- `LAST_PUSHED_COMMIT=<sha or none>`
- `PRESERVED_FAILED_WORKSPACE=<path or none>`

Do not improvise a repair after semantic execution begins.
