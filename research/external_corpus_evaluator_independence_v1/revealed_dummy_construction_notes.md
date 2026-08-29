# Revealed dummy construction notes

These notes concern only the synthetic dummy handoff used to test evaluator mechanics.

- `q1` deliberately contains two known support passages, one known counterevidence passage, one irrelevant passage, one jointly-required group, and one alternative-sufficient group.
- The frozen dummy run retrieves both q1 support passages but misses q1 counterevidence, so the evaluators should distinguish hit/support recall from counterevidence recall and partial group coverage.
- `q2` deliberately contains an `UNKNOWN` judgment on `p6`. That row is present to test that judged-but-unresolved differs from both an explicit irrelevant judgment and an absent judgment row.
- The `UNKNOWN` row deliberately makes graded nDCG ineligible under the frozen contract even though multiple positive gain levels exist.
- No fixture was selected or shaped using Evidence Bundler retrieval output. No production retriever was run.
