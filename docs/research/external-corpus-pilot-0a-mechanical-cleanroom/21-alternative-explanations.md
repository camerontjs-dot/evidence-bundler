# Explicit alternative explanations

This record is bounded by the Gate 1 hard stop. Alternatives requiring passage materialization or scientific gold were not tested after the falsifier.

| # | alternative | status | basis |
|---:|---|---|---|
| 1 | FreshStack aperture is secretly retrieval-conditioned | `FALSIFIED AS EXPLANATION` | pinned source loader derives corpus and query from the same topic subset; complete topic partition needs no candidate list/qrel |
| 2 | FreshStack source-version reconstruction is ambiguous | `REMAINS PLAUSIBLE / SECONDARY` | construction code records commit ID, but checked official dataset history did not expose one; source-byte binding was not completed |
| 3 | SciFact immutable reconstruction is not reproducible | `FALSIFIED AS EXPLANATION` | canonical archive reproduced expected SHA-256 and byte size exactly |
| 4 | Passage segmentation manufactures decisive evidence | `NOT_TESTED` | hard stop before Gate 5 |
| 5 | Independent judges follow the same superficial cue | `NOT_TESTED` | no scientific adjudicators created |
| 6 | Published qrels leaked before gold freeze | `FALSIFIED AS EXPLANATION` | exposure receipt records no FreshStack qrel or SciFact evidence exposure; no gold was created |
| 7 | Metadata leaks relevance | `NOT_TESTED` | hard stop before adjudication |
| 8 | Evaluator contract admits multiple reasonable interpretations | `NOT_TESTED` | fresh independent evaluator B unavailable |
| 9 | Evaluator B was not genuinely independent | `SUPPORTED AS A LIMITATION` | no independent evaluator B was created; same-context predecessor implementation was not reused |
| 10 | Gold stability depends on one corpus-specific convention | `NOT_TESTED` | no gold created |
| 11 | Information-acquisition surfaces leaked retrieval behavior despite allow-list | `FALSIFIED AS EXPLANATION FOR THIS RUN` | source-only workflow receipt reports no search, qrels, candidate lists, retrieval results, or retriever execution |
| 12 | Upstream source reconstruction silently substituted current HEAD | `FALSIFIED AS EXPLANATION FOR PERFORMED WORK` | no current-HEAD source substitution was used; source binding was left unexecuted rather than guessed |

## Strongest remaining alternative to the causal interpretation

The preregistered FreshStack query revision may itself be the wrong revision identity: a different historical revision may contain the frozen `angular` and `godot` row worlds that PR #20 intended. That possibility does **not** rescue Pilot 0A, because the exact frozen object binds the query dataset to `00150066ff2959688ad03ce7148ffb652f2fee38`, and changing that revision would change the frozen object.

## Cheapest successor discriminator

In a separate methodology-design task, inspect only the Git history of `freshstack/queries-oct-2024-unfiltered` to determine whether an exact historical revision contains all five preregistered topic partitions and row counts. The purpose would be to diagnose the preregistration failure and design a self-consistency freeze gate, not to repair Pilot 0A or create the 24–30-case apparatus.
