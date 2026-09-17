# EB Typed Selector RC1 — Freeze and Reveal Protocol

## Why two execution lanes

The fresh cohort/gold/evaluator must be authored without target knowledge, while the target execution must occur without using gold to tune or adapt the frozen selector.

Use two bounded lanes:

1. **Context-free authoring lane** — creates and freezes fresh inputs, candidate pools, profiles, gold, evaluator, gates, and receipts without target access.
2. **Normal execution lane** — receives the frozen input/evaluator identity, reveals the exact target/control implementation, runs all arms without opening gold, freezes arm outputs, then opens gold and evaluates.

This is a commit/reveal protocol. A fresh chat alone is not the assurance claim.

## Phase A — prereveal context-free authoring

The authoring lane may read only the pre-reveal allowlist in `BOOTSTRAP-MANIFEST.json`.

Required frozen objects:

- `COHORT.json` or an equivalent manifest listing the exact 30 lane identities;
- exact claim/source fixture bytes;
- exact depth-10 candidate-pool bytes for all lanes;
- exact claim-profile bytes;
- `GOLD.json` sidecar;
- evaluator source and tests;
- cohort-eligibility report;
- case replacement/deviation log;
- source-access log;
- prereveal freeze receipt.

The freeze receipt must record SHA-256 for every scientific object and Git commit/tree identities for the branch.

### Required authoring branches/refs

The context-free author should create two clearly separated refs from the same authoring lineage:

- `research/eb-typed-selector-rc1-fresh-input-<date>` — contains the frozen non-gold input cohort, candidate pools, profiles, evaluator, eligibility report, and prereveal receipt;
- `research/eb-typed-selector-rc1-sealed-gold-<date>` — contains the exact gold sidecar and gold hash receipt.

The sealed-gold ref must not be opened by the normal execution lane until arm output freeze.

If the repository implementation makes that two-ref arrangement impractical, an equivalent exact artifact separation is acceptable only when the freeze receipt states the substitute mechanism and preserves the same reveal order.

## Phase A freeze receipt

Minimum fields:

```json
{
  "status": "READY_FOR_REVEAL",
  "input_ref": "...",
  "input_commit": "...",
  "input_tree": "...",
  "gold_ref": "SEALED",
  "gold_commit_or_artifact_identity": "recorded but not opened by execution lane",
  "cohort_sha256": "...",
  "candidate_pools_sha256": "...",
  "profiles_sha256": "...",
  "evaluator_sha256": "...",
  "gold_sha256": "...",
  "eligible_lane_count": 30,
  "category_counts": {},
  "replacement_count": 0,
  "opened_sources_pre_freeze": [],
  "denylist_exposure": false,
  "deviations": []
}
```

Do not place selector-development results or target code in the receipt.

## Phase B — post-freeze target reveal

Only after a valid `READY_FOR_REVEAL` receipt exists may the normal execution lane open target material.

Authorized target identity:

- candidate freeze commit: `98ddfb4f2e9623da6b44009abf921657b9445955`
- selector source path after reveal: `research/eb_typed_selector_rc0/selector.py`
- expected selector SHA-256: `e83e6305008a0f7a264cde2167bff80ce6399f03d34ebce10376f106c52cec6c`

After reveal, the execution lane may also read only the minimum frozen files needed to bind the semantic comparison arm and weak control from the candidate freeze. Prefer immutable raw file/blob reads over PR narrative.

Do not use PR #82 body/comments or development reports as execution guidance when exact frozen source/config bytes suffice.

## Arm binding

After prereveal freeze and before execution, record a small reveal receipt binding the evaluator's opaque arm keys:

- `ARM_A` = rank-only top-3 control;
- `ARM_B` = frozen semantic-only top-3 control;
- `ARM_C` = frozen typed candidate selector top-3;
- `ARM_D` = frozen weak/ablation control from the selector candidate freeze.

The evaluator remains unchanged after this mapping is known.

## Post-reveal adapter rule

A thin adapter may be written after reveal only to transform the already-frozen lane/candidate/profile records into the frozen target's input shape and serialize selected IDs.

The adapter may not:

- inspect or import the sealed gold;
- contain lane IDs, passage IDs, category IDs, expected answers, per-case weights, or case-specific branches;
- change target weights/rules/model identity;
- change candidate text/order/history except for the exact transformations required by the frozen target input contract;
- alter the first-stage candidate pool;
- call CAL or any downstream verdict system.

Freeze and hash the adapter before arm execution.

## Phase C — blind arm execution

The execution lane opens:

- frozen non-gold input ref;
- exact target/control source/config authorized after reveal;
- no sealed gold.

Run all four arms twice on all 30 lanes.

Before any gold reveal:

1. freeze `ARM_OUTPUTS.json` for each replay;
2. verify byte-identical exact replay;
3. run all preregistered metamorphic/system gates;
4. commit an arm-output freeze receipt with input hashes, target/control hashes, adapter hash, output hashes, runtime/model identity, and source-access log;
5. declare that sealed gold was not opened.

If gold is opened before this receipt, terminal state is `BLOCKED_APPARATUS` for this decisive execution.

## Phase D — gold reveal and evaluation

Only after valid arm-output freeze:

1. open the sealed-gold identity supplied by Phase A;
2. verify its SHA-256 against the prereveal receipt;
3. run the already-frozen evaluator without editing it;
4. produce `DECISIVE-RESULT.json` and `DECISIVE-RESULT.md`;
5. assign exactly one research disposition allowed by `EVALUATION-CONTRACT.md`;
6. preserve all failures/deviations and both replays.

## Scientific-change rule

After Phase A freeze, any material change to:

- cohort/gold/evaluator;
- target selector;
- semantic control;
- weak control;
- K=3 budget;
- first-stage depth-10 pools;
- primary metrics or thresholds;

requires a successor experiment identity. Do not patch and continue the same decisive claim.

Purely mechanical execution fixes are allowed only when they cannot affect scientific behavior, are documented before rerun, and leave all frozen scientific object hashes unchanged.

## Final handoff

Return to the normal CAL Pipeline project with:

- input/gold/evaluator freeze identities;
- target/control identities;
- arm-output freeze identity;
- exact CI/run/artifact receipts;
- source-access/reveal order;
- deviations/contamination state;
- observations;
- bounded inference;
- terminal disposition;
- what remains unestablished;
- smallest next authorized action.
