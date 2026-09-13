# EB V1 K=7 Gold-Coverage Completion — Terminal Results

## Terminal disposition

`FALSIFIED`

Experiment-specific conclusion:

`FIXED_K_WIDENING_REJECTED_ON_COMPLETED_QUALIFICATION_GOLD`

## Reviewer evidence

Two independent blind reviewers adjudicated the exact preregistered 27-item packet.

- exact label agreement: `27 / 27`
- `UNRESOLVED`: `0`
- third-review items: `0`
- every completed relation: `KNOWN_NON_REQUIRED_OR_DISTRACTOR`

The reviewer-seen packet canonical SHA-256 is:

`4f50b1e385c48b6b15fc223f4700f0c104ce1633742887ced388fe6342420e9c`

The distributed ZIP raw packet SHA-256 is:

`0b8b3e9021a992bbcc810cce7c3d2293b881d4d9eb7db0d0e9b7e3cb4b211455`

That raw hash is the packet identity frozen in the original preregistration before reviewer exposure.

## Frozen predecessor verification

Predecessor K=7 artifact:

- run: `34649326414`
- artifact: `10282804289`
- digest: `sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`
- predecessor disposition: `INCONCLUSIVE_GOLD_COVERAGE`

The downloaded artifact ZIP hashes exactly to the frozen digest. Its internal `SHA256SUMS` also verifies.

Inherited K=7 facts remain unchanged:

- `candidate_depth=10`, `retained_k=7`
- rank-7 preserved defect crosses retention
- zero required-evidence regressions
- structural/order invariants passed
- total retained relationships `96 <= 108`

## Completed burden gate

Frozen failure rule:

> fail iff more than 50% of the 18 normative lanes are `KNOWN_DISTRACTOR_DOMINATED`, where a lane is dominated iff at least 80% of its retained proposition-passage relationships are `known_non_required_or_distractor`.

Observed after gold completion:

- fully adjudicable lanes: `18 / 18`
- distractor-dominated lanes: `10 / 18`
- threshold for failure: `> 9 / 18`
- gate result: **FAIL**

The ten dominated lanes are both lanes of `C01_DIRECT`, both lanes of `C03_POOL_MISS`, both lanes of `C06_HARD_NEG`, both lanes of `C07_DUPLICATE`, and both `RETRIEVAL_APERTURE` lanes.

The remaining eight lanes are not dominated.

## Preserved apparatus deviation

At reviewer-output ingestion, the GitHub archival copy of the blind packet was found to contain the correct 27 opaque IDs and the correct 27 semantic pairs but with IDs permuted against pairs due to the earlier connector repair sequence.

This did not affect reviewer exposure: the ZIP actually supplied to both reviewers is the exact preregistered packet and matches the frozen canonical packet hash. The archival defect is preserved in `DEVIATION-POSTREVIEW-PACKET-ARCHIVAL-PERMUTATION.md`, and the GitHub packet was restored to the exact reviewer-seen mapping before terminal evaluation.

## Interpretation

The K=7 experiment established a real mechanical benefit: widening retention to seven recovers the preserved rank-7 required passage and introduces no required-evidence regression on the frozen cohort.

However, after completing the previously missing proposition-relative judgments, that benefit comes with review burden that crosses the experiment's preregistered distractor-dominance failure boundary.

Therefore K=7 is **not** justified as the V1 production/default retention policy by this evidence.

This falsifies the tested fixed-K widening remedy. It does not by itself falsify candidate depth 10, BM25 as a candidate generator, or a different coverage-aware/nonredundant selection mechanism.

## Stop boundary

Stop here.

Do not automatically test K=8, another fixed K, an alternate selector, reranker, threshold, semantic retriever, query rewrite, CAL semantic run, production-default mutation, merge, release, tag, or promotion.

A new operator decision is required for the next V1 slice.
