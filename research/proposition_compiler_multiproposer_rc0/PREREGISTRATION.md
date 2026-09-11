# Multi-Proposer Convergence RC0 Preregistration

## Research question
Can heterogeneous proposal mechanisms increase the number of safely resolvable explicit-conjunction roots relative to the best single proposer while the exact frozen RC1 semantic-binding evaluator preserves fail-closed authority?

## Predecessor
- RC0 evaluator PR #61: `FALSIFIED`.
- RC1 evaluator PR #62: `INCONCLUSIVE`.
- frozen RC1 evaluator commit: `26539c53781148543e980fe1f07b25f1ad9c2005`.
- frozen evaluator SHA-256: `1091169da8e960cdf93242ee4c629c7a1a814009c8f80554f4a190f5b3fe989d`.

## Development evidence
Approximately 12 visible roots may be used to implement and debug proposer mechanics. RC1 false-negative families are development evidence only.

## Freeze boundary
Before any decisive fresh roots are authored:
1. freeze `proposers.py`;
2. freeze `resolver.py`;
3. freeze raw runner/scorer identities;
4. record exact frozen RC1 evaluator identity;
5. record development-only results and known limitations.

After this point no proposer/resolver repair is permitted before decisive disposition.

## Fresh decisive surface
Exactly 24 roots, four in each preregistered family:
1. explicit/shared-subject conjunction;
2. separate-subject relation/directional conjunction;
3. shared vs child-local qualifier/scope;
4. modality/negation/quantification;
5. attribution/reference/ellipsis;
6. comparison/connective/ambiguity traps.

Fresh roots must not reuse predecessor names or exact wording and must not be mere noun swaps of development examples.

## Gold
Gold is isolated from runtime and states:
- family;
- `RESOLVED` or `FAIL_CLOSED` expectation;
- one or more explicitly permitted child proposition sets for `RESOLVED` roots;
- adjudication rationale.

The resolver cannot read gold. Raw output is written and hashed before scoring.

## Positive gate
`SUPPORTED_FOR_FRESHER_QUALIFICATION` requires:
- zero unsafe pooled `RESOLVED` outcomes;
- every material ambiguity remains fail closed;
- pooled S4 resolves at least three more fresh roots than the best single proposer;
- positive gain occurs in at least two distinct families;
- exact replay byte-identical;
- candidate vote count never affects authority;
- predecessor unsafe-binding regressions remain fail closed;
- hosted reproduction succeeds on the exact frozen objects.

## Falsifiers
One is sufficient:
- unsafe semantic decomposition becomes pooled `RESOLVED`;
- material ambiguity is resolved due to proposer agreement;
- proposer identity/count overrides frozen authority failure;
- pooled system introduces an unsafe authoritative resolution;
- exact replay differs;
- runtime sees gold before raw freeze;
- post-result proposer/resolver/evaluator repair is required.

## Inconclusive conditions
Examples:
- no falsifier, but S4 gain < 3 roots;
- gain is confined to one family;
- frozen RC1 evaluator is the dominant bottleneck;
- hosted positive reproduction is unavailable/fails before semantic execution;
- decisive gold is not trustworthy enough for the claimed support.

## Non-claims
No result here authorizes a compiler, Contract A change, Evidence Bundler production change, retrieval optimization, CAL optimization, Decision Engine change, merge, release, or promotion.
