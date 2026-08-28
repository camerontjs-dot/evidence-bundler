# EB Retrieval Evaluator Assurance RC1 — Results

## Decision

Determine whether the retrieval/aperture evaluator is sufficiently validated for a later, separate Evidence Bundler measurement on the frozen `eb-challenge-corpus-v1` benchmark.

**Disposition:** `SUPPORTED FOR PROMOTION` for this bounded evaluator use.

**Evaluator assurance:** `E3 — Adversarially challenged`.

**Prompt 2:** AUTHORIZED, provided it uses the exact frozen benchmark and evaluator identity recorded below and remains a separate EB-performance experiment.

No real Evidence Bundler retrieval output was inspected or executed in RC1.

## Frozen identities

Benchmark:

- PR #8 frozen commit: `22b227ec2c34a085efc79267bc007ff78607aeed`
- corpus tree SHA-256: `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8`

Evaluator implementation/configuration used for the decisive run:

- frozen evaluator implementation/config commit: `acfa232c0a6d1708f249b71606cbdc96755bc4d9`
- base evaluator source SHA-256: `dcbcc38b6a1823a440851e6c4cb0b74491ae1c55b1d5cfb1788631fc792c35f4`
- explicit correction-layer source SHA-256: `fbf45ab888f9233bd753754e3490ddd559cbd7e1e60a66307db06ea75126eb98`
- composite evaluator source SHA-256: `48ccebbd81f43ddd951e83c2a2c4b9c1fae7a6a24ec7c3bf3fdea47b1b936f14`
- generic retrieval-result schema SHA-256: `2cfb4dc6cd746f55b690300aafe9a0d19678fcb09bd8e01b0dd5d15043fbf40b`
- preregistration SHA-256: `90f47f06a74516ce8f2e4fb6388a295c82e97855fc157b6d8473d5d53cb6f4ce`
- threshold configuration SHA-256: `066e99719168a366f03476fa779398f790cce7653bc3928470486d6bbb805461`

Decisive execution:

- GitHub Actions run: `33140033264`
- workflow artifact: `9673561889`
- workflow artifact ZIP digest: `sha256:30ff7d30d7286ca5f3a0664fae8c6d619c70fe06c8bb0a266013414cfe635e6f`
- assurance JSON SHA-256: `69ae61765937f8f67936200495b42e44ec9153a9add17bd39e04c44109cd6fe4`
- gold-semantics diagnostic SHA-256: `ea204f5a5eec4cb2f9c54251ae9f2e4d52356e0fa613c2de45bde7918d09f361`
- Python: `3.11.16`
- runner platform: `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39`

A later documentation-only commit does not change the frozen evaluator identity above unless evaluator/schema/preregistration/threshold bytes change.

## Preregistered later-EB gates

The numerical thresholds and critical gates were committed before any real EB output was inspected and were not changed after synthetic-control behavior was observed.

Critical failures remain non-compensable: schema error, retrieval-budget violation, corrupted provenance, false comprehensive/full-corpus aperture claim, nondeterminism, or incomplete F01-F12 reporting cannot be washed out by high recall.

Coverage gates remain:

- case-level accessible decisive hit@K >= 0.95 overall;
- decisive annotation recall@K >= 0.90 overall;
- decisive counterevidence/refutation recall >= 0.90 where applicable;
- decisive qualifier/exception recall >= 0.90 where applicable;
- complete joint-group coverage >= 0.90 where applicable;
- each applicable answerable family: case hit@K >= 0.75 and decisive annotation recall@K >= 0.70.

`K` is each case's configured `runtime_config.maximum_passages`.

## Preserved apparatus deviation

The first GitHub-hosted preflight, run `33139749679`, failed before C0-C8 could execute because the preregistered decisive-only interpretation of case-level `gold_*_ids` was wrong.

A complete gold-only diagnostic then established the following artifact facts over all 148 cases / 297 rows:

- decisive-only row identities matched case-level gold arrays in 136/148 cases;
- decisive plus `material_context` row identities matched in 148/148 cases;
- all 12 material-context rows are included in case-level gold;
- all 148 hard-negative rows are outside case-level gold;
- no case-level gold identity lacked a corresponding row identity;
- case-level gold arrays were internally consistent within every case.

The diagnostic also exposed that the initial material-context recall implementation was inert because it filtered material context through decisive rows. That metric was corrected before any C0-C8 control completed. No acceptance threshold or critical gate changed.

The complete deviation history is preserved in `deviation-07a-eb-retrieval-evaluator-gold-summary-semantics.md`.

## Synthetic control results

| Control | Qualified? | Key observation |
|---|---:|---|
| C0 Null | No | case hit@K 0.000; decisive recall 0.000 |
| C1 Gold oracle | Yes | case hit, decisive recall, counterevidence, qualifier/exception, material context, joint groups all 1.000 |
| C2 First-N/source-order | No | case hit 0.0833; decisive recall 0.0684; joint coverage 0.000 |
| C3 Lexical-only weak | No | case hit 1.000 and decisive recall 0.9658, but complete joint-group coverage only 0.750, below preregistered 0.900 gate |
| C4 Return-everything gamer | No | unbounded decisive recall 1.000, but all 148 cases violated their retrieval budget; bounded decisive recall 0.0684 |
| C5 Provenance-corrupt | No | 129 invalid-provenance hits; valid decisive recall 0.000 despite copied/correct text |
| C6 Aperture liar | No | retrieval coverage 1.000, but 94 false-completeness claims on bounded subsets triggered the critical aperture gate |
| C7 Honest bounded | Yes | same bounded retrieval target behavior without false-completeness failure; full coverage controls remained 1.000 |
| C8 Hard-negative-biased | No | case hit 0.0833; decisive recall 0.0684; materially below oracle |

### Important C3 warning

C3 is the most consequential surprise in RC1. A deliberately weak token-overlap heuristic retrieved enough gold to achieve:

- case hit@K: 1.000;
- decisive annotation recall@K: 0.9658;
- counterevidence recall: 1.000;
- qualifier/exception recall: 0.9481;
- material-context recall: 1.000.

It did **not** obtain a qualified pass because F10/multi-passage behavior pulled complete joint-group coverage to 0.750.

This is evidence that much of the frozen benchmark is lexically recoverable. The evaluator correctly refuses the weak retriever an unqualified pass, but future EB results near the ordinary recall ceiling should not be advertised as strong semantic-retrieval evidence merely because the number is high. Multi-passage composition, aperture, provenance, hard-negative behavior and family diagnostics remain decision-relevant.

## Metamorphic controls

All required RC1 metamorphic checks passed:

- source-enumeration permutation left evaluator judgment invariant;
- harmless metadata ordering left judgment invariant;
- exact duplicate insertion did not create extra decisive-evidence credit;
- paraphrased duplicate insertion did not create independent gold credit;
- paragraph-order transformed anchors were correctly mapped through the supplied semantic-anchor map;
- stale pre-transform offsets were rejected rather than credited.

The paragraph-transform sensitivity check used `case-dev-claim-001-a0`, `src-rimebridge-current`, `pas-4dc47025d4dd-002`.

## Mutation sensitivity

An isolated copy changed the required gold passage identity for `case-dev-claim-001-a0` from:

`pas-4dc47025d4dd-002`

to:

`pas-4dc47025d4dd-002-MUTATED`.

The canonical evaluator summary changed as required:

- baseline summary SHA-256: `f91ed2a726679e5cefb0fda1859a8fa45ab9b2283cf1ebb5a701313608aff0a1`
- mutated summary SHA-256: `816de4a3e2f1f58f4d7dd5467339a583283ab48faf17c406e21dfe6ec281e8b9`

Canonical benchmark bytes were not mutated.

## Determinism

Two deterministic control/evaluation passes produced canonical-identical output.

- run 1 canonical SHA-256: `b5c85b5ed14ca2ec787346a356d384b1c95e01552e416e614b76ce81a506240a`
- run 2 canonical SHA-256: `b5c85b5ed14ca2ec787346a356d384b1c95e01552e416e614b76ce81a506240a`

## Observed evidence

1. Frozen corpus identity matched the required receipt.
2. The initial gold interpretation failed before synthetic controls and is preserved as a deviation.
3. The corrected gold interpretation is supported by 148/148 frozen cases as an artifact-level consistency rule.
4. C0, C2, C3, C4, C5, C6 and C8 did not qualify; C1 and C7 behaved as intended.
5. C4 cannot game qualification with unbounded recall because budget is a critical gate.
6. C5 copied/correct text with corrupted identity receives no valid gold credit.
7. C6 cannot game qualification by claiming comprehensive coverage over bounded search.
8. C7 is not penalized merely for explicitly representing completeness as unknown.
9. Required metamorphic and mutation-sensitivity checks passed.
10. Deterministic result output reproduced canonically.
11. No real EB retrieval output was inspected or run.

## Inference

The evaluator is sufficiently challenged for the bounded next decision: measuring EB retrieval/aperture behavior on this exact frozen benchmark under the preregistered gates.

The evidence supports E3 because RC1 contains basic controls, sensitivity/invariance checks, adversarial/gaming controls, provenance corruption, aperture deception, budget gaming and hard-negative bias.

The evidence does not support E4 because there is no independently implemented or independently reviewed evaluator cross-check. It does not support E5 because RC1 alone cannot validate the evaluator for every future decision or corpus.

## Evaluator weaknesses / unknowns

1. `generator_source_commit` remains null. The frozen bytes are strongly identified, but independent regeneration from committed generator source remains unproven.
2. Gold is synthetic-adjudicator output, not independently established regulatory or real-world truth.
3. C3's near-ceiling lexical performance indicates substantial lexical accessibility in the benchmark. This weakens any interpretation that high aggregate recall alone demonstrates sophisticated retrieval.
4. RC1 has no independent evaluator implementation/cross-check, so E4 is not justified.
5. Preregistered numerical thresholds are engineering tolerances chosen before EB inspection, not empirically calibrated safety/error limits.
6. The evaluator measures behavior within this frozen evidence world. It does not prove corpus completeness, source legitimacy, claim decomposition correctness or external representativeness.

## Falsified evaluator alternatives

The experiment rejects the following evaluator designs/interpretations for this decision:

- decisive-only interpretation of case-level `gold_*_ids`;
- recall-only qualification that permits return-everything retrieval;
- text-similarity rescue of corrupted provenance;
- aperture logic that permits a bounded search to claim comprehensive coverage without failure;
- scoring that penalizes an honest bounded search merely because completeness is explicitly unknown;
- duplicate-counting logic that turns repeated/paraphrased evidence into independent coverage credit;
- paragraph-transform scoring that relies on stale canonical offsets instead of supplied anchor mapping.

## Final assurance decision

**Evaluator assurance level: E3 — Adversarially challenged, for the specific decision of evaluating retrieval/aperture behavior on frozen `eb-challenge-corpus-v1`.**

**Prompt 2 is authorized.** It must pin the exact frozen benchmark and evaluator identities in this record, preserve the C3 lexical-baseline warning in interpretation, and must not silently change the preregistered acceptance gates after seeing EB output.

## What this does not establish

RC1 does not establish:

- real Evidence Bundler retrieval performance;
- production readiness of an EB retrieval change;
- corpus completeness or real-world representativeness;
- source authority/legitimacy;
- CAL semantic-evaluator correctness;
- claim-decomposition correctness;
- independent benchmark regeneration from committed generator source;
- E4/E5 evaluator assurance.
