# RC1 Harness Audit Deviation — Portability Predicate False Negative

Status: **MECHANICAL AUDIT HARNESS DEFECT**

This is not a scientific result and did not launch any semantic reviewer.

## Trigger

The first mechanical V4 harness audit stopped with:

`HARNESS_AUDIT_FAILED`

`FAILING_STEP=V4 portability gate`

`ERROR=V4 portability gate missing: ["tr '[:lower:]' '[:upper:]'"]`

No audit report commit or push was produced by that execution.

## Diagnosis

`run_rc1_with_codex_v4.sh` generates Bash-3-compatible uppercase expressions from inside a Python heredoc. In the V4 source file, the single quotes around the `tr` character classes are escaped because they occur inside Python single-quoted string literals.

The first audit entrypoint incorrectly searched the V4 source for the unescaped generated-shell fragment:

`tr '[:lower:]' '[:upper:]'`

That exact source-text predicate was too literal. It produced a false negative even though the V4 generator contains the intended portability rewrite and the prelaunch `bash -n` gate.

## Correction

The audit entrypoint now checks the source-generation invariants instead:

- `bash -n "$TMP_RUNNER"` is present;
- generated-runner rejection remains if `${phase^^}` or `${set_name^^}` survives;
- the generator requires exactly two portability replacements;
- `phase_upper` and `set_upper` generation are present;
- the escaped `tr` source fragment is present;
- exactly two `portable_replacements += 1` accounting sites remain.

The corrected audit additionally refuses to inspect a failed worktree unless its HEAD is exactly the preserved V4 launch commit:

`ebed6c29b31614687c0b3d7b0f05444482166abd`

## Boundary

No V4 reviewer was rerun.
No semantic labels or judgments were inspected by this correction.
No failed output was deduplicated, repaired, normalized, replaced, or deleted.
No reference consolidation or evaluator was run.
RC1 remains paused as a harness/infrastructure investigation.
