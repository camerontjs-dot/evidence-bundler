# Wide-to-Narrow Pressure Programme

## Objective

Start with a broad, inspectable shadow surface and remove mechanisms with evidence.

Do not start by choosing the fields that seem most elegant.

The programme should answer, in order:

1. Can the field be represented deterministically and truthfully?
2. Does the field measure the concept its name claims?
3. Is it independent of unrelated inputs?
4. Does it add information beyond simpler fields and semantic relevance?
5. Does the **correct** field value causally improve EB compared with wrong/shuffled controls?
6. Is the gain worth the operational and provenance burden?
7. Does the effect reproduce on fresh cases?

Only then should a field influence an EB research candidate.

---

# Phase 0 - consumer apparatus qualification

This phase is mandatory before any causal Gate→EB experiment.

## 0A. Exact artifact verification

The consumer must verify:

- exact Gate implementation identity;
- exact ClaimGate output hash;
- exact EvidenceGate output hash;
- exact Contract A binding when present;
- exact paired receipt;
- exact raw reconstruction inputs required by the upstream contract;
- exact feature registry / qualification record identity.

## 0B. Cross-artifact consistency

PR #46 established that schema-valid objects can still be cross-artifact inconsistent after hashes are recomputed.

Therefore an EB consumer cannot rely on JSON Schema alone.

Require a canonical verifier that checks at minimum:

- receipt ClaimGate hash equals the exact ClaimGate artifact;
- receipt EvidenceGate hash/world identity equals the exact EvidenceGate artifact;
- Contract A binding equals the exact Contract A bytes;
- claim root identity agrees across the claim-side artifacts;
- evidence-world identity agrees across evidence-side artifacts;
- claim-independent EvidenceGate invariants hold;
- no causal authority flag is elevated beyond the qualification record.

If the upstream programme produces this verifier, EB should use the exact qualified identity.

If it does not yet exist, EB may build an experimental independent consumer verifier for pressure testing, but that does not replace upstream authority.

## 0C. Contract A conformance

Preserve the observed producer-conformance counterexample:

- Proposition Authoring can currently copy an unconstrained source media type into Contract A;
- released Contract A 2.0.0 permits only its frozen media-type vocabulary;
- EB correctly fails closed.

Do not widen EB or Contract A to absorb the producer defect.

Causal Gate→EB experiments requiring Contract A must use conformant frozen inputs.

---

# Phase 1 - representation pressure

## Goal

Pressure all broad shadow fields without allowing them to influence retrieval.

### Input

A fresh, frozen multi-domain case set covering:

- simple atomic claims;
- comparative claims;
- quantitative claims;
- status/approval claims;
- temporal claims;
- causal claims;
- existence/definition/compliance claims;
- attributed claims;
- negated/modal claims;
- compound/ambiguous surfaces;
- partial/incomplete evidence worlds;
- version/supersession cases;
- multi-jurisdiction cases;
- no-evidence / unknown-state cases.

Do not rely only on synthetic clean examples.

Include real-world-style identifiers, citations, dates, versions, source locators and messy prose.

## Field-level controls

Every field should face relevant variants of:

- positive case;
- explicit negative;
- absent/unknown;
- near-boundary counterexample;
- irrelevant mutation;
- causal mutation;
- order permutation;
- duplicate insertion;
- malformed declaration;
- contradictory declaration;
- cross-field isolation.

## Required outputs

For every registry entry:

- observed value;
- expected value/class where gold is valid;
- mutation behavior;
- deterministic replay;
- failure examples;
- field basis;
- whether the field name overstates the implementation;
- burden/cost;
- disposition.

Suggested dispositions:

- `SUPPORTED_SHADOW`;
- `REPAIR_AND_RETEST`;
- `REDUNDANT_SHADOW`;
- `DROP_CONCEPT`;
- `INCONCLUSIVE_REPRESENTATION`.

Do not create `QUALIFIED_HINT` in Phase 1.

---

# Phase 2 - mechanism and redundancy pressure

## Goal

Determine which surviving descriptors provide distinct information rather than duplicating semantic relevance or each other.

Test by **families first**, not 92 independent p-values.

Suggested families:

1. evidence-shape requirements;
2. claim structure / relation descriptors;
3. temporal / jurisdiction compatibility;
4. source/evidence form and role;
5. version / currency / supersession;
6. corpus aperture / completeness / gaps;
7. passage evidentiary posture;
8. redundancy / source breadth;
9. provenance/origin characterization.

## Baselines

Compare each family against:

- proposition text only;
- semantic embedding/relevance only;
- claim category only where available;
- evidence form only;
- semantic + evidence form.

## Questions

- Does the family predict where useful evidence lives?
- Does it distinguish unsafe/misleading evidence?
- Does it predict required-group coverage?
- Does it merely correlate with easier cases?
- Is the information recoverable directly from candidate text, making the upstream field redundant?
- Does the field add information after semantic score/rank is controlled?

Fields that add no distinct information can remain descriptive without becoming causal.

---

# Phase 3 - fixed-pool causal screening

## Goal

Test whether correct Gate-informed state changes K=3 selection beneficially on identical depth-10 pools.

First-stage retrieval stays frozen.

## Design

Use fresh hidden-gold cases.

For each candidate mechanism family, freeze:

- candidate pools;
- semantic model/revision;
- candidate characterization;
- hint values;
- field masks;
- wrong/shuffled controls;
- evaluator;
- thresholds.

## Core arm pattern

### A - incumbent

Semantic top-K.

### B - correct signal

Semantic incumbent plus one bounded, frozen mechanism.

### C - ablation/coarse control

Semantic plus the simpler parent signal.

Examples:

- claim family instead of structured requirement;
- evidence form without temporal compatibility;
- exact duplicate only instead of broader redundancy.

### D - wrong/shuffled signal

Same mechanism as B, but with a valid signal from another case or frozen incorrect mapping.

This arm is mandatory whenever an upstream hint is claimed to matter.

### Optional E - generic diversification control

Use only when needed to distinguish correct requirements from generic diversity.

## Promotion criterion

A mechanism must show that **correct signal matters**.

Improvement versus A is insufficient if D improves similarly.

---

# Phase 4 - component interaction pressure

Only mechanisms that survive Phase 3 enter interaction testing.

Do not jump straight to a weighted aggregate.

Test staged combinations such as:

```text
semantic relevance
  -> evidence-shape coverage repair
  -> temporal/jurisdiction repair
  -> posture safety repair
  -> duplicate/supersession repair
```

For each added stage, require:

- incumbent versus +stage;
- stage ablation;
- wrong/shuffled control if upstream-derived;
- burden delta;
- failure-localization output.

If two stages interfere, preserve the counterexample instead of retuning weights until it disappears.

---

# Phase 5 - first-stage retrieval planning

Eligible only after at least one upstream signal survives fixed-pool causal screening.

## Question

Can the supported signal help EB make **better evidence available in the candidate pool**, rather than merely rearrange available candidates?

## Candidate retrieval mechanisms

Pressure-test independently:

- multi-intent retrieval by evidence-shape branch;
- typed temporal retrieval intent;
- typed jurisdiction intent;
- version/currentness intent;
- gap-recovery intent;
- corroboration intent.

All query text remains EB-generated.

## Required controls

- baseline exact-proposition retrieval;
- correct signal;
- wrong/shuffled signal;
- signal absent/unknown;
- equivalent total retrieval budget.

## Metrics

- required evidence available by depth N;
- useful evidence recall by depth N;
- first useful rank;
- evidence-form coverage;
- source breadth;
- duplicate burden;
- unsafe/misleading burden;
- retrieval calls;
- latency;
- deterministic replay.

A gain created only by spending more retrieval budget is not evidence that the hint is useful.

---

# Phase 6 - adaptive budget and stopping research

This is deliberately later.

Possible hypotheses:

- allocate candidate depth per required branch;
- extend depth only for uncovered required branches;
- stop after all required branches have candidate representation;
- reserve a small unknown/unclassified budget;
- stop on diminishing novel-coverage gain.

Every adaptive policy needs:

- fixed global ceiling;
- deterministic behavior;
- no gold access;
- wrong-hint control;
- burden accounting.

Do not let adaptive depth become an unbounded completeness claim.

---

# Phase 7 - fresh independent reproduction

Any candidate that survives the development programme receives:

- fresh hidden cases;
- independent case/gold authoring;
- frozen input/evaluator separation;
- blind target execution;
- exact replay/metamorphic tests;
- explicit terminal disposition.

Development-set success never promotes directly.

---

# Broad pressure cohorts

To avoid overfitting the design to the current regulated examples, the research surface should include several evidence-world archetypes.

## Regulatory/status

Examples:

- approval;
- licence;
- registration;
- compliance state;
- current policy/version.

Pressure:

- identifiers;
- citations;
- effective dates;
- supersession;
- authority declarations.

## Quantitative/comparative

Pressure:

- measurements;
- units;
- thresholds;
- comparisons;
- tables;
- narrative summaries;
- contradictory measurements.

## Temporal/version

Pressure:

- point versus interval;
- old/current versions;
- supersession chains;
- effective/expiry dates;
- claims spanning multiple periods.

## Causal/event

Pressure:

- event records;
- measurements;
- narrative causal statements;
- hypotheses;
- confounding descriptions;
- rejected explanations.

The Gate does not judge causality. This cohort tests whether evidence-shape descriptors are useful for finding the right material.

## Attribution/definition/policy

Pressure:

- direct declarations;
- quoted statements;
- summaries;
- policy/rule text;
- secondary descriptions.

## Sparse/incomplete corpus

Pressure:

- explicit missing evidence forms;
- declared gaps;
- unknown completeness;
- inaccessible sources;
- empty evidence world.

The desired behavior may be faithful insufficiency rather than aggressive retrieval.

---

# Pruning rules

Drop or quarantine a field/operator when one of these becomes established:

1. representation cannot be made deterministic without semantic overclaim;
2. field fails ordinary counterexamples after a bounded repair attempt;
3. value is redundant with simpler stable signals;
4. correct and wrong/shuffled versions have indistinguishable causal effects;
5. improvement requires answer-bearing or CAL-relative state;
6. burden is disproportionate to effect;
7. field causes severe easy-case regression;
8. effect does not reproduce on fresh hidden cases.

Retain a field descriptively even if it has no causal EB value when it remains useful for audit/reconstruction.

The production surface should be a **pruned subset** of the research carrier, not the other way around.
