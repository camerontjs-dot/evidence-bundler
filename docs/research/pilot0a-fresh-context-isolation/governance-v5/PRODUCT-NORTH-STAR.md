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
