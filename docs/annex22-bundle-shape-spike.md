# Annex 22 evidence-bundle shape spike

**Status:** exploratory design spike, not an accepted contract decision  
**Branch:** `annex22-bundle-shape-spike`  
**Purpose:** use the European Commission draft GMP Annex 22 as a demanding regulatory corpus to discover what a general evidence bundle must represent before changing C-B or downstream CAL interfaces.

## Source status

The source used for this spike is the European Commission consultation draft **Annex 22: Artificial Intelligence**. The consultation opened on 7 July 2025 and closed on 7 October 2025.

Official consultation page: https://health.ec.europa.eu/consultations/stakeholders-consultation-eudralex-volume-4-good-manufacturing-practice-guidelines-chapter-4-annex_en

Official draft PDF: https://health.ec.europa.eu/document/download/5f38a92d-bb8e-4264-8898-ea076e926db6_en?filename=mp_vol4_chap4_annex22_consultation_guideline_en.pdf

This is a **draft consultation document**, not a final Annex currently listed in EudraLex Volume 4. It is being used as a schema stressor, not as a claim that its provisions are presently binding GMP.

## What we are trying to learn

The question is not "can Evidence Bundler retrieve Annex 22?" It is:

> Can a bundle faithfully preserve everything CAL or a human auditor needs to evaluate a claim without silently collapsing source identity, claim origin, candidate selection, human admission, coverage state, or downstream audit judgment?

If Annex 22 exposes a representational gap, first test whether the bundle shape is incomplete before teaching CAL to infer missing structure.

## Current C-B is carrying three different things

The current C-B contract was designed as an apparatus handoff from Scaffold Harness -> Evidence Bundler -> Claim Audit Lab.

Today a `ClaimAuditUnit` carries:

1. **Upstream experiment state**: scaffold support status, claim strength, extraction fidelity, counterevidence flags, workflow condition, task id.
2. **Evidence**: passage text, source id, offsets, trust level.
3. **Downstream audit surface**: null `audit.*` fields that CAL later populates.

The bundle manifest also carries CAL audit-config and validation-set pins.

That is coherent for the original evaluation apparatus. It is not a clean domain-level evidence package because evidence identity depends on both who produced the claim and which auditor will consume it.

### Working separation

A general workflow should distinguish:

- **Evidence bundle**: claims, sources, passages, candidate links, admission/review state, coverage, provenance, integrity.
- **Audit invocation**: CAL engine/rules/config selected for one audit run.
- **Audit result**: verdicts, traces, signals, and reviewer disposition.

The evidence bundle should not need CAL result fields to exist, and CAL should not need scaffold judgments to audit it.

## A second problem: semantic leakage into the auditor

The original spike assumed a reviewed claim-passage link should carry an authoritative relation such as `supports`, `contradicts`, or `qualifies`. Inspecting CAL shows that is unsafe as a default boundary.

CAL's C-B adapter constructs explicit `support_excerpt_ids` and `counter_excerpt_ids` from the two C-B passage containers. The scoped matcher then searches those lanes differently. That means the current C-B shape is not merely describing provenance; it can tell the auditor which semantic lane a passage belongs to before CAL measures the relationship itself.

That may be legitimate for replaying the original apparatus, but it is a poor default for an independent evidence audit.

### Revised boundary

A claim-passage link may preserve a retriever's **hypothesized role** as provenance, but that hypothesis is not an evidence verdict.

Human review should answer a narrower admission question such as:

> Is this passage relevant enough, and is the excerpt sufficient enough, to place in front of the auditor?

It should not have to pre-decide whether the passage entails or contradicts the claim. A CAL-facing view should ignore retrieval role labels and provide the admitted passages without support/counterevidence preclassification.

This gives us four epistemic layers instead of two:

`retrieved candidate -> review-admitted passage -> CAL semantic relation -> CAL verdict`

Those must not silently collapse into one field.

## Annex 22 stress cases

The wording below is compact paraphrase for schema testing, not a substitute for the source document.

| Case | Annex area | Schema pressure |
|---|---|---|
| A | Scope | A source can be primary yet still draft, scoped, and inapplicable to some model classes. |
| B | Intended use | One clause can contain several linked obligations, limitations, roles, and timing conditions. |
| C | Acceptance criteria | A requirement can depend on subgroup-specific criteria and comparison with a baseline process. |
| D | Test data | One conclusion may require several source locations rather than one passage. |
| E | Data independence | A general rule can have a procedural fallback that changes its interpretation. |
| F | Explainability | A requirement and the required review of that requirement can be distinct facts. |
| G | Confidence | Requirements may be conditional and may define an explicit undecided outcome. |
| H | Operation | One lifecycle claim can span change control, configuration, monitoring, drift, and human review. |

The fixture also contains four negative controls: no candidates, all candidates rejected, partial review, and a draft-status limitation.

## Representational requirements exposed by Annex 22

### R1. Source status is structured metadata

A consumer must be able to distinguish at least:

- draft / consultation / final / superseded / unknown status
- publication or issue date when known
- version or edition when known
- jurisdiction and issuing authority when relevant
- access time and immutable content hash

`source_type=regulatory_guidance` plus `trust_level=primary` cannot distinguish a primary consultation draft from a primary effective requirement.

Source quality or authority judgments should be separately attributed assessments, not smuggled into identity fields.

### R2. Anchors are typed and can be multi-modal

Character offsets alone are fragile for PDFs because an offset is against an extracted representation, not the original page artifact.

A passage should be able to carry several anchors, for example:

- clause / section id
- page number
- heading path
- paragraph index
- character span against a named and hashed extracted-text representation

The bundle must say which representation an offset refers to.

### R3. Claim origin is different from audit evidence

For a requirement extracted from Annex 22, the source location that **generated the claim** is not automatically proof that a separate target system complies with that claim.

Claim origin therefore needs its own lineage:

- external assertion
- source-derived / normalized claim
- multi-location derived claim
- generated audit question

Origin provenance must not be mistaken for support evidence.

### R4. Claim-passage links record selection provenance, not CAL's answer

A passage's relationship to a claim is claim-relative, so claim-passage links are still useful. But the durable link should distinguish:

- **nomination state**: how and why retrieval surfaced the passage
- **admission state**: whether review allowed it into the audit aperture
- **audit semantics**: entail / contradict / qualify / neutral, determined downstream

The first two belong in Evidence Bundler. The third belongs to CAL's trace/result unless a separately-attributed human semantic annotation is intentionally being stored for research.

### R5. Retrieval nomination and human admission remain distinct

A link can contain:

- `nomination`: method, query/run, rank, scores, matched child, `hypothesized_role`
- `review`: accepted/rejected/needs-review/insufficient-excerpt, review basis, reviewer, timestamp, notes

The review basis should be explicit, for example `audit_relevance_and_excerpt_sufficiency`.

A CAL-facing adapter should ignore `hypothesized_role`. Retrieval nominates; review admits; CAL judges semantic support.

### R6. Coverage state is first-class evidence about the evidence process

The bundle should distinguish:

- no candidates retrieved
- candidates retrieved but all rejected
- review incomplete
- admitted evidence exists but may be partial
- source/search scope limited

An empty `evidence_passages` array cannot tell those histories apart.

### R7. Composite claims need an escape hatch

Annex 22 clauses often combine actor, action, condition, timing, exception, and documentation requirements.

Do not build a full regulatory ontology prematurely. The schema should at minimum preserve:

- `atomic | composite | unknown`
- one or more origin anchors
- parent/child claim lineage if decomposition occurs

This lets extraction improve later without changing passage identity.

### R8. Audit configuration and results are not evidence identity

`audit_config.yaml`, `validation_set_ref.yaml`, and mutable/null `audit.*` fields should not be required members of a general evidence bundle.

An audit-run package can reference the immutable evidence-bundle hash and add the selected CAL configuration. An audit-result package can reference both.

## Draft v2 conceptual shape

Field names are not accepted contract yet.

```text
evidence-bundle-{bundle_id}/
  bundle_manifest.yaml
  claims/
    {claim_id}.yaml
  sources/
    {source_id}/
      source_profile.yaml
      passages/
        {passage_id}.yaml
  links/
    {link_id}.yaml
  coverage/
    {claim_id}.yaml
  CONTRACT_VERSION
  SHA256SUMS
```

### `bundle_manifest.yaml`

```yaml
bundle_id: eb-...
schema_version: "2.0.0-draft"
created_at_utc: ...
purpose: claim_support_audit
scope:
  closed_world: true
  source_selection_basis: supplied_corpus
  source_ids: [...]
generator:
  name: evidence-bundler
  version: ...
  config_hash: sha256:...
integrity:
  source_set_hash: sha256:...
  bundle_hash: sha256:...
transformations: [...]
review_state: reviewed | partial | unreviewed
```

### `claims/{claim_id}.yaml`

```yaml
claim_id: clm-...
claim_text: ...
claim_form: assertion | normative | definition | scope | other
atomicity: atomic | composite | unknown
origin:
  kind: external | source_derived | multi_source_derived | generated_question
  anchors: [...]
parent_claim_id: null
child_claim_ids: []
```

No scaffold support label and no CAL verdict lives here.

### `source_profile.yaml`

```yaml
source_id: src-...
title: ...
source_type: regulatory_guidance
publisher: European Commission
document_status: draft_consultation
publication_date: null
version_label: consultation_draft_2025
jurisdiction: EU
url: ...
accessed_at_utc: ...
content_hash: sha256:...
extraction:
  representation_id: ...
  extractor: ...
  extractor_version: ...
  extracted_text_hash: sha256:...
```

### `passages/{passage_id}.yaml`

```yaml
passage_id: psg-...
source_id: src-...
text: ...
passage_hash: sha256:...
anchors:
  - type: clause
    value: "6.5"
  - type: page
    value: 4
  - type: char_span
    representation_hash: sha256:...
    start: ...
    end: ...
parent_passage_id: null
extraction_method: auto_retrieved
```

### `links/{link_id}.yaml`

```yaml
link_id: lnk-...
claim_id: clm-...
passage_id: psg-...
nomination:
  method: hybrid
  retrieval_run_id: ...
  rank: ...
  scores: {...}
  hypothesized_role: qualifier_candidate
review:
  decision: accepted
  review_basis: audit_relevance_and_excerpt_sufficiency
  reviewed_by: ...
  reviewed_at_utc: ...
  notes: ...
```

`hypothesized_role` is provenance from the nomination process. It is not a support label and should be blinded from CAL's semantic decision path.

### `coverage/{claim_id}.yaml`

```yaml
claim_id: clm-...
search_scope:
  source_ids: [...]
  closed_world: true
candidate_count: ...
reviewed_count: ...
admitted_count: ...
outcome: admitted | no_candidates | all_rejected | partial_review
limitations: [...]
```

This is the minimum state needed to avoid interpreting every empty evidence set the same way.

## v1.x extension or v2 boundary?

Several gaps could technically be patched into v1.x as optional fields. The problem is cumulative:

- source identity needs status/version fields
- passage identity needs typed representation-aware anchors
- claim identity needs origin and atomicity
- finalization needs to preserve candidate/admission history
- coverage must travel with the bundle
- support/counterevidence preclassification should not control an independent CAL audit
- CAL config and result placeholders are still mandatory apparatus baggage

A backward-compatible v1.x extension can add the missing information, but it cannot remove the old semantic coupling. That would leave two competing interpretations in one contract.

**Provisional inference:** if the goal is a reusable Evidence Bundler product boundary rather than only apparatus replay, this is semantically a major-version change. Preserve a v1 reader/adapter for old sealed bundles rather than rewriting them.

That conclusion is still a hypothesis until the gates below are tested.

## Gates before changing production models

### Gate 1: representation

For stress cases A-H and controls N1-N4, can the proposed shape encode:

- source status
- claim origin
- exact source anchor(s)
- every nominated and admitted passage
- nomination hypothesis separately from human admission
- coverage/search outcome

without free-text notes carrying structurally essential meaning?

### Gate 2: audit sufficiency

Can CAL receive only a **blinded view** of the proposed bundle plus an audit config and determine what evidence is in scope without reading the source PDF or scaffold run?

The blinded view should include admitted passage content/provenance and coverage state, but exclude scaffold support labels, nomination scores, and hypothesized semantic roles from the decision path unless a specific experiment intentionally exposes them.

### Gate 3: provenance reconstruction

Can a reviewer reconstruct:

`verdict -> claim -> admitted link -> passage -> source/extraction representation -> original source hash`

without an ambiguous hop?

### Gate 4: negative controls

The downstream reader must distinguish:

- no candidates
- all candidates rejected
- partial review
- admitted evidence constrained by draft source status

If these collapse to the same state, the shape is underspecified.

### Gate 5: blinding invariance

Create two otherwise byte-equivalent audit inputs from the same admitted passages:

1. nomination metadata says `support_candidate`
2. nomination metadata says `counter_candidate` or is removed

After conversion to the CAL-facing blinded view, the audit request and verdict must be identical.

If changing a Bundler retrieval-role label changes CAL's result while passage content is unchanged, the handoff is leaking an upstream hypothesis into the measurement.

## Current hypothesis

**Hypothesis:** the durable Evidence Bundler boundary is a reusable, audit-neutral evidence package whose job ends after provenance-preserving nomination, admission, and coverage accounting. CAL configuration and CAL results sit outside it and reference it by hash.

**Strongest assumption:** human admission can be defined narrowly enough as relevance/excerpt sufficiency without becoming a disguised support judgment.

**What would falsify the redesign:** if the Annex 22 stress packet, the negative controls, and a blinded CAL round trip can all be represented cleanly with small optional v1.x additions while preserving audit independence, a new major contract is unnecessary churn.

The next evidence-producing step is to implement a tiny prototype loader/blinder for `examples/annex22-shape/prototype-bundle.yaml`, then test the four coverage controls and the blinding-invariance pair before touching canonical models.
