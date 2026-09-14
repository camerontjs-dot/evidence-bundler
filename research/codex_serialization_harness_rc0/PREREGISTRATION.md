# Codex Serialization Harness RC0 — Preregistration

Status: **PREREGISTERED / EXECUTION PENDING**

Classification: **Research Infrastructure Qualification**

This is not an Evidence Bundler retrieval experiment, not an RC1 semantic rerun, and not a production promotion task.

## Antecedent

Paused Evidence Bundler RC1 PR #74 reached semantic child execution under V4. The fourth Stage-1 child emitted a single final child message whose relation-ID sequence already contained duplicate IDs. The preserved mechanical audit at `b944e6d68cd9c711e1ad30e880b0226bb134e3d3` localized the defect to the child-message boundary and ruled out cross-review output reuse, file append, collector concatenation, packet duplication, and the RC1 validator as the source of the duplicate.

RC1 remains paused. This harness does not resume it.

## Question

Can the same local `codex exec` path used by RC1 reliably produce a structurally exact 96-key output when constrained by `--output-schema`, with fresh isolated execution state and independently validated final-message receipts?

## Frozen environment target

The V4 audit recorded:

`codex-cli 0.154.0`

RC0 qualifies only that installed CLI version. A different installed version is an environment mismatch, not a pass or fail of the frozen target.

## Synthetic fixture

The harness contains exactly 96 unique opaque relation IDs.

Each ID carries only a synthetic integer bucket `0..3`. There is no proposition, passage, evidence, retrieval score, admission state, or semantic judgment.

Deterministic bucket mapping:

- `0` -> `KEEP_DISTINCT`
- `1` -> `DROP_REDUNDANT`
- `2` -> `DROP_DISTRACTOR`
- `3` -> `UNRESOLVED`

The output schema represents all 96 relation IDs as required object keys under `labels`, forbids extra label keys, and constrains values to those four strings.

## Execution

Exactly **12** fresh sequential Codex executions.

Each execution must have:

- a unique fresh run directory;
- a unique `reviewer_id`;
- a previously nonexistent final-output path;
- a previously nonexistent JSONL trace path;
- `--ephemeral`;
- `--ignore-user-config`;
- `--ignore-rules`;
- `--skip-git-repo-check`;
- read-only sandbox;
- `--json`;
- `--output-schema`;
- `--output-last-message`;
- only the authorized child command:
  `cat SYNTHETIC_INPUT.json SERIALIZATION_TASK.md`.

No failed child is retried within RC0.

## Pre-execution controls

Before the first Codex child:

1. clean checkout required;
2. frozen synthetic packet / expected labels / output schema must mutually conform;
3. deterministic local self-test must pass;
4. the self-test must reject:
   - duplicate JSON object keys;
   - missing relation IDs;
   - extra relation IDs;
   - invalid labels;
   - valid-but-wrong deterministic labels;
   - wrong reviewer ID;
   - unauthorized child commands;
   - multiple completed final agent messages;
5. installed `codex --version` must equal `codex-cli 0.154.0`;
6. `codex exec --help` must expose all required flags, including `--output-schema`.

## Per-child validation

A child passes only if:

- process exit code is zero;
- `FINAL.json` is newly created;
- trace parses as JSONL;
- exactly one authorized completed command appears;
- no forbidden file-change / web / MCP / collaboration item appears;
- exactly one completed final agent message appears;
- trace final message and `FINAL.json` are text-identical after surrounding whitespace normalization;
- raw JSON parses with duplicate-key rejection at every object level;
- top-level key set is exact;
- `reviewer_id` is exact;
- `labels` has exactly the frozen 96 relation-ID keys;
- there are no missing or extra IDs;
- every value is allowed;
- every value equals the frozen deterministic bucket mapping.

## Terminal harness statuses

### `QUALIFIED`

Only if all 12 / 12 fresh executions pass every control and validation.

### `NOT_QUALIFIED`

Any structural, isolation, output, duplicate-key, deterministic-value, trace/final-identity, or child-execution failure after the target environment is established.

### `ENVIRONMENT_BLOCKED`

The frozen target cannot be exercised, including missing CLI, version mismatch, or missing required CLI capability.

### `HARNESS_ERROR`

Unexpected harness implementation failure.

## Interpretation boundary

A `QUALIFIED` result means only that this exact serialization path survived this synthetic 96-key stress qualification under the frozen CLI version.

It does **not**:

- validate any RC1 semantic judgment;
- rehabilitate the failed V4 cohort;
- authorize selective rerun of Cobalt-1;
- authorize RC1 continuation automatically;
- promote Evidence Bundler V1;
- alter K, retrieval, selection, admission, or production defaults.

Any RC1 continuation requires a separate explicitly documented post-exposure correction and fresh full Stage-1 cohort.

## Falsifier

One structurally invalid or non-isolated child among the 12 is sufficient to withhold qualification.

## Heaviest assumption

The heaviest assumption is that schema-constrained synthetic 96-key generation is a useful discriminator for the same serialization failure mode that affected the V4 96-relation Cobalt child.

A later RC1 continuation must still preserve independent child validation and cannot treat this qualification as proof that semantic outputs will never fail.
