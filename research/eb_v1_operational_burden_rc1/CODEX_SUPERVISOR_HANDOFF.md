# Codex Supervisor Handoff — EB V1 Operational Burden RC1

You are the **mechanical supervisor** for a preregistered Evidence Bundler research experiment.

Repository: `camerontjs-dot/evidence-bundler`

Required branch:

`research/eb-v1-operational-burden-rc1-20260913`

Draft research PR: **#74**

## Your role

You may use your existing informed Codex context for repository synchronization, worktree management, shell execution, validation, git commits, and pushes.

You are **not** a semantic reviewer. Do not classify passages yourself, alter reviewer judgments, resolve disagreements manually, infer expected outcomes, or rewrite the frozen scientific apparatus after reviewer exposure.

All semantic judgments are produced by fresh ephemeral child contexts launched by the frozen runner.

## Before execution

1. Inspect `git status`.
2. `git fetch origin`.
3. Treat GitHub as authoritative.
4. Do not overwrite, reset, stash, or otherwise disturb unrelated local work.
5. If the existing Evidence Bundler checkout is dirty, on unrelated active work, or otherwise unsafe to use, create a **separate temporary Git worktree** from the current remote RC1 branch and execute there.
6. The execution worktree must be clean and its `HEAD` must exactly equal `origin/research/eb-v1-operational-burden-rc1-20260913` before running anything.

Read these supervisor-facing files for procedure and boundaries:

- `research/eb_v1_operational_burden_rc1/PREREGISTRATION.md`
- `research/eb_v1_operational_burden_rc1/CONTEXT_FREE_EXECUTION.md`
- this handoff

Do not perform your own semantic inspection or adjudication of the blind packet contents.

## Execute exactly one command

From the repository root, run:

```bash
bash research/eb_v1_operational_burden_rc1/run_rc1_with_codex.sh
```

Do not replace the runner with an improvised workflow.

The runner is responsible for:

1. verifying the frozen apparatus hashes;
2. launching **six fresh Stage 1 reference reviewers** as isolated ephemeral Codex child contexts;
3. validating their packet identity, relation sets, labels, independence assertions, reviewer IDs, and trace aperture;
4. consolidating the Stage 1 references mechanically;
5. committing and pushing the frozen Stage 1 reference before Stage 2 begins;
6. launching **four new Stage 2 test reviewers** as separate isolated ephemeral Codex child contexts;
7. validating them under the same fail-closed rules;
8. running the deterministic RC1 evaluator;
9. writing the terminal result and concise results record;
10. committing and pushing the terminal research record.

## Do not

Do not:

- edit a child reviewer output;
- rerun a child merely because you dislike its judgment;
- manually adjudicate `UNRESOLVED` or reviewer disagreement;
- expose Stage 1 references to Stage 2 reviewers;
- alter packets, rubrics, mappings, thresholds, coverage guards, consolidator, evaluator, or preregistration after semantic execution begins;
- rerun retrieval;
- test K=8 or another K;
- add a selector, reranker, query rewrite, semantic retriever, or new retrieval family;
- change a production default;
- merge PR #74;
- release or tag anything;
- claim Evidence Bundler V1 promotion.

## Failure handling

Fail closed.

If any infrastructure, hash, child execution, validation, trace-aperture, git, or push step fails:

- stop;
- preserve any already-created outputs/workspaces and the exact error;
- do not patch scientific logic after reviewer exposure;
- do not continue to the next stage unless the frozen procedure explicitly permits it;
- report the exact failure and the last successfully pushed commit.

A purely mechanical pre-exposure environment issue may be diagnosed, but do not change scientific meaning without a new explicit operator decision.

## Final report

If the runner completes successfully, report only:

- `REFERENCE_FREEZE_COMMIT=<sha>`
- `FINAL_COMMIT=<sha>`
- `PRIMARY_DISPOSITION=<SUPPORTED FOR PROMOTION | FALSIFIED | INCONCLUSIVE>`
- `PRIMARY_CONCLUSION=<value printed by runner>`
- `ALL_TEN_ISOLATED_REVIEWERS_COMPLETED_SUCCESSFULLY=yes`

If it does not complete, report:

- `RC1_EXECUTION_FAILED`
- the exact failing step/error;
- `LAST_PUSHED_COMMIT=<sha or none>`

Then stop.
