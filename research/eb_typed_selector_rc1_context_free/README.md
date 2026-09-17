# Evidence Bundler Typed Selector RC1 — Context-Free Qualification Bootstrap

Status: **research infrastructure only / ready to launch prereveal authoring**.

This directory contains the minimum authorized packet for a fresh qualification of the frozen RC0 selector candidate without exposing its implementation or development results to the case/gold/evaluator author before freeze.

## Files

- `BOOTSTRAP-MANIFEST.json` — exact authority, pre-reveal allowlist/denylist, freeze rule, contamination rule, and opaque target identity.
- `PRE-REVEAL-TASK.md` — task to copy into the separate context-free execution surface.
- `FRESH-COHORT-CONTRACT.md` — 30-lane case/profile/candidate-pool/gold construction contract.
- `EVALUATION-CONTRACT.md` — frozen metrics, effect-size gates, burden/safety gates, weak-control discrimination, and terminal dispositions.
- `FREEZE-AND-REVEAL-PROTOCOL.md` — two-lane commit/reveal order: fresh authoring -> input/gold/evaluator freeze -> target reveal -> blind arm-output freeze -> gold reveal -> evaluation.
- `RETURN-HANDOFF-TEMPLATE.md` — compact handoff back to the normal CAL Pipeline project.

## Key isolation property

This bootstrap branch is based directly on protected `main` at `c26fbd4bfc8ba5c2604a784af158594b59fcae37` and does **not** contain the hidden selector implementation or its development record.

The target is represented prereveal only by opaque immutable identities. Exact target source/config becomes authorized only after a valid prereveal freeze receipt exists.

## Launch

In the separate context-free project/thread, provide only `PRE-REVEAL-TASK.md` plus the bootstrap files it names. Do not paste the surrounding CAL Pipeline conversation or PR #82 narrative.

The prereveal lane should stop at `READY_FOR_REVEAL`. It should not execute the target.

## Nonclaims

This packet does not qualify the selector, validate the eventual fresh cohort, authorize promotion, or alter Evidence Bundler production/integration behavior.
