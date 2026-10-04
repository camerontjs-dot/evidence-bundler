# Shared Fresh Successor Cohort Manifest

This cohort was authored only after both sibling scientific systems were frozen:

- authority-preserving fusion RC0 freeze: PR #70, commit `ca5b2591d62418415d13ec46abc97eb396b94b91`;
- CAL-specific learned reranker RC0 freeze: PR #71, commit `7f883ed7f04a73d4f8a7bcfbd5e4dc2c705d8e4b`.

The two sibling branches carry byte-identical case and gold blobs.

## Shape

- roots: `24`
- competing candidates: `96`
- `SELECT` roots: `20`
- intrinsic-ambiguity `ABSTAIN` roots: `4`
- explicitly critical unsafe candidates: `60`
- roots with multiple legitimate safe candidates: `3`

## Exact bytes

Decisive case order is `cases_a.jsonl` followed immediately by `cases_b.jsonl`.

- `cases_a.jsonl` content SHA-256: `42f9da9cdbe9223b3cfd6980690d801f19ffa42763df9ef4efa2635f55e2292d`
- `cases_b.jsonl` content SHA-256: `0ee3118b727ff30ae36401efc705306132b95ed6a74bd0da11c79efe5689ae6e`
- concatenated cases SHA-256: `480c2e876fefd66c3315152cefdb531b739e83e42a1c29a9371b2507a21c0319`
- `gold.jsonl` content SHA-256: `cb6a7805b9fefe5e26d6bb9ff5bf5081a347c32ee8d9902c94bf8c37b4ceaf67`

Git blobs on both sibling branches:

- `cases_a.jsonl`: `f78cb78f211ce9587a12408a4677c2c780b031fe`
- `cases_b.jsonl`: `b65bc4c2a8cbc9d58f4559aa3690ee7b897a6013`
- `gold.jsonl`: `d99225950c78e187482a3e5bd0bf6a7ace3d47ae`

## Boundary

No exact root wording from the PR #67 development or decisive cohorts was intentionally reused. The cohort targets the same semantic failure families with new entities, values, structures and surface forms.

Gold is prohibited from scorer access until decisive raw outputs are frozen and replayed. No scientific code, model, feature, weight, threshold, authority rule or hazard gate may change after this cohort exists.
