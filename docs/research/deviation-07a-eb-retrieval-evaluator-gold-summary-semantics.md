# Deviation 07a — RC1 gold summary semantics preflight failure

## Status

OPEN / diagnostic follow-up required before any synthetic retriever control may be treated as executed.

## When discovered

First GitHub-hosted evaluator run on 2026-08-28, workflow run `33139749679`, after frozen-transform presence checks and before C0-C8 control execution.

## Frozen objects unchanged

- benchmark parent commit: `22b227ec2c34a085efc79267bc007ff78607aeed`
- corpus tree SHA-256: `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8`
- preregistration thresholds/critical gates: unchanged
- canonical corpus: unchanged

## What failed

The preregistration made the following interpretation explicit before scoring:

> derive case-level `gold_source_ids` / `gold_passage_ids` from rows with `decisive: true`, and require every row's case-level summary arrays to equal that decisive-only set.

The first preflight falsified that interpretation.

Examples preserved from the workflow log:

- `case-dev-claim-029-a0` (`F08 DUPLICATE_PARAPHRASE`) has three case-level gold passage identities. Two rows are `decisive_support`; the third gold identity is a non-decisive `material_context` row. The hard negative is excluded from the case-level gold arrays.
- `case-test-claim-018-*` and `case-test-claim-020-*` similarly contain case-level gold identities not present in the evaluator's decisive-only derivation.

The evaluator therefore raised `EvaluatorError` during `validate_gold_interpretation` and produced no assurance artifact. C0-C8 were not run.

## Why this matters

The frozen gold clearly distinguishes at least two concepts:

1. row-level annotation identity/classification, including `decisive` and `relevance_class`;
2. a broader case-level `gold_*_ids` set that can include non-decisive material context.

Treating the case-level arrays as a decisive-only summary would erase that distinction and would make the evaluator misread the benchmark.

## Scientific impact

This is an apparatus-specification error discovered before any synthetic retriever control completed. It does **not** invalidate or change the preregistered later-EB numerical thresholds, critical budget/provenance/aperture gates, or stop conditions. It does invalidate the original gold-summary integrity rule.

No real Evidence Bundler retrieval output has been inspected or executed.

## Corrective procedure

Before editing scoring logic:

1. run a gold-only diagnostic over all 148 cases;
2. compare candidate interpretations of case-level `gold_*_ids` against row-level annotations, including at minimum:
   - decisive-only rows;
   - all non-hard-negative rows;
   - decisive plus `material_context` rows;
3. report every mismatch by family/relevance class;
4. adopt a replacement interpretation only if one is supported consistently by the frozen artifacts;
5. preserve this failed run and record the exact correction before rerunning the evaluator.

If no artifact-supported interpretation resolves the ambiguity, RC1 stops as `INCONCLUSIVE` and Prompt 2 is not authorized.

## Invalidated outputs

Workflow run `33139749679` is a preserved failed preflight only. It establishes that the original gold-summary interpretation was wrong. It establishes no evaluator assurance level beyond revealing this defect.
