# Composite Evidence Obligation RC1 — Fresh Cohort Contract

## Purpose

Build a fresh challenge that can separate four different hypotheses:

1. explicit child coverage matters;
2. exact claim-native subject binding matters;
3. exact claim-native scope binding matters;
4. expected evidence form matters.

The corpus must make these disagree. A descriptor match is never itself evidence usefulness.

## Population

Author exactly **36 fresh parent claims**, 6 per category. Every parent has exactly two meaning-preserving child propositions under explicit `all_of`.

### C1 — child-starvation controls

Both children concern the same named system but different evidentiary facts. Make semantic relevance naturally favor one child strongly enough that a fixed top-K can overrepresent it.

### C2 — explicit wrong-entity conflicts

Use pairs such as Valve 2 vs Valve 3, Channel A vs Channel B, Unit 4 vs Unit 5.

Both entities must appear naturally in the corpus with the same or very similar predicate vocabulary. Useful evidence is keyed to the entity named by the child.

### C3 — inherited-subject conflicts

The parent names the governed object. At least one child is intentionally elliptical but still meaning-preserving in parent context, for example:

- parent: "For Valve 2, the closure check passed and the witness record was signed."
- child 1: "the closure check passed."
- child 2: "the witness record was signed."

The corpus contains same-predicate passages for a sibling object. Freeze the inherited subject from the parent before corpus authoring.

### C4 — scope conflicts

Use same-entity/same-predicate evidence that differs only in claim-native scope such as:

- revision 3.0 vs revision 4.0;
- 2026-08-27 vs another date;
- 3.3 °C vs another threshold;
- 21-minute hold vs another duration.

### C5 — evidence-form conflicts

Use claim children whose experimental expected evidence forms differ, with plausible passages in both matching and nonmatching forms. Include same-subject hard negatives so form cannot stand in for subject identity.

### C6 — crossed anti-shortcut cases

For each parent, arrange candidate types that cross the factors:

- correct subject + correct scope/form;
- correct subject + wrong scope/form;
- wrong subject + correct scope/form;
- wrong subject + wrong scope/form.

At least one descriptor-matching candidate must be adjudicated non-useful or unsafe, and at least one useful candidate must not maximize every descriptor field.

## Claim and descriptor freeze

Before any corpus text is authored, freeze:

- parent ID/text;
- exactly two child IDs/text;
- `all_of` lineage;
- child-native subject anchors;
- parent-inherited subject anchors;
- claim-native scope literals;
- child-native predicate/property terms;
- experimental expected evidence forms;
- provenance for every descriptor field.

### Allowed descriptor content

A descriptor may contain only information already present in the frozen parent/child claim, except the separately generated experimental expected-evidence-form label.

Examples:

- `Valve 2` when Valve 2 is in the parent/child;
- `revision 3.0` when the claim says revision 3.0;
- `below 3.3 degrees C` when that threshold is in the claim;
- `event_record` as an experimental expected evidence form.

### Forbidden descriptor content

Do not include:

- evidence-derived terms absent from the claim;
- answer text copied from a passage;
- source IDs, domains, URLs, or issuer names to target;
- passage IDs;
- query strings/rewrites;
- support/refute direction;
- expected verdict;
- candidate scores/ranks;
- gold class or evaluator state.

If the claim says Valve 2, do not add Valve 3 just because Valve 3 appears in the corpus.

## Corpus

Target 12–20 fresh passages per parent.

For C2–C6, include hard negatives that are genuinely competitive rather than keyword caricatures.

Do not put gold-like hints in filenames, source IDs, headings, or metadata.

Intended-form metadata may be authored before retrieval for audit/eligibility, but is not gold and must not be edited after candidate inspection.

## Retrieval and candidate freeze

Use one exact frozen retrieval configuration for every arm.

Freeze at least the top 10 candidate pool per child/parent experiment unit before gold adjudication.

Preserve:

- passage bytes and IDs;
- source IDs;
- retrieval rank/score;
- child-query attribution;
- exact query/proposition identity;
- candidate-pool hash.

No post-reveal retrieval tuning.

## Gold

Adjudicate candidate usefulness independently of descriptor matching.

Use candidate classes:

- `REQUIRED`
- `USEFUL_DISTINCT`
- `REDUNDANT`
- `DISTRACTOR`
- `UNSAFE_OR_MISLEADING`
- `UNRESOLVED`

Also record which child proposition(s), if any, each useful candidate actually bears on.

Gold must answer the factual/evidentiary objective, not "did the candidate contain Valve 2?" or "did it use an event record?"

## Prereveal cohort gates

Before `READY_FOR_REVEAL`, require:

- 36 eligible parents, exactly 6 per category;
- 72 declared child propositions;
- all parent/child/descriptors frozen before corpus authoring;
- at least 24 parents where semantic top-K has a plausible opportunity to starve one child;
- all C2 cases contain same-predicate wrong-entity candidates;
- all C3 cases contain wrong-entity candidates that would fool an unbound elliptical child;
- all C4 cases contain same-entity wrong-scope candidates;
- all C5 cases contain at least two plausible evidence forms;
- all C6 cases satisfy the crossed-factor geometry;
- at least 18 parents contain one or more `UNSAFE_OR_MISLEADING` candidates;
- at least 18 parents contain useful evidence at retrieval rank 4–10;
- zero target/development exposure before freeze.

Failed lanes are preserved and replaced from scratch. Do not patch a lane after gold or target inspection.

## Primary preregistered comparisons after reveal

The execution lane will compare opaque frozen arms corresponding to:

- semantic baseline;
- child-coverage repair;
- child coverage + correct subject;
- child coverage + wrong/shuffled subject;
- child coverage + correct scope;
- child coverage + wrong/shuffled scope;
- child coverage + expected evidence form;
- child coverage + shuffled form;
- full obligation;
- broad claim-native lexical control.

The clean-room author must not see the implementation details, cap, or post-reveal arm mapping.
