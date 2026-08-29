# Evidence Bundler External Corpus Methodology Pilot 0A — Preregistration

## PR class

Research Infrastructure / benchmark-methodology experiment.

## Decision

Determine whether externally authored real material can be converted into an Evidence Bundler-compatible passage-level retrieval benchmark without passage construction or relevance adjudication becoming a new project-authored benchmark surface.

Allowed terminal dispositions for this methodology task:

- `SUPPORTED FOR EXTERNAL-CORPUS PILOT`
- `FALSIFIED`
- `INCONCLUSIVE`

A supported result authorizes only a later bounded 24–30-case methodology apparatus. It does not authorize production BM25, Hybrid, Semantic-only, a final benchmark, or production promotion.

## Authority and starting state

Durable CAL Pipeline governance defines procedure; live GitHub and immutable artifacts define current state.

Evidence Bundler starting production `main`:

- `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`

Preserved predecessor routing at task start:

- #18 RC4 apparatus: terminal `FALSIFIED`;
- #17 RC4 target: `SUPERSEDED WITHOUT TARGET EXECUTION`;
- #16 RC3 apparatus: terminal `FALSIFIED`;
- #15 RC3 target: superseded without target exposure;
- #14 exact production BM25 RC2 result: preserved predecessor evidence;
- #8/#9/#12/#13: benchmark/evaluator provenance and assurance lineage.

Apparatus Contracts #8 records the synthetic-program stop and authorizes a methodological successor rather than RC5. Apparatus Contracts #9 remains the living evaluator-assurance registry.

## Hard exposure firewall

Before this scientific methodology object is frozen and this task terminates, do not run, inspect, estimate, simulate, or use output from:

- production BM25;
- Hybrid retrieval;
- Semantic-only retrieval;
- any Evidence Bundler production retriever;
- any candidate retriever whose output could influence case selection, source selection, passage construction, gold judgments, negative definition, or benchmark eligibility.

Do not select cases for lexical difficulty. Do not create RC5. Do not repair RC4. Do not reuse RC4 synthetic challenge construction.

If prohibited retrieval output is accidentally exposed, record the contamination and do not characterize affected work as clean pre-exposure methodology evidence.

Initial exposure state:

- production BM25 exposed: `false`
- Hybrid exposed: `false`
- Semantic-only exposed: `false`

## Candidate corpora and pinned upstream identities

### FreshStack

Scientific query source for sampling:

- dataset: `freshstack/queries-oct-2024-unfiltered`
- pinned known data revision: `00150066ff2959688ad03ce7148ffb652f2fee38`
- license declared by dataset: CC-BY-SA-4.0
- queries/accepted answers originate from Stack Overflow;
- nuggets and published relevance judgments are GPT-4o-generated and are withheld from initial independent adjudication.

Corpus source:

- dataset: `freshstack/corpus-oct-2024`
- pinned revision: `069f66dc323e163b48b10d08408d282733d4393b`
- license declared by dataset: CC-BY-SA-4.0, with explicit warning that underlying GitHub repositories may carry different/non-permissive licenses.

FreshStack framework reference implementation inspected at:

- GitHub: `fresh-stack/freshstack`
- commit: `f1c4ec96477f5100f10c83798d33b3101db727fa`

The scientific pilot does not accept FreshStack published qrels as gold. They may be compared only after independent labels are frozen.

### SciFact

Canonical upstream:

- GitHub: `allenai/scifact`
- master at task start: `68b98a56d93e0f9da0d2aab4e6c3294699a0f72e`
- official acquisition script points to `https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz`;
- independently recorded Hugging Face download checksum for that archive: `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`, size 3,115,079 bytes.

Official upstream licensing at the pinned repository commit:

- claims/evidence annotations: CC BY 4.0;
- abstracts/corpus: S2ORC material under ODC-By 1.0;
- code: Apache 2.0.

The Hugging Face mirror currently advertises a conflicting CC-BY-NC-2.0 dataset-level label. This discrepancy is an audit item; official upstream LICENSE.md remains the primary license statement unless contrary authoritative evidence is found.

SciFact published evidence annotations are withheld from initial independent adjudication where practical and compared only after labels are frozen.

## Pre-retrieval sample selection

Sample size is exactly 10 information needs: five FreshStack and five SciFact. No case may be replaced after relevance inspection merely because it is inconvenient, ambiguous, easy, difficult, answerable, or unanswerable.

### FreshStack selection

Use the unfiltered October 2024 query dataset so inclusion is not conditioned on FreshStack's generated relevance labels.

For each topic, select physical test-row index:

`int(SHA256("pilot0a:" + topic), 16) mod topic_row_count`

Pinned topic row counts and selected zero-based indices:

| topic | rows | selected index |
|---|---:|---:|
| langchain | 318 | 271 |
| yolo | 94 | 42 |
| laravel | 230 | 121 |
| angular | 310 | 248 |
| godot | 197 | 36 |

Only `query_id`, `query_title`, and `query_text` may be used to construct the frozen information need before adjudication. `nuggets`, `relevant_corpus_ids`, `non_relevant_corpus_ids`, and accepted-answer text are evaluator-side comparison material and must be hidden initially.

### SciFact selection

Use the canonical 300-claim development file `claims_dev.jsonl`, one original claim per physical line, rather than the Hugging Face flattened evidence-row representation.

Select five unique zero-based physical line indices by iterating `i = 0,1,...`, computing:

`int(SHA256("pilot0a:scifact:" + str(i)), 16) mod 300`

and retaining the first five unique indices.

Frozen selected indices:

- 199
- 66
- 278
- 114
- 123

Only claim ID/text and the permitted source set defined below may be used initially. Published evidence labels/rationale sentence IDs are hidden until independent labels are frozen.

## Source-aperture rule

This task tests passage mapping and gold stability, not full-corpus retrieval performance.

For each sampled information need, the adjudication aperture must be established without retrieval output:

- FreshStack: source documents are selected only from externally declared corpus/source identity and deterministic query-associated source scope available without reading published relevance labels. If no defensible non-qrel source aperture can be reconstructed, FreshStack is `INCONCLUSIVE` or `FALSIFIED` for this methodology rather than using a retriever to nominate documents.
- SciFact: use the claim's externally authored `cited_doc_ids` as the permitted adjudication source aperture. `cited_doc_ids` are source provenance, not evidence labels. Do not use the `evidence` field to select passages or documents initially.

A source aperture may contain no relevant passage. That is a legitimate result.

## Passage representations frozen before label inspection

The experiment compares two reasonable, deterministic representations. Passage IDs may differ; semantic evidence relationships are the object of the stability test.

### Representation 1 — external/native boundaries

FreshStack:

- use the externally published FreshStack corpus chunk as the native accepted chunk;
- passage bytes are the corpus `text` field exactly, not filename/path metadata;
- parent source identity is reconstructed from corpus `_id`, `metadata.url`, offsets, and commit identity where available;
- do not prepend filename/path to passage text.

SciFact:

- each abstract sentence in the canonical corpus array is one native passage;
- sentence order/index is preserved;
- title/document identifiers remain metadata, not passage content.

### Representation 2 — deterministic bounded segmentation

Construct from the reconstructable parent source/document representation, not from relevance outcomes.

Algorithm:

1. normalize line endings only: CRLF/CR -> LF; preserve all other text exactly;
2. consume source text left-to-right with a hard maximum of 1,200 Unicode scalar values per passage;
3. when more than 1,200 remain, choose the last LF at or after position 600 and at or before 1,200; if none exists, choose the last ASCII whitespace at or after 600 and at or before 1,200; if none exists, hard cut at 1,200;
4. no overlap;
5. do not trim internal or boundary text except that the exact separator chosen for the cut remains assigned to the preceding passage;
6. deterministic passage ID = `sha256(parent_source_identity || representation_id || start || end || exact_passage_bytes)`.

For SciFact, the parent document representation for Representation 2 is the abstract sentence array joined with a single LF between original sentence strings. For FreshStack it is the exact upstream source file at the recorded corpus commit where reconstructable.

No passage boundary may be moved case-by-case. No paraphrase, bridge phrase, lexical deletion, manual merge, or synthetic negative construction is permitted.

## Required passage correspondence

For every passage record:

- corpus family;
- information-need ID;
- parent external source identity;
- source snapshot/version/commit identity;
- representation ID;
- start/end correspondence in the normalized parent representation;
- original/native boundary identity where applicable;
- exact transformation rule;
- deterministic passage ID;
- SHA-256 of exact passage bytes;
- SHA-256 of parent source/document representation when available.

Upstream source bytes, normalized bytes, and Evidence Bundler passage bytes must remain distinguishable.

## Relevance contract frozen before adjudication

Labels are passage-to-information-need relations, not retrieval scores.

Primary relevance degree:

- `DECISIVE`: passage contains evidence necessary or independently sufficient to resolve a material part of the information need within the permitted source world;
- `PARTIAL`: passage materially advances resolution but is insufficient alone and is not merely topical;
- `TOPICAL`: same subject/entity but does not materially answer/verify the information need;
- `IRRELEVANT`: no material relation;
- `UNKNOWN`: relation cannot be responsibly determined from the permitted context.

Semantic role when justified by the source task:

- `SUPPORT`
- `COUNTEREVIDENCE`
- `NEUTRAL_OR_NOT_APPLICABLE`
- `UNKNOWN`

FreshStack technical questions need not be forced into support/refute framing. `SUPPORT` means directly helps answer/establish the requested technical fact/action; `COUNTEREVIDENCE` is used only for material contrary/exception/version evidence.

SciFact claims may use SUPPORT/COUNTEREVIDENCE when the passage actually bears on truth of the claim. Published SciFact labels are not consulted initially.

Multi-passage groups:

- assign a stable `evidence_group_id` only when two or more passages are jointly necessary for a material answer/evidence relation;
- record whether the group is `JOINTLY_REQUIRED` or passages are `ALTERNATIVE_SUFFICIENT`;
- do not collapse multiple legitimate bases into one arbitrary winner.

Unknown/unjudged passages receive no relevance credit and remain explicitly distinguishable from irrelevant.

## Independent adjudication protocol

A positive methodology result requires at least two genuinely independent adjudications.

Each adjudicator receives only:

- frozen information need;
- permitted frozen source/passages in both representations;
- this frozen relevance contract.

They must not receive:

- the other adjudicator's decisions or reasoning;
- published FreshStack qrels/nuggets/accepted-answer text initially;
- published SciFact evidence labels/rationale sentence IDs initially;
- production BM25, Hybrid, Semantic-only, or any other candidate retriever output;
- expected benchmark difficulty;
- RC3/RC4 case-design material;
- desired lexical-overlap characteristics;
- desired terminal disposition.

Each adjudicator record must be frozen before comparison. Disagreements then enter a separately reasoned adjudication stage. Unresolved cases remain `UNKNOWN`/ambiguous rather than being forced.

If genuine independence cannot be established, this task cannot use one model's duplicated reasoning as two adjudicators. The independence gate becomes an explicit missing-evidence condition for the final disposition.

## Disagreement taxonomy

Every disagreement must be classified as one or more of:

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

Agreement coefficients may be reported only as supplements to this taxonomy.

## Gold-stability controls

Meaning-preserving transformations expected invariant in semantic gold:

- source-order permutation;
- stable passage-ID renaming with mapping retained;
- serialization reorder;
- removal of irrelevant metadata such as filenames/paths when not semantically part of source text;
- mapping between the two preregistered passage representations where semantic content is preserved.

Meaning-changing controls expected sensitive when applicable:

- negation;
- altered quantity;
- altered version/applicability;
- SUPPORT ↔ COUNTEREVIDENCE semantic flip.

Mutations test gold/evaluator behavior only and are not new retrieval examples.

## Corpus-authoring influence audit

For each case classify project control over:

- corpus selection;
- query selection;
- source selection;
- passage segmentation;
- relevance interpretation;
- negative definition;
- metadata availability;
- evaluator representation.

Allowed categories:

- `EXTERNALLY_FIXED`
- `DETERMINISTICALLY_DERIVED`
- `INDEPENDENTLY_ADJUDICATED`
- `PROJECT_DISCRETIONARY`
- `UNKNOWN`

The methodology fails if decisive semantic relationships remain materially project-discretionary.

## Explicit alternative explanations to test

1. adjudicators follow the same superficial textual cues;
2. native dataset construction already leaks relevance;
3. segmentation makes relevant passages artificially self-contained;
4. published qrels bias subsequent adjudication;
5. query wording uniquely identifies source type;
6. metadata acts as a relevance proxy;
7. external corpus selection narrows to one easy genre;
8. independent reviewers share the same mistaken interpretation.

## Parallel lane P1 — provenance/licensing/reconstruction

Independently establish source/dataset versions, frozen acquisition, licenses/redistribution, source stability, query/relevance provenance, missing artifacts, and passage reconstruction feasibility. Do not select cases using retrieval difficulty.

## Parallel lane P2 — evaluator contract preparation

Dummy fixtures only. Minimum evaluator contract must represent queries, sources/passages/provenance, binary/graded relevance where justified, semantic roles, evidence groups, ranked outputs, K, and unknown/unjudged passages.

Prepare metrics/validation for:

- hit@K;
- evidence recall@K;
- nDCG only where graded relevance is legitimately defined;
- counterevidence recall;
- evidence-group coverage;
- K enforcement;
- identity/provenance validation;
- malformed-input fail-closed behavior.

A second implementation may be prepared against synthetic fixtures only. It must not inspect scientific pilot gold if doing so would weaken later independence.

## Parallel lane P3 — dummy blind-handoff rehearsal

Dummy artifacts only.

Construction side exposes public corpus/query manifest, evaluator contract, and hidden-gold hash commitment. Execution side reconstructs permitted inputs without hidden qrels or construction reasoning. Reveal dummy gold afterward and verify precommitted hash exactly.

This lane tests isolation mechanics, not retrieval quality.

## Primary falsifiers

### Falsifier A — reconstruction

For a corpus, falsify if durable reconstruction requires unavailable data, unstable mutable sources with no defensible snapshot, prohibited redistribution for the intended artifact, or undocumented choices that cannot be reproduced.

### Falsifier B — passage mapping

Falsify or mark inconclusive if the two reasonable deterministic representations materially change evidence existence, semantic role, decisive source identity, answerability, or required evidence roles such that discretionary benchmark-author intervention is needed.

### Falsifier C — independent gold

Falsify if independently produced labels cannot be stabilized because disagreements expose a systematic ambiguity in the corpus/query/source relationship. Mark `INCONCLUSIVE` if the required independent process cannot actually be executed or its isolation cannot be established.

### Falsifier D — authoring influence

Falsify if project discretion dominates the decisive semantic relationship despite external source/query authorship.

### Falsifier E — isolation

Falsify if clean pre-retrieval methodology isolation is breached by prohibited retrieval exposure or hidden-gold leakage. Operational inability to execute a required independent lane without evidence of contamination is `INCONCLUSIVE`, not silently repaired.

## Terminal support rule

`SUPPORTED FOR EXTERNAL-CORPUS PILOT` requires all of:

- reconstructable external sources and durable provenance;
- sufficient licensing for intended research artifacts;
- deterministic passage mapping without outcome-driven surgery;
- stable relevance semantics across the two reasonable representations;
- sufficiently stable genuinely independent adjudication;
- preserved/explainable disagreement;
- decisive relationship not dominated by project authorship;
- no prohibited retrieval exposure.

## No retrieval-difficulty gate

This experiment will not ask whether BM25 is weak, Hybrid is stronger, lexical overlap is low enough, or a corpus makes Hybrid look favorable. Descriptive lexical overlap, if ever computed, cannot affect inclusion/exclusion.

## Stop rule

Stop with a terminal disposition when:

- all support conditions are observed;
- a preregistered promotion-critical falsifier is observed;
- the next scientific step would violate the exposure/isolation boundary; or
- the remaining uncertainty requires a new experiment rather than additional implementation.

Preserve failures and deviations. Do not repair this exact scientific sample around an observed methodological failure.
