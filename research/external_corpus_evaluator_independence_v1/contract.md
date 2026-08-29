# External Corpus Retrieval Evaluator Contract v0.1-draft

This is Research Infrastructure. It defines metric and handoff mechanics only. It does not establish benchmark validity or Evidence Bundler retrieval performance.

## Required identities

Every manifest, hidden-gold artifact, and retrieval run carries the same `corpus_version`, `corpus_sha256`, and `benchmark_sha256`. Any mismatch invalidates the evaluation. `K` is a positive integer supplied by the run and the run may contain at most K hits per query.

## Public manifest

The public manifest contains unique query IDs, unique source IDs, unique passage IDs, passage-to-source bindings, and provenance sufficient to reconstruct the represented source/passage unit. Source or passage list order has no metric meaning.

The evaluator uses IDs only as identity keys. Consistent stable-ID renaming must preserve metric values. It is expected to change artifact hashes because the revealed object is different bytes.

## Hidden gold

Each query may contain zero or more judgments. A judgment has:

- `passage_id`;
- integer `grade >= 0`;
- `role` in `support | counterevidence | other`.

`grade > 0` is binary relevance. `grade == 0` is explicitly judged non-relevant. A corpus passage with no judgment row is **unjudged**, not non-relevant.

Gold declares `qrels_mode`:

- `complete_relevant_set`: all passages intended to count as relevant for the query are represented in the gold. Unjudged passages may exist but are not known positives.
- `partial`: the judgment set is incomplete. Hit/recall results are lower bounds against known positives and must be labelled `lower_bound`.

Gold may set `ndcg_eligible=true`. nDCG is computed only if: (a) at least one grade exceeds 1, (b) qrels mode is `complete_relevant_set`, and (c) `ndcg_eligible=true`. Otherwise nDCG is `null`, not silently synthesized.

A query may also contain evidence groups with a unique `group_id` and a non-empty set of `required_passage_ids`. A group is covered only when **all** required passages are present in top K.

## Ranked run

Each query has zero to K unique hits. Ranks must be exact contiguous integers `1..N`, with no gaps, ties, zero rank, non-integer rank, or duplicate passage IDs. Every hit ID must exist in the public corpus manifest. Unknown IDs fail closed.

The set of run query IDs must exactly match the hidden-gold query IDs. Missing or extra queries fail closed.

## Metrics

Metrics are computed per query first, then macro-averaged over queries for which that metric is defined. The evaluator must also emit per-query values so aggregate denominators are auditable.

- `hit@K`: 1 if at least one known relevant passage of any role appears in top K, else 0. Undefined if the query has no known relevant passage.
- `evidence recall@K`: fraction of known relevant `support` passages retrieved in top K. Undefined if no known relevant support passages exist.
- `counterevidence recall@K`: fraction of known relevant `counterevidence` passages retrieved in top K. Undefined if none exist.
- `nDCG@K`: gain `(2^grade - 1) / log2(rank + 1)`, normalized by the ideal ordering of known judgments, only under the eligibility rule above. Unjudged hits have zero gain but are not thereby declared non-relevant.
- `joint/group coverage@K`: complete groups retrieved divided by total groups. Partial group retrieval receives zero credit for that group. Undefined if no groups exist.
- `judgment coverage@K`: judged retrieved passages divided by retrieved passages. Empty result lists have coverage 1.0. This is diagnostic, not a relevance score.

## Fail-closed conditions

Evaluation is invalid rather than scored when any of these occur:

- corpus-version, corpus hash, or benchmark hash mismatch;
- duplicate query, corpus-passage, judgment-passage, group, or ranked-hit IDs where uniqueness is required;
- unknown corpus IDs in gold, groups, or run hits;
- malformed ranks;
- more than K hits;
- query-set mismatch;
- invalid grade, role, group membership, or qrels mode.

## Invariance and sensitivity

The following must preserve metric values when semantics are unchanged:

- object-key order or list serialization order where order is declared irrelevant;
- source-order permutation;
- consistent stable-ID renaming.

The following must change the affected metric when the mutated item is decision-relevant:

- removing decisive support;
- removing counterevidence;
- moving a relevant passage across K;
- dropping a required group member;
- mutating support to counterevidence or the reverse.

## Hidden-gold commitment

The commitment is SHA-256 over `canonical-json-v1` bytes. Canonicalization sorts object keys, queries by `query_id`, judgments by `passage_id`, groups by `group_id`, and each group's required IDs lexicographically, then emits UTF-8 JSON with no insignificant whitespace.

Reordered serialization must verify to the same commitment. Any semantic mutation, including a stable-ID rename, is a different revealed gold object and must change the commitment.
