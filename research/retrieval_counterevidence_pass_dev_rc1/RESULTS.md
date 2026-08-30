# Counterevidence Pass Dev RC1 — Results

Status date: 2026-08-29 / 2026-08-30 UTC

Research disposition: **COUNTEREVIDENCE_PASS_NOT_SUPPORTED_AT_K**

Production disposition: **NO PROMOTION**

## OBSERVED — authority and receipts

- preregistration commit: `fffad330276e0579304911dd66fc247a5dd5319e`
- exact decisive implementation: `755a1877cb321b8e9a24e6a770ce7dd40e19433f`
- exact decisive tree: `083118fc1279437f7ef5fc07ed71ef096d4e7099`
- successful decisive workflow run: `33284797206`
- job: `99186007415`
- artifact: `9724085898`
- artifact digest: `sha256:0cfdf376dffa3637cdf70528039c29f79864f13f06188a8b6ed0847ca1eee821`
- raw gold-blind output SHA256: `af3eee12e77e90713024228fe13496761931baa498f31cfbe9a9b93c1dabd2d5`
- benchmark tree SHA256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`

## OBSERVED — preserved pre-execution deviations

Two apparatus failures occurred before any decisive E0/E1/E2 result existed.

1. First run stopped during test collection because the research runner imported
   `DEFAULT_CONTRADICTION_QUERY_PREFIXES` from the wrong module.
   The constant import was corrected without changing any preregistered arm behavior.

2. The next run passed the full suite and dedicated test but stopped at Ruff on one unused
   local variable and one formatting violation in the posthoc analyzer.
   Only analyzer lint was repaired.

Neither failed run generated counterevidence outputs or dev-gold analysis.

## OBSERVED — decisive validation

On the exact decisive head:

- full suite: **222 passed, 5 skipped**;
- dedicated counterevidence boundary test: **1 passed**;
- Ruff: **clean**;
- frozen benchmark identity: **pass**;
- gold-blind retrieval runner check: **pass**;
- E0/E1/E2 raw output generation: **pass**;
- posthoc dev-gold analysis: **pass**.

The raw E0/E1/E2 artifact was written before dev gold was read.

## OBSERVED — arms

### E0 — disabled

- counterevidence recall: **0.0**
- counter-case hit rate: **0.0**
- admissions: 0

This is the expected null counter-channel baseline.

### E1 — contradiction expansion, gate ON

- counterevidence recall: **0.0**
- counter-case hit rate: **0.0**
- total counter-channel admissions: **1**
- hard-negative admissions: **1**
- non-counterevidence-family admissions: **1**
- support-channel duplicate admissions: **1**
- role-gate rejections relative to E2: **39**
- decisive counterevidence rejected by the gate: **0**

The one admitted passage was an R01 hard negative and duplicate of supporting retrieval.

### E2 — contradiction expansion, gate OFF

- counterevidence recall: **0.0**
- counter-case hit rate: **0.0**
- total admissions: **40**
- hard-negative admissions: **29**
- non-counterevidence-family admissions: **36**
- support-channel duplicate admissions: **39**

Turning the gate off does not recover R02. It primarily exposes the broad, noisy candidate stream beneath the role gate.

## OBSERVED — R02 critical falsifier

R02 contains the decisive counterevidence challenge.

- E0: 0 admissions, counterevidence recall 0.0.
- E1: 0 admissions, counterevidence recall 0.0.
- E2: 4 admissions, counterevidence recall 0.0.
- all 4 E2 R02 admissions are hard negatives.

The decisive R02 counterevidence was not present in the final gate-off contradiction candidate output at the preregistered K budget.

This is particularly informative because previous candidate-aperture work established that ordinary semantic retrieval contains all R02 counterevidence by 2K.

## OBSERVED — spillover

With the role gate disabled, contradiction expansion admits counter-channel candidates broadly across families:

- R01: 4 admissions, 3 hard negatives;
- R02: 4 admissions, 4 hard negatives;
- R03: 4 admissions, 2 hard negatives;
- R04: 4 admissions, 2 hard negatives;
- R05: 6 admissions, 2 hard negatives;
- R06: 6 admissions, 6 hard negatives;
- R07: 4 admissions, 4 hard negatives;
- R08: 2 admissions, 0 hard negatives;
- R09: 6 admissions, 6 hard negatives.

The gate therefore performs strong suppression, but the underlying expanded-query ranking is not selectively surfacing the intended counterevidence at this budget.

## INFERENCE — falsifiers

### Counterevidence-pass usefulness

**NOT SUPPORTED at K.**

E1 does not improve R02 counterevidence recall over E0.

### Role-gate failure hypothesis

**FALSIFIED for the observed R02 failure.**

E2, which disables the role gate while preserving query expansion and ranking, still does not recover any decisive R02 counterevidence. No decisive R02 item is rejected by the gate because none reaches the E2 output.

The R02 failure therefore occurs upstream of the text-role gate under this configuration.

### Query-expansion usefulness

**NOT SUPPORTED at the preregistered K child budgets.**

The fixed contradiction prefixes plus K lexical/K semantic retrieval and RRF do not surface R02 counterevidence into the final contradiction candidate list.

### Gate usefulness

The gate clearly suppresses noise: admissions fall from 40 to 1. However, because no decisive counterevidence is surfaced by the underlying candidate ranking, this does not establish useful role-aware counterevidence selection. It is suppression without demonstrated recovery.

### Overbreadth

The gate-off stream is strongly overbroad:

- 29/40 admissions are hard negatives;
- 36/40 admissions occur in families with no decisive counterevidence;
- 39/40 duplicate the supporting semantic-K channel.

This weakens any interpretation that contradiction prefixing alone creates an independent counterevidence aperture.

## COMPETING EXPLANATIONS / UNKNOWNS

The current experiment does not distinguish among:

1. K-per-prefix child budgets are too narrow;
2. fixed contradiction prefixes worsen ranking relative to the unprefixed semantic query;
3. RRF across ten per-prefix rankings dilutes the decisive counterevidence;
4. the lexical side contributes little useful independent signal;
5. the contradiction top-K truncation discards a counterevidence candidate that appears deeper in the fused list.

Because ordinary semantic retrieval already finds R02 counterevidence by 2K, a smaller discriminating test exists before editing prefixes or inventing new semantics.

## NEXT

Run a **counterevidence candidate-aperture diagnostic** on RC2 dev with the gate OFF:

- preserve the exact five contradiction prefixes and RRF k=60;
- hold contradiction output truncation separate from child retrieval depth;
- measure R02 decisive counterevidence presence in the fused contradiction pool at child depths K, 2K, and 4K;
- separately record lexical-only, semantic-only, and fused presence/rank;
- do not modify prefixes, gate semantics, or model identity;
- do not use the sealed split.

This will determine whether the existing contradiction mechanism merely needs a wider candidate aperture or whether the fixed query-expansion/fusion geometry itself is actively worse than ordinary semantic retrieval.

No production change is justified by the current result.
