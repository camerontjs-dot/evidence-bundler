# EB Retrieval + Aperture Assurance RC1

**PR class:** Research
**Production impact:** None
**Base:** `evidence-bundler` production `main` at `c8189c31adbab11729c31430c2070126224a2d42`

## Decision this experiment supports

Decide which retrieval/aperture capabilities Evidence Bundler can legitimately claim, which failure modes require engineering changes, and what upstream Contract-A state is actually necessary for EB to construct a defensible evidence world.

This experiment does **not** test whether CAL's semantic judgments are correct. It tests evidence-world construction before Contract B.

## Claim under review

> For a frozen corpus and explicit audit target, Evidence Bundler can retrieve materially relevant evidence and counterevidence with measurable recall, preserve exact provenance, and expose enough search/aperture state that downstream consumers can distinguish searched/observed coverage from unmeasured completeness.

## Current observed evidence

- Evidence Bundler production `main` participates as the real producer in the promoted Contract-B 1.2.0 path.
- Contract-B promotion establishes a bounded producer/contract/consumer interface claim. It does not establish retrieval completeness, source authority, corpus quality, or retrieval-evaluator correctness.
- Current EB contains lexical and semantic retrieval machinery, but green local tests alone do not establish recall over known relevant evidence or calibrated aperture claims.

## Main hypotheses

### H1 — Known-answer retrieval
Given a frozen corpus with adjudicated relevance, EB retrieves material relevant passages within a declared top-k/search budget often enough to support a bounded retrieval claim.

### H2 — Counterevidence sensitivity
Meaningful contradicting, qualifying, limiting, superseding, or exception-bearing evidence is not systematically suppressed by query wording or retrieval lane.

### H3 — Aperture honesty
EB output distinguishes what was searched, nominated, reviewed, admitted, missed, or not measured. Limited search never becomes an implicit completeness conclusion.

### H4 — Provenance stability
Retrieved/admitted passages retain source, representation, anchor, and content identity through output construction without silent drift.

## Alternative explanations to keep alive

- Apparent recall may come from corpus construction that makes answers lexically trivial.
- Poor recall may be caused by a bad query/decomposition rather than the retriever itself.
- A benchmark may overfit one document style or domain.
- Top-k recall may look good while rare but decisive counterevidence remains systematically missed.
- Passage-overlap metrics may not measure whether the passage contains the decision-relevant fact.

## Required frozen corpus properties

The decisive corpus must be generated independently of EB's observed ranking outputs and frozen before the first decisive run. It must include:

- exact source bytes or stable local representations;
- source IDs and content hashes;
- document/version/effective-date identity where relevant;
- exact passage/span gold anchors;
- claim/audit propositions;
- adjudicated relevance roles used only as benchmark labels, never EB runtime hints;
- hard negatives and near-miss distractors;
- contradicting/qualifying evidence;
- duplicate/paraphrased evidence;
- terminology/synonym drift;
- numeric, temporal, negation, conditional, exception, and version-sensitive cases;
- deliberately absent-answer cases;
- cases where relevant evidence exists outside an intentionally bounded search subset;
- decomposition variants where specified by the sibling experiment.

The generator must not encode EB's expected ranking, BM25 terms, embedding neighborhood, or implementation-specific tokenization as the gold answer.

## Primary measurements

Record per case and aggregated by challenge family:

- passage recall@k;
- source recall@k;
- first relevant rank / reciprocal rank;
- decisive-counterevidence recall@k;
- false nomination rate against adjudicated hard negatives;
- admitted-evidence recall where EB admission is exercised;
- provenance/anchor round-trip exactness;
- emitted search/aperture state;
- explicit unknown/abstain behavior where required evidence is absent.

Do not collapse all metrics into one score before inspecting failure classes.

## Controls and metamorphic tests

- **Positive control:** lexically obvious relevant passage should be found.
- **Negative control:** no-answer corpus must not manufacture relevance/completeness.
- **Synonym mutation:** preserve meaning while changing surface wording.
- **Negation/polarity mutation:** change proposition meaning and require retrieval behavior to respond.
- **Numeric mutation:** alter threshold, quantity, date, percentage, or version so a near-match becomes materially wrong.
- **Distractor injection:** add high-overlap irrelevant passages.
- **Duplicate/paraphrase injection:** prevent repeated evidence from masquerading as independent coverage.
- **Source-order permutation:** reorder source enumeration without changing semantics.
- **Search-bound mutation:** narrow the available corpus/search surface and require aperture state to narrow accordingly.

## Falsification / weakening criteria

The broad claim is falsified or materially weakened if, after validating the apparatus:

- known decisive evidence is systematically missed across a meaningful challenge family;
- high-overlap distractors reliably outrank decisive evidence without an explicit uncertainty/aperture signal;
- counterevidence is materially less retrievable than confirming evidence for equivalent cases;
- exact source/passage identity cannot be reconstructed after retrieval/admission;
- source enumeration/order changes substantive output without documented tie semantics;
- bounded/partial search is represented as if completeness were established;
- a trivial return-all strategy can obtain an unqualified passing result.

## Evaluator validation

Before using this benchmark as a promotion gate:

1. verify gold anchors against source bytes;
2. independently adjudicate a stratified sample of relevance labels;
3. seed false-relevance and false-irrelevance labels and confirm adjudication detects them;
4. confirm an intentionally weak retriever fails challenge families it should fail;
5. confirm a return-all baseline is penalized or separately classified;
6. preserve benchmark corrections as explicit deviation records.

## Planned result record

Separate:

- observed retrieval measurements;
- inference about EB capability;
- benchmark/evaluator limitations;
- failure taxonomy;
- engineering hypotheses;
- Contract-A input requirements exposed by failures;
- supported and unsupported assurance claims.

## Stop condition

Do not redesign retrieval merely because a result is surprising. First test whether the corpus, labels, query construction, extraction, or metric could explain the observation.

Production changes require a separate promotion decision after research disposition.
