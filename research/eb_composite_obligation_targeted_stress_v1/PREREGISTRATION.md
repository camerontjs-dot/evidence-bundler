# Composite Obligation Targeted Stress V1 — Preregistration

## Classification

Exposed targeted stress only. This study is deliberately adversarial and is authored with knowledge of the prior development result. It can strengthen or falsify a mechanism claim, but it is not fresh qualification and cannot replace the context-free RC1 challenge in Draft PR #111.

## Questions

Q1. Does explicit child-proposition coverage prevent fixed-budget semantic selection from starving one child of a two-child `all_of` composite?

Q2. Once child coverage is enforced, do claim-native subject binding, scope binding, or expected evidence form improve discrimination against same-topic wrong-entity, wrong-scope, or wrong-form candidates?

## Frozen semantic scorer

Use exactly:

- model: `cross-encoder/ms-marco-MiniLM-L6-v2`
- revision: `233902d25c440f23af6f7d6e94d2946bac0bee0a`
- runtime: `torch==2.14.0`, `transformers==5.17.0`, `tokenizers==0.23.2`, `huggingface-hub==1.31.0`
- score: sigmoid of the single sequence-classification logit
- max length: 512

Every candidate is scored independently against both frozen child propositions.

Candidate semantic order uses:

1. maximum child semantic score;
2. original candidate ID for deterministic tie-breaking.

The child owning the maximum semantic score is the candidate's semantic child attribution for the coverage mechanism.

## Stress population

Generate exactly 24 deterministic parents, four in each category:

1. **STARVATION**  
   Several semantically attractive candidates target child A while the useful child-B candidate is less lexically obvious.

2. **NO_STARVATION_CONTROL**  
   Semantic top-3 should naturally have a fair opportunity to cover both children. Coverage repair should generally no-op.

3. **EXPLICIT_SUBJECT_CONFLICT**  
   The child itself names the target entity. The pool contains same-predicate sibling-entity candidates such as Valve 2 vs Valve 3.

4. **INHERITED_SUBJECT_CONFLICT**  
   The parent names the governed entity while one or both child propositions are elliptical. The pool contains same-predicate candidates for a sibling entity.

5. **SCOPE_CONFLICT**  
   Correct and incorrect candidates share entity and predicate but differ on claim-native revision, date, duration, or threshold scope.

6. **FORM_CONFLICT**  
   Correct and incorrect candidates share topic/entity but differ in evidentiary form, such as event record vs policy statement or registry entry vs narrative mention.

Every parent has exactly two children under `all_of`.

## Candidate world

Each parent receives exactly 10 passages.

Gold labels are deterministic fixture metadata and are not provided to the selector.

Each child has exactly one `REQUIRED` candidate. Other candidates are `REDUNDANT`, `DISTRACTOR`, or `UNSAFE_OR_MISLEADING`.

Wrong-entity, wrong-scope, and wrong-form candidates are intentionally semantically competitive.

## Allowed obligation descriptors

Per child:

- exact explicit subject anchor from child text;
- exact inherited subject anchor from parent text when the child is elliptical;
- exact claim-native scope literal;
- expected evidence form from the synthetic fixture's preregistered claim type.

No descriptor contains source IDs, candidate IDs, answer-bearing evidence phrases, support/refute direction, expected verdict, or gold class.

## Selection arms

For each semantic-loss cap `0.01, 0.03, 0.05, 0.10`, run:

- `semantic_top3`
- `child_coverage`
- `child_coverage_plus_subject`
- `child_coverage_plus_wrong_subject`
- `child_coverage_plus_scope`
- `child_coverage_plus_wrong_scope`
- `child_coverage_plus_form`
- `child_coverage_plus_wrong_form`
- `child_coverage_plus_full_obligation`
- `child_coverage_plus_predicate_lexical_control`

### Child coverage repair

Start from semantic top-3.

If both child semantic attributions are represented, no-op.

If one child is absent:

- choose the highest-semantic outside candidate attributed to the missing child;
- replace the lowest-semantic selected candidate whose removal does not remove the represented child's final candidate;
- require semantic loss <= cap;
- at most one coverage swap.

### Descriptor repair

Start from the child-coverage result.

For each child independently:

- compare descriptor match among candidates semantically attributed to that child;
- permit at most one replacement for that child;
- challenger must strictly improve the tested descriptor match;
- semantic loss <= cap;
- preserve both child attributions after replacement.

Correct and wrong controls use the same algorithm. Wrong subject/scope/form values are frozen sibling alternatives generated with the fixture.

## Primary metrics

For each arm/cap and relevant category:

- complete parent obligation coverage: both REQUIRED child candidates selected;
- required-child coverage: REQUIRED children selected / 48;
- unsafe/misleading selections;
- non-useful burden;
- number of changes from semantic top-3;
- exact replay identity.

Q1 principal population:
- STARVATION + NO_STARVATION_CONTROL.

Q2 subject population:
- EXPLICIT_SUBJECT_CONFLICT + INHERITED_SUBJECT_CONFLICT.

Q2 scope population:
- SCOPE_CONFLICT.

Q2 form population:
- FORM_CONFLICT.

## Q1 interpretation

Evidence for the child-coverage mechanism requires:

- higher complete-parent obligation coverage than semantic baseline on STARVATION;
- no lower required-child coverage on NO_STARVATION_CONTROL;
- no >2 additional unsafe selections across those eight parents;
- at least one genuine starvation rescue.

Falsify the bounded coverage mechanism if:

- no starvation parent improves at any cap <=0.10;
- controls materially regress;
- unsafe burden rises by >2 without offsetting complete-parent gains.

## Q2 interpretation

A descriptor has targeted support only if, after child coverage:

- correct descriptor improves complete-parent or required-child coverage over child coverage alone in its relevant category;
- the corresponding wrong descriptor does not reproduce that improvement;
- correct descriptor does not add >1 unsafe selection versus child coverage in that category.

If correct and wrong descriptor controls perform equivalently, the descriptor is not causally supported by this stress study.

If the full obligation improves while all individual descriptors fail, record it as an interaction hypothesis rather than attributing the effect to any field.

## No post-run tuning

Do not edit fixture text, caps, arms, model runtime, metrics, or thresholds after the first valid semantic-scoring run.

A mechanical failure before scoring may be repaired and preserved as a deviation.
