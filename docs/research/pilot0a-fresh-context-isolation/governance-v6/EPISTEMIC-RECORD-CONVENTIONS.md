# Epistemic Record Conventions

**Purpose:** Define stable conventions for living GitHub epistemic records without storing the changing records themselves in ChatGPT project context.

## 1. Epistemic Decision Records (EDRs)

Create an EDR when a decision materially changes:

- contract semantics;
- interface ownership;
- canonical architecture;
- version/compatibility policy;
- promotion criteria;
- an assurance gate;
- another decision that future work should not casually relitigate.

EDRs belong in GitHub correspondence.

### Minimum EDR fields

1. **Decision** — exact bounded choice.
2. **Effective artifact** — promotion PR, commit, release, or other concrete implementation.
3. **Observed evidence** — direct artifact/test facts only.
4. **Inference** — what those observations support.
5. **Alternatives considered** — credible competing options.
6. **Decision rationale** — why this choice follows for the decision being made.
7. **What is not established** — adjacent claims explicitly excluded.
8. **Compatibility / migration consequence** — when relevant.
9. **Residual uncertainty** — material unknowns retained.
10. **Reconsideration trigger** — evidence that should reopen the decision.
11. **Lineage** — preregistration, fixtures, PRs, CI, failures, deviations, and release links.

### EDR immutability rule

Do not rewrite the original evidence basis after later results arrive.

Add supersession, reconsideration, or follow-up context visibly.

The goal is an inspectable decision history, not a retrospectively perfect story.

## 2. Assurance cases

Use an assurance case for consequential promotions where the reasoning from evidence to the promoted claim is not obvious from one test result.

An assurance case may live in the EDR or promotion PR unless separation improves retrieval.

### Minimum assurance-case shape

- **Claim being assured**
- **Evidence items**
- **Reasoning linking evidence to the claim**
- **Falsification/negative evidence considered**
- **Residual uncertainty**
- **Scope and non-claims**
- **Revalidation trigger**

The argument must remain traceable to primary evidence.

Do not use assurance-case language as authority theater. Its value comes from exposing inferential links that can be challenged.

## 3. Claim registry convention

Material project beliefs should use a small status vocabulary:

- **OBSERVED**
- **SUPPORTED WITH BOUNDS**
- **HYPOTHESIS**
- **INCONCLUSIVE**
- **FALSIFIED**
- **SUPERSEDED**

Every supported claim should say what the evidence does **not** establish.

A claim's status changes only from new evidence or explicit reconsideration, not because implementation work makes the preferred conclusion convenient.

## 4. Epistemic risk convention

A risk register tracks assumptions capable of invalidating important conclusions or architecture.

Suggested statuses:

- **OPEN**
- **PARTIALLY TESTED**
- **SUPPORTED WITH BOUNDS**
- **FALSIFIED ASSUMPTION**
- **ACCEPTED RESIDUAL RISK**
- **SUPERSEDED**

A risk is not closed merely because a preferred implementation now exists.

Each high-priority risk should eventually have:

- why it matters;
- present evidence;
- discriminating test/observation;
- affected layer/interface;
- reconsideration condition.

## 5. Evaluator assurance convention

Evaluators are systems under test.

Use the following bounded assurance levels:

- **E0 — Unvalidated**
- **E1 — Basic controls**
- **E2 — Sensitivity/invariance validated**
- **E3 — Adversarially challenged**
- **E4 — Independently cross-checked**
- **E5 — Validated for a bounded decision**

An evaluator does not permanently “become E5.” The level applies to a named use under a named version/configuration.

### Promotion-critical evaluator record

Record:

- evaluator name/version/config;
- decision supported;
- intended property;
- observable proxy;
- positive controls;
- negative controls;
- sensitivity controls;
- invariance controls;
- adversarial/gaming controls;
- independent cross-check;
- known blind spots;
- assurance level for the specific decision;
- revalidation triggers;
- exact evidence links/SHAs/CI runs.

Do not make an automated check a required gate merely because it is easy to run.

### Evaluator correctness versus decision discrimination

Keep these questions separate:

- **Evaluator correctness:** does the implementation compute and react to the intended measurements correctly?
- **Decision discrimination:** does the evaluator/benchmark apparatus distinguish the target capability from plausible weak or gaming implementations strongly enough for the bounded decision?

For a promotion-critical evaluator or benchmark, include at least one intentionally weak but plausible implementation/control that should fail a meaningful decision gate for the intended reason. Prefer several independent weak strategies when cheap enough.

If the target system and a deliberately weak system both clear the promotion-critical gate, the apparatus may be functioning correctly while the broader capability claim remains `INCONCLUSIVE`. Do not redefine the gate after sealed exposure to restore discrimination.

A weak control failing only because of an incidental parser, shape, provenance, or environment defect is not evidence of semantic discrimination unless that property is itself part of the claimed capability.

Green CI establishes execution of the encoded checks, not evaluator validity or decision discrimination.

## 6. Causal-basis and multiplicity convention

Whenever a record claims an exact **basis**, **reason**, **cause**, or **dependency**, do not silently assume a single winner. Distinguish, where the system and evidence permit:

- a single necessary cause;
- independently sufficient alternatives;
- jointly sufficient / co-sufficient causes;
- redundant or non-deciding state;
- tied or co-maximal contributors;
- unavailable or not-testable causal structure.

Prefer controlled intervention, mutation, or counterfactual replay over correlation in one unchanged execution when causal attribution matters. Removing one candidate basis should change the claimed dependent result if that candidate is represented as necessary.

Do not collapse multiple legitimate bases into one arbitrary contributor merely to make a receipt compact. If current production state does not contain enough information to distinguish the causal structure, record that limitation explicitly rather than inventing attribution.

## 7. Disposition versus decision

Keep these distinct:

**Research disposition:** what did the experiment establish?

Allowed primary dispositions:

- `SUPPORTED FOR PROMOTION`
- `FALSIFIED`
- `INCONCLUSIVE`
- `SUPERSEDED`

**Decision record:** what should the project do given that evidence?

A supported research disposition does not dictate every implementation choice. The EDR records the smallest justified decision and the reasoning that connects evidence to action.

## 8. Costly-signaling standard for records

A record contributes to assurance when it reduces the project's freedom to rewrite history or smuggle unsupported claims forward.

High-value record properties include:

- preregistered falsifiers;
- frozen artifacts;
- exact SHAs;
- preserved failed runs;
- deviations;
- negative controls;
- independent reproductions;
- explicit non-claims;
- reconsideration triggers;
- lineage from promoted behavior back to evidence.

Avoid records whose primary function is ceremony.
