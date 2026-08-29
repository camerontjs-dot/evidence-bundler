# Pilot 0A clean-room rerun - contamination and exposure log

Date: 2026-08-29

## Terminal contamination event

A web search was issued with source-only intent to locate pinned FreshStack Hugging Face dataset surfaces and FreshStack construction-code provenance.

The returned result for `fresh-stack/freshstack` rendered README content that included a published FreshStack leaderboard snapshot and retrieval metrics. This was not intentionally opened as a leaderboard or paper result page, but the task firewall makes exposure itself disqualifying.

### Exact result surface exposed

The rendered README result included:

- a section titled `FreshStack Leaderboard`;
- a leaderboard snapshot dated Jun 12, 2025;
- published retrieval columns including average and per-topic `alpha@10`, `coverage@20`, and `recall@50`;
- an `Oracle: Fusion` row with aggregate/per-topic retrieval scores;
- an example `BM25` leaderboard-data object with aggregate/per-topic retrieval scores.

Values visibly exposed in that result included:

#### Oracle: Fusion row

- average: alpha@10 `0.541`, coverage@20 `0.868`, recall@50 `0.755`
- langchain: `0.519`, `0.881`, `0.655`
- yolo: `0.601`, `0.876`, `0.825`
- laravel: `0.566`, `0.888`, `0.818`
- angular: `0.544`, `0.881`, `0.756`
- godot: `0.476`, `0.815`, `0.719`

#### BM25 example object

- average: alpha_ndcg_10 `0.218`, coverage_20 `0.448`, recall_50 `0.316`
- langchain: `0.230`, `0.475`, `0.261`
- yolo: `0.137`, `0.342`, `0.337`
- laravel: `0.319`, `0.602`, `0.441`
- angular: `0.259`, `0.551`, `0.340`
- godot: `0.144`, `0.268`, `0.200`

These values were not used to select cases, set source aperture, match provenance, judge relevance, define negatives, change passage boundaries, or make any scientific-methodology claim.

## Required exposure state

- production BM25 exposed: `false`
- Hybrid exposed: `false`
- Semantic-only exposed: `false`
- Evidence Bundler dense retrieval exposed: `false`
- Evidence Bundler lexical retrieval exposed: `false`
- other candidate/substitute retriever exposed: `false`
- FreshStack retrieval-produced candidate-list exposure: `false`
- FreshStack published retrieval-result exposure: `true`
- published FreshStack qrel exposure before gold freeze: `false`
- published SciFact evidence/rationale exposure before gold freeze: `false`
- scientific gold creation state: `NOT_EXECUTED`

## Isolation surface event

Before the retrieval-result contamination event, the MainFrame/Conduit project-list call was attempted to establish whether genuine isolated evaluator/adjudicator sessions were available. It returned HTTP 429 and no project list. No isolated session was created.

## Stop action

Immediately after recognizing the published retrieval-result exposure:

- FreshStack provenance reconstruction stopped;
- FreshStack aperture confirmation stopped;
- SciFact reconstruction was not begun;
- evaluator-B implementation/comparison was not begun;
- passage materialization was not begun;
- scientific adjudication was not begun;
- published-qrel comparison was not begun;
- segmentation/gold stability was not begun.

The exposure is preserved as a terminal isolation falsifier. It is not being rationalized as harmless.