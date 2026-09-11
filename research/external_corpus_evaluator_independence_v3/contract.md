# External Corpus Retrieval Evaluator Contract v0.4-draft

This is Research Infrastructure. It defines evaluator and blind-handoff mechanics only. It does not establish benchmark validity or Evidence Bundler retrieval performance.

This revision preserves v0.3 metric semantics and resolves the validation/interface ambiguities exposed by the genuinely fresh v0.3 reproduction preserved in PR #35.

## Required identities

Manifest, hidden gold, and ranked run must each contain the keys `corpus_version`, `corpus_sha256`, and `benchmark_sha256`.

Each value must be a non-empty string. For each key, the value must be identical across manifest, hidden gold, and ranked run. Missing keys are invalid even when all three artifacts omit the same key.

`K` is a positive integer supplied by the run; each query may return zero through K hits.

## Public manifest

The public manifest represents queries, sources, passages, and provenance. Query, source, and passage IDs are unique non-empty strings.

Every passage record binds `passage_id` to a valid `source_id` plus at least one reconstructable representation locator:

- a non-empty string `locator`; or
- a non-empty string `representation_identity`.

Only `representation_identity` is the normative alternate representation field. Aliases such as `representation_id`, `representation_sha256`, or `representation` do not satisfy this contract.

Each passage `source_id` must identify a source in the same manifest. Source/passages list order has no metric meaning.

The gold query-ID set and run query-ID set must each exactly match the public manifest query-ID set. Missing or extra queries invalidate evaluation.

IDs are identity keys, not score features. A consistent stable-ID rename must preserve metric values. Artifact hashes are expected to change because the identified object changed.

## Hidden judgments

Every gold query object must explicitly contain:

- `judgments`: an array, which may be empty;
- `groups`: an array, which may be empty.

Omission of either collection is invalid and must not be silently defaulted to an empty collection.

A judgment row contains:

- `passage_id`;
- `relevance_degree`: `DECISIVE | PARTIAL | TOPICAL | IRRELEVANT | UNKNOWN`;
- `binary_relevant`: boolean for resolved judgments, `null` for `UNKNOWN`;
- `gain`: non-negative integer for resolved judgments, `null` for `UNKNOWN`;
- `role`: `SUPPORT | COUNTEREVIDENCE | NEUTRAL_OR_NOT_APPLICABLE | UNKNOWN`.

`binary_relevant=true` requires positive gain. `binary_relevant=false` requires gain 0.

If `relevance_degree == UNKNOWN`, then `binary_relevant`, `gain`, and semantic role are all unresolved: `binary_relevant=null`, `gain=null`, and `role=UNKNOWN` are required.

For resolved relevance degrees, role remains an independent dimension and may be any valid role, including `UNKNOWN`.

A passage with no judgment row is **unjudged**, not irrelevant. An `UNKNOWN` row is **judged but unresolved**, not irrelevant and not unjudged. Neither state receives relevance credit.

Gold declares `qrels_mode`:

- `complete_relevant_set`: all passages intended to count as relevant in the frozen evidence world are represented among resolved positive judgments;
- `partial`: known judgments are incomplete. Hit/recall are lower bounds against known positives and output must say `metric_interpretation=lower_bound`.

### Multi-passage groups

Within each query, a group has a non-empty `group_id` unique within that query, a `group_kind`, and a non-empty set of `passage_ids`.

The same textual `group_id` may be reused in a different query. Group identity is therefore `(query_id, group_id)`.

- `JOINTLY_REQUIRED`: covered only if all member passages occur within top K.
- `ALTERNATIVE_SUFFICIENT`: covered if at least one member occurs within top K.

Group members must be valid corpus passage IDs. Group semantics are benchmark gold and must not be inferred from rank or retrieval score.

## Ranked output

Each query has zero to K unique hits. Ranks must be exact contiguous integers `1..N`, with no gaps, ties, zero, non-integer rank, or duplicate passage IDs. Every hit passage must exist in the public corpus manifest. Unknown IDs fail closed.

The run query-ID set must exactly match both the gold and public-manifest query-ID sets. Missing or extra queries invalidate evaluation.

## Metrics

Compute each query independently first. Aggregate by macro-average over queries where the metric is defined. Always retain per-query values so undefined cases and denominators remain inspectable.

The exact metric field names are:

- `hit_at_k`: 1 if at least one known `binary_relevant=true` passage of any role appears in top K, otherwise 0. Undefined when that query has no known positive judgment.
- `evidence_recall_at_k`: retrieved known positive `SUPPORT` passages divided by all known positive `SUPPORT` passages for that query. Undefined if none exist.
- `counterevidence_recall_at_k`: retrieved known positive `COUNTEREVIDENCE` passages divided by all such passages for that query. Undefined if none exist.
- `ndcg_at_k`: gain `(2^gain - 1) / log2(rank + 1)` normalized by ideal gain ordering for that query.
- `joint_group_coverage_at_k`: satisfied groups divided by total groups for that query, using each group's declared `group_kind`. Undefined if no groups exist.
- `judgment_coverage_at_k`: retrieved passages with any judgment row divided by retrieved passages. Empty results = 1.0. Diagnostic only.
- `resolved_judgment_coverage_at_k`: retrieved passages with a non-null binary judgment divided by retrieved passages. Empty results = 1.0. Diagnostic only.

### nDCG eligibility scope

`qrels_mode=complete_relevant_set` and top-level `ndcg_eligible=true` are benchmark-wide prerequisites. All judgment-dependent nDCG eligibility predicates are then evaluated **within each query independently**.

For query `Q`, `ndcg_at_k(Q)` is defined only if all of the following hold:

1. top-level `ndcg_eligible=true`;
2. `qrels_mode=complete_relevant_set`;
3. query `Q` contains no unresolved `UNKNOWN` judgment; and
4. query `Q` contains at least two distinct positive gain levels.

Otherwise `ndcg_at_k(Q)` is null.

An unresolved `UNKNOWN` judgment in query `Q2` must not make `ndcg_at_k(Q1)` null when `Q1` independently satisfies the four conditions above. Likewise, insufficient gain-level diversity in one query must not suppress nDCG for another query.

Aggregate `ndcg_at_k` is the macro-average over queries whose per-query nDCG is defined. If no query has defined nDCG, aggregate nDCG is null.

Unjudged and `UNKNOWN` passages receive zero gain when ranking positions are inspected, but that zero must not be reinterpreted as an adjudicated non-relevance label.

## Exact successful result object

A successful evaluation returns exactly these top-level keys:

- `status`
- `k`
- `qrels_mode`
- `metric_interpretation`
- `ndcg_eligible`
- `ndcg_eligible_by_query`
- `aggregate`
- `per_query`

`status` is exactly `"ok"`.

`metric_interpretation` is exactly:

- `"point_estimate"` when `qrels_mode=complete_relevant_set`;
- `"lower_bound"` when `qrels_mode=partial`.

`ndcg_eligible_by_query` contains one boolean for every manifest query. `ndcg_eligible` is true iff at least one query is eligible.

Each `aggregate` and `per_query` metric object uses exactly the seven metric names defined above.

## Fail-closed conditions

Invalid rather than scored:

- any required identity missing, empty, or mismatched;
- duplicate manifest query, source, or passage IDs;
- passage references to unknown manifest source IDs;
- manifest passages lacking a non-empty `locator` and non-empty `representation_identity`;
- gold query object missing `judgments` or `groups`, or either field not being an array;
- duplicate judgment passage IDs within a query;
- invalid relevance degree, binary/gain combination, role, or UNKNOWN-degree/role coupling;
- invalid group kind/membership or duplicate `group_id` within a query;
- unknown passage IDs in judgments, groups, or run hits;
- gold or run query-ID set mismatch against the public manifest;
- malformed ranks or more than K hits;
- invalid qrels mode or non-boolean top-level `ndcg_eligible`.

## Required sensitivity and invariance

Sensitivity controls must change affected metrics when decision-relevant: missing decisive/support evidence, missing counterevidence, relevant rank moved across K, lost jointly-required member, and SUPPORT/COUNTEREVIDENCE mutation.

A dedicated nDCG-scope discriminator must demonstrate that an unresolved `UNKNOWN` in one query does not suppress otherwise-defined nDCG in another query.

Additional v0.4 validation discriminators must cover:

- all-missing required identity rejection;
- exact `representation_identity` spelling and alias rejection;
- UNKNOWN relevance degree with non-UNKNOWN role rejection;
- resolved relevance with `role=UNKNOWN` acceptance;
- cross-query reuse of `group_id` acceptance and same-query duplicate rejection;
- omitted `judgments`/`groups` rejection while explicit empty arrays remain valid;
- exact successful result-object field names and `metric_interpretation` labels.

Metric values must remain invariant to irrelevant serialization order, source/passages list permutation, and consistent stable-ID renaming. Gold commitment hashes are invariant to irrelevant serialization only, not ID renaming.

## Hidden-gold commitment

Commitment is SHA-256 over `canonical-json-v1` bytes. Canonicalization sorts object keys; queries by `query_id`; judgments by `passage_id`; groups by `group_id`; each group's `passage_ids` lexicographically; and emits UTF-8 JSON without insignificant whitespace.

Reordered serialization must verify to the same commitment. Any semantic mutation must fail verification.

## Scientific boundary

A fresh evaluator implementation must be frozen before reference implementation/test reveal. Even a successful reproduction establishes evaluator infrastructure only. Pilot 0A Scientific Gate 1, independent scientific adjudication, and any BM25/Semantic/Hybrid exposure remain separately governed.