# Evidence Bundler V1 RC1 — Codex Supervisor Handoff V3

Continue the existing RC1 execution on branch:

`research/eb-v1-operational-burden-rc1-20260913`

The first two launch attempts stopped before any semantic reviewer was launched. Both failures are preserved as pre-exposure apparatus deviations.

## Required start state

1. `git fetch origin`
2. Use a clean checkout or temporary worktree exactly matching current `origin/research/eb-v1-operational-burden-rc1-20260913`.
3. Do not reset, stash, overwrite, or disturb unrelated local work.
4. Do not modify the apparatus before execution.

## Prescribed command

Run exactly:

`bash research/eb_v1_operational_burden_rc1/run_rc1_with_codex_v3.sh`

Do not run the V1 or V2 launchers directly.

## Scope

The V3 wrapper is an apparatus-only pre-exposure correction. It verifies the frozen Git blobs, recomputes packet canonical identity using the same function used by the reviewer validator, validates packet relation sets against the frozen supervisor mapping, and deterministically substitutes only the stale cobalt canonical-hash literal in a temporary rubric copy.

The semantic task, packets, labels, reference construction, test design, evaluator, thresholds, arm mapping, and stop boundary are unchanged.

Do not perform semantic review yourself. Do not inspect or alter child judgments. Do not manually repair a failed child output.

## Reporting

If execution succeeds, report only:

- `REFERENCE_FREEZE_COMMIT=<sha>`
- `FINAL_COMMIT=<sha>`
- `PRIMARY_DISPOSITION=<value>`
- `PRIMARY_CONCLUSION=<value>`
- `ALL_TEN_ISOLATED_REVIEWERS_COMPLETED_SUCCESSFULLY=yes`

If anything fails, stop rather than improvising and report:

- `RC1_EXECUTION_FAILED`
- `FAILING_STEP=<step>`
- `ERROR=<exact error>`
- `LAST_PUSHED_COMMIT=<sha or none>`

No merge, release, tag, production-default mutation, K=8 test, selector experiment, semantic retriever change, query rewrite, or V1 promotion is authorized.
