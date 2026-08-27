# Research brief 01: Contract B seam shadow

**Status:** preregistered shadow experiment, not a production contract decision  
**Branch:** `research/contract-b-seam-shadow`  
**Upstream basis:** Apparatus Contracts issue #1, `Research: define the EB → Contract B → CAL decision-state boundary`  
**Downstream basis:** Claim Audit Lab PR #1, `Research: test relation-preserving downstream evidence decisions`  
**Parent spike:** `annex22-bundle-shape-spike`

## Research question

What is the **smallest state that must cross Evidence Bundler → Contract B → CAL** so that CAL does not have to invent or rediscover evidence-world facts, while Evidence Bundler does not become a proposition-specific semantic auditor?

This branch does not change the released C-B schema, production finalizer, retrieval behavior, CAL behavior, thresholds, or verdict rules.

## Evidence motivating the experiment

### Observed in Apparatus Contracts

The canonical design issue separates three categories that must not collapse:

1. observed / mechanically supplied facts;
2. admission / evidence-preparation judgments;
3. proposition-specific audit judgments.

It also records the preservation invariant:

> An admitted contribution may become non-deciding for a proposition or policy without being removed from the audit record.

And the boundary rule:

> `EB rejected` must not become a synonym for `CAL non-deciding`.

The issue explicitly says **do not change v1.0.0 yet**. It proposes testing current C-B, C-B plus minimal factual context, and C-B plus the full CAL research sidecar before making a schema amendment.

### Observed in CAL research

CAL PR #1 Rung 04 found that a realistic three-snapshot case needed explicit state for proposition-specific eligibility, semantic validity, aperture/completeness, temporal applicability, and authority/supplier applicability. The current Contract-B-shaped payload does not encode those states, so the research run supplied them through a labeled sidecar rather than inventing defaults.

That is evidence of an interface gap. It does **not** yet tell us which missing fields belong upstream and which should remain CAL assessment receipts.

### Observed in the Annex 22 shape spike

The Annex 22 fixture exposed a separate but compatible need for structured evidence-world facts such as document status, jurisdiction, version, source dates, typed anchors, claim origin, retrieval coverage, and immutable source identity. It also showed that nomination roles must not control CAL's semantic measurement.

## Candidate seam

The working seam is:

```text
Evidence Bundler
  passages + provenance
  mechanically observed/source-declared context facts
  retrieval nomination provenance
  admission/evidence-preparation state
  corpus/retrieval coverage facts
          │
          ▼
Contract B
  typed + integrity-sealed measurement-ready handoff
  no proposition-specific semantic verdicts invented here
          │
          ▼
CAL measurement view
  admitted evidence + evidence-world facts
  nomination scores/roles blinded from semantic decision path
          │
          ▼
CAL assessment receipts
  proposition-specific relation
  semantic validity
  temporal applicability
  authority/supplier applicability
  completeness conclusion
  decision participation
          │
          ▼
CAL decision trace / verdict
```

### Facts that are candidates to cross

These are candidate **facts**, not audit conclusions, when provenance-bound and mechanically extracted or explicitly source-declared:

- source identity and content hash;
- document status, issue/effective dates, version labels;
- source-declared system/model/version identifiers;
- source-declared supplier identity/status;
- event/validation/incident dates;
- passage text and typed anchors;
- retrieval method/run/rank/candidate lane as nomination provenance;
- admission decision and review basis;
- corpus/search scope and candidate/review/admission counts;
- explicit unknowns.

### Judgments that should not cross as authoritative EB facts

These remain proposition-specific CAL assessments in the current hypothesis:

- support/refutation relation;
- semantic validity for the obligation;
- temporal applicability to the audited proposition/state;
- authority/supplier eligibility for the proposition;
- whether aperture facts justify a completeness conclusion;
- final decision participation;
- verdict or abstention.

A retriever may preserve a `hypothesized_role`, but it is nomination provenance, not an audit relation.

## Strongest assumption

The seam depends on EB admission being operationally narrower than audit judgment.

EB review should ask approximately:

> Is this a faithful, traceable, sufficiently contextualized candidate that belongs in the auditor's evidence aperture?

It should not ask:

> Should this contribution decide this proposition?

If reviewers cannot make the first judgment without reliably importing the second, the proposed seam is unstable.

## Shadow fixture

`examples/contract-b-seam/tri-repo-fixture.yaml` contains one current-state validation claim with:

- stale pre-change validation evidence;
- a post-change incident;
- supplier qualification evidence;
- current-state validation;
- one rejected marketing candidate;
- provenance-bound source/context facts;
- retrieval/admission state;
- coverage facts;
- a clearly separated `cal_research_sidecar` containing proposition-specific judgments.

The sidecar is deliberately present in the research fixture so metamorphic tests can prove that changing downstream judgments does not change the proposed EB/Contract-B handoff.

## Preregistered variants

### V0: current-C-B-shaped projection

Approximate the information categories available in the current handoff: claim, admitted passage text/source references, and current trust-style metadata. Deliberately omit the new factual-context and coverage extensions.

This variant is a **projection for the experiment**, not a replacement implementation of the canonical Pydantic C-B model.

### V1: minimal factual-context handoff

Add only:

- provenance-bound context facts;
- complete retrieval/admission ledger;
- coverage/search facts;
- immutable claim/source/passage identities.

Do **not** include proposition-specific CAL assessments.

### V2: full research-sidecar handoff

V1 plus all proposition-specific CAL assessment state from the Rung-04-style sidecar.

V2 is intentionally over-complete. It is a comparison condition, not the desired outcome.

## Test rungs

### Rung 1: ownership separation

V1 must contain every preregistered mechanical fact and no proposition-specific audit keys. V0 is expected to be missing at least some required facts. V2 is expected to contain audit judgments.

### Rung 2: downstream-judgment invariance

Mutating only the CAL research sidecar must not change the V1 handoff hash or CAL measurement-view hash.

**Falsifier:** V1 changes when a downstream semantic/eligibility judgment changes.

### Rung 3: evidence-fact sensitivity

Mutating a provenance-bound mechanical fact, such as a source-declared system version, must change V1 and the CAL measurement view.

**Falsifier:** a fact CAL may need can change without changing the handoff.

### Rung 4: nomination blinding

Changing retrieval rank, score, or hypothesized candidate role may change the auditable V1 handoff because nomination provenance is retained, but must not change the CAL semantic measurement view.

**Falsifier:** nomination metadata changes the semantic measurement input while admitted evidence content is fixed.

### Rung 5: non-destructive decision filtering

The stale pre-change validation passage must remain in the retained handoff and pre-assessment CAL measurement view even though the research sidecar marks it non-deciding for the current-state proposition.

**Falsifier:** EB removes admitted evidence because a downstream temporal/authority/validity assessment says it is non-deciding.

### Rung 6: rejected-candidate recoverability

A rejected candidate should not enter the CAL admitted-evidence view. The experiment separately tests whether its nomination/admission record remains recoverable in V1.

This does **not** decide that canonical C-B must ship rejected candidate contents. It measures the provenance difference between retaining the ledger and retaining only aggregate coverage/finalization provenance.

### Rung 7: aperture fact / completeness judgment separation

V1 must carry corpus/search/candidate/review/admission facts but no `complete=true` style audit conclusion.

CAL can later assess whether those facts justify a completeness conclusion.

## Decision criteria

Support the candidate seam if all of the following hold:

- V1 preserves the objective facts missing from V0;
- V1 contains no proposition-specific audit judgments;
- sidecar mutations are invisible to V1;
- mechanical-fact mutations are visible to V1;
- nomination mutations are retained for auditability but blinded from CAL semantic measurement;
- admitted-but-non-deciding evidence is retained;
- aperture facts survive without an upstream completeness verdict.

Do **not** promote the seam if:

- CAL must rediscover facts EB already knows;
- factual context cannot be represented without proposition-specific judgment;
- an essential CAL decision rule has been disguised as a fact;
- preserving provenance requires copying the entire draft EB state into C-B;
- admission review itself proves inseparable from semantic validity/eligibility judgment.

## Explicit unknowns

1. Whether rejected candidate content must ship in canonical C-B or whether hash-bound finalization provenance is sufficient.
2. Whether `source_trust_level` is useful evidence metadata, an assessment, or dangerously ambiguous between global trust and proposition-specific authority.
3. Which context facts deserve generic typed predicates versus dedicated source/profile fields.
4. Whether CAL assessment receipts should be a separate immutable artifact or a downstream extension bound to the C-B hash.
5. Whether the candidate seam survives a real cross-repository CAL execution rather than this structural shadow.

## Next gate after this branch

If this structural shadow passes, the next test should be a **real tri-repository round trip** using one frozen fixture:

1. Evidence Bundler emits V0/V1/V2 artifacts.
2. Apparatus Contracts validates integrity and permitted field ownership.
3. CAL derives the same proposition-specific assessment inputs from V1 as from the full research sidecar where the information is genuinely factual, while failing explicitly rather than inventing defaults where judgment is required.

Only after that should we decide whether the canonical contract needs a small factual-context extension, a receipt-bound sidecar, or a major-version boundary.