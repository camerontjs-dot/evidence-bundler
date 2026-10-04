# EB purpose and fitness evidence — 2026-10-04

This directory supports the [dated assessment](../../docs/assessments/EB_V1_20261004.md) and the changing plan in [issue #132](https://github.com/camerontjs-dot/evidence-bundler/issues/132). These are bounded engineering observations, not a stable-release declaration or a replacement for earlier frozen research.

## Records

| Record | What it preserves |
|---|---|
| [CONTAINMENT-SUCCESSOR.md](CONTAINMENT-SUCCESSOR.md) / [JSON](CONTAINMENT-SUCCESSOR.json) | Complete 21-case independent baseline/correction matrix: the corrected installed artifact passes all 21 controls. The report's matrix link was adapted to its published filename. |
| [HOSTED-CI-ARTIFACT-AUDIT.json](HOSTED-CI-ARTIFACT-AUDIT.json) | Successful exact-head Linux run on Python 3.11/3.12, all four downloaded artifact digests, full installed dependencies, wheels, original sentinels and real positive/tampered consumer receipts. |
| [FIXTURE-CANONICAL-A2-CHECK.json](FIXTURE-CANONICAL-A2-CHECK.json) | All eight frozen synthetic inputs accepted unchanged by the exact canonical A2 validator. |
| [APPARATUS-FIRST-FAILURE.json](APPARATUS-FIRST-FAILURE.json) | Preparation preflight stopped before EB execution; ordinary helper correction and preserved first-attempt identity. |
| [workflow/OBSERVATION.json](workflow/OBSERVATION.json) | Exact candidate, wheel subject, kit/helper hashes, original preparation identity, per-case artifact maps, recorded CLI timings and publication adaptations. |
| [workflow/REVIEW-OBSERVATION.md](workflow/REVIEW-OBSERVATION.md) / [reviews](workflow/reviews) | Fresh review aperture, all first judgments/reasons, coverage notes, measured case intervals and source-inspection/presentation limitations. |
| [workflow/review-packets](workflow/review-packets) | The actual retained text and bindings seen by the reviewer. |
| [workflow/REVIEW-FREEZE.json](workflow/REVIEW-FREEZE.json) / [REPLAY-RESULT](workflow/REPLAY-RESULT.json) | Review-file freeze and complete emitted output hash map. |
| [workflow/COVERAGE.json](workflow/COVERAGE.json) / [EVALUATION](workflow/EVALUATION.json) | Helper-created counts/manual notes and frozen positive/gap gates, including fabricated weak evaluator controls. |
| [workflow/INSTALLED-IDENTITY.json](workflow/INSTALLED-IDENTITY.json) / [CONSUMERS](workflow/CONSUMERS.json) | Local wheel/install/exact-source comparison across 52 EB, nine B and 83 CAL payload files, then actual B/CAL checks of all eight reviewed outputs and exact admitted-pair equality. |

`SHA256SUMS` covers every other published file in this directory. The untouched 17-file [fixture kit](../eb_v1_workflow_acceptance_20261004) has its own earlier freeze and is intentionally separate from observed results. The reproduction commands are in [local acceptance](../../docs/EB_V1_LOCAL_ACCEPTANCE.md).

## Subjects and result boundaries

The local correction and workflow were measured at `0f5e7d9df2d4fe223b737bea27281c90cdfe0ebb`, wheel SHA-256 `63a1d6a3c89f2fb4daef6825773c024f6dc0f392a889e07d0adf3779f6b90a14`, in a lightweight Python 3.12 environment with the pinned consumers. Hosted full-dependency qualification was measured at `6be9ab4809440365f9fcdf4aafa6b264cdfdf02c`. The latter changes only receipt archiving in CI; product runtime bytes are unchanged. Their wheel archive hashes are separately recorded and must not be conflated.

The synthetic workflow passed five named adequate targets, four named gaps and complete/incomplete `all_of` boundaries. The fresh agent recorded seven accepted and six rejected relationships. This is one first-pass engineering judgment set, not independent human review, qualified automatic semantic assessment, population recall or human productivity. The p07 header/table acceptance depends on visible same-note context; the isolated table is not self-contained. The helper's readable packets, review binding and counts are test apparatus, not shipped V1 user-interface features.

Only publication path labels were shortened where explicitly recorded. Review decisions and fixture bytes were not edited to obtain a pass. Complete deterministic native/B payloads can be reproduced from the pinned inputs, runtime and frozen decisions; this compact evidence directory retains their identities and the review material rather than duplicating every output file.

The initial failed CI receipt-upload run, earlier containment failures, and the terminal #121 result remain preserved under their original identities. No frozen research attempt, main merge, tag or release was performed here.
