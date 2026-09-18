# Architecture

## 1. Boundary model

### ClaimGate may eventually provide qualified hints about

- bounded claim category/family;
- expected evidence forms or a successor evidence-shape expression;
- declared domain;
- verification world;
- jurisdiction;
- typed temporal scope;
- decomposition identity and child propositions;
- explicit unknowns and basis.

### EvidenceGate may eventually provide qualified hints about

- evidence/source form;
- document type;
- source role;
- issuer/provenance;
- temporal and jurisdictional coverage;
- version/currency state;
- corpus scope/completeness/gaps;
- exact source/content identity;
- explicit unknowns and basis.

### Gates must not provide EB causal instructions

Forbidden Gate-to-EB payload content:

- query strings;
- query rewrites;
- source IDs to search or prefer;
- URLs/domains to route to;
- passage IDs;
- rank weights;
- retained K;
- admission decisions;
- SUPPORTS/REFUTES or proposition-relative source authority;
- CAL, Decision, or Authorization state.

If a future upstream field contains one of these semantics, EB must reject it as an invalid hint rather than silently consuming it.

## 2. EB Hint Intake

The hint intake is an authority firewall, not a convenience adapter.

A field is eligible only when all are true:

1. upstream artifact identity is verified;
2. field identity is explicit;
3. field authority is at least `QUALIFIED_HINT`;
4. the field is allowlisted by the EB experiment/candidate;
5. basis/provenance is present;
6. value is valid under the exact upstream schema;
7. the field does not carry prohibited causal instructions.

Unknown values remain unknown. Missing authority does not degrade to best effort.

Suggested intake record:

```json
{
  "schema": "eb-gate-hint-intake-v0",
  "upstream_artifact_sha256": "sha256:...",
  "fields": [
    {
      "field_id": "claim.expected_evidence_shape",
      "authority_status": "QUALIFIED_HINT",
      "value": {},
      "basis": {},
      "qualification_ref": "..."
    }
  ],
  "rejected_fields": [],
  "intake_sha256": "sha256:..."
}
```

This is an EB receipt. It does not mutate the upstream Gate artifact.

## 3. Evidence Shape Requirement Expression

### Design goal

Represent evidence coverage structure without representing semantic sufficiency.

The expression should be small enough to validate, hash, mutate, and ablate.

### Draft operators

#### `unknown`

No justified evidence-shape requirement is available.

```json
{"op": "unknown"}
```

EB must fall back to its non-hint baseline rather than invent a requirement.

#### `form`

One descriptive evidence-form atom.

```json
{
  "op": "form",
  "form": "measurement"
}
```

The vocabulary must come from a qualified upstream contract, not arbitrary free text.

#### `any_of`

Alternative coverage forms.

```json
{
  "op": "any_of",
  "items": [
    {"op": "form", "form": "registry_entry"},
    {"op": "form", "form": "authoritative_declaration"},
    {"op": "form", "form": "document_text"}
  ]
}
```

Interpretation: representation of at least one branch may satisfy the retrieval coverage target.

This does not mean any branch proves the claim.

#### `all_of`

Distinct joint coverage targets.

```json
{
  "op": "all_of",
  "items": [
    {"op": "form", "form": "measurement"},
    {"op": "form", "form": "event_record"}
  ]
}
```

Interpretation: the search/selection process should attempt to represent each child target if candidate evidence exists.

#### `optional`

Non-required corroborative coverage.

```json
{
  "op": "optional",
  "item": {"op": "form", "form": "document_text"}
}
```

An optional miss must not count as failure of required coverage.

### Deliberately absent operators

V0 should not include:

- source authority score;
- preferred issuer;
- preferred domain;
- query term;
- relevance weight;
- confidence multiplier;
- support/refute polarity;
- passage-level expected answer.

Those would either leak routing authority upstream or recreate the failed weighted-score pattern.

## 4. Requirement binding

Each compiled expression must bind to:

- exact proposition identity;
- exact Gate artifact/field identity;
- exact hint authority/qualification identity;
- exact expression hash;
- explicit compiler identity.

For decomposed Contract A input, requirements should bind per authoritative child proposition.

A root-level requirement may not silently replace child-level requirements when decomposition exists.

## 5. EB Requirement Compiler

The compiler is owned by EB.

Its job is to convert an admitted Gate hint into an EB planning object.

The compiler may decide:

- whether a requirement is actionable under the current evidence world;
- which requirement branches remain open;
- whether a candidate set covers an evidence-form target;
- how to apply a bounded coverage rule in an experimental selector;
- later, whether separate retrieval lanes should be instantiated.

The compiler may not:

- alter the authoritative proposition text;
- infer Gate authority;
- turn unknown into a concrete requirement;
- make a CAL semantic judgment;
- treat evidence-form coverage as truth support.

Suggested output:

```json
{
  "schema": "eb-evidence-shape-plan-v0",
  "proposition_id": "...",
  "requirement_sha256": "sha256:...",
  "actionable": true,
  "required_targets": [],
  "optional_targets": [],
  "unresolved_targets": [],
  "compiler_identity": "...",
  "plan_sha256": "sha256:..."
}
```

No query strings or source routing appear in the first selector-stage plan.

## 6. Candidate characterization boundary

For the first experiment, candidate evidence-form characterization should be obtained independently of the claim outcome.

Permitted candidate features may include:

- EvidenceGate-declared evidence form where the candidate inherits a qualified source/passsage characterization;
- mechanically derived document/evidence form under a separately frozen EB classifier;
- explicit unknown.

Not permitted:

- gold class;
- CAL result;
- support/refute relation;
- expected answer;
- case-specific hand labels unavailable in deployment.

This is the highest-weight assumption in the first experiment: if candidate form characterization is poor, requirement coverage may appear useless even if the upstream requirement is good.

## 7. Selection architecture

Do not replace semantic relevance with a new blended score.

Preferred experimental structure:

```text
fixed depth-10 pool
      |
      v
semantic relevance ordering
      |
      v
initial semantic K=3
      |
      v
bounded requirement-coverage repair
      |
      v
final K=3
```

The coverage repair may substitute a candidate only when:

1. an explicit required target is uncovered;
2. a candidate is characterized as covering that target;
3. the candidate clears a preregistered semantic floor or bounded semantic-loss rule;
4. the substitution does not introduce a prohibited safety condition.

The exact rule belongs to a future frozen experiment, not this design branch.

This structure keeps semantic relevance as the incumbent and asks whether the Gate signal adds a distinct coverage correction.

## 8. Evidence posture

RC1 observed that evidence posture reduced unsafe selections from 62 to 58 relative to the no-posture ablation while not improving required-lane coverage.

Treat posture as a separate candidate safety hypothesis.

Do not combine posture with evidence-shape requirements in the first causal experiment unless both effects can be independently ablated.

A later selector may have three explicit stages:

```text
semantic relevance
    -> evidence-shape coverage repair
    -> evidence-posture safety filter/repair
```

Each stage must survive its own causal control.

## 9. First-stage retrieval eligibility

Gate-informed first-stage retrieval is not yet authorized.

It becomes eligible only if fixed-pool experiments establish that qualified evidence-shape information adds signal beyond semantic-only selection.

A later retrieval design could permit EB to create multiple retrieval intents from one requirement expression, but the generated query text and source routing must remain EB-owned and separately testable.

Example future architecture:

```text
any_of(measurement, authoritative_declaration)
       |
       v
EB compiler
       |
       +--> retrieval intent: measurement-shaped evidence
       +--> retrieval intent: declaration-shaped evidence
       |
       v
EB query generator / retriever
```

The Gate never emits the generated queries.

## 10. Main falsifiers

Reconsider this architecture if:

- improvements occur equally with shuffled/wrong requirements;
- requirement coverage only helps by sacrificing semantic relevance beyond the preregistered bound;
- candidate evidence-form characterization is too unreliable for deployment;
- useful performance requires Gate-provided queries, sources, weights, or answer-bearing state;
- requirement expressions become a disguised semantic verdict system;
- every claim family needs bespoke retrieval code with no stable compiler abstraction;
- first-stage effects cannot be separated from selector effects;
- unknown/missing upstream state is routinely overridden rather than preserved.
