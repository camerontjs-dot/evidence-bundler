# Evidence Bundler machinery audit baseline — 2026-08-29

## Scope

Research Infrastructure machinery audit against production base
`6011789957f3294f97bff260069cfb5bb1c5772f`.

This audit is explicitly separate from External Corpus Pilot scientific evaluation. Synthetic machinery smokes are not retrieval-quality evidence.

## OBSERVED

### Production retrieval machinery exists

The current codebase contains executable implementations for:

- deterministic source loading/chunking;
- BM25 child retrieval;
- SentenceTransformer semantic indexing/search;
- Reciprocal Rank Fusion hybrid retrieval;
- max-child parent aggregation;
- parent-level cross-encoder reranking;
- contradiction/limitation query expansion;
- contradiction text-role gating;
- review/finalization and retrieval reporting.

The ordinary bundle writer currently supports production `bm25` and `hybrid` paths. Although `semantic` is present in the `RetrievalMethod` type and CLI choice, `_assert_retrieval_method_available` explicitly rejects semantic-only bundle construction.

### Real-model smoke

Audit workflow run `33274011534` executed the real-model job successfully.

The job loaded the configured defaults:

- embedding model: `BAAI/bge-small-en-v1.5`
- reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`

On the synthetic paraphrase query `heart attack outcomes`:

- BM25 found the intended cardiac passage with score `0.5030201388527583`;
- semantic retrieval ranked the intended cardiac passage first with score `0.695410966873169`;
- hybrid RRF ranked the cardiac passage first;
- repeat semantic calls produced identical IDs and scores.

For the reranker control `Administrator actions are logged.`:

- audit passage rerank score: `6.813648700714111`;
- unrelated weather passage: `-11.387567520141602`;
- repeat reranker calls were identical.

Artifact from this run:
- id: `9720958204`
- archive digest: `sha256:8f2a96ce4e3389c03f92e2035abda75c50c9a032cbacaaae76466c5bd4978eb3`

This establishes only that the configured real model families can execute through the retrieval components on hosted infrastructure.

### Deterministic suite

On the same audit run:

- package installation succeeded;
- full pytest suite succeeded;
- repository-wide Ruff then failed.

The Ruff failure included one audit-file formatting defect plus four pre-existing findings in `src/evidence_bundler/contracts/factual_context.py`. The audit-file defect was corrected. The workflow was changed so pre-existing repository lint debt is recorded but cannot mask the separate audit-addition gate.

A corrected rerun is recorded separately by the workflow history.

### Configuration-surface findings

1. **Model revisions are not immutable.**

`RetrievalConfig` records model names, but the embedding and cross-encoder loaders do not require an immutable Hugging Face revision SHA. Therefore an unchanged retrieval-config hash can refer to different upstream model bytes over time.

This differs from CAL, whose production retriever and entailer refuse unpinned model revisions.

2. **`semantic_child_top_k` appears unwired in the live hybrid bundle path.**

The field exists in `RetrievalConfig`, is exposed by the CLI, and is reported in config output. But `_retrieve_hybrid_claim` invokes both BM25 and semantic retrieval with `rrf_candidate_pool`.

Therefore changing `semantic_child_top_k` does not appear able to affect normal hybrid candidate generation.

3. **Semantic-only is an advertised but unavailable end-to-end method.**

The CLI accepts `--method semantic`, but the writer rejects it before bundle execution.

4. **CLI help is stale for hybrid.**

The `--method` help still says semantic and hybrid writer paths are not wired, while hybrid is live.

5. **Chunk geometry is not a retrieval-config knob.**

`ChunkSpec` defaults to:
- `max_chars=1800`
- `overlap_chars=80`

The retrieval writer calls `chunk_source_documents(documents)` without passing a configurable ChunkSpec. Chunk size/overlap can materially affect retrieval but are not currently part of the normal retrieval experiment configuration/hash.

6. **Parent aggregation has only one implementation.**

The config currently accepts only `max`. There is no alternate aggregation strategy to compare yet.

7. **Hybrid budgets are partially coupled.**

Normal hybrid uses `rrf_candidate_pool` for both lexical and semantic child rankings. Reranking occurs after parent aggregation; the parent pool is enlarged to `max(top_k, rerank_top_n)`, the first `rerank_top_n` parents are reranked, and output is truncated to `top_k`.

8. **Existing deterministic comparison is not a real-model quality benchmark.**

`scripts/run_phase_2b_unit6_comparison.py` deliberately uses a fake embedder and fake cross-encoder. It is useful wiring evidence but cannot establish the quality of the production models.

## INFERENCE

Evidence Bundler is no longer at the stage of “does retrieval machinery exist?” It does.

The immediate barrier to meaningful optimization is the **experimental control surface**:

- model identities need to become immutable;
- dead/misleading configuration fields need reconciliation;
- chunk geometry needs to be explicitly controlled if it is to be optimized;
- semantic-only must either become a real end-to-end arm or stop being advertised as one.

A broad parameter sweep before those corrections would produce results whose independent variables are partly fictitious or insufficiently pinned.

## HYPOTHESES

- Hybrid + reranking is a reasonable high-recall candidate architecture, but no current evidence establishes it as globally optimal.
- Different use cases will likely prefer different retrieval budgets or contradiction settings.
- Chunk geometry may interact strongly with retrieval model and claim morphology and therefore should be treated as an experimental variable rather than a fixed ingest implementation detail.
- Contradiction retrieval may improve adverse/counterevidence recall but its lexical text gate may create a distinct false-positive/false-negative tradeoff.

## UNKNOWNS

This audit does not establish:

- retrieval recall/precision on a representative external corpus;
- optimal `top_k`, RRF, rerank, contradiction, or chunk settings;
- optimal model families;
- latency/cost tradeoffs across configurations;
- subgroup performance by claim/use-case morphology;
- scientific Pilot validity;
- evaluator independence sufficient for Pilot Gate 1.

The v0.3 external-corpus evaluator reproduction remains a separate research question and its terminal result must not be inferred from this machinery smoke.

## NEXT

### A. Configuration-surface hardening

Before optimization:

1. pin embedding and reranker model revisions;
2. decide whether `semantic_child_top_k` should be wired separately or removed;
3. make semantic-only either executable end to end or remove it from the advertised experiment surface;
4. expose/hash ChunkSpec for research runs;
5. correct stale CLI help;
6. preserve the existing production defaults until separate evidence justifies changing them.

### B. Retrieval characterization, not “one global optimum”

After A, freeze a use-case-stratified corpus and sweep blocks of variables rather than one combinatorial grid:

1. **candidate-generation budget**: chunk geometry, lexical/semantic child pools, parent top-k;
2. **retrieval family**: lexical vs semantic vs hybrid;
3. **fusion**: RRF pool and k;
4. **reranking**: enabled/disabled and top-N;
5. **counterevidence**: contradiction pass, prefixes, text gate, contradiction top-k/rerank.

Measure at minimum:
- relevant-source/passage recall at K;
- counterevidence recall;
- false-positive candidate burden / precision proxy;
- no-candidate rate;
- latency/model cost;
- worst subgroup performance.

Keep use-case-specific optima separate unless evidence supports one shared configuration.
