# Retrieval Characterization Block B Dev RC1 — Preregistration

Status: **AUTHORIZED BOUNDED DIAGNOSTIC EXECUTION**

Class: Research Infrastructure / retrieval characterization.

This experiment does not tune against Pilot scientific gold, does not inspect Pilot 0A scientific judgments, does not change production defaults, and does not authorize production retrieval promotion.

## Authority

- RC0 frozen source: `a02a9d313816ad8302efbcbb24bca265c31473e7`
- RC1 observability/receipt repair line: PR #38
- RC1 verified code object before this preregistration: `5dde0df3dbea8de476de240f2f48d2b9c0c5b715`
- RC1 evidence-record head used as branch parent: `c4a94c164ff83e4b2b512d537f0f3a8c1d206720`
- frozen diagnostic benchmark: `eb-retrieval-assurance-rc2-v1`
- benchmark tree SHA256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`
- frozen evaluator SHA256: `c443a64a2c2dfe8c9b0decd8c0414c1e7bb1069d86d3355dd0202fa9725aff08`
- frozen thresholds SHA256: `9df75b448ff5090d9bd2821f624e327d47ba5ea9848460cf69518bb6b04ea05a`

## Why this is the next slice

The diagnostic evaluator already exists and was adversarially challenged at E3 for the bounded apparatus-handoff decision. A historical real-EB BM25 run against RC2 was falsified, but it used SUT `c8189c31...` and predates the current semantic/hybrid control surface.

The smallest useful current experiment is therefore not another evaluator. It is a fixed, non-tuned retrieval-family comparison using the current retrieval machinery on the already frozen **dev** diagnostic split.

The sealed RC2 split is not used in this first current-stack comparison.

## Experimental question

Under one frozen synthetic diagnostic corpus and one fixed output budget per case, how do the current lexical, pinned semantic-only, and pinned hybrid retrieval families differ on the RC2 dev challenge families?

This experiment is descriptive. It does not search for a winner or global optimum.

## Arms

For every dev case, let `K` equal the benchmark-provided `maximum_passages`.

### B1 — BM25

- production `BM25Retriever`
- query: case claim text verbatim
- lexical candidate budget: `K`
- output budget: `K`
- score floor: `0.0`

### B2 — semantic-only

- production `SemanticIndex`
- model: `BAAI/bge-small-en-v1.5`
- immutable revision: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- query prefix: current RC1 default `Represent this sentence for searching relevant passages:`
- semantic candidate budget: `K`
- output budget: `K`

### B3 — hybrid

- same BM25 machinery as B1
- same semantic machinery/model/revision/prefix as B2
- lexical candidate budget: `K`
- semantic candidate budget: `K`
- RRF `k=60`
- fused output budget: `K`
- reranking: disabled
- contradiction/counterevidence pass: disabled

Hybrid therefore consumes up to `2K` source-list candidate positions before fusion. That extra candidate burden is part of the observed cost and must not be hidden.

## Representation boundary

The RC2 benchmark is already frozen as presegmented passages. Each runtime passage is adapted one-to-one to a `DocumentChunk`.

This experiment therefore characterizes retrieval over frozen passage units. It does **not** establish end-to-end production ingestion/chunking behavior.

The adapter must preserve exact `source_id`, `passage_id`, and passage text so the frozen evaluator can enforce provenance identity.

## Evaluator

Use the frozen RC2 dev evaluator and thresholds unchanged.

Preserve at minimum:

- case hit@K;
- decisive annotation recall@K;
- counterevidence recall@K;
- qualifier/exception recall@K;
- complete joint-group coverage@K;
- first decisive rank / MRR inputs where present;
- hard-negative burden before first decisive hit;
- budget violations;
- provenance failures;
- scope failures;
- false completeness claims;
- answerability overclaims;
- family-level metrics.

Do not collapse the result to one scalar.

## Expected invariants

- all three arms use the same frozen dev cases, apertures, and evaluator;
- all three arms return at most benchmark `K`;
- completeness remains `not_established`;
- answerability remains `not_established`;
- no arm may inspect evaluator-only gold during retrieval;
- model revision is immutable for semantic/hybrid;
- source-order reversal must not change hit identities/ranks for BM25 under the deterministic adapter;
- output and evaluation hashes are persisted.

## Falsifiers

### Semantic-only usefulness

The hypothesis that semantic-only adds useful recovery on low lexical-overlap evidence is weakened if it does not improve R01/other low-overlap family retrieval over BM25 and adds material cost.

### Hybrid usefulness over lexical

The hypothesis that hybrid adds complementary retrieval is weakened if its family-level recall/rank behavior is indistinguishable from or materially worse than BM25 despite consuming the additional semantic candidate list.

### One-family dominance

The assumption that one retrieval family is uniformly preferable is falsified if familywise rankings conflict materially across RC2 challenge families.

## Stop conditions

Stop without interpreting retrieval quality if:

- frozen benchmark/evaluator identities do not match the recorded hashes;
- exact pinned semantic model cannot execute;
- adapter provenance cannot round-trip exactly;
- any arm exceeds its preregistered output budget;
- evaluator or thresholds must be changed to accept current outputs;
- any retrieval code reads evaluator-only gold.

## Non-claims

This experiment does not establish:

- production retrieval configuration;
- Pilot 0A performance;
- end-to-end production chunking;
- external representativeness of RC2;
- superiority of BGE or BM25 generally;
- reranking usefulness;
- counterevidence-pass usefulness;
- production promotion.

Any later geometry, fusion, reranking, or counterevidence block requires a separate preregistered slice.
