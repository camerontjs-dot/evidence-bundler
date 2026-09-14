# Evidence Bundler V1 RC1 V5 Blind Operational Review Rubric

Use only `BLIND_REVIEW_PACKET.json` and this rubric. Judge every passage relative to the exact proposition and other passages in the same lane. Do not use information outside the two authorized files.

Labels:

- `KEEP_DISTINCT`: retain because the passage contributes distinct evidence useful to assessing the proposition, including distinct support, refutation, qualification, limitation, or necessary context.
- `DROP_REDUNDANT`: the passage bears materially on the proposition but its contribution is fully duplicated or subsumed by another passage in the same lane.
- `DROP_DISTRACTOR`: the passage contributes no proposition-relevant evidence to the review record.
- `UNRESOLVED`: the authorized proposition, lane context, and passage text are insufficient for safe classification.

Redundancy is lane-relative. Do not manufacture unstated identity bindings across lanes.

This must be a fresh isolated review. Do not use another set, another reviewer output, prior references, prior results, retrieval rank/score, or expected outcomes.

Frozen packet identity:
- set: `amber`
- canonical SHA-256: `c0255cb02a20f43179bbf6e2ba1117a38dbbd158ecac6c34e22eac926286c731`
- relationships: `54`

The supervisor supplies a strict JSON output schema plus the exact reviewer ID and phase. Return exactly one object matching that schema. The `labels` object must contain each packet relation ID exactly once with one of the four labels above. No rationales or extra relation IDs.
