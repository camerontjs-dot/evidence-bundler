# Brief 13 — Evidence Bundler Retrieval Assurance RC2: Independent Discriminating Sealed Challenge

**PR class:** Research Infrastructure / evaluator-benchmark assurance  
**Production impact:** none  
**Real EB exposure:** forbidden in this PR  
**Primary decision:** whether an independently generated frozen RC2 challenge/evaluator apparatus is sufficiently discriminating to authorize a later, separate real-EB execution.

## Predecessor evidence accepted as terminal

RC2 does not rerun or repair RC1.

Live predecessor expected and independently rechecked before this brief:

- merged evaluator Research Infrastructure PR #9;
- closed Research PR #6 with disposition `INCONCLUSIVE`;
- RC1 production SUT `c8189c31adbab11729c31430c2070126224a2d42`;
- v1 benchmark `22b227ec2c34a085efc79267bc007ff78607aeed`;
- RC1 evaluator `acfa232c0a6d1708f249b71606cbdc96755bc4d9`.

RC1's stopping reason is accepted: the real c818 BM25 run and the intentionally weak lexical C3 control both cleared every promotion-critical sealed gate. RC1 therefore did not discriminate the broader retrieval capability. End-to-end production chunking and native EB aperture/completeness receipts also remained outside the established surface.

Current `main` may contain later Research Infrastructure, but RC2 must not silently replace the historical RC1 SUT or alter RC1 records.

## Capability definition frozen before sealed generation/control

RC2 is implementation-independent at the property level. The sealed challenge is intended to distinguish retrieval systems that can preserve the following properties from plausible cheap shortcuts:

1. materially relevant retrieval when decisive language has low direct lexical overlap with the query;
2. counterevidence retrieval when superficially similar supporting/training/draft distractors are easier lexical matches;
3. qualifier retrieval where support plus qualifier are jointly required;
4. exception retrieval where support plus exception are jointly required;
5. complete multi-passage and multi-source joint groups;
6. distractor-heavy apertures under bounded K;
7. exact provenance when near-identical source twins exist;
8. honest bounded-search/aperture claims;
9. hard-negative behavior;
10. explicit no-answer/full-aperture cases where retrieval nominations must not be treated as semantic answerability.

Contract-A decomposition is not an input or controlled variable in RC2.

## Challenge families

- `R01 LOW_OVERLAP_RELEVANCE`
- `R02 COUNTEREVIDENCE_LEXICAL_TRAP`
- `R03 QUALIFIER_JOINT_PAIR`
- `R04 EXCEPTION_JOINT_PAIR`
- `R05 MULTI_SOURCE_COMPOSITION`
- `R06 DISTRACTOR_HEAVY_BOUNDED_K`
- `R07 APERTURE_BOUNDARY_HONESTY`
- `R08 PROVENANCE_TWIN`
- `R09 NO_ANSWER_HARD_NEGATIVES`

Generation is deterministic from seed `161803`. The generator is self-contained, does not import Evidence Bundler, does not inspect EB output, and writes runtime and evaluator-only state to different roots.

The development split contains 2 cases per family. The sealed split, not generated or controlled during development calibration, contains 8 cases per family.

## Frozen metric thresholds

RC2 retains the RC1 promotion-critical retrieval thresholds rather than choosing easier or harder numbers after seeing sealed controls:

- case hit@K `>= 0.95`;
- decisive annotation recall@K `>= 0.90`;
- counterevidence recall@K `>= 0.90`;
- qualifier/exception recall@K `>= 0.90`;
- complete joint-group coverage@K `>= 0.90`;
- family case hit@K `>= 0.75` where applicable;
- family decisive annotation recall@K `>= 0.70` where applicable;
- budget violations `= 0`;
- invalid provenance hits `= 0`;
- out-of-scope hits `= 0`;
- false completeness claims `= 0`;
- semantic answerability overclaims `= 0`.

First-decisive MRR and hard-negative counts are diagnostic, not independent promotion gates.

## Preregistered controls

Positive ceiling:

- `oracle`: exact accessible decisive identities, bounded by case K, with `not_established` completeness and answerability.

Cheap/weak retrieval shortcuts:

- `first_n`: deterministic source/passage order only;
- `token_overlap`: exact query-token overlap;
- `tfidf_cosine`: bag-of-words TF-IDF cosine;
- `char_trigram`: character-trigram Jaccard.

Adversarial/negative controls:

- `null`;
- `return_all`;
- `provenance_corrupt`;
- `aperture_liar`;
- `answerability_liar`;
- `hard_negative_biased`.

The lexical controls are independently implemented and do not reproduce the RC1 C3 code.

## Pre-exposure sealed control gate

A later real-EB run is authorized only if the **first hosted sealed control run** satisfies all of the following without redesigning the same challenge after seeing its outcome:

1. oracle qualifies;
2. null fails;
3. return-all fails with budget violations;
4. provenance-corrupt fails with invalid provenance credit;
5. aperture-liar fails with false-completeness findings;
6. answerability-liar fails because retrieval-only output cannot claim semantic answerability;
7. at least **two of the three preregistered lexical strategies** (`token_overlap`, `tfidf_cosine`, `char_trigram`) fail qualification;
8. their combined failure signatures cover at least **two distinct promotion-critical categories** among coverage, counterevidence, qualifier/exception, and joint-group coverage;
9. deterministic control replay is byte-identical;
10. source/passage enumeration permutation is evaluator-invariant for the positive ceiling;
11. provenance, aperture-completeness, and joint-group mutations produce the expected evaluator sensitivity.

`first_n` and `hard_negative_biased` are additional cheap-shortcut diagnostics; they are not needed to satisfy the lexical-count gate.

If this first hosted sealed gate fails, RC2 stops `INCONCLUSIVE`. Do not make the challenge harder and run the same version again until controls pass.

## Development-only calibration completed before freeze

Development calibration was permitted to catch apparatus defects without consuming sealed evidence. On the 18 development cases:

- generator/validator integrity checks passed;
- oracle qualified;
- null, return-all, provenance-corrupt, aperture-liar and answerability-liar failed for the intended reasons;
- all three lexical strategies failed qualification;
- their failure signatures covered coverage, counterevidence, qualifier/exception and joint-group behavior;
- deterministic replay, source-order invariance and the preregistered mutation probes passed.

These development observations are apparatus plumbing evidence only. They do not authorize EB and do not substitute for the first sealed control gate.

## Physical isolation requirement

The frozen benchmark package separates:

- `runtime/`: passages, cases and aperture subsets suitable for a later SUT mount;
- `evaluator_only/`: relevance classes, decisive identities and joint-group state.

A future real-EB execution may receive only the frozen runtime root. It must not receive evaluator-only gold, control outputs, expected rankings, or evaluator internals.

## No-answer boundary

`R09` contains full-aperture cases with no decisive gold. Returning retrieval nominees is not itself an error. The evaluator instead fails explicit `answer_present` or `no_answer` claims because a retrieval-only result has not performed the semantic assessment needed to establish either state.

## Freeze and stopping rule

If the first hosted sealed control gate passes:

1. freeze the exact generated benchmark bytes under a new versioned benchmark directory;
2. freeze generator, evaluator, schema and threshold bytes at the pre-control apparatus identity;
3. record exact hashes and commit identities;
4. rerun only deterministic reproduction/byte-comparison against the frozen package, not a redesigned sealed challenge;
5. record known limitations and the handoff for a separate real-EB thread;
6. stop before any real EB output is produced.

Allowed final dispositions are exactly:

- `SUPPORTED FOR PROMOTION`
- `FALSIFIED`
- `INCONCLUSIVE`
- `SUPERSEDED`

For RC2, `SUPPORTED FOR PROMOTION` means only that this exact frozen benchmark/evaluator apparatus is sufficiently discriminating to authorize a later separate real-EB execution.
