# Project State Location Policy

**Purpose:** Define which CAL Pipeline information belongs in durable ChatGPT project attachments and which belongs in live GitHub correspondence/evidence.

## Core rule

> **Project files define durable intent and procedure. GitHub defines live project state.**

A ChatGPT project attachment must never be treated as authoritative evidence of current repository state, research disposition, contract version, evaluator status, open risk, or release status.

Before any material implementation, promotion, or research decision, inspect the relevant live GitHub state and exact artifacts.

## What belongs in ChatGPT project files

Use project attachments for information expected to remain stable across many experiments and releases:

- product goal and non-goals;
- system/component responsibility boundaries;
- epistemic categories and reasoning conventions;
- experiment methodology;
- costly-signaling principles;
- PR classes and promotion procedure;
- agent isolation and contamination rules;
- conventions for EDRs and assurance cases;
- conventions for evaluator validation;
- rules describing where live state is stored;
- rules for deciding when work must move to the separate context-free project.

Project files answer:

> **How should this project reason and work?**

## What belongs in GitHub correspondence/evidence

Use GitHub for anything whose content or epistemic status should change as evidence accumulates:

- current research questions;
- current claim status;
- epistemic risk register;
- current interface/canonical-version state;
- evaluator assurance status;
- research dispositions;
- apparatus deviations;
- Epistemic Decision Records (EDRs);
- assurance cases;
- compatibility/version decisions;
- promotion/release lineage;
- current blockers and supersession state;
- current experiment priorities.

GitHub answers:

> **What do we currently know, believe, question, or operate?**

## Canonical correspondence surfaces

At time of adoption, the cross-repository governance surfaces are:

- `camerontjs-dot/apparatus-contracts#7` — research PR disposition and production-promotion governance;
- `camerontjs-dot/apparatus-contracts#8` — living epistemic state, interface status, EDR and assurance-case correspondence;
- `camerontjs-dot/apparatus-contracts#9` — evaluator assurance registry.

These issues are routing/index surfaces. Primary experiment evidence remains in exact PRs, briefs, fixtures, commits, CI runs, deviations, and releases.


## Context-free project location rule

The separate context-free project is an **execution isolation surface**, not another source of project truth.

Use it when freshness, blindness, clean-room reproduction, evaluator independence, hidden-gold separation, or another information boundary is part of the validity claim. The normal CAL Pipeline project remains the place to synthesize portfolio state and decide whether such routing is required.

Live state still comes from GitHub and exact immutable artifacts, but a context-free run may inspect only the subset authorized by its task-specific information aperture. Broad live-state inspection is prohibited when it would reveal information the preregistration requires to remain hidden before freeze.

A frozen authority/bootstrap manifest outranks later general project-file changes for the information aperture of that specific experiment. Do not retroactively inject new durable attachments into an already frozen clean-room protocol.

The durable routing convention is `CONTEXT-FREE-EXECUTION-PROTOCOL.md`.

## Source-of-truth hierarchy

When sources conflict, prefer:

1. exact immutable experiment/release artifacts and commits;
2. current GitHub PR/issue/release state;
3. current canonical contract/specification;
4. GitHub index/correspondence summaries;
5. durable ChatGPT project conventions;
6. conversational memory.

A summary never outranks the artifact it summarizes.

## New-thread rule

Before substantive work, an agent should:

1. read durable project conventions;
2. inspect live GitHub correspondence relevant to the task;
3. inspect exact primary artifacts/SHAs;
4. state any discrepancy instead of silently reconciling it;
5. proceed from the most authoritative current evidence.

## Update rule

Do not create a new project attachment merely because live state changed.

Update GitHub instead.

When a material experiment or promotion decision reaches a terminal state, reconcile the affected live GitHub surfaces before treating the thread as complete:

- primary result/decision artifact first;
- PR metadata/body/disposition next;
- canonical routing/index issue(s) after that;
- blockers, successor authorization, and supersession state made explicit.

The primary artifact remains authoritative if an index temporarily lags. That lag should be recorded and corrected; it must not be silently interpreted as a different scientific result.

Create or replace a project attachment only when a **durable convention itself** changes materially enough to justify the manual project-file update.
