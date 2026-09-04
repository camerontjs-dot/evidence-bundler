# Counterevidence Aperture Localization Dev RC1 — Terminal Result

Disposition: **LOCALIZED — CROSS_PREFIX_RRF_GEOMETRY WITH OUTPUT_TRUNCATION PRESSURE; NO PRODUCTION REPAIR ESTABLISHED**

This is a terminal research record for issue #47. It does not modify production retrieval defaults and must not be merged merely for housekeeping.

## Exact authority and execution receipts

- predecessor PR: #42
- predecessor final research head: `d02b7c61dc0d2779f35a8fa9eb534d9c301abdd8`
- predecessor decisive implementation: `755a1877cb321b8e9a24e6a770ce7dd40e19433f`
- predecessor decisive run: `33284797206`
- preregistration commit: `ef205de2775ea447eb275dd8cb1c973607684926`
- exact tested diagnostic head: `25d1ac5828564f519547a9bc4fdf2004fa71d510`
- tested tree: `fc44699f86612711122a0d9730c860857a0554c2`
- decisive workflow run: `33868501005`
- decisive job: `101008704048`
- artifact ID: `9934973320`
- artifact ZIP SHA-256: `f93573265c4ed9fe4a77b8b68de1ec5ac05cb6b1d1d5a162c0dfb932cbb31f2a`
- raw retrieval SHA-256, frozen before gold analysis: `b72399b3e2e7c44b4fd3ec179cebc259833b70b7d9b6aaecb6afab4f283ad816`
- analysis SHA-256: `086cc5420bd4986873bf3905f2aefe8d3cafd9458d34d36e11b9df29a15474bb`
- frozen RC2 benchmark tree SHA-256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`
- embedding model: `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- contradiction prefixes: exact predecessor five-prefix set
- RRF k constant: `60`
- contradiction reranking: disabled
- text-role gate: disabled
- split: RC2 dev only

The workflow passed the full predecessor deterministic suite (`224 passed, 5 skipped`), the two new aperture/firewall tests, and Ruff before the decisive diagnostic.

## OBSERVED

The runner executed all five frozen contradiction prefixes for both lexical and semantic retrieval at K, 2K and 4K across 18 dev cases, producing 540 prefix/channel/depth queries. The raw retrieval artifact was written and SHA-256 frozen before the separate analyzer opened dev annotations.

The dev gold contains two decisive R02 counterevidence passages. Both showed the same localization pattern.

### RC2-DEV-R02-001 / RC2-DEV-R02-001-P01

K = 2.

- first lexical discovery: prefix `evidence against`, K, rank 2;
- first semantic discovery: prefix `evidence against`, 2K, rank 3;
- at K: best lexical rank 2, semantic absent, fused rank 3, parent-candidate rank 3, final-K retained: no;
- at 2K: best lexical rank 2, best semantic rank 3, fused rank 3, parent-candidate rank 3, final-K retained: no;
- at 4K: best lexical rank 2, best semantic rank 3, fused rank 3, parent-candidate rank 3, final-K retained: no.

### RC2-DEV-R02-002 / RC2-DEV-R02-002-P01

K = 2. The ranks are identical to R02-001:

- first lexical discovery: prefix `evidence against`, K, rank 2;
- first semantic discovery: prefix `evidence against`, 2K, rank 3;
- fused and parent-candidate rank remain exactly 3 at K, 2K and 4K;
- final-K retention is false at every tested depth.

### Retained-output burden

For both R02 cases, at K, 2K and 4K the two final-K passages are both hard negatives and both overlap the ordinary support channel. The decisive counterevidence passage is not itself a support-channel duplicate.

Widening child retrieval from K to 2K to 4K increases the relevant parent-candidate aperture from 2 to 3 passages, but does not improve the decisive passage beyond fused/parent rank 3. Final output remains K=2.

The posthoc analyzer therefore classified both decisive passages as `CROSS_PREFIX_RRF_GEOMETRY`, with `OUTPUT_TRUNCATION_PRESSURE` as an observed submechanism.

## INFERENCE

The predecessor failure is **not primarily prefix/query suppression**. A decisive R02 passage is already present in lexical contradiction retrieval at rank 2 under the original K, and semantic contradiction retrieval finds it by 2K.

The loss occurs after child retrieval: cross-prefix fusion/parent ordering leaves the decisive passage stably at rank 3 while the final contradiction output admits only two passages. Increasing child depth through 4K does not change that ordering.

Therefore a simple wider child-retrieval aperture is not supported as a production repair. The diagnostic identifies a bounded failure surface in fusion/output geometry, but it does not discriminate among possible repairs such as prefix weighting, fusion changes, diversity-aware selection, counterevidence-specific final-K policy, or a different ranking stage.

## PRESERVED FAILURES / DEVIATIONS

The predecessor PR #42 retains its earlier wrong-import and Ruff failures before its decisive run. They are not rewritten here.

This successor diagnostic had no scientific-apparatus failure before its decisive run. Creating the evidence-record PR caused historical path-matched research workflows on the inherited PR #42 branch lineage to rerun; those unrelated reruns are not counted as evidence for this experiment.

## NONCLAIMS

This result does not establish:

- a production-safe fusion repair;
- that increasing final output K alone is safe or optimal;
- that contradiction prefixes should change;
- that a reranker should be added;
- that the text-role gate should change;
- retrieval completeness outside RC2 dev;
- behavior on sealed data;
- Contract A/B/CAL semantic or authority changes.

## Terminal decision

Issue #47 is sufficiently localized for the pre-build programme: decisive R02 counterevidence exists inside the contradiction child aperture but is displaced to fused/parent rank 3 and then excluded by final K=2. No tested bounded repair has earned production status.

The production build should therefore preserve this limitation rather than guess at a repair. A future repair experiment is a separate research question and should be activated only if production requirements make counterevidence ranking improvement a necessary architectural dependency.
