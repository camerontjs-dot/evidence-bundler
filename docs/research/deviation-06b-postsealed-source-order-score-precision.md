# Deviation 06b — Post-sealed source-order comparator precision diagnosis

**Experiment:** EB Retrieval + Aperture Assurance RC1 decisive frozen benchmark run  
**PR:** #6  
**Status:** preserved diagnostic; no apparatus correction and no rerun

## Trigger

The first decisive sealed run `33174250908` preserved a source-order permutation control.
The research wrapper reported:

- `changed_case_count = 99 / 111`;
- `invariant = false`.

The preregistered falsifier concerns source order changing **substantive retrieval output**.
Before attributing that flag to EB retrieval architecture, the preserved canonical and reversed
raw outputs were compared field by field without changing either artifact or the frozen
evaluator.

## Observed diagnosis

Across all 111 sealed cases:

- passage/source identity sequence changed in `0 / 111` cases;
- rank sequence changed in `0 / 111` cases;
- returned text changed in `0 / 111` cases;
- floating score bytes changed in `99 / 111` cases;
- maximum absolute score delta was `1.4210854715202004e-14`;
- maximum relative score delta was `4.132847672500785e-16`.

The wrapper's equality check included exact floating scores, so it treated numerically tiny
score-rounding differences as substantive behavioral changes.

## Scientific interpretation

This does **not** satisfy the preregistered source-order falsifier because retrieved identities,
ranks, and text are invariant. It does show that exact score-bit invariance was not achieved
under source enumeration reversal.

The original wrapper output remains preserved unchanged. No evaluator, threshold, SUT,
benchmark, retrieval configuration, raw result, or workflow is modified after observing the
sealed output. No corrected decisive run is created.

## Reconsideration trigger

If a future consumer treats BM25 score bits themselves as a contractual or decision-relevant
output, score-level numerical stability needs a separately preregistered tolerance/identity
policy. This experiment does not establish exact floating-score-byte invariance.
