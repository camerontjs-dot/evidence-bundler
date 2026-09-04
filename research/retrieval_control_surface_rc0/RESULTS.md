# Retrieval Control Surface RC0 — Terminal Reconciliation

Status date: 2026-08-29

Primary classification: **RC0_APPARATUS_FAILURE**

This classification is narrow. RC0 reached a real source freeze and its deterministic implementation checks passed. The failure is in the research apparatus required to reproduce and characterize retrieval arms from durable receipts. It is **not** a retrieval-quality result and it is **not** `RC0_BEHAVIORALLY_FALSIFIED`.

No Pilot 0A scientific judgments, qrels, target-system performance, or hidden-gold material were used in this reconciliation.

## 1. Live authority record

### Repository authority

- Repository: `camerontjs-dot/evidence-bundler`
- `main` HEAD inspected before reconciliation: `6011789957f3294f97bff260069cfb5bb1c5772f`
- `main` tree: `86e43da442d1b785ca8d886381ce4f5461838b25`
- Machinery-audit PR: `#36`
- Machinery-audit branch: `research/machinery-audit-20260829`
- Machinery-audit head: `5ea66001790384b0f528e1a75a1affc5aef60843`
- Machinery-audit primary results: `research/machinery_audit/RESULTS.md`
- RC0 preregistration blob at the frozen line: `0309516e01b696c81aeb7b7a8068c28fdc4ced3e`

Open PRs observed during reconciliation:

- `#36` — machinery audit baseline
- `#35` — terminal external-corpus evaluator v0.3 fresh reproduction
- `#34` — external-corpus evaluator contract v0.3 clarification
- `#7` — Contract A decomposition sensitivity

The terminal evaluator-independence disposition in PR `#35` is `INCONCLUSIVE`. This record does not borrow Pilot evaluator validity for retrieval characterization.

### RC0 lineage

- RC0 branch: `research/retrieval-control-surface-rc0-20260829`
- Earlier implementation head inspected: `2874974548174f6cc68ff96b5e2bd1235b50b031`
- Reconciliation repair commit: `18b0a67bb1c1d8e20589106a49e6a500dcfdf884`
- Frozen RC0 implementation commit: `a02a9d313816ad8302efbcbb24bca265c31473e7`
- Frozen RC0 tree: `9774b82c4c0be5ebbe190f7d8d120836fc7b354c`
- Frozen commit parent: `18b0a67bb1c1d8e20589106a49e6a500dcfdf884`

The frozen RC0 branch is unprotected. The SHA above, not the moving branch name, identifies the frozen implementation object.

## 2. Terminal reconciliation

### OBSERVED — earlier transport failure

An earlier hosted run completed the implementation checks with:

- `207 passed`
- `5 skipped`
- Ruff clean
- scoped mypy clean
- CLI truthfulness checks clean

The runner then created local freeze commit `60f38d1`, but GitHub rejected the push because the Actions-authored commit attempted to add/update `.github/workflows/research-retrieval-control-surface-rc0.yml` without workflow-file mutation permission.

That was a transport/authentication failure. It did not falsify retrieval machinery.

### OBSERVED — reconciliation repair

The RC0 preregistration required independent lexical- and semantic-budget mutation checks. The existing generated mutation suite covered semantic budget but did not contain an independent lexical-budget mutation test.

Commit `18b0a67bb1c1d8e20589106a49e6a500dcfdf884` made the smallest reconciliation repair:

1. added a lexical-budget mutation spy demonstrating that `rrf_candidate_pool` changes the BM25 pre-fusion call while the semantic budget remains fixed;
2. kept the already established scoped-mypy boundary;
3. removed the generated permanent workflow before the Actions-authored freeze so workflow-token scope could not block a source/test freeze.

No production retrieval default was intentionally changed by this repair.

### OBSERVED — successful freeze

GitHub Actions run `33280761548`, job `99175421755`, checked out `18b0a67bb1c1d8e20589106a49e6a500dcfdf884` and completed successfully.

Observed gates:

- `208 passed, 5 skipped`
- touched-file Ruff: clean
- RC0-touched mypy: clean across 5 source files
- guard confirming unrelated `src/evidence_bundler/contracts/factual_context.py` remained unchanged from `main`: clean
- CLI help truthfulness checks: clean
- temporary patch scripts removed before freeze
- freeze commit `a02a9d313816ad8302efbcbb24bca265c31473e7` created and pushed successfully

A manual retry of an older run later created a duplicate local freeze but lost a non-fast-forward race because the successful automatic run had already advanced the branch. That duplicate push failure is also transport history, not retrieval falsification.

### INFERENCE — terminal class

RC0 is not `RC0_IMPLEMENTED_NOT_FROZEN`: an exact frozen implementation exists.

RC0 is not `RC0_BEHAVIORALLY_FALSIFIED`: the deterministic checks did not expose a retrieval-machinery contradiction against the RC0 apparatus claims.

RC0 is not yet `RC0_FROZEN_AND_REPRODUCIBLE`: the frozen source object does not produce a sufficiently self-contained durable research-arm receipt, and the exact pinned real-model smoke was not executed on the final frozen SHA.

Therefore the terminal class is **RC0_APPARATUS_FAILURE**.

The smallest unresolved claim is reproducible experiment identity, not retrieval quality.

## 3. Implementation audit

### Model identity and immutable research mode

**OBSERVED**

`RetrievalConfig` now accepts full 40-hex model revisions for the embedding model and reranker. `require_immutable_model_revisions=True` requires an embedding revision for semantic/hybrid execution and a reranker revision when reranking is active. Non-40-hex values such as a branch name fail validation.

The SentenceTransformer and CrossEncoder loader boundaries pass the declared revision through to their underlying loaders. Mutation tests exercise both loader calls.

The semantic-index manifest binds:

- corpus hash;
- embedding model identity;
- embedding model revision;
- ordered chunk-set hash;
- embedding dimension and count;
- normalization setting.

A persisted semantic index with a different model revision or chunk-set hash is rejected rather than silently reused.

The preregistered exact model revisions exist upstream:

- `BAAI/bge-small-en-v1.5` at `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- `cross-encoder/ms-marco-MiniLM-L6-v2` at `233902d25c440f23af6f7d6e94d2946bac0bee0a`

**UNKNOWN**

The final frozen SHA did not execute `research/retrieval_control_surface_rc0/real_model_smoke.py`. Structural loader tests and upstream revision existence are not a substitute for a frozen-SHA real-model execution receipt.

### Semantic-only truthfulness

**OBSERVED**

`semantic` now executes through the ordinary `build_retrieval_bundle` path. It builds/loads a semantic index, queries with `semantic_child_top_k`, aggregates child hits to parents, writes a bundle, and reports semantic scores.

The CLI describes BM25, semantic, and hybrid as executable through the normal bundle path. The successful freeze workflow explicitly checked that the stale `not wired` help text was absent.

### Independent candidate budgets

**OBSERVED**

For the normal hybrid supporting pass:

- lexical child pool uses `rrf_candidate_pool`;
- semantic child pool uses `semantic_child_top_k`.

The frozen RC0 mutation suite independently demonstrates both controls:

- semantic budget mutation changes semantic pre-fusion candidate count while the lexical pool is held fixed;
- lexical budget mutation changes the BM25 pre-fusion `top_k` call while the semantic pool is held fixed.

**OBSERVED — remaining counterevidence coupling**

The contradiction pass still uses `rrf_candidate_pool` for both its BM25 and semantic child retrieval calls. `contradiction_top_k` is a parent/output budget, not an independent pre-fusion counterevidence child budget.

That does not falsify the normal hybrid support-pass separation. It does block a clean Block E experiment in which counterevidence candidate budget is varied independently of the ordinary hybrid pool.

### Chunk geometry and identity

**OBSERVED**

Chunk geometry is explicit in `RetrievalConfig` as `chunk_max_chars` and `chunk_overlap_chars`, with defaults `1800` and `80` preserved from the live pre-RC0 machinery.

The writer constructs `ChunkSpec` from those values. The retrieval config hash includes them. A geometry mutation test demonstrates a changed config hash, changed chunk IDs, and changed semantic chunk-set hash.

### Fusion

**OBSERVED**

The ordinary hybrid path sends the lexical ranking and semantic ranking actually produced under their declared budgets into reciprocal-rank fusion using `rrf_k_constant`.

RRF therefore consumes the declared inputs. RC0 did not replace fusion or introduce an alternative fusion family.

### Parent aggregation and rerank scope

**OBSERVED**

Parent aggregation remains `max` only. Because the type admits no alternative arm, it is a fixed mechanism, not a multi-valued experimental variable.

For hybrid reranking:

1. child hits are fused;
2. candidates are aggregated to parents;
3. the parent pool is bounded to `max(top_k, rerank_top_n)` when reranking is enabled;
4. only the first `rerank_top_n` parents are reranked;
5. the reranked head plus untouched tail is truncated to `top_k`.

The reranker therefore operates on parent candidates, not raw child hits. The scope is explicit in code.

### Configuration observability

**OBSERVED — closed RC0-specific mutations**

The RC0 mutation suite demonstrates:

- model revision changes configuration identity;
- missing/invalid immutable revisions fail closed at config validation;
- model loaders receive declared revisions;
- persisted semantic indexes reject revision/chunk-set aliasing;
- geometry mutation changes config and chunk identity;
- semantic child budget changes semantic pre-fusion computation;
- lexical candidate pool changes BM25 pre-fusion computation;
- pre-RC0 production defaults remain unchanged.

**OBSERVED — not exhaustively closed**

There is not yet a single observability matrix proving, for every field presented as an experimental independent variable, either:

1. a controlled downstream computation/receipt change, or
2. an explicitly documented no-op invariant.

Examples that are active by inspection but are not all covered by one RC0 mutation matrix include `semantic_query_prefix`, `rrf_k_constant`, the rerank scope knobs, contradiction prefixes, contradiction gate, and contradiction budgets.

A configuration hash changing is necessary identity evidence. It is not, by itself, proof that the corresponding value changes the intended downstream computation.

## 4. Durable receipt audit

### OBSERVED

`RetrievalRunReport` contains the full `RetrievalConfig` in memory, and `_retrieval_config_hash` hashes the normalized config after removing cache/index filesystem paths.

The durable Markdown report prints many material values, including method, geometry, model names/revisions, budgets, RRF constant, rerank settings, contradiction settings, and the configuration hash.

However, the durable Markdown report omits at least `semantic_query_prefix`, even though that prefix changes the text encoded by semantic retrieval. The sealed bundle carries the configuration hash rather than a complete machine-readable retrieval-arm configuration.

A transient semantic run also does not leave the computed semantic `chunk_set_hash` in the retrieval report when no semantic index is persisted.

The run receipt does not bind the retrieval apparatus Git commit/tree or exact retrieval-runtime package versions.

### INFERENCE

The current durable output can detect that two configurations differ by hash, but it cannot independently reconstruct an arm from the receipt alone.

That fails the characterization prerequisite requiring a reproducible retrieval configuration identity.

## 5. Cleanup audit

### OBSERVED — cleanup completed without rewriting history

The frozen commit removed the temporary bootstrap patch scripts:

- `apply_rc0.py`
- `apply_rc0_followup.py`
- `apply_rc0_followup2.py`
- `apply_rc0_followup3.py`

It also removed the generated permanent workflow that had caused workflow-token mutation problems.

Failed and deviating Actions runs remain available as historical evidence.

### OBSERVED — remaining debt

`.github/workflows/research-retrieval-control-surface-rc0-bootstrap.yml` remains on the frozen branch. Its path filters refer to patch scripts that no longer exist. It is historical bootstrap transport machinery, not a truthful ongoing RC0 validation workflow.

No permanent RC0 validation workflow remains on the frozen SHA.

The frozen RC0 research directory contains only the preregistration and `real_model_smoke.py`; it did not previously contain a terminal `RESULTS.md`.

The default reranker model string in `RetrievalConfig` retains the legacy alias `cross-encoder/ms-marco-MiniLM-L-6-v2`, while the research smoke uses canonical `cross-encoder/ms-marco-MiniLM-L6-v2`. The upstream service currently resolves the legacy form, but a research arm should persist the canonical ID rather than depend on redirect behavior.

### INFERENCE

The stale bootstrap workflow is demonstrably obsolete, but deleting it on the frozen branch would change the frozen experimental object. This reconciliation therefore leaves `a02a9d3` untouched and records the workflow as cleanup debt for a successor apparatus branch.

## 6. Characterization authorization gate

| Prerequisite | State | Basis |
| --- | --- | --- |
| Truthful independent variables | **PARTIAL / NOT CLEARED** | Main lexical/semantic budgets are independently observed; a complete mutation matrix is absent and counterevidence child budgets remain coupled. |
| Immutable model identities | **STRUCTURAL PASS / EXECUTION RECEIPT MISSING** | Revision validation/loader propagation exist; exact pinned models were not executed on the frozen SHA. |
| Reproducible chunking identity | **PARTIAL / NOT CLEARED** | Geometry and chunk-set hashing exist; the standalone durable arm receipt does not materialize all replay identity. |
| Reproducible retrieval configuration identity | **FAIL** | Durable report omits at least active `semantic_query_prefix` and is not a complete machine-readable arm specification. |
| BM25 / semantic / hybrid semantics established | **PASS** | All three execute through the normal path and are covered by deterministic tests. |
| Deterministic non-Pilot diagnostic evaluator | **FAIL / NOT YET FROZEN** | Pilot evaluator validity is not borrowed; no separate diagnostic evaluator has been frozen for this task. |
| No Pilot scientific-gold dependency | **PASS** | This reconciliation did not inspect or use sealed Pilot scientific judgments or target performance. |

**Decision:** retrieval characterization is **NOT AUTHORIZED** from RC0 as frozen.

No characterization run was started.

## 7. Exact changes made during reconciliation

Direct reconciliation change:

- commit `18b0a67bb1c1d8e20589106a49e6a500dcfdf884`
  - closed the missing lexical-budget mutation falsifier;
  - removed the generated workflow from the Actions-authored freeze diff;
  - did not authorize production defaults.

Actions-produced freeze:

- commit `a02a9d313816ad8302efbcbb24bca265c31473e7`
- tree `9774b82c4c0be5ebbe190f7d8d120836fc7b354c`

This terminal record is written on a successor reconciliation branch so the frozen RC0 SHA remains unchanged.

## 8. Falsifiers for the future characterization experiment

These falsifiers are preregistration inputs only. They do not authorize execution.

### Semantic-only usefulness

**HYPOTHESIS:** semantic-only adds useful recovery on low lexical-overlap evidence.

Falsify usefulness for the bounded diagnostic corpus if, under controlled candidate budgets, semantic-only produces no material recall/rank benefit on the intended low-overlap families and introduces losses/cost without a compensating subgroup benefit.

### Hybrid usefulness over lexical

**HYPOTHESIS:** hybrid provides complementary evidence recovery rather than merely spending a larger candidate budget.

Falsify if hybrid's apparent gains disappear when lexical budget is matched, or if hybrid produces no meaningful family-level recall/rank gain while materially increasing candidate burden, latency, or worst-case failures.

### Reranking usefulness

**HYPOTHESIS:** parent reranking improves the ordering of already-retrieved relevant candidates.

Falsify if relevant candidates are present in the rerankable parent pool but reranking does not improve justified rank-sensitive measures, or if it materially worsens worst-case retrieval while adding execution cost.

### Counterevidence pass usefulness

**HYPOTHESIS:** contradiction-query expansion and the role gate increase recovery of genuine disconfirming/limiting evidence.

Falsify if a same-budget comparison shows no counterevidence Recall@K gain, if the pass mainly duplicates ordinary supporting retrieval, or if the text-role gate removes true counterevidence at a rate that defeats its distractor filtering benefit.

### One-configuration generalization

**HYPOTHESIS:** a single retrieval configuration may be adequate across claim families.

Falsify if familywise arm rankings conflict materially, if no single arm is non-dominated across the diagnostic families, or if acceptable worst-case behavior requires materially different settings for different claim classes.

## 9. Non-claims

This record does not establish:

- better retrieval;
- any Pilot 0A scientific result;
- evaluator validity for Pilot 0A;
- a production retrieval configuration;
- superiority of BGE, MiniLM, or any alternative model family;
- authorization to merge the RC0 research implementation into production paths.

The next task is smaller: repair retrieval-arm identity and observability, then freeze a separate non-Pilot diagnostic evaluator/corpus before any characterization run.