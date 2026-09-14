# Codex Supervisor Handoff — Operational Review Burden RC0

This is an execution handoff for the already-preregistered Evidence Bundler V1 Operational Review Burden RC0 on Draft PR #73.

## Authority

Repository: `camerontjs-dot/evidence-bundler`

Branch:

`research/eb-v1-operational-burden-rc0-20260913`

The scientific apparatus and review packets are already frozen. Do not redesign the experiment, change packets/rubrics, rerun retrieval, inspect hidden gold, or infer the arm-to-profile mapping.

## Task

1. Fetch and check out the exact branch above.
2. Confirm `research/eb_v1_operational_burden_rc0/run_context_free_reviews_with_codex.sh` exists.
3. Run exactly:

```bash
bash research/eb_v1_operational_burden_rc0/run_context_free_reviews_with_codex.sh
```

4. Do not manually inspect, edit, normalize, regenerate, select among, or retry individual semantic reviewer outputs based on their content.
5. If the runner exits non-zero, stop and report the exact infrastructure/apparatus failure. Do not improvise a repair that changes the scientific review procedure.
6. If the runner exits zero, freeze all files created under:

`research/eb_v1_operational_burden_rc0/codex_review_outputs/`

7. Commit those generated review receipts to the same research branch with commit message:

`research: freeze Codex operational-burden reviews`

8. Push the branch.
9. Stop. Do not run `evaluate_operational_burden.py`, inspect hidden answer keys, interpret reviewer disagreements, update the PR disposition, merge, release, tag, or promote V1.

## Independence boundary

The supervisor context may know it is orchestrating a four-review experiment. Scientific reviewer independence is created by the runner itself: each child `codex exec --ephemeral` process receives a new temporary working directory containing only one neutral blind packet and its matching rubric, with user config/rules and Git-repository context disabled.

Do not replace those child executions with one shared Codex conversation.
