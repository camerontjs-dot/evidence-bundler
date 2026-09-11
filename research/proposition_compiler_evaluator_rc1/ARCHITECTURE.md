# RC1 Binding-Conservation Architecture

## Boundary
RC1 is deliberately narrower than general semantic parsing. It recognizes a small set of explicit English constructions required to test binding conservation. Unrecognized or multiply parsed constructions fail closed.

## Core representation

```text
PropositionFrame
  predicate: normalized relation identifier
  arguments: ordered role -> normalized referent
  operators:
    negation
    modality
    quantifier
  qualifiers:
    unit
    temporal
    population
    location
    condition
    exception
    attribution
  references:
    explicit | uniquely_resolved | unresolved
  source_span / clause_index
```

`RootFrameSet` additionally records `all_of` membership and any qualifier explicitly shared across root conjuncts.

## Parsing discipline
1. Parse only preregistered bounded templates / constructions.
2. A root parse must be unique to authorize acceptance.
3. A child parse must be unique and proposition-like.
4. Shared root qualifiers are represented as inherited bindings to each dependent root frame, not as global token inventory.
5. Local qualifiers remain attached only to their source frame.
6. Pronouns may be resolved only when authorized context yields one admissible referent under the bounded resolver.
7. `or` and `and/or` are outside the authoritative `all_of` profile; corruption to `or` is unsafe, while an unsupported root is `INDETERMINATE`.

## Correspondence
For accepted `all_of`, root authoritative frames and child proposition frames must form a bijection after normalization. Each root frame is represented exactly once; each child corresponds to exactly one root frame.

A match requires equality of the represented semantic bindings, not equality of surface text:
- predicate/relation;
- argument roles and referents;
- local operators;
- attached qualifiers;
- resolved reference identity;
- connective membership compatible with `all_of`.

Extra, missing, duplicated or mismatched frames fail.

## Ambiguity gate
Before correspondence, enumerate bounded parse/binding alternatives. If more than one materially distinct alternative remains and those alternatives imply different authoritative child frames, return `INDETERMINATE`. Harmless representational multiplicity that canonicalizes to the same frame set is not semantic ambiguity.

## Propositionhood
Propositionhood is established by successful bounded frame construction, not punctuation or verb count. Elliptical forms are permitted only when a unique argument can be recovered from the declared root/context without inventing content. Unrecoverable fragments fail closed.

## Instrument authority
RC1 initially uses deterministic bounded parsing only. No parser, NLI model, LLM, embedding model or SRL system is granted semantic authority. If later added, exact identity/configuration must be frozen and disagreement affecting acceptance must yield `INDETERMINATE`.
