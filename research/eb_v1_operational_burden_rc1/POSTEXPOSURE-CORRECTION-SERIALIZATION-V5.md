# RC1 post-exposure continuation correction — V5 serialization apparatus

Status: FROZEN BEFORE V5 SEMANTIC EXECUTION

RC1 V4 reached semantic child execution before stopping. Three Amber reference reviewers produced structurally valid outputs. Cobalt reference reviewer 1 produced an invalid output containing duplicate relation IDs. No Stage-1 reference was frozen, Stage 2 never began, and no evaluator or RC1 scientific conclusion ran.

The mechanical audit frozen at `b944e6d68cd9c711e1ad30e880b0226bb134e3d3` established that the duplicate relation IDs were already present in the child's final agent message. It ruled out output-file reuse/append, collector concatenation, packet duplication, and the validator as the source.

The exposed V4 outputs remain preserved evidence. V5 excludes them completely. They are not repaired, deduplicated, consolidated, selectively rerun, or reused.

Serialization Harness RC0 PR #75 qualified the replacement output mechanism at `1240671474b0f2cf638338bbcfd7ba0fc98e7322` using `codex-cli 0.154.0`: 12/12 fresh 96-key structured-output executions passed, with exact trace/final equality and negative controls for duplicate keys, missing/extra IDs, duplicate/malformed result messages, result-not-last, identity errors, deterministic-value errors, and unauthorized commands.

V5 changes only child serialization and mechanical validation. Labels are emitted as a required JSON object keyed by opaque relation ID, with a strict `--output-schema`, supervisor-generated unique reviewer IDs, duplicate-key-aware parsing, and the exact qualified trace-classifier blob loaded from the qualified harness commit.

Scientific invariants are unchanged: same blind packets; same four label definitions; same lane-relative rule; `amber=5/3`, `cobalt=10/7`; three fresh reference reviewers per arm; 2-of-3 non-UNRESOLVED consolidation; reference freeze before test review; two fresh test reviewers per arm; the same `>=49/54` plus all-18-lanes coverage guard; the same false-keep, false-drop, unresolved, and action-disagreement primary counts; the same larger-arm decision rule; and the same stop boundary.

V5 must use a completely fresh six-reviewer Stage-1 cohort. If any child or apparatus step fails, stop and preserve the failure. No selective child replacement is authorized.

No merge, release, tag, production-default change, or V1 promotion is authorized by this correction.
