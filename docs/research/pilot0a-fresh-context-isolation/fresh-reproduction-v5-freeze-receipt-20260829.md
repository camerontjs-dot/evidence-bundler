# External Corpus Evaluator v0.3 Fresh Reproduction v5 — Pre-Reveal Freeze Receipt

Research Infrastructure only. This receipt records the information aperture and frozen independent implementation before any authorized reference evaluator/canonicalizer/test surface is opened.

## Freeze identity

- repository: `camerontjs-dot/evidence-bundler`
- sanitized base commit: `e14df1bd8239445ef0b0a07525b07ae9c2b78835`
- sanitized base tree: `a63098cabf02e78e2f27c8b5df827db02a0c06cf`
- implementation branch: `research-infra/external-corpus-evaluator-v03-fresh-reproduction-v5-20260829`
- implementation path: `research/external_corpus_evaluator_independence_v2/fresh_reproduction_v5.py`
- implementation bytes: `15266`
- implementation SHA-256: `6a7d08b87517d27e37ba9f371cfe52736a93130d1240279c73ccb6636a676355`
- implementation Git blob: `602f78a3416ae4eb3c2aafa64c6c4a91f2b04857`
- implementation freeze commit: `066ed4308e0d918a528248494763db200e96229c`
- freeze receipt authored before reveal at: `2026-08-29T19:24:04Z`

## Bootstrap source opened

- `docs/research/pilot0a-fresh-context-isolation/authority-manifest-v5.json` at bootstrap ref `0bbc848650bc60c8806357428dbb879336ba7f81`
  - verified Git blob: `8bf223467347551957bd53284892c380bb4a71ec`
- exact Git commit metadata for sanitized commit `e14df1bd8239445ef0b0a07525b07ae9c2b78835`
  - verified tree: `a63098cabf02e78e2f27c8b5df827db02a0c06cf`
  - parent was not traversed or opened

## Governance blobs opened and verified pre-freeze

1. `docs/research/pilot0a-fresh-context-isolation/governance-v5/CAL-PIPELINE-PROJECT-CONTEXT.md` — `5ce89ea50dcd467ef52dc741f986e951339eea65`
2. `docs/research/pilot0a-fresh-context-isolation/governance-v5/PRODUCT-NORTH-STAR.md` — `48e25f18e3070005a55088fe1a5d7a8ebe7427b4`
3. `docs/research/pilot0a-fresh-context-isolation/governance-v5/GITHUB-AND-PR-GOVERNANCE.md` — `e8f224a7464e62aaea468f43aa0f73139e2f7142`
4. `docs/research/pilot0a-fresh-context-isolation/governance-v5/PROJECT-STATE-LOCATION-POLICY.md` — `73c5721c1b85ceacfc626cdfd00a932fed464f53`
5. `docs/research/pilot0a-fresh-context-isolation/governance-v5/EPISTEMIC-RECORD-CONVENTIONS.md` — `7e99ff66f29cf52bc51617b0e025a03af7881344`
6. `docs/research/pilot0a-fresh-context-isolation/governance-v5/RELEASE-AND-VERSION-GOVERNANCE.md` — `aaa0e535263acb441d430a6f46484fafa5c47302`
7. `docs/research/pilot0a-fresh-context-isolation/governance-v5/AGENT-TASK-DESIGN-GUIDANCE-SYNTHESIS.md` — `33a503d35915ce1cff7eac7686300d7b58e7a282`
8. `docs/research/pilot0a-fresh-context-isolation/governance-v5/CAL-PIPELINE-WRITING-STYLE-GUIDANCE.md` — `4c84516bd6bf1da47171cddac34ec65f2746c633`
9. `docs/research/pilot0a-fresh-context-isolation/governance-v5/CONTEXT-FREE-EXECUTION-PROTOCOL.md` — `acb4282838919a38ce69926e986cb4292c6af954`

Git blob identities were verified through content-addressed GitHub blob reads. The manifest-recorded SHA-256 values were not independently recomputed because exact commit/tree/blob identity was already established and the manifest makes that cross-check optional.

## Evaluator inputs opened and verified pre-freeze

1. `research/external_corpus_evaluator_independence_v2/contract.md` — `3e77312723133ee7ec536d4414e547c7313b8fa8`
2. `research/external_corpus_evaluator_independence_v1/dummy_manifest.json` — `f2d0c1ff3b39d20c92878d75d8a345bc152f971d`
3. `research/external_corpus_evaluator_independence_v1/dummy_run.json` — `45b9ef6e005fd7e005ec75305c2829fa241f8f81`
4. `research/external_corpus_evaluator_independence_v1/revealed_dummy_gold.json` — `c6960cebeafa4c5dd214d7f32d47e68294a3f4da`
5. `research/external_corpus_evaluator_independence_v2/ndcg_scope_manifest.json` — `018323363aecb3b2528b9097177c9aa48f79e88b`
6. `research/external_corpus_evaluator_independence_v2/ndcg_scope_run.json` — `4e830255062b00406ba7c64cfff4126c1e16433b`
7. `research/external_corpus_evaluator_independence_v2/ndcg_scope_gold.json` — `f9c4133ef83e0fac350428a693847f0c79d7d33f`

## Other pre-freeze sources actually accessed

- the newly created independent implementation at its own freeze commit, fetched only to verify its Git blob;
- local derived/materialized copies of the seven authorized evaluator inputs for execution against the fresh implementation;
- local Python standard-library tooling and shell utilities used to compile, hash, and execute the implementation.

No ChatGPT project attachments were searched or used. No repository directory listing, adjacent file, historical PR body/comment/review/patch, or parent/history traversal was used for orientation.

## Pre-freeze execution receipts

Commands/functions executed locally before freeze:

- `python -m py_compile /mnt/data/fresh_external_corpus_evaluator_v03.py`
- `sha256sum /mnt/data/fresh_external_corpus_evaluator_v03.py`
- `wc -c /mnt/data/fresh_external_corpus_evaluator_v03.py`
- a Python execution of `evaluate(...)` on the authorized dummy fixture trio;
- a Python execution of `evaluate(...)` on the authorized nDCG-scope fixture trio;
- a contract-derived self-check script covering identity mismatch, malformed rank, unknown hit ID, serialization-order metric invariance, canonical commitment reorder invariance, semantic commitment sensitivity, consistent stable-ID metric invariance, and the query-local nDCG discriminator.

Observed pre-freeze fixture metrics included:

- broad dummy aggregate `nDCG@K = 0.938506417451168`; q1 nDCG defined; q2 nDCG null due to its own unresolved judgment;
- nDCG-scope discriminator q_clean `nDCG@K = 0.7098097413968655`; q_unknown nDCG null; aggregate nDCG equals q_clean only.

## Pre-freeze deviation

The first contract-derived stable-ID self-check harness attempted to sort Python dictionaries directly and raised `TypeError: '<' not supported between instances of 'dict' and 'dict'`. This was a self-check harness defect, not an evaluator result. The harness comparison was corrected before freeze by comparing deterministic JSON serializations of the per-query metric dictionaries. The corrected self-check passed. The evaluator implementation bytes were not changed in response to any reference behavior because no reference behavior had been opened.

## Independence / contamination declaration at freeze

Before this receipt:

- `research/external_corpus_evaluator_independence_v2/evaluator_a.py` was not intentionally opened;
- `research/external_corpus_evaluator_independence_v2/evaluator_b.py` was not intentionally opened;
- `research/external_corpus_evaluator_independence_v2/canonical.py` was not intentionally opened;
- `tests/test_external_corpus_evaluator_independence_v2.py` was not intentionally opened;
- v1 evaluator A/B/canonicalizer/tests were not intentionally opened;
- decision rationale, PR #34 narrative, PR #33 narrative/results, prior fresh reproduction implementations/results/reasoning, Pilot scientific rows/gold, FreshStack scientific qrels/nuggets, SciFact rationale, and Evidence Bundler retrieval outputs were not intentionally opened.

Contamination status at freeze: `CLEAN WITHIN THE SPECIFIED APERTURE`.

The implementation at `066ed4308e0d918a528248494763db200e96229c` is frozen for the independence claim. It must not be edited after authorized reveal and still be called the same independent run.
