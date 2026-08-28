# Deviation 06a — Pre-sealed PyYAML dependency omission

**Experiment:** EB Retrieval + Aperture Assurance RC1 decisive frozen benchmark run  
**PR:** #6  
**Status:** recorded pre-decisive plumbing correction

## Observed evidence

GitHub Actions run `33174045876` at research head
`3e9f6208126aebbc6fd8576316cca4582a3a9de8` completed the exact SUT/evaluator
checkouts, immutable-identity verification, benchmark byte verification, and clean runtime
mount. It then failed in the pre-sealed production-chunker alignment diagnostic with:

```text
ModuleNotFoundError: No module named 'yaml'
```

The diagnostic imports the c818 production chunker. That import traverses
`evidence_bundler.contracts.yaml_io`, which imports PyYAML. The research workflow had
installed Pydantic and rank-bm25 but omitted PyYAML even though c818 declares
`PyYAML>=6.0,<7` as a project dependency.

Development retrieval, sealed-test retrieval, replay, source-order falsifier, and evaluator
scoring were all skipped. No real sealed EB retrieval output existed in this run.

## Correction

Add only `PyYAML>=6.0,<7` to the research workflow's runtime dependency installation.

## Frozen elements unchanged

The correction does not change:

- SUT commit `c8189c31adbab11729c31430c2070126224a2d42`;
- benchmark commit or bytes;
- evaluator commit or bytes;
- evaluator thresholds;
- query construction;
- retrieval method;
- per-case budgets;
- passage-unit adapter;
- aperture subsets;
- runtime contamination boundary;
- search-scope/completeness serialization.

## Scientific impact

No decisive run is invalidated because the failure occurred before development retrieval and
before the first sealed-test output step. Run `33174045876` remains preserved as a failed
pre-sealed apparatus attempt. The first successful execution of the sealed-test output step
will remain the first decisive result and may not be replaced merely because its score is
inconvenient.

## Receipts

- Failed workflow run: `33174045876`
- Failed-run artifact ID: `9686808604`
- Failed-run artifact ZIP SHA-256 reported by upload step:
  `620c57b5d8c93d4da33a53763ac9d963b2966a6d430e0a129db972314d38828f`
- Identity receipt SHA-256:
  `4f05a4788600556f52fb64136cac0f1d0858c032cfaa67284f3f406fe544f8c1`
- Benchmark byte-check log SHA-256:
  `145e68e1c24150a604a51c0d73d1768081710282664318d5dd0a969a0b1248cb`
- Clean runtime-mount manifest SHA-256:
  `064ad086048d1b15811218b8bc78493a437e64020c0dc658c1ea6aebae1da062`
