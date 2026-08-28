# Deviation 13b — Post-sealed RC2 freeze workflow omitted its work directory

**Status:** preserved post-sealed durability/infrastructure correction  
**Scientific first sealed control:** unchanged, successful run `33183653897` at apparatus commit `82ec006e888e22c5e5cde600546c05cc6e0b5e33`  
**Real Evidence Bundler exposure:** none

## Observation

After the first hosted RC2 sealed discrimination gate had completed successfully, a separate workflow was added solely to reproduce the already-accepted candidate bytes, verify their exact hashes, and commit that same candidate under `benchmarks/eb-retrieval-assurance-rc2-v1`.

Freeze workflow run `33183864097` failed before regeneration because shell redirection attempted to open `work/freeze-generation.json` before the `work/` directory existed:

`work/freeze-generation.json: No such file or directory`

The preceding exact apparatus-byte verification step passed for the generator, validator, evaluator, control runner, thresholds, result schema, and preregistration. The generator therefore did not execute in the failed freeze run, no candidate bytes were changed, and no real EB output was produced.

## Correction

Create the `work/` directory before redirecting generator output. No benchmark construction rule, seed, case, gold identity, aperture, K budget, evaluator rule, threshold, family floor, weak-control strategy, mutation/metamorphic probe, or first sealed result is changed.

The corrected durability run must still reproduce and verify the exact identities from the authoritative first sealed run:

- frozen apparatus commit: `82ec006e888e22c5e5cde600546c05cc6e0b5e33`;
- candidate tree SHA-256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`;
- first sealed control SHA-256: `d3cdc3ac7c356cc4ec0edc06b6d149bc80082e861b078e8ef94a2df9ad8dfb74`.

Any mismatch must fail the freeze rather than silently create a new RC2 candidate.

## Epistemic effect

None on the pre-exposure discrimination result. This deviation concerns durable repository freezing after the scientific gate, not benchmark/evaluator redesign or EB performance.
