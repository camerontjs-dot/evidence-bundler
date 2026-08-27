# Results 01: Contract B seam shadow

**Status:** structural shadow passed; cross-repository execution still required  
**Branch:** `research/contract-b-seam-shadow`  
**Draft PR:** #4  
**Certified push run:** GitHub Actions run `33029501232`  
**Head:** `69d373f11d037cae1f5ca077530214b09346b74c`

## Observed test result

The targeted research workflow completed successfully on the branch head:

- **26 passed in 0.71s**
- Ruff: **All checks passed**

The 26 tests comprise:

- 11 Contract-B seam metamorphic/ownership tests;
- 7 current C-B production-model surface tests;
- 8 Annex 22 parent-spike tests.

No released Evidence Bundler model, finalizer, retrieval path, canonical C-B schema, contract version, or CAL behavior was changed.

## What is now observed

### O1. The current C-B model is closed to undeclared context state

`StrictBaseModel` uses `extra="forbid"`. The current contract cannot silently carry new factual-context fields without an explicit schema change.

### O2. Current C-B is apparatus-bound

The real `ClaimAuditUnit` requires scaffold-specific state including workflow condition, task id, scaffold support status/strength/fidelity, counterevidence state, and downgrade state.

It also contains an `audit` block intended for CAL-populated fields.

### O3. Current C-B lacks several evidence-world surfaces exposed by the Annex 22 and Rung-04 work

The real model surface does not contain general fields for:

- claim origin;
- atomicity;
- retrieval/admission coverage;
- nomination/admission records;
- document status;
- jurisdiction;
- version label;
- effective date;
- generic provenance-bound context facts;
- representation-bound typed anchors.

This is a representational observation, not yet a conclusion about the final schema.

### O4. Current C-B contains a semantic lane split

`ClaimAuditUnit` has distinct `evidence_passages` and `counterevidence_passages` containers. The Annex 22 parent spike separately established that CAL's current adapter consumes these lanes as support/counter scopes.

Therefore the current handoff is not audit-neutral by construction.

### O5. Current C-B pins downstream audit configuration in the bundle manifest

The real `BundleManifest` contains audit-config and validation-set version/hash fields. This confirms the current handoff is an apparatus measurement package, not merely an auditor-independent evidence identity package.

## What the shadow fixture demonstrated

### S1. A minimal factual-context handoff can preserve the preregistered evidence-world facts without CAL judgments

The V1 `minimal_context` projection preserved every preregistered mechanical/source-declared fact in the fixture while containing none of the proposition-specific audit keys:

- support/refutation relation;
- semantic validity;
- temporal applicability;
- authority applicability;
- decision participation;
- completeness conclusion;
- verdict.

### S2. Downstream judgment mutations are invisible to the handoff

Changing every CAL research-sidecar assessment did not change either:

- the V1 handoff hash; or
- the CAL pre-assessment measurement-view hash.

This supports the ownership boundary: proposition-specific judgments can vary without rewriting evidence identity.

### S3. Evidence-world fact mutations are visible

Changing a provenance-bound source-declared system version changed both the V1 handoff hash and CAL measurement-view hash.

This supports the complementary rule: a fact CAL may legitimately need cannot change invisibly.

### S4. Nomination provenance can be retained without controlling semantic measurement

Changing retrieval rank, scores, and candidate-role hypotheses changed the V1 handoff hash because nomination provenance is auditable, but did **not** change the CAL measurement-view hash.

This is the desired asymmetry:

> preserve the retriever's history; blind its semantic guess.

### S5. Admitted-but-non-deciding evidence survives

The fixture's stale pre-change validation contribution remained present in the retained handoff and CAL pre-assessment evidence view even though the separate CAL sidecar marked it temporally stale and non-participating for the current-state proposition.

This supports the preservation invariant:

> admitted evidence can become non-deciding downstream without being erased upstream.

### S6. EB rejection remains distinct from CAL non-decision

The marketing candidate is explicitly rejected for the narrow EB admission basis and does not enter the CAL admitted-evidence view. Its nomination/admission record remains recoverable in the V1 research ledger.

This demonstrates that the two concepts can be represented separately. It does **not** yet prove canonical C-B must ship rejected candidate content.

### S7. Aperture facts can cross without a completeness verdict

The CAL measurement view retained:

- search scope;
- closed-world flag for the supplied fixture;
- candidate count;
- reviewed count;
- admitted count;
- limitations.

It did not contain the sidecar's `completeness_conclusion`.

This supports the split proposed in Apparatus Contracts issue #1:

> Contract B can supply corpus/retrieval facts; CAL decides whether those facts justify a completeness conclusion.

## Epistemic compression

### Supported by current evidence

The cleanest seam tested so far is:

**Evidence Bundler / Contract B owns evidence-world state**

- immutable claim/source/passage identity;
- provenance and integrity;
- mechanically observed or source-declared context facts;
- nomination provenance;
- admission/evidence-preparation state;
- corpus/retrieval/aperture facts;
- explicit unknowns.

**CAL owns proposition-specific audit state**

- semantic relation;
- semantic validity;
- temporal applicability;
- authority/supplier applicability;
- completeness assessment;
- decision participation;
- verdict/abstention.

The CAL-facing measurement view may be narrower than the retained handoff: it can blind nomination ranks/scores/roles and reviewer notes while preserving admitted evidence and evidence-world facts.

### Inference

The interface gap is now more strongly supported than after the Annex 22 spike alone. Current C-B cannot express the tested factual-context state without a declared schema extension, and its present shape carries both upstream apparatus state and downstream CAL configuration.

A **minimal factual-context extension plus downstream assessment receipts** is therefore a credible design candidate.

### Not yet established

We have **not** shown that the V1 candidate contains every fact a real CAL execution needs.

We have also not shown that generic `context_facts` is the best final representation. Dedicated typed fields may be clearer for stable concepts such as document status, jurisdiction, version, and effective dates.

### Strongest remaining assumption

EB admission can be kept narrow enough that reviewers decide evidence preparation fitness without covertly deciding proposition-specific temporal, authority, or semantic validity.

### Unknowns that still matter

1. Must rejected candidate contents cross canonical C-B, or is a hash-bound omission/finalization receipt enough?
2. What exactly is `source_trust_level`: global source metadata, attributed assessment, or an ambiguous proxy for authority?
3. Which factual context deserves dedicated typed fields versus a generic fact/attribute structure?
4. Should CAL assessment receipts be a separate immutable artifact bound to the evidence-bundle hash?
5. Can real CAL consume the minimal handoff and reproduce the Rung-04 sequence without invented defaults?

## Next discriminating experiment

Run a **real tri-repository fixture** rather than another internal shape test.

For one frozen realistic case:

1. Evidence Bundler emits three artifacts from identical evidence:
   - current C-B;
   - C-B + minimal factual context;
   - C-B + full research sidecar.
2. Apparatus Contracts validates identity, integrity, preservation, and ownership constraints.
3. CAL consumes each artifact through an experimental adapter.
4. CAL must fail explicitly when a required fact/judgment is absent rather than inventing a default.
5. Compare the minimal variant against the full sidecar to identify which state is truly necessary at the boundary.

### Falsification criteria

Reject or revise the candidate seam if the real round trip shows any of the following:

- CAL repeatedly has to rediscover basic facts EB already had;
- V1 cannot provide enough evidence-world state without embedding proposition-specific judgments;
- nomination/admission metadata changes semantic output despite blinding;
- important historical evidence must be destructively filtered upstream to make CAL work;
- two CAL consumers cannot derive the same assessment inputs because an essential decision rule was incorrectly treated as a fact;
- the full sidecar is actually required because the proposed factual/judgment distinction is not operationally stable.

## Current disposition

- **ADOPT for further testing:** preserve admitted evidence non-destructively.
- **ADOPT for further testing:** EB nomination/admission is not CAL semantic/eligibility judgment.
- **ADOPT for further testing:** aperture facts are distinct from a completeness conclusion.
- **SUPPORTED CANDIDATE:** minimal factual-context handoff plus separate CAL assessment receipts.
- **UNRESOLVED:** rejected-candidate shipping, `source_trust_level`, final context-fact typing.
- **DO NOT CHANGE canonical C-B yet:** execute the real tri-repository round trip first.
