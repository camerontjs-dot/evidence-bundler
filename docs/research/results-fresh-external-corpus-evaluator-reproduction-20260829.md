# Evidence Bundler External Corpus Evaluator Independence — Fresh Reproduction

## Terminal record

Scope: Research Infrastructure / evaluator-independence only.

This execution did not run Evidence Bundler retrieval, inspect Pilot scientific source rows or scientific gold, inspect FreshStack qrels/nuggets, inspect prohibited SciFact evidence/rationale, construct a larger apparatus, or modify the frozen Pilot scientific object.

## OBSERVED

### Bootstrap and durable-governance identity

Bootstrap manifest retrieved at exactly:

- repository: `camerontjs-dot/evidence-bundler`
- ref: `417f352400685c5d4db31b8e23f13c530857105a`
- path: `docs/research/pilot0a-fresh-context-isolation/authority-manifest-v3.json`
- Git blob: `ee3cf5ec59f4228b96af5b70c7c0fa439bbe2f3a`

The nine manifest-required durable governance attachments were present as uploaded files and SHA-256 matched exactly:

- `CAL-PIPELINE-PROJECT-CONTEXT.md` -> `f5f4081e8d4942f7eb993d937c9e46c80e5a8898811d795f76e2dcb3e7c51caa`
- `PRODUCT-NORTH-STAR.md` -> `fedf1cb2f7473f427455c88137ad05164fa935c2584df383ed2eb8f609f01f64`
- `GITHUB-AND-PR-GOVERNANCE.md` -> `515b7541313c8ace8807fd1ca46d8ade0569521845e0e68f927d0783202d637c`
- `PROJECT-STATE-LOCATION-POLICY.md` -> `dcf80aee6abfa9f4d67f1a8d10176297ea96defb123bce16f4ef1e0187b6085c`
- `EPISTEMIC-RECORD-CONVENTIONS.md` -> `df571d1bfb809b2ec6eada35c16f70d4d2697b9dca0f09c3502fff2ed4b19c25`
- `RELEASE-AND-VERSION-GOVERNANCE.md` -> `15047684338f726ff598575498c06f53e0e0b7dbfab58817c31c2ed827d1b03a`
- `AGENT-TASK-DESIGN-GUIDANCE-SYNTHESIS.md` -> `3ac309c059aea19c8fa4f6c0fb963933018fb299339073ef4252feeff7517279`
- `CAL-PIPELINE-WRITING-STYLE-GUIDANCE.md` -> `b8a36814e9bbd8fdba5ef0b1ab9b70d87d5e5058364a11fd124f1827ec5ac66b`
- `CONTEXT-FREE-EXECUTION-PROTOCOL.md` -> `3c97f27922398cb311a122046d89ac443342a48f675ff01faad344cc0890e30d`

An additional uploaded `PROJECT-FILE-MANIFEST(2).md` was not opened because it was not listed by the v3 manifest as authorized durable governance for this execution.

### Exact pre-freeze task-specific sources opened

All were retrieved at source head `764144f3da77140a8e542158948b4e88d40a7421` and matched the v3 manifest-pinned Git blobs:

- `research/external_corpus_evaluator_independence_v1/contract.md` -> `61ad95dab08c89c34e3416c2a3b9b0f35dabb7f0`
- `research/external_corpus_evaluator_independence_v1/dummy_manifest.json` -> `f2d0c1ff3b39d20c92878d75d8a345bc152f971d`
- `research/external_corpus_evaluator_independence_v1/dummy_run.json` -> `45b9ef6e005fd7e005ec75305c2829fa241f8f81`
- `research/external_corpus_evaluator_independence_v1/revealed_dummy_gold.json` -> `c6960cebeafa4c5dd214d7f32d47e68294a3f4da`

No existing evaluator, canonicalizer, evaluator-independence test, expected-result/prior-comparison artifact, prior evaluator implementation reasoning, or Pilot scientific/retrieval material was intentionally opened before freeze.

### Independent implementation and freeze

Fresh branch:

`research-infra/fresh-evaluator-reproduction-20260829-contextfree`

Base SHA:

`764144f3da77140a8e542158948b4e88d40a7421`

Frozen implementation:

`research/external_corpus_evaluator_independence_fresh_reproduction_20260829/fresh_external_corpus_evaluator.py`

Implementation freeze commit:

`dfb9912f871f0ca5bba295609da1929bcf883e67`

Implementation Git blob:

`28b8a50df9c073eaf13db30f6264304b75be567c`

Implementation SHA-256:

`a1c18384627b929a434f38a81762b592b2483661dc81e11e0a210c1a12a4de5a`

Freeze receipt commit:

`8345da9f7d324a857d50af460546b5bcedf74e1c`

The implementation was re-fetched after reveal and remained the same Git blob `28b8a50df9c073eaf13db30f6264304b75be567c`. No post-reveal implementation edit was made.

### Pre-freeze commands/checks

Executed before comparison reveal:

- `python -m py_compile /mnt/data/fresh_external_corpus_evaluator.py`
- `python /mnt/data/fresh_external_corpus_evaluator.py /mnt/data/dummy_manifest.json /mnt/data/revealed_dummy_gold.json /mnt/data/dummy_run.json`
- contract-derived pre-freeze self-check harness covering identity mismatch, malformed rank, duplicate hit, unknown hit, unknown judgment, invalid UNKNOWN encoding, partial-qrels lower-bound behavior, counterevidence/group sensitivity, role mutation, canonical serialization invariance, semantic commitment mutation, stable passage-ID rename invariance, and source/passage permutation invariance

Observed pre-freeze baseline fresh metrics:

- `hit@K` macro: `1.0`
- evidence recall macro: `1.0`
- counterevidence recall macro: `0.5`
- joint group coverage macro: `0.75`
- judgment coverage macro: `1.0`
- resolved judgment coverage macro: `1.0`
- `q1 nDCG@K`: `0.938506417451168`
- `q2 nDCG@K`: `null`
- nDCG macro over defined queries: `0.938506417451168`
- hidden-gold commitment: `2d0e0d99d23295b91c838e01a4e1a6274e2a77af45cd52ab834ed78fd5b6131f`

### Post-freeze comparison surfaces opened

At pinned source head `764144f3da77140a8e542158948b4e88d40a7421`:

- `evaluator_a.py` -> Git blob `0d97c5f057ace0fe97211640b764eb6d7824ddfa`
- `evaluator_b.py` -> Git blob `39eff5c55a553b7af60a1599388a8a651eb80e75`
- `canonical.py` -> Git blob `29f3d86c2b043cd450f65df39eecdd448b4ff7f4`
- `tests/test_external_corpus_evaluator_independence.py` -> Git blob `269db78be4330304792fef7d136302e655b19c16`
- `dummy_gold_commitment.sha256` -> Git blob `da36dcd8de0e7fff4a2eb84eab6475c2663965d1`
- `.github/workflows/external-corpus-evaluator-independence.yml` -> Git blob `425bca9dec8f233891fc2ef9276d5cff349c0f83`

### Agreements

The fresh implementation agrees with the revealed contract machinery on the dummy fixture for:

- hit@K;
- evidence recall@K;
- counterevidence recall@K;
- jointly-required / alternative-sufficient group coverage;
- judgment coverage;
- resolved-judgment coverage;
- fail-closed treatment of the revealed malformed-run cases;
- partial-qrels `metric_interpretation=lower_bound` behavior;
- canonical serialization invariance;
- semantic commitment mutation sensitivity;
- stable-ID metric invariance;
- source/passage serialization-order metric invariance.

The fresh canonical commitment for the authorized dummy gold was `2d0e0d99d23295b91c838e01a4e1a6274e2a77af45cd52ab834ed78fd5b6131f`, exactly matching the revealed committed hash.

### Material disagreement

The fresh implementation does not reproduce the revealed evaluator A/B nDCG eligibility semantics on the authorized dummy fixture.

The contract says to compute metrics per query first, and says nDCG is computed only if, among other conditions, no unresolved `UNKNOWN` judgment exists. The fresh implementation interpreted that eligibility condition per query. Therefore:

- q1 has no unresolved UNKNOWN and has at least two positive gain levels, so fresh q1 nDCG is `0.938506417451168`;
- q2 contains an unresolved UNKNOWN, so fresh q2 nDCG is `null`.

Both revealed evaluators instead accumulate UNKNOWN state across all gold queries and compute one global `ndcg_allowed`/`allow_ndcg` flag. Because q2 contains one unresolved UNKNOWN, both disable nDCG for q1 and q2.

The revealed adversarial test `test_independent_implementations_agree_on_dummy_run` explicitly requires `ndcg_eligible is False` on the dummy fixture. `test_ndcg_only_when_graded_complete_and_no_unknowns` changes q2's UNKNOWN row to resolved irrelevant and then expects nDCG eligibility to become globally true.

This is a semantic disagreement, not a parser/environment failure. Repairing the fresh implementation after reveal would violate the independence claim, so no repair was made.

### Non-material representation difference

For complete qrels, evaluator A/B emit `metric_interpretation="point_estimate"`; the fresh implementation emits `"complete_relevant_set"`. The contract explicitly requires `lower_bound` for partial qrels but does not prescribe the complete-mode label. This is preserved as a representation difference and is not the basis for the terminal disposition.

### CI / execution receipts

Pinned source head `764144f3da77140a8e542158948b4e88d40a7421` has GitHub Actions run:

- run ID: `33232925008`
- workflow: `External corpus evaluator independence`
- event: pull request
- conclusion: `success`
- Python 3.11 job: `success`
- Python 3.12 job: `success`
- exact test command in both jobs: `python -m pytest -q tests/test_external_corpus_evaluator_independence.py`

This establishes that the revealed A/B implementations and revealed adversarial test suite were green together at the pinned source head.

A post-freeze comparison test file and narrowly scoped comparison workflow were added on the fresh branch after reveal. GitHub reported zero workflow/check runs for connector-originated branch updates, so no fresh-branch CI result is claimed. This is an execution-infrastructure limitation, not evaluator evidence.

Draft research PR: #33, targeting `research-infra/external-corpus-evaluator-independence-v1`, not `main`.

### Deviations / contamination

No known prohibited answer-bearing surface was intentionally opened before implementation freeze.

Post-freeze, a repository-workflow directory listing was inspected only to diagnose absent CI and the exact evaluator-independence workflow was opened. This occurred after reveal and does not affect the frozen implementation-independence claim.

No scientific or retrieval material was opened or executed.

## INFERENCE

The bounded claim that a genuinely fresh implementation can reproduce the frozen evaluator contract is not supported by this run.

The fresh implementation independently reproduced most metric, validation, mutation, invariance, and canonicalization behavior, but it reached a different nDCG eligibility rule from the same frozen contract and authorized dummy inputs. Because evaluator A, evaluator B, and the frozen adversarial tests agree on the global interpretation, the difference is stable in the existing apparatus rather than an A/B implementation split.

The strongest supported inference is that the contract is insufficiently explicit about the scope of the unresolved-UNKNOWN nDCG gate for independent reproduction. Another possible explanation is that the fresh implementation chose the wrong reading of an intended global rule. The current run cannot distinguish those explanations without changing or authoritatively clarifying the contract, which would create a new object requiring a new fresh reproduction.

This result is about evaluator reproducibility only. It is not evidence about Pilot methodology validity or Evidence Bundler retrieval performance.

## UNKNOWNS

This dummy reproduction cannot establish:

- which nDCG scope rule is scientifically preferable;
- whether the intended contract should be changed to global or per-query UNKNOWN gating;
- whether other untested edge cases contain further under-specification;
- Pilot 0A source reconstruction, adjudication, passage stability, gold stability, or methodology validity;
- FreshStack or SciFact scientific judgment quality;
- Evidence Bundler BM25, Hybrid, Semantic-only, dense, lexical, reranked, or any other retrieval performance;
- whether a corrected/clarified evaluator contract would independently reproduce in a new clean-room execution.

## DISPOSITION

**FALSIFIED**

Falsified specifically: the bounded independent-reproduction claim for the frozen external-corpus evaluator contract.

The frozen fresh implementation materially disagrees with the existing evaluator A/B plus adversarial-test contract on nDCG UNKNOWN-gating scope. The disagreement was discovered only after the required freeze and has been preserved without repair.

This disposition does not falsify Pilot 0A science, scientific gold, benchmark validity, or Evidence Bundler retrieval.

It does not authorize scientific Gate 1. The smallest justified next step is to resolve the nDCG scope ambiguity in a separately governed contract revision, freeze that revision, and perform a new genuinely fresh evaluator reproduction against the revised contract before any Pilot scientific execution.
