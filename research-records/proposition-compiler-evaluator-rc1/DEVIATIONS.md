# RC1 Deviations

## Hosted-test formatting correction after local decisive raw output

After the frozen target had already produced local decisive raw output, the hosted-CI preparation identified that the compact research test file would likely violate maintained Ruff style rules. The test file was reformatted before hosted execution.

- original test SHA-256 recorded in `FREEZE_MANIFEST.json`: `a54dd8a708cd0b85d198cdd740099f8ec30710adc7866b52f7c0071b3630eae5`
- reformatted test SHA-256: `60134dbbad79496fa9f1f663ff52c2401dd98aeef5be19024b0a6f530fc9eebf`
- Git commit carrying the formatting-only test change: `69f5a9962d4bcacc8576a18874c0003976737dc5`

No change was made to:
- frozen `evaluator.py`;
- frozen `controls.py`;
- fresh cases;
- fresh gold;
- scorer;
- raw local target/control output already produced.

The test assertions and scientific meaning were unchanged. This is recorded as a harness deviation rather than silently rewriting the freeze record.

## Fresh adjudication independence
Independent human adjudicators were unavailable in the current execution surface. Fresh gold is internally adjudicated and labeled as such in `FRESH_ADJUDICATION.md` and the gold rows. This limits the strength of any positive semantic claim but does not create or erase a direct unsafe-acceptance falsifier.
