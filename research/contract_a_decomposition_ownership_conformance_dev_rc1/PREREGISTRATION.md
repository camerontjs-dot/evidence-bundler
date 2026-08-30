# Contract A Decomposition Ownership / Downstream Conformance Dev RC1

Status: AUTHORIZED BOUNDED RESEARCH INFRASTRUCTURE EXECUTION

## Question

With retrieval held byte-for-byte fixed, does representing decomposition only as retrieval-query lineage preserve the same downstream semantic information as representing child propositions as first-class canonical claims?

This experiment does not authorize a Contract A change.

## Live authority

- Evidence Bundler main at start: `6011789957f3294f97bff260069cfb5bb1c5772f`
- parent decomposition experiment PR #43 result head: `0e4bed62553ebb6aef6a1b485664fb80cc78c802`
- decisive frozen retrieval source SHA: `55d158f829f4aad1ed8ad69b19d9e39d445c953d`
- decisive workflow run: `33286415682`
- raw retrieval SHA256: `b7522a147f1dccd1614bb8dcb4565b8a8834bee4cf2d47695befeb311ebd6680`
- fixed F10 A1 snapshot SHA256: `8dbedd537c024c4a624f21abd5fa11536ddfe558000f3a9366584c30c045e31c`
- Claim Audit Lab live main: `53f0885b111676794d1bd20e10b91aa58b07e9d4`
- Apparatus Contracts live main: `00bdf9546a877f9f6c1d7fd227fd959e1d7aa99e`

## Frozen evidence world

Use only claim-037 A1 from the previous experiment:

- parent claim: Morrow-2 quarantine release requires both a temperature check below 3.3 C and a signed identity match before movement;
- two frozen meaning-preserving child propositions;
- exact pinned semantic equal-total-budget retrieval;
- 12 fixed retrieved paragraph identities;
- actual child query coverage vector: 6 passages for child 1 and 6 passages for child 2.

No retrieval is rerun.

## Arms

### Q — query-lineage representation

One canonical Contract-B claim remains the parent claim.

The Contract-B 1.2 factual-context history records exact child query identity, text, rank and score as nomination metadata while every admitted passage remains linked to the parent canonical claim.

CAL's current promoted semantic-context projection is then applied unchanged.

### P — proposition-lineage representation

The parent and both child propositions are canonical Contract-B claims.

Child origin lineage records the parent and decomposition identity.

Each admitted passage history link names the child proposition whose frozen query retrieved it.

CAL's current promoted semantic-context projection is applied unchanged.

This is a research shadow representation, not a proposal to promote three-claim encoding as the final contract.

## Lineage-collision mutation

Create a counterfactual attribution mutation without changing:

- parent text;
- child texts;
- retrieved passage union;
- passage bytes;
- source identities;
- number of admitted passages.

Actual attribution has child coverage `(6, 6)`.

Mutation M assigns every admitted passage to child 1, producing child coverage `(12, 0)`.

This is deliberately not claimed to be a plausible retriever output. It is a metamorphic information-preservation test.

## Critical falsifier

If Q and Q+M produce different CAL semantic contexts, query-lineage representation preserves the child distinction needed by current CAL semantic measurement and first-class proposition identity is not established by this test.

If Q and Q+M collide but P and P+M remain distinguishable, current query-lineage-only representation loses proposition-level attribution before semantic measurement.

## Additional checks

1. Current CAL Contract-B strict claim model must reject an ungoverned `propositions` field added to one canonical claim.
2. Q intake/audit ledger must preserve nomination lineage.
3. Q semantic context must exclude nomination metadata, as required by promoted Contract B 1.2.
4. P must expose child-specific admitted passage sets.
5. Both arms must preserve the identical fixed passage union.
6. No support/refutation/verdict/completeness conclusion is written into Contract B.

## Interpretation boundary

A collision in Q is evidence that the current Contract-B-to-CAL semantic context cannot carry child attribution when children exist only as nomination/query metadata.

It is not by itself proof that Contract A must own decomposition. Other explicit, governed proposition-lineage mechanisms could solve the information loss.

The promotion question remains: what is the smallest explicit seam that preserves the distinction?
