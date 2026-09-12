# Evidence Bundler V1 — K=7 Gold-Coverage Completion

Status: **PREREGISTERED — ADJUDICATION NOT YET RUN**

## Purpose

Resolve exactly the `INCONCLUSIVE_GOLD_COVERAGE` blocker from Evidence Bundler PR #63 without rerunning retrieval, changing the frozen V1 implementation, changing K, changing the corpus, or changing the burden gate.

This is a bounded successor evidence-completion experiment. It does not amend PR #60 or PR #63.

## Frozen authorities

- repository: `camerontjs-dot/evidence-bundler`
- live protected `main` at successor start: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- frozen V1 implementation: `c4e3f97ec8f0bd36180954c3aa382418925bf947`
- predecessor K=7 PR: `#63`
- predecessor decisive run: `34649326414`
- predecessor artifact: `10282804289`
- predecessor artifact digest: `sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`
- predecessor result: `INCONCLUSIVE_GOLD_COVERAGE`
- predecessor treatment: `candidate_depth=10`, `retained_k=7`

The predecessor runtime output is immutable. No retrieval execution is authorized in this successor.

## Frozen scientific question

> After completing only the 27 proposition-relative relationship judgments that frozen sparse gold left unresolved, does the already-executed `10/7` treatment pass or fail the exact preregistered known-distractor dominance gate from PR #63?

No new burden threshold may be introduced.

## Exact unresolved set

The successor must contain exactly 27 unresolved proposition-passage relationships derived mechanically from `KNOWN_DISTRACTOR_BURDEN.json` in artifact `10282804289`.

The blind packet must expose only:

- opaque item ID;
- exact proposition text;
- exact retained passage text.

It must not expose:

- case/proposition/evidence/source IDs;
- rank or BM25 score;
- K position;
- admission state;
- previous required/distractor labels;
- lane burden counts;
- expected treatment disposition.

Packet identity is frozen before adjudication:

`BLIND_ADJUDICATION_PACKET.json` SHA-256:
`0b8b3e9021a992bbcc810cce7c3d2293b881d4d9eb7db0d0e9b7e3cb4b211455`

## Adjudication labels

For each item, the adjudicator must choose exactly one:

1. `MATERIAL_OR_POTENTIALLY_USEFUL_FOR_PROPOSITION`
   - the passage directly supports, refutes, qualifies, limits, contextualizes, or otherwise materially bears on the exact proposition;
   - use this conservatively whenever a reasonable audit could treat the passage as useful evidence for the proposition.

2. `KNOWN_NON_REQUIRED_OR_DISTRACTOR`
   - the passage does not materially bear on the exact proposition, including facts about a different entity/condition, mere quotations/examples/hypotheticals, rejected or unverified mentions, or unrelated context.

3. `UNRESOLVED`
   - the relation cannot be classified safely from the proposition and passage alone.

Absence from prior sparse gold is never evidence for label 2.

## Reviewer independence

Two reviewers must adjudicate the exact blind packet independently.

Each reviewer must receive only:

- `BLIND_ADJUDICATION_PACKET.json`
- `ADJUDICATION_RUBRIC.md`

They must not inspect PR #60, PR #63, predecessor receipts, retrieval ranks/scores, gold files, source case names, or the other reviewer's output before freezing their own result.

A reviewer may be a human or model, but the execution context and model identity must be recorded.

The two reviewer outputs must be frozen before comparison.

### Disagreement rule

- Exact agreement on labels resolves an item.
- Any disagreement, or any `UNRESOLVED` label, routes only that item to a third isolated adjudicator under the same blind aperture.
- The third adjudicator may not see the first two labels.
- If the third adjudicator returns `UNRESOLVED`, the successor is `INCONCLUSIVE`.

No majority inference may be made without the third blind judgment.

## Frozen burden gate

After all 27 relations are resolved, restore the opaque IDs to their frozen proposition-relative relationships and combine them with the classifications already authorized by PR #63.

Require all 18 normative lanes to be fully adjudicable.

A lane is `KNOWN_DISTRACTOR_DOMINATED` iff at least 80% of its retained proposition-passage relationships are classified `known_non_required_or_distractor`.

The K=7 burden gate fails iff **more than 50% of the 18 lanes** are `KNOWN_DISTRACTOR_DOMINATED`.

All other PR #63 gates remain inherited and frozen:

- P6 retained at natural rank 7;
- zero required-evidence regression;
- structural invariants pass;
- total retained relationships 96 <= 108.

This successor does not rerun or reinterpret those gates.

## Terminal research dispositions

Use one primary governance disposition:

### `SUPPORTED FOR PROMOTION`

Only if:
- all 27 relations are resolved under the independent-review procedure;
- all 18 lanes become fully adjudicable;
- <= 9 of 18 lanes are `KNOWN_DISTRACTOR_DOMINATED`;
- predecessor artifact identity and all inherited gates verify exactly.

Experiment-specific conclusion:

`K7_NOT_FALSIFIED_AS_SMALLEST_BOUNDED_REMEDY_AFTER_GOLD_COMPLETION`

This authorizes only preparation of a separate minimal V1 promotion candidate. It does not merge, release, tag, or promote by itself.

### `FALSIFIED`

Use if:
- all 27 relations are resolved;
- >= 10 of 18 lanes are `KNOWN_DISTRACTOR_DOMINATED`.

Experiment-specific conclusion:

`FIXED_K_WIDENING_REJECTED_ON_COMPLETED_QUALIFICATION_GOLD`

Do not automatically test K=8 or a selector.

### `INCONCLUSIVE`

Use if:
- any item remains unresolved after the third-review procedure;
- reviewer independence cannot be established;
- predecessor artifact cannot be verified.

### `APPARATUS_INVALID`

Use for packet mismatch, wrong unresolved set, altered proposition/passage bytes, mapping error, leakage of prohibited predecessor labels into the blind packet, or evaluator defect.

## Stop boundary

After one terminal disposition is frozen, stop.

No retrieval rerun, K=8, alternate selector, threshold tuning, BM25 change, CAL semantic execution, production-default mutation, merge, release, tag, or PR #60/#63 amendment is authorized by this experiment.
