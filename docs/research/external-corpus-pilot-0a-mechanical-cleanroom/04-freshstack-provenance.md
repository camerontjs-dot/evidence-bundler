# Gate 1 — FreshStack exact provenance reconstruction

## Outcome

`FALSIFIED`

The exact frozen Pilot 0A FreshStack object cannot be reconstructed from its preregistered query dataset revision without changing the frozen sample or substituting another dataset state.

## Decisive frozen-object mismatch

Frozen query dataset:

- dataset: `freshstack/queries-oct-2024-unfiltered`
- revision: `00150066ff2959688ad03ce7148ffb652f2fee38`

Source-only acquisition at that exact revision observed:

| topic | frozen row count | frozen selected index | observed test rows | selected row present |
|---|---:|---:|---:|---|
| langchain | 318 | 271 | 318 | yes |
| yolo | 94 | 42 | 94 | yes |
| laravel | 230 | 121 | 310 | yes |
| angular | 310 | 248 | 230 | **no** |
| godot | 197 | 36 | 0 | **no** |

The exact pinned file tree contains test parquet files for `langchain`, `yolo`, `laravel`, and `angular`, but no `godot` test data file. `angular` contains only 230 physical test rows, so frozen physical row 248 does not exist.

This is not an ambiguity in relevance or source selection. It is an identity/reconstruction contradiction in the frozen preregistration itself. Repair would require changing the frozen case identity, changing the pinned query revision, or substituting another state, all explicitly forbidden.

## Official corpus reconstruction

The exact official corpus revision remained mechanically accessible:

- dataset: `freshstack/corpus-oct-2024`
- revision: `069f66dc323e163b48b10d08408d282733d4393b`

Observed complete topic partitions:

| topic | corpus rows | parquet SHA-256 |
|---|---:|---|
| langchain | 49,514 | `f1e63bf897f30062704cd77b22a4c4961ea74824c0511c17e20098f4f203fa52` |
| yolo | 27,207 | `bb59408c51b3bddc527ae5de46858955d129b9157adb1100e6a7b50c560c76da` |
| laravel | 52,351 | `3d7c39368af7ccf23c41d69bc95d0b942060a4f140a38664bede593a51375a01` |
| angular | 117,288 | `d0eacace62e67c6880f114f75554e7ae6b362062935bc8a54f03a9113f3d5879` |
| godot | 25,482 | `2e3f700c033c3f5dc6cdc4dd05c7e402baca1b7c4f9ed87a274ce73f4b6ffa41` |

Each official parquet schema is `_id`, `text`, `metadata`.

## Immutable upstream source binding

Pinned FreshStack construction code independently establishes that source chunk generation records the cloned repository's `git rev-parse HEAD` as `commit_id`, while the emitted source URL is constructed from the repository default branch.

The source-only harness inspected the Git history of the same official corpus dataset only. It checked 16 accessible revisions; 12 contained the langchain train data with the same top-level schema and four predated that data. No checked revision yielded a non-null `commit_id` through the published representation. Therefore no deterministic official-to-historical commit-bearing join was available from that exact dataset history, and upstream source-byte binding was `NOT_EXECUTED`.

This secondary provenance gap did not require a terminal classification decision because the frozen query-identity contradiction already falsified Gate 1.

## Firewall state

The Gate 1 acquisition used direct pinned dataset/Git artifacts only. It did not open FreshStack README, qrels, nuggets, candidate lists, retrieval results, leaderboards, papers, or general web search results.

## Stop rule

Per the frozen hard gate, scientific passage materialization and adjudication stop here. The exact frozen ten-case object is not repaired around the failure.
