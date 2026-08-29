# Evidence Bundler External Corpus Methodology Pilot 0A - clean-room rerun terminal decision

Date: 2026-08-29

## Terminal disposition

# `FALSIFIED`

This run cannot support a clean pre-retrieval methodology claim because published FreshStack retrieval results were exposed by the rendered result of a source-only web search. The task explicitly defines prohibited retrieval exposure as a clean-room falsifier and requires the affected scientific claim to stop.

This disposition is about this clean execution attempt. It does not establish that the frozen ten-case Pilot 0A object is scientifically invalid.

The frozen object remains unchanged and no production retriever was run.

## OBSERVED

- Evidence Bundler production `main` was `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37` at run start.
- PR #20 remained closed/unmerged with terminal `INCONCLUSIVE` and preserved preregistration commit `bf6a347704d8711628e044f46c0c3fb9fa4557df`.
- PR #21 remained open/unmerged/draft with terminal `INCONCLUSIVE`; genuine fresh-context evaluator-B independence remained unestablished.
- PR #22 remained closed/unmerged with terminal `FALSIFIED` as a contamination record.
- PR #18 remained terminal `FALSIFIED`; PR #17 remained `SUPERSEDED WITHOUT TARGET EXECUTION`.
- The exact Pilot 0A sample identities, corpus revisions, passage rules, relevance semantics, and adjudication protocol were re-established from the frozen PR #20 preregistration and were not modified.
- A MainFrame/Conduit isolation-surface check returned HTTP 429 before exposing any project/session list. No isolated evaluator or adjudicator was launched.
- A source-only FreshStack web search rendered the `fresh-stack/freshstack` README and exposed a FreshStack leaderboard snapshot containing published Oracle/Fusion and BM25 retrieval metrics.
- No FreshStack retrieval-produced candidate list was inspected.
- No FreshStack qrels were inspected before scientific gold freeze.
- No SciFact published evidence/rationale annotations were inspected before scientific gold freeze.
- No production BM25, Hybrid, Semantic-only, dense, lexical, or substitute candidate retriever was run or inspected.
- No scientific gold was created.

## INFERENCE

- The clean-room isolation condition for this execution is falsified regardless of whether the exposed retrieval numbers would have changed any later judgment, because the preregistered rule makes exposure itself disqualifying.
- Continuing provenance joins, adjudication, evaluator comparison, or gold-stability work in this same execution context would produce scientifically weaker evidence and would violate the required stop posture.
- The frozen ten-case object remains reusable in a genuinely fresh execution because this run changed none of its scientific bytes or rules.

## HYPOTHESIS

A future clean rerun may still be able to complete Pilot 0A if source acquisition is made mechanically source-only, without search-result surfaces that can inline benchmark leaderboards or paper results, and if genuinely isolated evaluator/adjudicator sessions are available.

## UNKNOWN

The following remain untested in this run:

- whether every relevant frozen FreshStack official corpus row deterministically joins to a historical row carrying construction `commit_id`;
- whether exact upstream FreshStack source bytes can be bound to immutable commits for all required source rows;
- whether the full pinned FreshStack topic partitions satisfy the frozen source-aperture rule in a clean rerun;
- whether SciFact immutable archive acquisition independently reproduces the preregistered archive hash and exact five case bytes;
- whether a genuinely independent evaluator B reproduces the frozen PR #21 contract;
- whether two genuinely isolated scientific adjudicators can stabilize the gold;
- whether both frozen passage representations preserve decisive evidence and semantic roles;
- whether project discretion remains sufficiently bounded across the exact ten cases.

# Gate results

## 1. FreshStack provenance

`NOT_EXECUTED` after contamination.

No official-to-historical join claim is made. No failed/ambiguous join set was generated in this run.

## 2. FreshStack aperture

`NOT_EXECUTED` after contamination.

No source-aperture classification is claimed from this run. PR #22 was not imported as scientific proof.

## 3. SciFact reconstruction/licensing

`NOT_EXECUTED` after contamination.

The preregistered SciFact identities were re-established only as frozen inputs. No independent archive reconstruction or licensing re-verification was completed in this run.

## 4. Evaluator independent cross-check

`INDEPENDENCE NOT ESTABLISHED`.

The only available isolated-agent surface attempted returned HTTP 429 before a session could be created. No same-context substitute was used. Evaluator A outputs were not opened for a new comparison.

## 5. Evaluator-contract defects

`NOT_EXECUTED` in this run.

No new ambiguity/defect claim is made about the frozen PR #21 contract.

## 6. Independent adjudication

`NOT_EXECUTED`.

Adjudicator A frozen record: not created.

Adjudicator B frozen record: not created.

## 7. Disagreement structure

`NOT_EXECUTED`.

No agreement coefficient or zero-disagreement claim is reported.

## 8. Published-qrel comparison

`NOT_EXECUTED`.

No FreshStack qrel or SciFact evidence comparison occurred.

## 9. Segmentation stability

`NOT_EXECUTED`.

No passage-materialization or representation comparison occurred.

## 10. Gold invariance

`NOT_EXECUTED`.

No meaning-preserving or meaning-changing scientific controls were run.

## 11. Project-control analysis

`NOT_EXECUTED` for case-level scientific influence classification.

The project did not modify the frozen corpus selection, query selection, segmentation rules, relevance contract, or evidence-group semantics in this run.

## 12. Contamination/exposure

- production BM25 exposed: `false`
- Hybrid exposed: `false`
- Semantic-only exposed: `false`
- Evidence Bundler dense exposed: `false`
- Evidence Bundler lexical exposed: `false`
- substitute/candidate retriever exposed: `false`
- FreshStack candidate-list exposure: `false`
- FreshStack published retrieval-result exposure: `true`
- FreshStack published qrel exposure before gold freeze: `false`
- SciFact published evidence/rationale exposure before gold freeze: `false`
- scientific gold creation state: `NOT_EXECUTED`

Exact retrieval-result exposure is preserved in `contamination-exposure-log.md`.

## 13. Falsified alternatives

The following alternative is falsified for this execution:

- `The rerun remained clean of prohibited FreshStack retrieval-result exposure.`

No scientific alternatives about provenance, source aperture, segmentation, adjudication, qrel leakage, metadata leakage, evaluator semantics, or corpus-specific gold stability were tested after the stop.

## 14. Strongest remaining alternative

The strongest remaining alternative is procedural rather than scientific:

> Pilot 0A may still be methodologically viable, but the current information-acquisition path is too permissive because a search result can inline forbidden benchmark-result content even when the query is source-oriented.

This must be tested in a new execution context, not repaired here.

## 15. Terminal disposition

`FALSIFIED`

Reason: explicit clean-room retrieval-result exposure falsifier.

This does not authorize any 24-30 case apparatus, production BM25, Hybrid, Semantic-only, dense, lexical, or substitute retrieval execution.

## 16. Smallest next authorized task

Run the exact frozen ten-case Pilot 0A completion again from a fresh context with a mechanically narrower acquisition policy:

1. do not use general web/search rendering for FreshStack source reconstruction;
2. acquire only exact pinned dataset files, exact source-code files, Git objects, and immutable upstream blobs by direct path/commit;
3. pre-block FreshStack README, website, paper, leaderboard, retrieval/evaluation documentation, and qrel/candidate-list surfaces before any source reconstruction;
4. establish a genuinely isolated evaluator-B session before evaluator A comparison;
5. only after provenance/aperture and evaluator-independence gates pass, create two isolated scientific adjudication contexts;
6. preserve the exact PR #20 object unchanged.

The cheapest discriminator is therefore not another benchmark modification. It is whether a fresh execution with mechanically source-only acquisition and real isolation can complete Gate 1 without prohibited exposure.

# Required durable-record status map

1. live starting state - `RECORDED`
2. frozen Pilot 0A identities - `RECORDED`
3. clean-room access allow-list - `RECORDED`
4. contamination/exposure log - `RECORDED`
5. FreshStack official/historical provenance join - `NOT_EXECUTED`
6. failed/ambiguous FreshStack joins - `NOT_EXECUTED`
7. FreshStack source-aperture decision - `NOT_EXECUTED`
8. SciFact immutable acquisition record - `NOT_EXECUTED`
9. licensing decision - `NOT_EXECUTED`
10. source hashes - `NOT_EXECUTED`
11. passage correspondence - `NOT_EXECUTED`
12. evaluator-B access audit - `RECORDED: isolation surface 429; no session created`
13. evaluator-B implementation identity - `NOT_CREATED`
14. evaluator A/B cross-check - `NOT_EXECUTED`
15. evaluator disagreement record - `NOT_EXECUTED`
16. adjudicator A frozen record - `NOT_CREATED`
17. adjudicator B frozen record - `NOT_CREATED`
18. adjudication comparison - `NOT_EXECUTED`
19. published-qrel comparison - `NOT_EXECUTED`
20. segmentation/gold stability - `NOT_EXECUTED`
21. corpus-authoring influence audit - `NOT_EXECUTED`
22. deviations - `RECORDED: isolation HTTP 429; prohibited FreshStack retrieval-result exposure`
23. terminal methodology decision - `RECORDED: FALSIFIED`
24. machine-readable receipt - `RECORDED`

## Non-claims

This run does not establish FreshStack provenance failure, FreshStack aperture failure, SciFact reconstruction failure, evaluator-contract failure, scientific-gold instability, passage-instability, Evidence Bundler retrieval performance, benchmark difficulty, or invalidity of the frozen Pilot 0A object.