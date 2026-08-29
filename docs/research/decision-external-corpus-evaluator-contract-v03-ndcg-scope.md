# External Corpus Evaluator Contract v0.3 — nDCG Scope Adjudication

## Status

Research Infrastructure decision record. No retrieval execution or Pilot scientific execution is authorized by this record.

## OBSERVED

1. Contract v0.2-draft required per-query metric computation and macro-aggregation over queries where a metric is defined.
2. Contract v0.2-draft also said nDCG is available only when no unresolved `UNKNOWN` judgment exists and at least two distinct positive gain levels exist, without explicitly stating whether those judgment-dependent conditions are query-local or benchmark-global.
3. The pinned reference evaluators A/B at `764144f3da77140a8e542158948b4e88d40a7421` implemented both conditions globally across all gold queries.
4. A genuinely fresh implementation was frozen before reveal and independently implemented those conditions per query. Its frozen bytes were not repaired after reveal.
5. The fresh run therefore produced a material disagreement: one clean query had defined nDCG while A/B suppressed nDCG everywhere because a different query contained an unresolved `UNKNOWN`.
6. The same comparison also exposed that A/B v1 did not enforce every manifest invariant already stated by the contract, including unique manifest query/source IDs and passage-to-source validity.

## ALTERNATIVES CONSIDERED

### Global nDCG suppression

Any unresolved `UNKNOWN` anywhere in benchmark gold would suppress nDCG for every query.

This is conservative but introduces a cross-query dependency into a metric whose numerator and ideal denominator are query-local. It also conflicts with the existing rule to macro-average only over queries where a metric is defined. Preserving A/B v1 behavior is not sufficient justification for choosing this semantics after an independent disagreement has been observed.

### Per-query nDCG eligibility

Benchmark-wide switches (`qrels_mode`, top-level `ndcg_eligible`) remain global. Judgment-dependent conditions (`UNKNOWN` presence and positive-gain diversity) are evaluated within each query.

This preserves local metric semantics, permits inspectable nulls on affected queries, and makes aggregate nDCG a macro-average over actually defined query values.

## DECISION

Adopt **per-query nDCG eligibility** in contract v0.3-draft.

For query `Q`, nDCG is defined only when:

1. top-level `ndcg_eligible=true`;
2. `qrels_mode=complete_relevant_set`;
3. `Q` has no unresolved `UNKNOWN`; and
4. `Q` has at least two distinct positive gain levels.

An unrelated query's `UNKNOWN` or gain-level deficiency cannot suppress nDCG for `Q`.

Also make already-written manifest invariants explicit fail-closed requirements in the successor contract and successor reference evaluators rather than silently preserving v1 under-validation.

## WHY THIS IS THE SMALLEST JUSTIFIED CHANGE

The fresh disagreement falsified reproducibility of the ambiguous v0.2 contract. The smallest repair is to make the disputed scope explicit and add one direct discriminating fixture. No scientific rows, retrieval output, benchmark expansion, model behavior, or production code needs to change.

The v1 contract/evaluators/tests remain unchanged as historical evidence. The corrected material lives in a new v2 research-infrastructure directory.

## FALSIFIER / FUTURE TEST

A dedicated two-query fixture must contain:

- one query with complete resolved graded judgments and at least two positive gain levels; and
- a second query containing an unresolved `UNKNOWN` while otherwise having sufficient graded gain diversity.

The required result is:

- nDCG defined for the first query;
- nDCG null for the second query; and
- aggregate nDCG equal to the first query's nDCG.

A future genuinely fresh implementation must reproduce this and the broader dummy/adversarial contract after freezing before reveal. If it does not, evaluator reproducibility remains unsupported.

## NON-CLAIMS

This decision does not establish benchmark validity, scientific gold quality, Pilot 0A methodology validity, Evidence Bundler retrieval performance, or authorization to begin scientific Gate 1.
