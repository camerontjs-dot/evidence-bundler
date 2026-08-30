# Contract A Decomposition Ownership Boundary RC1 — Preregistration

Status: AUTHORIZED BOUNDED RESEARCH INFRASTRUCTURE EXECUTION

## Candidate boundary

Test the hypothesis:

> Semantic decomposition is declared upstream at the Contract-A boundary. Evidence Bundler may use declared child propositions for retrieval/query planning, but does not author new semantic child propositions.

This is not authorization to promote a Contract-A schema.

## Starting evidence

1. Decomposition is retrieval-consequential under fixed budget.
2. Query-lineage-only child identity is lost before CAL semantic measurement.
3. CAL already exposes an explicit-claim API whose module contract says it does not decompose claim text; the caller supplies stable provenance-bound atoms.
4. Current EB verified intake reads a hash-sealed Contract-A claims registry and retrieval is executed for those claim identities/texts.

## Falsifiers

The candidate boundary is weakened if any of these are observed:

- current Contract A already carries sufficient governed parent/child lineage;
- CAL can truthfully identify an EB-generated atom as a governed provenance origin without inventing authority;
- a minimal upstream lineage packet cannot be adapted losslessly into CAL's existing ExplicitClaimRequest;
- EB requires semantic reinterpretation rather than retrieval/query execution to consume an upstream child proposition.

## Tests

1. Current Contract-A ScaffoldClaim rejects ad-hoc parent/decomposition/sequence fields.
2. Current CAL AtomProvenance accepts source_contract and operator_declared, and rejects evidence_bundler_generated.
3. Freeze the F10 A1 parent/children from the previous experiments in a minimal shadow Contract-A decomposition packet.
4. Adapt that packet to CAL ExplicitClaimRequest with source_contract provenance and all_of operator.
5. Verify parent/child text, identities, operator, and source-contract reference hashes survive exactly.
6. Verify an EB-generated child identity not present in the upstream packet cannot be represented as source_contract provenance without failing an explicit membership check.
7. Verify EB retrieval-query execution can consume the declared child text without changing its semantic identity.

## Interpretation

If all tests pass, the smallest supported ownership boundary is:

- Contract A owns declaration/identity/lineage of semantic propositions;
- EB owns retrieval/query planning and evidence construction for those propositions;
- CAL owns semantic audit/aggregation over caller-declared propositions.

This does not decide who physically runs the decomposition algorithm. An operator or upstream system may generate it, but the semantic result becomes authoritative only when frozen into Contract A.

