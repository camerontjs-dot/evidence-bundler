# EB Typed Selector RC1 — Context-Free Return Handoff

Use this exact structure when returning from the prereveal authoring lane.

## Terminal state

One of:

- `READY_FOR_REVEAL`
- `BLOCKED_APPARATUS`
- `CONTAMINATED_PRE_FREEZE`

## Repository identities

- repository:
- bootstrap branch/head:
- context-free authoring branch:
- input freeze ref:
- input freeze commit/tree:
- sealed-gold ref or artifact identity:
- evaluator identity/hash:

## Frozen cohort

- eligible lanes:
- category counts:
- positive lanes:
- no-clear-suitable lanes:
- lanes with deep useful candidate rank 4-10:
- lanes with unsafe/misleading candidates:
- complementary-coverage lanes:
- preregistered exclusions from primary scoring:

## Frozen hashes

- cohort manifest SHA-256:
- claim/source fixture SHA-256 or manifest root hash:
- depth-10 candidate-pools SHA-256:
- profiles SHA-256:
- evaluator SHA-256:
- evaluator-tests SHA-256:
- sealed gold SHA-256:
- prereveal receipt SHA-256:

## First-stage authority

- integration candidate commit used:
- candidate depth:
- retrieval replay status:
- candidate-pool determinism evidence:
- any first-stage deviations:

## Information aperture

### Sources opened before freeze

List exact paths/refs only.

### Forbidden sources opened

Must be `none` for `READY_FOR_REVEAL`.

### Broad searches performed

Must be `none` unless explicitly allowed and justified by the bootstrap manifest.

## Replacement/deviation record

For every rejected/replaced lane, list:

- lane/category;
- reason;
- whether retrieval output had already been seen;
- replacement identity;
- confirmation that no target information was available.

## Evaluator freeze

- metrics implemented:
- support gate encoded:
- falsification gate encoded:
- inconclusive gate encoded:
- metamorphic/system controls:
- deterministic replay result:
- weak-control discrimination logic encoded before reveal: yes/no

## Gold separation

- sealed gold exact identity:
- gold hash recorded in prereveal receipt: yes/no
- normal execution lane has not opened gold: not yet applicable / evidence if known

## Deviations

List every apparatus or protocol deviation. Do not omit repaired failures.

## What is established

Only describe prereveal apparatus facts, for example:

- fresh cohort is frozen;
- candidate pools are deterministic;
- evaluator and thresholds are frozen;
- target/development denylist remained unopened.

## What is not established

Must include:

- no selector arm has been executed on the fresh cohort;
- no research disposition about the selector is authorized;
- no production promotion is authorized.

## Exact next authorized step

For `READY_FOR_REVEAL`:

> In the normal CAL Pipeline execution lane, open only the frozen non-gold input/evaluator identity plus the post-freeze target/control surfaces permitted by `FREEZE-AND-REVEAL-PROTOCOL.md`; bind ARM_A-D; freeze the adapter; run all arms and metamorphic gates twice without opening sealed gold; commit the arm-output freeze receipt; only then reveal gold and run the frozen evaluator.
