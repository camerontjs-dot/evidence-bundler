# Retrieval Characterization Block B Dev RC1 — Results

Status date: 2026-08-29 / 2026-08-30 UTC

Research disposition: **CHARACTERIZED_WITH_CONFLICTING_FAMILY_BEHAVIOR**

Production disposition: **NO PROMOTION**

## OBSERVED — authority and receipts

- preregistration commit: `a5d00a6f3fe6985a12979f52332755b3946b70f3`
- exact decisive implementation/test commit: `7383407b58e78fad9d090482037a5ff86fb74a9e`
- exact decisive tree: `73857c2cacbd2669046210da518ab1ead5a37245`
- successful decisive workflow run: `33282443190`
- job: `99179770792`
- artifact: `9723401822`
- artifact digest: `sha256:8436a20d8b0147e9d2977f24a7993acffa512bed276210fa8b83ba301b8bbede`
- comparison receipt SHA256: `55210589523405a66a39e1430a763c31a7bcd1fc3c13f3b2e99eeb368e7d293f`
- benchmark tree SHA256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`
- evaluator SHA256: `c443a64a2c2dfe8c9b0decd8c0414c1e7bb1069d86d3355dd0202fa9725aff08`

The retrieval adapter was verified not to reference evaluator-only gold. All three result files were written before the frozen evaluator consumed dev gold.

## OBSERVED — pre-execution deviation

The first preregistered workflow run `33282337753` stopped before any retrieval arm executed because Ruff found formatting-only line-length violations in the new adapter/tests.

Before stopping it had already established:

- frozen evaluator identities: pass;
- gold-blind adapter grep gates: pass;
- full suite: `219 passed, 5 skipped`;
- explicit adapter suite: `3 passed`.

No retrieval result existed in that stopped run. Only formatting was repaired. No arm configuration, benchmark, evaluator, threshold, model identity, or success criterion changed.

## OBSERVED — decisive validation

On the decisive exact head:

- full deterministic suite: **219 passed, 5 skipped**;
- Block B adapter suite: **3 passed**;
- Ruff: **clean**;
- benchmark/evaluator identity checks: **pass**;
- gold-blind adapter check: **pass**;
- all three fixed arms executed and evaluated successfully.

## OBSERVED — aggregate dev results

| Metric | BM25 | Semantic-only | Hybrid |
| --- | ---: | ---: | ---: |
| Case hit@K | 0.5714 | 0.6429 | **0.7143** |
| Decisive annotation recall@K | 0.4545 | 0.5000 | **0.5455** |
| Counterevidence recall@K | **1.0000** | 0.0000 | 0.5000 |
| Qualifier/exception recall@K | 0.0000 | 0.0000 | 0.0000 |
| Complete joint-group coverage@K | 0.0000 | 0.0000 | 0.0000 |
| First-decisive MRR | 0.2857 | **0.5000** | 0.4286 |
| Hard negatives at K | **12** | 29 | 28 |
| Hard negatives before first decisive | **12** | 26 | 28 |
| Budget violations | 0 | 0 | 0 |
| Invalid provenance hits | 0 | 0 | 0 |
| Scope mismatches | 0 | 0 | 0 |
| Qualified under frozen RC2 thresholds | no | no | no |

None of the arms clears the frozen RC2 diagnostic thresholds.

## OBSERVED — family behavior

### R01 low-overlap relevance

- BM25: case hit 0.0; decisive recall 0.0.
- Semantic-only: case hit 0.5; decisive recall 0.5.
- Hybrid: case hit 0.5; decisive recall 0.5.

Semantic retrieval recovers one of the two dev low-overlap cases missed by BM25.

### R02 counterevidence lexical trap

- BM25: case hit 1.0; counterevidence recall 1.0.
- Semantic-only: case hit 0.0; counterevidence recall 0.0.
- Hybrid: case hit 0.5; counterevidence recall 0.5.

The pinned semantic model is not a drop-in counterevidence replacement on this diagnostic family. RRF with equal K source pools preserves only part of BM25's counterevidence advantage.

### R03/R04 qualifier and exception joint pairs

All three arms:

- case hit 1.0;
- decisive recall 0.5;
- qualifier/exception recall 0.0;
- complete joint-group coverage 0.0.

Each family appears to retrieve one side of the required pair while missing the other within K.

### R05 multi-source composition

All three arms:

- case hit 1.0;
- decisive recall 0.6667;
- complete joint-group coverage 0.0.

Again, at least one decisive element is found, but full composition is not.

### R06 distractor-heavy bounded K

All three arms:

- case hit 0.0;
- decisive recall 0.0.

This is a shared severe failure and is particularly important because semantic/hybrid do not rescue it.

### R08 provenance twin

- BM25: case hit 0.0; decisive recall 0.0.
- Semantic-only: case hit 1.0; decisive recall 1.0.
- Hybrid: case hit 1.0; decisive recall 1.0.

This is the clearest semantic-family gain in the current dev slice.

## OBSERVED — execution burden

- BM25:
  - source candidate positions budgeted: 40;
  - returned hits: 22;
  - elapsed runner time: about 0.01 s.
- Semantic-only:
  - source candidate positions budgeted: 40;
  - 60 passage encodes + 18 query encodes;
  - returned hits: 40;
  - elapsed runner time: about 10.08 s.
- Hybrid:
  - source candidate positions budgeted: 80;
  - 60 passage encodes + 18 query encodes;
  - returned hits: 40;
  - elapsed runner time: about 6.72 s.

Elapsed time is a single hosted-run observation, not a stable performance benchmark. Candidate/encode counts are the more reproducible burden records.

## INFERENCE — falsifiers

### Semantic-only usefulness

**Not globally supported.**

The low-overlap usefulness hypothesis receives bounded support from R01 and R08, but semantic-only loses all R02 counterevidence recall and does not improve R03-R06.

### Hybrid usefulness over lexical

**Partially supported, not sufficient for promotion.**

Hybrid improves aggregate case hit and decisive recall over BM25 and recovers R01/R08 behavior, but:

- consumes twice the source candidate positions;
- cuts R02 counterevidence recall from 1.0 to 0.5;
- increases hard-negative burden;
- leaves R03-R06 structural failures unchanged.

### One-configuration / one-family generalization

**FALSIFIED on this dev diagnostic slice.**

Family rankings conflict materially. BM25 dominates R02; semantic/hybrid dominate R01 and R08; none solves the joint/composition/distractor families.

## INFERENCE — most important competing explanations

The current results do not tell us whether R03-R06 failures arise because:

1. the decisive passage never enters the retriever candidate pool;
2. it enters a larger pool but ranks below the final K cutoff;
3. fusion displaces a good lexical or semantic candidate;
4. the current K budget is simply too narrow for multi-passage evidence;
5. the benchmark construction encodes a failure mode neither current retriever represents well.

A reranker experiment now would confound these explanations.

## NEXT

Run a **candidate-pool aperture diagnostic** on the same frozen RC2 dev split before reranking:

- preserve final evaluation K separately;
- inspect lexical and semantic candidate-pool recall at preregistered K, 2K, and 4K;
- record whether each missed decisive/joint/counterevidence item ever enters the larger pool;
- do not alter the frozen RC2 evaluator or use the sealed split;
- stop before reranking if the relevant evidence is absent even at the larger candidate pool.

That is the smallest test that can distinguish candidate-generation failure from ranking/truncation failure.
