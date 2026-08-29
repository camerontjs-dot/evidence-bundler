# Deviation 18a — Preimplementation RC4 seed collision

## Observation
The first RC4 design draft recorded generator seed `271828`.

Live lineage inspection then established that frozen benchmark PR #8 had already used seed `271828`.

## Why this matters
RC4 explicitly requires a new deterministic seed. Reusing a prior benchmark seed would violate the preregistered freshness boundary even though seed reuse alone would not imply byte reuse.

## Timing
The collision was discovered before:
- generator implementation;
- benchmark generation;
- validator/evaluator implementation;
- scientific-object freeze;
- any sealed control execution;
- exact BM25 RC4 execution;
- Hybrid or Semantic-only RC4 exposure.

## Correction
The RC4 seed was changed to repository-unused value `173205` and recorded in the design brief, generator config, and no-exposure design receipt before any generation.

## Scientific consequence
No scientific output or candidate/system output was invalidated because none existed. No threshold, family definition, target configuration, semantic requirement, or success/falsification gate changed.

This record is preserved so the preregistration history remains inspectable rather than silently rewriting the initial draft.
