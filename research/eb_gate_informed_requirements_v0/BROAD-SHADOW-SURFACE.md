# Broad Shadow Surface for Gate-Informed Evidence Bundler Research

## Purpose

This document deliberately defines a **wider research surface than the eventual production surface**.

The objective is not to guess the smallest correct set of Gate-derived inputs in advance.

The objective is to:

1. carry forward what survived pressure;
2. reformulate concepts whose current implementations were falsified;
3. add adjacent, mechanically testable descriptors that follow from the observed failure mechanisms;
4. keep every new field non-causal by default;
5. pressure-test the whole surface and prune it with evidence.

The governing rule is:

> broad capability, narrow authority.

No field in this document is automatically authorized to alter retrieval, selection, admission, CAL semantics, Decision policy, or Authorization.

## Evidence basis

### Proven stable or boundedly supported

From Proposition Authoring field pressure:

- 41 registered fields were exercised over 118 frozen cases;
- 26 were `SUPPORTED_BASELINE`;
- 14 were `FALSIFIED_BASELINE`;
- 1 was `INCONCLUSIVE`;
- deterministic replay passed;
- authority remained unchanged.

The following concepts survived their frozen baseline representations:

### Claim-side

- declared domain;
- declared verification world;
- declared jurisdiction;
- expected evidence forms.

### Evidence-side

- source identity;
- content identity;
- provenance;
- issuer;
- source role;
- authority basis as declared metadata;
- document type;
- evidence form;
- temporal coverage;
- jurisdictional coverage;
- version;
- currency state;
- duplicate-content groups;
- verification world;
- corpus scope;
- completeness state.

### Preflight

- evidence-form observation;
- missing expected evidence forms;
- verification-world compatibility;
- corpus aperture;
- corpus completeness;
- known-gap observation.

The focused evidence-form taxonomy successor also reached 8/8 on its frozen comparative/status matrix.

### RC2 boundary mechanics that survived bounded qualification

The Gate RC2 successor established, within its tested scope:

- claim-independent EvidenceGate output/identity;
- stable evidence-world identity from evidence rather than claim identity;
- typed separation of source origin type and source locator;
- exact reconstruction inputs for ClaimGate and EvidenceGate;
- prohibited downstream authority flags remaining false;
- preservation of Contract A bytes;
- deterministic replay;
- source-byte mutation changing evidence-world identity;
- source-ID mutation changing evidence-world identity;
- source metadata/URI mutation changing Gate output without changing intrinsic byte-world identity;
- duplicate source IDs failing closed;
- metadata for unsupplied sources failing closed;
- empty evidence worlds remaining representable without invented completeness.

RC2 was **not** final-freeze ready. Its pressure test found four bounded failure mechanisms and three open design decisions. Those failures are incorporated below rather than ignored.

## Surface status classes

Every candidate field or relation must be in exactly one research status:

### A. `SUPPORTED_REPRESENTATION`

Current representation survived a frozen pressure surface well enough to use as a baseline subject for further qualification.

This does **not** imply `QUALIFIED_HINT`.

### B. `REPAIR_REQUIRED`

The concept remains useful, but its tested implementation or representation was falsified.

A successor representation may be pressure-tested.

### C. `DESIGN_HYPOTHESIS`

The field is broader than the proven surface but is directly motivated by observed failures or by the need to distinguish mechanisms during pressure testing.

It carries no positive evidence yet.

### D. `REJECTED_CONCEPT`

Only use this after pressure evidence shows the concept itself is not useful or cannot be represented without semantic leakage.

Do not assign this status merely because one parser or lexical implementation failed.

---

# 1. Claim-side shadow surface

## 1.1 Exact identity and lineage

Status: `SUPPORTED_REPRESENTATION`

Candidate descriptors:

- proposition/root ID;
- exact proposition text hash;
- decomposition parent/child identity;
- terminal ClaimGate authoring state/reason;
- exact Contract A binding;
- producer/work/handoff identity.

These are primarily provenance and binding surfaces, not retrieval hints.

## 1.2 Declared verification context

Status: `SUPPORTED_REPRESENTATION`

Candidate descriptors:

- domain;
- verification world;
- jurisdiction.

Pressure-test questions:

- does the declaration remain stable under irrelevant text changes?
- does it meaningfully distinguish evidence requirements or only restate task metadata?
- can EB use it without source-routing leakage?

Potential EB use remains experimental.

## 1.3 Evidence-shape requirement

Status:
- flat expected forms: `SUPPORTED_REPRESENTATION`;
- structured requirement expression: `DESIGN_HYPOTHESIS`.

The current flat set should be widened into an expression language so pressure can determine which operators are actually useful.

Candidate operators:

- `unknown`;
- `form`;
- `any_of`;
- `all_of`;
- `optional`;
- `at_least_n_of`;
- `distinct_sources`;
- `distinct_forms`;
- `corroborative`.

The last four are intentionally broader hypotheses.

They should be included in the shadow design because the current flat set cannot express:

- alternatives versus joint requirements;
- whether two pieces of evidence must be distinct;
- whether corroboration is useful but non-required;
- whether multiple independent observations matter.

No operator establishes evidence sufficiency.

## 1.4 Claim-family / verification-dimension descriptors

Status: `REPAIR_REQUIRED`

The current family detector was falsified by lexical collisions such as `standard deviation` adding `compliance`.

Do not delete the concept.

Split it into:

### Mechanical observations

- numeric token present;
- date expression present;
- standard/regulatory citation present;
- identifier-like token present;
- comparative cue present;
- causal cue present;
- status/state cue present;
- existence cue present;
- definition cue present;
- attribution cue present;
- compliance cue present.

### Separately qualified semantic dimensions

Candidate dimensions:

- quantitative;
- comparative;
- temporal;
- causal;
- attributional;
- definitional;
- existence;
- status/state;
- compliance.

The mechanical layer should be allowed to be broad and noisy.

The semantic layer should remain unknown until separately qualified.

## 1.5 Entity and relation structure

Status: `REPAIR_REQUIRED`

The narrow comparative parser failed ordinary comparison wording.

Instead of one all-or-nothing field, pressure-test:

### Surface observations

- entity mention spans;
- candidate relation cue spans;
- comparator markers;
- quantity/measure/unit spans;
- threshold spans;
- temporal spans;
- jurisdiction spans;
- attribution-source spans.

### Structured hypotheses

- subject/entity;
- predicate/relation;
- object/target;
- comparator entity;
- measure;
- unit;
- threshold;
- time anchor/range;
- jurisdiction target;
- attributed source.

These fields are intentionally broader than the previous bounded grammar.

They should be tested for precision, recall, invariance, and whether they add anything beyond semantic retrieval.

## 1.6 Temporal representation

Status: `REPAIR_REQUIRED`

The current string representation lost interval semantics.

Pressure-test a typed model:

- unknown;
- instant/date;
- year;
- closed interval;
- open interval;
- relative period;
- current/as-of relation;
- multiple disjoint intervals.

Candidate relations:

- before;
- after;
- during;
- overlaps;
- contains;
- contained_by;
- disjoint;
- unknown.

Do not reduce interval structure to string equality.

## 1.7 Jurisdiction representation

Status:
- declared jurisdiction: `SUPPORTED_REPRESENTATION`;
- compatibility relation: `REPAIR_REQUIRED`.

Pressure-test:

- exact jurisdiction identity;
- parent/child hierarchy;
- contains;
- contained_by;
- overlaps;
- disjoint;
- unknown.

The representation must distinguish `Ontario, Canada` from `Canada` without automatically treating them as incompatible.

## 1.8 Context

Status: `REPAIR_REQUIRED`

Current `context_dependence` measured whether context was supplied, not whether it was required.

Split into:

### Mechanical

- context supplied;
- context source identity;
- context byte hash;
- context length/availability.

### Semantic hypothesis

- context required;
- context relevance;
- context scope;
- unresolved without context.

Only the mechanical fields are immediately eligible for descriptive pressure tests.

## 1.9 Structure and scope

Status: `REPAIR_REQUIRED`

Current coordination heuristics confused proper names with compound propositions.

Split into:

### Mechanical surface observations

- coordination token present;
- punctuation boundary present;
- multiple finite-clause cue;
- parenthetical/qualifier cue;
- scope marker present.

### Semantic hypotheses

- proposition count;
- compound structure;
- scope ambiguity;
- attachment ambiguity;
- qualification dependency.

This avoids presenting a surface cue as a semantic fact.

## 1.10 Negation, modality, attribution

Status: `REPAIR_REQUIRED`

Current bounded regexes missed ordinary forms such as `cannot`, future modality, and `according to`.

Pressure-test two layers:

### Cue layer

- negation cue spans;
- modality cue spans;
- attribution cue spans;
- quoted/deictic cue spans.

### Interpreted layer

- negated proposition span;
- modal force;
- attributed proposition/source relation.

EB should not consume the interpreted layer causally unless separately qualified.

---

# 2. Evidence-side shadow surface

## 2.1 Intrinsic evidence-world identity

Status: `SUPPORTED_REPRESENTATION` after RC2 bounded repair.

Required properties:

- claim-independent;
- source-order invariant;
- metadata-order invariant;
- source-byte sensitive;
- source-ID sensitive;
- reconstructable.

Pressure-test open design question:

- whether media type belongs in intrinsic evidence-world identity or only in characterization.

## 2.2 Source/content identity

Status: `SUPPORTED_REPRESENTATION`

Fields:

- source ID;
- content hash;
- media type;
- source count;
- exact duplicate-content group.

Potential adjacent shadow descriptors:

- near-duplicate group;
- chunk-equivalent group;
- mirrored-copy group.

Near-duplicate/mirror grouping is `DESIGN_HYPOTHESIS` and should not be treated as the same thing as exact duplicate hashing.

## 2.3 Source origin and provenance

Status:
- provenance concept: `SUPPORTED_REPRESENTATION`;
- RC2 `origin_type` / source locator split: boundedly supported;
- vocabulary/validation: unresolved.

Pressure-test candidate fields:

- origin type;
- source locator;
- issuer;
- publication/host organization;
- declared source role;
- declared authority basis;
- acquisition channel;
- retrieval timestamp if available outside intrinsic identity;
- original versus mirrored/cached representation.

Open design decisions:

- finite versus open `origin_type` vocabulary;
- true URI validation versus generic locator;
- whether `authority_basis` must be renamed/restricted to prevent proposition-relative semantic smuggling.

## 2.4 Evidence/document form

Status: `SUPPORTED_REPRESENTATION`

Fields:

- document type;
- evidence form;
- media type;
- form basis.

Broader pressure-test forms should include at least the existing forms plus candidate distinctions such as:

- measurement;
- event record;
- registry entry;
- database record;
- authoritative declaration;
- document text;
- table;
- figure/chart;
- policy/rule text;
- inspection/audit record;
- administrative record;
- experiment/study result;
- correspondence;
- unknown.

Not all need survive.

The point is to discover which distinctions causally help EB.

## 2.5 Source role

Status: `SUPPORTED_REPRESENTATION`

Pressure-test a finite role vocabulary versus free text.

Candidate roles:

- primary record;
- authoritative registry;
- policy/rule source;
- measurement source;
- secondary summary;
- index/locator;
- corroborative source;
- superseded source;
- unknown.

Do not turn role into a truth score.

## 2.6 Temporal and jurisdictional coverage

Status: `SUPPORTED_REPRESENTATION` as declared metadata.

Widen the shadow representation to typed structures compatible with claim-side interval/jurisdiction relations.

Pressure-test:

- exact coverage;
- partial coverage;
- contains claim scope;
- overlaps;
- stale/out-of-window;
- unknown.

These relations are descriptive compatibility observations, not support judgments.

## 2.7 Version and currency

Status: `SUPPORTED_REPRESENTATION`

Pressure-test:

- explicit version;
- effective date;
- expiry/supersession date;
- current;
- stale;
- superseded;
- historical;
- unknown.

Version/currency should be kept separate from source truth.

## 2.8 Conflict and supersession graph

Status: `REPAIR_REQUIRED`

Concept retained.

Required successor hygiene:

- reject self-conflict;
- reject self-supersession;
- distinguish symmetric conflict from directed supersession;
- validate referenced source IDs exist;
- detect cycles where relevant;
- preserve declared versus inferred relation basis.

Additional shadow hypotheses:

- partial conflict;
- version replacement chain;
- same-issuer replacement;
- cross-source contradiction declaration.

No claim-relative contradiction inference belongs in EvidenceGate.

## 2.9 Completeness and gaps

Status:
- completeness state: `SUPPORTED_REPRESENTATION`;
- known gaps: representational repair required.

Use explicit tri-state or richer declaration:

- unknown;
- declared_none;
- declared_some.

For declared gaps, pressure-test structured gap kinds:

- missing source;
- missing time period;
- missing jurisdiction;
- missing evidence form;
- missing version;
- inaccessible source;
- incomplete corpus;
- unknown gap type.

These describe corpus limitations, not claim falsity.

## 2.10 Candidate/passage-level EB-owned characterization

Status: `DESIGN_HYPOTHESIS`

This is intentionally broader than Gate V1 because EB operates on passages, not only source records.

Candidate features worth pressure-testing separately:

### Structural

- source ID;
- passage identity/hash;
- section/offset;
- evidence/document form inherited from source;
- local numeric density;
- table/figure adjacency;
- citation density;
- heading/title proximity.

### Evidentiary posture

- asserted result;
- measured result;
- observation;
- administrative status statement;
- definition/rule;
- hypothesis/proposal;
- unresolved question;
- hypothetical/example;
- rejected claim/hypothesis;
- unverified report;
- explicit non-result.

RC1 gives only weak evidence here: posture reduced unsafe selections by four in that cohort.

Therefore posture belongs in the broad pressure surface but not as proven authority.

### Local semantic fit

- proposition relevance;
- local span relevance;
- entity/relation coverage;
- temporal compatibility;
- jurisdiction compatibility;
- evidence-form coverage.

Keep these as separable features, never a single opaque composite during pressure testing.

---

# 3. Preflight / compatibility shadow surface

## 3.1 Proven observational fields

Status: `SUPPORTED_REPRESENTATION`

- evidence-form state;
- missing expected evidence form state;
- verification-world compatibility;
- corpus aperture;
- corpus completeness;
- known-gap observation.

Allowed states may include:

- match;
- partial;
- mismatch;
- unknown;
- not_applicable.

## 3.2 Repaired compatibility relations

Status: `REPAIR_REQUIRED`

Replace exact-string temporal and jurisdiction checks with typed relations.

Candidate outputs:

### Temporal

- contains;
- contained_by;
- overlaps;
- before;
- after;
- disjoint;
- unknown.

### Jurisdiction

- equal;
- contains;
- contained_by;
- overlaps;
- disjoint;
- unknown.

## 3.3 Broader evidence-shape preflight

Status: `DESIGN_HYPOTHESIS`

Given a structured evidence-shape requirement, pressure-test:

- required branches observed;
- required branches missing;
- optional branches observed;
- optional branches missing;
- unresolved due unknown source characterization;
- impossible under current corpus declaration;
- partially coverable.

Again, this is search/coverage state, not epistemic sufficiency.

---

# 4. EB-owned planning surface

The Gate should not expose this directly.

This section is intentionally broad so EB can pressure-test candidate planners and prune them.

## 4.1 Requirement compiler outputs

Candidate fields:

- proposition ID;
- requirement expression hash;
- actionable targets;
- optional targets;
- unresolved targets;
- target priority class;
- candidate characterization requirements;
- fallback mode when target unknown;
- compiler identity.

## 4.2 Retrieval-intent hypotheses

Status: `DESIGN_HYPOTHESIS`

Potential EB-generated intents:

- semantic proposition intent;
- measurement intent;
- registry/status intent;
- declaration/policy intent;
- event-record intent;
- definitional/rule intent;
- historical/version intent;
- temporal-window intent;
- jurisdiction-constrained intent;
- corroboration intent;
- missing-gap recovery intent.

These are **EB-generated**.

The Gate must never provide the actual query strings or source routes.

## 4.3 Candidate-depth / budget hypotheses

Pressure-test rather than assume:

- fixed total depth;
- per-requirement branch depth;
- adaptive depth when a required branch remains uncovered;
- stop when every required branch has at least one candidate;
- stop on diminishing retrieval gain;
- reserve budget for unknown/unclassified evidence.

Any adaptive policy must have a fixed global ceiling and deterministic replay.

## 4.4 Fusion hypotheses

Keep mechanisms isolated:

- semantic rank;
- requirement coverage repair;
- evidence posture safety repair;
- duplicate/redundancy collapse;
- supersession/currentness handling;
- conflict-preservation policy;
- source breadth;
- evidence-form breadth.

Do not immediately collapse these into one weighted score.

## 4.5 Selection hypotheses

Candidate strategies to pressure-test:

- semantic top-K incumbent;
- semantic + one bounded coverage substitution;
- semantic + iterative coverage repair;
- semantic + distinct-form coverage;
- semantic + distinct-source coverage;
- semantic + posture filter;
- semantic + current-version preference;
- semantic + conflict pair preservation;
- semantic + corroboration reserve;
- semantic + unknown-preserving reserve.

Wrong/shuffled controls are required wherever an upstream hint is claimed to add causal value.

---

# 5. Pressure-test matrix

The broad surface should be reduced by mechanism, not taste.

Every candidate field/operator should face some subset of the following.

## Representation tests

- exact replay;
- canonicalization invariance;
- serialization round-trip;
- source/input order invariance;
- irrelevant metadata invariance;
- explicit unknown preservation;
- malformed-value rejection;
- cross-language/schema validator parity.

## Mutation tests

- change only the causal input and verify field changes;
- mutate unrelated input and verify field does not change;
- recompute object hashes after tampering to ensure semantic validators still reject invalid state;
- break cross-artifact identities and require bundle verifier failure.

## Counterexample tests

- identifiers versus quantities;
- dates versus quantities;
- regulatory citations versus quantities;
- proper names versus coordination;
- supplied context versus required context;
- temporal point versus interval;
- parent versus child jurisdiction;
- self-conflict/self-supersession;
- absent declaration versus declared none.

## Causal EB tests

For any proposed `QUALIFIED_HINT`:

- correct hint;
- shuffled/wrong hint;
- missing hint;
- unknown hint;
- adversarially plausible but wrong hint.

A field should not be promoted if correct and wrong hints have similar effects.

## Redundancy tests

Determine whether a field adds information beyond:

- proposition text embeddings;
- semantic rank;
- claim category;
- evidence form;
- source role;
- temporal/jurisdiction metadata.

Fields that are redundant can remain descriptive without becoming causal.

## Burden tests

Measure:

- extra retrieval calls;
- added candidate count;
- duplicate burden;
- reviewer burden;
- latency;
- memory;
- failure surface;
- provenance complexity.

A small accuracy gain may not justify a large operational tax.

---

# 6. Promotion ladder for EB consumption

The upstream authority ladder remains useful, but EB should add its own consumption state.

Suggested EB-side states:

1. `VISIBLE_SHADOW`
   - stored and inspectable;
   - zero causal effect.

2. `PRESSURE_TEST_ELIGIBLE`
   - allowed in frozen experiments;
   - not used in normal EB runs.

3. `SUPPORTED_EXPERIMENTAL_SIGNAL`
   - has survived a causal experiment against wrong/shuffled controls;
   - still not a default.

4. `CANDIDATE_HINT`
   - may be included in a successor EB research candidate behind explicit profile identity.

5. `QUALIFIED_EB_HINT`
   - authorized for the exact bounded EB profile that qualified it.

6. `PRODUCTION_CAUSAL`
   - only after separate promotion evidence.

Upstream `QUALIFIED_HINT` is necessary but not sufficient for `QUALIFIED_EB_HINT`.

EB must independently prove the field is useful and safe in EB.

---

# 7. Recommended first wide build

Do **not** implement all causal behaviors.

Build a shadow-only research carrier capable of representing the broad surface above.

The first wide build should:

- ingest exact Gate V1/RC2-compatible artifacts;
- preserve all upstream identities and basis;
- expose current supported fields;
- expose repaired successor fields when available;
- include explicit placeholders for reformulated fields;
- normalize every field to a known state;
- prohibit all causal routing/ranking/admission effects;
- record a field-level status and qualification identity;
- support deterministic feature masking/ablation;
- support wrong/shuffled-hint substitution for experiments;
- emit a complete observation receipt.

Then pressure-test the carrier and field representations before enabling any planner.

This deliberately creates more knobs than the eventual system should keep.

That is the point.

The pruning decision should come from frozen evidence, not from design intuition.
