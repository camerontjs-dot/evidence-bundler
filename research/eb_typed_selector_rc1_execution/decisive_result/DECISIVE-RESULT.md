# EB Typed Selector RC1 - Decisive Fresh Qualification Result

**Disposition:** FALSIFIED

## Frozen role binding

- Rank-only: ARM_A
- Semantic: ARM_B
- Candidate: ARM_C
- Weak: ARM_D

## Observed primary metrics

| Arm | Required lanes | Useful recall@3 | Unsafe | Non-useful burden |
|---|---:|---:|---:|---:|
| ARM_A | 16/27 | 0.536585 | 62 | 68 |
| ARM_B | 21/27 | 0.585366 | 62 | 66 |
| ARM_C | 17/27 | 0.536585 | 58 | 68 |
| ARM_D | 17/27 | 0.536585 | 62 | 68 |

## Research disposition record

{
  "disposition": "FALSIFIED",
  "reasons": [
    "required_lane_coverage_worse_by_at_least_3"
  ]
}

This disposition is bounded to the frozen RC1 selector identity and frozen fresh 30-lane cohort. It is not production authorization and does not establish CAL semantic correctness, source truth, or universal evidence completeness.
