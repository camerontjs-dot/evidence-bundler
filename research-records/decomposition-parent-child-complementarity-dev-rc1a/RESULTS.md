# Decomposition + Parent/Child Complementarity Dev RC1A — Frozen Result

Status: terminal RC1A decomposition/retrieval result. Downstream CAL-facing probe is recorded separately. This branch remains a research evidence record and is not for merge.

## Exact identities

- Evidence Bundler production `main` at programme start: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- RC1A preregistration: `32434828264ec9613c7f3530ce4ec39f3d5bd1f4`
- exact RC1A apparatus head: `6de9d37140bc16301c151a3ca1b148f13df4c3f5`
- apparatus tree: `3d0c3482986ec89cb94fb3d975eae6d1f6e19820`
- workflow run: `33890894890`
- job: `101081997375`
- artifact ID: `9944022915`
- artifact ZIP SHA256: `5577c756fd7f09e2249caa523e4acb3ba1b900028a5945ea1b99f408c996d86d`
- frozen generation-input SHA256: `fdec774d7d1b7aa7eb330bed352b315fc2724679304a8c69d07347fcc7a90812`
- Contract A fixture manifest SHA256: `670ee91a4045bfd6cfc6f3d84ab0d2b979745d6d6bb55a9b2cbfd3006e2ff20e`
- faithfulness output SHA256: `61f003f7dcc35578ce9c518d9c06d994abd622321c99d7cf28cf9df47a6bae08`
- raw retrieval SHA256, frozen before dev relevance analysis: `58bb4b1a9e93bd6147013a3787b06bb433d09f5aa51a040def520cc420c81707`
- posthoc analysis SHA256: `ac68060d4051bf4997a87fe359351ff28c05dba45aac7fabc214aa7061c7f625`

Canonical authorities/pins:

- Contract A authority: `camerontjs-dot/apparatus-contracts@c3563cff66d2c85dcbf575c693056e2d8e4563d4`
- Contract A validator blob: `42e5f5b3bf38d677445e9d01ea130ba604e53409`
- challenge corpus tree SHA256: `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8`
- historical decomposition file SHA256: `2120228c81466471214ca8b56a6eba2fa5bc498cd0b0243ff3b8fe24c9da2144`
- semantic retrieval: `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- faithfulness NLI: `cross-encoder/nli-deberta-v3-small@fa2804872c3b4bd748f38c0185cc85775361e735`
- FLAN: `google/flan-t5-small@14fd6edcfdd71f2ef5b67d4e735fee8bc6d9fd31`
- Smol: `HuggingFaceTB/SmolLM2-360M-Instruct@a10cc1512eabd3dde888204e902eca88bddb4951`

Run quality gates:

- deterministic suite: 230 passed / 5 skipped
- RC1A boundary tests: 6 passed
- Ruff research apparatus: passed under the preregistered explicit E501 exclusion inherited from the preserved pre-gold RC1 repair
- 42/42 research Contract A fixtures validated under the pinned canonical validator
- same exact root and source representation bytes per case across all seven treatment objects: verified
- split: dev only
- sealed/test data: not used

## OBSERVED — decomposition generation

The root-only successor removed RC1's model-context overflow without changing the frozen model identities.

FLAN:

- 12 generation attempts: D3 + D5a across six cases
- all inputs were below the model context limit
- declared: 0/12
- failed/abstained: 12/12
- all 12 raw generations were `[]`, parsed as `CHILD_COUNT_OUT_OF_RANGE`
- output SHA256: `e5edce47d537537e3e6776e140b5dd251068aa7ed80128a011f19648ce57c2f3`

Smol:

- 12 generation attempts: D4 + D5b across six cases
- all inputs were below the model context limit
- declared: 0/12
- failed: 12/12
- failure surface: 8 `NON_JSON_OUTPUT`, 4 `NON_STRING_CHILD`
- output SHA256: `c9b9ecd4acf8310cb9818e2daa59d21c710117b122d0d713fae289585ab88e82`

Per preregistration, no prompt change, regeneration, parsing relaxation, or manual repair was performed after these outputs were observed.

The 42 Contract A treatment fixtures therefore contain:

- 18 declared treatments: D1, D2 and D6 for six cases
- 24 valid `decomposition.state=failed` treatments: D3, D4, D5a and D5b for six cases

## OBSERVED — separate faithfulness instruments

The instrument emitted 6 warnings among the 18 declared treatments and 24 explicit generation abstentions.

- claim-013 / D6: low child auditability token count
- claim-017 / D1: critical-root-feature warning because lexical condition marker `while` was absent from children
- claim-017 / D2: same `while` warning; the feature extractor also observed added token `Within`
- claim-017 / D6: `while` warning plus low child auditability token count
- claim-037 / D6: low child auditability token count
- claim-049 / D6: low child auditability token count

All declared rows had high bidirectional NLI entailment probabilities; the warning instrument is not treated as semantic authority. In particular the claim-017 `while` warning is retained as an evaluator observation, not silently converted into a conclusion that D1/D2 are semantically invalid.

No retrieval-success conclusion is used to erase a faithfulness warning.

## OBSERVED — semantic retrieval, equal-total budget

K = 12 total requested candidate positions for R0, R1 and R2. R2 therefore divides the same total budget over root + children rather than purchasing additional positions.

### D1 — minimal conjunctive decomposition

Five estimable cases showed identical decisive recall for R1 children-only and R2 root+children. F12 has no decisive evidence annotation in the cohort and is not estimable for decisive recall.

The only case where root-only R0 differed was F10 / claim-037:

- R0 root only: decisive recall `1/2 = 0.5`; qualifier recall `0`; joint-group coverage `0`
- R1 children only: decisive recall `2/2 = 1.0`; qualifier recall `1.0`; joint-group coverage `1.0`
- R2 root + children: decisive recall `2/2 = 1.0`; qualifier recall `1.0`; joint-group coverage `1.0`
- the decisive passage that R2 has and R0 lacks is child-retrieved, not root-only
- R2 has no decisive passage absent from R1

Across the six D1 cases:

- total R2 decisive gains over R1: 0
- average unique candidates: R1 `11.5`; R2 `8.17`
- average duplicate burden: R1 `0.5`; R2 `3.83`
- average source diversity: R1 `8.0`; R2 `5.83`
- R2 root-only physical passages observed: 3 total
- root-only passages that were physically new over R1: 2 total
- decisive passages new over R1: 0

Thus the added root lane did not add decisive information over mandatory D1 child retrieval under equal-total budget, while budget division increased duplicate burden and reduced average candidate/source diversity.

### D2 — scope-preserving decomposition

For every estimable case, R1 and R2 decisive recall were identical. In F10 both remained incomplete:

- R0: `1/2 = 0.5`
- R1: `1/2 = 0.5`
- R2: `1/2 = 0.5`
- qualifier recall remained `0`; joint-group coverage remained `0`

Across the six D2 cases:

- total R2 decisive gains over R1: 0
- average unique candidates: R1 `11.83`; R2 `8.17`
- average duplicate burden: R1 `0.17`; R2 `3.83`
- average source diversity: R1 `8.83`; R2 `6.17`
- R2 root-only physical passages observed: 2 total
- root-only passages physically new over R1: 1 total
- decisive passages new over R1: 0

The parent lane again added no decisive information over mandatory child retrieval.

### D6 — deliberate over-decomposition negative control

F03 / claim-009 is the only equal-total case where R2 improves over R1:

- R0: decisive/exception recall `1.0`
- R1 over-decomposed children only: decisive/exception recall `0.0`
- R2 root + over-decomposed children: decisive/exception recall `1.0`
- the rescued decisive passage `src-cinderwell-current:paragraph:002` is root-only in R2

This is an observation about the deliberate over-decomposition control, not evidence that a parent lane improves valid declared decompositions.

D6 also has the expected negative-control signal: decomposition harms retrieval relative to the exact root in one equal-total case.

## OBSERVED — semantic retrieval, equal-per-query capacity

For D1 and D2 the same K=12 depth was allowed for every active query lane:

- R1 two-child treatments request 24 positions
- R2 root + two children request 36 positions

Across D1 and D2:

- R2 decisive passages new over R1: 0 in every case
- D1 average unique candidates: R1 `23.33`, R2 `24.33`
- D1 average duplicate burden: R1 `0.67`, R2 `11.67`
- D2 average unique candidates: R1 `23.67`, R2 `24.67`
- D2 average duplicate burden: R1 `0.33`, R2 `11.33`

The extra 50% requested positions for the root lane bought roughly one additional unique candidate on average and no additional decisive passage over children-only.

F10/D1 remained the same substantive representation result: children recover the qualifier/joint evidence that root-only misses, and R2 adds nothing decisive beyond R1.

F03/D6 is informative about capacity confounding. Under equal-per-query capacity, the six over-decomposed children alone request 72 positions and recover the decisive evidence without the root lane. The equal-total D6 failure is therefore consistent with severe budget fragmentation/noise from over-decomposition, not a general necessity for parent retrieval.

## OBSERVED — BM25 secondary control

For every declared treatment and both budget regimes, the aggregate analyzer recorded:

- no R2 decisive gain over R0;
- no R2 decisive gain over R1;
- no decomposition-hurts-vs-root case.

The secondary lexical control therefore does not supply an independent reason to add a parent lane.

## OBSERVED — counterevidence, qualifiers, exceptions, hard negatives

This six-case decomposition cohort does not contain an estimable decisive-counterevidence target for the analyzer, so counterevidence recall is reported as `NOT_ESTIMABLE_IN_COHORT`. No counterevidence-production claim is made from Lane B; issue #47 is the relevant counterevidence diagnostic.

Qualifier/exception observations are preserved above:

- F10/D1 children recover the missing qualifier and complete the joint evidence world; root-only does not.
- F03/F06 valid D1/D2 root, child and dual arms all retain the annotated exception evidence.
- F03/D6 over-decomposition loses the exception under equal-total R1 and the root lane rescues it.

The aggregate analyzer recorded zero cases where R2 added new hard negatives over R1 without decisive gain. Candidate duplication and source-diversity changes remain explicit rather than being collapsed into recall.

## OBSERVED — typed R2 versus flattened R3

For every declared treatment, retriever and budget regime:

- R2 and R3 physical passage identities were exactly identical;
- physical-identity invariant failures: 0;
- R3 removed proposition/retrieval-lane relationships by construction.

Relationship removals recorded by the analyzer include:

Semantic equal-total:
- D1: 72 relationships removed across six cases
- D2: 72
- D6: 72

Semantic equal-per-query:
- D1: 216
- D2: 216
- D6: 480

Therefore flattening is proven to destroy proposition/retrieval provenance while holding the physical evidence set fixed. Whether that lost information changes downstream CAL measurements is tested only in the separately preregistered CAL-facing probe.

## INFERENCE

1. **Mandatory authoritative child retrieval is supported.** F10/D1 reproduces a representation effect under equal-total budget: a legitimate minimal conjunctive decomposition recovers decisive qualifier/joint evidence that exact-root retrieval misses.
2. **A default parent lane is not supported by this cohort.** For the legitimate D1 and D2 treatments, R2 never adds a decisive passage over R1 under either equal-total or equal-per-query comparison.
3. **The D6 root rescue is a robustness observation about a deliberately poor decomposition, not production evidence for a parent default.** Increased per-query capacity also repairs that D6 child failure at large search cost.
4. **Production architecture must not rely on Evidence Bundler generating authoritative decomposition.** Both fresh frozen model generators failed to produce usable declarations in RC1A, and the authority boundary already places decomposition ownership upstream.
5. **Retrieval-lane/proposition relationships should not be flattened internally.** R3 destroys real provenance while changing no physical passage identity. Downstream semantic value remains subject to the separate CAL probe.

## UNRESOLVED pending downstream probe

- whether lane-specific evidence partitioning changes CAL semantic measurements relative to the identical flattened physical union;
- whether the representational lineage can be carried through strict Contract B 1.2 without falsely converting retrieval nominations into admitted evidence;
- consequently whether parent retrieval should be absent, research-only, or an explicit optional diagnostic/backstop rather than default.

## NONCLAIMS

RC1A does not establish:

- semantic truth of any proposition;
- a universally optimal decomposition strategy;
- that D1 is always superior to D2;
- that model decomposition is impossible in general;
- that a root lane can never help;
- that the D6 root rescue applies to valid Contract A decompositions;
- counterevidence completeness;
- an evidence-admission policy;
- a root/child aggregation rule;
- a Contract B schema change;
- Contract C projection;
- production release readiness by itself.

## Preserved predecessor failures

The two RC1 pre-gold apparatus failures remain immutable in `research-records/decomposition-parent-child-complementarity-dev-rc1/FAILED_RUNS.md`. RC1A does not rewrite them.
