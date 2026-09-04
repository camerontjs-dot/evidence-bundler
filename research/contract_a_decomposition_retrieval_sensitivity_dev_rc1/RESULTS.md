# Composite vs Decomposed Claim Retrieval Sensitivity Dev RC1 — Results

Status date: 2026-08-29 / 2026-08-30 UTC

Research disposition: **DECOMPOSITION_IS_RETRIEVAL_CONSEQUENTIAL_BUT_OWNERSHIP_UNRESOLVED**

Contract-A disposition: **DO_NOT HARDEN DECOMPOSITION OWNERSHIP YET**

Production disposition: **NO PROMOTION**

## OBSERVED — authority and receipts

- legacy Contract-A research: PR #7
- experiment PR: #43
- frozen decomposition benchmark source: `22b227ec2c34a085efc79267bc007ff78607aeed`
- frozen corpus tree SHA256: `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8`
- frozen dev decomposition SHA256: `2120228c81466471214ca8b56a6eba2fa5bc498cd0b0243ff3b8fe24c9da2144`
- frozen dev relevance SHA256: `da5b06d78060897f85dc78a8ff45c9622c697a10fe43942ea74a688115c7fac3`
- preregistration commit: `9ea0c2b4b1d565c2a28404693778376f2a06bf50`
- exact decisive tested implementation: `55d158f829f4aad1ed8ad69b19d9e39d445c953d`
- exact decisive tree: `56657ceddf203d6ef03d60bb01e853dd4b247050`
- decisive workflow run: `33286415682`
- decisive job: `99190260567`
- artifact: `9724593640`
- artifact digest: `sha256:de37750385594fd00f683e5ca67cbe1fe2ef29e19dcb41d754b431fbb8c5c21b`
- raw gold-blind retrieval SHA256: `b7522a147f1dccd1614bb8dcb4565b8a8834bee4cf2d47695befeb311ebd6680`
- analysis SHA256: `04616ee0cab1a2f0fe26494350389cab2e618e0f80f622201af0e7ccc2e415cd`
- compact comparison SHA256: `9c96caa3bf8c7979f1019d8fe2740d5b518d9785f2aa5927f2df0bd7893b52ad`

Only the frozen development decomposition split was used. The frozen test decomposition and test relevance objects were not accessed by the runner or analyzer.

## OBSERVED — preserved pre-execution deviations

Several apparatus defects were discovered and preserved before any scientific retrieval artifact existed.

1. The first run used an invalid semantic-index corpus-hash representation (`sha256:<digest>:subset`). It stopped in the full test suite before retrieval.
2. The first attempted repair accidentally wrote literal escaped newline sequences into the Python source. Test collection stopped before retrieval.
3. The corrected source then passed **224 tests, 5 skipped** and the two experiment tests but Ruff stopped execution on formatting/lint findings.
4. A remaining one-line Ruff violation stopped another exact head after **224 passed, 5 skipped** and **2 experiment tests passed**.

Only representation/formatting defects were repaired. No decomposition text, budget rule, corpus, gold, retriever identity, model revision, success criterion, or comparison arm changed after preregistration.

## OBSERVED — decisive validation

On exact head `55d158f8...`:

- full deterministic suite: **224 passed, 5 skipped**;
- explicit decomposition apparatus tests: **2 passed**;
- Ruff: **clean**;
- frozen development treatment hashes: **pass**;
- no-test-split / gold-blind runner firewall: **pass**;
- exact pinned BGE execution: **pass**;
- raw retrieval artifact written before dev relevance analysis: **pass**;
- ownership-equivalence runner invariants: **48/48**;
- primary A1/A2 ownership-equivalence analysis checks: **24/24 identical**.

## OBSERVED — experimental population

Six frozen development base claims were used:

| Claim | Family | Aperture |
| --- | --- | --- |
| claim-009 | F03 NEGATION_POLARITY | distractor_heavy |
| claim-013 | F04 NUMERIC_THRESHOLD | distractor_heavy |
| claim-017 | F05 TEMPORAL_SUPERSESSION | full |
| claim-021 | F06 CONDITION_EXCEPTION | ordinary_window |
| claim-037 | F10 MULTI_PASSAGE_COMPOSITION | full |
| claim-049 | F12 APERTURE_BOUNDARY | bounded_missing_decisive |

For claim-049, decisive evidence is deliberately absent from the accessible aperture, so accessible decisive recall is undefined. Paired decisive-recall comparisons therefore contain five claims.

## OBSERVED — equal-total-budget primary result

Every A1/A2 decomposed treatment received exactly the same **12 requested candidate positions total** as the corresponding composite query.

### BM25

For both legitimate decompositions A1 and A2:

- decisive recall improved: 0/5;
- worsened: 0/5;
- tied: 5/5;
- mean decisive-recall delta: 0.0.

Giving each child K instead of sharing K also produced no decisive-recall improvement.

However, identical decisive recall did **not** imply identical evidence worlds.

Relative to the composite BM25 result, mean same-budget evidence-set Jaccard was:

- A1: approximately **0.529**;
- A2: approximately **0.561**.

A1 and A2 themselves were more similar under BM25, with mean same-budget Jaccard approximately **0.894**, but were not universally identical.

### Pinned semantic retrieval

A1 direct decomposition:

- improved decisive recall: **1/5**;
- worsened: 0/5;
- tied: 4/5;
- mean decisive-recall delta: **+0.10**;
- median delta: 0.0.

A2 alternative legitimate decomposition:

- improved: 0/5;
- worsened: 0/5;
- tied: 5/5;
- mean delta: 0.0.

The exact sign-flip diagnostic for A1 is 1.0 because there is only one non-zero paired effect. With five scored pairs this is descriptive mechanism evidence, not a population-level significance claim.

## OBSERVED — decisive counterexample: F10 multi-passage composition

The strongest treatment effect is claim-037:

> The Morrow-2 quarantine rack quarantine release requires a temperature check below 3.3 degrees C, and a signed identity match is required before movement.

Raw pinned semantic retrieval on the composite query:

- decisive paragraph recall: **0.5**;
- complete joint-group coverage: **0.0**.

A1 direct decomposition, under the same total K=12 requested candidate positions:

1. temperature check below 3.3 degrees C;
2. signed identity match before movement.

Result:

- decisive paragraph recall: **1.0**;
- complete joint-group coverage: **1.0**.

A2 is also marked meaning-preserving, but adds explicit scope language to both children. Under the same total budget:

- decisive paragraph recall remains **0.5**;
- complete joint-group coverage remains **0.0**.

Thus two frozen, legitimate, meaning-preserving decompositions of the same parent claim create materially different retrieval outcomes under the same retriever, corpus, aperture, model, and total requested budget.

For semantic same-budget A1 versus A2 across all six dev base claims:

- mean evidence-set Jaccard: approximately **0.523**;
- mean A1-only paragraph identities: approximately **3.83**;
- mean A2-only identities: approximately **4.17**.

The most divergent legitimate-decomposition cases include:

- F06 CONDITION_EXCEPTION: Jaccard approximately 0.278;
- F10 MULTI_PASSAGE_COMPOSITION: Jaccard approximately 0.263.

This is evidence-world sensitivity, not merely a score difference.

## OBSERVED — extra search capacity does not explain the A1 gain

The legitimate A1/A2 records contain two children, so:

- equal-total treatment: 12 requested positions total;
- equal-per-query treatment: 24 requested positions total.

For both BM25 and semantic retrieval, the paired decisive-recall outcomes for A1/A2 were unchanged when moving from equal-total to equal-per-query.

The semantic A1 F10 improvement therefore already occurs at the **same total requested candidate budget** as the composite query.

The additional per-query budget substantially expands the evidence set without improving decisive recall on this dev slice:

- BM25 A1 mean unique candidates: about 10.7 at total-K vs 21.7 at K-per-child;
- semantic A1: about 11.5 vs 23.3;
- semantic A2: about 11.8 vs 23.7.

This separates a representation effect from a simple "more queries means more budget" explanation for the observed A1 F10 gain.

## OBSERVED — over-decomposition control

A4 intentionally fragments the parent into excessively small pieces.

Under pinned semantic retrieval and the same total requested budget:

- worsened decisive recall: **1/5**;
- improved: 0/5;
- tied: 4/5;
- mean decisive-recall delta: **-0.20**.

The concrete failure is F03 claim-009:

- composite semantic decisive recall: **1.0**;
- over-decomposed A4 decisive recall: **0.0**.

A4 also creates much more divergent evidence sets. Mean same-budget semantic Jaccard versus the composite is approximately **0.153**.

This supports a real fragmentation cost. It does not establish an optimal decomposition granularity.

## OBSERVED — meaning-drift control

A3 intentionally changes the parent meaning. Its relevance semantics are not directly comparable to A0, so it is not assigned a paired decisive-recall effect.

The retrieval sets nevertheless change in multiple cases under fixed budget, as expected for a semantic mutation. This control does not by itself validate retrieval sensitivity to every material meaning change.

## OBSERVED — ownership-equivalence discriminator

For every legitimate A1/A2 child-query plan, the exact same child texts/results were represented in two metadata-only interpretations:

1. first-class child audit propositions with parent lineage;
2. retrieval query expansion under one original audit target.

All **24 primary checks were byte-identical**.

This is an important falsifier:

> Retrieval behavior alone cannot determine whether decomposition belongs in Contract A or inside EB query planning when the actual child query texts are identical.

Calling a string an "audit proposition" rather than a "retrieval query" does not change BM25 or BGE retrieval.

## INFERENCE — what is supported

### Decomposition harmlessness is falsified

Decomposition is not safely characterizable as invisible, inconsequential preprocessing.

Even when decisive recall ties, the evidence identities can change substantially. For pinned semantic retrieval, legitimate A1/A2 same-budget evidence worlds differ materially.

The F10 A1 counterexample goes further: decomposition changes complete decision-relevant evidence coverage under equal total budget.

### A universal "decompose first" rule is not supported

A1 helps one semantic dev case, A2 does not, BM25 receives no decisive-recall benefit, and over-decomposition can destroy retrieval.

Therefore the evidence does not justify a production rule that all composite claims should be decomposed.

### First-class lineage is more justified than first-class ownership

Because legitimate decompositions can create different evidence worlds, any decomposition that does occur should be attributable and reconstructable.

But the ownership-equivalence result means this experiment cannot tell us whether:

- Contract A should contain child audit propositions; or
- Contract A should preserve only the original audit target while EB records derived child retrieval queries and their transformation lineage.

The retrieved evidence is identical when the query strings are identical.

### The decomposition producer is potentially consequential

A1 and A2 are both frozen as meaning-preserving, yet the current semantic retriever treats them differently in F10 and their same-budget candidate sets differ substantially.

Therefore "a decomposition exists" is not enough identity. The exact decomposition artifact/text/producer lineage can matter.

## HYPOTHESIS

The architectural discriminator is downstream of retrieval.

If CAL or another downstream consumer must assess proposition-level completeness, combine evidence across children, or preserve distinct epistemic states for each child proposition, decomposition likely needs first-class semantic identity upstream of EB.

If the same downstream semantics can be reconstructed from one original audit target plus attributable EB query lineage, decomposition may remain query planning rather than Contract-A semantics.

## UNKNOWN

This dev-only synthetic experiment does not establish:

- population-level decomposition benefit;
- test/holdout generalization;
- real-corpus decomposition behavior;
- semantic correctness of A1/A2;
- who should produce decomposition;
- whether CAL requires proposition-level identity;
- an optimal decomposition algorithm or granularity.

The frozen test decomposition split remains unused.

## NEXT

Before hardening Contract A, run a **decomposition ownership/consequence conformance experiment** with retrieval held fixed.

Use the exact same A1/A2 child query texts and exact same retrieved evidence, then compare two downstream representations:

1. **query-lineage representation:** one original audit target; child strings are EB retrieval queries only;
2. **proposition-lineage representation:** children are explicit audit propositions linked to the parent.

The discriminating question is whether downstream evidence attribution, completeness accounting, CAL consumption, Contract-B identity, or epistemic state becomes ambiguous or non-equivalent.

If those downstream results remain equivalent, keep Contract A smaller and place decomposition in attributable EB query planning.

If they diverge for principled semantic reasons, that is direct evidence for first-class decomposition identity in Contract A.

Do not harden decomposition ownership from the retrieval result alone.
