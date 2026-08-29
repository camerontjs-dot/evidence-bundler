# Pre-reveal alignment deviation: Pilot 0A semantics

After the first dummy pre-reveal snapshot (`496f5bed508fb00673d77c00621036e4eefc3dd5`) was created, the parallel External Corpus Methodology Pilot 0A preregistration became available at `bf6a347704d8711628e044f46c0c3fb9fa4557df`.

Only the preregistration was inspected. No scientific pilot relevance judgments, qrels, evidence labels, or adjudicator outputs were opened or used.

The preregistration made two evaluator-contract requirements explicit that the first dummy draft represented too narrowly:

1. `UNKNOWN` must remain distinct from both `IRRELEVANT` and an unjudged passage.
2. Multi-passage groups may be `JOINTLY_REQUIRED` or `ALTERNATIVE_SUFFICIENT`.

Because no dummy gold had been revealed and no scientific target execution had occurred, the contract and dummy fixture were corrected before the decisive handoff rehearsal. The hidden dummy gold commitment therefore changed from the superseded v0.1 value to a new v0.2 commitment. The first commit remains preserved as pre-reveal lineage and is not the authorized handoff snapshot.

No production retriever was run. No scientific benchmark byte or judgment was changed.
