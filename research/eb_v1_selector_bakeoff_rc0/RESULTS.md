# Evidence Bundler V1 Frozen-Pool Selector Bake-off RC0 — Results

Terminal screening disposition:

`SETWISE_NOT_JUSTIFIED_ON_FROZEN_POOL`

Secondary observation:

`CONSTRUCT_TENSION_OBSERVED`

This is frozen-pool architecture screening only. No selector is qualified for V1 or production use.

## Frozen inputs

- PR #63 decisive artifact `10282804289`
- exact ZIP digest `sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`
- 18 normative proposition lanes
- 96 positive-score candidate relationships
- PR #72 completed qualification gold
- RC1 V5 Cobalt operational reference freeze `79e8c41462b791716c89b7f8329f15b580d504a7`

No retrieval was rerun and no semantic reviewer was launched.

## Primary result

At the same three-passage-per-lane budget, all three preregistered facility-location weights reproduced the K=3 qualification outcome rather than improving it.

| Arm | Retained | Qualification required | Full lanes | V5 KEEP_DISTINCT | C05 contextual KEEP |
|---|---:|---:|---:|---:|---:|
| fixed K=3 | 54 | 19/22 | 15/18 | 17/19 | 2/2 |
| facility alpha 0.25 | 54 | 19/22 | 15/18 | 17/19 | 2/2 |
| facility alpha 0.50 | 54 | 19/22 | 15/18 | 17/19 | 2/2 |
| facility alpha 0.75 | 54 | 19/22 | 15/18 | 17/19 | 2/2 |
| largest relative gap, cap 3 | 45 | 18/22 | 14/18 | 17/19 | 2/2 |

Every facility variant missed the same qualification-required relationships as K=3:

- `C03_POOL_MISS:child:2|C03-P2`
- `C06_HARD_NEG:child:1|C06-P1`
- `RETRIEVAL_APERTURE:child:1|RET-AP-P6`

On the operational V5 construct, `C03-P2` is `UNRESOLVED`, while `C06-P1` and `RET-AP-P6` are `KEEP_DISTINCT`. Thus the two operationally decisive deep misses are exactly the rank-4 hard-negative case and rank-7 aperture case.

The facility family did not rescue either.

## Burden

Completed PR #72 qualification gold means every non-required relationship in this frozen 96-relationship world is classifiable.

- fixed K=3: 35 non-required relationships selected;
- facility 0.25: 35;
- facility 0.50: 35;
- facility 0.75: 35.

Operationally:

- K=3 / facility 0.25 / facility 0.50 each selected 34 `DROP_DISTRACTOR`, 3 `DROP_REDUNDANT`, 17 `KEEP_DISTINCT`;
- facility 0.75 selected 35 `DROP_DISTRACTOR`, 2 `DROP_REDUNDANT`, 17 `KEEP_DISTINCT`.

There is therefore no burden/recall argument for this lexical facility objective over K=3.

## Cheap score control and construct tension

Largest-relative-gap stopping retained only 45 relationships while preserving the same 17/19 operational `KEEP_DISTINCT` set as K=3. It selected 26 operational distractors and 2 redundant relationships.

However it fell from 19/22 to 18/22 on qualification-required recall because it additionally removed:

`C04_QUALIFIER:child:2|C04-P2`

RC1 V5 labels that relationship `DROP_REDUNDANT`.

This is a concrete construct tension, not an evaluator nuisance. The qualification-required set and operational materiality reference answer different questions and must remain separate.

The gap rule still misses both operationally important deep items (`C06-P1`, `RET-AP-P6`), so it is at most a burden-trimming signal, not a solution to the evidence-survival problem.

## Failure-mechanism observation

The two operationally important deep misses have different lexical failure shapes:

### C06 hard negative

Proposition:

`Lumen Filter removal in the 5 micron test was 93 percent.`

Required/KEEP passage at BM25 rank 4:

`Lumen Filter measured efficiency result was ninety-three percent.`

Three higher-ranked hard negatives reproduce essentially the full proposition vocabulary but explicitly describe setup/humidity/revision uses rather than the measured result. Generic lexical relevance and lexical diversity therefore prefer the decoys.

### Retrieval aperture

Proposition:

`Alpha exceeded Beta by 4 units.`

Required/KEEP passage at BM25 rank 7 contains the exact proposition, but only after a very long repeated `Calibration context` prefix. It has full query-token coverage but a low BM25 score due to the long candidate context.

These are different failure mechanisms: hard-negative semantic/materiality confusion and long-context score dilution. A single diversity objective should not be expected to solve both.

## Systems checks

PASS:

- exact predecessor artifact digest;
- canonical selector replay byte equality;
- 20 input-order permutations per lane for each facility alpha;
- selected identities remain within the frozen pool;
- no duplicate selected identity;
- exact fixed-budget cardinality for K=3/facility arms;
- no semantic support/refutation/verdict output;
- no retrieval rerun;
- no semantic reviewer.

The pre-evaluation GitHub archive formatting deviation is preserved separately and did not change selection semantics.

## Interpretation

This bounded lexical facility-location implementation does not support H2 as the immediate V1 remedy.

It does **not** falsify set-wise selection generally. More semantic demand representations, learned set selectors, or generated information requirements could behave differently, but those mechanisms would introduce additional authority and complexity that now require explicit justification.

The evidence shifts attention toward **H3: materiality representation / relevance-signal failure**.

The next smallest discriminator should characterize and test proposition-relative materiality signals that can separately address:

1. hard lexical negatives that copy query vocabulary but negate/non-result its evidentiary role;
2. long-context candidates containing a highly relevant local span whose chunk-level BM25 score is diluted;
3. contextual/qualifier evidence where qualification-required and operational KEEP/DROP constructs diverge.

Do not advance this facility selector to metamorphic qualification or fresh operational review.

## Stop boundary

No production-default change, selector deployment, learned reranker, semantic subquery generation, candidate-generation replacement, merge, release, tag, or V1 promotion is authorized.
