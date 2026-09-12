# Blind Adjudication Rubric — EB V1 K=7 Gold Completion

You are an isolated adjudicator.

You may use only the attached `BLIND_ADJUDICATION_PACKET.json` and this rubric.

Do not inspect the Evidence Bundler repository, PRs, prior experiment results, ranks, scores, gold labels, case IDs, or another adjudicator's output.

For each packet item, classify the relationship between the exact proposition and exact passage.

Allowed labels:

- `MATERIAL_OR_POTENTIALLY_USEFUL_FOR_PROPOSITION`
  - the passage directly supports, refutes, qualifies, limits, contextualizes, or otherwise materially bears on the exact proposition;
  - use this whenever a reasonable audit could consider the passage useful for deciding the proposition.

- `KNOWN_NON_REQUIRED_OR_DISTRACTOR`
  - the passage does not materially bear on the exact proposition;
  - examples include a fact about a different entity or condition, a mere example/hypothetical, a rejected/unverified mention, or unrelated operational context.

- `UNRESOLVED`
  - you cannot safely classify the relation from the two texts alone.

Important rules:

1. Do not assume a passage is a distractor just because it looks secondary.
2. Do not infer hidden case intent.
3. Do not infer that an assertion is true merely because its sentence is declarative.
4. Quoted, hypothetical, rejected, unverified, or no-conclusion mentions are not positive evidence for the quoted proposition.
5. A passage about a sibling entity or different trial/condition is not automatically material to the exact proposition unless it genuinely bears on it.
6. Be conservative: uncertainty belongs in `UNRESOLVED`, not in `KNOWN_NON_REQUIRED_OR_DISTRACTOR`.

Return a single JSON object with:

```json
{
  "schema": "eb-v1-k7-blind-adjudication-result-v1",
  "reviewer": {
    "reviewer_id": "<opaque name>",
    "model_or_human": "<description>",
    "execution_context": "<fresh context description>",
    "packet_sha256": "0b8b3e9021a992bbcc810cce7c3d2293b881d4d9eb7db0d0e9b7e3cb4b211455",
    "independent_of_other_reviewers": true
  },
  "judgments": [
    {
      "item_id": "<item id>",
      "label": "<allowed label>",
      "rationale": "<brief text-only rationale>"
    }
  ]
}
```

Requirements:

- exactly 27 judgments;
- exactly one judgment for every packet item;
- no extra item IDs;
- preserve item IDs exactly;
- do not include rank, score, case identity, or guesses about the expected experiment outcome.
