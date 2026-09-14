# Evidence Bundler V1 Selector Research Plan

Status: successor research planning record. No production authorization.

## Current decision state

Evidence Bundler V1 is substantially converged outside the candidate-selection seam. Frozen V1 implementation remains `c4e3f97ec8f0bd36180954c3aa382418925bf947`; protected `main` remains `c26fbd4bfc8ba5c2604a784af158594b59fcae37` at setup.

Existing evidence establishes:

- fixed 5/3 loses qualification-required evidence;
- candidate depth 10 can recover evidence below rank 3;
- fixed 10/7 mechanically recovers the preserved rank-7 example but is rejected as the V1 default by completed burden qualification (PR #72);
- task-aligned RC1 V5 (PR #74, final `e84cfd84826eacb9751ecf4b54ff9c369547df58`) independently falsifies fixed 10/7 under its preregistered non-harm rule because inter-reviewer KEEP/DROP disagreement increased from 0 to 2, while false-keep, false-drop and unresolved counts were not worse;
- the prior pinned MiniLM reranker is falsified on its dev diagnostic; this does not falsify reranking or set selection generally.

Therefore do not continue a fixed-K search. The unresolved engineering/research seam is:

`high-recall proposition-relative candidate pool -> compact retained evidence set`

## Research hypotheses

H1 — Ranking-boundary failure: a simple adaptive score/stopping rule is sufficient.

H2 — Set-composition failure: independent ranking is the wrong objective; selector must optimize a jointly useful/nonredundant set.

H3 — Materiality-representation failure: neither rank nor generic semantic diversity is enough; EB needs an explicit bounded representation of evidence requirements/materiality before reliable set construction is possible.

The plan must be capable of falsifying H2/H3 in favor of a simple deterministic rule.

## Research direction

Prioritize candidate-to-set selection, not a broad retriever redesign. Relevant families:

1. deterministic adaptive score/stopping rules as the cheapest explanation;
2. set-wise facility-location/submodular coverage selection;
3. conservative redundancy handling that preserves independent corroboration;
4. explicit bounded information-requirement/materiality representations only if score/set geometry is insufficient;
5. learned pointwise rerankers only after simpler mechanisms fail and only under a relevance/materiality authority audit.

Do not equate semantic diversity with material evidence. Do not use support/refutation/entailment as an EB selection target.

## Phase 0 — Oracle/headroom retrospective (current)

Use only frozen evidence. No retrieval rerun and no new reviewer.

Authorities:

- PR #63 decisive run `34649326414`, artifact `10282804289`, digest `sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`;
- PR #72 terminal head `22d83d9af465a026eb58ff64888267c4fce18619`, which resolved all 27 previously unresolved retained relationships as `KNOWN_NON_REQUIRED_OR_DISTRACTOR`;
- PR #74 terminal V5 result as separate operational context, not as interchangeable gold.

Questions:

- How small is the qualification-required oracle set?
- How deep are required relations in the frozen BM25 ordering?
- What recall/burden frontier does fixed K produce?
- Can a simple score ratio or score-gap rule approach the oracle without losing required evidence?
- Is there enough theoretical headroom to justify selector work?

Phase-0 success means only that meaningful selector headroom exists. It does not qualify any selector.

## Phase 1 — Frozen-pool selector bake-off

Proceed only if Phase 0 shows material headroom.

Start with the smallest discriminating set:

- frozen K=3 baseline;
- one deterministic adaptive-score baseline;
- one deterministic set-wise facility-location/coverage selector.

MMR may be included as a diagnostic comparator, not automatically as a promotion candidate. Do not introduce another learned reranker in the first bake-off.

Primary measurements:

- qualification-required evidence recall;
- complete multi-relation/lane coverage;
- retained proposition-passage relationships;
- unique physical passages and token burden where reconstructable;
- known distractor and known redundancy burden;
- deterministic replay;
- source/provenance preservation;
- selection stability under metamorphic mutation.

A selector is not successful merely because it improves an aggregate retrieval score.

## Phase 2 — Metamorphic selector qualification

Any promising selector must be tested against at least:

- irrelevant-candidate addition;
- exact/near duplicate addition;
- rank perturbation;
- high-BM25 hard lexical negative;
- candidate-order permutation;
- proposition paraphrase where the scoring mechanism supports it;
- contextual evidence cases of the C05 type;
- independent corroboration from distinct sources;
- counterevidence symmetry;
- passage/source identity mutation and provenance preservation.

Hard falsifiers include losing previously preserved required evidence under an inconsequential mutation, silently collapsing independent corroboration, systematic support-side preference, nondeterminism where deterministic behavior is claimed, or semantic authority leakage.

## Phase 3 — Operational requalification

Only after a selector passes frozen-pool and metamorphic tests should it face fresh task-aligned operational review. Reuse the lessons of RC1 V5:

- reference and test review must use the same operational construct;
- preserve contextual-evidence ambiguity rather than forcing gold;
- measure false keep, false drop, unresolved, and inter-reviewer action disagreement separately;
- do not collapse evaluator geometry into one accuracy score.

## Phase 4 — Candidate-generation reconsideration

Candidate depth 10/BM25 remains unfalsified on the current qualification cohort, not universally sufficient. Reopen candidate generation only if selector-qualified failures show required evidence is absent from the candidate pool. Then compare lexical, semantic, or hybrid candidate generation as a separate question.

## Stop boundaries

No production-default change, merge, release, tag, promotion, K=8 search, selector training, semantic retriever replacement, query rewrite, or CAL semantic-authority transfer follows automatically from this plan.
