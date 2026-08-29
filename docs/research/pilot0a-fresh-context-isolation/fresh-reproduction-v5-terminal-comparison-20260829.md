# External Corpus Evaluator v0.3 Fresh Reproduction v5 — Terminal Post-Reveal Comparison

Research Infrastructure only. This record completes the already-frozen fresh reproduction. It does not authorize Pilot 0A scientific Gate 1, retrieval execution, benchmark expansion, or production promotion.

## OBSERVED

### Frozen implementation identity

- repository: `camerontjs-dot/evidence-bundler`
- implementation branch: `research-infra/external-corpus-evaluator-v03-fresh-reproduction-v5-20260829`
- sanitized base commit: `e14df1bd8239445ef0b0a07525b07ae9c2b78835`
- sanitized base tree: `a63098cabf02e78e2f27c8b5df827db02a0c06cf`
- frozen implementation commit: `066ed4308e0d918a528248494763db200e96229c`
- frozen implementation path: `research/external_corpus_evaluator_independence_v2/fresh_reproduction_v5.py`
- frozen implementation Git blob: `602f78a3416ae4eb3c2aafa64c6c4a91f2b04857`
- frozen implementation SHA-256: `6a7d08b87517d27e37ba9f371cfe52736a93130d1240279c73ccb6636a676355`
- implementation bytes: `15266`
- pre-reveal freeze-receipt commit / prior branch head: `c2b8e826a8235c28d1674035fe3ecfb0774e146e`
- freeze receipt: `docs/research/pilot0a-fresh-context-isolation/fresh-reproduction-v5-freeze-receipt-20260829.md`
- freeze receipt contamination state: `CLEAN WITHIN THE SPECIFIED APERTURE`

The freeze commit is a direct child of the sanitized base. The freeze-receipt commit is a direct child of the implementation freeze commit. The implementation blob at the freeze commit was re-verified before this terminal record was written and had not changed.

### Freeze-before-reveal ordering

The pre-reveal receipt records `2026-08-29T19:24:04Z` as authored before reveal. GitHub records the implementation freeze commit at `2026-08-29T19:23:51Z` and the freeze-receipt commit at `2026-08-29T19:24:28Z`.

The four authorized reference surfaces were first opened only after the implementation commit and freeze receipt existed. The frozen implementation was not edited after reveal.

### Reference source and revealed blobs

Reference source SHA: `a6408a594ede083cf4997b47103d836819c559b8`

Authorized revealed surfaces, each re-verified by exact Git blob before terminalization:

1. `research/external_corpus_evaluator_independence_v2/evaluator_a.py`
   - blob `00726ce244c80c89bfab37e31a76db263c986ab5`
2. `research/external_corpus_evaluator_independence_v2/evaluator_b.py`
   - blob `079e1e90e64b60bdd0a806e0c6694aadcb045a6e`
3. `research/external_corpus_evaluator_independence_v2/canonical.py`
   - blob `29f3d86c2b043cd450f65df39eecdd448b4ff7f4`
4. `tests/test_external_corpus_evaluator_independence_v2.py`
   - blob `2a1e42b4cbaf040e4c8b78a8ed78eebc5dc2bb8d`

No broader historical PR reasoning, Pilot scientific data, retrieval output, or unrelated repository history was used for the comparison.

### Commands / comparison receipts

The authorized post-reveal comparison already executed in this same fresh-reproduction run produced these receipts:

- `cd /mnt/data/refrepo && pytest -q tests/test_external_corpus_evaluator_independence_v2.py`
  - result: `24 passed in 0.08s`
  - meaning: reference A and B agree on every behavior represented by the authorized v0.3 test suite.

- `python /mnt/data/postfreeze_compare.py`
  - result: `38 passed, 0 failed`
  - meaning: the behaviors represented by the authorized suite, translated to the frozen fresh evaluator's own API, all agreed.

- `python /mnt/data/direct_cross_compare.py`
  - result: `21 agree, 0 disagree`
  - meaning: reference A, reference B, and the frozen fresh evaluator agreed on acceptance/rejection and normalized metric semantics across the baseline fixtures and the suite-derived mutations included in this direct comparison.

- `python /mnt/data/divergence_probes.py`
  - result: additional post-freeze validation/interface disagreements were observed outside the frozen authorized test coverage; these are preserved below.

Pre-freeze receipts remain recorded separately in `fresh-reproduction-v5-freeze-receipt-20260829.md` and include compilation, implementation hashing, broad dummy evaluation, the dedicated two-query nDCG discriminator, and contract-derived self-checks.

### Agreements

A and B showed no observed disagreement.

The frozen fresh evaluator agreed with A and B on all metric behavior exercised by the authorized suite, including:

- baseline `hit@K = 1.0`;
- baseline evidence recall `= 1.0`;
- baseline counterevidence recall `= 0.5`;
- dummy q1 `nDCG@K = 0.938506417451168`;
- dummy q2 nDCG undefined because q2 itself contains an unresolved judgment;
- dummy aggregate nDCG averaging only the query with defined nDCG;
- dedicated q_clean `nDCG@K = 0.7098097413968655`;
- dedicated q_unknown nDCG undefined;
- dedicated aggregate nDCG equal to q_clean alone;
- resolving the unrelated UNKNOWN enables the second query's nDCG without changing the first query's nDCG;
- `qrels_mode=partial` disables nDCG for every query and marks metric interpretation `lower_bound`;
- top-level `ndcg_eligible=false` disables nDCG for every query;
- SUPPORT/COUNTEREVIDENCE role mutation changes the corresponding recall metrics;
- loss of a member of a `JOINTLY_REQUIRED` group reduces group coverage;
- UNKNOWN remains distinct from irrelevant and unjudged for relevance credit and judgment-coverage diagnostics;
- empty result judgment-coverage behavior represented by the implementations;
- unknown ranked passage IDs fail closed;
- duplicate ranked passage IDs fail closed;
- malformed/gapped ranks fail closed;
- corpus-version mismatch fails closed;
- corpus-hash mismatch fails closed;
- benchmark-hash mismatch fails closed;
- duplicate manifest query IDs fail closed;
- duplicate manifest source IDs fail closed;
- unknown manifest source references fail closed;
- the authorized missing-locator case fails closed;
- gold query-ID set mismatch fails closed;
- run query-ID set mismatch fails closed;
- reordered gold serialization preserves metrics and hidden-gold commitment;
- the frozen dummy commitment is `2d0e0d99d23295b91c838e01a4e1a6274e2a77af45cd52ab834ed78fd5b6131f`;
- consistent stable query/source/passage ID renaming preserves metric values while changing the gold commitment;
- deterministic rerun behavior on the tested fixtures.

The central v0.3 clarification reproduced independently: a judgment-dependent nDCG eligibility failure in one query does not suppress nDCG in a different query that independently satisfies the nDCG prerequisites.

### Preserved disagreements and classification

#### 1. Required identity field absent from all three artifacts

Counterexample: remove `benchmark_sha256` from manifest, gold, and run.

- frozen fresh evaluator: rejects;
- evaluator A: accepts;
- evaluator B: accepts;
- A vs B: no disagreement.

Classification:

- **fresh implementation disagrees with A/B**;
- **reference appears inconsistent with the written contract**.

The written v0.3 contract states that manifest, hidden gold, and ranked run must carry identical `corpus_version`, `corpus_sha256`, and `benchmark_sha256`. A/B compare `.get()` values and therefore allow the all-missing case when all three yield `None`. The frozen fresh implementation requires presence as well as equality.

#### 2. Representation-identity field spelling / admissible shape

Counterexamples with a passage locator removed:

- `representation_identity` supplied: A/B accept; fresh rejects;
- `representation_id` supplied: fresh accepts; A/B reject.

Source inspection also showed that the fresh implementation recognizes `representation_sha256` and non-empty `representation` forms while A/B specifically recognize `representation_identity`.

Classification:

- **fresh implementation disagrees with A/B**;
- **written contract admits multiple interpretations**.

The written contract requires a reconstructable locator/representation identity but does not define a normative representation-identity field name or shape.

#### 3. `relevance_degree=UNKNOWN` with a resolved role such as `SUPPORT`

Counterexample: `relevance_degree=UNKNOWN`, `binary_relevant=null`, `gain=null`, `role=SUPPORT`.

- fresh: rejects;
- A/B: accept;
- A vs B: no disagreement.

Classification:

- **fresh implementation disagrees with A/B**;
- **written contract leaves a coupling question unresolved**.

The contract explicitly requires null binary relevance and gain for UNKNOWN relevance degree and separately enumerates valid roles, but does not explicitly say that UNKNOWN relevance degree must force `role=UNKNOWN`. The fresh evaluator imposed that additional coupling.

#### 4. Resolved judgment with `role=UNKNOWN`

Counterexample: resolved positive judgment with a normal relevance degree, boolean binary judgment, positive gain, and `role=UNKNOWN`.

- fresh: rejects;
- A/B: accept;
- A vs B: no disagreement.

Classification:

- **fresh implementation disagrees with A/B**;
- **the fresh implementation is stricter than the explicit written validation rule**.

The contract includes `UNKNOWN` in the role enumeration but does not explicitly prohibit that role for otherwise resolved judgments. This makes the fresh restriction unsupported by an explicit fail-closed clause, although the semantic intent of `role=UNKNOWN` remains open to interpretation.

#### 5. Group-ID uniqueness scope

Counterexample: reuse the same `group_id` in two different queries.

- fresh: rejects because it enforces global group-ID uniqueness;
- A/B: accept because they enforce uniqueness within each query;
- A vs B: no disagreement.

Classification:

- **fresh implementation disagrees with A/B**;
- **written contract admits multiple interpretations**.

The contract says a group has a unique `group_id` but does not explicitly state whether uniqueness is benchmark-wide or query-local.

#### 6. Omitted `judgments` / `groups` collection fields

Counterexamples: omit both `judgments` and `groups` from a gold query, or omit only `groups`.

- fresh: rejects missing collection fields;
- A/B: treat missing fields as empty lists and accept where the remaining artifact is otherwise valid;
- A vs B: no disagreement.

Classification:

- **fresh implementation disagrees with A/B**;
- **written contract admits multiple interpretations**.

The contract defines judgment and group semantics but does not explicitly specify whether absent collection fields are invalid or equivalent to empty collections.

#### 7. Raw result-object surface

The fresh evaluator's result object is not byte/shape-equal to A/B:

- A/B include `status`, `ndcg_eligible`, and `ndcg_eligible_by_query`;
- fresh omits those fields;
- A/B use metric field names ending `_at_k`;
- fresh uses the contract's displayed `@K` metric names;
- for complete qrels A/B emit `metric_interpretation="point_estimate"` while fresh emits `metric_interpretation="complete_relevant_set"`.

Classification:

- **implementation behavior differs but tested metric semantics agree**;
- **written contract does not specify a complete result-object schema**.

The contract requires `metric_interpretation=lower_bound` for partial qrels but does not define the complete-mode label or require A/B's exact output field names.

### Summary of difference classes

- observed A-vs-B disagreements: **0**;
- observed fresh-vs-A/B disagreements: **7 classes** outside the authorized test coverage;
- disagreements that appear to expose a reference inconsistency with explicit written contract language: **at least 1** (`benchmark_sha256` absent everywhere);
- disagreements driven by underspecified schema/validation scope: representation identity, group-ID scope, omitted collections, and UNKNOWN-role coupling;
- output-shape differences where metric semantics agree and the contract does not specify an exact schema: present.

### Deviations

Pre-freeze deviation preserved from the freeze receipt:

- the first stable-ID self-check attempted to sort Python dictionaries directly and raised a `TypeError`; the self-check harness was corrected before freeze without consulting reference behavior and without post-reveal repair of the evaluator.

Post-freeze tooling deviations:

- during the original comparison, exact raw GitHub materialization through one tool path was blocked; the four already-authorized files were materialized from authorized GitHub blob content and re-verified by Git blob identity instead;
- in this terminalization continuation, the ephemeral local scratch directory from the original comparison was no longer present, and attempts to rematerialize exact raw GitHub URLs were blocked by the environment. The comparison was therefore **not rerun or altered** in this continuation. Instead, the original same-run execution receipts above were preserved, while live GitHub state, the frozen implementation blob, the freeze receipt, the sanitized base branch, and all four authorized reference blob identities were re-verified before committing this record.

These tooling deviations did not expose additional answer-bearing repository content and did not require modifying the frozen implementation.

### Contamination status

`CLEAN WITHIN THE SPECIFIED APERTURE`

No prohibited pre-freeze reference material was exposed before freeze according to the frozen receipt. No Pilot scientific rows, scientific qrels/gold, target-system retrieval outputs, production BM25/Hybrid/Semantic-only/dense/lexical candidate retrieval, or Pilot Gate 1 execution was used in the post-reveal comparison.

### CI / workflow receipts

CI is recorded separately from research disposition.

- GitHub workflow runs associated with the pre-terminal branch head `c2b8e826a8235c28d1674035fe3ecfb0774e146e`: none observed when queried during terminalization.
- Local reference suite: `24 passed in 0.08s`.
- Local fresh translated-suite comparison: `38 passed, 0 failed`.
- Local normalized three-way comparison: `21 agree, 0 disagree`.

A green local or CI check is not by itself the research disposition.

## INFERENCE

The observations strongly support independent reproducibility of the core External Corpus Retrieval Evaluator v0.3 metric semantics exercised by the frozen fixtures and authorized suite. In particular, the query-local nDCG clarification that motivated v0.3 reproduced without reference exposure before freeze, and every behavior represented by the authorized suite agreed across the frozen fresh implementation and both reference evaluators.

The observations do **not** establish complete evaluator-contract reproducibility across validation and interface semantics. A genuinely fresh implementation made several validation choices that differ from both references. Some differences arise because the written contract does not define the relevant schema or uniqueness/default scope precisely enough; at least one difference instead shows A/B accepting an artifact that the written contract explicitly says must carry a required identity.

Because validation/fail-closed behavior is itself part of the evaluator contract and part of the requested independence prerequisite, the evidence does not justify treating the complete v0.3 evaluator as unambiguously independently reproducible. At the same time, the agreement is too strong and the disagreement causes too mixed to characterize the core evaluator semantics as simply falsified.

The bounded conclusion is therefore: **core tested metric semantics are independently reproduced, but the full v0.3 contract/reference behavior remains insufficiently specified or aligned on uncovered validation surfaces to clear the evaluator-independence prerequisite without qualification.**

## HYPOTHESES

1. `representation_identity` was intended as the normative field name, but the v0.3 written contract failed to freeze that schema detail.
2. Group-ID uniqueness was intended to be query-local because groups are nested under queries, despite the unqualified phrase `unique group_id`.
3. UNKNOWN relevance degree and UNKNOWN role were intended to be coupled, but that coupling was omitted from the normative validation text; alternatively, A/B correctly implement independent degree/role dimensions and the fresh implementation is simply over-strict.
4. Missing `judgments` and `groups` keys were intended to mean empty collections, but that default exists in the references rather than clearly in the contract.
5. Required identity keys were intended to be present as well as equal, making A/B's all-missing acceptance a reference implementation defect rather than intended behavior.
6. A/B's extra result fields and `point_estimate` label are implementation conveniences rather than normative v0.3 interface requirements.
7. A small successor contract clarification plus a separately fresh reproduction could discriminate these remaining interpretations without changing the scientific Pilot object.

## UNKNOWNS

This experiment does not establish:

- benchmark validity;
- benchmark decision discrimination against weak retrieval systems;
- Pilot 0A methodology validity;
- scientific adjudication validity;
- scientific qrel/gold quality;
- corpus quality, authority, completeness, or passage stability;
- Evidence Bundler retrieval performance;
- BM25, Hybrid, Semantic-only, dense, lexical, or reranked retrieval performance;
- target-system scientific behavior;
- whether the uncovered validation disagreements would occur on any separately governed Pilot scientific artifact;
- which interpretation of the representation-identity field, group-ID uniqueness scope, UNKNOWN-role coupling, or missing collection semantics should become canonical without a further explicit contract decision.

No Pilot scientific Gate 1 execution was performed or authorized by this record.

## DISPOSITION

INCONCLUSIVE
