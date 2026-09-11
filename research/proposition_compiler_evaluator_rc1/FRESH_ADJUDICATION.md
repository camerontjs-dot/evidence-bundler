# RC1 Fresh Surface Adjudication Record

## Timing and contamination boundary
The fresh surface was authored only after target/control freeze commit `26539c53781148543e980fe1f07b25f1ad9c2005` was recorded. No target output on these fresh cases existed when the cases, expected dispositions, families, and rationales were written and hashed.

## Surface
- 30 fresh root propositions;
- 57 fresh candidate decompositions;
- expected dispositions: 27 `ACCEPTABLE_WITHIN_PROFILE`, 26 `REJECT_UNSAFE`, 4 `INDETERMINATE`;
- 8 separate metamorphic invariance follow-ups.

The fresh roots intentionally use different names, lexical material, and relation patterns from the RC0 regression fixtures. The surface concentrates on the preregistered binding boundary: directional roles, cross-clause arguments, shared/local qualifier attachment, operator attachment, conditions/exceptions, connective semantics, reference binding, propositionhood, and ambiguity gating.

## Gold construction
Each gold row preserves:
- proposed gold;
- final resolved label;
- semantic family;
- promotion-critical flag;
- adjudication rationale;
- disagreement state;
- unresolved flag.

Gold was constructed from the sentence/context semantics without retrieval, CAL, Decision Engine, or factual-world lookup. Truth of the claims is irrelevant.

## Human-adjudication limitation
No independent human adjudicator was available in the current execution surface. The fresh gold is therefore internally adjudicated and explicitly marked `not_independently_adjudicated` rather than being represented as independent consensus.

The decisive ambiguity cases were selected where the intended fail-closed judgment is itself the semantic claim: when materially different referent bindings remain compatible and would produce different children, expected disposition is `INDETERMINATE`. A separate benign lexical-ambiguity control has multiple possible word senses but identical decomposition bindings and is expected to remain acceptable.

If later review finds a promotion-critical gold label materially disputable, that case must be removed from decisive positive evidence or converted to an ambiguity/inconclusive probe. It must not be silently relabeled after observing target output.
