# Benchmark assets

## `eb-challenge-corpus-v1`

[`eb-challenge-corpus-v1/`](eb-challenge-corpus-v1/) is a frozen, fully
fictional technical/regulatory micro-world for two separate experiments:

1. retrieval and aperture evaluation for an Evidence Bundler-like system; and
2. claim-decomposition evaluation using independently generated A0-A4 variants.

It is not production evidence, a regulatory requirement set, a compliance
opinion, a software-qualification record, or a replacement for review. The
package's organizations, products, procedures, dates, thresholds, incidents,
and document histories are synthetic.

The package is deliberately separate from the existing Contract-A/Contract-B
fixtures. It is a benchmark asset, not a change to EB's production retrieval
or output behavior.

### Runtime boundary

An experiment runner may provide EB only the source bytes and permitted source
metadata, the selected case, the named aperture subset, and ordinary runtime
configuration. Keep `gold/` and `decompositions/` outside the runtime mount.
Do not provide gold identifiers, evaluator labels, challenge-family metadata,
adjudication rationales, expected rankings, or expected outputs to the system
under test. The package README contains the full runtime/evaluator boundary.

### Freeze and provenance

- generator: `eb-challenge-corpus-generator` 1.0.0;
- deterministic seed: `271828`;
- canonical corpus tree hash: `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8`;
- validation: 16 check groups passed, 0 failed;
- generation was independent of observed Evidence Bundler retrieval output and
  used no LLM.

Do not edit or regenerate this directory in place. A correction requires a
new corpus version or an explicit deviation record that identifies the
invalidated results.
