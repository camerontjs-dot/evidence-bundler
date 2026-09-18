# EB Gate Specialty Selector RC1 — Fresh Cohort Contract

## Purpose

Author a fresh cohort that can distinguish claim-specific expected specialty forms from semantic-only selection and from non-specific specialty preferences.

The cohort is not allowed to define evidence usefulness by form identity. Evidence form is an experimental input and stress dimension, not the gold answer.

## Cohort size

Author exactly **36 fresh lanes**, exactly 6 from each category:

1. **authoritative-declaration conflict**  
   Claim Gate must freeze `authoritative_declaration` as a supported expected specialty. The corpus must contain plausible competing specialty-form evidence.

2. **event-record conflict**  
   Claim Gate must freeze `event_record` as a supported expected specialty. The corpus must contain plausible competing specialty-form evidence.

3. **registry-entry conflict**  
   Claim Gate must freeze `registry_entry` as a supported expected specialty. The corpus must contain plausible competing specialty-form evidence.

4. **multi-specialty conflict**  
   Claim Gate must freeze at least two supported specialties among `authoritative_declaration`, `event_record`, and `registry_entry`.

5. **anti-tautology specialty trap**  
   Claim Gate must freeze at least one supported specialty, but corpus construction must include both:
   - at least one candidate in an expected specialty form that is later independently adjudicated unsafe, misleading, distractor, or redundant; and
   - at least one useful candidate in a non-expected specialty or ordinary document/measurement form.

6. **no-specialty controls**  
   Claim Gate must freeze no supported specialty form. Author exactly 3 positive ordinary lanes and exactly 3 no-clear-suitable lanes.

Categories describe fixture geometry, not expected selector behavior.

## Freshness

All claims, entities, values, organizations, source text, measurements, event descriptions, registry records, declarations, and evidence arrangements must be authored from scratch in the context-free lane.

Do not mutate or paraphrase any prior Gate-selector development fixture or prior RC1 selector cohort.

## Authoring and freeze order

Use this order:

1. author all claim texts;
2. freeze claim texts;
3. generate Claim Gate profiles mechanically from the exact pinned Claim Profile authority;
4. freeze profiles and their hashes;
5. verify category eligibility from the frozen profiles only;
6. author source corpora and intended evidence-form metadata;
7. freeze corpus bytes and metadata;
8. run exact frozen first-stage retrieval to depth 10;
9. freeze candidate pools;
10. compute exact pinned semantic scores for every top-10 candidate;
11. freeze semantic scores;
12. adjudicate gold without target access;
13. freeze gold;
14. author and test the target-agnostic evaluator;
15. freeze evaluator, cohort eligibility, source-access log, and prereveal receipt.

Claims/profiles may not be repaired after corpus authoring begins. Corpus may not be repaired after target information becomes available.

## Claim Profile authority

Generate profiles using the exact Proposition Authoring subject:

`e29a165b682d060f5dc2a0f3c7d64a7f29b172b4`

Use `build_claim_profile(AuthoringRequest)` from claim text alone.

Do not manually write or override `expected_evidence_forms`.

Supported experiment-level specialty vocabulary:

- `authoritative_declaration`
- `event_record`
- `registry_entry`

Other profile forms may remain in the frozen profile but do not change category counting.

## Corpus construction

Target 12–20 source passages per lane before retrieval.

Each source fixture must include independently authored metadata describing its intended source/evidence form. This metadata:

- is authored before retrieval;
- is not gold;
- may be used for cohort eligibility and audit;
- is outside the frozen selector's target input contract;
- must not be edited after candidate or gold inspection.

For categories 1–4, aim to make specialty identity genuinely discriminating without using hidden target behavior. Each lane should contain naturalistic, same-topic material in more than one specialty form where feasible.

For category 5, expected-form membership must not imply usefulness. The category exists specifically to falsify that shortcut.

Avoid trivial cues:

- no IDs or headings containing `gold`, `correct`, `required`, `unsafe`, `distractor`, `support`, or `refute`;
- no formatting unique to useful candidates;
- no answer keys or usefulness labels in metadata visible to execution arms;
- do not systematically make useful passages shorter, longer, or more numerically dense unless that is the lane's declared difficulty.

## Frozen first-stage retrieval

Use exact Evidence Bundler integration candidate:

`4e1f6fe00e7c350b28f52bfea14f1f8988847884`

Candidate depth is exactly 10.

Do not change tokenizer, BM25 behavior, chunking, query generation, source aperture, ranking, candidate depth, or ranking history.

Preserve the full top-10 pool. Retained-K behavior is not part of cohort authoring.

## Frozen semantic scorer

For every frozen top-10 pool, score claim/candidate pairs with:

- model: `cross-encoder/ms-marco-MiniLM-L6-v2`
- revision: `233902d25c440f23af6f7d6e94d2946bac0bee0a`
- transform: sigmoid of the single output logit
- max length: 512
- deterministic eval mode

Freeze semantic scores before gold adjudication.

## Lane eligibility

A positive lane is eligible when:

- first-stage retrieval deterministically returns 10 unique candidates;
- at least one candidate later adjudicated `REQUIRED` or `USEFUL_DISTINCT` is in the top 10;
- at least one non-useful competitor is in the top 10;
- no target/development information was used to construct or repair the lane.

A no-clear-suitable lane is eligible when:

- first-stage retrieval returns 10 unique candidates;
- none is later adjudicated `REQUIRED` or `USEFUL_DISTINCT`;
- it remains a meaningful selection-burden test.

For categories 1–4, the frozen top-10 pool must contain passages from at least two intended specialty-form families, including the claim's frozen expected specialty and at least one non-expected specialty, unless a prereveal replacement is made from scratch.

For category 5, the frozen top-10 pool must preserve the anti-tautology geometry specified above.

If a lane fails eligibility after retrieval/gold adjudication, preserve it in the deviation log and author a new lane from scratch under the same category. Do not patch the failed lane.

## Gold schema

Adjudicate every top-10 candidate into exactly one class:

- `REQUIRED`
- `USEFUL_DISTINCT`
- `REDUNDANT`
- `DISTRACTOR`
- `UNSAFE_OR_MISLEADING`
- `UNRESOLVED`

Use the same meanings as the frozen RC1 evaluator lineage:

- `REQUIRED`: necessary for complete lane evidence objective;
- `USEFUL_DISTINCT`: independently useful, non-required evidence;
- `REDUNDANT`: relevant but materially duplicative;
- `DISTRACTOR`: not useful for the lane objective;
- `UNSAFE_OR_MISLEADING`: superficially attractive but liable to misrepresent scope, status, measurement, attribution, provenance, timing, population, or evidence state;
- `UNRESOLVED`: reliable adjudication is not possible from the frozen fixture.

Also record required-group IDs, redundancy group, concise reason code, one-sentence justification, and confidence.

Gold adjudication must be based on the factual/evidentiary objective of the lane, not on whether a candidate's form matches the Claim Gate profile.

## Cohort-level prereveal eligibility

Require all of the following before `READY_FOR_REVEAL`:

- exactly 36 eligible lanes;
- exactly 6 lanes per category;
- exactly 33 positive lanes;
- exactly 3 no-clear-suitable lanes;
- exactly 30 lanes whose frozen Claim Gate profile contains at least one supported specialty;
- exactly 6 no-specialty control lanes;
- at least 18 specialty lanes whose top-10 pool contains both an intended expected-specialty passage and an intended non-expected-specialty passage;
- all 6 anti-tautology lanes preserve an expected-specialty non-useful candidate and a useful non-expected-form candidate;
- at least 12 lanes contain one or more `UNSAFE_OR_MISLEADING` candidates;
- at least 12 positive lanes contain a useful candidate at original retrieval rank 4–10;
- at least 9 positive lanes have a non-useful candidate at original rank 1;
- at least 6 lanes have two or more distinct useful/required groups;
- zero `UNRESOLVED` candidates in primary-scoring lanes unless excluded in the freeze receipt before reveal.

These gates may not be relaxed after target reveal.
