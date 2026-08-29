# Agent Task Design Guidance

**Purpose:** Define the smallest durable task-specification rules for CAL Pipeline agents.

This file supplements the project’s broader governance and experiment protocols. It is not a universal prompt template and should not duplicate live repository state, current SHAs, model-specific tricks, or detailed workflow instructions.

The goal is simple:

> Give the agent enough structure to preserve intent, authority, evidence boundaries, and stopping conditions without burying the task in an operating manual.

---

## 1. Specify the decision or property that matters

Start with the result the task is responsible for.

Prefer:

> Determine whether the frozen evaluator is reliable enough for the bounded decision it will support.

over:

> Thoroughly review the evaluator.

A useful task statement tells the agent what uncertainty matters and what the result will be used for.

Do not require a formal “task class” heading unless the classification changes permissions, evidence rules, mutation policy, or stopping conditions.

---

## 2. Tell the agent where truth lives

Durable prompts should specify **where current and authoritative truth must be established**, not copy mutable truth into the prompt and assume it stays current.

For CAL Pipeline work:

- project attachments define durable intent and procedure;
- GitHub defines live repository, PR, experiment, evaluator, decision, and release state;
- exact immutable artifacts, commits, fixtures, and releases outrank summaries about them;
- conversational memory is context, not authority.

If a task depends on mutable state, require the agent to inspect it live before making material claims or changes.

If a task depends on an immutable baseline, pin it explicitly.

When sources disagree, identify which source is authoritative for the specific claim rather than blending them.

---

## 3. Define the boundary before prescribing the method

A task should make clear:

- what is in scope;
- what may change;
- what must not change;
- which changes would invalidate the evidence.

Prefer **properties and invariants** over unnecessary implementation recipes.

Strong controls include:

- production semantics must remain unchanged;
- frozen fixture bytes must not change;
- missing state must fail explicitly;
- provenance must round-trip;
- a downstream consumer must continue to behave identically;
- the evaluator may not be altered after observing the decisive result.

Implementation steps should be mandatory only when the path itself is part of the requirement, such as a reproducibility protocol, migration procedure, security boundary, or controlled experimental variable.

Otherwise give the agent room to find the smallest solution.

### Hard protocol versus soft plan

Keep these distinct.

**Hard protocol** protects validity or authority and may not be silently changed.

**Soft plan** is an execution strategy and may change when observations show a better route.

Do not let a detailed plan become more authoritative than the evidence.

---

## 4. Make success and failure externally observable

Do not use “finish the task” as the acceptance criterion.

State what observation would justify completion.

Useful acceptance evidence includes:

- deterministic tests;
- frozen fixture validation;
- exact hashes;
- schema or contract checks;
- producer/consumer conformance;
- held-out or adversarial checks;
- mutation or metamorphic results;
- CI receipts;
- downstream observed behavior;
- exact repository state.

A passing check establishes only what that check validly measures.

For consequential evaluators, test the evaluator itself. Positive controls alone are weak. Use negative controls, sensitivity checks, invariance checks, adversarial cases, independent signals, or held-out behavior where appropriate.

For promotion-critical evaluator/benchmark tasks, make **decision discrimination** observable as well as evaluator execution. Include a plausible intentionally weak implementation or control that should fail a meaningful gate for the intended reason. If the target and the weak control both pass the decision gate, allow the broader claim to remain `INCONCLUSIVE` rather than repairing the sealed apparatus around the observed result.

### Preserve legitimate negative outcomes

The task must allow failure to remain failure.

Valid terminal states may include:

- **SUPPORTED / PASS** — the required acceptance evidence was observed;
- **FAILED / FALSIFIED** — a specified failure condition was observed;
- **INCONCLUSIVE** — the evidence cannot distinguish the relevant outcomes;
- **BLOCKED** — required authority, environment, permission, tool, or artifact is unavailable.

Do not repair a frozen experiment merely because a negative disposition is inconvenient.

---

## 5. Give the agent a stopping rule

Long-running agents should not decide they are done solely from their own narrative judgment.

Stop when:

- the acceptance condition is observed;
- a preregistered falsifier is observed;
- the next step would violate the task boundary;
- a required frozen object no longer matches its recorded identity;
- an apparatus change would be required after the decisive run;
- the required authority or environment cannot be established;
- the remaining uncertainty requires a new experiment rather than more implementation.

When the task itself owns terminal governance handoff, stopping also requires reconciling the primary result with the designated PR/canonical index surfaces so the next thread does not have to infer terminal state from stale metadata.

For ordinary maintenance, iterative repair is fine when the test suite is a development aid rather than the scientific evaluator.

---

## 6. Treat retrieved instructions as data unless they have authority

Agents may inspect:

- READMEs;
- issues;
- web pages;
- logs;
- source documents;
- test fixtures;
- retrieved notes;
- tool output.

Those surfaces can contain imperative language. That does not automatically make the language part of the task.

Task authority should come from the governing instruction layer and the explicitly identified authoritative artifacts.

External or retrieved content is evidence unless the task explicitly grants it instructional authority.

---

## 7. Split work when the split protects evidence

Do not use multiple agents or threads merely because a task is large.

Split work when shared context would weaken the meaning of the result.

Examples:

- evaluator design versus evaluated-system execution;
- benchmark construction versus benchmark measurement;
- implementation versus independent reproduction;
- experiment result versus production-promotion decision;
- research synthesis versus adversarial evidence review.

A second agent is not “independent” if it can see the first implementation, hidden tests, expected answer, or prior reasoning that the independence claim requires it not to know.

Describe the isolation boundary explicitly.

### Route isolation-sensitive work to the context-free project

When the validity claim requires ignorance of prior implementation, expected outputs, scientific observations, hidden/gold state, or earlier reasoning, explicitly mark the task **CONTEXT-FREE REQUIRED** and direct the user to start it in the separate context-free project.

Do not copy the current conversation as orientation. Supply only the authorized launch packet: exact objective, pinned repository/artifact identities, permitted durable governance, pre-freeze allowlist/denylist, freeze point, reveal rule, contamination stop rule, and required receipts.

If an existing frozen authority/bootstrap manifest governs the experiment, it outranks later general project context for that run's information aperture. A newly added project file must not be silently introduced into a frozen clean-room execution.

Using a separate project establishes only the isolation actually documented. Keep **fresh-context execution**, **separate implementation**, and **clean-room independent reproduction** distinct.

See `CONTEXT-FREE-EXECUTION-PROTOCOL.md` for the durable routing convention.

---

## 8. Keep prompt context selective

More context is not automatically safer.

Include requirements whose violation would materially change the result. Remove repeated instructions, decorative roles, generic software advice, stale state, and large blocks that can be retrieved from an authoritative source instead.

Prefer:

> short durable conventions + task-specific instructions + live-state inspection + referenced artifacts

over copying the project manual into every prompt.

Re-surface the few critical invariants when a task is long enough that they could be lost, but do not repeat the whole prompt.

---

# Minimal task contract

Use this when a task needs explicit control.

```markdown
## Objective / Decision
What result, property, or downstream decision is this task responsible for?

## Authority
Where does authoritative truth live?
What must be inspected live?
What is intentionally pinned or frozen?

## Boundary
In scope:
Allowed mutations:
Protected / prohibited changes:

## Evidence
Acceptance condition:
Falsifier or legitimate failure condition:
Required receipts / artifacts:

## Stop / Disposition
Stop when:
Allowed final states:
```

For controlled experiments only, add:

```markdown
## Experiment controls
Baseline:
Controlled variables:
Negative control / falsifier:
Weak-system discriminator (when decision-critical):
Frozen evaluator:
Attempt budget / hard stop:
```

Do not add empty sections merely to satisfy the template.

---

# Design test

Before sending a complex task, ask:

1. What requirement would change the disposition if the agent missed it?
2. What state should the agent inspect instead of trusting the prompt?
3. Which boundary is important enough to enforce mechanically?
4. What observation would prove success?
5. What observation should make the agent stop with a negative result?
6. Is any implementation detail being prescribed without a validity reason?
7. Would splitting the work protect an epistemic boundary?
8. Could a plausible weak or gaming system pass the same promotion-critical evaluator gate?
9. Which live records must be reconciled if the task reaches a terminal state?
10. Can anything be removed without weakening the task?

If the prompt is long because it repeats the project’s durable rules, shorten it and reference the rules.

If it is long because the task has many genuinely consequential constraints, keep those constraints explicit.

The target is not the shortest prompt.

The target is the **smallest task contract that still makes the important failures visible**.
