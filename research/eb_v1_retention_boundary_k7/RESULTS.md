# Evidence Bundler V1 — K=7 Retention-Boundary Result

## Terminal disposition

`INCONCLUSIVE_GOLD_COVERAGE`

## Exact scope

Frozen V1 implementation: `c4e3f97ec8f0bd36180954c3aa382418925bf947`. The only successor treatment was `candidate_depth=10`, `retained_k=7`; `5/3` was reproduced only as the preregistered baseline consistency control. No other K or retrieval/selection mechanism was run.

## Preserved rank-7 defect

`RET-AP-P6` remained at natural rank `7` with raw BM25 score `0.294235083295` and retained state `True`. Its frozen admission state after retention was `accepted`; no admission repair was performed.

## Required-evidence regression

Baseline stage reproduction: `True`. Required-evidence regressions: `0`.

## Review burden

- baseline retained relationships: `54`
- treatment retained relationships: `96`
- hard ceiling: `108`
- hard ceiling pass: `True`
- mean lane delta: `2.3333333333333335`
- median lane delta: `2.0`
- maximum lane delta: `4`
- lanes saturated at seven: `4` / 18
- unique physical retained passages under treatment: `48`

## Known-distractor burden

- fully adjudicable lanes: `0`
- known-distractor-dominated lanes: `0`
- dominated proportion among fully adjudicable lanes: `None`
- dominance gate pass: `False`

Unknown relationships were kept unresolved rather than converted to distractors merely because sparse gold omitted them.

## Structural invariants

All preregistered structural invariants hold: `True`. Raw BM25 score remains diagnostic in the research receipts and was not added to the V1 package contract.

## Frozen evidence record

- workflow run: `34649326414`
- workflow head: `97189e37f1bc14fa00203f7b987989b4799d5f0e`
- artifact: `10282804289`
- artifact digest: `sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`

The workflow artifact contains the complete preregistered output set, including `RETENTION_BOUNDARY_RESULT.json`, both runtime receipts, candidate-ordering comparison, required-evidence stage comparison, review burden, known-distractor burden, structural invariants, `RESULTS.md`, and `SHA256SUMS`. The checksum manifest passed in the decisive run.

## Interpretation boundary

This result is bounded to the frozen nine-case, eighteen-lane qualification set. `10/7` crossed the preserved rank-7 retention boundary and passed the hard retention ceiling, required-evidence regression check, and structural invariants, but the frozen sparse gold could not adjudicate every retained relationship in any lane. The preregistered distractor-dominance gate therefore cannot be evaluated without inventing relevance labels.

This result does not qualify a production V1 default, does not amend PR #60, and does not authorize merge, release, tag, promotion, K=8, selector redesign, or any automatic successor experiment.