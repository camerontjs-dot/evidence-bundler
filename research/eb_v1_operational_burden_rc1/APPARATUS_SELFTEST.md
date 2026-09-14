# RC1 Apparatus Self-Test

Status: **MECHANICAL SELF-TEST ONLY — NOT SCIENTIFIC EVIDENCE**

Performed before any RC1 semantic reviewer exposure.

Checks:

- Python apparatus files compile successfully.
- `run_rc1_with_codex.sh` passes `bash -n`.
- Synthetic reference reviewers with complete unanimous `DROP_DISTRACTOR` labels consolidate deterministically.
- Synthetic test reviewers matching that reference produce:
  - `SUPPORTED FOR PROMOTION`
  - `NO_OBSERVED_OPERATIONAL_DECISION_HARM`
  - 54/54 matched relationships scoreable
  - 18/18 lanes represented.
- Mutation control: flipping one **matched larger-arm** test decision from `DROP` to `KEEP` produces:
  - `FALSIFIED`
  - `OPERATIONAL_DECISION_HARM_OBSERVED`
  - larger-arm `false_keep=true`
  - larger-arm action disagreement worse than smaller arm.
- Coverage control: forcing six shared reference relationships unresolved produces:
  - `INCONCLUSIVE`
  - `REFERENCE_COVERAGE_GUARD_FAILED`
  - 48/54 scoreable matched relationships.

No synthetic labels or outcomes are review evidence and none may be used to infer the RC1 result.
