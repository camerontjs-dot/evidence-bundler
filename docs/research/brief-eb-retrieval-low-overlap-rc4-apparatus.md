# Evidence Bundler Retrieval Generalization RC4 — Apparatus Preregistration

## PR class
Research Infrastructure / Draft / preregistration and design only.

This PR does not yet contain an assured sealed benchmark and does not authorize target exposure.

## Bounded decision
Construct and later assure a new `eb-retrieval-low-overlap-rc4-v1` apparatus that can discriminate meaning-preserving semantic retrieval from lexical retrieval, construction/style-cue gaming, source/structural gaming, and counterevidence regression before any Hybrid or Semantic-only sealed target execution.

## Preserved predecessor failure
RC3 PR #16 is terminal `FALSIFIED` and must not be repaired in place.

Observed RC3 failure to preserve:
- a runtime-only construction-cue gamer cleared the intended absolute target gate at approximately 0.9792 combined low-overlap hit/recall/MRR with zero technical violations;
- exact c818 BM25 fresh C01 counterevidence recall was only 0.3125;
- `hybrid_sealed_exposed = false`;
- `semantic_sealed_exposed = false`.

## Production pins
- exact production SUT source: `c8189c31adbab11729c31430c2070126224a2d42`
- exact production BM25 implementation blob carried from verified RC3 config: `f8d7dd7e56710453edbca7c51aeea6da949ff903`
- target preregistration: PR #17
- target config SHA256: `65c671e25dfd998350cfdb6d2a84c4a46d4db7e867827dd99fd4e57a8003f60e`

## Fresh deterministic design
Benchmark name: `eb-retrieval-low-overlap-rc4-v1`.

Generator seed: `173205`.

The initial design draft used `271828`, but live lineage inspection showed that seed was already used by frozen benchmark PR #8. Before generator implementation, before any scientific object existed, and before any sealed execution, the seed was corrected to the new repository-unused value `173205`. The correction is preserved in deviation record `deviation-18a-preimplementation-seed-collision.md`.

Minimum balanced design: 80 sealed cases, 16 each for L01, L02, L03, L04, and C01. Each family consists of 8 fresh semantic scenarios with two paired surface variants. The pair structure is part of the apparatus, not duplicate case inflation.

No RC2/RC3 case text, passage text, exposed fictional entity stems, decisive/hard-negative bytes, or candidate output may be reused.

## Independent cue variation
The generator must cross semantic role and construction cues rather than merely diversify prose.

Eight construction families are preregistered:
1. policy-like prose;
2. procedural prose;
3. technical explanatory prose;
4. incident-like prose;
5. FAQ/dialogue-like prose;
6. terse catalog/register-like prose;
7. multi-sentence narrative prose;
8. conditional/declarative summary prose.

Within every capability family, deterministic balanced assignment must ensure these construction families occur across decisive passages, hard negatives, ordinary distractors, and counterevidence. Genre itself may not predict gold role.

The paired variants must independently balance or permute:
- source and passage position;
- passage-length bin;
- sentence position of decisive meaning;
- punctuation/format family;
- identifier pattern;
- metadata density/style;
- concise versus verbose realization;
- construction family.

For L04 specifically, nonsemantic cue profiles are swapped between decisive and hard-negative passages while semantic roles remain fixed.

## Capability families
### L01 — terminology / ontology substitution
Meaning-equivalent but lexically distinct terminology.

### L02 — compositional paraphrase
Relevant meaning distributed or structurally expressed differently from the query.

### L03 — lexical-decoy conflict
A wrong passage is deliberately more lexically attractive than the decisive passage.

### L04 — cue-swap semantic control
Promotion-critical family. Decisive and hard-negative passages exchange nonsemantic construction/style/structural cues while semantic roles remain unchanged.

### C01 — counterevidence retention
Fresh cases designed independently of RC2 text so exact BM25 can demonstrate whether a strong fresh counterevidence capability actually exists on this apparatus.

## Freeze order
Before any exact BM25, weak/gaming control, Hybrid, or Semantic-only sealed execution, freeze and hash at minimum:
- generator source;
- generator config and seed;
- validator;
- runtime corpus;
- runtime cases;
- source/passages scope;
- evaluator-only gold;
- family membership;
- evaluator source;
- threshold config;
- result schema;
- control runner;
- anti-gaming runner;
- metamorphic definitions;
- target preregistration identity;
- benchmark tree.

The first sealed control output must be preserved separately and hashed. No scientific byte or gate may change after first sealed control exposure.

## Exact BM25 prerequisite
Before Hybrid/Semantic exposure, exact BM25 must satisfy all strong fresh C01 requirements and simultaneously remain materially weak on L01-L04 according to the frozen threshold record.

If C01 strength is not established, stop. Do not weaken the threshold.

## Anti-gaming requirement
The frozen control suite must include null, first-N/source-order, return-all, token overlap, bag-of-words TF-IDF, character n-gram, hard-negative-biased lexical, passage-length, source-position, metadata/identifier-pattern, runtime-only construction/style-cue gamer, cue-swap gamer, provenance-corrupt, completeness/aperture liar where supported, and semantic-answerability liar where supported.

The construction/style gamer and cue-swap gamer may inspect only retriever-runtime-visible information. They may not read evaluator gold, family labels, decisive IDs, hard-negative IDs, or hidden annotations.

A gaming control must fail on an intended semantic/anti-cue gate. Incidental parser/provenance/shape failure does not count as semantic discrimination.

## Evaluator assurance requirements
Before target exposure require:
- oracle positive ceiling;
- decisive-ID mutation sensitivity;
- hard-negative-ID mutation sensitivity;
- family-label/aggregation mutation sensitivity;
- broken provenance failure;
- result coverage mismatch failure;
- K/budget enforcement;
- deterministic replay;
- source-order invariance where applicable;
- preregistered metamorphic expected-direction checks;
- construction-gamer discrimination;
- exact result/hash reproducibility.

## Program-level stop
RC4 is the final attempt in this exact synthetic sealed-challenge construction program. If the apparatus cannot simultaneously achieve oracle ceiling, strong fresh BM25 C01, material BM25 low-overlap weakness, failure of lexical and runtime-only construction gamers, and stable evaluator mutation/metamorphic behavior, stop the synthetic strategy. Do not immediately build RC5.

The next method should consider externally sourced heterogeneous corpora, independently authored cases, transformed real documents, independent benchmark construction, cross-repository or third-party retrieval benchmarks, or another costly-to-fake design.

## Current contamination / exposure state
This PR is design-only at creation.

- `scientific_object_frozen = false`
- `sealed_controls_executed = false`
- `bm25_sealed_exposed = false`
- `hybrid_sealed_exposed = false`
- `semantic_sealed_exposed = false`

## Next task
A dedicated apparatus-assurance task may implement the generator/validator/evaluator/control machinery from this preregistration, freeze the scientific object, and execute assurance in the required order. It must not run Hybrid or Semantic-only unless and until it reaches an explicit authorized handoff decision.