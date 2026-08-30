# Semantic 4K → MiniLM Rerank → K Dev RC1 — Preregistration

Status: **AUTHORIZED BOUNDED DIAGNOSTIC EXECUTION**

Class: Research Infrastructure / reranking characterization.

This task does not use Pilot scientific gold, does not use the RC2 sealed split, does not change production defaults, and does not authorize production promotion.

## Starting evidence

The frozen RC2 dev candidate-pool aperture diagnostic established that the exact pinned BGE semantic pool at 4K contains:

- 100% accessible decisive annotations;
- 100% counterevidence;
- 100% qualifier/exception evidence;
- 100% complete joint groups;
- every answerable dev case, including R06.

Therefore the intended reranker receives a candidate pool in which all decisive dev evidence is already present.

## Frozen authority

- benchmark tree SHA256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`
- split: **dev only**
- embedding model: `BAAI/bge-small-en-v1.5`
- embedding revision: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- semantic query prefix: `Represent this sentence for searching relevant passages:`
- semantic candidate depth: **4K**
- reranker: `cross-encoder/ms-marco-MiniLM-L6-v2`
- reranker revision: `233902d25c440f23af6f7d6e94d2946bac0bee0a`
- final output depth: benchmark-provided **K**

No parameter search is permitted.

## Experimental question

Can the current pinned parent-level cross-encoder compress the complete semantic 4K dev aperture back to K while retaining more decision-relevant evidence than raw semantic K?

## Arm

For each dev case:

1. construct the same one-frozen-passage → one-`DocumentChunk` representation used in Block B;
2. retrieve semantic top `4*K` using the exact pinned BGE model/revision/prefix;
3. convert the semantic candidates to current `CandidateEvidence` objects without reading gold;
4. rerank all available 4K candidates with current `ParentReranker` using the exact pinned MiniLM revision;
5. emit only top K;
6. evaluate with the unchanged frozen RC2 dev evaluator.

No BM25 fusion.
No RRF.
No contradiction-query expansion.
No text-role gate.
No counterevidence-specific query.
No threshold changes.

## Baseline

The comparison baseline is the already frozen raw semantic-K Block B dev result:

- result SHA256: `632c727928e49257c4a5840b9325b742be9225a4bbfbbcfa1cbffd6bbeeaf922`
- evaluation SHA256: `fb6673a3c90512f7fd4c2f732b5a669bd1a064017b5e0c4eb87f8be1007db6f8`
- case hit@K: 0.642857
- decisive recall@K: 0.500000
- counterevidence recall@K: 0.000000
- qualifier/exception recall@K: 0.000000
- joint-group coverage@K: 0.000000
- first-decisive MRR: 0.500000

## Measurements

Preserve:

- case hit@K;
- decisive annotation recall@K;
- counterevidence recall@K;
- qualifier/exception recall@K;
- complete joint-group coverage@K;
- first-decisive MRR;
- hard-negative hits and hard negatives before first decisive;
- family-level metrics;
- provenance/scope/budget/shape violations;
- semantic candidate count;
- reranker pair count;
- exact model revisions;
- result/evaluation hashes;
- execution receipt.

## Falsifiers

### Reranker usefulness

The reranker-usefulness hypothesis is weakened if it does not improve at least one decision-relevant retrieval dimension without a material compensating loss elsewhere.

### Counterevidence critical falsifier

R02 is critical. All R02 counterevidence is present in the semantic 4K pool. If the reranker still produces poor R02 counterevidence recall at K, that is evidence that generic relevance reranking does not preserve counterevidence adequately.

### Joint evidence

R03/R04/R05 are ranking-opportunity families because their complete evidence is present before reranking. Failure to recover complete joint groups after reranking is an ordering/compression failure.

### Distractor-heavy R06

R06 decisive evidence is present only by semantic 4K. If reranking cannot elevate it into K, the current reranker does not solve the observed distractor-heavy ranking problem.

## Stop conditions

Stop without interpreting reranker quality if:

- frozen benchmark identity changes;
- exact pinned model revision cannot load;
- candidate generation reads dev gold;
- candidate pool is not exactly bounded to 4K before reranking;
- evaluator or thresholds require modification;
- any output provenance cannot round-trip exactly.

## Non-claims

This experiment does not establish:

- optimal semantic depth;
- optimal rerank depth;
- production reranking;
- general MiniLM superiority;
- counterevidence-pass usefulness;
- sealed generalization;
- Pilot performance;
- production promotion.
