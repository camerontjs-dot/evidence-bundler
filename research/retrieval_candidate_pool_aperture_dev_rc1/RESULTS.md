# Retrieval Candidate-Pool Aperture Dev RC1 — Results

Status date: 2026-08-29 / 2026-08-30 UTC

Research disposition: **RANKING_APERTURE_IDENTIFIED**

Production disposition: **NO PROMOTION**

## OBSERVED — authority and receipts

- preregistration commit: `7e2e7e11cfba4baa380e4060adce07525e3d3f05`
- first execution head: `21bc6fed561491d28a8e6d54a5db229668f5840e`
- first run: `33282654922`
- first-run artifact: `9723454795`
- decisive corrected head: `8ef9edcfbe12c8a5066f1b1dcce9e45a1718288e`
- decisive tree: `05cebeb85530d5e58ddcd9dc585beb29b52db688`
- decisive workflow run: `33282745386`
- decisive job: `99180565050`
- decisive artifact: `9723482406`
- decisive artifact digest: `sha256:1f07f1ebb1d05ea765368b8b73d2ba19b31dc1f933e70c6a0d060f58525c57b1`
- candidate artifact SHA256: `ba55593cb3151b6c3a559cf1bf4b62ac40d25797d14e4d6a852f6056fa6c5d64`
- analysis SHA256: `aaffd8f2a9e2e56bd6362dbbe0b6528022256072dc526c67d5f144acbad6cc45`

Frozen benchmark identity remained:
`0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`.

## OBSERVED — preserved execution deviation

The first run passed:

- frozen benchmark identity;
- mechanical gold-blind generator check;
- full tests;
- dedicated pool-boundary test;
- Ruff.

It then failed at the start of gold-blind candidate generation with:

`ModuleNotFoundError: No module named 'research'`

Cause: the script was invoked directly while importing a sibling research namespace. No candidate artifact and no gold analysis existed.

The only correction changed workflow invocation from direct script execution to Python module execution. Candidate logic, multipliers, benchmark, model identity, scoring, gold boundary, and preregistered criteria did not change.

## OBSERVED — decisive validation

On the corrected exact head:

- full suite: **220 passed, 5 skipped**;
- pool boundary test: **1 passed**;
- Ruff: **clean**;
- frozen benchmark identity: **pass**;
- gold-blind generator gate: **pass**;
- candidate generation: **pass**;
- posthoc dev-gold analysis: **pass**.

The raw candidate artifact was written before dev gold was read.

## OBSERVED — pool aperture

### K pools

| Measure | Lexical | Semantic | Union |
| --- | ---: | ---: | ---: |
| Case hit rate | 0.5714 | 0.6429 | **0.7857** |
| Decisive pool recall | 0.4545 | 0.5000 | **0.6818** |
| Counterevidence pool recall | **1.0000** | 0.0000 | **1.0000** |
| Qualifier/exception pool recall | 0.0000 | 0.0000 | 0.0000 |
| Complete joint-group pool coverage | 0.0000 | 0.0000 | **0.3333** |
| Actual candidate count | 22 | 40 | 45 |
| Hard negatives | 12 | 29 | 30 |

At K, lexical and semantic are materially complementary. The union recovers more decisive evidence than either component alone.

### 2K pools

| Measure | Lexical | Semantic | Union |
| --- | ---: | ---: | ---: |
| Case hit rate | 0.7143 | **0.8571** | **0.8571** |
| Decisive pool recall | 0.7273 | **0.9091** | **0.9091** |
| Counterevidence pool recall | 1.0000 | **1.0000** | **1.0000** |
| Qualifier/exception pool recall | 0.5000 | **1.0000** | **1.0000** |
| Complete joint-group pool coverage | 0.6667 | **1.0000** | **1.0000** |
| Actual candidate count | 30 | 58 | 58 |
| Hard negatives | 14 | 38 | 38 |

At 2K, semantic contains all counterevidence, qualifier/exception, and joint-group evidence, but still misses both R06 decisive items.

### 4K pools

| Measure | Lexical | Semantic | Union |
| --- | ---: | ---: | ---: |
| Case hit rate | 0.7143 | **1.0000** | **1.0000** |
| Decisive pool recall | 0.7273 | **1.0000** | **1.0000** |
| Counterevidence pool recall | 1.0000 | **1.0000** | **1.0000** |
| Qualifier/exception pool recall | 0.5000 | **1.0000** | **1.0000** |
| Complete joint-group pool coverage | 0.6667 | **1.0000** | **1.0000** |
| Actual candidate count | 30 | 60 | 60 |
| Hard negatives | 14 | 38 | 38 |

At 4K, the semantic pool contains every accessible decisive annotation on the RC2 dev split.

The lexical pool saturates before 4K because fixed BM25 score-floor semantics return no additional positive-scoring candidates for several challenge cases.

## OBSERVED — family discriminators

- **R01 low-overlap:** both lexical and semantic reach 1.0 decisive pool recall by 2K. The K miss is a rank/cutoff problem for both.
- **R02 counterevidence:** semantic goes from 0.0 at K to 1.0 at 2K. The evidence exists in the semantic ranking, but below K.
- **R03 qualifier joint pair:** lexical remains stuck at 0.5 even at 4K; semantic reaches 1.0 at 2K. Semantic candidate generation is necessary for the missing qualifier.
- **R04 exception pair:** both reach 1.0 at 2K.
- **R05 multi-source composition:** both reach 1.0 at 2K.
- **R06 distractor-heavy bounded K:** both are 0.0 at 2K. Lexical remains 0.0 at 4K, while semantic jumps to **1.0 at 4K**.
- **R08 provenance twin:** lexical remains 0.0 even at 4K; semantic is 1.0 already at K.

## INFERENCE

### Reranking opportunity

A reranker now has a valid opportunity on the semantic 4K pool: the frozen dev diagnostic shows that every decisive item is present before reranking.

Therefore a failure of a fixed reranker to recover those items into final K would be a reranking/order failure, not a candidate-absence explanation.

### Lexical limitation

BM25 has candidate-generation limitations on R03 and R08 under its fixed score-floor semantics. Increasing lexical K alone cannot recover those missing items.

### Semantic limitation

The current BGE semantic path is primarily a ranking-depth problem on this dev challenge, not an absolute candidate-generation failure. Its strongest failure is R06, whose decisive evidence appears only between 2K and 4K.

### Union behavior

At 2K and 4K, the union has the same aggregate candidate count and recall as the semantic pool. On this small frozen challenge, the lexical candidates are effectively contained within the broader semantic aperture by those depths.

That does not establish semantic dominance generally; it only means union expansion adds no additional candidate identities beyond semantic at these dev depths.

## HYPOTHESIS

A fixed cross-encoder reranker over the 4K semantic pool may compress the complete candidate aperture back to final K while retaining more decisive/joint evidence than raw semantic K.

The strongest falsifier is R02: a generic relevance reranker may prefer supportive lexical similarity and push counterevidence back out of final K even though it is present in the candidate pool.

## NEXT

Run one fixed **semantic-4K → MiniLM rerank → K** dev diagnostic:

- exact same RC2 dev split;
- semantic candidate pool fixed at 4K;
- exact BGE revision unchanged;
- reranker fixed to `cross-encoder/ms-marco-MiniLM-L6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a`;
- output budget remains benchmark K;
- no parameter search;
- no contradiction-query expansion;
- compare to the already frozen raw semantic-K result;
- preserve R02 counterevidence behavior as a critical falsifier.

Do not proceed to sealed execution or production promotion from that result.
