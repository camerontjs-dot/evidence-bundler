# EB Typed Candidate Selector RC0

This directory owns the development apparatus for issue #80.

The target is deliberately narrow: keep the frozen depth-10 candidate world and three-passage budget, then test whether explicit characterization can select a better set than both BM25 top-3 and semantic-only top-3.

## Current phase

**Development only. No production or promotion authority.**

The existing frozen 10/3 integration candidate in PR #79 remains unchanged.

## Files

- `PREREGISTRATION.md` — scientific boundary, development acceptance, freeze and decisive rules.
- `selector.py` — characterization record plus BM25, semantic, typed and ablation selectors.
- `test_selector.py` — deterministic systems and weak-control tests.
- `DEVELOPMENT_FIXTURES.json` — synthetic mechanism controls.
- `DEVELOPMENT_PROFILES.json` — answer-aware profiles for two previously exposed frozen-pool failures.
- `score_frozen_pool.py` — gold-blind scorer/selector runner over the exact predecessor artifact.
- `evaluate_known_cases.py` — answer-bearing retrospective development evaluation, run only after selector output is frozen.

## Important boundary

The development profiles are not ClaimGate/EvidenceGate authority. They exist only to prove that the selector machinery can represent the two known failure mechanisms before a fresh experiment is built.

Fresh decisive case/gold work is context-free required after scientific freeze.
