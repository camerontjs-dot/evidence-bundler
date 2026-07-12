# FDA guidance demo inputs

This directory contains the committed input files for the FDA guidance retrieval exercise. The claims and memo are fictional. The source manifest points to a real FDA CGMP quality systems guidance PDF that the runner downloads and verifies at runtime.

The generated scaffold, retrieval bundle, review annotations, final bundle, coverage reports, and measurement files are written under `build/phase-5-fda-guidance-demo/`. They are intentionally not committed.

## Files

| File | Purpose |
|---|---|
| `fictional-compliance-review-note.md` | Fictional memo used as the claim source. The file marks itself as demo content. |
| `claims.yaml` | C-A claims registry derived from the fictional memo. It covers supported, contradicted, conditional, ambiguous, and no-candidate retrieval cases. |
| `source-manifest.yaml` | FDA source URL, metadata, SHA-256 policy, and runtime download instructions. |

## Claim expectations

| Claim ID | Theme | Expected retrieval path |
|---|---|---|
| `clm-qms-coverage` | QMS framework coverage | Supporting candidate expected |
| `clm-validation-exemption` | Process validation exemption | Counter-candidate expected |
| `clm-apr-scope` | Annual product review scope | Conditional candidate expected |
| `clm-capa-risk` | CAPA risk-based approach | Supporting candidate expected |
| `clm-equipment-requalification` | Equipment requalification interval | Needs review |
| `clm-clinical-endpoint` | Clinical endpoint improvement | No strong candidate expected |
| `clm-supplier-qualification` | Supplier qualification and change control | Supporting candidate expected |
| `clm-stability-extension` | Shelf-life extension without long-term data | Counter-candidate expected |

These expectations are hypotheses for exercising retrieval behavior, not support determinations. Mixed and null outcomes are valid demo results.
