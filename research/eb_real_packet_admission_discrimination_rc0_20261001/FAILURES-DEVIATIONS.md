# Failures and deviations

## 2026-10-01 — local worker launch refused before decisive execution

A Conduit `conduit_create_task` request for a fresh Codex worker in the `evidence-bundler` project was refused with:

`global_live_task_limit_reached`

The Conduit response stated that global live-task capacity was full and that no runtime was started, changed, or ended.

Classification:

- execution-environment blocker;
- pre-freeze / pre-review;
- no private packet, retained candidate, reviewer label, CAL output, or Decision output was exposed by this failed launch;
- no scientific disposition follows from it.

No unrelated live task was closed to make room. The public preregistration and research-only apparatus were prepared through GitHub instead.

If a later local slot becomes available, the decisive run may proceed under the already-frozen preregistration. The failed launch remains part of the record.
