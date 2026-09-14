# EB V1 Operational Review Burden RC0 — Post-review construct mismatch

Status: **APPARATUS-INVALIDATING DEVIATION**

## What was observed

The four context-free Codex reviews completed and passed the intended packet-identity / independence assertions. The salvage commit is `6da1d1489c7451726dab3bc6fdd92f9d1c99b89e`.

During result verification, the supervisor compared the frozen reviewer rubric to the frozen hidden answer-key construction rule and found that they do not encode the same decision construct.

The answer key mechanically maps:

- predecessor `required` -> `MATERIAL_FOR_PROPOSITION`
- predecessor `known_non_required_or_distractor` -> `NONMATERIAL_FOR_PROPOSITION`

The reviewer rubric instead defines `MATERIAL_FOR_PROPOSITION` as any passage that directly supports, refutes, qualifies, limits, or otherwise materially bears on the exact proposition, including anything a reasonable evidence reviewer should retain while assessing the proposition.

Those categories are not equivalent on the frozen cohort.

## Decisive counterexamples

### Duplicate exact support

Semantic relationship:

`C07_DUPLICATE:child:1|C07-P1T`

Proposition:

`Atlas Valve bench-test closing time was 0.74 seconds.`

Passage:

`Bench test table: Atlas Valve closing time 0.74 seconds.`

The predecessor burden gold classifies this relationship as non-required/distractor, so RC0's hidden answer key labels it `NONMATERIAL_FOR_PROPOSITION`.

Both blind review arms' reviewers label the passage `MATERIAL_FOR_PROPOSITION`, which is directly consistent with the frozen reviewer rubric because the passage exactly supports the proposition.

Therefore a reviewer can follow the rubric correctly and still be scored as a false-material error.

### Hard-negative qualification passages

Three shared relationships in `C06_HARD_NEG:child:1` are classified non-required/distractor by the predecessor gold but explicitly tell the reader that a 93-percent mention is a protocol label, fixture mark, or humidity value rather than measured removal efficiency.

The frozen reviewer rubric says qualifying / limiting material should be retained as `MATERIAL_FOR_PROPOSITION`. Both amber reviewers classified all three as material. Both cobalt reviewers classified all three as nonmaterial when the larger context also exposed the true measured-efficiency passage.

The preregistered evaluator therefore treats these context-sensitive semantic judgments as gold errors even though the gold category was not built for the rubric's materiality construct.

### Hidden identity / aperture mismatch

Semantic relationship:

`C03_POOL_MISS:child:2|C03-P2`

Proposition:

`Slate Sensor endurance runtime was 14.2 hours.`

Passage:

`The competing grey unit ceased operation after fourteen point two hours under the same protocol.`

The hidden predecessor gold treats this as required/material, but the blind packet does not expose the hidden identity binding that makes `the competing grey unit` Slate Sensor. Both cobalt reviewers therefore returned `UNRESOLVED`, which is permitted by the rubric and rational from the authorized aperture.

This shows that the hidden answer authority can rely on information the blind reviewer is not allowed to see.

## Salvage-runner deviation

The original frozen runner validator looked for top-level `relationships` / `items`, while the already-frozen blind packets store relations under `lanes[].passages[]`.

During execution the runner was repaired to flatten `lanes[].passages[]` for structural validation. The four-line change does not alter packet bytes, reviewer prompt, model isolation, allowed labels, packet hashes, or review judgments. Final traces show each reviewer reading only `BLIND_REVIEW_PACKET.json` and `REVIEWER_RUBRIC.md` in a distinct ephemeral Codex thread.

This runner repair is preserved rather than erased. It is not the scientific invalidator identified above.

## Consequence

The preregistered evaluator's mechanical comparison can be reconstructed, but its `false_material` / `false_nonmaterial` counts do not have the claimed semantic meaning.

Accordingly RC0 must not use the mechanical `SUPPORTED FOR PROMOTION` result as evidence that the larger arm preserves or improves admission decision quality.

Terminal experiment validity is `APPARATUS_INVALID`.
