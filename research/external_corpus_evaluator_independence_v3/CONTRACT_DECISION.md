# External Corpus Retrieval Evaluator Contract v0.4 — Decision Record

## Classification

Research Infrastructure only. This does not modify Pilot 0A scientific cases, source bytes, passage rules, scientific gold, retrieval configuration, production code, Contract A/B/C, or CAL behavior.

## Frozen predecessor evidence

This successor responds only to the seven uncovered validation/interface disagreement classes preserved by fresh reproduction PR #35 at terminal head `0d202671eb2aa638b68cc1dd36bb29084119e41c`.

The predecessor independently reproduced all metric semantics exercised by the v0.3 authorized suite, including the query-local nDCG discriminator, but the full evaluator-independence prerequisite remained `INCONCLUSIVE` because uncovered schema/validation choices were not normative enough.

No Pilot scientific row, qrel, relevance label, retriever output, or target-system result is used to select these clarifications.

## Objective

Clarify only the ambiguous or reference-inconsistent surfaces exposed by PR #35 so that a future genuinely fresh implementation can be judged against one complete written contract rather than inferred reference behavior.

## Normative decisions

### D1 — required envelope identities are present and equal

`corpus_version`, `corpus_sha256`, and `benchmark_sha256` are required keys in manifest, hidden gold, and ranked run.

Each value must be a non-empty string and the value for each key must be identical across all three artifacts.

All-missing `None == None == None` is invalid.

Reason: v0.3 already said the artifacts "must carry" these identities. This clarification makes presence explicit rather than adopting the predecessor reference bug.

### D2 — normative passage representation field

Every manifest passage must contain either:

- a non-empty string `locator`; or
- a non-empty string `representation_identity`.

Only `representation_identity` is the normative alternate field. `representation_id`, `representation_sha256`, `representation`, or other aliases do not satisfy this requirement.

Reason: freeze one portable wire shape rather than permit implementation-specific aliases.

### D3 — UNKNOWN relevance degree is fail-closed on semantic role

If `relevance_degree == "UNKNOWN"`:

- `binary_relevant` must be `null`;
- `gain` must be `null`;
- `role` must be `"UNKNOWN"`.

For resolved relevance degrees, `role` may be any member of the existing role enumeration, including `UNKNOWN`.

Reason: an unresolved relevance relation must not carry authoritative SUPPORT/COUNTEREVIDENCE polarity. Conversely, resolved relevance and unresolved semantic-role classification remain separable dimensions.

### D4 — group identity is query-local

`group_id` must be unique within each gold query. The same textual `group_id` may occur in different queries.

Reason: groups are nested under and evaluated within a query; their semantic identity is `(query_id, group_id)`.

### D5 — gold collections are explicit

Every gold query object must contain both:

- `judgments`: an array, which may be empty;
- `groups`: an array, which may be empty.

Omission is invalid and is not silently defaulted to an empty list.

Reason: preserve explicit evidence-state representation and fail closed on absent required collections.

### D6 — exact result-object interface

A successful evaluation result uses exactly these top-level keys:

- `status`
- `k`
- `qrels_mode`
- `metric_interpretation`
- `ndcg_eligible`
- `ndcg_eligible_by_query`
- `aggregate`
- `per_query`

`status` is exactly `"ok"`.

Metric field names are exactly:

- `hit_at_k`
- `evidence_recall_at_k`
- `counterevidence_recall_at_k`
- `ndcg_at_k`
- `joint_group_coverage_at_k`
- `judgment_coverage_at_k`
- `resolved_judgment_coverage_at_k`

`metric_interpretation` is exactly:

- `"point_estimate"` for `complete_relevant_set`;
- `"lower_bound"` for `partial`.

`ndcg_eligible_by_query` reports the query-local nDCG eligibility boolean for every manifest query. `ndcg_eligible` is `true` iff at least one query is eligible.

Reason: independent reproduction requires an interface contract, not only approximately equivalent metric semantics.

### D7 — all v0.3 metric semantics remain unchanged

The v0.3 metric definitions, query-local nDCG eligibility, ranked-output constraints, hidden-gold commitment, sensitivity controls, and invariance requirements remain unchanged except where this decision record explicitly clarifies validation/interface behavior.

## Required successor discriminator

Before Pilot 0A Scientific Gate 1 can be authorized, a new genuinely fresh implementation must be built from the v0.4 written contract without access to either v0.4 reference evaluator.

It must be frozen before reference reveal and must reproduce:

1. all existing v0.3 metric/invariance behaviors;
2. the dedicated query-local nDCG discriminator;
3. all seven clarification classes above;
4. malformed-input fail-closed behavior;
5. exact successful result-object shape.

Any uncovered disagreement must be preserved. Do not repair the fresh implementation after reveal and retain the same independence claim.

## Falsifier

The evaluator-independence prerequisite remains unresolved if a genuinely fresh implementation, built from this clarified contract, differs materially from the frozen reference implementations on any contract-governed validation, metric, commitment, invariance, or output-interface behavior and the difference cannot be localized to a reference defect that directly contradicts the written v0.4 contract.

## Nonclaims

This decision does not establish corpus validity, scientific-gold validity, independent scientific adjudication, retrieval quality, Hybrid superiority, production readiness, or authorization to run Pilot 0A retrieval.