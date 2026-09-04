# Evidence Bundler Retrieval Control Surface RC0 Preregistration

Classification: Research Infrastructure / retrieval apparatus only.

This is not an External Corpus Pilot scientific run. It does not authorize inspection or modification of Pilot scientific gold, qrels, relevance judgments, or target-system performance. It does not authorize retrieval-parameter optimization.

## Frozen implementation base

- Repository: `camerontjs-dot/evidence-bundler`
- Base branch: `main`
- Base SHA: `6011789957f3294f97bff260069cfb5bb1c5772f`
- Base tree: `86e43da442d1b785ca8d886381ce4f5461838b25`
- RC0 branch: `research/retrieval-control-surface-rc0-20260829`

No implementation change is authorized by this record beyond the smallest control-surface hardening required to test the falsifiers below.

## Research question

Can Evidence Bundler expose a small, truthful, immutable retrieval experiment surface in which every advertised independent variable actually changes the machinery it claims to control?

## Verified pre-change observations

### OBSERVED

1. `RetrievalConfig.retrieval_method` advertises `bm25`, `semantic`, and `hybrid`.
2. The normal bundle writer rejects `semantic` before execution.
3. The hybrid positive-retrieval path passes `rrf_candidate_pool` to both BM25 and semantic retrieval. `semantic_child_top_k` is therefore not an independent live control in that path.
4. `load_embedding_model(...)` and `load_reranker_model(...)` accept model names but do not pass a Hugging Face revision.
5. The semantic-index manifest records the embedding model name but not a model revision.
6. The normal writer calls `chunk_source_documents(documents)` without an explicit `ChunkSpec`.
7. At the frozen base, `ChunkSpec()` defaults are `max_chars=1800` and `overlap_chars=80`. This disagrees with machinery-audit PR #36 `RESULTS.md`, which reports `3200/300`. RC0 treats the live base code as authority and preserves the disagreement.
8. `_retrieval_config_hash(...)` at the frozen base serializes `RetrievalConfig` directly, excluding only cache/index filesystem paths. Therefore live retrieval fields already participate in that hash. This disagrees with PR #36's statement that production retrieval fields are absent from the config hash.
9. CLI `build-bundle --method` accepts all three families while its help says semantic and hybrid writer paths are not wired, even though hybrid is live.
10. The deterministic comparison machinery uses deterministic fake semantic/reranker implementations and is wiring evidence only, not real-model retrieval-quality evidence.
11. Production defaults currently leave model revisions unpinned. Changing those defaults would change production loading behavior.

### INFERENCE

- Model revision identity can be added without changing default production loading by making revision fields optional and making immutable-revision enforcement opt-in for research execution.
- Chunk geometry can be made explicit in `RetrievalConfig` at the current live defaults and passed to `ChunkSpec`, preserving default chunk output while bringing geometry into retrieval identity.
- `rrf_candidate_pool` can remain the hybrid lexical candidate budget and `semantic_child_top_k` can become the independent hybrid semantic candidate budget. Their current defaults are both 50, so the default hybrid candidate counts remain unchanged.
- Semantic-only can be retained with a small writer-path addition using the same semantic index, parent aggregation, report, manifest, and bundle writer machinery.

### UNKNOWN

- No retrieval-quality effect of any family, budget, model, reranker, contradiction setting, or chunk geometry is established here.
- No Pilot scientific evidence is in scope.
- Real-model numerical equivalence across different model-repository revisions is not assumed and is not needed for the identity test.

## Intended immutable model objects for RC0 research receipts

Authoritative Hugging Face repository metadata observed before implementation:

- Embedding default `BAAI/bge-small-en-v1.5`: repository revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`.
- Reranker default `cross-encoder/ms-marco-MiniLM-L6-v2`: repository revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`.

These revisions are recorded for research configuration and receipts. They MUST NOT be silently installed as production defaults.

## Explicit falsifiers

RC0 is falsified or only partially ready if any of the following survives the attempted hardening:

1. **Advertised-parameter no-op**: changing an advertised independent parameter does not change the corresponding execution path or declared apparatus provenance.
2. **Model-identity collision**: two different immutable model revisions can produce the same declared retrieval identity/hash.
3. **Impossible advertised family**: an advertised retrieval family cannot execute end to end through the normal retrieval bundle machinery.
4. **Geometry identity collision**: changing chunk geometry does not alter the declared retrieval experiment identity/provenance.
5. **Budget coupling**: supposedly independent lexical and semantic candidate budgets remain mechanically coupled.
6. **Default drift**: the existing default configuration changes retrieval/chunk/model-loading behavior beyond newly explicit provenance.
7. **Declared/executed mismatch**: a configuration can claim one apparatus while executing another.
8. **Persisted-index revision aliasing**: a semantic index created for one embedding-model revision can be accepted as matching another declared revision.
9. **Loader revision drop**: an explicit model revision is present in configuration/identity but is not passed to the model loader.

Failures and disagreements are evidence and must be preserved. Test expectations must not be weakened merely to make RC0 pass.

## Minimal implementation decisions frozen before coding

1. Add optional embedding and reranker revision fields.
2. Add an opt-in immutable-revision requirement for research execution. When enabled, semantic/hybrid execution requires a full 40-hex embedding revision; enabled reranking also requires a full 40-hex reranker revision. Default remains off.
3. Include model revisions and immutable-execution declaration in `RetrievalConfig`, therefore in the existing retrieval identity/hash.
4. Record embedding revision in the semantic-index manifest and reject revision mismatch.
5. Make chunk max/overlap explicit retrieval-config fields with frozen live defaults `1800/80`; pass them to `ChunkSpec`.
6. Keep `rrf_candidate_pool` as the hybrid lexical candidate budget and wire `semantic_child_top_k` as the hybrid semantic candidate budget. Default behavior remains 50/50.
7. Retain semantic-only and implement it through the normal writer path. Semantic-only uses `semantic_child_top_k` and the shared parent-aggregation/provenance machinery.
8. Correct CLI help so advertised methods match executable behavior. Do not add optimization guidance.

## Required discriminating tests

- Model revision mutation changes retrieval hash and the loader receives the new revision.
- Immutable execution fails closed for missing/non-commit revisions.
- Semantic-index manifest revision mismatch is rejected.
- Semantic budget mutation changes the semantic child candidate set before fusion while the lexical budget remains fixed.
- Lexical budget mutation changes the lexical child candidate set while the semantic budget remains fixed.
- Chunk geometry mutation changes retrieval identity and generated chunk/corpus apparatus provenance.
- BM25, semantic-only, and hybrid each execute their intended deterministic synthetic path.
- Existing defaults retain `1800/80` geometry, unpinned model loading, and the current 50/50 hybrid candidate budgets.

## Success boundary

`CONTROL_SURFACE_READY` is permitted only if the hard tests show that the retained advertised controls are mechanically live, immutable research execution fails closed, declared identity tracks the manipulated apparatus, semantic-only executes normally, and default production behavior is preserved.

Passing these tests does not authorize Retrieval Characterization RC1, parameter optimization, Pilot scientific execution, or any retrieval-quality claim.