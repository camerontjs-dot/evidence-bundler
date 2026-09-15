# Evidence Bundler V1 integration candidate

## Classification

**Draft Research Infrastructure / integration-candidate assembly.**

This surface assembles the strongest currently justified Evidence Bundler V1 object for local CAL Pipeline testing. It does not promote a production retrieval default, merge or release Evidence Bundler, alter Contract A or Contract B, or add CAL semantic authority.

Current status:

`IMPLEMENTED_AWAITING_LOCAL_QUALIFICATION`

The status must not be upgraded to `EVIDENCE_BUNDLER_V1_INTEGRATION_CANDIDATE_FROZEN` until the local qualification sequence in `LOCAL-QUALIFICATION.md` passes on one exact branch head and the result is committed without changing the tested candidate bytes.

## Frozen upstream implementation

The branch starts directly from the exact V1 implementation freeze:

- implementation commit: `c4e3f97ec8f0bd36180954c3aa382418925bf947`
- implementation tree: `1d254e38cb0e174635efc7687c2b0ab091aa52b3`

The existing V1 retrieval/package implementation is not rewritten by this candidate assembly. New code is a downstream Contract B projection boundary plus an explicit integration runner.

## Exact integration profile

Profile:

`eb-v1-integration-10x3-rc0`

Configuration:

- candidate depth `10`
- retained K `3`
- chunk max chars `1800`
- chunk overlap chars `80`
- root diagnostic `false`
- deterministic in-repo Okapi BM25
- `k1 = 1.5`, `b = 0.75`
- tokenizer `lowercase_word_v1`
- source scope `all_contract_a_sources`
- query strategy `exact_primary_target_text`
- no semantic reranker
- no query rewrite
- no adaptive K

Canonical configuration identity:

`sha256:5b10d0c29794e80d6876a99e26bcf6ec6a27a4c5165aee78054a6bc32759f4bc`

The generic `V1Config()` default remains `5/3`. This candidate does **not** convert 10/3 into a qualified production default. The dedicated integration runner supplies 10/3 explicitly and the Contract B projection rejects any native package with another configuration.

## Why this profile

The integration profile carries forward the Stage-A 10/3 freeze from Draft PR #78 after reconciling the completed Evidence Bundler research:

- depth 5 can hide required evidence later observed at rank 7;
- depth 10 preserves that candidate history for diagnosis;
- fixed 10/7 recovered deeper evidence but failed the completed burden gate in PR #72;
- fixed 10/7 also failed the preregistered operational-instability gate in PR #74;
- the tested frozen-pool facility-location selectors in PR #77 did not improve over K=3.

Therefore 10/3 is the current integration baseline with known retention misses. It is not asserted to be the theoretically best retrieval profile.

## Native package remains the system of record

The immutable Evidence Bundler V1 native package remains authoritative for:

- Contract A identity;
- proposition and normative lane identity;
- query and retrieval identity;
- requested/searched source aperture;
- candidate order and nomination rank;
- retained/not-retained state;
- explicit admission state;
- source content hash;
- passage content hash and exact offsets;
- configuration identity;
- package identity.

Raw BM25 scores remain outside the native V1 package contract.

## Contract B 1.2 projection

The downstream projection is:

```text
native Evidence Bundler V1 package
        ↓
validate exact eb-v1-integration-10x3-rc0 identity
        ↓
explicit legacy compatibility carrier
        ↓
released Contract B 1.2 bundle
        ↓
projection_receipt.json
```

Released Contract B authority:

- version `1.2.0`
- production lock `c314e53bd91c0736aa4370a364673b069aceb43e`

The projector consumes an already-built native package. It does **not** rerun retrieval, rank passages, select K, change admission, or call CAL.

### Compatibility-only state

Contract A 2.0 does not own every legacy field still required by the locked Contract B core. The carrier therefore supplies those values explicitly rather than silently inventing them inside the adapter.

Carrier values include legacy:

- claim type/workflow/support scalars and booleans;
- source bibliographic/trust/retrieval metadata;
- passage section/paragraph/extraction metadata;
- Contract B manifest timestamps/operator/validation pointer/sign-off requirement;
- legacy Contract B audit-policy payload.

The carrier explicitly declares that it supplies neither Contract A authority nor CAL semantic authority and that semantic use is unauthorized.

The audit-policy compatibility payload is pinned to `cal-rules-v1.2.0` because the maintained CAL Contract B consumer fails closed on any other B1.2 audit-policy identity.

## Full candidate history in B

Every native depth-10 candidate passage is emitted as a canonical Contract B passage record so the B1.2 factual-context extension can preserve the complete candidate history.

For retained candidates, B `review.decision` equals the native admission state: `accepted`, `rejected`, or `needs-review`.

For native `not_retained` candidates, V1 correctly records `admission_state = not_applicable`, but B1.2 has no `not_applicable` review decision. The projection therefore uses:

- B `review.decision = needs-review` only as a compatibility encoding;
- `review.native_admission_state = not_applicable` to preserve the native state;
- `nomination.selection_state = not_retained` to preserve the actual loss stage.

This cannot admit evidence semantically because the released CAL B1.2 consumer admits only history links whose `review.decision == accepted`.

Canonical claim `evidence_passages` contain only native accepted passages. Rejected, unresolved, and not-retained candidates remain recoverable in canonical passage records plus factual-context history.

## Projection receipt

`projection_receipt.json` is not a new contract and carries no semantic judgment. It binds:

- frozen V1 implementation commit/tree;
- integration profile/config hash;
- native package SHA;
- compatibility carrier SHA;
- Contract B version/production lock;
- B bundle ID/tree hash;
- every native candidate relation to its B proposition/source/passage representation;
- native selection/admission state and any B compatibility encoding.

## Known limitations preserved

This candidate intentionally preserves:

- deep required evidence that may be nominated at ranks 4-10 but not retained at K=3;
- lexical hard-negative pressure;
- long-context BM25 dilution;
- bounded candidate depth rather than a completeness claim;
- explicit `needs-review` admission states;
- unsupported downstream CAL semantic families as legitimate fail-closed outcomes.

These are pipeline observations to learn from, not reasons to mutate the profile mid-run.

## Nonclaims

This work does not establish:

- universal retrieval recall;
- evidence completeness;
- source truthworthiness;
- a qualified production retrieval default;
- CAL semantic correctness;
- Contract C readiness;
- Decision Engine readiness;
- Authorization or automatic action;
- release or merge readiness.

## Current execution constraint

Hosted GitHub runner usage is unavailable for this project until the user's quota resets. This branch therefore includes deterministic local qualification tests and an exact local handoff rather than claiming an unexecuted hosted result.

No green qualification result should be inferred from code review or syntax compilation alone.
