# Evidence Bundler Retrieval Generalization RC4 — Target Preregistration

## PR class
Research / Draft / preregistered target experiment.

## Decision
Determine whether the already-existing frozen Evidence Bundler Hybrid retrieval path materially improves fresh meaning-preserving low-lexical-overlap retrieval over the exact frozen production BM25 baseline while preserving a separately demonstrated fresh BM25 counterevidence capability.

This is a new RC4 target record. It does not retarget or rewrite RC3 PR #15 or apparatus PR #16.

## Predecessor evidence
- PR #14: exact production BM25 RC2 measurement, terminal `FALSIFIED` for the bounded RC2 retrieval gate. Strong RC2 counterevidence recall was observed at 1.0.
- PR #15: RC3 Hybrid preregistration, blocked before target exposure.
- PR #16: RC3 apparatus, terminal `FALSIFIED` because a runtime-only construction-cue gamer cleared the intended target gate; fresh RC3 C01 BM25 counterevidence recall was only 0.3125.

RC3 remains frozen and rejected. No RC3 Hybrid or Semantic-only sealed output was produced.

## Exact frozen target identity
Production-source Evidence Bundler SHA: `c8189c31adbab11729c31430c2070126224a2d42`.

Primary candidate: existing production `hybrid` retrieval path only.

- embedding model: `BAAI/bge-small-en-v1.5`
- model revision: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- normalized embeddings: true
- semantic query prefix: unchanged from production configuration
- semantic child top-K: 50
- RRF pool: 50
- RRF k: 60
- reranking: disabled
- contradiction retrieval: disabled
- scored K: 5

Exact BM25 from the same production-source SHA is the baseline. Semantic-only is diagnostic decomposition only and cannot rescue a failed Hybrid result.

Canonical target configuration SHA256 over sorted compact JSON: `65c671e25dfd998350cfdb6d2a84c4a46d4db7e867827dd99fd4e57a8003f60e`.

## Apparatus dependency
Target execution is forbidden until the separately versioned `eb-retrieval-low-overlap-rc4-v1` apparatus has completed a dedicated assurance task and explicitly authorizes unchanged handoff.

The apparatus must be frozen before any exact BM25, weak/gaming control, Hybrid, or Semantic-only sealed execution. It must then independently demonstrate all promotion-critical apparatus requirements, including a strong fresh BM25 C01 baseline and failure of runtime-only construction/style gaming.

If the apparatus fails any promotion-critical requirement, stop. Do not alter the sealed object around observed outputs.

## Target gates
These gates are preregistered before any RC4 Hybrid/Semantic exposure.

Hybrid must satisfy all of:

1. Combined L01-L04 case hit@5 >= 0.85.
2. Combined L01-L04 decisive recall@5 >= 0.80.
3. Combined L01-L04 first-decisive MRR >= 0.60.
4. Each L01-L04 family case hit@5 >= 0.75 and decisive recall@5 >= 0.70.
5. Cue-swap paired semantic-role stability >= 0.80 on the preregistered paired-control metric.
6. >= 0.20 absolute improvement over exact BM25 on both combined L01-L04 case hit@5 and decisive recall@5.
7. C01 counterevidence case hit@5 >= 0.90.
8. C01 counterevidence recall@5 >= 0.90 and no more than 0.05 below exact BM25.
9. C01 first-counterevidence MRR >= 0.75.
10. Zero budget, provenance, scope, coverage, shape, completeness-overclaim, or answerability-overclaim violations.
11. Deterministic hit identity/rank replay and required source-order invariance.

A Hybrid failure is a Hybrid failure. Semantic-only cannot substitute for it.

## Apparatus prerequisite before target exposure
Exact BM25 must first show both sides of the intended contrast on the frozen RC4 object:

- combined L01-L04 case hit@5 <= 0.70;
- combined L01-L04 decisive recall@5 <= 0.65;
- at least 3 of 4 low-overlap families fail a target family floor;
- C01 counterevidence case hit@5 >= 0.90;
- C01 counterevidence recall@5 >= 0.90;
- C01 first-counterevidence MRR >= 0.75.

If BM25 does not satisfy the fresh C01 strength prerequisite, the RC4 apparatus cannot support the preservation question. Stop before Hybrid exposure.

## Explicit non-claims
This experiment does not establish production chunking/extraction behavior, native aperture/completeness receipts, semantic entailment, semantic answerability, Contract-A decomposition, Contract-B/C changes, CAL behavior, universal retrieval quality, production authorization, or release readiness.

## Contamination / exposure state at preregistration
- `hybrid_sealed_exposed = false`
- `semantic_sealed_exposed = false`
- no RC4 sealed benchmark bytes exist in this target PR
- no RC4 target result has been produced or inspected

## Stop rule
Stop with no target exposure if the RC4 apparatus is not explicitly authorized unchanged by a separate assurance task. RC4 is the last attempt in this synthetic sealed-challenge construction program before methodology reassessment if the apparatus again fails discrimination.