# Proposition Compiler Evaluator RC0 Preregistration

This research-only apparatus implements issue #59 plus the prospective 2026-09-11 preregistration addendum. It does not modify Evidence Bundler production behavior, Contract A/B/C, CAL, or Decision Engine semantics.

## Exact base

Evidence Bundler main at execution start: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`.

## Question

Can a frozen evaluator for the narrow `single` / explicit-conjunctive `all_of` profile discriminate adjudicated safe candidates from semantic loss/addition/binding mutations and intrinsic ambiguity strongly enough to justify a separate fresh qualification?

## Result vocabulary

`ACCEPTABLE_WITHIN_PROFILE | REJECT_UNSAFE | INDETERMINATE | INVALID_INPUT`

## Promotion-critical dimensions

Structural validity; profile membership/ambiguity; root-supports-children; children-reconstruct-root; operator/qualifier attachment; polarity/modality; reference and argument binding; assertion/embedding type; relation/direction; duplication; propositionhood/auditability; under-decomposition; over-decomposition; metamorphic consistency; deterministic replay.

## Corpus plan

Development target: 30 roots, 150 core candidates, 40 metamorphic follow-ups. The six-root pilot is a pre-corpus annotation-spec sanity check and is not the decisive RC0 run.

## Weak controls

C0 accept-all; C1 shape-only; C2 lexical-retention-only; C3 bag-of-words similarity; C4 gold oracle (ceiling only); C5 one-direction NLI; C6 bidirectional-NLI threshold; C7 entity/operator retention; C8 dependency/SRL-only; C9 LLM binary judge; C10 LLM majority vote if independently invokable; C11 conjunction-aware scope-blind rule system; C12 aggregate bidirectional coverage without propositionhood.

Unavailable external-model controls must be recorded as unavailable and never simulated.

## Decision discipline

Zero critical unsafe candidates may be accepted. Intrinsic ambiguity must fail closed. Hard positive controls are required to defeat reject-all behavior. A target evaluator that cannot separate from named weak controls on preregistered kill subsets is `INCONCLUSIVE`. A post-result semantic repair requires a successor experiment, not patching this frozen target.
