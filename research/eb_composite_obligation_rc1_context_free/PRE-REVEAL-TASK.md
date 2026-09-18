# Pre-Reveal Task — Composite Obligation RC1

Operate as an isolated prereveal author/evaluator builder.

You have no access to the normal CAL Pipeline conversation and must not seek it.

Use only the bootstrap files explicitly supplied by the workflow.

Your job is to produce a sealed fresh fixed-pool qualification packet for composition, claim-native subject identity, and mechanically derived expected evidence forms.

Follow the freeze order exactly:

1. author 24 fresh parent/child claims;
2. freeze claims and subject provenance;
3. mechanically derive/freeze expected evidence forms;
4. author/freeze 10-candidate pools;
5. mechanically score/freeze child-candidate semantic scores;
6. adjudicate sealed gold from sanitized inputs that exclude descriptor/design metadata;
7. validate eligibility;
8. return `READY_FOR_REVEAL` with exact refs/hashes.

Do not inspect or infer the post-reveal selector implementation, stage ordering, loss cap, development results, or expected winner.

Do not tune or repair cases after gold inspection. Preserve invalid outputs and terminate `BLOCKED_COHORT` if eligibility cannot be met without post-gold repair.

Terminal states:

- `READY_FOR_REVEAL`
- `BLOCKED_APPARATUS`
- `BLOCKED_COHORT`
- `CONTAMINATED_PRE_FREEZE`
