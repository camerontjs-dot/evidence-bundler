# RC1 Pre-Exposure Deviation — Apparatus Identity Verification

Status: **PRE-EXPOSURE APPARATUS CORRECTION**

## Trigger

The first prescribed RC1 execution started from launch head:

`4f62c8f0e7b75f8869d189430787360f20996203`

It stopped during the runner's apparatus hash preflight before any semantic reviewer was launched.

Reported failure:

`RC1_EXECUTION_FAILED`

`FAILING_STEP=prescribed runner apparatus hash verification`

`ERROR=apparatus hash mismatch: BLIND_REVIEW_PACKET_AMBER.json: da53a4cfc359f2eb17cfa90cef60af057a04bf41a694b3587bd86b18c982cdcb != 0e26242f3ec742e62c4cfba5334f06ef4d5d1da0c4847bf3e4dbb8f050824756`

`LAST_PUSHED_COMMIT=4f62c8f0e7b75f8869d189430787360f20996203`

## Diagnosis

The V1 apparatus manifest treated a transport/serialization-derived raw SHA-256 as repository-byte authority for reused blind packet files.

That assumption was false for a normal Git checkout. The checked-out amber file produced a different filesystem SHA-256 even though GitHub shows that the RC1 amber packet is exactly the same Git blob as the frozen PR #73 source packet:

- amber Git blob: `269f99548e9381945c94553bd34111c500b061d6`
- cobalt Git blob: `c1b5965625c06f134208637091890700e6552978`

The packet semantic identities remain independently frozen as canonical JSON SHA-256:

- amber: `c0255cb02a20f43179bbf6e2ba1117a38dbbd158ecac6c34e22eac926286c731`
- cobalt: `9692386b125c73520fbdbd3c3f61b0c0b020f35b57b089cbd1bb17f662043675`

Therefore the failure was an identity-verification defect, not a packet-content mutation or scientific result.

## Contamination check

No RC1 semantic reviewer was launched before the preflight failure. No reference judgment, test judgment, consolidated reference, or terminal scientific result existed when this correction was made.

RC1 therefore remains pre-exposure and uncontaminated.

## Correction

The original failed runner and V1 manifest are preserved unchanged as audit evidence.

The retry uses a new V2 launch wrapper and V2 apparatus manifest:

1. repository-file identity is verified with Git blob SHA-1 using `git hash-object`;
2. blind-packet semantic identity is independently verified with canonical JSON SHA-256;
3. after those checks pass, the V2 wrapper executes the frozen original runner with only its defective V1 raw-SHA preflight block removed in a temporary copy outside the repository;
4. the rest of the original Stage 1, reference freeze, Stage 2, evaluator, commit, push, and stop-boundary logic is unchanged.

## Scientific invariants unchanged

This correction does **not** change:

- either blind packet's Git blob or canonical semantic content;
- retrieval outputs or retained relationships;
- proposition or passage cohort;
- arm mapping;
- operational labels or rubric semantics;
- reference-consolidation rule;
- Stage 1 / Stage 2 isolation design;
- matched cohort or coverage guard;
- primary metrics;
- directional rule;
- terminal dispositions;
- production defaults;
- merge, release, tag, or promotion state.

The correction is apparatus-only and occurred before semantic exposure.
