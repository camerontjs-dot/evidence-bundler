# EB Retrieval + Aperture Assurance RC1 — Decisive Run Freeze

**PR:** #6  
**Task class:** Research experiment  
**Status:** frozen execution mapping before first real EB sealed-test output

## Decision

Determine whether the bounded Evidence Bundler retrieval/aperture claim preregistered in
`brief-05-eb-retrieval-aperture-assurance-rc1.md` survives the frozen
`eb-challenge-corpus-v1` sealed test under the already-assured frozen evaluator.

This record does not authorize production changes.

## Immutable identities

- SUT production commit: `c8189c31adbab11729c31430c2070126224a2d42`
- Frozen benchmark commit: `22b227ec2c34a085efc79267bc007ff78607aeed`
- Frozen benchmark tree SHA-256: `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8`
- Frozen validation report SHA-256: `1c3db5529f14b18035c11aae0d3454c28914bcd822b41ec3bc6b85fd1deeec2a`
- Frozen evaluator commit: `acfa232c0a6d1708f249b71606cbdc96755bc4d9`
- Evaluator composite source SHA-256: `48ccebbd81f43ddd951e83c2a2c4b9c1fae7a6a24ec7c3bf3fdea47b1b936f14`
- Result schema SHA-256: `2cfb4dc6cd746f55b690300aafe9a0d19678fcb09bd8e01b0dd5d15043fbf40b`
- Threshold config SHA-256: `066e99719168a366f03476fa779398f790cce7653bc3928470486d6bbb805461`

No live correspondence observed before this freeze superseded the c818 production SUT pin.

## Exact bounded SUT configuration

The c818 production README names BM25 as the default retrieval baseline. The decisive run
therefore exercises the real c818 `BM25Retriever` implementation with:

- retrieval method: `bm25`;
- query text: frozen case `claim_text` verbatim;
- score floor: `0.0`;
- retrieval budget: each case's frozen `runtime_config.maximum_passages`;
- searchable sources: only the case's frozen named aperture subset;
- semantic retrieval: off;
- reranking: off;
- contradiction query expansion: off.

### Passage-unit adapter

The frozen benchmark runtime metadata provides exact permitted passage boundaries and IDs.
The frozen evaluator grants retrieval credit only for exact frozen passage identity or exact
anchor identity.

The c818 general-purpose production chunker can coalesce multiple benchmark paragraphs into
larger chunks. Awarding evaluator credit merely because a larger production chunk overlaps a
gold paragraph would change the frozen evaluator's exact-provenance semantics.

For this retrieval experiment, the research adapter therefore constructs exactly one flat
production `DocumentChunk` per permitted frozen benchmark passage and passes those chunks to
the unmodified c818 `BM25Retriever`. Returned hits are serialized with the exact passage ID
and anchor from the permitted source metadata.

This freezes the SUT claim at the **passage-nomination retrieval boundary**. It does **not**
establish c818 extraction/chunking quality or end-to-end `build-bundle` behavior. A separate
pre-sealed diagnostic records how the c818 general chunker aligns with the frozen passage
units so extraction is not silently blamed on retrieval.

## Runtime contamination boundary

The SUT process receives only a clean runtime mount containing:

- `sources/`;
- the frozen `cases/`;
- `aperture/subsets.json`.

It does not receive:

- `gold/`;
- `decompositions/`;
- challenge-family labels;
- expected rankings;
- evaluator source;
- evaluator rationales;
- expected outcomes.

The evaluator runs only after raw SUT results have been serialized.

## Aperture serialization rule

The generic evaluator result needs explicit search-scope and completeness fields.

- `search_scope` is a research-harness observation of the exact named subset mechanically
  mounted for the SUT.
- `completeness_claim.status` is always `not_established`.
- The adapter does not infer `full_corpus` or `comprehensive` from source count.
- This mapping must not be described as evidence that c818 natively emits an aperture receipt.

## Development and sealed-test rule

- Development cases are run first only to exercise plumbing/schema/provenance.
- No retrieval setting, query construction, evaluator byte, threshold, or benchmark byte may
  change based on development or sealed output.
- The research disposition is based on the 111 frozen sealed-test cases.
- The frozen evaluator source and threshold functions are invoked unchanged. A thin wrapper
  filters the already-frozen cases to `split == "test"` before using the evaluator's exact
  `evaluate_case`, aggregation, and qualification functions because the corpus preregistration
  assigns decisive authority to the sealed split.

## Preserved falsifiers

The decisive workflow also records:

- exact-byte deterministic replay;
- source-enumeration reversal invariance;
- hard-negative behavior;
- no-answer behavior;
- per-family metrics;
- per-aperture metrics;
- pooled exact passage recall and source recall as auxiliary, non-threshold metrics;
- comparison against frozen weak controls C2 and C3 on the same sealed split.

No auxiliary metric changes the frozen gates.

## First-run rule

The first sealed-test raw result and evaluator output are evidence even if they fail.

No fix-until-green loop is allowed. Any apparatus correction after sealed output requires an
explicit deviation record and must state whether the first decisive run remains valid.

## Non-claims

This experiment does not establish:

- production chunker/extraction quality;
- semantic support or contradiction judgment;
- CAL behavior;
- Contract A decomposition correctness;
- corpus legitimacy or real-world completeness;
- production promotion authorization.
