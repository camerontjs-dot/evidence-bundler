# Annex 22 evidence-bundle shape spike

**Status:** exploratory design spike, not an accepted contract decision  
**Branch:** `annex22-bundle-shape-spike`  
**Purpose:** use the European Commission draft GMP Annex 22 as a demanding regulatory corpus to discover what a general evidence bundle must be able to represent before changing C-B or downstream CAL interfaces.

## Source status

The source used for this spike is the European Commission consultation draft **Annex 22: Artificial Intelligence**, opened for consultation on 7 July 2025 and closed on 7 October 2025.

Official consultation page: https://health.ec.europa.eu/consultations/stakeholders-consultation-eudralex-volume-4-good-manufacturing-practice-guidelines-chapter-4-annex_en

Official draft PDF: https://health.ec.europa.eu/document/download/5f38a92d-bb8e-4264-8898-ea076e926db6_en?filename=mp_vol4_chap4_annex22_consultation_guideline_en.pdf

This is a **draft consultation document**, not a final Annex currently listed in EudraLex Volume 4. It is being used here as a schema stressor, not as a claim that these provisions are presently binding GMP.

## What we are trying to learn

The question is not "can Evidence Bundler retrieve Annex 22?" The question is:

> Can the bundle faithfully preserve the information CAL or a human auditor would need to evaluate a claim without silently collapsing source identity, claim origin, evidentiary relationship, review state, retrieval history, or coverage state?

If Annex 22 exposes a representational gap, the first hypothesis should be that the bundle shape is incomplete, not that CAL should infer the missing structure downstream.

## Current C-B is carrying three different things

The current C-B contract was designed as an apparatus handoff from Scaffold Harness -> Evidence Bundler -> Claim Audit Lab. That history is visible in `models/cb.py`.

Today a `ClaimAuditUnit` contains:

1. **Upstream experiment state**: scaffold support status, claim strength, extraction fidelity, counterevidence flags, workflow condition, task id.
2. **Evidence**: passage text, source id, offsets, trust level.
3. **Downstream audit surface**: null `audit.*` fields that CAL later populates.

The bundle manifest also carries CAL audit-config and validation-set pins.

That is coherent for the original evaluation apparatus, but it is not a clean domain-level evidence package. It makes the persisted evidence shape depend on who produced the claim and which auditor will consume it.

### Working separation

A general evidence bundle should separate three artifacts conceptually:

- **Evidence bundle**: claims, sources, passages, claim-passage relationships, coverage, provenance, integrity.
- **Audit invocation**: CAL engine/rules/config selected for a particular audit run.
- **Audit result**: verdicts, traces, confidence/signals, reviewer disposition.

The evidence bundle should not need CAL fields in order to exist, and CAL should not need scaffold judgments in order to audit it.

## Annex 22 stress cases

These cases are intentionally selected because they exercise different representational pressures. The wording below is a compact paraphrase for testing, not a substitute for the source document.

| Case | Annex area | Schema pressure |
|---|---|---|
| A | Scope | A source can be authoritative-looking while still being draft, scoped, and inapplicable to some model classes. |
| B | Intended use | One numbered clause can contain several linked obligations, limitations, responsible roles, and a timing condition. |
| C | Acceptance criteria | A requirement can depend on subgroup-specific criteria and comparison with the process being replaced. |
| D | Test data | Support for one conclusion may require several clauses rather than one passage. |
| E | Data independence | A general rule can have an explicit procedural fallback or exception that qualifies it. |
| F | Explainability | One passage can establish a required record while another establishes the required review of that record. |
| G | Confidence | Requirements may be conditional (for example, applicability-dependent logging) and may define an abstention-like outcome. |
| H | Operation | Evidence can describe lifecycle obligations spanning change control, configuration control, monitoring, drift, and human review. |

These cases imply that "supporting passages" versus "counterevidence passages" is too narrow as the only relationship vocabulary.

## Representational requirements exposed by Annex 22

### R1. Source status is evidence metadata, not a note

A consumer must be able to distinguish at least:

- draft / consultation / final / superseded / unknown status
- publication or issue date
- version or edition when known
- jurisdiction / issuing authority when relevant
- access time and immutable content hash

`source_type=regulatory_guidance` and `trust_level=primary` are not enough. A primary draft and a primary effective requirement are materially different evidence objects.

### R2. Anchors must be typed and multi-modal

Character offsets alone are fragile for PDFs because offsets are against extracted text, not the original page artifact.

A passage should be able to carry multiple anchors, for example:

- clause / section id (`6.5`, `10.1`)
- page number
- heading path
- paragraph index
- character span against a named extracted-text representation

The bundle should also record which extraction representation an offset is relative to.

### R3. Claim origin and evidence support are different relationships

For a requirement extracted from Annex 22, the source passage that **generated the claim** is not automatically evidence that a separate target system complies with the claim.

The bundle therefore needs an explicit claim-origin link, distinct from claim-evidence links.

Examples of claim origins:

- external assertion supplied by a user
- extracted/normalized from a source clause
- derived from multiple source clauses
- generated as an audit question

### R4. Claim-passage relationship belongs on the link

The current final C-B routes passages into `evidence_passages` and `counterevidence_passages`. Annex 22 exposes at least these useful relations:

- supports
- contradicts
- qualifies
- scopes
- defines
- contextual

A passage is not inherently "supporting". Its role exists **relative to a claim**, so the relationship should be stored on a claim-passage link.

### R5. Retrieval nomination and review judgment must remain distinct

Retrieval metadata should survive without becoming evidence semantics.

A claim-passage link can therefore have two separate blocks:

- `nomination`: method, query/run, rank, scores, matched child
- `review`: accepted/rejected/needs-review/insufficient-excerpt plus reviewed relation and notes

This preserves ADR-001: retrieval nominates; review admits.

### R6. Coverage state is first-class evidence about the evidence process

CAL now distinguishes several abstention mechanisms. The bundle should make it possible to tell whether:

- no candidates were retrieved
- candidates were retrieved but all rejected
- review is incomplete
- admitted evidence exists but is partial
- the source/search scope itself was limited

An empty `evidence_passages` array cannot distinguish these cases.

### R7. Composite claims need an explicit escape hatch

Annex 22 clauses often combine actor, action, condition, timing, exception, and documentation requirements.

We should not prematurely build a regulatory ontology, but the schema should at minimum be able to say:

- this claim is atomic or composite/unknown
- this claim was derived from one or more origin anchors
- this claim has child claims when decomposition is performed

That lets extraction improve later without changing passage identity.

### R8. Audit configuration is not evidence

`audit_config.yaml`, `validation_set_ref.yaml`, and mutable/null `audit.*` result fields should not be required members of a general evidence bundle.

They belong to an audit-run package or audit-result package that references an immutable evidence-bundle hash.

## Draft v2 conceptual shape

This is deliberately conceptual. Field names are not yet an accepted contract.

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
publication_date: "2025-07-01"
version: null
jurisdiction: EU
url: ...
accessed_at_utc: ...
content_hash: sha256:...
extraction:
  extractor: ...
  extractor_version: ...
  extracted_text_hash: sha256:...
```

Any source-quality assessment should be a separate assessment block with attribution, not silently collapsed into source identity.

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
review:
  decision: accepted
  relation: qualifies
  reviewed_by: ...
  reviewed_at_utc: ...
  notes: ...
```

The important boundary is that `nomination.method/rank/scores` do not determine `review.relation`.

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

This is the minimum information needed to avoid interpreting every empty evidence set the same way.

## What this would supersede if accepted

A real v2 contract would need an explicit ADR superseding the parts of ADR-002 that say C-B is both the Bundler's internal schema and the CAL handoff shape.

It would also require coordinated changes in:

1. `apparatus-contracts` canonical C-B specification and validators
2. Evidence Bundler models/writer/finalizer/tests
3. Claim Audit Lab C-B reader and `audit-bundle` path
4. demo/round-trip fixtures

The v1.0/v1.1 apparatus contract should remain readable for reproducibility. A v2 reader can be additive; old sealed bundles should not be rewritten.

## Gates before changing the schema

We should not accept the v2 shape merely because it looks cleaner. The smallest useful proof is to build several Annex 22 claim packets and ask whether the shape can represent them without hidden assumptions.

### Gate 1: representation

For each stress case A-H, can we encode:

- source status
- claim origin
- exact source anchor(s)
- all admitted passages
- relation of each passage to the claim
- nomination versus review state
- coverage/search outcome

without free-text notes carrying structurally essential meaning?

### Gate 2: audit sufficiency

Can CAL receive only the proposed bundle plus an audit config and determine what evidence is in scope without reading the original PDF or the scaffold run?

### Gate 3: provenance reconstruction

Can a reviewer start from one CAL verdict and reconstruct:

`verdict -> claim -> admitted link -> passage -> source/extraction representation -> original source hash`

without an ambiguous hop?

### Gate 4: negative controls

Construct at least four deliberately difficult packets:

- empty because retrieval found nothing
- empty because review rejected all candidates
- partially reviewed
- source is a draft whose status materially limits the claim

If the downstream reader cannot tell these apart, the shape is still underspecified.

## Current hypothesis

**Hypothesis:** the durable Evidence Bundler product boundary is not "C-B as originally specified." It is a reusable evidence package whose job ends after provenance-preserving nomination, review, and coverage accounting. CAL configuration and CAL results should sit outside that package and reference it by hash.

**What would falsify this:** if the Annex 22 stress packets and current CAL use cases can be represented cleanly in C-B v1.x with only small optional additions, a full v2 separation would be unnecessary churn.

The next step is therefore not to rename fields. It is to encode the Annex 22 stress packets and compare the smallest v1.x extension against the cleaner v2 boundary above.
