# Composite Evidence Obligation RC1 — Narrow Fresh Cohort Contract

## Purpose

Construct a fresh fixed-pool challenge for three bounded inputs only:

1. explicit parent/child `all_of` composition;
2. exact claim-native subject identity;
3. expected evidence form derived mechanically from the frozen Claim Profile implementation.

This cohort must discriminate the fields without encoding the answer in them.

It is a **post-retrieval selector qualification**. It does not test first-stage retrieval.

## Population

Author exactly **24 fresh parents**, exactly four per category. Every parent has exactly two meaning-preserving child propositions under explicit `all_of`.

### C1 — composition starvation

Create two legitimate child obligations where a semantic top-K selector could overrepresent one child. Both children must remain meaningful independently.

### C2 — explicit subject conflicts

Each child explicitly names the target subject. Candidate pools later must be able to contain same-predicate sibling-subject competitors.

### C3 — inherited subject conflicts

The parent explicitly names one target subject. One or both children are deliberately elliptical but meaning-preserving in parent context. The frozen subject binding for an elliptical child must be copied exactly from the parent.

### C4 — evidence-form conflicts

Choose child proposition types likely to produce a nontrivial expected form under the frozen Claim Profile, such as status/compliance, existence/registration, attribution/declaration, causal/event, or quantitative/measurement claims. Do not author an evidence form manually.

### C5 — crossed subject × form conflicts

Create propositions for which wrong-subject/right-form and right-subject/wrong-form passages could both be plausible competitors. Do not state which factor is expected to win.

### C6 — easy/no-op controls

Create straightforward two-child claims where direct evidence for both children should be semantically easy to identify. These detect gratuitous selector churn.

## Claim authoring

Before corpus authoring, freeze for every case:

- `case_id`;
- `category`;
- `parent_text`;
- exactly two child IDs/texts;
- `logic = all_of`;
- `subject_anchor` for each child;
- `subject_source = child | parent`.

### Subject boundary

A subject anchor must be copied verbatim from the declared claim:

- `subject_source=child`: exact substring of child text;
- `subject_source=parent`: exact substring of parent text and the child is elliptical with respect to that subject.

Allowed examples include synthetic identifiers such as `Valve 12`, `Unit 4`, `Channel 7`, or unique named systems.

Forbidden:

- evidence-derived entities;
- an entity absent from the declared claim;
- answer values;
- support/refute labels;
- source identifiers;
- search phrases.

Use fresh synthetic names/numbers. Do not copy prior development fixtures.

## Expected evidence form

After claim freeze, the apparatus runs exact Proposition Authoring subject:

`e29a165b682d060f5dc2a0f3c7d64a7f29b172b4`

For each child, call `build_claim_profile(AuthoringRequest)` from child text alone and freeze its `expected_evidence_forms`.

The isolated author must not manually edit the returned forms.

The relevant experimental vocabulary may include:

- `authoritative_declaration`
- `event_record`
- `registry_entry`
- `measurement`

Other returned forms remain recorded but may be non-actionable to the later selector.

## Candidate-pool authoring

Only after claims and descriptors are frozen, author exactly **10 fresh candidate passages per parent**.

Each candidate has:

- `candidate_id`;
- `text`;
- `intended_form` for construction audit;
- `design_role` for cohort eligibility only.

Allowed `design_role` values:

- `target_subject_target_form`
- `target_subject_other_form`
- `other_subject_target_form`
- `other_subject_other_form`
- `neutral_distractor`
- `redundant_target`

The later selector and gold adjudicator do **not** receive `design_role`.

The candidate author may use the frozen expected-form descriptors to construct genuine form conflicts, but may not label usefulness, correctness, support/refute, or gold state.

Avoid giveaway filenames, headings, phrases such as “correct evidence,” or other answer-key cues.

## Category geometry

C1: at least four candidates should plausibly concern one child and at least two should plausibly concern the other.

C2: include at least two same-predicate wrong-subject competitors.

C3: include at least two wrong-subject or subject-omitted competitors that could fool an elliptical child.

C4: include at least two target-subject candidates in a different evidentiary form from at least one actionable expected form.

C5: include at least one candidate in each crossed cell when applicable:
- target subject + target form;
- target subject + other form;
- other subject + target form;
- other subject + other form.

C6: include direct target evidence for both children and ordinary distractors, without adversarial overpacking.

## Semantic scoring

After corpus freeze, score every child/candidate pair with:

- `cross-encoder/ms-marco-MiniLM-L6-v2`
- revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`
- sigmoid of the one-logit output
- max length 512.

Freeze all scores before gold adjudication.

## Gold adjudication

Gold adjudication receives only:

- parent text;
- child IDs/texts;
- candidate IDs/texts.

It must **not** receive:

- expected-evidence-form descriptors;
- subject-source metadata;
- design-role metadata;
- selector implementation;
- arm mapping;
- development results.

Label every candidate exactly one of:

- `REQUIRED`
- `USEFUL_DISTINCT`
- `REDUNDANT`
- `DISTRACTOR`
- `UNSAFE_OR_MISLEADING`
- `UNRESOLVED`

For useful evidence, record which child proposition(s) it actually bears on.

Gold usefulness is determined from the evidentiary objective, not by subject/form metadata matching.

## Primary eligibility

Require before `READY_FOR_REVEAL`:

- exactly 24 parents and 48 children;
- exactly four parents in each C1-C6;
- every subject anchor passes exact-substring provenance validation;
- every child has a frozen Claim Profile;
- every parent has exactly 10 candidate passages;
- candidate IDs are unique within and across parents;
- every positive parent has at least one `REQUIRED` candidate for each child;
- at least 12 parents contain one or more `UNSAFE_OR_MISLEADING` candidates;
- at least 8 parents contain useful evidence whose maximum semantic rank is 4-10;
- all C2/C3/C5 construction-geometry checks pass;
- no `UNRESOLVED` candidate remains in the primary population;
- exact scorer replay/hash checks pass;
- no denylisted source was exposed prereveal.

Failed model output or invalid cases are preserved as apparatus/cohort deviations. Do not patch a case after gold inspection.

## Nonclaims

The cohort does not establish first-stage retrieval quality, retrieval completeness, CAL semantics, or the reliability of a production subject extractor.
