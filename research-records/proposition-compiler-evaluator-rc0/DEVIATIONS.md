# Deviations

## D1 — pre-freeze test-loader collection failure

Observed during local development before any evaluator freeze or decisive RC0 run.

`pytest -q tests/test_pc_rc0.py` initially failed during collection because the dynamic import test harness executed `evaluator.py` without registering the module in `sys.modules`; Python 3.13 `dataclasses` then could not resolve the module namespace.

Disposition: harness defect. The test harness was corrected by registering the module before `exec_module`. No evaluator semantic rule, candidate fixture, gold label, or decision gate was changed in response to this failure.

This failure is preserved because failed/deviant runs are evidence, even when non-semantic.
