# Composite vs Decomposed Claim Retrieval Sensitivity Dev RC1 — Preregistration

Status: **AUTHORIZED BOUNDED DIAGNOSTIC EXECUTION**

Class: Research Infrastructure / Contract-A precursor experiment.

This experiment does not define or promote Contract A. It tests whether decomposition is a materially consequential intervention on retrieval before ownership or schema semantics are frozen.

It does not use Pilot scientific gold, does not expose the frozen benchmark test split, does not change production retrieval defaults, and does not authorize a production decomposition stage.

## Live authority

- Evidence Bundler main at experiment start: `6011789957f3294f97bff260069cfb5bb1c5772f`
- current research-apparatus ancestor: `d02b7c61dc0d2779f35a8fa9eb534d9c301abdd8`
- legacy Contract-A decomposition research: PR #7
- frozen decomposition benchmark source object: `22b227ec2c34a085efc79267bc007ff78607aeed`
- frozen corpus tree SHA256: `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8`
- frozen dev decomposition file SHA256: `2120228c81466471214ca8b56a6eba2fa5bc498cd0b0243ff3b8fe24c9da2144`
- frozen dev relevance file SHA256: `da5b06d78060897f85dc78a8ff45c9622c697a10fe43942ea74a688115c7fac3`

Only development decomposition cases are used. Frozen test decomposition cases and test relevance remain unopened by the experiment runner and analyzer.

## Scientific question

Holding corpus bytes, accessible source aperture, retriever/model identity, and benchmark K fixed, does replacing one composite claim query with its meaning-preserving child decomposition materially change the evidence retrieved?

A secondary question is whether any observed benefit is caused by decomposition itself or merely by granting more retrieval budget through multiple child queries.

## Decomposition variants

The frozen benchmark defines five variants for each decomposition-sensitive base claim:

- **A0** — original composite claim.
- **A1** — direct defensible meaning-preserving decomposition.
- **A2** — alternative legitimate meaning-preserving decomposition.
- **A3** — meaning-drift negative control.
- **A4** — intentionally excessive over-decomposition.

The primary causal comparison is A0 vs A1 vs A2.

A3 and A4 are controls. They must not be treated as legitimate candidate Contract-A semantics.

## Development families

Use the frozen dev decomposition-sensitive claims only, covering:

- F03 NEGATION_POLARITY;
- F04 NUMERIC_THRESHOLD;
- F05 TEMPORAL_SUPERSESSION;
- F06 CONDITION_EXCEPTION;
- F10 MULTI_PASSAGE_COMPOSITION;
- F12 APERTURE_BOUNDARY.

## Representation boundary

The frozen source documents are split into their existing blank-line-delimited paragraphs. Each paragraph becomes one deterministic research `DocumentChunk`.

Gold spans are mapped to a paragraph only when the exact frozen `span_text` is a substring of that paragraph. Ambiguous or unmapped gold is a stop condition.

This experiment therefore measures retrieval over frozen paragraph units. It does not establish end-to-end production chunking.

## Retrieval families

Run the same decomposition comparison independently with:

1. current `BM25Retriever`;
2. current pinned semantic retrieval:
   - model `BAAI/bge-small-en-v1.5`;
   - revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`;
   - semantic query prefix `Represent this sentence for searching relevant passages:`.

No hybrid fusion, reranking, contradiction pass, or counterevidence expansion is used.

## Query treatments

### C0 — composite

Issue one query using the exact A0 `original_claim_text`.

Return up to benchmark K candidates.

### D-total — decomposed, equal total retrieval budget

For A1, A2, A3, or A4, issue one query per frozen child proposition.

Distribute benchmark K deterministically across children:

- base allocation = `K // n_children`;
- first `K % n_children` children receive one additional candidate;
- children are ordered by frozen `sequence`.

The sum of requested child candidate positions is exactly K.

Deduplicate candidates by paragraph identity after retrieval. Preserve query lineage for every hit.

This treatment asks whether decomposition improves targeting when it receives no additional requested candidate positions.

### D-per-query — decomposed, equal per-query budget

Issue every child query with benchmark K.

Union and deduplicate all child results without truncating back to K.

This deliberately grants additional search capacity. It measures attainable coverage and its candidate/duplicate cost; it is not a fair same-budget performance comparison.

## Semantic ownership equivalence invariant

For A1 and A2, the exact same child texts and retrieval outputs are interpreted in two metadata-only ways:

- **first-class-proposition interpretation**: each child is an audit proposition with parent lineage;
- **query-expansion interpretation**: the original claim remains the sole audit target and the children are retrieval queries only.

The retrieval identity set, ranks per child query, and union candidate set must be byte-identical between these interpretations.

This is an invariant, not a performance arm. If it holds, retrieval performance alone cannot decide where decomposition belongs architecturally.

## Gold boundary

Retrieval generation may read:

- frozen source contents;
- frozen dev cases;
- frozen dev decomposition records;
- frozen aperture subsets.

It must not read relevance gold.

A separate posthoc analyzer may read frozen **dev relevance** only after all raw retrieval artifacts are written.

## Measurements

For each retriever, variant, base claim, and budget regime preserve:

- decisive paragraph recall;
- source-level decisive recall;
- counterevidence/contradiction/exception decisive recall where represented;
- complete joint-group coverage;
- case hit;
- first decisive rank where meaningful;
- requested candidate positions;
- unique returned candidates;
- duplicate burden across child queries;
- no-hit child count;
- evidence identities unique to composite retrieval;
- evidence identities unique to decomposition;
- Jaccard overlap between composite and decomposed evidence sets;
- child-level evidence coverage;
- proposition-complete coverage for A1/A2;
- family-level behavior.

Do not compress these into one scalar.

## Primary estimands

### Equal-budget decomposition effect

For A1 and A2 under D-total, compare against C0 at the same total requested candidate budget K.

### Additional-search-capacity effect

For A1 and A2, compare D-per-query against D-total. This quantifies how much apparent decomposition gain comes from extra search opportunities rather than target representation.

### Legitimate-decomposition sensitivity

Compare A1 against A2. Material evidence-world differences between two meaning-preserving decompositions strengthen the case that decomposition lineage is consequential.

### Negative-control sensitivity

A3 should be allowed to differ. The experiment asks whether retrieval is sensitive to meaning drift, not whether A3 performs "better."

### Fragmentation cost

A4 tests whether excessive decomposition increases duplicate/no-hit burden or loses decisive/joint evidence.

## Falsifiers

### First-class decomposition necessity from retrieval alone

Weakened if A1/A2 do not materially change same-budget retrieval relative to A0, or if all apparent gains disappear after equalizing total candidate budget.

### Decomposition as retrieval aid

Weakened if D-total fails to improve any relevant coverage dimension and materially increases no-hit/duplicate burden.

### Decomposition harmlessness

Falsified if A1/A2 materially alter evidence identities, decisive coverage, or complete joint-group coverage under equal total budget.

### Ownership inference from retrieval

Falsified by construction if the ownership equivalence invariant passes: identical child queries must yield identical retrieval regardless of whether metadata calls them audit propositions or query expansion. Architectural ownership then requires downstream semantic evidence, not retrieval performance alone.

## Stop conditions

Stop before scientific interpretation if:

- frozen corpus/decomposition/dev-gold hashes do not match;
- any dev gold span cannot be mapped uniquely to one frozen paragraph;
- the exact pinned semantic model cannot execute;
- retrieval generation reads dev relevance;
- D-total requested candidate positions exceed K;
- A1/A2 ownership interpretations produce different retrieval bytes;
- test-split decomposition or test relevance is accessed.

## Non-claims

This experiment does not establish:

- that decomposition is semantically correct;
- who should own decomposition;
- a Contract-A schema;
- production query-planning behavior;
- optimal decomposition granularity;
- production retrieval defaults;
- Pilot performance;
- external-corpus generalization.

The intended decision is narrower: determine whether decomposition is consequential enough that Contract A should remain unfrozen until its identity/lineage role is understood.
