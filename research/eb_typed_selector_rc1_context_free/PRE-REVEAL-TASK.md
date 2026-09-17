# EB Typed Selector RC1 — Context-Free Prereveal Authoring Task

## Role

Act as an independent benchmark/case author, adjudicator, evaluator designer, and qualification-apparatus reviewer for one bounded Evidence Bundler selector experiment.

This is a **context-free prereveal task**. The validity claim depends on not seeing the target selector implementation, its development results, prior answer-bearing selector cases, or expected target behavior before freeze.

Use only the information aperture authorized by `BOOTSTRAP-MANIFEST.json`.

Do not inspect adjacent PRs/issues/branches for orientation. Do not search broadly for the hidden selector. GitHub live state is authoritative only within the exact allowed surfaces.

## Objective

Create one fresh decisive cohort that can answer, after reveal:

> When first-stage Evidence Bundler retrieval is held fixed at depth 10 and every arm may retain at most 3 candidates, does the frozen candidate selector provide decision-useful selection improvement over the comparison arms without worsening unsafe/misleading retention or ordinary-case behavior?

You do **not** need to know how any post-freeze arm works.

## Exact starting authority

Repository: `camerontjs-dot/evidence-bundler`

Bootstrap branch:

`research-infra/eb-typed-selector-rc1-context-free-bootstrap-20260917`

Bootstrap base:

`c26fbd4bfc8ba5c2604a784af158594b59fcae37`

Frozen first-stage integration candidate:

`4e1f6fe00e7c350b28f52bfea14f1f8988847884`

Read `BOOTSTRAP-MANIFEST.json`, `FRESH-COHORT-CONTRACT.md`, `EVALUATION-CONTRACT.md`, `FREEZE-AND-REVEAL-PROTOCOL.md`, and `RETURN-HANDOFF-TEMPLATE.md` before authoring.

## Required work

1. Create a dedicated context-free authoring branch from the exact bootstrap branch.
2. Record every material pre-freeze source actually opened.
3. Author exactly 30 fresh lanes according to `FRESH-COHORT-CONTRACT.md`.
4. Author each claim profile from the claim alone before inspecting that lane's retrieval candidates.
5. Construct the lane corpus without access to the hidden target.
6. Run only the authorized frozen first-stage Evidence Bundler machinery to obtain the exact top-10 candidate pool.
7. Apply only the preregistered lane-eligibility and replacement rules. Do not tune a lane to any post-retrieval selector.
8. Freeze the complete input cohort and candidate pools.
9. Adjudicate and freeze the gold sidecar under the required schema.
10. Implement a target-agnostic evaluator that consumes arm outputs plus the sealed gold and computes exactly the metrics/gates in `EVALUATION-CONTRACT.md`.
11. Add deterministic evaluator controls and mutation/metamorphic controls that do not require the hidden target.
12. Commit a prereveal freeze receipt containing exact commit/tree/file hashes, source-access log, denylist compliance, case replacement/deviation log, evaluator identity, thresholds, and sealed-gold identity.
13. Stop at `READY_FOR_REVEAL`. Do not open the hidden target after freezing in this context-free authoring lane unless explicitly instructed by the normal project supervisor.

## Freshness requirements

Do not reuse, paraphrase, mutate, or reverse-engineer prior selector-development claims/passages. The new claims and corpora must be authored from scratch in this context-free lane.

Do not deliberately imitate a known prior case. The category taxonomy is intentionally broad. It is acceptable for a fresh case to instantiate a common retrieval/selection difficulty, but the concrete claim, entities, values, wording, passage structure, and evidence arrangement must be new.

## Gold separation

Gold must be frozen independently of target outputs.

The gold sidecar may be stored in the authoring repository/branch, but the return handoff must identify it as **SEALED UNTIL ARM OUTPUT FREEZE**. The normal execution lane is prohibited from opening it before arm outputs are frozen.

The authoring lane may know the gold because it created it. It must not implement or tune the hidden target.

## Stop rules

Stop and record `CONTAMINATED_PRE_FREEZE` if any forbidden selector/development/answer-bearing source is exposed before the prereveal freeze.

Stop and record `BLOCKED_APPARATUS` if the frozen first-stage machinery cannot produce stable candidate pools or if the evaluator cannot be made deterministic without changing the scientific question.

Do not repair the target, change first-stage retrieval behavior, alter K, or redefine success after target reveal.

## Completion condition

The task is complete only when GitHub contains an immutable prereveal freeze receipt and a compact handoff matching `RETURN-HANDOFF-TEMPLATE.md`.

The strongest valid terminal state from this lane is `READY_FOR_REVEAL`. It is **not** a selector research disposition.
