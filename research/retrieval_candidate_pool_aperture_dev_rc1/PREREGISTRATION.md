# Retrieval Candidate-Pool Aperture Dev RC1 — Preregistration

Status: **AUTHORIZED BOUNDED DIAGNOSTIC EXECUTION**

Class: Research Infrastructure / retrieval characterization.

This is the immediate successor to Block B dev RC1. It does not tune against Pilot scientific gold, does not use the RC2 sealed split, does not change production defaults, and does not authorize reranking or production promotion.

## Starting evidence

Block B dev RC1 at exact implementation `7383407b58e78fad9d090482037a5ff86fb74a9e` found:

- BM25: case hit@K 0.5714; decisive recall@K 0.4545; counterevidence recall@K 1.0.
- semantic-only: case hit@K 0.6429; decisive recall@K 0.5000; counterevidence recall@K 0.0.
- hybrid: case hit@K 0.7143; decisive recall@K 0.5455; counterevidence recall@K 0.5.
- all three: qualifier/exception recall 0.0; complete joint-group coverage 0.0; R06 distractor-heavy case hit 0.0.

Those results do not distinguish candidate-generation failure from final-K ranking/truncation failure.

## Frozen authority

- benchmark: `eb-retrieval-assurance-rc2-v1`
- benchmark tree SHA256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`
- dev split only
- BGE model: `BAAI/bge-small-en-v1.5`
- immutable BGE revision: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- semantic query prefix: `Represent this sentence for searching relevant passages:`
- BM25 score floor: `0.0`

## Question

For evidence missed at final K in Block B, does the decisive evidence enter the lexical pool, semantic pool, or their union at K, 2K, or 4K?

This is a candidate-aperture diagnostic, not a ranking optimization.

## Pools

For each RC2 dev case with benchmark output budget `K`:

- lexical pool: top `m*K` from current `BM25Retriever`;
- semantic pool: top `m*K` from current pinned `SemanticIndex`;
- union pool: set union of the lexical and semantic pools at the same multiplier.

Preregistered multipliers: **1, 2, 4**.

No reranking. No RRF. No contradiction expansion. No counterevidence query expansion. No score-floor search.

If a retriever returns fewer candidates than requested under its fixed semantics, preserve that fact.

## Gold boundary

Candidate generation is gold-blind and reads only:

- runtime passages;
- dev cases;
- apertures.

A separate analyzer may read evaluator-only **dev** gold only after the raw candidate-pool artifact is written.

The analyzer must not modify candidate pools.

## Measurements

At each multiplier and for lexical, semantic, and union pools, preserve:

- decisive annotation pool recall;
- counterevidence pool recall;
- qualifier/exception pool recall;
- complete joint-group pool coverage;
- case hit rate;
- family-level decisive pool recall;
- actual candidate count / requested candidate count;
- hard-negative count where available.

No scalar composite score.

## Falsifiers / discriminators

### Candidate-generation failure

A family is candidate-generation limited for a retriever if decisive evidence remains absent at 4K.

### Ranking/truncation opportunity

A family is potentially ranking-limited if decisive evidence is absent at K but present at 2K or 4K.

This only establishes that a reranker could have something to rescue. It does not establish that the current reranker can do so.

### Complementarity

Lexical/semantic complementarity is supported if the union pool materially exceeds both component pools on the same family and multiplier.

### Reranking stop rule

Do **not** begin a reranker experiment for a failure family if the decisive evidence is still absent from the intended rerankable pool at 4K.

## Non-claims

This experiment does not establish:

- optimal candidate budget;
- production top-K;
- reranker usefulness;
- fusion usefulness;
- counterevidence-pass usefulness;
- end-to-end chunking;
- Pilot performance;
- production promotion.
