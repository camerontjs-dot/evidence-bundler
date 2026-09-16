# Typed Candidate Selection V0 — Deferred Research Note

## Status

Research infrastructure only. This note preserves a later Evidence Bundler experiment and does not modify runtime behavior, the frozen 10/3 integration candidate, Contract B projection, admission semantics, or CAL behavior.

Tracking issue: #80.

## Context

Current V1 evidence supports a depth-10 candidate aperture for integration use, but fixed retention at K=3 can miss deeper required evidence. Fixed K=7 increased burden and was not qualified as a production default. The tested generic set-wise selector did not establish a better selector on the frozen pool.

A later hypothesis is that explicit pre-retrieval ClaimGate / EvidenceGate characterization may provide useful type, provenance, temporal, jurisdictional, and evidence-form signals for selecting among the already-retrieved depth-10 candidates.

## First experiment

Hold first-stage retrieval fixed:

```text
same claim
+ same corpus / evidence world
+ same query
+ same BM25 implementation
+ same depth-10 candidate pool
```

Compare:

```text
CONTROL
frozen EB ranking -> retain top 3

EXPERIMENTAL
depth-10 pool
-> candidate characterization
-> preregistered typed selector
-> retain 3
```

The candidate characterization / selector must not use CAL output, gold labels, downstream verdicts, SUPPORTS / REFUTES judgments, or answer-bearing evaluator state.

Candidate-side observations may include evidence form, relevant entities/events/measures, temporal coverage, jurisdiction, source/provenance role, and compatibility with frozen Claim Profile / Evidence World Profile inputs.

## Primary question

Can typed selection recover materially useful deeper candidates while retaining only three passages, without increasing distractor burden, reviewer burden, or unsafe evidence promotion?

## Measurements

At minimum:

- required-evidence retained@3;
- claim / lane coverage;
- distractor burden;
- reviewer burden or disagreement where available;
- deterministic replay;
- unknown / abstention behavior;
- preservation of complete native candidate history;
- comparison against frozen EB 10/3 on the exact same candidate pools.

## Later follow-on

Only after the post-retrieval selector question is resolved should a separate experiment test whether pre-retrieval Claim Profile / Evidence World Profile information improves query generation or source routing.

Do not combine retrieval-generation changes with typed selection in the first experiment.

## Current programme boundary

This work is deliberately deferred while ClaimGate and EvidenceGate are developed as pre-retrieval characterization / authority boundaries. Nothing in this note authorizes changing the current EB integration baseline.