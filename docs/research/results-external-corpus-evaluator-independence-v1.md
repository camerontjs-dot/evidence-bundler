# External Corpus Evaluator Independence and Blind-Handoff Prep — Results

## Terminal disposition

**INCONCLUSIVE**

The evaluator contract, fail-closed semantics, adversarial fixture suite, cryptographic dummy handoff, and Git-level hidden-gold object separation are supported by the completed dummy rehearsal. The requested stronger claim of a **genuinely independent second evaluator implementation** is not established because evaluator B was produced in the same supervisory context with knowledge of evaluator A and the separate-agent bridge was unavailable.

This is not a benchmark-validity result and not an Evidence Bundler retrieval result.

## Observed evidence

- Live production `main` at task start: `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`.
- RC4 apparatus #18 is terminal `FALSIFIED`; RC4 target #17 was superseded without Hybrid/Semantic exposure.
- Prior RC2 evaluator assurance explicitly stopped at E3 because no genuinely independent evaluator implementation existed.
- Parallel Pilot 0A preregistration became available during this task at `bf6a347704d8711628e044f46c0c3fb9fa4557df`. Only the preregistration was inspected. No scientific relevance judgments were opened.
- The first pre-reveal dummy snapshot `496f5bed508fb00673d77c00621036e4eefc3dd5` was preserved, then superseded before reveal when Pilot 0A clarified UNKNOWN and group-kind semantics.
- Final authorized pre-reveal snapshot: `9123eec2ec0da48f61bd063f634f1e20b1fc5f68`.
- At that snapshot the exact dummy revealed-gold path is absent/404.
- Precommitted dummy gold SHA-256: `2d0e0d99d23295b91c838e01a4e1a6274e2a77af45cd52ab834ed78fd5b6131f`.
- Post-reveal canonical hashing of the exact dummy gold reproduces that commitment.
- Evaluator A and B return exactly equal result objects on the frozen dummy tuple.
- Local adversarial/invariance suite: `20 passed`.
- Hosted GitHub Actions run `33232876329`: assurance jobs succeeded on Python 3.11 and 3.12 at code/evidence head `185e169eea11e01cab39b9d658d78a9f2159a270`.
- No production BM25, Hybrid, Semantic-only, or other Evidence Bundler retriever was run.

## Contract semantics now explicit

The contract represents:

- query, source, passage, and provenance identity;
- DECISIVE/PARTIAL/TOPICAL/IRRELEVANT/UNKNOWN relevance state;
- binary relevance plus graded gain when resolved;
- SUPPORT/COUNTEREVIDENCE/NEUTRAL_OR_NOT_APPLICABLE/UNKNOWN roles;
- JOINTLY_REQUIRED and ALTERNATIVE_SUFFICIENT evidence groups;
- ranked output and K;
- explicit unjudged versus judged-UNKNOWN distinction;
- complete versus partial qrels.

Metric semantics are explicit for hit@K, evidence recall@K, counterevidence recall@K, nDCG@K, joint/group coverage@K, judgment coverage, and resolved-judgment coverage. Undefined denominators become null, not zero. Partial qrels are labelled lower bounds. nDCG fails closed to null unless graded, complete, resolved gold makes it legitimate.

## Fail-closed and metamorphic assurance

Both implementations reject unknown IDs, duplicate hits, malformed ranks, over-K results, query-set mismatches, identity/hash mismatches, invalid judgments, and invalid group definitions rather than converting them into low scores.

Controlled mutations show sensitivity to missing decisive/support evidence, K boundary movement, group-member loss, and support/counterevidence role changes. Metric output is invariant to irrelevant serialization order, source/passages order, and consistent stable-ID renaming. The hidden-gold commitment is intentionally invariant only to irrelevant serialization, not semantic identity renaming.

## Dummy result

At K=3 the dummy result is hit@K `1.0`, evidence/support recall@K `1.0`, counterevidence recall@K `0.5`, joint/group coverage@K `0.75`, and nDCG `null` because an explicit UNKNOWN judgment makes the graded metric ineligible. These values are fixture expectations only, not retrieval-performance evidence.

## Deviations preserved

### Pre-freeze harness failures

1. Initial dynamic test-module loading failed before metric execution because a dataclass module was not registered in `sys.modules`.
2. The next dry run was `15 passed, 1 failed` because a mutation assertion incorrectly required support recall itself to change even though another retrieved support passage kept that metric at ceiling. The assertion was corrected to test the support/counterevidence metric pair.

No evaluator formula, gold byte, or target threshold was changed in either correction.

### Pilot 0A alignment

After first pre-reveal commit `496f5bed...`, Pilot 0A's preregistration clarified explicit `UNKNOWN` semantics and `JOINTLY_REQUIRED` versus `ALTERNATIVE_SUFFICIENT` groups. Before any dummy reveal, the evaluator contract and dummy commitment were versioned to v0.2 and frozen at `9123eec2...`. The original pre-reveal commit remains in lineage.

## Access-boundary finding

Directory separation alone is rejected. If hidden gold is committed anywhere in history reachable by the target execution identity, normal Git/GitHub operations can recover it even if runtime code never imports it. The dummy protocol therefore uses a pre-reveal commit that lacks the new dummy gold and a later reveal commit.

That demonstrates object separation, but not separate-principal enforcement. The same authenticated owner/supervisory context controlled both sides of this rehearsal.

## Inference

The mechanics are strong enough to support a later blind scientific run **if** the remaining principal/context independence condition is satisfied before scientific gold exposure. Repository object separation can be real; directory separation is not sufficient.

## Remaining unknown / blocker

A genuinely isolated evaluator-B reproduction from the frozen contract has not been observed. This is the sole promotion-critical reason the terminal disposition is `INCONCLUSIVE` rather than `INFRASTRUCTURE READY FOR PILOT INTEGRATION`.

## Falsified alternatives

- “Put hidden gold in a separate directory in the same readable repository” is rejected as information separation.
- “Treat unjudged or UNKNOWN passages as ordinary non-relevant rows” is rejected by the contract and fixtures.
- “Let a metrics library choose defaults for partial qrels, nDCG, rank ties, or undefined denominators” is rejected.
- “Green evaluator execution alone establishes independence” is rejected.

## Smallest discriminating next step

From a fresh, isolated agent/context that cannot read evaluator A, provide only:

1. `contract.md`;
2. public dummy manifest/run schema and revealed dummy gold for this already non-scientific rehearsal;
3. a requirement to implement the contract independently.

Freeze that implementation before comparing it with evaluator A. Run the same adversarial fixtures. If outputs agree and no implementation-specific knowledge is required, the remaining independence gate can be cleared without touching scientific Pilot 0A gold.

## What must be frozen before later scientific apparatus

- exact evaluator contract version and SHA-256;
- two genuinely independent evaluator implementations and identities;
- exact canonicalization/commitment specification;
- result schema including undefined/lower-bound semantics;
- public corpus/query/source/passage manifest identity and benchmark hash;
- K and ranked-run schema;
- qrels completeness mode and nDCG eligibility rule;
- role/group semantics;
- adversarial fixture suite and expected fail-closed outcomes;
- target-execution allow-list and forbidden-source list;
- construction-only storage/ref/credential boundary;
- pre-reveal hidden-gold commitment;
- access audit proving target credentials cannot reach hidden gold/notes;
- reveal/reconstruction procedure;
- exact receipt fields for commits, hashes, CI, deviations, and exposure state.

## Non-claims

No benchmark validity, external-corpus representativeness, retrieval difficulty, Evidence Bundler retrieval performance, Hybrid superiority, production change, or release authorization is established here.
