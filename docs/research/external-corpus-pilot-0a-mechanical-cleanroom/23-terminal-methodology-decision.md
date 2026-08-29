# Evidence Bundler External Corpus Methodology Pilot 0A — Mechanically Isolated Clean-Room Completion

## Terminal disposition

# `FALSIFIED`

The mechanically isolated execution failed its absolute information-access firewall.

The intended source-only FreshStack query reader deserialized complete Parquet rows using `ParquetFile.iter_batches()` without an allow-listed column projection. Pinned FreshStack loader source establishes that those query rows contain the `nuggets` field used to construct qrels/relevant corpus IDs. Therefore published qrel-bearing data entered process memory **before scientific gold freeze**.

The harness never printed, persisted, rendered, or intentionally used the qrel values. That does not cure the failure: the frozen task defines mechanical access/exposure itself as the falsifier and requires the affected clean execution to stop.

All corpus diagnostics produced after the first affected deserialization are retained only as contaminated procedural evidence. In particular, the later observed FreshStack row/revision mismatch and SciFact archive reproduction are **not** clean scientific gate results from this execution.

---

## OBSERVED

- Production `main` at execution start was `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`.
- PR #20 is closed/unmerged; frozen head `357fe735067dbbd3d54f8872ffc8391dac724950`; preregistration `bf6a347704d8711628e044f46c0c3fb9fa4557df`.
- PR #21 is open/unmerged at `764144f3da77140a8e542158948b4e88d40a7421`; contract blob `61ad95dab08c89c34e3416c2a3b9b0f35dabb7f0`.
- PR #22/#23 are closed/unmerged contamination records at `4d91e7a3de78981e4f73489aab179767c58c1914` / `a24542a32acb4f3c04da2dd5bfd8aeaa63123769`.
- PR #17 is closed/unmerged at `27be0c85fdaae9e56a7622e007ca062575e9c433` with live `disposition:superseded`; PR #18 is closed/unmerged at `f0331faa6f97b655de5b22dc419e21f3c0205df3` with live `disposition:falsified`. Result-bearing bodies were not opened.
- Pre-exposure pinned FreshStack source inspection established that `DataLoader` uses the topic/config to load same-topic corpus/query partitions and that its qrel loader consumes the query dataset's `nuggets` field.
- Pre-exposure SciFact source inspection established canonical licensing text: claims/evidence CC BY 4.0; abstracts via S2ORC ODC-By 1.0; code Apache-2.0.
- MainFrame/Conduit failed with HTTP 404 before an independent evaluator-B context could be created.
- Actions run `33253126024` was the first affected acquisition. Its query iterator read all query Parquet columns into process memory before selecting allow-listed identity/text fields.
- Actions run `33253265218` repeated that access pattern before the defect was recognized.
- No qrel value was rendered to the model/user, intentionally used for matching, or persisted in the artifact.
- No scientific gold was created.

### Post-exposure diagnostic observations, not clean evidence

The contaminated harness later reported that exact query revision `00150066ff2959688ad03ce7148ffb652f2fee38` appeared to have observed row counts `318 / 94 / 310 / 230 / 0` for langchain/yolo/laravel/angular/godot, with frozen angular index 248 and godot index 36 not reconstructing. It also reproduced the recorded SciFact archive hash/size. These may be important, but must be independently re-established in a future fresh execution before any scientific use.

## INFERENCE

- The execution's terminal clean-room state is `FALSIFIED` because published FreshStack qrel-bearing fields crossed the mechanical boundary before gold freeze.
- Gate 1 was not validly completed.
- Gate 2 was not completed as a promotion gate; only a pre-exposure source-code proposition survives: a complete same-topic corpus aperture can be deterministically defined without retrieval.
- Gate 3 was not executed as a clean scientific gate; the archive observation occurred after contamination.
- Gate 4 is `INDEPENDENCE NOT ESTABLISHED`; no evaluator B was simulated.
- Gates 5–10 were not scientifically executed.
- This run does **not** establish that the frozen ten-case Pilot 0A object itself is scientifically invalid. It establishes that this completion execution is invalid.

## HYPOTHESIS

- The post-exposure FreshStack row-count mismatch may reveal a second preregistration-integrity defect in the frozen object.
- A future clean run may independently confirm or refute that mismatch.
- The source-access design failed because it enforced forbidden-field filtering only at output/persistence rather than before deserialization.

## UNKNOWN

- Whether the exact frozen FreshStack rows reconstruct under a genuinely qrel-blind reader.
- Whether FreshStack official corpus rows can be deterministically rebound to historical commit-bearing source representations.
- Whether SciFact immutable reconstruction passes in a fresh uncontaminated execution.
- FreshStack upstream-source licensing adequacy.
- Independent evaluator-contract reproduction.
- Passage correspondence, independent gold, published-qrel divergence, segmentation stability, gold invariance, and full corpus-authoring influence.

---

## 1. Clean-room access status

`FAILED — TERMINAL FIREWALL EXPOSURE`.

A pre-execution allow-list/forbidden-surface receipt was frozen before corpus work. General web search was not used for FreshStack provenance, no retrieval candidate/result surface was intentionally opened, and predecessor retrieval-result bodies were avoided. However, the custom acquisition harness itself violated the mechanical firewall by reading qrel-bearing columns into memory.

The named CAL Pipeline governance files could not be located through the available GitHub code-search surface before execution; that remains a recorded deviation.

## 2. FreshStack provenance

`NOT VALIDLY COMPLETED`.

Later row counts, dataset hashes, same-dataset history checks, and source-binding diagnostics occurred after qrel exposure. They are retained only for debugging/procedural learning.

## 3. FreshStack aperture

`NOT COMPLETED AS A PROMOTION GATE`.

A clean pre-exposure source-code observation supports the structural rule that complete same-topic corpus partitions are deterministically derivable without retrieval. This must be re-established as part of a fresh gate sequence after the access harness is assured.

## 4. SciFact reconstruction/licensing

`RECONSTRUCTION NOT EXECUTED AS A CLEAN GATE`.

The archive reproduction happened after contamination. The authoritative licence text was inspected pre-exposure and remains a source-only observation, but the full Gate 3 reconstruction must be rerun in a fresh context.

## 5. Evaluator independent cross-check

`INDEPENDENCE NOT ESTABLISHED`.

No separate evaluator B was created or frozen. PR #21's same-context B implementation was not reused as independent evidence.

## 6. Evaluator-contract defects

`UNKNOWN`.

No genuine independent implementation/cross-check occurred.

## 7. Independent adjudication

`NOT_EXECUTED`.

No adjudicator A/B scientific record exists.

## 8. Disagreement structure

`NOT_EXECUTED`.

## 9. Published-qrel comparison

`NOT_EXECUTED`.

Important distinction: no deliberate Gate 8 comparison occurred and no qrel value was rendered, but qrel-bearing FreshStack query fields were accessed prematurely by the acquisition process. Therefore `published FreshStack qrel exposed before gold freeze = true` at the mechanical-access level.

## 10. Segmentation stability

`NOT_EXECUTED`.

## 11. Gold invariance

`NOT_EXECUTED`.

## 12. Project-control analysis

`NOT_EXECUTED AS A SCIENTIFIC AUDIT`.

Only the pre-exposure source-code observation about topic-level aperture is retained. No relevance/role/grouping conclusion is admissible.

## 13. Contamination/exposure

Terminal exposure state:

- production BM25 exposed: `false`
- Hybrid exposed: `false`
- Semantic-only exposed: `false`
- dense exposed: `false`
- lexical exposed: `false`
- FreshStack candidate-list exposed: `false`
- FreshStack published retrieval-result exposed: `false`
- historical predecessor retrieval-result exposed: `false`
- published FreshStack qrel exposed before gold freeze: `true` at acquisition-process level
- published SciFact evidence exposed before gold freeze: `false`
- scientific gold creation state: `NOT_STARTED`

First affected run: `33253126024`, head `2b1cbb7e00a67138384e15ce547b9be87630380a`.

## 14. Falsified alternatives

The acquisition-leak alternative is **supported**, not rejected. Output redaction did not provide information isolation because forbidden query columns had already been deserialized.

Other scientific alternatives requiring source reconstruction, adjudication, or gold remain unresolved in this execution.

## 15. Strongest remaining alternative

There is no contract-consistent interpretation under which this run is clean. A narrower definition of exposure limited to rendered values would change the answer, but the frozen task explicitly requires mechanical source-access separation and makes information-acquisition leakage terminal.

The observed query-revision mismatch is a possible second defect, not an alternative to the exposure falsifier, and must be retested cleanly.

## 16. Terminal disposition

# `FALSIFIED`

**Falsifier:** prohibited pre-gold FreshStack qrel-bearing field access by the source-acquisition machinery.

The frozen Pilot 0A scientific object remains **unresolved**, not rescued and not scientifically invalidated by this run. It may be reused only unchanged in a genuinely fresh future execution after the source-access machinery has passed isolation assurance.

No BM25, Hybrid, Semantic-only, dense, lexical, reranker, substitute retriever, or 24–30-case apparatus is authorized.

## 17. Smallest next authorized task

Run a **source-access isolation assurance** task before another Pilot 0A completion attempt:

1. replace full-row Parquet deserialization with explicit allow-listed column projection before any row data enters memory;
2. for FreshStack query files, permit only frozen identity/text fields needed to reconstruct the sample; never deserialize `nuggets`, qrel IDs, accepted answers, evidence labels, candidate lists, or result fields;
3. add fail-closed tests proving forbidden columns cannot be accessed even when present in the same physical Parquet file;
4. emit an access receipt proving which physical columns were read;
5. only after that harness is frozen and assured, start a new fresh-context Pilot 0A completion from Gate 1.

Do not use this contaminated context to diagnose the row-revision mismatch further. Do not repair the frozen ten cases. Do not construct the 24–30-case apparatus. Do not run any retriever.

---

## Isolation and acquisition receipts

- branch: `research-infra/external-corpus-pilot0a-mechanical-cleanroom-20260829`
- run 1: `33253126024`, head `2b1cbb7e00a67138384e15ce547b9be87630380a`, artifact digest `sha256:f99d9cd54fdd47844d8b357a00c790233f8c6bd9254174c72db73e30b94fc51c` — contaminated
- run 2: `33253265218`, head `ede95664a581e7958307143a800b416e0bb544e2`, artifact digest `sha256:e50d7a74872de095726a194b2757097e0c6414f29b636d723fb6f6a7b29090a9` — contaminated
- evaluator isolation: MainFrame/Conduit HTTP 404 before session creation

## Deviations

1. Required named CAL Pipeline governance records were not discoverable through the available GitHub code-search surface.
2. An early overbroad PR-search call rendered procedural PR bodies but no prohibited retrieval/qrel value.
3. The acquisition harness filtered forbidden fields at output rather than preventing them from entering memory. This is the terminal defect.
4. A second acquisition run and later diagnostics occurred before that defect was recognized; those records are explicitly marked contaminated.

## What was not established

This run does not establish FreshStack exact provenance, SciFact clean immutable reconstruction, external-corpus passage stability, independent gold stability, evaluator independent reproduction, source-byte binding, published-qrel agreement/divergence, segmentation stability, corpus-authoring influence, any retrieval performance property, a final benchmark, the 24–30-case apparatus, or production promotion.
