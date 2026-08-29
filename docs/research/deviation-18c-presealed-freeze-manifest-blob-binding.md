# RC4 deviation 18c: pre-sealed freeze-manifest Git-blob binding correction

## Observation

The first hosted RC4 apparatus workflow run, GitHub Actions run `33226673867`, stopped in the frozen-source preflight before benchmark regeneration or any sealed control execution.

The failing check compared the Git blob identity recorded for the original preregistered `control_plan.json` against the live file:

- manifest value: `43478f4b0c92e915dc14c65257c9241b4c9a5f53`
- actual Git blob: `43478f173c0bf08bd9636ffe78b6b0da31d109ae`

Direct comparison of the file at its original preregistration commit `50aa5443ba60d80e436d1a920914ef2f4f090228` and the failed-run head `768d38f7d0e34b823e51b7840095e723b9a65eb6` shows identical content and the same actual Git blob `43478f173c0bf08bd9636ffe78b6b0da31d109ae`.

## Exposure state

The failed workflow stopped before:

- benchmark regeneration/validation;
- first sealed oracle control;
- evaluator assurance;
- exact production BM25;
- sealed weak/gaming controls;
- metamorphic sealed assurance.

Hybrid and Semantic-only remained unexposed.

Therefore no promotion-critical sealed scientific result existed when this discrepancy was diagnosed.

## Classification

This is an infrastructure/freeze-receipt binding defect, not a scientific-object mutation.

The original `control_plan.json` bytes did not change. The separately added pre-exposure controls remain recorded in `additional_control_plan.json` and deviation 18b. No target identity, generator seed, benchmark bytes, evaluator bytes, threshold, original control plan, metamorphic direction, success criterion, or falsifier is changed by this correction.

## Correction

Correct only the erroneous `preregistration_git_blobs` value in `apparatus_freeze_manifest.json` to the actual unchanged preregistered Git blob:

`43478f173c0bf08bd9636ffe78b6b0da31d109ae`

Then rerun the unchanged frozen apparatus workflow from the corrected manifest.

The failed first hosted run remains preserved as evidence and is not reclassified as a scientific apparatus result.
