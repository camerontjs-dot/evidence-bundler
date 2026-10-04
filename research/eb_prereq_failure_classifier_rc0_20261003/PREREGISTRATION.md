# Prerequisite failure-classifier qualification RC0

## Objective / decision

Determine whether a structured checker/classifier can distinguish profile-configuration failure from custody failure strongly enough to support a future prerequisite experiment.

This is an apparatus qualification. It does not authorize another writer attempt.

## Authority

Repository: `camerontjs-dot/evidence-bundler`.

Live GitHub is authoritative for current repository and PR state.

Pinned predecessor evidence:

- PR #127 terminal head: `534f6801998d96c72783fa1895d6a404dec7ec1a`
- RC2 frozen source: `e850d812036d0eca2ab1c79185bf871a9636684a`
- RC2 source tree: `2a115eca48d0ec2e4896b98280d2d4b1fcb4439d`
- RC2 frozen checker blob: `21a3fe9e9dbb90cb8894e8c1ee36d78a61e99a74`
- RC2 public checker witness: result FAIL, reason `'output'`

RC2 remains immutable evidence. Do not edit PR #127 or reinterpret its terminal disposition.

## Hypothesis

A structured diagnostic checker with explicit failure categories and codes can correctly classify the frozen synthetic mutation matrix, while plausible weak message-based classifiers fail meaningful cases.

## Categories and dispositions

`PROFILE_CONFIGURATION` -> `BLOCKED_PROFILE_CONFIGURATION`

`CUSTODY_VERIFICATION` -> `BLOCKED_CUSTODY_VERIFICATION`

`CONTAMINATION` -> `CONTAMINATED`

`APPARATUS_ERROR` -> `INCONCLUSIVE`

A fully valid fixture returns `PASS`.

Unexpected exceptions must never default to custody.

## Frozen synthetic matrix

The matrix includes profile-configuration mutations, custody mutations, one contamination mutation, a valid baseline, and a raw unexpected `KeyError("output")` apparatus witness.

The profile group covers missing calibration/decisive output fields, missing decision state, wrong enum, malformed review JSON, config drift, missing uncertainty instruction, and a missing profile file.

The custody group covers request/response hash mismatches, incomplete/truncated response state, runtime digest mismatch, and profile-hash mismatch.

## Decision discrimination

Two deliberately weak controls are frozen:

1. the RC2-style exception-message substring heuristic;
2. an everything-is-custody classifier.

The raw `'output'` witness must defeat the RC2-style heuristic for the intended reason. The everything-custody control must fail profile and contamination boundaries.

If the target classifier and either weak control both achieve a perfect decision gate, the apparatus claim is `INCONCLUSIVE`.

## Acceptance

Support requires:

- valid baseline PASS;
- every frozen mutation returns exactly its preregistered category, code, and disposition;
- no raw `KeyError` or other unstructured exception escapes the target checker;
- unexpected exceptions map to `APPARATUS_ERROR / INCONCLUSIVE`;
- weak RC2-style heuristic fails the raw `'output'` witness;
- everything-custody weak control fails profile and contamination cases;
- two-run byte-identical machine result;
- Python 3.11 and 3.12 dedicated CI pass;
- no production or predecessor bytes change.

## Falsifiers / legitimate negative outcomes

`FALSIFIED` if any target classification differs from the preregistered expected result.

`INCONCLUSIVE` if the target passes but weak controls are not meaningfully discriminated, or the harness cannot establish the intended boundary.

`BLOCKED` if required immutable predecessor authority or environment is unavailable.

`SUPPORTED_FOR_APPARATUS_SUCCESSOR` only if every acceptance condition is observed.

## Boundary

Allowed:
- this research-infrastructure subtree;
- its dedicated workflow;
- synthetic temporary fixtures;
- offline deterministic execution.

Prohibited:
- reading unpublished RC2 profile bodies;
- using RC2 native request/response bodies as fixtures;
- model/API/network invocation;
- another writer attempt;
- semantic calibration;
- target generation;
- private PR #124 material;
- production changes;
- merge, release, or promotion.

## Stop

Stop after the frozen matrix and weak controls reach a terminal disposition. Do not expand the suite after observing a failing case inside the same qualification candidate.
