# EB Typed Selector RC1 — Fresh Cohort Contract

## Cohort size

Author exactly **30 fresh lanes**.

Use exactly 3 lanes from each category below:

1. high lexical overlap with non-useful competing passages;
2. long/noisy passages where useful content occupies a small local span;
3. redundant or near-duplicate evidence;
4. competing numeric, measurement, or evidence-form context;
5. temporal, population, jurisdiction, or scope mismatch;
6. provenance/source-role variation;
7. qualifier, negation, modality, or attribution traps;
8. complementary multi-passage coverage where more than one distinct item matters;
9. ordinary straightforward evidence;
10. no-clear-suitable-candidate / unresolved evidence-world cases.

The categories are broad test families, not expected target features.

## Freshness

All concrete claims, entities, values, source text, passage wording, and evidence arrangements must be authored from scratch in the context-free lane.

Do not reuse or mutate prior selector-development fixtures.

## Lane authoring order

For each lane, use this order:

1. author the claim;
2. freeze the claim text;
3. author the claim profile from the claim alone;
4. freeze the profile;
5. author the source corpus;
6. assign opaque source/passage IDs that contain no gold meaning;
7. run the frozen first-stage retrieval at depth 10;
8. freeze the resulting candidate pool before gold adjudication;
9. adjudicate candidate gold from the source/candidate content;
10. freeze gold.

Do not edit a claim/profile/corpus after seeing any hidden target output.

## Profile schema

The prereveal profile is an experiment input, not a target explanation.

Use only:

```json
{
  "requires_direct_evidence": true,
  "concepts": [
    {
      "name": "opaque descriptive name",
      "terms": ["claim-derived term or close synonym"],
      "weight": 1.0
    }
  ],
  "evidence_forms": [],
  "source_roles": []
}
```

Rules:

- derive profile content from the claim only, before retrieval candidates are inspected;
- use 1-4 concepts per lane;
- use only terms needed to express the claim's entities, relationship, quantity/measure, event, comparison, or explicit contextual constraint;
- synonyms may be added when they are ordinary lexical equivalents evident from the claim, not from candidate text;
- concept weights must default to `1.0` unless the claim itself clearly contains a primary versus subordinate structure; any non-default weight must be justified before corpus authoring;
- `requires_direct_evidence` should be `true` for a factual proposition that purports to be established by evidence and `false` only when the claim itself is explicitly about discussion, uncertainty, possibility, or another non-direct-evidence state;
- leave `evidence_forms` and `source_roles` empty in RC1 unless a separate pre-retrieval rule can populate them from the claim/fixture schema without reading candidate content;
- profile generation may not depend on selector behavior or gold labels.

## Corpus construction

Each lane should contain enough source material to make depth-10 selection meaningful. Target 12-20 candidate-bearing passages/chunks before retrieval.

Avoid trivial gold cues:

- no labels such as `correct`, `gold`, `required`, `distractor`, `unsafe`, `support`, or `refute` in passage IDs or formatting;
- no unique formatting reserved for useful passages;
- do not make useful passages systematically much shorter/longer than all competitors unless passage length is itself the intended lane difficulty;
- no answer keys inside source metadata visible to the target.

## Frozen first-stage retrieval

Use the exact Evidence Bundler first-stage behavior from integration candidate commit:

`4e1f6fe00e7c350b28f52bfea14f1f8988847884`

Candidate depth must be exactly 10.

Do not change:

- tokenizer;
- BM25 implementation/parameters;
- chunking profile;
- query text generation;
- source aperture behavior;
- candidate depth;
- candidate ranking.

The retained-3 behavior of the integration candidate is not part of cohort authoring. Preserve the **full top-10 nomination pool** for later selector comparison.

## Lane eligibility

A positive lane is eligible when:

- the frozen first-stage run deterministically returns 10 unique candidate identities;
- at least one candidate later adjudicated `REQUIRED` or `USEFUL_DISTINCT` appears in the top 10;
- the pool contains at least one non-useful competitor;
- no target-selector information was used to construct or repair the lane.

A category-10 no-clear-suitable lane is eligible when:

- the frozen first-stage run returns 10 unique candidates;
- none is adjudicated `REQUIRED` or `USEFUL_DISTINCT`;
- the lane still presents a meaningful selection-burden test.

If a drafted lane fails eligibility, preserve it in the replacement/deviation log and author a new lane from scratch under the same category. Do not repair the failed lane by editing passages after retrieval exposure.

## Gold schema

Adjudicate every top-10 candidate into exactly one primary class:

- `REQUIRED` — necessary to satisfy the lane's evidence objective; missing it makes the selected set materially incomplete;
- `USEFUL_DISTINCT` — independently useful, non-required evidence that adds a distinct relevant fact/facet;
- `REDUNDANT` — relevant but materially duplicative of a stronger/equivalent candidate already represented in the pool;
- `DISTRACTOR` — not useful for the lane's evidence objective;
- `UNSAFE_OR_MISLEADING` — superficially attractive but liable to misrepresent scope, measurement, attribution, temporal context, population, or evidence status if selected as evidence;
- `UNRESOLVED` — adjudication cannot be made reliably from the frozen fixture.

Also record:

- `required_group_ids` for complementary coverage lanes where multiple distinct required facets exist;
- `redundancy_group_id` where applicable;
- concise reason code and one-sentence justification;
- reviewer confidence: `high`, `medium`, or `low`.

Gold may describe usefulness for selection. It must not contain CAL truth/entailment verdicts unless the claim itself requires such a distinction for fixture interpretation.

## Cohort-level eligibility

Before reveal, require:

- exactly 30 eligible lanes;
- exactly 3 per category;
- at least 27 lanes with one or more `REQUIRED`/`USEFUL_DISTINCT` candidates;
- exactly 3 category-10 no-clear-suitable lanes;
- at least 6 lanes with one or more `UNSAFE_OR_MISLEADING` candidates;
- at least 6 lanes where the highest-ranked candidate is not `REQUIRED`/`USEFUL_DISTINCT`;
- at least 6 lanes where a useful candidate occurs below rank 3;
- at least 3 complementary-coverage lanes with two or more required groups;
- zero `UNRESOLVED` candidates in lanes used for the primary metric unless the prereveal freeze receipt explicitly marks that lane as excluded from primary scoring before target reveal.

These gates are checked before target reveal and may not be changed afterward.
