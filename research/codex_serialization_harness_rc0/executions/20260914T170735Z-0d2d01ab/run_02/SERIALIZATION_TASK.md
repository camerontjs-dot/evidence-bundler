# Synthetic Serialization Task

This is a non-semantic harness qualification task.

Read `SYNTHETIC_INPUT.json`. It contains exactly 96 opaque `relation_id` values and an integer `bucket` for each.

Produce exactly one JSON object conforming to the output schema supplied by the supervisor.

For each `relation_id`, set its value in the `labels` object according to this deterministic mapping:

- bucket `0` -> `KEEP_DISTINCT`
- bucket `1` -> `DROP_REDUNDANT`
- bucket `2` -> `DROP_DISTRACTOR`
- bucket `3` -> `UNRESOLVED`

The supervisor will tell you the exact `reviewer_id` to emit.

Requirements:

- include every relation ID exactly once as a key in `labels`;
- do not invent relation IDs;
- do not omit relation IDs;
- use only the four allowed values;
- emit no commentary outside the JSON object.

This task does not ask for evidence review, semantic judgment, retrieval evaluation, or any CAL / Evidence Bundler conclusion.
