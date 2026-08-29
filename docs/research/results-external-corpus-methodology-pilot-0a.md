# External Corpus Methodology Pilot 0A — Execution Record

The hard part turned out to be upstream of passage adjudication. The preregistration could be frozen cleanly, and the dummy evaluator / hidden-gold mechanics behaved as intended, but this execution did not obtain the frozen scientific bytes or two genuinely independent adjudicators. I therefore do not treat the unexecuted core as evidence of passage or gold stability.

## 1. Live repository starting state

**OBSERVED**

- Evidence Bundler production `main` was `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`.
- RC4 apparatus #18 was terminal `FALSIFIED`.
- RC4 target #17 was closed `SUPERSEDED WITHOUT TARGET EXECUTION`.
- RC3 apparatus #16 was terminal `FALSIFIED`.
- RC3 target #15 was superseded without Hybrid / Semantic-only exposure.
- Apparatus Contracts #8 explicitly terminated the exact synthetic challenge-construction program and authorized a methodology reassessment rather than RC5.
- Apparatus Contracts #9 remains the living evaluator-assurance registry.
- Pilot 0A was preregistered on a fresh branch before scientific relevance inspection.

**INFERENCE**

The correct successor is a methodology record, not another retrieval run.

## 2. Corpus eligibility and P1 provenance / licensing / reconstruction audit

### FreshStack

**OBSERVED**

- The unfiltered October 2024 query dataset contains 1,149 real Stack Overflow questions across five topics and explicitly includes cases with zero generated relevant documents.
- FreshStack states that GPT-4o generated nuggets and labeled nugget-to-document relevance.
- The official `freshstack/corpus-oct-2024` corpus contains 271,842 chunks and declares CC-BY-SA-4.0 while warning that underlying GitHub repositories may have different/non-permissive licenses.
- The official corpus schema exposes `_id`, `text`, and metadata containing `url`, `start_byte`, and `end_byte`; it does not expose `commit_id`.
- The earlier `nthakur/corpus-oct-2024` viewer exposes the same form of chunk IDs/text plus a short `commit_id`.
- The FreshStack construction code at `f1c4ec96477f5100f10c83798d33b3101db727fa` records the cloned repository HEAD and writes it as `metadata.commit_id`, while the source URL is built against the mutable default branch.
- The acquisition code shallow-clones the repository's current default branch rather than an explicit preregistered commit.
- This runtime could inspect cards, code, revisions, and object hashes, but could not resolve the Hugging Face binary host to fetch the selected Parquet bytes.

**INFERENCE**

The official transferred corpus is not, by itself, a complete durable source-reconstruction record because its published URL is mutable and its current schema has dropped the commit identifier produced by the construction code. A deterministic provenance-restoration join against the historical `nthakur` corpus may recover the source commit without changing passage text, but that join has not been executed or byte-verified here.

A second and more important problem is query-specific source aperture. FreshStack's published nugget-document labels are over a document list produced by its own benchmark-construction retrieval process. Using those candidate lists to choose passages for our independent gold would violate Pilot 0A's pre-retrieval firewall. I found no external, qrel-independent query-to-source mapping that can be used instead. Reviewing the entire 25k–117k-passage topic corpus per query is not a bounded adjudication protocol.

**UNKNOWN**

- Whether every official chunk can be deterministically joined to exactly one historical row carrying a recoverable full Git commit.
- Whether an upstream artifact exists that maps each Stack Overflow question to source documents independently of FreshStack's retrieval-generated candidate list.
- The per-repository redistribution obligations for the exact sampled source files.

**Corpus disposition:** `INCONCLUSIVE` for reconstruction; `UNRESOLVED / NOT ELIGIBLE YET` for a clean bounded source aperture.

### SciFact

**OBSERVED**

- Canonical upstream repository HEAD inspected: `68b98a56d93e0f9da0d2aab4e6c3294699a0f72e`.
- Upstream `LICENSE.md` states claims/evidence annotations are CC BY 4.0, abstracts are S2ORC material under ODC-By 1.0, and code is Apache 2.0.
- The official acquisition script downloads `release/latest/data.tar.gz`, which is a mutable path.
- A historical Hugging Face dataset-info record pins that archive to SHA-256 `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`, 3,115,079 bytes.
- The Hugging Face mirror displays a conflicting dataset-level CC-BY-NC-2.0 label; its dataset-info `license` field is empty.
- Canonical claims have `cited_doc_ids` separate from the evidence/rationale field, making a non-retrieval source aperture possible in principle.
- This runtime could not acquire the archive bytes from S3.

**INFERENCE**

SciFact has a much cleaner pre-retrieval source-aperture design than FreshStack: `cited_doc_ids` can nominate the permitted source world without reading published rationale labels. The recorded archive hash can detect drift, but the mutable `latest` URL is not itself an immutable acquisition locator.

**UNKNOWN**

- Whether the historical archive bytes remain reacquirable from an immutable upstream location.
- Whether the mirror's license label reflects an intended downstream restriction or stale/incorrect metadata.
- Exact selected claim/source bytes and their hashes, because the pinned archive was not materialized here.

**Corpus disposition:** `PARTIALLY ELIGIBLE`, blocked on frozen-byte acquisition and license-discrepancy resolution.

## 3. Passage-mapping specification

The two representations were frozen in the preregistration before scientific labels:

1. external/native boundaries;
2. deterministic left-to-right segmentation capped at 1,200 Unicode scalar values with a frozen LF/whitespace/hard-cut fallback and no overlap.

No case-specific boundary moves, paraphrases, bridge phrases, lexical deletions, manual merges, or synthetic negatives are allowed.

FreshStack Representation 1 uses the published corpus `text` field only. SciFact Representation 1 uses each original abstract sentence. Representation 2 must be generated from a reconstructable parent source/document, not from qrels.

## 4. Passage correspondence manifest

**OBSERVED**

No scientific passage correspondence rows were produced.

**Reason**

The selected pinned query/claim/source bytes could not be acquired in this runtime. Creating passage IDs or hashes from search-result snippets would not meet the reconstruction contract.

**Disposition**

`NOT EXECUTED`, not a pass and not a fabricated empty success.

## 5. Relevance contract

The frozen contract distinguishes `DECISIVE`, `PARTIAL`, `TOPICAL`, `IRRELEVANT`, and `UNKNOWN`; semantic roles `SUPPORT`, `COUNTEREVIDENCE`, `NEUTRAL_OR_NOT_APPLICABLE`, and `UNKNOWN`; and `JOINTLY_REQUIRED` versus `ALTERNATIVE_SUFFICIENT` evidence groups.

FreshStack questions are not forced into support/refute semantics. `UNKNOWN` is not silently converted to irrelevant.

## 6. Independent adjudication results

**OBSERVED**

No scientific relevance labels were produced.

Two genuinely independent adjudicators were required. The intended Conduit isolation surface failed first with HTTP 429 and then HTTP 404. I did not replace that with two outputs from the same supervisory context.

**INFERENCE**

The independence requirement remains untested rather than failed scientifically. Duplicating one model's reasoning would have made the evidence look stronger while weakening its meaning.

## 7. Disagreement taxonomy / adjudication record

No adjudicator pair exists, so all disagreement counts remain unobserved.

The preregistered taxonomy remains:

- passage-boundary disagreement;
- support vs topical-relatedness disagreement;
- contradiction/counterevidence disagreement;
- query underspecification;
- source-context insufficiency;
- multiple valid evidence passages;
- relevance-degree disagreement;
- document-level versus passage-level mismatch;
- genuine domain uncertainty;
- annotation error;
- unresolved.

No zero-count table is reported because zero observed disagreements and no observations are different claims.

## 8. Segmentation sensitivity and gold-stability report

### Scientific gold

`NOT EXECUTED`.

Without frozen source bytes and independent labels, this task cannot claim that evidence existence, answerability, source identity, semantic role, or evidence-group structure is stable across the two passage representations.

### Dummy evaluator controls

P2 exercised source/passage registry-order invariance, stable passage-ID renaming, unknown handling, graded-label sensitivity, counterevidence-role sensitivity, K enforcement, identity/provenance rejection, duplicate rejection, rank validation, and malformed evidence-group failure. Those are evaluator-contract mechanics only.

The first dummy counterevidence mutation was preserved as non-discriminating: it changed the role of a passage that was already retrieved alongside the original counterevidence, so recall stayed 1.0. A corrected dummy-only mutation flipped an unretrieved passage and changed counterevidence recall from 1.0 to 0.5. No scientific fixture or threshold changed.

## 9. Corpus-authoring influence audit

| Variable | FreshStack | SciFact | Current implication |
|---|---|---|---|
| corpus-family selection | PROJECT_DISCRETIONARY, preregistered | PROJECT_DISCRETIONARY, preregistered | bounded but still a project choice |
| query/claim content | EXTERNALLY_FIXED | EXTERNALLY_FIXED | strong |
| sample selection | DETERMINISTICALLY_DERIVED | DETERMINISTICALLY_DERIVED | strong |
| source selection | UNKNOWN / unresolved without retrieval-generated candidates | EXTERNALLY_FIXED through `cited_doc_ids` | FreshStack is the weak seam |
| native segmentation | EXTERNALLY_FIXED | EXTERNALLY_FIXED | strong |
| Representation 2 | DETERMINISTICALLY_DERIVED | DETERMINISTICALLY_DERIVED | strong if parent bytes exist |
| relevance interpretation | UNKNOWN pending independent adjudication | UNKNOWN pending independent adjudication | promotion-critical missing evidence |
| negative definition | UNKNOWN pending independent adjudication | UNKNOWN pending independent adjudication | must not inherit published qrels by default |
| metadata availability | EXTERNALLY_FIXED, with mutable URL / missing official commit ID | EXTERNALLY_FIXED | requires invariance tests |
| evaluator representation | DETERMINISTICALLY_DERIVED | DETERMINISTICALLY_DERIVED | dummy mechanics exercised |

**INFERENCE**

Project discretion has been reduced for sampling and segmentation, but it has not yet been reduced enough for the decisive relevance relationship because independent adjudication is absent. FreshStack additionally lacks a clean bounded source-selection mechanism under the no-retrieval rule.

## 10. P2 evaluator-contract preparation

Two separate Python implementations were written against dummy fixtures only.

They agree on the base dummy metrics:

- hit@K = 1
- evidence recall@K = 2/3
- nDCG@K = 0.9072836011519267
- counterevidence recall@K = 1.0
- evidence-group coverage@K = 0.5

Both fail closed on the preregistered malformed-input classes exercised.

**Boundary:** the implementations were authored in the same supervisory context. This is a differential cross-check, not an E4 independent implementation claim and not evidence that scientific gold is valid.

## 11. P3 blind-handoff rehearsal

Dummy-only handoff mechanics passed.

- public manifest SHA-256: `350d785a41b8d46e6e244c76f03de503d643e206d2819e8e5cad147dbe9bd4e4`
- hidden-gold commitment SHA-256: `43854ac4ae6d804ae7682252dcc35fa31cad7477cce7210bd7b9cc280891a21d`
- execution packet contained no `judgments`, `grade`, or `role` keys;
- revealed dummy gold reproduced the commitment exactly.

This establishes only that a precommit/reveal packet can be represented and verified. It does not establish operational secrecy against an actor with repository access or scientific benchmark validity.

## 12. Failures and deviations

1. **Conduit isolation unavailable.** First probe returned HTTP 429; retry returned HTTP 404. No independent-adjudicator substitute was manufactured.
2. **Binary source acquisition unavailable in this runtime.** DNS resolution failed for Hugging Face from the local execution container; SciFact S3 bytes were likewise not materialized. Web-visible metadata/revisions/checksums were inspected, but scientific bytes were not reconstructed from snippets.
3. **FreshStack provenance gap observed.** Current official corpus schema omits the `commit_id` that the construction code writes and that the historical `nthakur` viewer exposes.
4. **FreshStack source-aperture gap observed.** No clean query-specific source mapping independent of FreshStack's retrieval-generated candidate list was established.
5. **P2 non-discriminating dummy mutation preserved.** The first role flip could not change counterevidence recall because the modified passage was already retrieved. The corrected dummy control changed only the dummy test stimulus, before any scientific exposure.

None of these deviations exposed production BM25, Hybrid, or Semantic-only output.

## 13. Contamination / exposure state

- production BM25 exposed: `false`
- Hybrid exposed: `false`
- Semantic-only exposed: `false`
- FreshStack published qrels used for scientific labels: `false`
- SciFact published evidence/rationale labels used for scientific labels: `false`
- scientific gold created: `false`

The task remains clean with respect to the prohibited retrieval systems, but incomplete with respect to its scientific evidence requirements.

## 14. Strongest alternative explanation

The strongest remaining alternative is **native construction leakage / shared cue structure**, not retrieval-system performance.

FreshStack's generated relevance labels are attached to a candidate document list created inside FreshStack's own retrieval-oriented construction process. Even if later independent adjudicators agree with those labels, that agreement could partly reflect a source world pre-shaped by retrieval rather than a query-to-corpus relation that was independently sampled. Using the unfiltered query set removes one selection bias, but it does not solve source-aperture leakage.

For SciFact, the strongest alternative is different: two reviewers could share the same mistaken interpretation of a scientific claim or a sentence boundary could make rationale evidence appear more self-contained than the underlying document relation. That is exactly what the unexecuted two-adjudicator / two-representation test is meant to discriminate.

## 15. Cheapest remaining falsifier

Do not expand to 24–30 cases.

The cheapest discriminating continuation is to execute the **already frozen 10-case Pilot 0A object unchanged** in an environment that can:

1. fetch and hash the exact pinned FreshStack/SciFact bytes;
2. test a deterministic FreshStack official-to-historical provenance join without reading qrels;
3. either establish a qrel-independent FreshStack source aperture or record FreshStack as ineligible;
4. run two isolated adjudicators on the frozen permitted passages;
5. run the frozen segmentation and gold-stability controls.

No sample index, passage rule, relevance contract, or support criterion should change.

# Terminal methodology decision

## `INCONCLUSIVE`

**OBSERVED**

The task established a clean preregistration, deterministic sampling, meaningful corpus-provenance risks, a viable SciFact non-retrieval source aperture in principle, a blocked FreshStack source-aperture question, dummy evaluator mechanics, and dummy hidden-gold commitment mechanics. It did not materialize the scientific cases or produce two independent adjudications.

**INFERENCE**

There is not enough evidence to say the external-corpus passage/gold methodology is stable, and there is not yet enough sampled scientific evidence to falsify passage mapping or independent gold globally. Calling this supported would launder missing evidence into success. Calling the entire external-corpus method falsified would overgeneralize the FreshStack/source-access problems beyond what was tested.

**HYPOTHESIS**

SciFact can probably support the core pre-retrieval passage/gold experiment once exact bytes and independent reviewers are available. FreshStack may require a provenance-restoration layer and may still fail because its query-specific source aperture is entangled with retrieval-generated construction.

**UNKNOWN**

The promotion-critical unknown is the one the pilot was designed to answer: whether independently adjudicated evidence semantics remain stable across two reasonable deterministic passage representations on the frozen external cases.

## Smallest next authorized task

**Pilot 0A execution completion on the frozen preregistration and frozen sample, with no sample replacement and no retrieval exposure.**

This is not authorization for the 24–30-case apparatus and not authorization for production BM25, Hybrid, or Semantic-only execution.
