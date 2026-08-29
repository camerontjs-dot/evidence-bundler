# Context-Free Execution Routing Protocol

**Purpose:** Define when CAL Pipeline work should be moved from the normal project context into the separate context-free project because shared conversational/project history would weaken the meaning of the result.

## Core rule

> **Use the normal CAL Pipeline project for continuity, synthesis, governance, and ordinary implementation. Use the context-free project only when information isolation is itself part of the validity claim.**

The context-free project is an execution surface, not a source of truth. Durable project files still define procedure, and GitHub plus exact immutable artifacts still define live state and evidence.

A fresh project/thread does not automatically make a result independent. The task must also define and preserve the allowed information aperture.

## When context-free execution is required

Route a task to the context-free project when the result depends materially on the executor **not** knowing prior implementation details, expected answers, hidden/gold state, prior scientific observations, or earlier reasoning.

Typical triggers include:

- a task explicitly requiring a fresh context, clean room, blind handoff, or independent reproduction;
- Consumer B / independent consumer implementation from a frozen specification;
- independent evaluator implementation where evaluator A, tests, canonicalizer, or expected outputs must remain unseen until freeze;
- benchmark construction or adjudication that must be separated from target-system execution;
- held-out, hidden-gold, commit/reveal, or sealed-candidate experiments;
- pre-freeze evaluator or apparatus work where prior candidate results would permit retrospective tuning;
- a successor run whose predecessor was invalidated by context contamination;
- any preregistration that names prior threads, results, implementation files, PR narrative, or reasoning as forbidden pre-freeze information.

## When context-free execution is not required

Do not move work merely because it is consequential or large.

The normal CAL Pipeline project is preferable for:

- live-state audits and portfolio synthesis;
- governance reconciliation;
- ordinary maintenance and production fixes;
- promotion work that legitimately consumes already-published research evidence;
- implementation of a requirement whose supported evidence is intentionally part of the task input;
- architecture review where prior project history is relevant evidence rather than a contaminant.

## Routing decision

Before launching a consequential research task, ask:

1. Would knowing a prior result, implementation, expected answer, or scientific observation make the claimed result easier to produce?
2. Is independence, blindness, freshness, or pre-freeze ignorance part of the claim?
3. Does the governing experiment identify information that must remain unavailable until a freeze or reveal point?
4. Could the same question be answered without an isolation claim?

If any of 1-3 is yes and the isolation claim matters to the disposition, mark the task **CONTEXT-FREE REQUIRED**.

If isolation is useful but not necessary to the claim, mark it **CONTEXT-FREE PREFERRED** and state what weaker claim remains valid if ordinary context is used.

## Required launch packet

A context-free task must not be started by copying the surrounding project conversation.

Provide only the smallest authorized packet:

- exact objective/decision;
- exact repository and starting identity needed for the task;
- the frozen authority/bootstrap manifest when one exists;
- durable governance files explicitly permitted by that manifest/task;
- exact pre-freeze allowlist;
- exact pre-freeze denylist;
- freeze point and required freeze receipt;
- post-freeze reveal permissions;
- contamination stop rule;
- allowed terminal states and required output receipts.

Prefer immutable paths, SHAs, blob hashes, and mechanically constrained readers over narrative summaries.

**Important:** a frozen experiment's existing authority manifest outranks this general routing protocol for the information aperture of that experiment. Do not inject a newly added project file, summary, or audit into an older frozen clean-room run unless the experiment's authoritative manifest explicitly permits it.

## GitHub access rule inside a context-free run

“Inspect GitHub live” does not mean “search GitHub broadly.”

When the experiment has a constrained aperture:

- use only the exact GitHub paths/ref/blob surfaces authorized before freeze;
- prefer body-free ref/commit/tree/blob identity surfaces when narrative is forbidden;
- do not browse historical PR bodies, issue comments, search snippets, results files, or adjacent branches merely to orient the executor;
- record every material pre-freeze source actually opened.

After the authorized freeze, reveal only the surfaces the protocol permits.

## Freeze and contamination rule

The executor must freeze the object that needs independence **before** opening comparison/answer-bearing material.

The freeze receipt should identify, as applicable:

- implementation/evaluator bytes or commit;
- fixture/spec identities;
- model/config/tool identity when material;
- allowed inputs actually read;
- prohibited inputs not read;
- time/order of freeze versus reveal.

If forbidden information is exposed before freeze:

1. stop the claimed clean-room/independent run;
2. preserve the exposure record;
3. do not continue and later relabel the same execution independent;
4. create a fresh successor only if the scientific question still warrants it.

Contamination is a valid terminal result about the execution protocol. It is not automatically a scientific result about the system under test.

## Return handoff to the normal project

A context-free run should return a compact durable handoff rather than hidden reasoning:

- repository / PR / branch;
- base and final SHAs;
- frozen object identities;
- exact sources opened before and after freeze;
- CI/run/artifact receipts;
- deviations or contamination;
- observed result;
- bounded inference;
- allowed research disposition;
- what is not established;
- exact next authorized step.

The normal CAL Pipeline project may then synthesize the result with the rest of the portfolio.

## Independence vocabulary

Use the strongest term the aperture actually supports:

- **fresh-context execution:** prior project conversation was not supplied, but no stronger implementation-independence claim is made;
- **separate implementation/review:** a distinct implementation/reviewer was used, but contamination-free independence is not established;
- **clean-room / independent reproduction:** the preregistered information boundary, freeze order, and contamination record support that stronger claim for the bounded task.

Do not infer the strongest label merely from using a different project or thread.
