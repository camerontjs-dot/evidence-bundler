# Prerequisite failure-classifier qualification RC0

This research-infrastructure experiment follows Evidence Bundler PR #127.

RC2 completed the writer request, extracted all five profile files, and then the frozen checker failed with raw reason `'output'`. Inspection of the frozen checker shows that this witness occurs at the first direct access to `calibration["output"]`. The launcher then misclassified the raw KeyError as `BLOCKED_CUSTODY_VERIFICATION` because its message-based fallback did not recognize `'output'` as a profile-surface failure.

This successor does not repair or rerun RC2. It qualifies a structured diagnostic boundary offline, using synthetic fixtures only.

The decision is whether a checker/classifier can reliably distinguish:

- profile-configuration failures;
- custody-verification failures;
- contamination;
- unexpected apparatus errors;

without relying on exception-message substring guessing.

No model, network, writer, semantic evaluator, generation case, weak generator, private corpus, retrieval, or production path is exercised.
