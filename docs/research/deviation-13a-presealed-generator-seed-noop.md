# Deviation 13a — Pre-sealed RC2 generator seed was initially inert

**Status:** preserved pre-exposure apparatus correction  
**Real EB exposure:** none  
**Sealed RC2 control exposure before correction:** none

## Observation

During development-only RC2 apparatus calibration, the first committed generator draft accepted and recorded seed `161803` but selected its paraphrase pair deterministically from the case index rather than consuming the seeded RNG.

The resulting development bytes were deterministic, but the recorded seed was not causally operative. Treating that state as a properly seeded generator would have overstated generator provenance.

## Correction

Before generating or controlling the RC2 sealed split, the generator was changed so paraphrase-pair selection is made through the seeded `random.Random(seed)` instance.

No capability family, case count, K budget, acceptance threshold, evaluator rule, weak-control rule, promotion gate, production EB byte, RC1 record, or Contract-A decomposition state changed.

Development generation, validation, weak controls, deterministic replay, metamorphic invariance and mutation sensitivity were rerun after the correction and remained passing.

## Boundary

This correction occurred before the first hosted sealed control gate and before any real Evidence Bundler output on RC2. The earlier generator draft remains in Git history and is not a frozen RC2 identity.

If the first hosted sealed gate later fails, the benchmark must not be redesigned around that result under this version.
