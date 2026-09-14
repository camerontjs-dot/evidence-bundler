# RC1 Pre-Exposure Deviation — Cobalt Canonical Identity

Status: **PRE-EXPOSURE APPARATUS CORRECTION**

## Trigger

The V2 retry started from:

`40142ae3897fe046475d9ee88d49e8a97285643a`

It stopped during packet canonical identity verification before any semantic reviewer was launched.

Observed failure:

`RC1_EXECUTION_FAILED`

`FAILING_STEP=V2 packet canonical identity verification`

`ERROR=packet canonical hash mismatch: BLIND_REVIEW_PACKET_COBALT.json: 9cc015f234e20eab7bf3f68569732c60db55edebe1053c8d32b10120537d3621 != 9692386b125c73520fbdbd3c3f61b0c0b020f35b57b089cbd1bb17f662043675`

`LAST_PUSHED_COMMIT=40142ae3897fe046475d9ee88d49e8a97285643a`

## Observed evidence

- Git blob verification passed before the canonical check.
- The frozen cobalt packet Git blob is `c1b5965625c06f134208637091890700e6552978`.
- The same canonicalization rule used by `review_common.py` is `json.dumps(..., sort_keys=True, separators=(',', ':'), ensure_ascii=False)` followed by UTF-8 SHA-256.
- Applied to the checked-out cobalt packet, that rule yields `9cc015f234e20eab7bf3f68569732c60db55edebe1053c8d32b10120537d3621`.
- Historical RC0/RC1 metadata and the frozen cobalt rubric carried `9692386b125c73520fbdbd3c3f61b0c0b020f35b57b089cbd1bb17f662043675`.
- The amber packet passed the same V2 canonical identity check.

## Interpretation

The cobalt expected canonical hash in the inherited metadata is stale relative to the committed packet object. The exact historical point at which the stale value diverged from the committed cobalt packet has not been established and is therefore left unknown.

This is not evidence of a semantic-review result. It is an apparatus identity defect discovered before semantic exposure.

## Latent failure caught

`OPERATIONAL_REVIEW_RUBRIC_COBALT.md` also hardcodes the stale `969238...` value, while `review_common.py` recomputes canonical identity from the packet actually presented. Without this preflight stop, cobalt reviewer outputs would later fail validation even if their judgments were otherwise well formed.

## Contamination check

No RC1 semantic reviewer was launched in either failed attempt. No Stage 1 reference judgment, Stage 2 test judgment, consolidated reference, or terminal RC1 scientific result exists.

RC1 therefore remains pre-exposure.

## V3 correction boundary

V3 may correct only packet-identity apparatus:

1. keep the exact amber and cobalt Git blobs unchanged;
2. treat Git blob identity as repository-byte authority;
3. recompute packet canonical SHA-256 using the same function used by `review_common.py`;
4. use `9cc015f234e20eab7bf3f68569732c60db55edebe1053c8d32b10120537d3621` as the cobalt canonical identity;
5. create the cobalt reviewer rubric only as a temporary deterministic copy of the frozen source rubric with the stale hash literal replaced by the recomputed hash;
6. require the stale literal to occur exactly twice before replacement and zero times afterward;
7. preserve the scientific task, packets, labels, reference rule, test rule, evaluator, thresholds, arm mapping and stop boundary unchanged.

The original V1 and V2 launch records remain preserved in Git history and this deviation record.
