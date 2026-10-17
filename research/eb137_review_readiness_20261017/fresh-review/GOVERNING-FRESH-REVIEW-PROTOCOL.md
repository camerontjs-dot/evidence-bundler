## Preregistered fresh-review gate: installed display-context surface

Treat this as a new bounded operator/reviewer qualification. It does **not** reuse the result identity of the earlier synthetic run.

### Subject
Run only after the exact #137 candidate head and wheel are recorded. If the candidate changes, freeze a new execution identity.

### Frozen inputs
Use the eight Contract A inputs already frozen and merged by #134, byte-for-byte. Do not edit fixtures or expected opportunities after seeing the candidate output.

### Reviewer aperture
Use a fresh context. Before decisions, the reviewer may read only:
- a short reviewer rule below;
- each candidate-generated `review_context.md`;
- its corresponding candidate-generated `review_record.json`.

The reviewer must not read:
- `EXPECTED-OPPORTUNITIES.json`;
- prior p01-p08 reviews, decisions, evaluation or local report;
- #121/#133/#134/#135/#137 conclusions;
- product source/tests;
- the oracle or expected outcome.

Record the actual files read and contamination status.

### Reviewer rule
For each retained proposition/passage pair, choose `accepted`, `rejected` or `needs-review`, with a nonblank reason.

**Accept only when the admitted passage text itself is materially on-target and locally adequate for subsequent assessment.** Display context may orient the reviewer to the source, but it is explicitly not admitted downstream and therefore may not supply a fact, qualifier, subject, unit, scope or relation that is missing from the passage text. A passage can be accepted when it contradicts the claim; acceptance is evidence suitability, not support.

For a target with no retained passage, record the displayed gap state without inventing evidence.

### Evaluation kept hidden from reviewer
After all review files are frozen:
1. mechanically verify their bindings and complete retained-pair coverage;
2. apply them through the installed **`--review`** route, not `--admission`;
3. require stale-review refusal/no-output as a separate control;
4. compare adequate-positive/gap and complete/incomplete parent boundaries against the already frozen #134 opportunity set;
5. require the separated-context limitation case to retain **zero accepted passages** if no individual admitted span is locally adequate;
6. run the actual pinned B1.2/CAL consumer check and require exact admitted-pair equality;
7. preserve the first result and any contamination/failure.

Always-accept and always-reject fabricated evaluator controls must remain failing controls.

### Disposition
- `SUPPORTED_FOR_REVIEWED_WORKFLOW_PROMOTION` only if the frozen gate passes, the separated-context control does not smuggle display-only authority into admission, and the actual consumers match the reviewed decisions.
- `FALSIFIED_REVIEW_CONTEXT_BOUNDARY` if display-only information causes admission of a locally inadequate passage or another required semantic boundary fails.
- `APPARATUS_INVALID` if the reviewer aperture, bindings or evaluator are invalid.
- `INCONCLUSIVE` for an unresolved result that is neither a valid pass nor falsifier.

This gate does not establish representative-workload usefulness, human throughput, stable carrier policy, dependency packaging, CAL semantic correctness, or 1.0 readiness.
