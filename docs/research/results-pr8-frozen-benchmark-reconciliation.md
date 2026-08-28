# PR #8 frozen benchmark reconciliation assay

## Class

Research Infrastructure / reconciliation evidence only.

## Frozen comparison targets

- exact production base: `c8189c31adbab11729c31430c2070126224a2d42`
- exact frozen benchmark head: `22b227ec2c34a085efc79267bc007ff78607aeed`

## Standalone differential — completed

GitHub Actions run `33142286775` executed `python -m pytest -q` after identical `pip install -e '.[dev]'` procedures on both exact targets.

- base: 199 passed, 5 skipped, 0 failed
- frozen head: 199 passed, 5 skipped, 0 failed

The five skips were identical: one real-reranker smoke test plus four tests that require mounted external repositories. The latter are therefore not evidence that the historical four reported failures disappeared under the environment that originally activated them.

Artifacts:

- base artifact `9674413749`, digest `sha256:33bd8b372254aed909460428a7839cd5e6189661596599296f91097061caa855`
- frozen-head artifact `9674416888`, digest `sha256:a8a243c5d5757285309002388dcc484679c6e7dfdfe016ab413e756b74411f44`

## Extended assay — encoded

The workflow now also mounts the locked production seam:

- Apparatus Contracts `c314e53bd91c0736aa4370a364673b069aceb43e`
- Claim Audit Lab `33a928db97316a3652d57df9cafb8ca240305233`

and runs the same ordinary EB suite against both exact EB targets with project-local virtual environments. It additionally performs frozen-byte receipt, count, diff-boundary, machine-path, and runtime/evaluator-reference checks against the exact benchmark head.

No real EB benchmark retrieval scoring is authorized or executed by this assay.
