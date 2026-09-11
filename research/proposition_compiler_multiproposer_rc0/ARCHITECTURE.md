# Multi-Proposer Convergence RC0 Architecture

## Boundary
This experiment tests proposal diversity only. It does not build a production Proposition Compiler and does not alter the frozen semantic-binding authority layer from Proposition Compiler Evaluator RC1.

## Fixed authority
The decisive resolver loads the exact RC1 evaluator from commit `26539c53781148543e980fe1f07b25f1ad9c2005` and verifies evaluator SHA-256 `1091169da8e960cdf93242ee4c629c7a1a814009c8f80554f4a190f5b3fe989d` before execution.

No proposal mechanism can override a non-accepting RC1 disposition.

## Proposal lanes

### P1 — conservative surface/scope splitter
- explicit `and` only;
- shared-subject predicate coordination;
- copies an unambiguous leading shared qualifier to both proposed children;
- emits at most one candidate.

### P2 — relation/frame-guided splitter
- explicit `and` only;
- requires two surface clauses with independently visible subjects/predicates;
- preserves directional/comparison surface structure;
- excludes pronoun-led second clauses so reference alternatives remain a distinct lane;
- emits at most one candidate.

### P3 — alternative reconstruction proposer
- may emit several bounded variants;
- surface-preserving full-clause split;
- shared-subject expansion;
- ellipsis expansion;
- pronoun-preserving and, when context uniquely identifies a referent, explicit-reference variants;
- shared-qualifier local-scope variants are intentionally allowed into the proposal pool so the authority layer is tested for rejecting them;
- proposer does not rank its own variants.

## Candidate authority
Each proposed candidate is evaluated independently by the exact frozen RC1 evaluator. Only `ACCEPTABLE_WITHIN_PROFILE` candidates survive.

Proposer provenance is removed before evaluator invocation and retained only in the research receipt.

## Semantic clustering
For each surviving candidate, every child is reparsed through the same frozen RC1 `parse_child` representation. The unordered set of child frame keys becomes a proposer-independent semantic-cluster identity.

- zero surviving semantic clusters => `UNRESOLVED`;
- exactly one => `RESOLVED`;
- more than one materially distinct cluster => `INDETERMINATE`.

Candidate count and proposer vote count never affect the resolver state.

## Systems
- `S1_P1`: P1 only;
- `S2_P2`: P2 only;
- `S3_P3`: P3 only;
- `S4_POOL`: P1 + P2 + P3.

All systems use the same fixed authority and resolver.

## Known limitation intentionally retained
If the frozen RC1 evaluator cannot parse or uniquely bind the root, proposer diversity cannot rescue it. RC1's modal/shared-coordination and local-attribution parser failures are retained as diagnostic development cases rather than repaired here.

## LLM boundary
No live LLM is promotion-critical in RC0. This isolates the architectural question of heterogeneous proposal diversity from model-service reproducibility. A later successor may replace or supplement P3 with a pinned LLM proposer/checklist reader if this architecture earns its complexity.
