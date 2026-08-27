# Contract A Decomposition Sensitivity RC1

**PR class:** Research
**Production impact:** None
**Base:** `evidence-bundler` production `main` at `c8189c31adbab11729c31430c2070126224a2d42`

## Decision this experiment supports

Decide whether claim decomposition must be a first-class, identity-bearing part of the upstream handoff into Evidence Bundler, and which decomposition facts Contract A must preserve so downstream evidence-world differences remain reconstructable.

This experiment does not assume that decomposition is beneficial. It tests whether decomposition materially changes retrieval and evidence-world construction.

## Claim under review

> When an original claim is transformed into one or more audit propositions, the decomposition can materially alter Evidence Bundler retrieval and therefore must be explicitly attributable, reproducible, and distinguishable from the original claim rather than silently treated as preprocessing.

## Competing explanations

- Decomposition materially improves retrieval by creating clearer evidence targets.
- Decomposition materially harms retrieval by narrowing or distorting the original proposition.
- Different legitimate decompositions retrieve different evidence, meaning decomposition is a consequential epistemic intervention.
- Decomposition has little practical effect because EB already retrieves broadly enough from the original claim.
- Apparent decomposition effects are actually caused by query-generation differences or evaluator artifacts.

## Frozen variables

For each comparison family hold fixed:

- exact corpus bytes and source IDs;
- EB implementation SHA and retrieval configuration;
- embedding/model versions where applicable;
- search budget/top-k;
- admission/review policy;
- Contract-B output profile;
- gold relevance labels.

Only the audit-object/decomposition representation may vary unless a secondary mutation is explicitly preregistered.

## Experimental variants

### A0 — Original-claim only
EB receives the original claim/audit question without decomposition.

### A1 — Explicit reference decomposition
EB receives the same original claim plus a frozen reference decomposition with parent/child lineage.

### A2 — Alternative legitimate decomposition
A second decomposition preserves the intended overall meaning but groups/splits propositions differently.

### A3 — Meaning-drifting decomposition control
A deliberately defective decomposition drops, weakens, strengthens, changes scope, or changes a condition. This is a negative control, not a legitimate candidate.

### A4 — Over-decomposition control
Split the original claim into unnecessarily granular propositions to test fragmentation costs and cross-passage evidence loss.

## Required observations

For every variant record:

- exact original claim identity/hash;
- exact child proposition texts and hashes;
- decomposition method/producer identity;
- decomposition configuration/prompt hash where applicable;
- parent/child graph;
- retrieval queries actually issued;
- retrieved and admitted source/passage IDs;
- gold relevant passage coverage;
- decisive counterevidence coverage;
- evidence unique to one decomposition;
- provenance integrity;
- Contract-B artifact identity where produced.

## Primary comparisons

1. Does decomposition change source/passage recall?
2. Does it change decisive counterevidence recall?
3. Does it change which evidence reaches the admitted measurement view?
4. Are changes explainable from the explicit decomposition lineage?
5. Do two legitimate decompositions create materially different evidence worlds?
6. Can the original claim and every child audit proposition be reconstructed without free-text inference?
7. Does over-decomposition cause evidence requiring cross-passage or cross-proposition composition to disappear?

## Metamorphic / adversarial tests

- reorder child propositions without changing their content;
- rename child IDs while preserving identity bindings;
- paraphrase a child proposition without changing meaning;
- remove one material condition from a child proposition;
- change a quantifier or numeric threshold;
- split one proposition into two equivalent children;
- merge two children where the conjunction/disjunction semantics differ;
- introduce a child unsupported by the parent claim;
- omit parent lineage and verify the apparatus treats lineage as missing rather than inventing it.

## Falsification criteria

The claim that decomposition needs first-class Contract-A identity is weakened if:

- across diverse frozen cases, legitimate decomposition variants do not materially change retrieval, admission, or downstream evidence-world state;
- all decomposition effects can be reproduced solely from a simpler explicit query object that does not require decomposition lineage;
- EB can reconstruct the needed upstream distinction from existing immutable claim/task state without ambiguity.

The claim is strengthened if:

- legitimate decompositions reliably produce materially different evidence worlds;
- meaning-drifting decomposition changes retrieval in ways that would be invisible without lineage;
- downstream audit differences cannot be explained without knowing the exact decomposition that created the search target.

## Evaluator risks

- gold labels may privilege one decomposition style;
- the benchmark may treat proposition-level relevance independently when real support requires composition;
- a decomposer could overfit to corpus wording;
- a single domain may exaggerate or hide decomposition sensitivity.

## Expected Contract-A consequences if supported

Contract A RC1 should likely carry, without declaring correctness:

- immutable original claim/question identity;
- exact audit proposition identity/text;
- parent/child lineage;
- decomposition artifact identity;
- producer/model/operator identity;
- method/config/prompt hash where material;
- explicit `not_decomposed` versus `decomposed` state;
- optional rationale/notes as attributable upstream assertions, not evidence facts;
- no silent replacement of the original claim by a child proposition.

This is a hypothesis to test, not a preregistered schema decision.

## Stop condition

If surprising differences appear, first determine whether they arise from decomposition semantics, query generation, retrieval randomness/configuration, corpus labeling, or evaluator design before changing Contract A or EB production behavior.
