# Evidence Bundler V1 RC1 V5 Blind Operational Review Rubric

Use only the blind packet and this rubric. Classify every passage relative to the exact proposition and the other passages in the same lane.

`KEEP_DISTINCT`: the passage contributes distinct evidence useful for assessing the proposition.

`DROP_REDUNDANT`: the passage bears materially on the proposition, but another passage in the same lane fully duplicates or subsumes its contribution.

`DROP_DISTRACTOR`: the passage contributes no proposition-relevant evidence to the review record.

`UNRESOLVED`: the authorized proposition, lane context, and passage text are insufficient for safe classification.

Redundancy is lane-relative. Do not infer unstated identity bindings across lanes. This is a fresh isolated review; do not use another set, another review, prior references, prior results, retrieval rank or score, or expected outcomes.

The supervisor supplies the exact packet identity, reviewer identity, phase, and strict JSON output schema. Return one object matching that schema. The `labels` object must contain every packet relation ID exactly once with one of the four labels above. Do not add rationales or extra relation IDs.
