# External Corpus Retrieval Evaluator Contract v0.2-draft

This is Research Infrastructure. It defines evaluator and blind-handoff mechanics only. It does not establish benchmark validity or Evidence Bundler retrieval performance.

## Required identities

Manifest, hidden gold, and ranked run must carry identical `corpus_version`, `corpus_sha256`, and `benchmark_sha256`. Any mismatch invalidates evaluation. `K` is a positive integer supplied by the run; each query may return zero through K hits.

## Public manifest

The public manifest represents queries, sources, passages, and provenance. Query, source, and passage IDs are unique. Passage records bind `passage_id` to `source_id` plus a reconstructable locator/representation identity. Source/passages list order has no metric meaning.

IDs are identity keys, not score features. A consistent stable-ID rename must preserve metric values. Artifact hashes are expected to change because the identified object changed.

## Hidden judgments

A judgment row contains:

- `passage_id`;
- `relevance_degree`: `DECISIVE | PARTIAL | TOPICAL | IRRELEVANT | UNKNOWN`;
- `binary_relevant`: boolean for resolved judgments, `null` for `UNKNOWN`;
- `gain`: non-negative integer for resolved judgments, `null` for `UNKNOWN`;
- `role`: `SUPPORT | COUNTEREVIDENCE | NEUTRAL_OR_NOT_APPLICABLE | UNKNOWN`.

`binary_relevant=true` requires positive gain. `binary_relevant=false` requires gain 0. `UNKNOWN` requires both binary relevance and gain to be null. This keeps a deliberately unresolved judgment distinct from an absent judgment row.

A passage with no judgment row is **unjudged**, not irrelevant. An `UNKNOWN` row is **judged but unresolved**, not irrelevant and not unjudged. Neither state receives relevance credit.

Gold declares `qrels_mode`:

- `complete_relevant_set`: all passages intended to count as relevant in the frozen evidence world are represented among resolved positive judgments;
- `partial`: known judgments are incomplete. Hit/recall are lower bounds against known positives and output must say `metric_interpretation=lower_bound`.

### Multi-passage groups

A group has unique `group_id`, `group_kind`, and a non-empty set of `passage_ids`.

- `JOINTLY_REQUIRED`: covered only if all member passages occur within top K.
- `ALTERNATIVE_SUFFICIENT`: covered if at least one member occurs within top K.

Group members must be valid corpus passage IDs. Group semantics are benchmark gold and must not be inferred from rank or retrieval score.

## Ranked output

Each query has zero to K unique hits. Ranks must be exact contiguous integers `1..N`, with no gaps, ties, zero, non-integer rank, or duplicate passage IDs. Every hit passage must exist in the public corpus manifest. Unknown IDs fail closed.

The run query-ID set must exactly match the gold query-ID set. Missing or extra queries invalidate evaluation.

## Metrics

Compute per query first. Aggregate by macro-average over queries where the metric is defined. Always retain per-query values so undefined cases and denominators remain inspectable.

- `hit@K`: 1 if at least one known `binary_relevant=true` passage of any role appears in top K, otherwise 0. Undefined when a query has no known positive judgment.
- `evidence recall@K`: retrieved known positive `SUPPORT` passages divided by all known positive `SUPPORT` passages. Undefined if none exist.
- `counterevidence recall@K`: retrieved known positive `COUNTEREVIDENCE` passages divided by all such passages. Undefined if none exist.
- `nDCG@K`: gain `(2^gain - 1) / log2(rank + 1)` normalized by ideal gain ordering. It is computed only if `ndcg_eligible=true`, qrels mode is `complete_relevant_set`, no unresolved `UNKNOWN` judgment exists, and at least two distinct positive gain levels exist. Otherwise it is null.
- `joint_group_coverage@K`: satisfied groups divided by total groups, using each group's declared `group_kind`. Undefined if no groups exist.
- `judgment_coverage@K`: retrieved passages with any judgment row divided by retrieved passages. Empty results = 1.0. Diagnostic only.
- `resolved_judgment_coverage@K`: retrieved passages with a non-null binary judgment divided by retrieved passages. Empty results = 1.0. Diagnostic only.

Unjudged and `UNKNOWN` passages receive zero gain when ranking positions are inspected, but that zero must not be reinterpreted as an adjudicated non-relevance label.

## Fail-closed conditions

Invalid rather than scored:

- corpus version/hash or benchmark hash mismatch;
- duplicate query, corpus-passage, judgment-passage, group, or ranked-hit IDs where uniqueness is required;
- unknown passage IDs in judgments, groups, or run hits;
- malformed ranks or more than K hits;
- query-set mismatch;
- invalid relevance degree, binary/gain combination, role, group kind/membership, or qrels mode.

## Required sensitivity and invariance

Sensitivity controls must change affected metrics when decision-relevant: missing decisive/support evidence, missing counterevidence, relevant rank moved across K, lost jointly-required member, and SUPPORT/COUNTEREVIDENCE mutation.

Metric values must remain invariant to irrelevant serialization order, source/passages list permutation, and consistent stable-ID renaming. Gold commitment hashes are invariant to irrelevant serialization only, not ID renaming.

## Hidden-gold commitment

Commitment is SHA-256 over `canonical-json-v1` bytes. Canonicalization sorts object keys; queries by `query_id`; judgments by `passage_id`; groups by `group_id`; each group's `passage_ids` lexicographically; and emits UTF-8 JSON without insignificant whitespace.

Reordered serialization must verify to the same commitment. Any semantic mutation must fail verification.
