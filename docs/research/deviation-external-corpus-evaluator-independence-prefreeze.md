# Pre-freeze development deviations

These failures occurred before the two-commit blind-handoff object was frozen. They are preserved because they informed the harness, but they are not scientific or benchmark results.

1. The first local dry run failed during test collection because the dynamic test loader did not register the loaded module in `sys.modules` before executing a dataclass declaration. The loader was corrected. No evaluator metric completed and no expected metric value was changed.
2. The next dry run produced `15 passed, 1 failed`. The failing mutation assertion incorrectly expected support recall to change when a support passage was relabelled as counterevidence even though the remaining support passage was also retrieved. The fixture assertion was corrected to test the role-metric pair rather than require both components to change. Evaluator implementations, gold bytes, metric formulas, and fail-closed rules were unchanged.

After these pre-freeze corrections the local dummy suite completed `16 passed`.
