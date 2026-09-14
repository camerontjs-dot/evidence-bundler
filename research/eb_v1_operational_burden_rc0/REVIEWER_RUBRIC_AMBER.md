# Blind Evidence Review Rubric

You are an isolated semantic reviewer.

Use only the attached `BLIND_REVIEW_PACKET.json` and this rubric.

Do not inspect GitHub, CAL Pipeline history, prior experiment results, retrieval ranks or scores, prior admission states, hidden answer keys, another review set, or another reviewer's output.

For every proposition-passage relationship in the packet, classify whether the passage is materially useful for evaluating the exact proposition.

Allowed labels:

- `MATERIAL_FOR_PROPOSITION`
  - the passage directly supports, refutes, qualifies, limits, or otherwise materially bears on the exact proposition;
  - use this if a reasonable evidence reviewer should retain the passage when assessing that proposition.

- `NONMATERIAL_FOR_PROPOSITION`
  - the passage does not materially bear on the exact proposition;
  - examples include facts about a different entity or condition, unrelated operational details, mere examples/hypotheticals, rejected/unverified mentions, or unrelated sibling facts.

- `UNRESOLVED`
  - the relation cannot be classified safely from the proposition and passage alone.

Do not infer support/refutation polarity, truth, or a final claim verdict. The task is only proposition-relative materiality/admission.

## Independence rule

This review must be performed in a fresh isolated context. If you have seen the other review set, another reviewer's judgments, prior gold, or the expected experiment result, stop and return `CONTEXT_CONTAMINATED` instead of judgments.

## Required output

Return only one JSON object:

```json
{
  "schema": "eb-v1-operational-review-result-v1",
  "reviewer": {
    "reviewer_id": "<opaque reviewer id>",
    "model_or_human": "<description>",
    "execution_context": "<fresh isolated context description>",
    "packet_canonical_sha256": "c0255cb02a20f43179bbf6e2ba1117a38dbbd158ecac6c34e22eac926286c731",
    "independent_of_other_reviewers": true,
    "saw_other_review_set": false
  },
  "judgments": [
    {
      "relation_id": "<opaque relation id>",
      "label": "MATERIAL_FOR_PROPOSITION | NONMATERIAL_FOR_PROPOSITION | UNRESOLVED"
    }
  ]
}
```

Requirements:

- exactly `54` judgments;
- exactly one judgment for every relation ID in the packet;
- preserve relation IDs exactly;
- use only the allowed labels;
- no commentary before or after the JSON.
