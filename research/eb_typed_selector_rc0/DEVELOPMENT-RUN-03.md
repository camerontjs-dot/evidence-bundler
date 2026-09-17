# Development Run 03 — Full Operational-Pool Screen

Classification: **retrospective development evidence only / not a research disposition**

Corrected hosted run: `35186274289`

Job: `105088911831`

Tested head: `e93a9283181a754288d8b6d8e6f67be2a4371c96`

Tree: `a31f3f24bb125f4f46261ec51dd9c915aca67f49`

Hosted artifact: `10482472144`

Hosted artifact ZIP SHA-256: `3117b3028c7c216001f3f5050b0d1b7704d35a9f08c41ad4fc0f337b9c50729a`

Selector SHA-256: `e83e6305008a0f7a264cde2167bff80ce6399f03d34ebce10376f106c52cec6c`

Operational-pool selection SHA-256: `b1cb5c0e0a0634638e01ac017f44968218f945af7468fcb595bf2b532ad5c8dc`

Operational evaluation SHA-256: `73542390f11e436111f5ce995f698b2458f2ef3a93d8da6a5a614814bd1232db`

Relation-map SHA-256: `7e567f169dc5ce1e2b39fd5eca59413daf8fc552d9c0a8308a3a298449e9d246`

Operational-label binding SHA-256: `ee8653f348455c68f3f1c4b663df40c326315bc32ec645c1f2af27d0b9142821`

Predecessor candidate artifact SHA-256: `3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`

Semantic scorer:

- model: `cross-encoder/ms-marco-MiniLM-L6-v2`
- revision: `233902d25c440f23af6f7d6e94d2946bac0bee0a`

Generic development profile:

- `requires_direct_evidence = true`
- no lane-specific concept terms
- no operational labels or gold exposed during selection

## Preserved predecessor deviation

Run `35186045197` failed before scoring or label exposure because the workflow attempted to fetch the supervisor relation map from PR #77 rather than its PR #74 terminal authority.

That failure is preserved in `DEVIATION-OPERATIONAL-SCREEN-01-PREEXPOSURE-AUTHORITY-FETCH.md`.

The corrected successor changed only the relation-map fetch identity. Selector source, weights, candidate world, semantic scorer, generic profile, operational label binding, evaluator, and K=3 budget were unchanged.

## Execution observations

- exact predecessor candidate artifact digest: PASS;
- PR #74 relation-map staging: PASS;
- exact 18-lane / 96-relationship operational universe: PASS;
- all 96 relationships scored before label reveal: PASS;
- repeated selection replay: byte-identical;
- operational labels opened only after selection bytes existed: PASS;
- evaluator recovered the expected frozen operational label universe: 19 `KEEP_DISTINCT`, 3 `DROP_REDUNDANT`, 73 `DROP_DISTRACTOR`, 1 `UNRESOLVED`.

Each compared arm selected exactly 54 relationships: three per 18 lanes.

## Observed comparison

| Arm | KEEP_DISTINCT retained | Lanes with all KEEP covered | Non-KEEP selected |
|---|---:|---:|---:|
| BM25 top-3 | 17 / 19 | 16 / 18 | 37 |
| semantic top-3 | 17 / 19 | 16 / 18 | 37 |
| typed top-3 | **19 / 19** | **18 / 18** | **35** |
| typed without evidence posture | 17 / 19 | 16 / 18 | 37 |

The full typed arm selected:

- 19 `KEEP_DISTINCT`;
- 3 `DROP_REDUNDANT`;
- 32 `DROP_DISTRACTOR`;
- 0 `UNRESOLVED`.

BM25, semantic-only, and the evidence-posture ablation each selected:

- 17 `KEEP_DISTINCT`;
- 3 `DROP_REDUNDANT`;
- 34 `DROP_DISTRACTOR`;
- 0 `UNRESOLVED`.

## Inference

This retrospective development surface supports freezing the current selector as a **candidate for fresh qualification**.

The useful observation is not only that the typed arm recovered the two exposed deep KEEP relationships. On the broader 96-relationship operational world, the same unchanged selector recovered all 19 operational KEEP relationships at the same three-per-lane budget, while the semantic-only control did not improve on BM25.

The evidence-posture ablation exactly fell back to the BM25/semantic-only operational result. That is development evidence that the new candidate-side evidence/discourse-form signal is doing decision-relevant work rather than merely decorating the selector.

## Important limits

This does **not** qualify the selector or authorize production promotion.

The screen is retrospective and the operational labels predate this selector. The 96 relationships are the frozen 10/7 operational review world, not a complete new depth-10 corpus. The generic `requires_direct_evidence` profile is development scaffolding, not canonical ClaimGate/EvidenceGate output. The selector has been iterated after observing known predecessor failures.

Therefore the next valid step is a scientific freeze followed by fresh context-free qualification on unseen cases. No further selector tuning should occur on these exposed operational labels if this exact candidate is carried forward.
