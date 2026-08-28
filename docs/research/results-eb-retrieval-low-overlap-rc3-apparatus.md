# EB Retrieval Low-Overlap RC3 — Apparatus Assurance Result

**PR class:** Research Infrastructure

**Terminal apparatus disposition:** `FALSIFIED`

**Target exposure authorization:** **NO**

```text
hybrid_sealed_exposed = false
semantic_sealed_exposed = false
```

## Decision

The exact frozen `eb-retrieval-low-overlap-rc3-v1` apparatus must not be handed to PR #15 for Hybrid or Semantic-only target exposure.

The evaluator implementation reacted correctly to the preregistered mutations, invariances, technical violations, oracle, and lexical weak controls, but the benchmark itself failed the required decision-discrimination test: a deliberately weak runtime-only construction-cue heuristic qualified without performing meaning-preserving semantic retrieval.

This is an apparatus falsification, not a Hybrid result.

## Frozen object

The scientific apparatus was frozen before the first sealed BM25/lexical output at:

- apparatus freeze commit: `36ec382c3cd94b6dd1a6be652e49a80469e6b1a4`
- production-source pin: `c8189c31adbab11729c31430c2070126224a2d42`
- target PR #15 preregistration head: `b2650e2a64c96f2d13500e4be27a8eb41d085c1d`
- freeze-manifest SHA-256: `3f8efeaab3e814c146da937f7824ae62ba8506320dd3ddb7149454f9a063bed7`
- benchmark-tree SHA-256: `f83bdbec6fd89864ee512ff4557ce51eb53164917bec32b03fb5560e01a71c1e`
- first sealed control SHA-256: `b3769f79de6687c4f07f5cb9b65ef759576bef337b5b351d496a9c5b894ac6b7`
- post-freeze gaming diagnostic SHA-256: `efe412966f073ec38f417e320df72d3b55b4e936d5959a8397085cef80ad0ca9`

The exact generated runtime cases, passages, scopes, sources, evaluator-only gold, generator receipt, and benchmark manifest hashes are recorded in `receipt-eb-retrieval-low-overlap-rc3-apparatus-terminal.json`.

## Observed evidence

### Structural / oracle checks

- exactly 64 sealed answerable cases were generated: 16 each L01/L02/L03/C01;
- 576 passages were generated, nine per case, with K=5;
- runtime material and evaluator-only gold were physically separated;
- L01-L03 designated hard negatives had greater token overlap than the decisive passage in every case;
- decisive passages were outside first-N K=5 for L01-L03;
- deterministic regeneration matched the frozen expected benchmark bytes/tree;
- oracle achieved 1.0 low-overlap hit@5, 1.0 decisive recall@5, 1.0 C01 counterevidence recall@5, with zero technical violations.

### Exact c818 BM25

The adapter used the exact c818 production BM25 source blobs and a byte-identical `rank_bm25.py` from upstream tag `0.2.2`.

Observed:

- combined L01-L03 case hit@5: `0.0`
- combined L01-L03 decisive recall@5: `0.0`
- combined first-decisive MRR: `0.0`
- L01 case hit@5 / recall@5: `0.0 / 0.0`
- L02 case hit@5 / recall@5: `0.0 / 0.0`
- L03 case hit@5 / recall@5: `0.0 / 0.0`
- C01 counterevidence case hit@5: `0.3125`
- C01 counterevidence recall@5: `0.3125`
- technical violations: `0`

Exact BM25 therefore failed the required low-overlap discriminator, as expected, but its weak C01 result also means this fresh C01 object does not reproduce the strong counterevidence baseline observed in RC2.

### Required weak controls

- token overlap: failed qualification;
- TF-IDF cosine: failed qualification;
- character-trigram similarity: failed qualification;
- null: failed;
- first-N/source-order: failed;
- return-all: failed with 64 budget violations;
- provenance-corrupt: failed with 64 invalid provenance hits;
- hard-negative-biased: materially underperformed oracle on low-overlap retrieval;
- false-completeness claimant: failed with 64 false completeness claims;
- semantic-answerability liar: failed with 64 answerability overclaims.

The encoded weak-control gate therefore returned green. That green result is not the terminal disposition.

### Evaluator assurance

Observed pass:

- deterministic replay;
- source enumeration reversal hit/rank invariance;
- BM25 maximum score delta under reversal `3.552713678800501e-15`, within frozen `1e-12` tolerance;
- decisive-identity mutation sensitivity;
- hard-negative-identity mutation sensitivity;
- exact text/provenance mutation sensitivity;
- family-label / family-aggregation sensitivity with combined low-overlap invariance;
- result-coverage mismatch fail-closed behavior;
- K/budget enforcement.

These observations support evaluator correctness for the encoded measurements. They do not establish benchmark decision discrimination.

## Decisive adversarial result

After the first sealed control, the all-zero L01-L03 outcomes across BM25, token overlap, TF-IDF, and character trigrams raised the competing explanation that the benchmark's repeated decoy templates were creating a construction cue rather than measuring semantic generalization.

A smallest runtime-only gaming diagnostic was therefore executed against the already frozen bytes. Its ranker:

- did not read evaluator gold;
- did not read family labels;
- did not read decisive or hard-negative identities;
- read only the same runtime passages available to a retriever;
- penalized recurring meta-document phrases such as training simulator, worksheet, documentation index, maintenance checklist, prototype note, service inventory, release record, incident register, policy glossary, training slide, audit plan, change ticket, support guide, historical index, review queue, and monitoring dashboard.

It performed no claim-to-passage semantic matching.

Observed qualification:

- combined L01-L03 case hit@5: `0.9791666666666666`
- combined decisive recall@5: `0.9791666666666666`
- combined first-decisive MRR: `0.9791666666666666`
- L01 case hit@5: `1.0`
- L02 case hit@5: `1.0`
- L03 case hit@5: `0.9375`
- C01 counterevidence case hit@5: `1.0`
- C01 counterevidence recall@5: `1.0`
- technical violations: `0`
- absolute target qualification: `true`

This is promotion-critical negative evidence. A weak construction-aware system can clear the same target gates without demonstrating the intended meaning-preserving low-overlap capability.

## Competing explanations checked

- **Malformed or inaccessible gold:** not supported by the oracle or source/provenance reconstruction checks.
- **K/scope mistakes:** not supported by K enforcement, scope checks, or oracle behavior.
- **Source enumeration artifacts:** not supported by reversal invariance.
- **Evaluator aggregation defect:** named family mutation changed per-family aggregation while preserving the combined low-overlap total as expected.
- **Controls failing only on parser/provenance defects:** not supported; lexical weak controls failed substantive retrieval gates with zero technical violations.
- **Benchmark-specific quirks unrelated to semantic retrieval:** **supported** by the runtime-only meta-cue gamer qualifying.
- **Fresh C01 faithfully reproduces the RC2 BM25 counterevidence strength:** **not supported**; exact BM25 C01 recall was 0.3125.

## Deviations and unresolved limitations

Two execution deviations are preserved separately:

- `deviation-16a-rc3-git-data-push-no-actions-event.md`
- `deviation-16b-rc3-local-execution-surface.md`

The available GitHub connector write path did not emit an Actions event, so the branch-local Python 3.12 workflow could not be started. The first sealed control was executed on Python 3.13.5 after exact frozen-byte verification. This is not represented as a GitHub-hosted CI receipt.

The local validator also could not execute its exact RC2 text/entity non-reuse comparison, so that check remains unresolved (`performed=false`). This limitation would independently block a positive apparatus handoff, but it is not needed to produce the terminal negative disposition because the runtime-only gamer already falsified decision discrimination.

## Inference

The RC3 evaluator appears sensitive to the intended encoded measurements, but `eb-retrieval-low-overlap-rc3-v1` is not a valid bounded discriminator for the PR #15 semantic-generalization question. The repeated generator/document-style cues create a cheap, non-semantic route to qualification.

## Falsified apparatus claim

> The exact frozen RC3 apparatus distinguishes meaning-preserving low-lexical-overlap retrieval from plausible weak or gaming implementations strongly enough to authorize first Hybrid/Semantic target exposure.

**Falsified.**

## Non-claims

This result does **not** establish anything about:

- Hybrid retrieval performance;
- Semantic-only retrieval performance;
- whether Hybrid would outperform BM25 on RC3;
- production Evidence Bundler semantics;
- Contract A/B/C;
- CAL or Decision Engine behavior;
- release or promotion state.

Hybrid and Semantic were never exposed to the sealed RC3 challenge.

## Smallest justified successor

Do not repair `eb-retrieval-low-overlap-rc3-v1` after exposure.

If the generalization question remains worth pursuing, create a newly versioned fresh apparatus in a separate Research Infrastructure task. The smallest justified change is to remove systematic document-style/template cues through heterogeneous decoy/source constructions and preregister a runtime-only construction-cue gaming control that must fail before any Hybrid/Semantic sealed exposure.
