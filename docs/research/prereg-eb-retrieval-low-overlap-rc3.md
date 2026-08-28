# Evidence Bundler Retrieval Generalization RC3 — Low-Overlap Method Comparison

**PR class:** Research / Draft

**State:** PREREGISTERED. No fresh sealed RC3 target-system output has been produced or inspected.

## Objective / decision

Determine whether the existing frozen Evidence Bundler hybrid retrieval path can recover meaning-preserving, low-lexical-overlap evidence on a fresh sealed challenge materially better than the frozen production BM25 baseline **without sacrificing counterevidence retrieval**, under an identical presegmented passage representation and identical top-K budget.

This experiment is intentionally narrower than RC2. It tests retrieval method/representation only.

It does not test or authorize:

- production chunking/extraction;
- native aperture/completeness receipts;
- semantic entailment/support/refutation judgment;
- semantic answerability/no-answer judgment;
- Contract-A decomposition;
- Contract-B/C or CAL changes;
- production promotion by itself.

## Predecessor evidence

Primary predecessor: Evidence Bundler PR #14, terminal `FALSIFIED` for the full RC2 presegmented-retrieval gate on frozen production BM25 `c8189c31adbab11729c31430c2070126224a2d42`.

RC2 observations motivating this narrower test:

- R01 low-overlap: 1/8 case hits; decisive recall 0.125;
- R02 counterevidence: 8/8 case hits; counterevidence recall 1.0;
- deterministic replay and source-order invariance held;
- zero scored budget, returned-provenance, scope, completeness-overclaim, and answerability-overclaim violations.

RC2 sealed cases are now exposed evidence and **must not be used to tune, select, or repair RC3 candidate behavior**.

## Frozen code under test

All retrieval methods are drawn from the same production-source commit:

- Evidence Bundler source SHA: `c8189c31adbab11729c31430c2070126224a2d42`
- retrieval config/model blob: `27796662f76c506fcafde32719b40c42aae5dc8d`
- semantic retrieval blob: `ab5bbf938d894f5111ff434918115a8a84a88add`
- hybrid RRF blob: `761e010da2976d03dc69808ab8d488375869bdb9`

Later `main` Research-Infrastructure commits are not substitute SUT identities.

### Baseline A — BM25

Exact production BM25 behavior from `c8189c31...`, with RC3 runtime passage units supplied through the same bounded presegmented adapter class used only to preserve exact passage identity.

### Candidate B — Hybrid

Existing production-source hybrid retrieval only. No new retrieval algorithm is introduced in this experiment.

Frozen semantic/hybrid configuration:

- `embedding_model = BAAI/bge-small-en-v1.5`
- model revision: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- normalized embeddings: `true`
- semantic query prefix: `Represent this sentence for searching relevant passages: `
- `semantic_child_top_k = 50`
- `rrf_candidate_pool = 50`
- `rrf_k_constant = 60`
- `rerank_enabled = false`
- `contradiction_enabled = false`
- scored output budget: `K = 5`

A model-loading wrapper may pin the external model revision and record model-file hashes. It may not alter text, embeddings, query prefix, ranking, RRF, or output ordering.

### Diagnostic C — Semantic-only

The semantic child ranking from the same frozen model/config may be evaluated in the same first target exposure as a **diagnostic decomposition**. It is not the primary promotion candidate in this experiment.

If semantic-only succeeds while hybrid fails, this experiment still falsifies the primary hybrid claim. Semantic-only may motivate a separate future experiment; it is not promoted by substitution.

## Environment identity gate

Before any fresh sealed target exposure, freeze and record:

- Python version;
- exact `sentence-transformers`, `transformers`, `torch`, `faiss-cpu`, `numpy`, `rank-bm25`, and transitive package snapshot;
- exact Hugging Face revision above;
- model artifact/file hashes actually loaded;
- adapter source hash;
- candidate configuration canonical hash.

Environment/model identity may be established before sealed target exposure. Performance-dependent package/model substitution is forbidden.

## Fresh RC3 apparatus requirement

A separate Research Infrastructure / apparatus-assurance task must construct and freeze `eb-retrieval-low-overlap-rc3-v1` **without running Candidate B or Diagnostic C on the fresh sealed split**.

### Generator freeze

Preregistered deterministic generator seed: `141421`.

The sealed challenge should contain exactly 64 answerable cases:

- `L01 terminology substitution`: 16;
- `L02 compositional paraphrase`: 16;
- `L03 lexical-decoy low-overlap`: 16;
- `C01 counterevidence retention`: 16.

No RC2 case text, fictional entity stem, decisive passage, or hard-negative passage may be copied into RC3.

Each low-overlap case must:

- preserve the same proposition meaning between query and decisive passage;
- intentionally reduce surface lexical overlap;
- contain at least one hard negative that is lexically closer to the query than the decisive passage;
- expose only runtime passage identity/text/scope to retrievers;
- keep gold and family labels evaluator-only;
- use `K = 5`.

The apparatus may include a separate small development/transport fixture, but fresh sealed target performance must remain unobserved by semantic/hybrid retrieval until apparatus authorization is terminal.

## Apparatus assurance gate before target exposure

The fresh apparatus is authorized for target use only if, on its exact frozen sealed bytes:

1. oracle passes all primary retrieval gates;
2. frozen BM25 baseline fails at least one primary low-overlap capability gate;
3. token-overlap, TF-IDF cosine, and character-trigram lexical weak controls each fail qualification;
4. null, return-all, provenance-corrupt, scope/aperture liar, and answerability-liar controls fail on their intended surfaces where applicable;
5. deterministic evaluator replay succeeds;
6. source-order invariance succeeds for the oracle/control layer;
7. named gold/provenance mutation checks change evaluator output as preregistered;
8. benchmark/evaluator/threshold/result-schema bytes are frozen and hashed;
9. the apparatus record explicitly confirms `hybrid_sealed_exposed=false` and `semantic_sealed_exposed=false`.

If BM25 or the lexical weak controls clear the fresh low-overlap gate, stop before semantic/hybrid exposure. The apparatus has failed to discriminate the intended decision and must not be repaired after target exposure.

## Primary target acceptance gates

Candidate B (`hybrid`) is `SUPPORTED FOR PROMOTION` for this bounded research capability only if **all** of the following hold on the first legitimate fresh sealed target measurement:

### Absolute low-overlap capability

Across L01-L03 combined:

- case hit@5 `>= 0.85`;
- decisive annotation recall@5 `>= 0.80`;
- first-decisive MRR `>= 0.60`.

For each of L01, L02, and L03 individually:

- case hit@5 `>= 0.75`;
- decisive annotation recall@5 `>= 0.70`.

### Improvement over frozen BM25 baseline

On the same sealed cases and same K:

- hybrid minus BM25 low-overlap case hit@5 `>= 0.25` absolute;
- hybrid minus BM25 low-overlap decisive recall@5 `>= 0.25` absolute.

### Counterevidence non-regression

On C01:

- hybrid counterevidence case hit@5 `>= 0.90`;
- hybrid counterevidence recall@5 `>= 0.90`;
- hybrid counterevidence recall may be no more than `0.05` absolute below the frozen BM25 baseline on C01.

### Technical integrity

Required counts are zero:

- budget violations;
- invalid returned provenance;
- out-of-scope hits;
- scope mismatches;
- false completeness claims;
- semantic answerability overclaims;
- result-shape errors.

Candidate output must emit `not_established` for completeness and semantic answerability unless those states are independently and legitimately produced by the frozen SUT. The adapter may not invent them.

### Determinism and invariance

- repeated target execution must preserve hit identity and rank exactly;
- source enumeration reversal must preserve hit identity and rank exactly;
- floating-score comparison may use a preregistered absolute tolerance of `1e-12`, but score tolerance cannot excuse identity/rank changes.

## Falsifiers

The primary hybrid claim is `FALSIFIED` if the apparatus is valid and Candidate B fails any required target acceptance gate.

Particular falsifiers include:

- low-overlap improvement is small or absent;
- semantic gain is erased by hybrid fusion;
- counterevidence materially regresses;
- hard negatives dominate the top-K despite semantic retrieval;
- candidate behavior depends materially on source enumeration;
- model/environment identity cannot reproduce the same ranking;
- technical adapter/provenance/scope failures contaminate the measurement.

## Competing explanations to preserve

A strong hybrid result could still mean:

- the fresh benchmark contains semantic-model-friendly regularities that do not generalize broadly;
- presegmented passage retrieval succeeds while production chunking does not;
- BGE specifically matches the synthetic transformation families rather than establishing general semantic retrieval;
- RRF succeeds because one component rescues the other, not because every component is individually strong.

A weak hybrid result could mean:

- semantic retrieval does not solve the tested low-overlap failure;
- the fixed BGE model/query representation is inadequate;
- RRF suppresses useful semantic hits;
- K=5 is too restrictive for this candidate;
- the fresh challenge encodes a boundary that neither production retrieval method can satisfy;
- a technical model-loading/adapter defect occurred.

Use the semantic-only diagnostic, exact BM25 control, rank provenance, and smallest available invariance checks to distinguish these explanations. Do not tune against sealed cases.

## Experimental firewall

After Candidate B or Diagnostic C first receives fresh sealed runtime cases, do not change:

- benchmark or gold bytes;
- family composition;
- thresholds or family floors;
- result schema;
- evaluator logic;
- candidate code/config/model revision;
- query prefix;
- RRF constants;
- K;
- success/failure definitions.

Any defect discovered after exposure is a preserved deviation. A repair requires a new experiment/version unless the defect is demonstrably non-scientific and cannot affect the result.

## Disposition

Use exactly one terminal research disposition for the target experiment:

- `SUPPORTED FOR PROMOTION`
- `FALSIFIED`
- `INCONCLUSIVE`
- `SUPERSEDED`

`SUPPORTED FOR PROMOTION` means only that the exact frozen hybrid candidate has earned consideration for a later, separate production-promotion decision on the bounded low-overlap retrieval capability. It is not production authorization.

Use `INCONCLUSIVE` if an unexpected apparatus/model/adapter ambiguity prevents the result from discriminating the decision.

## Stop rule

Stop after:

- the apparatus has been frozen and separately authorized;
- the first legitimate semantic/hybrid sealed target measurement and preregistered controls complete;
- the primary result, failures/deviations, PR disposition, Apparatus #8 living epistemic state, and Apparatus #9 evaluator correspondence are reconciled.

Do not optimize any retrieval configuration against the sealed RC3 apparatus in this task.

## Smallest successor implied by each outcome

- Hybrid passes: open a separate promotion-analysis task; do not promote automatically.
- Hybrid fails but semantic-only passes: preregister a separate semantic-only candidate experiment on another unexposed discriminator.
- Both fail: investigate query/representation alternatives using new unexposed evidence, beginning with the smallest failed subfamily.
- Apparatus fails discrimination before target exposure: redesign/version the apparatus without exposing semantic/hybrid to the rejected sealed object.
