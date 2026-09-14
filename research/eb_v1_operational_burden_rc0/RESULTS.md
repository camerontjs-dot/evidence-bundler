# Evidence Bundler V1 — Operational Review Burden RC0 Results

## Terminal validity

`APPARATUS_INVALID`

## Review execution

Source review commit:

`6da1d1489c7451726dab3bc6fdd92f9d1c99b89e`

Observed execution facts:

- four isolated Codex reviews completed;
- four distinct ephemeral reviewer threads are preserved in trace files;
- each final reviewer asserts the correct frozen packet canonical hash;
- each final reviewer asserts independence and no exposure to the other review set;
- amber reviewers agree on all 54 relationships;
- cobalt reviewers agree on all 54 matched relationships;
- cobalt reviewers disagree on one larger-arm-only relationship;
- cobalt reviewer 1 returns two `UNRESOLVED` judgments; reviewer 2 returns one.

The execution hiccup was a parent-validator schema bug. The validator originally searched for top-level `relationships` / `items` while the already-frozen packet shape stores relationships under `lanes[].passages[]`. The repair only adds that flattening path. It does not alter reviewer packets, reviewer prompt, packet hashes, model isolation, labels, or judgments.

## Mechanical preregistered evaluator result

If the frozen hidden answer-key mapping is accepted literally, the evaluator reconstructs:

### Amber / 5/3, matched 54

Each reviewer:

- false-material: 4
- false-nonmaterial: 0
- unresolved: 0
- total error: 4

Pooled:

- false-material: 8
- false-nonmaterial: 0
- unresolved: 0
- inter-reviewer disagreement: 0

### Cobalt / 10/7, matched 54

Each reviewer:

- false-material: 1
- false-nonmaterial: 0
- unresolved: 0
- total error: 1

Pooled:

- false-material: 2
- false-nonmaterial: 0
- unresolved: 0
- inter-reviewer disagreement: 0

Mechanical directional result:

`NO_OBSERVED_DECISION_QUALITY_HARM`

Mechanical disposition:

`SUPPORTED FOR PROMOTION`

**This mechanical disposition is non-authoritative and must not be used for V1 promotion or policy review.**

## Why the mechanical result is invalid

The hidden answer key maps predecessor `known_non_required_or_distractor` to `NONMATERIAL_FOR_PROPOSITION`.

The frozen reviewer rubric defines `MATERIAL_FOR_PROPOSITION` more broadly: any passage that supports, refutes, qualifies, limits, or otherwise materially bears on the exact proposition and should reasonably be retained during review.

The frozen cohort contains direct counterexamples proving those are different constructs.

### Exact duplicate support

For `C07_DUPLICATE:child:1|C07-P1T`, the passage is literally:

`Bench test table: Atlas Valve closing time 0.74 seconds.`

for proposition:

`Atlas Valve bench-test closing time was 0.74 seconds.`

The hidden key says nonmaterial because the predecessor burden gold treated the duplicate as non-required. Both blind-arm reviewers say material, exactly as the review rubric instructs.

### Hard-negative passages

Three `C06_HARD_NEG:child:1` passages explicitly explain that 93-percent mentions are not measured removal-efficiency results. Amber reviewers call them material under the rubric's qualifying/limiting rule. Cobalt reviewers call them nonmaterial when the larger lane also contains the true measured-efficiency passage.

Those three relationships account for the descriptive cross-arm matched-label flips. The evaluator scores the amber labels as errors, but the predecessor burden category was not designed to be semantic-materiality gold.

### Hidden identity

The hidden key treats `C03_POOL_MISS:child:2|C03-P2` as required/material, while the reviewer sees only:

`The competing grey unit ceased operation after fourteen point two hours under the same protocol.`

for the Slate Sensor proposition. The blind aperture does not reveal that the grey unit is Slate Sensor, so both cobalt reviewers return `UNRESOLVED`.

The answer authority therefore uses identity information unavailable to the reviewer.

## Descriptive observations retained

These observations remain usable without claiming gold correctness:

- 51/54 shared relationships receive the same consensus label across the smaller and larger contexts.
- 3/54 shared relationships flip from `MATERIAL` in amber to `NONMATERIAL` in cobalt.
- all three flips are the same `C06_HARD_NEG:child:1` passages.
- within-arm agreement on the matched 54 is 54/54 for both arms.
- the larger arm adds 42 relationships and introduces one reviewer disagreement on those added relationships.

These are context-sensitivity observations, not evidence that one arm has better decision quality.

## Disposition

Per the preregistered apparatus-invalid rule, RC0 terminates as:

`APPARATUS_INVALID`

No V1 promotion authorization follows.

## Next discriminating test

A successor should align the reviewer task and gold authority before comparing arms. The smallest clean options are:

1. define the review task in predecessor terms (`REQUIRED`, `REDUNDANT_NON_REQUIRED`, `DISTRACTOR`, `UNRESOLVED`) and expose whatever identity/provenance is necessary to make those labels decidable; or
2. keep the semantic materiality rubric, but independently adjudicate materiality gold under that exact rubric before arm comparison.

No retrieval rerun is needed for either option.

## Stop boundary

Do not automatically test K=8, another fixed K, a selector/reranker, threshold tuning, semantic retrieval, query rewriting, production defaults, merge, tag, release, or promotion.
