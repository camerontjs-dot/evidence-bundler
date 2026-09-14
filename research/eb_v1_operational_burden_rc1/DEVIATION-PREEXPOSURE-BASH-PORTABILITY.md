# RC1 Pre-Exposure Deviation 3 — macOS Bash Portability

Status: **PRE-EXPOSURE APPARATUS CORRECTION**

## Trigger

The V3 retry started from:

`7b89496a8b51072197db6384bad4ef75b6ae0dad`

It stopped during generated-runner setup with:

`RC1_EXECUTION_FAILED`

`FAILING_STEP=V3 runner execution setup`

`ERROR=.../run_rc1_with_codex_v3_inner.sh: line 67: $out_dir/${phase^^}_${set_name^^}_${ordinal}.json: bad substitution`

`LAST_PUSHED_COMMIT=7b89496a8b51072197db6384bad4ef75b6ae0dad`

## Diagnosis

The original frozen RC1 runner used Bash uppercase parameter expansion:

- `${phase^^}`
- `${set_name^^}`

That syntax requires Bash 4 or newer. macOS ships an older system Bash that rejects this expansion with `bad substitution`.

The failure occurs while constructing the child output filename, before the runner prints `Launching isolated ...` and before the `codex exec` child command is reached.

## Contamination check

No RC1 semantic reviewer launched during this attempt. No Stage 1 reference judgment, Stage 2 test judgment, consolidated reference, or terminal scientific result was produced.

RC1 therefore remains pre-exposure.

## V4 correction

V4 preserves the original V1, V2, and V3 launchers unchanged.

The V4 launcher performs the same V3 scientific/apparatus preflight and deterministically rewrites only the two Bash-4-only output-path expressions in the temporary generated runner. It replaces them with Bash-3-compatible uppercase variables computed using `tr`:

- `phase_upper=$(printf '%s' "$phase" | tr '[:lower:]' '[:upper:]')`
- `set_upper=$(printf '%s' "$set_name" | tr '[:lower:]' '[:upper:]')`

The resulting output filenames are unchanged in meaning and spelling (`REFERENCE_AMBER_1.json`, `TEST_COBALT_2.json`, etc.).

V4 fails closed unless exactly the expected two Bash-4-only lines are replaced and no `${...^^}` expansion remains in the temporary runner.

## Scientific invariants unchanged

This correction does **not** change:

- either blind packet;
- packet relation IDs or lane structure;
- proposition or passage text;
- arm mapping;
- operational labels or rubric semantics;
- Stage 1 reference procedure;
- Stage 2 test procedure;
- reviewer prompt;
- reviewer isolation aperture;
- evaluator;
- coverage guard;
- directional rule;
- terminal dispositions;
- retrieval, K, selection, admission, or production defaults.

This is a shell-portability correction only and occurred before semantic exposure.
