# Decomposition + Parent/Child Complementarity Dev RC1 — Preregistration

Status: preregistered before fresh decomposition generation or retrieval execution.

## Decision questions

1. Which bounded decomposition strategies produce useful evidence worlds without semantic-faithfulness instrument failures?
2. For a valid Contract A `declared/all_of` root, does retrieving the exact root in addition to mandatory exact-child retrieval add material information?
3. Does preserving proposition/retrieval roles outperform flattening the same available root/child evidence into an anonymous union?

This experiment does not decide a CAL aggregation rule and cannot confer Contract A authority on generated semantics outside each sealed research fixture.

## Frozen predecessor / corpus lineage

- predecessor research PR: #43
- predecessor terminal head: `0e4bed62553ebb6aef6a1b485664fb80cc78c802`
- predecessor decisive implementation: `55d158f829f4aad1ed8ad69b19d9e39d445c953d`
- predecessor decisive run: `33286415682`
- frozen challenge corpus tree SHA256: `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8`
- frozen dev decomposition file SHA256: `2120228c81466471214ca8b56a6eba2fa5bc498cd0b0243ff3b8fe24c9da2144`
- retrieval embedding model: `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- split: dev only
- sealed/test split: prohibited

The bounded case cohort is the six predecessor composite/decomposition cases:

- `claim-009` / F03 NEGATION_POLARITY
- `claim-013` / F04 NUMERIC_THRESHOLD
- `claim-017` / F05 TEMPORAL_SUPERSESSION
- `claim-021` / F06 CONDITION_EXCEPTION
- `claim-037` / F10 MULTI_PASSAGE_COMPOSITION
- `claim-049` / F12 APERTURE_BOUNDARY

## Canonical contract authority pins

Every treatment must be materialized as a valid Contract A 2.0.0 wire object and validated by the exact canonical production validator at:

- repository: `camerontjs-dot/apparatus-contracts`
- authority commit: `c3563cff66d2c85dcbf575c693056e2d8e4563d4`
- Contract A 2.0.0 validator engine blob: `42e5f5b3bf38d677445e9d01ea130ba604e53409`
- wire token: `contract-a-wire-candidate-rc2`

Each case keeps one exact immutable root proposition and one identical ordered source-representation array across all treatments. Every declared treatment has a unique decomposition identity and exact child proposition IDs/text/hashes/order. A generator that cannot safely produce at least two unique children emits a valid Contract A `decomposition.state=failed` object and is recorded as an abstention; it is not repaired posthoc.

## Frozen decomposition treatments

Treatments are generated/frozen before retrieval gold is opened.

### D1 — minimal conjunctive

Use the predecessor frozen A1 child texts exactly. This is the minimal conjunctive baseline.

### D2 — scope preserving

Use the predecessor frozen A2 child texts exactly.

### D3 — retrieval-oriented, meaning-preservation constrained

Fresh model generation using only the exact root proposition and supplied source representations. Prompt requires two to four independently auditable propositions, preservation of all numbers, negation, temporal scope, modality, conditions/exceptions and named population/entity scope, and forbids adding facts. The model is:

`google/flan-t5-small@14fd6edcfdd71f2ef5b67d4e735fee8bc6d9fd31`

This treatment is not accepted as semantically faithful merely because retrieval improves.

### D4 — typed-semantic, bounded CAL concepts

Fresh model generation using only the same root/source aperture. The prompt asks for two to four proposition units aligned to bounded semantic dimensions (condition/exception, temporal scope, numeric/qualifier, modal/deontic force, entity/population scope) while preserving exact proposition meaning and forbidding additions. The model is:

`HuggingFaceTB/SmolLM2-360M-Instruct@a10cc1512eabd3dde888204e902eca88bddb4951`

Semantic type labels are retained only in the generation record. They are not added to Contract A proposition text and do not themselves confer authority.

### D5a / D5b — independent-model neutral decomposition cohort

Run both frozen models independently with the same neutral prompt: decompose the exact root into two to four jointly necessary, independently auditable propositions with no semantic additions/removals and preserve all scope/negation/numbers/modality/conditions/exceptions. Neither generator sees retrieval gold, downstream expected verdicts, or the other generator output before both outputs are frozen.

- D5a: FLAN-T5-small pin above
- D5b: SmolLM2-360M-Instruct pin above

These are separate model-generation executions, not a claim of context-free supervisor independence. The local context-free/Conduit execution surface is unavailable for this run; no stronger clean-room label may be used.

### D6 — deliberate over-decomposition negative control

Use the predecessor frozen A4 child texts exactly.

The frozen A3 meaning-drift treatment remains historical evaluator-only evidence and is not used as a candidate production strategy.

## Fresh generation firewall

Before any new retrieval run:

1. construct a generation-input artifact containing only exact root propositions, allowed source representations, case IDs and strategy prompts;
2. hash it;
3. run D3, D4, D5a and D5b without loading `gold/`, expected retrieval outputs, predecessor RESULTS, or the other model's output;
4. materialize and validate every Contract A object;
5. hash the complete generated decomposition/Contract A fixture set;
6. only then begin retrieval.

Failed model generation or parse is retained as a valid `failed` decomposition state, not regenerated after observing retrieval.

## Retrieval arms for each declared decomposition

For each retriever (`semantic` primary, `bm25` secondary control), strategy and case:

- **R0 — root only:** exact Contract A root query.
- **R1 — children only:** every exact declared child queried independently; child lanes retained.
- **R2 — typed root + children:** exact root plus every exact child; every lane retained independently. Physical passage dedupe is allowed only if every `(proposition_id, proposition_role, retrieval_lane, passage_id)` relationship survives.
- **R3 — flattened root + children control:** exactly the same R2 physical passage set, but proposition/retrieval-lane attribution is removed in the research projection. R3 is never a proposed default.

No retrieved passage may be silently attributed from one proposition to another.

## Budget comparisons

### Equal-total budget

Use the case's frozen K as the total requested candidate positions in each arm:

- R0: K to root.
- R1: divide K deterministically across N children using quotient/remainder in child sequence order.
- R2/R3: divide K deterministically across root + N children using quotient/remainder in root-then-child sequence order.

This tests representation rather than purchased capacity.

### Equal-per-query capacity

Every active root/child query receives K. Record total requested positions and returned candidates before/after dedupe. This tests attainable coverage and explicit cost expansion.

The two comparisons may not be collapsed into one result.

## Frozen raw retrieval record

The gold-blind retrieval runner must preserve, for every case/strategy/retriever/budget/arm:

- exact Contract A handoff/root/decomposition/child/source identities;
- each query lane and requested depth;
- full per-lane ranked hits and scores;
- physical candidate union;
- all proposition-role/retrieval-lane relationships for every hit;
- root-only, child-only and both-hit passage identities;
- duplicate burden;
- source diversity;
- requested and returned candidate cost;
- exact flattened R3 projection derived from the same R2 physical set.

Raw retrieval must be written and SHA-256 frozen before the analyzer opens dev relevance annotations.

## Retrieval measurements

The posthoc analyzer reports at minimum:

- decisive evidence recall;
- joint-group/root coverage;
- decisive qualifier recovery;
- decisive exception recovery;
- decisive counterevidence recovery when present in this frozen cohort, otherwise `NOT_ESTIMABLE_IN_COHORT`;
- hard-negative burden;
- duplicate burden;
- source diversity;
- passages only root finds;
- passages only children find;
- passages both find;
- R2 marginal information gain over R1 and R0;
- candidate/search cost of that gain;
- cases where root retrieval adds hard negatives without decisive gain;
- cases where decomposition lowers decisive/joint coverage;
- over-decomposition harm.

Recall is not sufficient for success if noise/cost grows without bounded information gain.

## Decomposition-faithfulness analysis

Semantic-faithfulness analysis is separate from retrieval evaluation and may not infer correctness from retrieval performance.

Use the following frozen instruments:

1. bidirectional NLI between exact root and the conjunction of exact children with:
   `cross-encoder/nli-deberta-v3-small@fa2804872c3b4bd748f38c0185cc85775361e735`;
2. exact critical-feature retention checks for numeric values, dates/temporal markers, explicit negation, modal/deontic markers, condition/exception markers, and named/alphanumeric scope/entity tokens;
3. independent-auditability and redundancy measures over child text;
4. pairwise generator disagreement / decomposition-text Jaccard.

NLI and heuristics are instruments under test, not Contract A authority. Report their raw scores and disagreements. A decomposition with better retrieval but a material faithfulness-instrument failure is not counted as a semantically safe retrieval success.

## Downstream CAL-facing probe gate

Only after the retrieval artifact and decomposition-faithfulness artifact are frozen may a bounded CAL-facing probe run.

If the current Contract B 1.2.0 + CAL interfaces can carry separate explicit root/child proposition units and common Contract A lineage without minting authority, compare:

1. child-specific audits with child-specific evidence;
2. exact-root audit with root-specific evidence;
3. root + children as distinct proposition units with explicit common lineage;
4. flattened-evidence control.

If canonical Contract B/CAL cannot carry the necessary distinction, record that exact representation boundary instead of inventing a schema or aggregation rule.

Preserve disagreements. No root-over-child or child-over-root override rule may be invented.

## Primary architectural discriminators

### Parent lane earns a production role only if

Across semantically admissible decompositions, R2 shows repeatable marginal decisive/qualifier/exception/joint information over R1 that is not explained solely by extra per-query capacity, and the added hard-negative/duplicate/cost burden remains bounded enough to justify the lane.

### Parent lane remains optional/research-only if

Benefits are sparse/case-specific or available only with materially higher capacity/noise, while child retrieval remains the normative reliable minimum.

### Children-only remains supported if

Equal-total R2 does not add material information over R1 and/or root retrieval primarily adds noise.

### Role preservation is supported if

R2 and R3 have identical physical passage sets but downstream or audit-relevant proposition attribution differs materially, or if flattening destroys facts needed to state which proposition/lane discovered which passage.

## Legitimate negative outcomes

- model generators may abstain;
- strategies may converge to identical children;
- root retrieval may add no value or may hurt;
- over-decomposition may or may not hurt every case;
- NLI/heuristics may disagree;
- CAL probe may expose a representation limitation.

Do not repair a frozen treatment because its result is inconvenient.

## Stop rule

Stop after frozen generation, Contract A validation, both retrieval budget comparisons, posthoc retrieval analysis, faithfulness analysis, the bounded CAL-facing probe if representable, exact receipts, issue/PR reconciliation and synthesis input.

Do not touch sealed/test data, tune retrieval or prompts after results, change Contract A/B, invent a composition rule, change production defaults, merge this research PR, or implement the final production A→EB→B architecture here.
