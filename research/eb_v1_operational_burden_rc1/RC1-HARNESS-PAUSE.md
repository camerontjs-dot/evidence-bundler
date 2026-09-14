# Evidence Bundler V1 RC1 — Harness / Infrastructure Pause

Status: **PAUSED — HARNESS / INFRASTRUCTURE**

This record is not a scientific disposition and does not authorize a retry, merge, release, tag, production-default change, or V1 promotion.

## Current scientific state

- No Stage 1 reference freeze exists.
- No Stage 2 test execution exists.
- No evaluator result exists.
- No RC1 scientific conclusion exists.
- V1 remains `NOT_READY`.

## Preserved attempts

1. V1 at `4f62c8f0e7b75f8869d189430787360f20996203`: pre-exposure raw-SHA identity failure.
2. V2 at `40142ae3897fe046475d9ee88d49e8a97285643a`: pre-exposure stale Cobalt canonical-hash failure.
3. V3 at `7b89496a8b51072197db6384bad4ef75b6ae0dad`: pre-exposure macOS Bash portability failure on `${phase^^}` / `${set_name^^}`.
4. V4 at `ebed6c29b31614687c0b3d7b0f05444482166abd`: V4 preflight passed and semantic child execution began. Three isolated reference reviewers completed and validated. Cobalt reference reviewer 1 produced a structurally invalid output containing duplicate `relation_id c9b5f817e8c9b400`; validation stopped the run before reference consolidation/freeze.

The V4 failure is the first RC1 attempt to reach semantic exposure. Therefore any later real-review execution requires an explicit post-exposure correction/deviation and a new supervisor handoff. The failed Cobalt-1 output must not be repaired, deduplicated, normalized, deleted, or selectively rerun.

## Preservation boundary

Do not reset, squash, delete, clean, or rewrite:

- this RC1 branch or its commits;
- the original dirty checkout;
- temporary Git worktrees used by the attempts;
- temporary child work directories that survived failure;
- V4 reference outputs, traces, warnings, or failed output;
- deviation records or prior launchers.

## Authorized next action

Mechanical harness audit only.

The audit may inspect file identity, relation-ID structure, output-path mechanics, trace/output equivalence, validator behavior, and synthetic non-semantic fixtures. It must not inspect or report semantic labels or passage judgments and must not launch another real reviewer.
