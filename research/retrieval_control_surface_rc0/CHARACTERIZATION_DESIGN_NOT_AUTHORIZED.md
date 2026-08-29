# Retrieval Characterization Design — NOT AUTHORIZED

Status: **DESIGN ONLY**

This is not a preregistration and does not authorize execution.

The RC0 reconciliation classified the current surface as `RC0_APPARATUS_FAILURE` because durable arm identity/replay and several experimental-control prerequisites are not yet closed. This design exists so the successor apparatus repair can be judged against the experiment it must actually support.

No Pilot 0A scientific judgments, qrels, target-system performance, or hidden-gold material may be used to construct, tune, select, or score this diagnostic experiment.

## 1. Question

Can the Evidence Bundler retrieval apparatus distinguish where lexical, semantic, hybrid, reranking, and counterevidence machinery help or fail across controlled claim families without collapsing those effects into one global score or one global optimum?

The target is characterization, not promotion.

## 2. Diagnostic corpus

Freeze a separate diagnostic corpus before comparing retrieval configurations.

The corpus must contain at least these strata:

1. **Exact lexical / terminology-heavy**
   - decisive evidence uses the same or near-identical technical terminology as the claim;
   - lexical retrieval should be a strong control.

2. **Low lexical-overlap paraphrase**
   - decisive evidence is semantically aligned but shares little surface vocabulary with the claim;
   - constructed to test the actual semantic-retrieval hypothesis rather than generic search difficulty.

3. **Explicit counterevidence / contradiction**
   - sources contain passages that directly disconfirm or materially limit the claim;
   - supporting-looking distractors should also be present where useful.

4. **Numerical / quantitative**
   - relevance depends on matching quantities, thresholds, ranges, units, dates, or comparative statements;
   - lexical and semantic false friends should be represented.

5. **Long regulatory / legal / scientific passages**
   - decisive language appears inside long, structured text;
   - cases should make chunk boundaries and overlap consequential.

6. **Distributed evidence**
   - relevant evidence spans multiple passages or multiple source regions;
   - passage-level recall and source-level recall should diverge meaningfully.

7. **Distractor-heavy**
   - corpus includes many lexically or semantically similar but non-decisive passages;
   - candidate burden becomes a material measurement.

8. **Legitimate absence**
   - no relevant evidence exists in the frozen corpus for the claim;
   - `no_candidate` is potentially correct behavior and must not be scored as an automatic retrieval failure.

### Freeze requirements

Before any arm runs, freeze and hash:

- source bytes;
- claim/query text;
- source IDs;
- passage IDs and offsets;
- family/stratum labels;
- relevant source sets;
- relevant passage sets;
- counterevidence passage sets where applicable;
- explicit no-relevant-evidence cases;
- corpus manifest and evaluator version.

The diagnostic corpus should be small enough to inspect and mutate but large enough that a trivial lexical-only, semantic-only, return-all, and random-ranking control do not all satisfy the same decision boundary.

## 3. Diagnostic evaluator requirements

The evaluator must be a separate non-Pilot object.

Before it is used to compare retrieval arms, demonstrate:

- deterministic scoring on frozen inputs;
- source-level and passage-level relevance semantics;
- explicit treatment of legitimate absence;
- separate counterevidence relevance;
- correct handling of multiple relevant passages/sources;
- query-local rank-sensitive metrics where used;
- no dependence on output ordering where the metric is set-based;
- no hidden normalization that changes candidate budgets;
- mutation tests for dropped relevant passage, duplicated candidate, rank swap, extra distractor, and empty result;
- at least one intentionally weak but plausible control that fails a meaningful diagnostic gate for the intended reason.

A green evaluator test suite is not, by itself, evidence of useful discrimination.

## 4. Arm identity

Every arm must produce a machine-readable receipt sufficient for replay without reading experiment prose.

The arm identity must bind:

- apparatus Git commit/tree;
- diagnostic corpus hash;
- evaluator hash/version;
- normalized complete retrieval configuration;
- chunk-set hash;
- canonical model IDs and exact revisions;
- model/runtime versions;
- output hashes;
- relevant compute/device identity for latency/cost interpretation.

No arm may differ from another in an unrecorded variable.

## 5. Sequential experimental blocks

Do not run one giant Cartesian sweep. Freeze each block's invariant dimensions before execution and preserve every arm result.

### Block A — geometry and candidate budgets

Purpose: determine whether basic retrieval aperture and chunk geometry explain later family differences before attributing effects to model family.

Candidate factors:

- chunk max size;
- chunk overlap;
- lexical child pool;
- semantic child pool;
- parent candidate pool.

Required apparatus repair before this block:

- a truthful parent-pool control distinct from final `top_k` if parent-pool size is to be varied independently.

Keep retrieval family/fusion/rerank/counterevidence behavior otherwise fixed.

Do not choose a global winner from this block. Record familywise sensitivity and identify geometry/budget settings that cause obvious aperture failure.

### Block B — retrieval family

Compare under matched, frozen geometry and controlled candidate budgets:

- BM25;
- semantic-only;
- hybrid.

Questions:

- Does semantic-only recover low-overlap evidence that lexical misses?
- Does lexical remain stronger on exact terminology/numerical cases?
- Does hybrid add complementary recall or merely spend more candidate budget?
- Which family has the worst subgroup failure?

### Block C — fusion

Hold lexical and semantic rankings, candidate budgets, geometry, models, and reranking fixed.

Characterize only the declared fusion variable, initially RRF behavior such as `rrf_k_constant` if it remains the active fusion mechanism.

Do not introduce a new fusion algorithm in this task. A new fusion family is a separate apparatus/modeling hypothesis.

### Block D — reranking

Hold the pre-rerank candidate pool fixed.

Compare:

- reranking disabled;
- reranking enabled;
- bounded rerank candidate counts.

Measure whether the cross-encoder improves rank among candidates that were already retrieved. Do not credit reranking for recall failures caused upstream.

Record cases where relevant parents exist outside the rerank scope.

### Block E — counterevidence

Required apparatus repair before this block:

- an independently controlled counterevidence child candidate budget rather than reusing the ordinary `rrf_candidate_pool` for both contradiction lexical and semantic calls.

Then characterize separately:

- contradiction-query expansion on/off or bounded prefix sets;
- counterevidence candidate budget;
- text-role gate on/off;
- contradiction reranking only after the earlier dimensions are fixed.

Do not tune these settings using Pilot target performance.

## 6. Measurements

Preserve the following separately. Do not collapse them into one scalar objective.

### Retrieval effectiveness

- source-level Recall@K;
- passage-level Recall@K;
- counterevidence Recall@K;
- MRR or another rank-sensitive measure only where the relevance structure justifies it;
- no-candidate rate;
- correct-empty rate for legitimate-absence cases;
- candidate burden, including surfaced candidates per claim and a precision-like distractor proxy.

### Robustness

- per-family results;
- family worst case;
- number and identity of total misses;
- failure type by stage where observable;
- sensitivity to geometry/budget changes.

### Cost and execution

- wall-clock latency;
- embedding calls/vectors;
- cross-encoder pair count;
- semantic index build/load cost;
- candidate counts at each stage;
- compute/device identity;
- model/runtime versions.

### Identity

- retrieval config hash;
- full normalized config;
- corpus hash;
- chunk-set hash;
- model revisions;
- apparatus SHA/tree;
- evaluator identity;
- result/output hashes.

## 7. Stage attribution

The characterization report should distinguish at least:

- relevant child never retrieved;
- relevant child retrieved but lost in fusion;
- relevant child survived fusion but parent aggregation displaced the relevant parent representation;
- relevant parent entered rerank pool but reranker demoted it;
- relevant parent existed outside the rerank pool;
- counterevidence query expansion never retrieved the relevant child;
- text-role gate filtered a relevant counterevidence parent;
- final `top_k` truncation removed an otherwise available relevant parent;
- evaluator/relevance ambiguity rather than retrieval error.

A final miss without stage attribution is weaker evidence than a trace showing where the miss arose.

## 8. Controls

Include cheap controls before interpreting sophisticated arms:

- lexical-only at matched budget;
- semantic-only at matched budget;
- deterministic random ranking over the same candidate universe where practical;
- return-all or very-wide retrieval as an aperture control, scored separately for burden and never treated as a deployable arm;
- deliberately tiny candidate-budget control expected to fail recall;
- no-retrieval/empty control for evaluator mechanics;
- duplicated-result control for evaluator canonicalization.

The controls test the evaluator and the interpretation, not only the retriever.

## 9. Falsifiers

### Semantic-only

Falsify bounded usefulness if it shows no material advantage on low-overlap families under matched aperture/cost and introduces uncompensated losses elsewhere.

### Hybrid over lexical

Falsify bounded usefulness if apparent gains disappear under matched lexical budget or if no meaningful subgroup gain survives the added candidate burden/latency.

### Reranking

Falsify bounded usefulness if relevant parents are present in the rerankable pool but ranking does not improve on justified measures, or if worst-case behavior degrades materially for the added cost.

### Counterevidence pass

Falsify bounded usefulness if a matched-budget comparison does not improve counterevidence recall, the pass mostly duplicates ordinary retrieval, or the text-role gate removes genuine counterevidence enough to erase its distractor-filtering value.

### Single general configuration

Falsify the assumption that one configuration generalizes if familywise rankings conflict materially, no arm is non-dominated across families, or acceptable worst-case behavior requires materially different settings.

## 10. Analysis rules

- Report observed arm results before selecting an interpretation.
- Preserve all failed and dominated arms.
- Do not retune the diagnostic corpus after observing arm outcomes.
- Do not select thresholds from Pilot results.
- Do not infer causal benefit from a configuration change that also changed an uncontrolled variable.
- Prefer the smallest discriminating follow-up over a larger sweep when two explanations remain plausible.
- If the evaluator gives surprising results, test the evaluator before blaming retrieval.
- Treat a better aggregate result with worse subgroup floor as a tradeoff, not an automatic improvement.

## 11. Production boundary

Even if an experimental arm performs better on the diagnostic corpus, this design does not authorize:

- changing Evidence Bundler production defaults;
- replacing BGE or MiniLM with another model family;
- merging experimental retrieval settings;
- using Pilot scientific gold for post-hoc confirmation;
- promoting a global configuration when family-specific behavior remains unresolved.

A later promotion task must identify the smallest production change supported by independent evidence.