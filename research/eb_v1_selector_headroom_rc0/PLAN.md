# Evidence Bundler V1 Selector Research Plan

Status: successor research planning record. No production authorization.

Updated after terminal frozen-pool selector screening PR #77.

## Current decision state

Evidence Bundler V1 is substantially converged outside the candidate-selection seam. Frozen V1 implementation remains `c4e3f97ec8f0bd36180954c3aa382418925bf947`; protected `main` remains `c26fbd4bfc8ba5c2604a784af158594b59fcae37` at setup.

Existing evidence establishes:

- fixed 5/3 loses qualification-required evidence;
- candidate depth 10 can recover evidence below rank 3;
- fixed 10/7 mechanically recovers the preserved rank-7 example but is rejected as the V1 default by completed burden qualification (PR #72);
- task-aligned RC1 V5 (PR #74, final `e84cfd84826eacb9751ecf4b54ff9c369547df58`) independently falsifies fixed 10/7 under its preregistered non-harm rule because inter-reviewer KEEP/DROP disagreement increased from 0 to 2, while false-keep, false-drop and unresolved counts were not worse;
- the prior pinned MiniLM reranker is falsified on its dev diagnostic; this does not falsify reranking generally;
- Phase 0 oracle/headroom analysis shows 96 frozen candidate relationships versus only 22 qualification-required relationships, leaving large theoretical selector headroom;
- Phase 1 PR #77 shows a deterministic lexical facility-location selector at three preregistered coverage weights does **not** improve either qualification-required recall or RC1 V5 `KEEP_DISTINCT` recall over K=3 at the same budget.

Therefore do not continue a fixed-K search and do not iterate generic lexical diversity weights. The unresolved engineering/research seam remains:

`high-recall proposition-relative candidate pool -> compact retained evidence set`

but the evidence now localizes the problem more strongly to the **materiality/relevance signal** than to generic set composition.

## Research hypotheses

### H1 — Ranking/budget geometry

A simple adaptive score/stopping rule can trim burden without materially harming the useful set.

Current evidence: partially supported as a burden-control idea, not as an evidence-survival solution. The largest-relative-gap control in PR #77 retained 45 rather than 54 relationships while preserving the same 17/19 V5 `KEEP_DISTINCT` items as K=3, but still missed both operationally important deep items and lost one qualification-required relationship that V5 independently labels redundant.

### H2 — Generic set-composition failure

Independent ranking is the principal problem and a relevance/diversity set objective can solve it.

Current evidence: weakened for the tested deterministic lexical facility-location form. PR #77's alpha 0.25/0.50/0.75 arms all reproduced K=3's 19/22 qualification-required and 17/19 operational KEEP result while selecting the same total burden.

Do not generalize this to all set-wise selection, but do not spend the next slice sweeping more MMR/submodular weights without a new discriminating rationale.

### H3 — Materiality/relevance representation failure

The candidate world contains useful evidence, but the available retrieval signals do not adequately distinguish materially useful evidence from lexical decoys, contextual qualifiers, or long-context evidence.

Current evidence: strengthened. The two V5 operational KEEP misses expose different signal failures:

1. `C06_HARD_NEG:child:1|C06-P1`, BM25 rank 4: the short measured-result passage loses to three hard negatives that reproduce nearly all proposition vocabulary but explicitly concern setup/humidity/revision rather than the result;
2. `RETRIEVAL_APERTURE:child:1|RET-AP-P6`, BM25 rank 7: the exact proposition occurs inside a very long passage but chunk-level BM25 is diluted by surrounding repeated context.

A generic diversity objective does not repair either failure.

## Research direction now

Prioritize **materiality-signal discrimination**, not another broad retriever redesign and not another generic set selector.

The next work should test the cheapest auditable signals first:

1. **local-span / MaxP-style lexical scoring** to separate long-context score dilution from genuine low relevance;
2. **hard-negative discrimination** to determine whether lexical and structural signals can distinguish result-bearing passages from query-copying non-result passages;
3. **bounded proposition feature representation** only if raw/local lexical signals remain insufficient;
4. modern learned relevance/reranking models only after the deterministic diagnostics establish what signal is missing and only under an explicit authority audit;
5. generated information requirements/subqueries only if simpler materiality representations fail, because they add a new semantic-planning authority surface.

Do not equate semantic diversity with material evidence. Do not use support/refutation/entailment as an EB selection target.

## Phase 0 — Oracle/headroom retrospective — COMPLETE

Authorities:

- PR #63 decisive run `34649326414`, artifact `10282804289`, digest `sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`;
- PR #72 terminal head `22d83d9af465a026eb58ff64888267c4fce18619`;
- PR #74 V5 as separate operational context.

Observed:

- 18 lanes;
- 96 candidate relationships;
- 22 qualification-required relationships;
- K=3 preserves 19/22 and fully covers 15/18 lanes;
- K=7 preserves 22/22 at 96 relationships;
- a lossless global score/top-score threshold must fall to approximately 0.2465 and still retains 73 relationships;
- largest-gap stopping misses required evidence.

Decision: substantial headroom exists, but naive threshold geometry does not close it.

## Phase 1 — Frozen-pool selector bake-off — COMPLETE

Terminal screening record: PR #77.

At fixed three-passage budget:

- K=3: 19/22 qualification-required; 17/19 V5 KEEP;
- facility alpha 0.25: 19/22; 17/19;
- facility alpha 0.50: 19/22; 17/19;
- facility alpha 0.75: 19/22; 17/19.

All facility arms missed the same deep operational KEEP items as K=3 and did not reduce completed non-required burden.

Disposition:

`SETWISE_NOT_JUSTIFIED_ON_FROZEN_POOL`

Secondary:

`CONSTRUCT_TENSION_OBSERVED`

Do **not** advance this facility selector to metamorphic qualification or fresh operational review.

## Phase 2A — Materiality Signal Discriminator — NEXT

Use the same frozen candidate world first. No retrieval rerun and no new semantic reviewer unless a later preregistration explicitly requires one.

### Question A — long-context dilution

Can an auditable local-span scorer recover `RET-AP-P6` without promoting the known decoy/hypothetical passages that already outrank it?

Required tests:

- deterministic sentence/window segmentation;
- MaxP-style local BM25 or equivalent lexical local-span score;
- exact proposition/passage identity preservation;
- compare chunk score versus best-local-span score;
- mutation: prepend/append irrelevant context to a relevant local span and require local materiality ranking to remain stable;
- mutation: repeat irrelevant context many times and ensure it does not suppress the relevant local span;
- verify no hidden semantic/support authority enters the score.

Falsifier: local-span scoring still fails to recover the buried exact proposition, or promotes unrelated local snippets enough to worsen burden materially.

### Question B — hard lexical negatives

Can deterministic observable signals distinguish a result-bearing passage from candidates that copy proposition vocabulary but explicitly describe non-result/setup/hypothetical/revision contexts?

Start with diagnostic feature analysis, not hand-written benchmark-specific rescue rules.

Measure per candidate at least:

- chunk BM25 rank/score;
- query-token coverage;
- candidate length;
- local-span score;
- numeric/value normalization effects as a diagnostic;
- explicit negation/non-result/context cues as observed features, not automatic truth labels;
- source/provenance identity.

Use `C06-P1` and the RET aperture case as named falsifiers, but evaluate all frozen lanes to avoid solving two examples by hand.

Falsifier for simple deterministic materiality signals: the hard-negative passage remains indistinguishable from or consistently below the decoys without introducing benchmark-specific semantic rules.

### Question C — construct boundary

Keep qualification-required and V5 operational labels separate.

The next evaluator must explicitly surface cases such as:

- qualification-required + operational `UNRESOLVED`;
- qualification-required + operational `DROP_REDUNDANT`;
- operational `KEEP_DISTINCT` contextual evidence.

Do not optimize one label system while silently calling it universal evidence gold.

### Decision from Phase 2A

Possible bounded outcomes:

- `LOCAL_SPAN_SIGNAL_USEFUL`: local-span scoring fixes long-context dilution without unacceptable new burden, but hard-negative materiality remains open;
- `DETERMINISTIC_MATERIALITY_SIGNAL`: a transparent non-learned feature family improves both named failure classes across the frozen cohort;
- `MATERIALITY_REPRESENTATION_REQUIRED`: simple lexical/local structural signals cannot distinguish the hard-negative evidence role, justifying research into bounded semantic materiality representations;
- `CANDIDATE_GENERATION_LIMITATION`: required evidence is absent even before selection in a successor naturalistic cohort, which reopens lexical/semantic/hybrid candidate generation as a separate question.

No outcome alone qualifies production behavior.

## Phase 2B — Metamorphic qualification — CONDITIONAL

Only a signal/selector with a positive Phase 2A result should face metamorphic qualification.

Required mutations include:

- irrelevant addition;
- duplicate/near-duplicate addition;
- rank perturbation;
- high-BM25 hard lexical negative;
- candidate-order permutation;
- long irrelevant prefix/suffix addition;
- contextual C05 evidence;
- independent corroboration;
- counterevidence symmetry;
- passage/source identity mutation and provenance preservation.

Hard falsifiers include losing previously preserved material evidence under an inconsequential mutation, silently collapsing independent corroboration, systematic support-side preference, nondeterminism where deterministic behavior is claimed, or semantic authority leakage.

## Phase 3 — Operational requalification — CONDITIONAL

Only after a mechanism passes frozen-pool and metamorphic tests should it face fresh task-aligned operational review.

Reuse RC1 V5 lessons:

- reference and test review use the same operational construct;
- preserve ambiguity rather than forcing gold;
- measure false keep, false drop, unresolved, and inter-reviewer action disagreement separately;
- do not collapse evaluator geometry into one accuracy score.

## Phase 4 — Candidate-generation reconsideration — CONDITIONAL

Candidate depth 10/BM25 remains unfalsified on this qualification cohort, not universally sufficient. Reopen candidate generation only if later qualified selector/signal work exposes required evidence absent from the candidate pool. Then compare lexical, semantic, or hybrid generation as its own experiment.

## Stop boundaries

No production-default change, merge, release, tag, promotion, K=8 search, model training, semantic retriever replacement, query rewrite, generated semantic subqueries, or CAL semantic-authority transfer follows automatically from this plan.
