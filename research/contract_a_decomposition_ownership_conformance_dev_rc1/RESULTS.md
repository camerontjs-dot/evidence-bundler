# Contract A Decomposition Ownership / Downstream Conformance Dev RC1 — Results

Status date: 2026-08-29 / 2026-08-30 UTC

Research disposition: **QUERY_LINEAGE_ALONE_IS_NOT_SEMANTICALLY_SUFFICIENT_FOR_CHILD_ATTRIBUTION**

Contract-A disposition: **EXPLICIT_PROPOSITION_LINEAGE_IS_JUSTIFIED; OWNERSHIP/FINAL_SCHEMA_REMAINS_UNRESOLVED**

Production disposition: **NO PROMOTION**

## OBSERVED — authority and frozen inputs

- Evidence Bundler main at experiment start: `6011789957f3294f97bff260069cfb5bb1c5772f`
- parent decomposition experiment result head: `0e4bed62553ebb6aef6a1b485664fb80cc78c802`
- decisive parent retrieval implementation: `55d158f829f4aad1ed8ad69b19d9e39d445c953d`
- parent workflow run: `33286415682`
- parent raw retrieval SHA256: `b7522a147f1dccd1614bb8dcb4565b8a8834bee4cf2d47695befeb311ebd6680`
- frozen F10 A1 semantic snapshot SHA256: `8dbedd537c024c4a624f21abd5fa11536ddfe558000f3a9366584c30c045e31c`
- Claim Audit Lab consumer pin: `53f0885b111676794d1bd20e10b91aa58b07e9d4`
- Apparatus Contracts authority pin: `00bdf9546a877f9f6c1d7fd227fd959e1d7aa99e`
- decisive ownership implementation: `c3e4b113fc230c333e02af67d17c64921d3f323a`
- decisive tree: `a859177f1541458354af069534593a8b67991d25`
- decisive workflow run: `33288231081`
- decisive job: `99195132731`
- artifact: `9725141991`
- artifact digest: `sha256:21e8d0e94956f034cbb3205e2958ef29d1841d24febf1b8d4a0d48a6e972686e`
- result SHA256: `1df1ad56d55fdce4d3aace0fc92c8e61a285cb9f0965ea67c56e8bd26bde0056`

No retrieval was rerun.

## OBSERVED — validation

On exact decisive head `c3e4b113...`:

- frozen retrieval snapshot identity: PASS;
- exact CAL consumer pin: PASS;
- full EB deterministic suite: **224 passed, 5 skipped**;
- Ruff research apparatus: PASS;
- fixed-retrieval downstream conformance assertions: PASS.

The first workflow attempt stopped before conformance execution on three Ruff findings after the full EB suite passed. Only import/formatting issues were repaired. No treatment, mutation, fixed evidence, falsifier, CAL pin, or contract interpretation changed.

## OBSERVED — current Contract B / CAL boundary

The promoted Contract B 1.2 factual-context profile deliberately preserves nomination/admission/review history in the intake ledger but excludes nomination metadata from CAL's semantic-measurement context.

The current strict CAL Contract-B claim model rejects an ungoverned inline `propositions` field.

Observed:

- `strict_contract_b_claim_rejects_inline_propositions = true`.

Therefore child propositions cannot simply be attached ad hoc to one existing Contract-B claim without a governed contract change.

## OBSERVED — fixed evidence world

The frozen F10 A1 object contains:

- parent claim: `claim-037`;
- child 1: `claim-037-a1-01`;
- child 2: `claim-037-a1-02`;
- exactly 12 admitted paragraph identities;
- actual frozen child-query coverage: **(6, 6)**.

The passage union is identical in every arm and mutation:

- passage count: **12**;
- union SHA256: `fee2a9ffbe379c201f5d59ef883647bda21d0406474b0b55b93ee11af8f626b6`.

## OBSERVED — lineage-collision mutation

The counterfactual mutation changes only child attribution:

- actual state: child coverage **(6, 6)**;
- mutation: child coverage **(12, 0)**.

It does not change:

- parent claim text;
- child proposition texts;
- passage union;
- passage bytes;
- source identities;
- admitted-passage count.

This is a metamorphic information-preservation test, not a claim about likely retriever behavior.

## OBSERVED — query-lineage representation

Q has one canonical Contract-B claim:

- `claim-037`.

Exact child identity/query text/rank/score remains available in the validated Contract-B intake history.

Therefore the intake ledger can distinguish:

- actual: `(6, 6)`;
- mutation: `(12, 0)`.

However CAL's promoted semantic-context projection intentionally strips nomination metadata.

Observed semantic child coverage in both worlds:

- child 1: 0;
- child 2: 0.

The normalized semantic-context hashes are byte-identical:

- actual: `4a8d9f64e9f0f129c8f138d0edcb26a7984f1db9b419a4b12ed4112eef0a35d1`;
- mutation: `4a8d9f64e9f0f129c8f138d0edcb26a7984f1db9b419a4b12ed4112eef0a35d1`.

Result:

**QUERY-LINEAGE SEMANTIC COLLISION OBSERVED.**

Two materially different proposition-coverage states become the same CAL semantic-measurement input.

## OBSERVED — first-class proposition shadow representation

P uses three canonical Contract-B claims in the research shadow:

- parent `claim-037`;
- child `claim-037-a1-01`;
- child `claim-037-a1-02`.

The same exact 12 passages are used.

CAL semantic context preserves child-specific admitted sets.

Actual semantic child coverage:

- child 1: 6;
- child 2: 6.

Mutation:

- child 1: 12;
- child 2: 0.

Normalized semantic-context hashes differ:

- actual: `ed61b2c22355888bbf73dab8387ee7b000ab9a9004219a18736ddda7c60de35a`;
- mutation: `2484dde6ffaca12af65126a0b9cab2068a3f9b3eec866c3a7f0c3498516dbab4`.

Result:

**FIRST-CLASS PROPOSITION REPRESENTATION DISTINGUISHES THE ATTRIBUTION MUTATION.**

## INFERENCE — what this establishes

### Query lineage is audit-sufficient but not semantic-measurement sufficient

The Contract-B 1.2 intake ledger faithfully preserves child retrieval provenance.

That is useful audit history.

But because nomination metadata is intentionally excluded from semantic measurement, child identity carried only in nomination/query lineage does not survive into the current CAL semantic context.

This is not a defect in the promoted Contract-B 1.2 design. The extension is behaving exactly as governed.

The failure arises if retrieval-query metadata is asked to carry a semantic distinction that downstream CAL must reason over.

### Explicit proposition lineage is now justified

The previous retrieval experiment showed that decomposition can change the evidence world.

This experiment shows a stronger downstream requirement:

> If downstream semantic machinery must know which evidence belongs to which decomposed proposition, that proposition identity must survive as governed semantic identity rather than only as retrieval nomination metadata.

Otherwise a complete two-child state `(6,6)` and a missing-child state `(12,0)` are observationally equivalent to CAL semantic measurement.

### This does not yet prove Contract A owns decomposition

The falsified architecture is specifically:

> original canonical claim + child identity only in EB retrieval-query / nomination metadata.

At least three architectures remain logically possible:

1. Contract A contains explicit parent/child proposition lineage before EB;
2. EB creates governed proposition objects after Contract A and emits them through a downstream contract;
3. a separate explicit decomposition/proposition contract sits between claim intake and evidence construction.

The evidence supports **first-class semantic lineage**, not yet a specific producer.

### Encoding children as ordinary Contract-B claims is only a research witness

The P arm demonstrates that current CAL can preserve the distinction when child identities are canonical claims.

It does not establish that this is the correct production encoding.

Turning one parent into parent + child claim files affects:

- claim counts;
- bundle identity;
- downstream audit cardinality;
- parent/child aggregation semantics;
- potentially Contract C cardinality.

Those consequences must be tested before proposing that encoding.

## FALSIFIED

The following proposition is falsified for systems requiring proposition-level semantic measurement:

> Child decomposition may remain exclusively in retrieval query metadata as long as the parent claim and union evidence set are preserved.

The fixed-evidence collision is a constructive counterexample.

## UNKNOWN

This experiment does not establish:

- which component should produce decomposition;
- whether Contract A itself should contain children;
- whether children should be canonical Contract-B claims;
- how parent verdicts compose from child verdicts;
- whether every composite claim requires decomposition;
- whether child claims should independently reach Contract C;
- production schema/version consequences.

## NEXT

Run one smaller **parent-child audit composition conformance** experiment before hardening Contract A.

Hold fixed:

- parent text;
- child texts;
- child-specific passage sets from this exact snapshot;
- CAL model/machinery.

Compare:

1. auditing only the parent against the union evidence;
2. auditing each child independently against its attributed evidence;
3. a shadow parent composition record that does not invent a verdict rule.

The discriminator is whether child-level audit outputs contain information that cannot be reconstructed from the parent-union audit, and whether current CAL/Contract C has any governed way to represent parent completeness without inventing aggregation semantics.

If child-level states diverge materially and parent composition is not representable, then Contract A should preserve explicit parent/child proposition lineage before the pipeline is hardened, while the exact ownership and downstream composition contract remain separate decisions.
