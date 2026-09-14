# Evidence Bundler V1 RC1 — Codex Supervisor Retry Handoff V2

Status: **PRE-EXPOSURE RETRY AUTHORIZED AFTER APPARATUS-IDENTITY CORRECTION**

Read first:

- `PREREGISTRATION.md`
- `DEVIATION-PREEXPOSURE-APPARATUS-IDENTITY.md`
- `APPARATUS_MANIFEST_V2.json`
- `CONTEXT_FREE_EXECUTION.md`

The first RC1 attempt stopped before any semantic reviewer launched because the V1 runner compared a transport-derived raw SHA-256 against normal Git-checkout packet bytes. The original runner and V1 manifest are preserved unchanged.

The scientific design has not changed.

## Supervisor boundary

You are the informed mechanical supervisor only.

Do not perform semantic classification yourself. Do not inspect, rewrite, repair, reconcile, or substitute semantic child judgments. Do not expose one arm, reviewer output, consolidated reference, prior result, profile identity, K, rank, score, or expected outcome to another semantic child.

All semantic judgments must come from the fresh ephemeral children launched by the frozen runner apparatus.

## Safe checkout

1. `git fetch origin`
2. Use branch `research/eb-v1-operational-burden-rc1-20260913`.
3. The execution checkout must exactly match the current remote branch head and be clean.
4. If the existing checkout is dirty or occupied, use a separate temporary worktree. Do not reset, stash, overwrite, or disturb unrelated local work.

## Prescribed retry

From the clean RC1 checkout run only:

```bash
bash research/eb_v1_operational_burden_rc1/run_rc1_with_codex_v2.sh
```

The V2 wrapper:

1. verifies frozen repository-file identity with Git blob hashes;
2. independently verifies both packet canonical JSON SHA-256 values;
3. preserves the original V1 runner unchanged;
4. executes a temporary copy of that original runner with only the defective V1 raw-SHA preflight removed;
5. leaves all downstream Stage 1 review, mechanical reference consolidation, reference freeze/push, Stage 2 review, evaluator, result freeze/push, and stop boundaries unchanged.

Do not manually bypass any other validation.

## Success report

If the runner completes successfully, report only:

- `REFERENCE_FREEZE_COMMIT=<sha>`
- `FINAL_COMMIT=<sha>`
- `PRIMARY_DISPOSITION=<value>`
- `PRIMARY_CONCLUSION=<value>`
- `ALL_TEN_ISOLATED_REVIEWERS_COMPLETED_SUCCESSFULLY=yes`

## Failure report

If anything fails, stop rather than repairing scientific procedure and report:

- `RC1_EXECUTION_FAILED`
- `FAILING_STEP=<step>`
- `ERROR=<exact error>`
- `LAST_PUSHED_COMMIT=<sha or none>`

## Stop boundary

Do not merge, release, tag, promote V1, change production defaults, test K=8, introduce another selector, or start another experiment.

Stop after reporting the RC1 execution result.
