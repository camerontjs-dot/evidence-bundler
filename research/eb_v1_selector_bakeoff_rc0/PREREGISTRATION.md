# Evidence Bundler V1 Frozen-Pool Selector Bake-off RC0

Status: preregistered dev/frozen-pool architecture screening. This is not production qualification.

This preregistration is frozen before implementation or execution of the set-wise selector described below.

## Question

Given the exact frozen depth-10 BM25 candidate world that underlies the 10/7 Evidence Bundler qualification work, can deterministic set-wise composition recover materially more useful evidence than fixed top-3 at the **same three-passage-per-lane budget**, without importing support/refutation authority or requiring a learned reranker?

The experiment is designed to discriminate among:

- **H1 — ranking-boundary failure:** simple score geometry is sufficient;
- **H2 — set-composition failure:** independent ranking is the wrong objective and a jointly optimized set improves the retained evidence composition;
- **H3 — materiality-representation failure:** rank plus generic lexical coverage is insufficient, implying a later need for an explicit bounded representation of evidence requirements/materiality.

No hypothesis is presumed correct.

## Frozen authorities

### Implementation / repository

- protected `main` at setup: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- frozen V1 implementation: `c4e3f97ec8f0bd36180954c3aa382418925bf947`

### Frozen candidate world

- predecessor PR: #63
- decisive run: `34649326414`
- artifact: `10282804289`
- exact artifact ZIP digest: `sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`
- treatment receipt: exact `10/7` raw retrieval ordering/scores from `TREATMENT_10_7_RECEIPT.json`
- normative lanes: 18
- frozen positive-score proposition-passage relationships: 96

No retrieval rerun is permitted.

### Qualification-required evaluation authority

PR #72 terminal head:

`22d83d9af465a026eb58ff64888267c4fce18619`

PR #72 resolved all 27 relationships left unknown by the sparse PR #63 burden gold as `KNOWN_NON_REQUIRED_OR_DISTRACTOR`. Therefore the explicit PR #63 `required` mappings constitute the conservative qualification-required positive set for this retrospective frozen world.

Phase-0 headroom record is Draft PR #76. It reports 22 qualification-required relationships across 18 lanes and is planning/retrospective evidence only.

### Operational evaluation authority

RC1 V5 reference freeze:

`79e8c41462b791716c89b7f8329f15b580d504a7`

Terminal RC1 V5 final:

`e84cfd84826eacb9751ecf4b54ff9c369547df58`

Use only the frozen Cobalt reference labels from:

`research/eb_v1_operational_burden_rc1/reference_outputs_v5/REFERENCE_COBALT.json`

with relation identities mapped through:

`research/eb_v1_operational_burden_rc1/SUPERVISOR_RELATION_MAP.json`

Operational labels are:

- `KEEP_DISTINCT`
- `DROP_REDUNDANT`
- `DROP_DISTRACTOR`
- `UNRESOLVED`

These labels are a **separate evaluation construct** from PR #72 qualification-required gold. They must never be silently merged into one gold set.

## Gold firewall

Selector generation may read only:

- proposition text;
- candidate passage text;
- candidate relation/evidence identity needed to preserve provenance;
- original BM25 rank;
- raw BM25 score.

Selector generation must NOT read:

- PR #63 required/non-required classification;
- PR #72 adjudication result;
- RC1 V5 reference labels;
- Stage-2 reviewer outputs;
- expected disposition.

All selector outputs and their hashes must be frozen before evaluator access to either gold authority.

## Arms

All primary arms have a hard maximum budget of **three passages per proposition lane**. This isolates composition from the retention-budget increase that falsified fixed 10/7.

The oracle analysis found that the qualification-required set contains at most two positive relationships in any lane, so a three-passage budget has enough theoretical capacity to preserve all qualification-required relationships. Failure therefore cannot be excused solely by insufficient cardinality on this frozen qualification construct.

### Arm A — fixed K=3

Select the first three BM25-ranked candidates in each lane, or all candidates if fewer than three exist.

This is the frozen simple baseline.

### Arm B — largest-relative-gap control

For each lane, compute relative consecutive score drops:

`gap_i = (score_i - score_(i+1)) / score_i`

Stop at the largest gap, capped at three selected passages. Ties choose the earliest gap.

This is a deliberately cheap deterministic H1 control, not a favored contender. Phase-0 retrospective analysis already indicates naive gap stopping misses qualification-required evidence; it is included to make the selector comparison explicit under the same runner/evaluator.

### Arm C — deterministic query-weighted facility-location family

Selection unit: proposition-passage relationship.

Representation:

- lowercase `\w+` tokens;
- deterministic TF-IDF vectors computed independently within each proposition lane over the proposition plus lane candidates;
- no embeddings, external model, network access, training data, generated subqueries, or LLM calls.

Candidate-candidate similarity:

- cosine similarity of lane-local TF-IDF vectors.

Proposition relevance signal:

- normalized frozen BM25 score `r_i = score_i / max_lane_score`.

Coverage demand weights:

- each candidate j contributes demand weight `w_j = r_j`;
- therefore a cluster of low-BM25 candidates cannot dominate coverage merely by cardinality.

For a selected set S, normalized facility-location coverage is:

`coverage(S) = sum_j w_j * max_(s in S) sim(j,s) / sum_j w_j`

Normalized relevance is:

`relevance(S) = sum_(s in S) r_s / min(3, lane_candidate_count)`

Objective:

`F_alpha(S) = alpha * coverage(S) + (1-alpha) * relevance(S)`

Greedy construction starts with the empty set and repeatedly adds the candidate with maximum marginal gain in `F_alpha` until exactly `min(3, lane_candidate_count)` candidates are selected.

Tie-break order:

1. larger objective gain;
2. better original BM25 rank;
3. lexicographically smaller stable evidence/relation identity.

Predeclared alpha sensitivity family:

- `alpha = 0.25`
- `alpha = 0.50`
- `alpha = 0.75`

All three are co-primary sensitivity observations. No alpha may be selected post hoc and described as if it were preregistered as uniquely optimal.

## Why this facility-location form

The experiment tests H2 without yet granting EB a generated semantic information-demand planner.

It deliberately avoids:

- entailment/support/refutation scoring;
- LLM-generated subqueries;
- learned embeddings;
- trained rerankers;
- external corpora.

The selector asks only whether a retained set jointly represents high-relevance lexical regions of the frozen candidate pool. If even this bounded set objective cannot improve composition, that weakens the case for simple H2 and increases the plausibility of H3.

## Primary evaluation axes

### Axis Q — qualification-required preservation

Report separately for each arm:

- required relationships retained out of 22;
- required recall;
- fully covered lanes out of 18;
- deepest original BM25 rank among retained required relationships;
- retained relationship count;
- selected known-non-required/distractor count under completed PR #72 qualification gold.

### Axis O — task-aligned operational materiality

Report separately for each arm using RC1 V5 Cobalt reference labels:

- `KEEP_DISTINCT` retained out of 19;
- operational KEEP recall;
- `DROP_REDUNDANT` selected;
- `DROP_DISTRACTOR` selected;
- `UNRESOLVED` selected;
- survival of both C05 contextual `KEEP_DISTINCT` relationships that triggered RC1 action disagreement.

Do not convert `UNRESOLVED` to DROP or KEEP.

Do not treat qualification-required and `KEEP_DISTINCT` as interchangeable.

## Secondary systems checks

Before interpreting selector quality, require:

- exact PR #63 artifact digest verification;
- exact input lane/relationship identity preservation;
- deterministic replay byte equality for selection outputs;
- candidate-order permutation invariance when original rank/score fields remain attached;
- no duplicate selected identity;
- no selected identity absent from the frozen candidate pool;
- exactly `min(3,n)` selected candidates per lane for fixed-budget arms;
- no mutation of proposition, passage, source/evidence identity, original rank, or score;
- no semantic support/refutation/verdict field in selector output.

Failure of a systems check invalidates that arm's experiment result.

## Interpretation / dispositions

This is screening evidence. No outcome authorizes production use.

### `SETWISE_STRONG_SIGNAL`

May be assigned only if at least two adjacent facility alpha values:

- improve qualification-required recall over K=3;
- do not reduce RC1 V5 `KEEP_DISTINCT` recall versus K=3;
- preserve both C05 contextual KEEP relationships at the fixed three-passage budget;
- pass all systems checks;
- and do not require choosing one isolated alpha after seeing gold.

This disposition supports a separately preregistered metamorphic selector qualification. It does not qualify the selector itself.

### `CONSTRUCT_TENSION_OBSERVED`

Use when qualification-required and operational `KEEP_DISTINCT` axes materially disagree about selector quality. Preserve both results without forcing one into the other.

### `SETWISE_NOT_JUSTIFIED_ON_FROZEN_POOL`

Use when the facility family provides no robust improvement over K=3, improvement exists only at one isolated alpha, or it sacrifices operational KEEP materiality to improve qualification recall.

Such a result weakens H2 in this bounded lexical facility form and directs attention toward H3 or candidate-generation limitations rather than automatic selector complexity.

## Metamorphic successor gate

No facility selector advances directly to fresh operational review.

A promising family must first face a separately frozen metamorphic suite covering at least:

- irrelevant addition;
- duplicate and near-duplicate addition;
- rank perturbation;
- hard lexical negative;
- candidate-order permutation;
- contextual C05 evidence;
- independent corroboration;
- counterevidence symmetry;
- provenance/identity mutation.

## Stop boundary

Do not:

- rerun retrieval;
- test K=8 or another wider fixed K;
- introduce a learned reranker;
- generate semantic subqueries;
- use CAL entailment/support/refutation labels as selector inputs;
- change V1 production/default behavior;
- merge, release, tag, or promote.

Freeze all selector outputs and evaluator artifacts as a Draft Research record and stop for operator review.
