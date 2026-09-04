# Semantic 4K → MiniLM Rerank → K Dev RC1 — Results

Status date: 2026-08-29 / 2026-08-30 UTC

Research disposition: **RERANKER_USEFULNESS_FALSIFIED_ON_DEV_DIAGNOSTIC**

Production disposition: **NO PROMOTION**

## OBSERVED — authority and receipts

- preregistration commit: `9bef4a115ae600e0ab7b7105166a1e622a328da9`
- exact tested implementation: `6b381dad7ad5c0c1876800adfb746867a938a855`
- exact tested tree: `8d79bb5f295a65cd29cf379fe77a746dd6250c17`
- workflow run: `33282906795`
- job: `99180984477`
- artifact: `9723530775`
- artifact digest: `sha256:98f79f39955c74ce619f9bf19868508cf5e8b65f667723bd1b9c631910b742aa`
- output SHA256: `f69d2825bc6e7e703b8e925834d921c9195b431fa0edb1a9532645f90b2513d7`
- evaluation SHA256: `498a16ecc8a58d88776e3fc503a12716d7973ace9e59f72661ab9e51c16bfb0b`
- comparison SHA256: `b09e8458cb8d8231bdf00a62f5bfeaa076696034611b7a2059ffc8dff39ec067`

Frozen benchmark/evaluator/threshold identities were verified before execution.

## OBSERVED — validation

- full suite: **221 passed, 5 skipped**;
- rerank boundary test: **1 passed**;
- Ruff: **clean**;
- gold-blind result generator gate: **pass**;
- exact BGE revision execution: **pass**;
- exact MiniLM revision execution: **pass**;
- frozen dev evaluator: **pass**.

Execution burden:

- semantic passage encodes: 60;
- semantic query encodes: 18;
- reranker pairs scored: 60;
- final returned hits: 40;
- single hosted-run elapsed time: about 13.15 s.

## OBSERVED — comparison to raw semantic K

| Metric | Raw semantic K | Semantic 4K → MiniLM → K |
| --- | ---: | ---: |
| Case hit@K | **0.6429** | 0.5714 |
| Decisive annotation recall@K | **0.5000** | 0.4545 |
| Counterevidence recall@K | 0.0000 | 0.0000 |
| Qualifier/exception recall@K | 0.0000 | 0.0000 |
| Complete joint-group coverage@K | 0.0000 | 0.0000 |
| First-decisive MRR | **0.5000** | 0.3571 |
| Hard negatives at K | 29 | 30 |
| Hard negatives before first decisive | 26 | 30 |

The reranked arm is worse than raw semantic K on aggregate hit rate, decisive recall, MRR, and hard-negative burden.

## OBSERVED — family falsifiers

The semantic 4K input pool was previously shown to contain all decisive dev evidence, including all of the following families.

### R01 low overlap

- 4K input pool decisive recall: 1.0.
- after MiniLM compression: case hit 0.0; decisive recall 0.0.

The reranker removes the recovered low-overlap evidence from final K.

### R02 counterevidence

- 4K input pool counterevidence recall: 1.0.
- after MiniLM compression: counterevidence recall 0.0.

This is the critical counterevidence falsifier. The relevant counterevidence is available to the reranker and is still discarded.

### R03 / R04 qualifier and exception pairs

- semantic 4K pool has complete joint-group coverage 1.0.
- after reranking, joint-group coverage is 0.0 and qualifier/exception recall is 0.0.

The generic relevance reranker does not preserve the paired evidence structure.

### R05 multi-source composition

- semantic 4K pool has complete decisive coverage.
- after reranking: decisive recall 0.6667 and complete joint-group coverage 0.0.

### R06 distractor-heavy

- semantic 4K pool decisive recall: 1.0.
- after MiniLM compression: case hit 0.0 and decisive recall 0.0.

The current reranker does not rescue the deep semantic candidates that motivated the experiment.

### R08 provenance twin

- remains 1.0 / 1.0 after reranking.

This is the only challenged family whose semantic success is fully preserved.

## INFERENCE

### Reranker usefulness hypothesis

**FALSIFIED for this fixed current MiniLM reranker on the RC2 dev diagnostic.**

This is stronger than a simple “no gain” result because the input aperture was independently shown to contain every decisive annotation. The failure therefore cannot be explained by missing candidate evidence.

### What this says about the mechanism

The current MiniLM cross-encoder is a generic relevance scorer. On this diagnostic it does not preserve the distinctions the evidence-construction task needs:

- contradiction/counterevidence;
- qualifier/exception pairs;
- multi-passage completeness;
- deep distractor-heavy decisive evidence.

The result does not establish why the score function behaves this way internally, but it falsifies the claim that this fixed generic reranker is a useful compression stage for the observed failures.

### Production implication

No evidence supports enabling the current reranker by default. This negative result is not authorization to replace it with another fashionable model.

## HYPOTHESIS

The remaining failure is not one scalar ranking problem. The evidence suggests at least two different mechanisms may be required:

1. **role-aware retrieval/order** for counterevidence and qualifiers;
2. **coverage-aware selection** for multi-passage/joint evidence and distractor-heavy cases.

A single generic query-passage relevance score may be structurally unable to preserve all of these objectives.

## UNKNOWN

This dev diagnostic does not establish whether:

- the existing contradiction/counterevidence pass can rescue R02;
- a coverage-aware selector can recover R03-R06 from the complete semantic pool;
- alternative reranker families would help;
- these synthetic families generalize to external corpora.

## NEXT

Do not test another generic reranker yet.

The smallest next discriminating block is **Block E counterevidence pass characterization** on RC2 dev:

- hold supporting semantic retrieval fixed;
- compare contradiction expansion disabled/enabled;
- use the now-independent counterevidence lexical/semantic child budgets;
- keep the text-role gate explicit;
- measure R02 counterevidence recall, duplicate burden, false role-gate rejection, and spillover into non-counterevidence families;
- preserve final supporting and counterevidence channels separately.

After that, design a separate coverage-aware selection diagnostic for R03-R06 rather than asking a generic relevance reranker to solve composition.
