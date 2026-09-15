# Evidence Bundler V1 Stage-A smoke freeze

**Status:** `FROZEN_FOR_STAGE_A_SMOKE_PREPARATION`

**Profile:** `eb-v1-pilot-10x3-smoke-rc0`

**Scope:** first 10-claim CAL Pipeline Stage-A smoke only.

This is a Research Infrastructure freeze record. It does not change Evidence Bundler production behavior, merge the V1 candidate, qualify a production retrieval default, release a version, or authorize automatic action.

## Frozen object

Use exactly:

- Evidence Bundler implementation commit: `c4e3f97ec8f0bd36180954c3aa382418925bf947`
- implementation tree: `1d254e38cb0e174635efc7687c2b0ab091aa52b3`
- configuration identity: `sha256:5b10d0c29794e80d6876a99e26bcf6ec6a27a4c5165aee78054a6bc32759f4bc`

Configuration:

```json
{
  "candidate_depth": 10,
  "retained_k": 3,
  "chunk_max_chars": 1800,
  "chunk_overlap_chars": 80,
  "root_diagnostic": false,
  "retrieval_engine": "evidence_bundler_okapi_bm25_v1",
  "tokenizer": "lowercase_word_v1",
  "bm25_k1": 1.5,
  "bm25_b": 0.75,
  "source_scope_policy": "all_contract_a_sources",
  "query_strategy": "exact_primary_target_text"
}
```

The hash is computed using the V1 package canonical JSON algorithm: sorted keys, compact separators, UTF-8, and a trailing newline.

## Why this profile

The Stage-A smoke needs a baseline that is inspectable enough to preserve deeper lexical nominations without automatically widening the retained review set.

The existing research record establishes:

- `5/3` can lose required evidence at candidate generation;
- increasing candidate depth to 10 can expose the preserved rank-7 item;
- fixed `10/7` can retain that item but was subsequently falsified as a qualified default on review/noise burden and reviewer-action stability;
- the tested frozen-pool facility-location selectors did not improve over fixed K=3.

Therefore the smoke freezes `10/3`: preserve a deeper candidate aperture for diagnosis while retaining the smaller fixed selection budget. A useful passage at rank 4-10 may therefore appear in the trace as `not_retained`. That is an expected, informative failure mode, not permission to tune K during the smoke.

## Trace boundary

The native V1 package remains the retrieval-trace authority for the smoke. Preserve it unchanged for every claim.

At minimum preserve:

- exact Contract A input identity;
- exact configuration and `config_sha256`;
- retrieval/query/proposition identities;
- candidate order through depth 10;
- nomination rank;
- retained versus not-retained state;
- admission state;
- source and passage IDs/hashes and offsets;
- retrieval aperture state;
- whole-package identity;
- warnings, failures, and irregularities.

Raw BM25 score is not part of the native V1 package contract. If the Stage-A harness records raw scores, keep them in a diagnostic-only, non-semantic sidecar that is identity-bound to the native package. Do not add score to the maintained V1 package as part of smoke preparation.

## Contract B seam

The smoke is **not yet executable end-to-end from this freeze alone**.

Current CAL V1 production-intent intake requires released Contract B 1.2.0. The maintained EB V1 package does not natively declare a current production Contract B projection. Earlier research demonstrated a compatibility-carrier pattern, but that older apparatus must not be silently treated as current V1 authority.

Before claim 1, freeze and qualify the smallest test-only projection/carrier from the exact native package above to released Contract B 1.2.0. It must:

1. add no semantic judgment;
2. preserve native EB output unchanged;
3. identify itself exactly in the run receipt;
4. bind emitted Contract B evidence back to exact EB proposition, passage, source, and admission identities;
5. treat any legacy compatibility fields as explicit compatibility payload rather than recovered Contract A authority;
6. fail closed on missing or malformed carrier state;
7. produce a Contract B object that validates under the exact released authority used by CAL;
8. preserve both the native EB package and the resulting Contract B package for reconstruction.

Do not route EB-private state directly into CAL merely to avoid this seam.

## Stop rules

During the 10-claim smoke:

- no K changes;
- no candidate-depth changes;
- no reranker;
- no embeddings;
- no query rewrite;
- no adaptive selection;
- no root diagnostic promotion;
- no proposition-compiler reopening;
- no tuning against observed smoke claims.

A retrieval miss, retention loss, admission failure, unsupported CAL semantic family, or other fail-closed result is evidence if its stage can be reconstructed.

After claim 10, decide separately whether this pilot profile should be retained for a larger cohort, replaced by another already-supported frozen profile, or returned to Evidence Bundler research. This freeze never silently becomes a production default.

## Evidence lineage

Relevant terminal/current records:

- Evidence Bundler PR #60 — V1 convergence record; frozen implementation `c4e3f97...`; product disposition `NOT_READY`.
- Evidence Bundler PR #72 — fixed K=7 gold completion; terminal `FALSIFIED` for fixed-K widening as the qualified default.
- Evidence Bundler PR #74 — task-aligned operational burden RC1; terminal `FALSIFIED / OPERATIONAL_DECISION_HARM_OBSERVED`.
- Evidence Bundler PR #77 — frozen-pool selector bake-off; `SETWISE_NOT_JUSTIFIED_ON_FROZEN_POOL`.
- MainFrame Live PR #20 — pipeline pilot preparation; useful harness conventions, but its earlier provisional 10/7 profile is superseded for this smoke by this later live-state reconciliation.

## Nonclaims

This freeze establishes only an exact pilot object and configuration. It does not establish retrieval quality, evidence completeness, a qualified production default, Contract B projection readiness, CAL semantic correctness, Decision Engine readiness, release readiness, or authorization for automatic MainFrame mutation/action.
