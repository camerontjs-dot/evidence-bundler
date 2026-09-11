# CAL Pipeline Project Context

**Use:** single stable attachment for the CAL Pipeline ChatGPT project.

This file intentionally excludes the dated governance audit and copy-ready templates. It contains the durable product intent, system boundaries, work conventions, PR governance, experimental protocol, agent rules, bootstrap procedure, and repository setup target.

---

# Product North Star

## One-sentence goal

Build a reproducible **evidence-to-decision assurance pipeline** that preserves what was observed, separates it from what was inferred, and lets a reviewer reconstruct why a claim or action was supported, blocked, held, or escalated.

## The product is not a truth machine

The system should not imply that it has established objective truth merely because a model, rule engine, or test returned a verdict.

Its strongest defensible claim is narrower:

> Given a defined evidence world, explicit policies, identified measurements, and preserved provenance, the system can produce an auditable epistemic assessment and carry that assessment into a decision process without silently changing authority or meaning.

Completeness, source legitimacy, applicability, and decision authority must be measured or supplied explicitly. They must never appear through convenient defaults.

## Product layers

### 1. Evidence construction

**Evidence Bundler** builds and preserves the evidence world presented downstream:

- source and representation identity;
- passage identity and provenance;
- retrieval/search history where relevant;
- nomination and admission/preparation state;
- mechanically observed or source-declared context facts;
- explicit unknowns and coverage facts.

It must not quietly decide proposition-specific support, validity, applicability, completeness, or verdict.

### 2. Typed evidence handoff

**Apparatus Contract B** is the immutable typed boundary from Evidence Bundler to CAL.

Its job is transport, validation, preservation, and semantic boundary enforcement. It should carry only the minimum state demonstrated necessary for the consumer.

### 3. Claim audit

**Claim Audit Lab (CAL)** owns proposition-specific epistemic work:

- claim ↔ passage semantic measurement;
- support/refutation relations;
- eligibility and semantic-validity assessments;
- temporal / authority / supplier applicability where explicitly evaluated;
- aperture/completeness assessment where justified;
- retained evidence contribution state;
- blockers, abstention, and decision basis;
- policy/config/model/validation identity for the work performed.

Non-deciding evidence remains evidence. A downstream view must not erase the underlying record.

### 4. Typed audit-result handoff

**Apparatus Contract C** should bind CAL's attributable work immutably to the Contract-B input.

It should preserve enough state for a downstream consumer to reconstruct what CAL measured, assessed, and concluded, without rewriting upstream evidence facts.

### 5. Decision assurance

**Decision Engine** owns decision-context policy:

- materiality;
- requirements;
- risk tolerance;
- options and trade-offs;
- escalation/hold/fail/pass routing;
- decision rationale and policy identity.

An epistemic conclusion is not operational authorization.

### 6. Execution and operator authority

**MainFrame / Conduit / local agents** coordinate work and execution. They do not acquire epistemic or operational authority merely because they can run tools or mutate state.

Human/operator authority remains explicit where the workflow requires it.

## The deeper product thesis

As AI makes code and analysis cheap, assurance must shift from trusting authorship to testing observable behavior and preserving evidence.

The pipeline therefore has two mutually reinforcing goals:

1. **Useful system:** make evidence-backed decisions more reconstructable and less dependent on hidden judgment.
2. **Assurance system:** demonstrate that AI-assisted implementation can be trusted only to the extent that its behavior survives falsifiable, reproducible checks.

## Success criteria

The project is succeeding when:

- an independent consumer can reproduce the intended contract semantics from the specification and frozen artifacts;
- missing critical state fails closed rather than becoming an invented default;
- failed, stale, contradicted, or non-deciding evidence remains traceable;
- a decision can be traced back through Contract C, CAL receipts, Contract B, and evidence provenance;
- changing a downstream policy does not mutate upstream facts;
- changing a purely upstream nomination heuristic does not silently alter semantic measurement unless the contract explicitly says it should;
- production changes can be linked to bounded experimental evidence;
- the system can say **unknown**, **inconclusive**, or **not checkable** without laundering those states into failure or success;
- a future reviewer can tell what was observed, inferred, hypothesized, and still unknown.

## Non-goals unless explicitly added

Do not silently expand the product claim to include:

- proof that the corpus is complete;
- proof that every source is legitimate or authoritative;
- universal factual truth;
- fully autonomous operational approval;
- automatic policy correctness;
- automatic regulatory applicability;
- guaranteed correctness of model-generated semantic judgments;
- automatic claim decomposition correctness;
- market demand merely because the technical problem is real.

Each of those would require its own evidence program.

## Design preference

Prefer architectures that produce **better evidence about their own correctness** over architectures that merely look elegant.

---

# System Boundaries

## Canonical chain

```text
Reality / external world
        ↓
Sources and records
        ↓
Evidence Bundler
        ↓
Contract B
        ↓
Claim Audit Lab
        ↓
Contract C
        ↓
Decision Engine / Gate
        ↓
Human or explicitly authorized system action
```

MainFrame/Conduit coordinates execution around this chain but should not silently inherit the authority of any layer.

## Ownership matrix

| Concern | Primary owner | Must not silently become |
|---|---|---|
| Source identity / representation | Evidence Bundler | CAL verdict |
| Passage provenance | Evidence Bundler / Contract B | support judgment |
| Retrieval nomination | Evidence Bundler | semantic relation |
| Admission / preparation history | Evidence Bundler | proposition validity |
| Typed evidence handoff | Contract B | downstream policy |
| Claim ↔ passage relation | CAL | upstream evidence fact |
| Eligibility / applicability assessment | CAL or explicit named assessor | source metadata shortcut |
| Completeness/aperture judgment | CAL or explicit policy layer | retrieval count |
| Epistemic result package | Contract C | operational authorization |
| Materiality / requirements / risk policy | Decision Engine | factual evidence |
| Operational mutation | human / authorized operator system | model inference |
| Task lifecycle / orchestration | MainFrame / Conduit | proof of completion or correctness |

## Boundary invariants

### Evidence facts are not proposition judgments

A publication date, source type, trust tier, retrieval score, or nomination role may be relevant to a later judgment, but none is automatically equivalent to that judgment.

Every semantic promotion should have a named policy or assessment receipt.

### Non-deciding does not mean erased

Evidence can remain in the retained ledger while becoming ineligible, stale, invalid, non-applicable, or non-deciding for a particular proposition or policy.

Derived views may filter. The underlying evidence record should remain reconstructable.

### Unknown is data

If required state is unavailable, record the absence explicitly. Do not manufacture a default merely to keep the pipeline moving.

### Epistemic conclusion is not authorization

CAL can conclude that evidence supports, refutes, mixes, or cannot resolve a proposition. That does not itself authorize a downstream operational action.

### Transport contracts do not own policy

Contract B and Contract C should preserve and validate state, not acquire decision authority because a field exists in the schema.

### Lifecycle observation is not completion proof

Queued work, delivered prompts, terminal output, quiet terminals, or closed captures are observations. Completion should be established by the relevant task-specific evidence or acceptance criterion.

## Versioning principle

Do not choose PATCH, MINOR, or MAJOR because one seems convenient.

Compatibility class should follow observed consumer behavior:

- **PATCH:** clarification or correction without interface/semantic expansion.
- **MINOR:** backward-compatible optional capability demonstrated to preserve existing consumers.
- **MAJOR:** required/incompatible shape or semantic change.

A schema can be syntactically backward compatible while being semantically breaking. Test both.

## Interface test rule

For any meaningful handoff change, test at least:

1. producer emission;
2. contract validation;
3. consumer behavior;
4. missing-state behavior;
5. mutation sensitivity for facts that should matter;
6. invariance for metadata that should not matter;
7. provenance round-trip;
8. backward-compatibility behavior where claimed.

Local unit tests alone do not establish a cross-repository interface.

---

# Working Conventions

## 1. Start from live state, not remembered state

Before material work:

- inspect the relevant repository's current branch/head;
- record exact SHAs used for cross-repository experiments;
- check open research and promotion PRs;
- inspect recent CI and known failed runs;
- identify whether a referenced artifact has advanced since it was last discussed.

Project attachments provide stable conventions. GitHub provides live status.

## 2. Separate four epistemic categories in substantive work

Use these labels when a conclusion matters:

- **Observed evidence:** directly measured, fetched, executed, or present in an artifact.
- **Inference:** conclusion supported by observations but not directly observed.
- **Hypothesis:** proposition deliberately awaiting a discriminating test.
- **Unknown:** unresolved because required evidence is absent or ambiguous.

Add **Falsified alternative** when an experiment actually rejects a candidate explanation.

Do not convert one category into another during summarization.

## 3. Prefer discriminating tests over architecture discussion

Before building a new mechanism, ask:

- What observation would tell us this is needed?
- What simpler explanation could produce the same symptom?
- What assumption is carrying the design?
- What is the smallest test that distinguishes the options?

A prototype whose result cannot change the decision is demonstration, not experiment.

When the claim is about an exact basis, reason, cause, or dependency, also ask whether more than one causal structure could explain the same result. Where feasible, distinguish single necessary causes, independently sufficient alternatives, jointly/co-sufficient causes, tied contributors, and merely present/non-deciding state with controlled interventions rather than one-run correlation. Do not invent a single winner when production state cannot justify one.

## 4. Freeze the object of evaluation

When testing an agent, model, contract, or pipeline:

- freeze fixtures before the decisive run;
- record model/config/tool versions where material;
- pin repository SHAs;
- separate test-harness changes from system-under-test changes;
- do not repair the evaluator after seeing an inconvenient result without recording a deviation.

## 5. Preserve negative evidence

Do not delete or rewrite:

- failed runs;
- counterexamples;
- unexpected outputs;
- superseded hypotheses;
- harness deviations;
- non-deciding evidence;
- incompatibilities found during promotion.

A clean-looking history is less valuable than an informative one.

## 6. Minimal changes after evidence

Once an experiment supports a bounded conclusion, implement only the smallest production change the evidence actually justifies.

New architecture discovered while implementing the promotion belongs in a new research question, not inside the promotion PR.

## 7. Keep research and production paths distinguishable

Use isolated research modules, fixtures, workflows, branches, or feature flags where practical.

A research artifact can live in the production repository without becoming production behavior, but the boundary must be explicit and testable.

## 8. Treat evaluators as systems under test

For important evaluators:

- add positive and negative controls;
- test mutation sensitivity;
- test invariance where expected;
- verify deterministic behavior when determinism is claimed;
- challenge labels or gold data with targeted adjudication;
- validate that the metric corresponds to the decision you care about.

Do not optimize against an evaluator until you have evidence it measures the intended thing.

For promotion-critical evaluator/benchmark decisions, validate **decision discrimination** separately from evaluator execution. Include at least one plausible intentionally weak or gaming implementation that should fail a meaningful gate for the intended reason. If both the target and weak control pass the promotion-critical gate, treat the broader capability claim as potentially `INCONCLUSIVE` even when the evaluator itself is functioning correctly.

## 9. Avoid self-confirming agent loops

An implementer saying its implementation is correct is weak evidence.

Prefer, in increasing strength:

1. deterministic automated checks;
2. adversarial/mutation/metamorphic tests;
3. separate review context;
4. independent implementation from specification;
5. external reviewer or real downstream consumer.

Independence must be described, not assumed.

## 10. Record deviations immediately

If the experimental apparatus changes after preregistration, create a deviation record containing:

- what changed;
- why;
- when the issue was discovered;
- whether the change could affect the scientific conclusion;
- which outputs/runs are invalidated;
- whether fixtures, expected results, thresholds, or policies changed.

A corrected experiment is valid when the correction is transparent and does not quietly move the goalposts.

## 11. Keep machine-local details out of public artifacts

Before public commits, check for:

- secrets and tokens;
- `.env` files;
- private source material;
- local absolute paths;
- personal identifiers;
- private URLs or attachments;
- generated caches and large irrelevant artifacts.

## 12. Make status legible

Every material research branch/PR should make it possible to answer quickly:

- What claim is under review?
- What evidence exists?
- What failed?
- What remains unknown?
- What is the current disposition?
- What is the next discriminating test?
- Does this change production behavior?

## 13. Completion standard

A task is complete only when its acceptance condition is observed.

Code written, prompt delivered, tests started, terminal output observed, or green CI are not substitutes for the actual acceptance criterion.

When a material research task owns its terminal governance handoff, completion also includes reconciling the primary result with the affected PR metadata and canonical GitHub routing/index surfaces. Primary evidence still outranks those summaries, but stale terminal metadata should not be left for the next thread to reinterpret.

---

# GitHub and PR Governance

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

A research task is not governance-complete merely because the decisive run finished or a disposition appears in one document. When applicable, reconcile the terminal state across the primary result, PR body/labels/open-draft-closed posture, canonical routing/index issues, and blocker/successor authorization before declaring the thread complete.

Primary artifacts still outrank summaries. Temporary index lag is governance drift, not a different scientific result. Preserve the primary evidence and correct the lag rather than blending the two states.

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

---

# Experiment and Evidence Protocol

## Objective

Turn architectural questions into experiments whose outcomes can actually change what the project believes or builds.

## Step 1: State the decision

Write the decision the experiment informs.

Example:

> Decide whether Contract B requires an optional factual-context extension, a breaking revision, or no canonical change.

An experiment without a downstream decision tends to become decorative testing.

## Step 2: State the claim under review

Use a narrow falsifiable proposition.

Good:

> A minimal V1 factual-context handoff contains enough evidence-world state for CAL to construct its pre-assessment view without invented defaults.

Weak:

> Contract B V1 is better.

## Step 3: Separate current evidence from hypothesis

Record:

- observations already established;
- inferences drawn from them;
- the remaining hypothesis;
- alternative explanations;
- unknowns.

This prevents prior belief from leaking into the experimental conclusion.

## Step 4: Define acceptance and falsification before the decisive run

Specify:

- observations required for support;
- observations that falsify or materially weaken the claim;
- ambiguous results that produce `INCONCLUSIVE`;
- which variables must remain fixed.

A test that cannot fail the idea is not an epistemic gate.

## Step 5: Freeze the apparatus

Record exact identities for material inputs:

- repository SHAs;
- fixture bytes/hashes;
- schemas/spec versions;
- model and tokenizer identifiers where material;
- thresholds;
- prompts if an LLM is part of the evaluator;
- random seeds where relevant;
- environment/tool versions where they can affect results.

## Step 6: Add controls

Prefer several control types:

### Positive control

A case expected to succeed if the apparatus is functioning.

### Negative control

A case expected to fail or abstain.

### Mutation control

Change one factor that **should** matter and verify the result changes appropriately.

### Invariance / metamorphic control

Change one factor that **should not** matter and verify the relevant output remains invariant.

### Missing-state control

Remove required information and confirm the system fails explicitly rather than inventing a default.

### Contamination control

When testing independence, prevent the reproducer from reading the implementation under evaluation.

## Step 7: Execute without goalpost movement

During execution:

- preserve first-run failures;
- do not modify expected answers because the observed output looks plausible;
- separate harness bugs from scientific failures;
- document every material apparatus change.

## Step 8: Validate the evaluator

Before trusting surprising or important results, test whether the measurement system itself could be wrong.

Questions:

- Could the metric miss the failure we care about?
- Could the gold label be wrong?
- Is the parser or adapter changing semantics?
- Is the test correlated with implementation details rather than the intended property?
- Would an adversarial implementation pass without satisfying the real requirement?
- Would a plausible intentionally weak implementation pass the promotion-critical gate?
- If a weak control fails, is it failing for the intended capability boundary rather than an incidental parser/shape/environment defect?

Evaluator correctness and decision discrimination are different properties. If the target system and a deliberately weak control both clear the promotion-critical gate, do not treat the target pass as broad capability support merely because the evaluator executed correctly. The correct result may be `INCONCLUSIVE` for that broader decision.

## Step 9: Epistemic compression

After execution, produce five sections:

### Observed evidence

Only direct measurements and artifact facts.

### Inference

What the observations support.

### Remaining hypotheses

Plausible explanations or architectural choices still awaiting evidence.

### Unresolved unknowns

Questions the experiment did not answer.

### Falsified alternatives

Ideas actually rejected by the evidence.

Then assign a research disposition.

## Step 10: Promotion decision

If **SUPPORTED FOR PROMOTION**, ask:

> What is the smallest production change that becomes justified if these observations are true?

Do not promote adjacent conveniences.

## Experimental evidence hierarchy

Different tests support different claims:

| Evidence | Strongly supports | Does not automatically establish |
|---|---|---|
| Unit tests | local function behavior | system architecture correctness |
| Integration tests | component interaction | real downstream compatibility |
| CI | reproducibility in that workflow | validity of assertions |
| Metamorphic tests | invariance/sensitivity property | completeness of test space |
| Fuzz/property tests | behavior over broad generated space | semantic correctness of oracle |
| Independent consumer | specification reproducibility | universal interoperability |
| Cross-repo frozen fixture | concrete seam behavior | all future cases |
| External review | independent scrutiny | correctness by authority |
| Production observation | real-use behavior | causal explanation without controls |

## When code reading matters

Behavioral verification can carry much of the assurance burden, especially at scale, but tests cannot establish properties they do not measure.

Human or agent code inspection remains useful for:

- identifying hidden state or untested side effects;
- security-sensitive logic;
- evaluator/oracle review;
- concurrency and resource-leak risks;
- understanding why a failure occurred;
- generating new adversarial tests.

The preferred loop is not **read or test**. It is:

> inspect enough to create good falsifiers, then let reproducible behavior carry the claim.

## Publication / costly-signal standard

A public experimental claim should ideally link to:

- preregistration/brief;
- exact code SHA;
- frozen fixture identity;
- CI run(s);
- failed run(s) and deviations;
- result document;
- independent reproduction where claimed;
- bounded conclusion and explicit non-claims.

This makes the claim inspectable by someone who does not trust the author.

---

# Agent Work Protocol

## Purpose

Use coding/research agents aggressively without allowing speed to blur experiment boundaries, repository state, or epistemic authority.

## Default launch context

When project-wide hooks and conventions are needed, start work from the MainFrame root unless a task explicitly benefits from stronger repository isolation.

Before making changes, the working agent should identify:

- target repository;
- base branch and SHA;
- intended branch;
- task class: research, research infrastructure, promotion, maintenance, or hotfix;
- acceptance criteria;
- whether cross-repository state must be pinned.


## Context-free project routing

The normal CAL Pipeline project is the default context for continuity, live-state synthesis, governance, ordinary implementation, and evidence-backed promotion work.

Use the separate **context-free project** when information isolation is part of the validity claim, including clean-room or fresh-context executions, independent evaluator/consumer implementations, hidden-gold or sealed-candidate work, and successor runs whose predecessors were invalidated by context contamination.

A new project/thread is not sufficient by itself. Every context-free task must define a mechanically bounded information aperture: exact allowed inputs, forbidden inputs, freeze point, post-freeze reveal rule, contamination stop rule, and receipts. Do not copy the surrounding project conversation into the isolated run.

When an experiment already has a frozen authority/bootstrap manifest, that manifest controls the run. Do not inject new project files or narrative merely because they are now durable conventions unless the manifest explicitly permits them.

The main project should explicitly mark routed tasks **CONTEXT-FREE REQUIRED** or **CONTEXT-FREE PREFERRED** and provide the smallest safe launch packet. After completion, return only the durable execution handoff needed for portfolio synthesis.

See `CONTEXT-FREE-EXECUTION-PROTOCOL.md` for the full routing and contamination rules.

## Agent role separation

Use explicit roles when independence matters.

### Implementer

Can inspect relevant code and build the candidate implementation.

### Reviewer

Attempts to find defects, hidden assumptions, missing tests, and semantic boundary violations.

### Reproducer / Consumer B

Implements from the specification and frozen artifacts without consulting Consumer A implementation logic when independence is the variable under test.

### Supervisor

Compares claims against receipts and decides whether evidence supports disposition or promotion.

Do not call two agents independent merely because they ran in separate terminals. Independence depends on information boundaries.

## Contamination rules

For an independent-consumer experiment, the reproducer may read only the allowed specification/artifacts defined in the preregistration.

Record:

- model/agent used;
- context supplied;
- repositories/files explicitly forbidden;
- whether prior thread memory could contain implementation details;
- deviations from the isolation boundary.

If contamination cannot be ruled out, downgrade the claim from **independent reproduction** to **separate implementation/review**.

## Prompting rule

Do not give an experimental implementer the desired output bytes or implementation strategy unless that information belongs in the public specification being tested.

Otherwise the test measures instruction following, not interface reproducibility.

## “Fix until green” rule

Avoid unrestricted `fix until tests pass` loops when the tests are the scientific evaluator.

Safer pattern:

1. freeze tests/fixtures;
2. let the agent implement;
3. run the frozen evaluator;
4. if it fails, record the failure;
5. decide whether the implementation or apparatus was wrong;
6. document any apparatus change before another decisive run.

For ordinary production maintenance, iterative repair is fine.

## Agent-generated tests

Tests written by the same agent as the implementation are useful but weakly independent.

For important properties, add at least one of:

- preregistered tests written before implementation;
- adversarial tests from a separate context;
- property-based/fuzz tests;
- mutation testing;
- independent consumer test;
- real downstream conformance fixture.

## Required receipts from an agent task

For material work, capture:

- base SHA;
- final head SHA;
- files changed;
- commands/tests run;
- pass/fail counts;
- CI run identifiers when available;
- known failures/warnings;
- deviations;
- what the results establish;
- what they do not establish;
- terminal PR/index reconciliation when the task owns that handoff.

Terminal prose is not a substitute for receipts.

## Safe mutation posture

Agents should not:

- merge a research PR solely because tests are green;
- bump a contract version before compatibility evidence exists;
- rewrite failed results into cleaner summaries;
- delete counterexamples because they are inconvenient;
- modify canonical schemas while running a supposedly shadow-only experiment;
- accept upstream semantic labels as authoritative unless the contract explicitly assigns that authority;
- infer completion from PTY quietness or delivery status;
- force-push shared research history without a documented reason.

## Handoff between threads/agents

A good handoff contains:

1. decision being pursued;
2. exact live repository/branch/SHAs;
3. claim under review;
4. evidence already established;
5. unresolved alternatives;
6. next discriminating action;
7. allowed and forbidden mutations;
8. expected output artifacts.

Avoid narrative-only handoffs that require the next agent to reconstruct state from chat history.

## Local-model use

Local agents are especially useful for repeatable, bounded work:

- deterministic fixture generation;
- test expansion;
- mutation/fuzz case generation;
- static scans;
- schema round-trip checks;
- documentation consistency checks;
- independent implementation where model capability is sufficient.

Use stronger models where the task depends on subtle semantic architecture or adversarial review, then push the conclusion back into executable tests where possible.

---

# Project Context Bootstrap

## First principle

Do not assume the project state in these attachments is current.

The attachments define durable **intent, boundaries, and procedure**. GitHub and current experimental artifacts define live state.

## Before substantive work

Inspect the relevant live state in this order:

1. target repository default branch/head;
2. relevant research/promotion branches;
3. open PRs and their bases;
4. latest CI runs and failed runs;
5. experiment briefs, results, and deviation records;
6. current Apparatus contract candidate/canonical versions;
7. downstream/upstream consumer pins if the task crosses a seam.

Record exact SHAs actually used.

## Questions every new thread should answer internally

- What decision is this work intended to support?
- What do we already know from direct evidence?
- What are we merely inferring?
- Which hypothesis is still live?
- What else could explain the observation?
- What assumption carries the most architectural weight?
- What observation would falsify the leading idea?
- Is there a smaller experiment that would discriminate before we build more?
- Is this research, research infrastructure, production promotion, maintenance, or a hotfix?

## Current architecture terms

Use these terms consistently unless a live spec supersedes them:

- **Evidence Bundler:** constructs/preserves evidence-world state.
- **Contract B:** Evidence Bundler → CAL typed handoff.
- **CAL:** proposition-specific semantic measurement and epistemic assessment.
- **Contract C:** CAL → Decision Engine result handoff candidate.
- **Decision Engine / Gate:** decision-context policy and routing.
- **MainFrame / Conduit:** orchestration/execution/lifecycle, not automatic proof or authority.

## Research thread output standard

A thread that materially changes project belief should finish with:

- observed evidence;
- inference;
- hypotheses still open;
- unknowns;
- falsified alternatives;
- disposition if justified;
- smallest next evidence-producing step;
- exact artifacts/SHAs created or relied on;
- affected canonical GitHub routing/index state reconciled when in scope.

## Implementation thread output standard

A thread that changes code should finish with:

- repository and branch;
- base and final SHAs;
- PR class and PR link/number if created;
- tests/CI receipts;
- behavior changed;
- behavior explicitly unchanged;
- unresolved risks;
- whether the evidence authorizes promotion.

## Stop conditions

Stop before mutation and escalate the ambiguity when:

- the requested branch has advanced materially and the delta changes the experiment;
- the supposed frozen fixture does not match its recorded hash/bytes;
- the task requires inventing a missing semantic default;
- a production change is being requested from evidence that is still inconclusive;
- independence is claimed but the isolation boundary is contaminated;
- a version bump is requested before compatibility class is demonstrated.

If the ambiguity does not affect validity, document it and proceed with the smallest safe assumption.

---

# Repository Setup Checklist

This is a practical target configuration, not a claim that every repository needs enterprise-style governance.

## Priority 1: protect production history

For each production repository, verify `main` is protected by either a GitHub ruleset or classic branch protection.

Recommended minimum:

- [ ] require pull request before merge;
- [ ] require meaningful CI/status checks;
- [ ] require resolution of review conversations;
- [ ] block force pushes to `main`;
- [ ] block deletion of `main`;
- [ ] restrict direct pushes where practical.

Do **not** add a required human approval merely to display a green badge if no genuinely independent reviewer is available.

## Priority 2: standardize PR entry points

Add PR templates for:

- [ ] research experiment;
- [ ] research infrastructure;
- [ ] promotion / production;
- [ ] maintenance / docs if useful.

Templates in this pack can be copied into `.github/PULL_REQUEST_TEMPLATE/` or adapted to repository conventions.

## Priority 3: standardize experiment records

Create conventional locations such as:

```text
docs/research/
  brief-XX-...
  results-XX-...
  deviation-XX-...
  decision-XX-...
fixtures/
research/
```

Exact layout may differ by repository, but a reviewer should be able to find preregistration, apparatus, result, and disposition quickly.

## Priority 4: labels

Create a small shared taxonomy:

- [ ] `research`
- [ ] `research-infrastructure`
- [ ] `promotion`
- [ ] `experiment:preregistered`
- [ ] `disposition:supported`
- [ ] `disposition:falsified`
- [ ] `disposition:inconclusive`
- [ ] `disposition:superseded`
- [ ] `needs-cross-repo-conformance`
- [ ] `apparatus-deviation`
- [ ] `breaking-change`
- [ ] `blocked`

Avoid a huge label ontology unless it solves a retrieval problem.

## Priority 5: release integrity for contracts

For canonical Apparatus contract releases:

- [ ] promote through a dedicated minimal PR;
- [ ] include compatibility classification evidence;
- [ ] run producer/consumer conformance;
- [ ] create immutable release/tag for canonical versions;
- [ ] include migration/adapter notes for breaking or additive changes;
- [ ] preserve the research PRs that justified the release.

## Priority 6: automated evidence gates

Where useful, add checks for:

- [ ] unit/integration tests;
- [ ] formatting/lint/type checks;
- [ ] schema validation;
- [ ] deterministic fixture validation;
- [ ] leak/secret/private-path scan;
- [ ] cross-repo conformance for contract changes;
- [ ] artifact/hash consistency;
- [ ] generated-file drift if committed generated outputs exist.

Only make checks *required* if they are stable, meaningful, and expected on the branch class.

## Priority 7: review independence

When external collaboration increases:

- [ ] add real CODEOWNERS only for actual owners/reviewers;
- [ ] require reviews for genuinely consequential areas if a reviewer is available;
- [ ] document independent consumer/reviewer isolation where it is an experimental variable.

A self-owned CODEOWNERS file has navigation value but weak assurance value.

## Lower-priority / conditional controls

### Signed commits

Useful for identity/supply-chain assurance. They do not prove code correctness. Add if the operational burden is low enough.

### Linear history

Useful if the project benefits from a simple production history. Not necessary for epistemic integrity by itself.

### Merge queue

Use only if concurrent merges begin causing stale-base failures. It is unnecessary ceremony for low merge volume.

## Project-level management

Consider one canonical cross-repository issue or project board that tracks:

- active research questions;
- owning repository;
- pinned branches/SHAs;
- disposition;
- blocking experiment;
- promotion PR when one exists.

Do not duplicate the full research record into the board. It should be an index, not a second source of truth.

---
