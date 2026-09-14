# Evidence Bundler V1 RC1 — Blind Operational Review Rubric

You are an isolated semantic reviewer for a bounded evidence-review study.

Use only `BLIND_REVIEW_PACKET.json` and this rubric in the current working directory.

The packet's inherited `instructions_ref` field names the RC0 rubric and is non-authoritative in RC1. For RC1, this file is the sole review rubric.

Do not inspect GitHub, parent directories, the internet, CAL Pipeline history, prior experiments, retrieval ranks/scores, prior admission states, hidden answer keys, another set, another reviewer output, or any expected result.

For **every passage in every proposition lane**, classify the passage relative to the exact proposition and the other passages visible in that same lane.

## Labels

### `KEEP_DISTINCT`
Retain the passage because, given the other passages in the same lane, it contributes distinct evidentiary information materially useful for assessing the exact proposition. Distinct support, refutation, qualification, limitation, or necessary contextual evidence can qualify.

### `DROP_REDUNDANT`
The passage bears materially on the proposition, but its evidentiary contribution is fully duplicated or subsumed by another passage in the same lane. Dropping it loses no distinct evidentiary contribution. Do not use this merely because another passage is also relevant.

### `DROP_DISTRACTOR`
The passage does not provide a proposition-relevant evidentiary contribution to the review record. Examples include unrelated entities or conditions, lexical/numeric decoys, operational details that do not bear on the proposition, or hypothetical/rejected/unverified mentions that do not themselves contribute usable evidence.

### `UNRESOLVED`
The authorized proposition, lane context, and passage text are insufficient to classify the relationship safely. Do not infer hidden entity bindings, source semantics, or provenance facts that are not present in the packet.

## Lane-relative rule
Judge each passage in the context of the other passages in the **same lane**. Redundancy is lane-relative. A passage that is distinct in a smaller lane can be redundant when another passage in the same lane fully subsumes it. Do not use information from another lane to manufacture an unstated identity binding.

## Independence rule
This must be a fresh isolated execution. If you have seen the other set, another reviewer’s judgments, a consolidated reference, hidden gold, prior experiment results, or expected outcomes, stop and return `CONTEXT_CONTAMINATED` instead of judgments.

## Frozen packet identity
- expected set ID: `cobalt`
- expected canonical packet SHA-256: `9692386b125c73520fbdbd3c3f61b0c0b020f35b57b089cbd1bb17f662043675`
- expected relationship count: `96`

## Required output
Return only one JSON object, with no markdown fences and no commentary:

```json
{
  "schema": "eb-v1-operational-burden-rc1-review-v1",
  "reviewer": {
    "reviewer_id": "<new opaque reviewer id>",
    "review_phase": "<reference or test, exactly as specified in the launch prompt>",
    "model_or_human": "<description>",
    "execution_context": "<fresh isolated context description>",
    "packet_canonical_sha256": "9692386b125c73520fbdbd3c3f61b0c0b020f35b57b089cbd1bb17f662043675",
    "independent_of_other_reviewers": true,
    "saw_other_set": false,
    "saw_prior_reference": false
  },
  "judgments": [{"relation_id": "<opaque relation id>", "label": "KEEP_DISTINCT | DROP_REDUNDANT | DROP_DISTRACTOR | UNRESOLVED"}]
}
```

Requirements:
- exactly `96` judgments;
- exactly one judgment for every relation ID in the packet;
- preserve relation IDs exactly;
- use only the four allowed labels;
- no rationales or extra judgment fields;
- do not inspect or mention profile identity, K, rank, score, prior labels, or expected outcomes.
