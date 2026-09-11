# RC0 Execution-Surface Limitations

## Observed execution surface

The connected container could not clone `https://github.com/camerontjs-dot/evidence-bundler.git` because outbound DNS/network access was unavailable (`Could not resolve host: github.com`). Repository authority and writes were therefore handled through the GitHub connector, while the research evaluator/corpus execution occurred in a local temporary workspace.

## Consequences

- The decisive evaluator run was **not** a GitHub Actions run.
- No workflow-run, job, or artifact ID exists for the decisive local execution.
- The maintained Evidence Bundler regression suite and Contract A validator were not completed as a post-freeze CI qualification sequence in this execution surface.
- Several planned external-model/parser weak controls (C5/C6/C8/C9/C10) were unavailable and were not simulated.
- Independent human adjudicators were unavailable for the six-root pilot; the pilot is only a development annotation-spec sanity check.
- The complete local corpus, gold, runners, control outputs, and target raw outputs were bundled and hash-addressed; the durable GitHub PR records the frozen evaluator, preregistration/spec, receipt, terminal results, deviations, and decisive counterexamples. The full local bundle is supplemental, not GitHub authority.

## Why the terminal disposition remains FALSIFIED

The missing CI steps could prevent a positive qualification claim, but they do not rescue the exact frozen evaluator from a directly observed preregistered semantic falsifier. In the frozen development execution, the target accepted multiple explicit unsafe minimal mutations and intrinsic-ambiguity cases as `ACCEPTABLE_WITHIN_PROFILE`, and exact replay reproduced the same raw bytes. Issue #59 states that any critical meaning-changing mutation accepted as safe or ambiguity silently converted to acceptance is a terminal falsifier.

Accordingly, the exact RC0 evaluator cannot advance to fresh qualification. No claim is made that the overall research infrastructure satisfied every planned CI/independence requirement.
