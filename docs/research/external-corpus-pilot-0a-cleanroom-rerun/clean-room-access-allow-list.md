# Pilot 0A clean-room rerun - access allow-list and audit

Date: 2026-08-29

## Intended clean-room allow-list

### Durable governance

Read-only access to the durable CAL Pipeline governance files named by the task, including:

- `CAL-PIPELINE-PROJECT-CONTEXT`
- `GITHUB-AND-PR-GOVERNANCE`
- `PROJECT-STATE-LOCATION-POLICY`
- `EPISTEMIC-RECORD-CONVENTIONS`
- `AGENT-TASK-DESIGN-GUIDANCE-SYNTHESIS`
- `PRODUCT-NORTH-STAR`

### Evidence Bundler live GitHub

Read-only access to:

- repository metadata and `main` branch state;
- PRs #17, #18, #20, #21, #22;
- their metadata/comments as needed;
- exact PR #20 preregistration artifact at commit `bf6a347704d8711628e044f46c0c3fb9fa4557df`;
- exact PR #21 public evaluator contract lineage, but not evaluator A implementation when constructing a future genuinely independent evaluator B.

### FreshStack source-only surfaces

Permitted in principle:

- `freshstack/queries-oct-2024-unfiltered` at revision `00150066ff2959688ad03ce7148ffb652f2fee38`;
- `freshstack/corpus-oct-2024` at revision `069f66dc323e163b48b10d08408d282733d4393b`;
- source dataset cards/schemas/files that do not expose retrieval outputs;
- `fresh-stack/freshstack` source construction code at commit `f1c4ec96477f5100f10c83798d33b3101db727fa`, limited to construction/provenance code and excluding retrieval-result/leaderboard surfaces;
- exact upstream GitHub repository commits/files reconstructed from construction provenance.

Explicitly forbidden:

- FreshStack paper pages containing retrieval results;
- FreshStack website/leaderboard;
- README sections containing benchmark retrieval scores;
- retrieval-result tables;
- retrieval-produced candidate lists;
- published BM25/dense/fusion outputs;
- FreshStack qrels before independent scientific gold freeze.

### SciFact source-only surfaces

Permitted in principle:

- `allenai/scifact` pinned source at `68b98a56d93e0f9da0d2aab4e6c3294699a0f72e`;
- canonical dataset acquisition/licensing files;
- immutable/content-addressed archive identity and exact claim/corpus bytes;
- claim `cited_doc_ids` before adjudication;
- published evidence/rationale labels only after both independent scientific judgment artifacts are frozen.

### Isolation surface

A genuine fresh-context evaluator/adjudicator may receive only the task-prescribed handoff. Access to prior implementation/reasoning is forbidden.

## Actual access audit before terminal stop

Observed accesses:

1. Durable governance library files listed above.
2. Evidence Bundler live GitHub repository state and PR metadata/comments for #17, #18, #20, #21, #22.
3. Exact PR #20 preregistration markdown at `bf6a347704d8711628e044f46c0c3fb9fa4557df`.
4. MainFrame/Conduit project-list call attempted once for isolated-agent availability; it failed with HTTP 429 before returning a project list.
5. Source-only web search attempted for pinned FreshStack Hugging Face datasets and FreshStack construction code.

## Allow-list breach

The source-only web search unexpectedly rendered the `fresh-stack/freshstack` repository README as a search result and included a FreshStack leaderboard snapshot plus published retrieval metrics. This surface was outside the clean allow-list because the task explicitly forbids published FreshStack BM25/dense/fusion retrieval results.

No further FreshStack source reconstruction, evaluator comparison, scientific adjudication, qrel comparison, passage stability, or gold work was performed after recognizing the exposure.

## Independence status

The only attempted isolated-agent surface failed with HTTP 429. No evaluator-B implementation was commissioned, no adjudicator was commissioned, and no same-context duplicate was substituted.

Result: `INDEPENDENCE NOT ESTABLISHED` for this run.