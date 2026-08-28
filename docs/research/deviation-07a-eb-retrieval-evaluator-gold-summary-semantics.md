# Deviation 07a — RC1 gold summary semantics preflight failure

## Status

RESOLVED FOR RC1 by frozen-gold diagnostic and explicit corrected-runner layer. Original failed run remains part of the record.

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

No real Evidence Bundler retrieval output was inspected or executed.

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

## Resolution evidence

The gold-only diagnostic was subsequently executed over the complete frozen gold set before C0-C8 were allowed to complete.

Observed diagnostic facts:

- 148/148 cases had internally consistent case-level `gold_source_ids` / `gold_passage_ids` arrays;
- 297 annotation rows were inspected;
- the decisive-only interpretation matched 136/148 cases and therefore remained falsified;
- `decisive == true OR relevance_class == material_context` matched the case-level gold identities in 148/148 cases;
- all 12 `material_context` rows were included in case-level gold;
- all 148 `hard_negative` rows were outside case-level gold;
- no case-level gold identity lacked a corresponding row identity.

Diagnostic artifact SHA-256:

`ea204f5a5eec4cb2f9c54251ae9f2e4d52356e0fa613c2de45bde7918d09f361`

This supports the bounded operational interpretation that row identities and relevance classes own scoring semantics, while case-level arrays are integrity summaries for decisive plus material-context gold. It does **not** establish undocumented generator intent because the frozen receipt still has `generator_source_commit: null`.

## Second apparatus defect discovered before C0-C8 completion

Reviewing the preflight-failing evaluator exposed a related implementation defect: `material_context_recall_at_k` selected material-context rows only from the already filtered set of decisive rows. In this benchmark the 12 material-context rows are non-decisive, so the metric would have been inert.

This was corrected before any C0-C8 run completed by computing material-context recall over accessible rows whose relevance class is material context. The positive oracle was correspondingly made capable of returning every accessible gold target needed by the required retrieval metrics.

This correction changed a required reported metric from broken to operative. It did **not** change any preregistered numerical acceptance threshold, budget/provenance/aperture gate, family floor, or stop condition.

## Corrected apparatus identity

The correction is explicit rather than hidden in rewritten history:

- base evaluator source SHA-256: `dcbcc38b6a1823a440851e6c4cb0b74491ae1c55b1d5cfb1788631fc792c35f4`
- correction-layer source SHA-256: `fbf45ab888f9233bd753754e3490ddd559cbd7e1e60a66307db06ea75126eb98`
- composite evaluator source SHA-256: `48ccebbd81f43ddd951e83c2a2c4b9c1fae7a6a24ec7c3bf3fdea47b1b936f14`
- frozen evaluator implementation/config commit: `acfa232c0a6d1708f249b71606cbdc96755bc4d9`

The corrected decisive control run is GitHub Actions run `33140033264`. Its assurance artifact SHA-256 is:

`69ae61765937f8f67936200495b42e44ec9153a9add17bd39e04c44109cd6fe4`

## Resolution consequence

Because the defect was discovered during preflight before any synthetic retriever control completed, the correction did not follow observation of C0-C8 behavior and did not move their acceptance criteria. The corrected run may therefore be used for RC1 with this deviation attached.
