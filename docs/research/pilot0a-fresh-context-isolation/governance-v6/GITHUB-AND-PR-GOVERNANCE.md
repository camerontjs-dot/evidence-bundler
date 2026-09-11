# GitHub and Pull Request Governance

## Why this exists

The goal is not to make a solo project imitate a large company. The goal is to create visible constraints that make unsupported claims, accidental semantic changes, and retrospective story-editing harder.

The strongest signals are **costly to fake because they expose the project to possible failure**.

## PR classes

### A. Research PR

Use when the branch is testing a substantive hypothesis or architecture.

**Default state:** Draft.

Required contents:

- claim under review;
- preregistered or pre-run evidence requirements where practical;
- falsification criteria;
- controlled variables / invariants;
- exact repository SHAs and fixture identities where cross-repo;
- observed results, including failures;
- deviations;
- explicit unknowns;
- production impact;
- next discriminating test;
- final disposition when enough evidence exists.

A green research PR means only that the encoded assertions passed.

### B. Research Infrastructure PR

Use for machinery that enables experiments but does not itself establish the hypothesis:

- frozen fixtures;
- validators;
- harness improvements;
- deterministic test utilities;
- research-only workflows;
- artifact readers/writers with no production path.

These may merge to `main` when:

- production semantics are unchanged and this is demonstrated;
- the infrastructure has its own deterministic tests;
- the PR states exactly what conclusions the tooling **cannot** establish;
- no unresolved apparatus deviation changes the intended meaning.

Do not cite “the infrastructure merged” as evidence that the research hypothesis is supported.

### C. Promotion / Production PR

Use only after research or existing production evidence justifies a change.

Required contents:

- exact claim being promoted;
- evidence basis and linked research PRs/results;
- what is not established;
- minimal change surface;
- compatibility and migration consequences;
- rollback path where relevant;
- required CI and cross-repo conformance;
- release/version decision with evidence basis.

Promotion PRs should normally be much smaller than the research history that justified them.

### D. Maintenance / Documentation PR

Use for low-risk changes that do not alter the system's semantic or operational behavior.

Examples: typo fixes, presentation assets, dependency housekeeping, non-semantic documentation.

Still run appropriate leak/security checks and ordinary CI.

### E. Hotfix PR

Use only for an actual production defect requiring prompt correction.

A hotfix may compress the research loop, but must include:

- observed failure;
- minimal correction;
- regression test reproducing the failure;
- rollback note;
- follow-up issue when root-cause analysis remains incomplete.

## Branch naming

Recommended patterns:

- `research/<question-or-experiment>`
- `research-infra/<fixture-or-harness>`
- `promotion/<bounded-change>`
- `fix/<defect>`
- `docs/<topic>`
- `chore/<maintenance>`

Branch names are navigation aids, not evidence.

## Research PR lifecycle

```text
question
  ↓
preregister / define falsifier
  ↓
open Draft PR early
  ↓
freeze fixture + pin SHAs
  ↓
execute controls and experiment
  ↓
record failures + deviations
  ↓
epistemic compression
  ↓
SUPPORTED FOR PROMOTION / FALSIFIED / INCONCLUSIVE / SUPERSEDED
  ↓
reconcile terminal state across primary result + PR + canonical indexes
  ↓
close/retain research record
  ↓
new minimal promotion PR if supported
```

## Allowed research dispositions

Use exactly one primary disposition when the question reaches a stopping point:

- **SUPPORTED FOR PROMOTION**
- **FALSIFIED**
- **INCONCLUSIVE**
- **SUPERSEDED**

`PASSED` is a test result, not a research disposition.

### Terminal-state reconciliation

A research task is not governance-complete merely because the decisive run finished or a disposition appears in one document. Before the thread is treated as complete, reconcile the terminal state across the surfaces that future work will actually inspect.

At minimum, when applicable:

- freeze the result/disposition in the primary results artifact or PR record;
- make the PR body, labels, draft/open/closed posture, and explicit non-claims agree with that disposition;
- update canonical routing/index issues affected by the result;
- state which blockers were cleared, which remain, and what successor experiment or promotion is actually authorized;
- preserve failed/deviating runs and do not rewrite them into the terminal summary;
- close or retain the research PR according to its evidentiary value rather than using merge state as a proxy for success.

Primary artifacts still outrank index summaries. Temporary index lag is therefore governance drift, not a reason to reinterpret the experiment. Reconcile that drift before declaring the research task complete when the task has authority to do so.

A green workflow is never, by itself, a terminal research disposition.

## Promotion rules

Never promote because:

- CI is green;
- an agent says the design is good;
- the implementation is elegant;
- the branch has accumulated lots of work;
- changing course would be inconvenient;
- a version number was already discussed.

Promote only the narrow capability demonstrated by evidence.

## Stacked PRs

Stack research PRs only when dependency is real and visible.

For each stacked PR:

- state its non-`main` base explicitly;
- state which parent result it depends on;
- avoid presenting the stacked child as independent evidence;
- when the parent is superseded, rebase/rebuild or mark the child accordingly;
- split the eventual production change into minimal PRs against the real production base.

## Merge method

Recommended defaults:

- **Promotion / maintenance / research-infrastructure:** squash merge when the PR represents one coherent logical change.
- **Research experiment:** often leave as a preserved PR and close after disposition. If its artifacts must become durable repository history, merge only the intended research record/infrastructure, not an accidental experimental production path.

Do not rely on commit-count aesthetics as an assurance signal.

## Review policy for a solo-maintainer project

Do not manufacture review theater.

Strong options include:

- automated deterministic gates;
- an independently implemented consumer;
- a reviewer agent isolated from implementation context;
- a second model with explicit contamination controls;
- a real external technical reviewer when available.

A self-approval checkbox is not independent review.

If a reviewer is not independent, say so.

## Costly-signal test

A process is a useful assurance signal when it is **harder for a weak or incorrect system to survive than for a strong one**. This is the relevant game-theoretic criterion.

High-value examples:

- preregistration removes the option to rewrite success criteria after seeing results;
- frozen fixtures prevent selective case replacement;
- metamorphic and mutation tests force the implementation to preserve invariants rather than memorize examples;
- independent consumers impose a real reproducibility burden on an underspecified contract;
- preserved failures reduce narrative flexibility;
- cross-repository conformance exposes interface assumptions that local tests can hide;
- narrow promotion PRs make it harder to smuggle untested architecture into a supported change.

Low-value examples:

- mandatory self-approval;
- badges disconnected from required gates;
- complex branching rules that do not protect an actual failure mode;
- signed commits presented as proof of semantic correctness;
- extra paperwork whose answers are never checked.

Prefer **falsifiability-producing friction** over ceremonial friction.

## Costly-signal ladder

From weaker to stronger:

1. clear written claim;
2. deterministic unit/integration tests;
3. public CI receipts on pinned code;
4. preregistered falsifiers;
5. frozen fixtures and negative controls;
6. mutation/metamorphic/adversarial tests;
7. preserved failed runs and deviations;
8. independent implementation from specification;
9. cross-repository producer/contract/consumer conformance;
10. external independent review or real downstream use;
11. narrow production promotion with rollback and post-release monitoring.

The point is exposure to disconfirmation, not pageantry.

## Main-branch protection target

Where repository/plan capabilities permit, protect `main` using GitHub rulesets or classic branch protection with the useful subset of:

- require a pull request before merging;
- require the repository's meaningful status checks;
- require conversation resolution;
- block force pushes;
- block branch deletion;
- restrict direct pushes where practical.

Consider signed commits only as an identity/supply-chain measure, not as evidence of correctness.

Do not require a human approval that nobody independent can actually provide. Add required reviewers when a real reviewer/collaborator exists.

A merge queue is unnecessary unless concurrent merge traffic creates a real integration problem.

## Release/version procedure

For a promoted contract or behavior change:

1. link the supporting evidence;
2. state the compatibility class;
3. update schemas/specs/validators together where required;
4. run consumer conformance;
5. tag/release the exact promoted commit if it represents a public version;
6. preserve migration/adapter notes;
7. do not rewrite the release tag after publication.

## Labels worth standardizing

Suggested minimal taxonomy:

- `research`
- `research-infrastructure`
- `promotion`
- `experiment:preregistered`
- `disposition:supported`
- `disposition:falsified`
- `disposition:inconclusive`
- `disposition:superseded`
- `needs-cross-repo-conformance`
- `breaking-change`
- `apparatus-deviation`
- `blocked`

Use labels for discoverability, never as a substitute for the written evidence record.

## GitHub reference points

Current GitHub documentation used when preparing these recommendations:

- Rulesets and available rules: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
- Protected branches: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- Pull request reviews: https://docs.github.com/en/pull-requests/reference/pull-request-reviews
- Status checks: https://docs.github.com/en/pull-requests/reference/status-checks

