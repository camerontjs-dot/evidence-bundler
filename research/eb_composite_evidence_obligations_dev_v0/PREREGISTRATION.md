# Composite Evidence Obligations Dev V0 — Preregistration

## Classification

Exposed-development mechanism pressure only. No production authority, no Gate authority promotion, no retrieval-default change, no Contract change.

## Question

Given an already-declared composite claim and its frozen meaning-preserving A1 child propositions, does an explicit **evidence obligation descriptor** improve fixed-pool post-retrieval selection beyond child semantic retrieval alone?

The descriptor may say what evidence must be **about** and what **form** it may take. It may not tell Evidence Bundler the answer, source, passage, verdict, or query.

## Frozen development source

Reuse the exact six-claim decomposition development object from the terminal composite/decomposition experiment:

- decisive retrieval implementation: `55d158f829f4aad1ed8ad69b19d9e39d445c953d`
- workflow run: `33286415682`
- artifact ID: `9724593640`
- artifact digest: `sha256:de37750385594fd00f683e5ca67cbe1fe2ef29e19dcb41d754b431fbb8c5c21b`
- raw retrieval SHA-256: `b7522a147f1dccd1614bb8dcb4565b8a8834bee4cf2d47695befeb311ebd6680`
- development decomposition SHA-256: `2120228c81466471214ca8b56a6eba2fa5bc498cd0b0243ff3b8fe24c9da2144`
- development relevance SHA-256: `da5b06d78060897f85dc78a8ff45c9622c697a10fe43942ea74a688115c7fac3`

Only the frozen A1 meaning-preserving decomposition is used as the semantic child structure.

## Claim-profile source

For expected evidence forms, use exact shadow Claim Profile subject:

`e29a165b682d060f5dc2a0f3c7d64a7f29b172b4`

This remains research/shadow characterization. The experiment does not grant `QUALIFIED_HINT` authority.

## Evidence Obligation Descriptor V0

One obligation is emitted per frozen A1 child.

Allowed fields:

- `proposition_id`
- `expected_evidence_forms`
- `subject_anchors`
- `inherited_subject_anchors`
- `predicate_terms`
- `scope_literals`
- `logic = all_of` at the parent-child coverage layer
- exact field provenance: `claim_native`, `parent_inherited_claim_native`, or `shadow_expected_form`

### Subject anchors

Only exact claim-native identifiers mechanically copied from the child or parent are allowed, such as:

- `Morrow-2`
- `Larkspur-12`
- `sample 2`
- `revision 3.0`

A named object inherited from the parent may be attached to a child that omits it. This preserves subject binding; it does not add an answer.

### Predicate terms

Content terms mechanically copied from the child proposition after stopword, subject-anchor, and scope-literal removal.

No synonym generation or gold-derived terminology.

### Scope literals

Exact claim-native scope expressions, including dates, revisions, durations, thresholds, units, and explicit numbered components.

These are not hidden answers because they already occur in the declared proposition/parent.

### Expected evidence forms

Use only the frozen shadow Claim Profile output for the exact child proposition.

### Forbidden fields

The descriptor must not contain:

- support/refute direction;
- expected verdict;
- expected answer text;
- evidence-derived values not present in the declared claim;
- source IDs, domains, URLs, issuer names to search;
- passage IDs;
- query strings or rewrites;
- rank weights;
- candidate IDs;
- gold classes;
- CAL/Decision/Authorization state.

## Important boundary examples

Allowed:
- claim says `Valve 2 remained closed` -> subject anchor `Valve 2`;
- parent says `Morrow-2...` and child says only `a signed identity match...` -> inherited subject anchor `Morrow-2`;
- claim says `below 3.3 degrees C` -> scope literal `3.3 degrees C`;
- claim type maps to `event_record` -> expected evidence form.

Not allowed:
- corpus happens to reveal `Valve 3 actually failed` when Valve 3 was not in the claim -> do not add `Valve 3`;
- gold paragraph contains wording absent from the claim -> do not add those words;
- `look in source X` or `search for phrase Y`;
- `this should support the claim`.

## Candidate world

Use the exact A1 semantic **equal-per-query** retrieval output as a fixed over-retrieved candidate pool.

No retrieval is rerun.

This intentionally gives the selector headroom while preserving exact frozen candidate identities and scores.

Test retention budgets:

- K=3
- K=6

No claim is made about production first-stage cost. The original equal-total A1 retrieval remains a reference baseline.

## Arms

For each K and each bounded semantic-loss cap `0.01, 0.03, 0.05`:

1. `semantic_topk`
2. `child_coverage_only`
3. `expected_form_only`
4. `subject_only_child`
5. `subject_with_parent_inheritance`
6. `predicate_terms_only`
7. `scope_literals_only`
8. `claim_native_lexical_all`
9. `form_plus_inherited_subject`
10. `full_obligation`
11. correct-vs-shuffled controls for:
   - expected form;
   - inherited subject;
   - predicate terms;
   - scope literals;
   - full obligation.

Shuffling is deterministic across child propositions and preserves descriptor value distributions.

## Repair rule

Start from semantic top-K over the frozen candidate pool.

A descriptor arm may make at most one bounded replacement per child proposition.

A replacement is allowed only when:

- the outside candidate has strictly higher descriptor match for that child than the victim;
- semantic-score loss is <= the arm's frozen cap;
- candidate remains in the exact frozen pool;
- final K is unchanged.

No weighted global score is used.

## Metrics

Primary exposed-development diagnostics:

- decisive paragraph recall;
- complete joint-group coverage;
- child propositions with at least one decisive hit;
- qualifier/exception recall;
- deep decisive rescue from outside semantic top-K.

Secondary:

- candidate identities changed;
- duplicate burden after selection;
- per-claim evidence-set Jaccard vs semantic baseline;
- exact replay;
- shuffled-control discrimination.

## Direct falsifiers

A descriptor family is not worth fresh qualification if:

- correct and shuffled descriptors perform equivalently;
- gains are reproduced by `claim_native_lexical_all`;
- complete child/joint coverage does not improve where semantic top-K misses;
- gains require caps larger than 0.05;
- a field helps only by using evidence/gold-derived content;
- inherited subject binding harms children that already contain an explicit subject;
- full obligation adds no benefit over a smaller surviving field.

## Nonclaims

This study cannot establish population-level benefit, fresh generalization, optimal decomposition, Gate authority, or production retrieval behavior.

The goal is to identify the smallest additional obligation fields, if any, worth a fresh qualification.
