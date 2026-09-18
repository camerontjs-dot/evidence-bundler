# Gate-informed Evidence Bundler design V0

## Classification

Research/design only.

This branch changes no Evidence Bundler retrieval, ranking, selection, admission, Contract B, CAL, release, or production behavior.

Tracking issue: #91.

## Exact current authorities

Evidence Bundler protected `main` at branch creation:

`c26fbd4bfc8ba5c2604a784af158594b59fcae37`

Frozen EB V1 integration candidate:

`4e1f6fe00e7c350b28f52bfea14f1f8988847884` in Draft PR #79.

Typed selector RC1 terminal result:

`80ed2cad8a25dec268d2830f466cfff8126a90a0` in Draft PR #90, disposition `FALSIFIED`.

Relevant Proposition Authoring evidence currently includes:

- capability-complete shadow subject `e29a165b682d060f5dc2a0f3c7d64a7f29b172b4`;
- 41-field sweep in PR #39, where `claim.expected_evidence_forms`, EvidenceGate evidence-form characterization, and evidence-form preflight survived the frozen baseline, but authority remained `IMPLEMENTED_SHADOW`;
- bounded taxonomy successor `e30773f24719b835b5efc0640b705a3e6a68a2be`, 8/8 on its frozen comparative/status matrix, explicitly not routing authority;
- Gate V1 RC2 subject `8c10bd703a747f5448c424fbe7ce1e2521b7647e`, currently surface-falsified in PR #46 with a bounded repair set.

The design therefore does not depend on RC2 becoming the final Gate identity.

## Problem

EB V1 currently retrieves with exact proposition text and deterministic BM25, keeps depth 10 candidate history for the integration profile, and retains K=3.

Known limits include:

- useful evidence can appear below rank 3;
- generic widening to K=7 failed burden and operational gates;
- frozen-pool facility-location selection did not improve over K=3;
- typed selector RC1 lost required-evidence coverage versus semantic-only.

The next design should not add another blended ranking score without isolating what additional information it contributes.

## Working hypothesis

A Gate can describe the shape of the verification problem without prescribing retrieval behavior.

Evidence Bundler can then own the causal translation from that description into a retrieval or selection plan.

The proposed layers are:

```text
ClaimGate / EvidenceGate
        |
        | only separately qualified descriptive hints
        v
EB Hint Intake + Authority Firewall
        |
        v
Evidence Shape Requirement Expression
        |
        v
EB-owned Requirement Compiler
        |
        +--> selection coverage plan
        |
        +--> later, separately qualified retrieval plan
        v
retrieval / nomination / selection
        |
        v
native EB package -> Contract B
```

## Governing distinction

An evidence-shape requirement is not a statement that some evidence form is sufficient to prove a proposition.

It is a bounded retrieval/coverage description such as:

- one of several forms may be useful to seek;
- multiple distinct evidence forms may need representation;
- a form may be optional or corroborative;
- the required shape may be unknown.

CAL remains the proposition-relative semantic judge.

## Immediate stopping point

This branch should end with:

1. a stable design vocabulary;
2. an inspectable Gate-to-EB authority boundary;
3. a draft evidence-shape expression;
4. an EB-owned compilation model;
5. a preregisterable first experiment using fixed candidate pools.

No causal implementation should begin on this branch.


## Revision after completed Gate pressure

The Gate pressure programme is now treated as completed evidence for this design revision.

### Field-pressure evidence

Exact capability subject:

`e29a165b682d060f5dc2a0f3c7d64a7f29b172b4`

Frozen 118-case field sweep:

- 26 `SUPPORTED_BASELINE`;
- 14 `FALSIFIED_BASELINE`;
- 1 `INCONCLUSIVE`;
- all 41 registered fields exercised;
- deterministic replay PASS;
- authority unchanged.

This does **not** mean only the 26 passing concepts remain in the research design.

The 14 failures mostly identify representation or aperture problems:

- semantic names backed by surface proxies;
- too-narrow parsing aperture;
- missing typed temporal/jurisdiction relations;
- relation/input hygiene defects.

The design therefore keeps those concepts in repaired or split form for shadow pressure testing.

### Gate RC2 boundary-pressure evidence

Exact RC2 pressure subject:

`8c10bd703a747f5448c424fbe7ce1e2521b7647e`

Frozen 44-case pressure result:

- 27 `SUPPORTED_SURFACE`;
- 14 `FALSIFIED_SURFACE`;
- 3 `INCONCLUSIVE_DESIGN`;
- deterministic replay PASS.

Supported architectural invariants include:

- claim-independent EvidenceGate identity/output;
- source/order invariance;
- byte-sensitive and source-ID-sensitive evidence-world identity;
- source origin separated from pipeline retention locators;
- exact reconstruction inputs;
- downstream authority flags remaining false;
- preserved Contract A bytes.

The four falsified mechanisms are preserved as design constraints:

1. incomplete identifier/date/regulatory-citation masking;
2. unconstrained source-URI field;
3. Python validators weaker than frozen JSON Schemas;
4. no canonical cross-artifact bundle verifier.

Three design questions remain open:

1. whether media type participates in intrinsic evidence-world identity;
2. whether `origin_type` uses a finite vocabulary;
3. how to prevent free-text `authority_basis` from smuggling proposition-relative semantics.

### External integration counterexample

A later CAL Pipeline run showed Proposition Authoring can emit Contract A with a source media type not permitted by released Contract A 2.0.0.

This is treated as an upstream producer-conformance defect.

The EB design must not widen Contract A or EB to make that invalid producer output pass.

## Wide research posture

The research carrier is intentionally larger than the expected final consumer surface.

See:

- `BROAD-SHADOW-SURFACE.md`;
- `SHADOW-FIELD-REGISTRY.json`;
- `WIDE-PRESSURE-PROGRAMME.md`.

The field registry currently contains a broad set of supported representations, repaired concepts, design hypotheses, EB-owned candidate descriptors and boundary mechanics.

Everything defaults to shadow visibility.

The aim is to pressure-test and delete.

Not to infer the final feature set from intuition.
