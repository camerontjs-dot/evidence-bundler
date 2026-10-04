# Proposition Compiler Authority-Preserving Signal Fusion RC0 — Terminal Record

## Governance disposition

`INCONCLUSIVE`

Experimental classification: `INCONCLUSIVE_NO_MATERIAL_RESOLUTION_GAIN`

This is a research evidence record. It does not authorize merge, production use, Proposition Compiler promotion, Contract change, release, or production Evidence Bundler mutation.

## Exact decisive execution

- decisive head: `1238d3e2a06c6f2207877d1df1cba50a38b6dc03`
- GitHub Actions run: `34679045565`
- job: `103514080737`
- artifact: `10293990746`
- artifact digest: `sha256:7dfa1724bc4da9bddddc28e7e5929d00e913c91ab0780b261affbc64429d796f`
- shared fresh cohort SHA-256: `480c2e876fefd66c3315152cefdb531b739e83e42a1c29a9371b2507a21c0319`
- raw output SHA-256, run A and exact replay: `ed68ee2ee7d1d3aae5a416ea1aa9aecfd7b3a7dc6ca9bda521bf5bb6144b7186`
- score SHA-256: `60fc0c887eeda5327eb7c862f0faf24510b04b55914189acfec36437c2d0e22a`
- terminal SHA-256: `ff25c61895fc42e5b6b02e7ede4f77069bcd0200d300611691a7e0ba954d72af`
- replay: byte-identical
- maintained CI at decisive head: PASS

## Fresh result

Shared fresh surface: 24 roots / 96 competing candidate decompositions, including 4 intrinsic-ambiguity roots.

### A0_AUTHORITY_ONLY

- safe selections: 19
- unsafe selections: 0
- correct abstentions: 4
- false abstentions: 1

### A1_FUSION

- safe selections: 18
- unsafe selections: 0
- correct abstentions: 4
- false abstentions: 2
- decisions changed vs A0: 3
- authority override violations: 0
- safe-resolution gain vs A0: -1

## Interpretation

The bounded authority-preserving architecture succeeded at the safety property tested here: the NLI lane did not override RC1 authority or explicit hazard gates, no unsafe decomposition was selected, and all four intrinsic ambiguities remained abstentions.

It did not establish added decision value. On the fresh cohort the fusion lane resolved one fewer safe root than authority-only. Therefore the preregistered positive gate was not met.

The supported claim is narrow: a generic NLI reranker can be subordinated without necessarily corrupting authority, but this particular fusion rule has no evidence-based reason to be added to the resolver because it reduced safe coverage on the decisive surface.

## Competing explanation / falsifier status

The result is consistent with at least two explanations:

1. generic NLI contains some useful ordering information but the current deterministic fusion rule exposes it at the wrong decision boundary; or
2. once RC1 authority and hazard gates have done their work, generic NLI contributes too little incremental information to justify another resolution layer.

This RC0 does not distinguish those explanations. A successor should not retune this exact fusion against the revealed fresh cohort. Any further test must be a new experiment with a new preregistration and fresh decisive evidence.
