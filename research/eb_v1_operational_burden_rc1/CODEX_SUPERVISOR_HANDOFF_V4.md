# Evidence Bundler V1 RC1 — Codex Supervisor Handoff V4

Role: mechanical supervisor only.

This is a retry of the already-preregistered RC1 experiment. Three prior launch attempts stopped before semantic exposure and are preserved in Git history. Do not redesign the experiment.

## Required branch

`research/eb-v1-operational-burden-rc1-20260913`

GitHub is authoritative.

## Start conditions

1. `git fetch origin`
2. Use a clean checkout or temporary worktree exactly at the current remote branch head.
3. Do not reset, stash, overwrite, or disturb unrelated local work.
4. Do not modify any RC1 apparatus file before execution.

## Prescribed command

Run exactly:

`bash research/eb_v1_operational_burden_rc1/run_rc1_with_codex_v4.sh`

Do not run V1, V2, or V3 launchers directly.

## V4 scope

V4 keeps the V3 identity, packet, structure, relation-map, rubric-hash, isolation, reference, evaluator, and stop-boundary logic unchanged.

The only new correction is Bash portability for macOS system Bash. The launcher deterministically rewrites exactly two Bash-4-only uppercase expansions in the temporary generated runner, verifies none remain, and runs `bash -n` before any semantic child execution.

The V4 apparatus record is:

`research/eb_v1_operational_burden_rc1/APPARATUS_MANIFEST_V4.json`

The preserved portability deviation is:

`research/eb_v1_operational_burden_rc1/DEVIATION-PREEXPOSURE-BASH-PORTABILITY.md`

## Supervisor prohibitions

Do not:

- perform semantic review yourself;
- inspect or alter child judgments;
- manually repair a failed child output;
- alter packets, proposition text, passage text, relation IDs, rubrics, labels, arm mapping, reference rules, evaluator, coverage guard, directional rule, thresholds, or stop boundary;
- rerun retrieval;
- test another K;
- add a selector, reranker, semantic retriever, query rewrite, or threshold change;
- merge, release, tag, or promote V1.

If any V4 preflight, portability check, child execution, trace aperture validation, reviewer validation, Stage 1 freeze/push, Stage 2 execution, or evaluator step fails, stop rather than improvising.

## Success report

If execution completes, report only:

- `REFERENCE_FREEZE_COMMIT=<sha>`
- `FINAL_COMMIT=<sha>`
- `PRIMARY_DISPOSITION=<value>`
- `PRIMARY_CONCLUSION=<value>`
- `ALL_TEN_ISOLATED_REVIEWERS_COMPLETED_SUCCESSFULLY=yes`

## Failure report

If execution fails, report only:

- `RC1_EXECUTION_FAILED`
- `FAILING_STEP=<step>`
- `ERROR=<exact error>`
- `LAST_PUSHED_COMMIT=<sha or none>`

Then stop.
