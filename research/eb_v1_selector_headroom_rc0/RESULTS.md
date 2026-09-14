# Oracle / Headroom RC0 Results

Classification: retrospective diagnostic only. No selector qualification and no production authorization.

## Authorities

- PR #63 decisive artifact: run `34649326414`, artifact `10282804289`, exact ZIP SHA-256 `3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`.
- PR #72 terminal head: `22d83d9af465a026eb58ff64888267c4fce18619`.
- PR #72 established that all 27 relationships left unresolved by the sparse PR #63 burden gold were `KNOWN_NON_REQUIRED_OR_DISTRACTOR`.

The oracle below is therefore a **qualification-required oracle**, not the later RC1 V5 `KEEP_DISTINCT` operational construct.

## Observed headroom

Across 18 normative proposition lanes:

- frozen positive-score candidate/retained relationships in the 10/7 receipt: **96**;
- qualification-required relationships: **22**;
- conservative perfect-selector set size: **22**;
- theoretical removable relationships: **74 / 96 = 77.08%**;
- required relationships per lane: mean **1.22**, median **1**, maximum **2**;
- 14 lanes require one relationship; 4 require two.

This is substantial selector headroom. It does not show that a realizable selector can achieve the oracle.

## Fixed-K frontier

| K | retained relationships | required recall | fully covered lanes |
|---:|---:|---:|---:|
| 1 | 18 | 13/22 = 59.09% | 9/18 |
| 2 | 36 | 17/22 = 77.27% | 13/18 |
| 3 | 54 | 19/22 = 86.36% | 15/18 |
| 4 | 72 | 20/22 = 90.91% | 16/18 |
| 5 | 86 | 20/22 = 90.91% | 16/18 |
| 6 | 92 | 21/22 = 95.45% | 17/18 |
| 7 | 96 | 22/22 = 100% | 18/18 |

The three qualification-required relationships below rank 3 are:

- `C06-P1`, rank 4;
- `C03-P2`, rank 6;
- `RET-AP-P6`, rank 7.

Thus the fixed-K tradeoff is not an artifact of one isolated rank-7 case.

## Cheap adaptive-score diagnostics

### Global score / top-score ratio

The lowest required relation has a BM25 score only **0.2464923714** times the top score in its lane. A single global relative-score threshold must therefore be at or below that value to preserve all 22 qualification-required relationships.

At the lossless threshold, the selector still retains **73 / 96 relationships**.

Interpretation: a simple global score threshold reduces burden somewhat but captures only a minority of the available oracle headroom.

### Largest relative score-gap stopping

A lane-local rule that stops at the largest relative score drop retains **56 relationships**, but preserves only **19 / 22 required relationships** and fully covers only **15 / 18 lanes**.

It misses:

- `C04-P2` at rank 2;
- `C06-P1` at rank 4;
- `RET-AP-P6` at rank 7.

This directly falsifies the naive explanation that the useful/noisy boundary is reliably visible as the largest BM25 score gap on this frozen cohort.

## Decision

Phase 0 shows enough theoretical headroom to justify a selector bake-off.

The data also weaken H1 in its simplest form. Fixed thresholds/gaps do not approach the 22-relationship oracle while preserving all qualification-required evidence.

The next discriminating test should therefore compare:

1. frozen K=3;
2. the strongest simple deterministic score baseline retained as a control;
3. one deterministic set-wise facility-location/coverage selector.

Do not add a learned pointwise reranker yet. The next test should determine whether H2 (set composition) explains the gap before paying the complexity/authority cost of H3 or learned selection.

## Non-claims

- Candidate depth 10 is not established as universally sufficient.
- The 22-relation oracle is not an operational production target.
- Qualification-required gold is not identical to RC1 V5 `KEEP_DISTINCT` task gold.
- No selector has been qualified.
- No retrieval, admission, CAL, or production behavior was changed.
