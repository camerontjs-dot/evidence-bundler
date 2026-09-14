# Evidence Bundler V1 RC1 V5 — Blind Operational Review Rubric

You are an isolated semantic reviewer for a bounded evidence-review study.

Use only `BLIND_REVIEW_PACKET.json` and this rubric in the current working directory.

The packet's inherited `instructions_ref` field is non-authoritative in RC1. This file is the sole semantic review rubric for V5.

Do not inspect GitHub, parent directories, the internet, CAL Pipeline history, prior experiments, retrieval ranks/scores, prior admission states, hidden answer keys, another set, another reviewer output, prior references, or expected outcomes.

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
This must be a fresh isolated execution. If you have seen the other set, another reviewer's judgments, a consolidated reference, hidden gold, prior experiment results, or expected outcomes, do not provide judgments.

## Required output
The supervisor supplies a strict JSON output schema plus the exact packet identity, reviewer ID, and review phase. Return exactly one JSON object conforming to that schema, with no markdown fences and no commentary.

The `labels` object is keyed by the opaque relation IDs from the packet. Include every required relation ID exactly once and use only `KEEP_DISTINCT`, `DROP_REDUNDANT`, `DROP_DISTRACTOR`, or `UNRESOLVED`.

Do not add rationales or extra relation IDs. Do not inspect or mention profile identity, K, rank, score, prior labels, or expected outcomes.
