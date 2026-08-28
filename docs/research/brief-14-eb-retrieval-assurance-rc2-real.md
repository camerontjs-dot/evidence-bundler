# Brief 14 — Evidence Bundler Retrieval Assurance RC2: Real Production Measurement

**PR class:** Research / Draft  
**Production impact:** none  
**Decision:** measure the locked production Evidence Bundler BM25 retriever against the exact frozen RC2 apparatus authorized by EB #13.

## Claim under review

For the frozen RC2 runtime representation and bounded named aperture, production Evidence Bundler BM25 retrieval can recover the decisive evidence, counterevidence, qualifiers/exceptions, and required joint evidence groups strongly enough to clear the preregistered RC2 retrieval gates without invalid provenance, budget violations, or unsupported completeness/answerability claims.

A passing result may support only **presegmented passage retrieval under the frozen RC2 runtime representation**. It does not establish production chunking/extraction, native Evidence Bundler aperture/completeness receipts, semantic relevance/entailment, Contract-A decomposition, or production promotion.

## Frozen production SUT

The intended system under test is the locked production retriever used by the predecessor RC1 experiment:

- repository: `camerontjs-dot/evidence-bundler`
- SUT SHA: `c8189c31adbab11729c31430c2070126224a2d42`
- retriever: production `BM25Retriever`
- query: frozen `case.claim_text`, verbatim
- index unit: one frozen RC2 runtime passage adapted to one production `DocumentChunk`
- source aperture: exactly the frozen case `accessible_subset_id`
- `top_k`: frozen `runtime_config.maximum_passages`
- `score_floor`: `0.0`

Current `main` is not substituted as the SUT. Later commits are Research Infrastructure / governance / benchmark durability and are not silently folded into the measured implementation.

## Exact frozen apparatus

Durable storage commit after EB #13 merge:

- `2643385c998dd3b08af84eb37f3f089fea7d5e73`

First decision-relevant apparatus commit and sealed control:

- apparatus commit: `82ec006e888e22c5e5cde600546c05cc6e0b5e33`
- first sealed control run: `33183653897`
- first sealed control SHA256: `d3cdc3ac7c356cc4ec0edc06b6d149bc80082e861b078e8ef94a2df9ad8dfb74`
- apparatus composite SHA256: `9d3599e34c5ff6eda05e91370c77010ca2f28c9294a69f76972098ad0838673d`

Frozen components:

- benchmark tree SHA256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`
- runtime passages SHA256: `352ce375a9b2e987f5a7fc686c4560d018646e56a13743027b0b06602cf66dbd`
- runtime apertures SHA256: `9f11111aee7bc9b0b0c798184b09efb0d2502c8463d63fef3ed2d08d598ad236`
- runtime sealed cases SHA256: `b5f15e7ec52e34846d26e15f530daf242264862ccf56950f5151735c55ce8120`
- evaluator-only sealed gold SHA256: `4c114dd2f00e70f26581f0287058ce68ad40ef5b8d28fcaae582a6b4e719915c`
- evaluator SHA256: `c443a64a2c2dfe8c9b0decd8c0414c1e7bb1069d86d3355dd0202fa9725aff08`
- thresholds SHA256: `9df75b448ff5090d9bd2821f624e327d47ba5ea9848460cf69518bb6b04ea05a`
- result schema SHA256: `26a56b08c90277f6d13434d5bb5db4a0f71edc925ff78db6de285b6a4b992dd0`

These objects and their success/failure definitions are frozen. They may not be changed after real-output exposure in this experiment.

## Adapter boundary

The adapter is research-only transport. It may:

- instantiate the exact production `BM25Retriever` from the SUT SHA;
- represent each already-frozen runtime passage as one flat production `DocumentChunk`;
- mount only the source IDs in the case's frozen aperture;
- normalize returned production hits into the already-frozen RC2 result schema;
- record the mechanically mounted aperture as a research-harness search-scope observation;
- emit `not_established` for completeness and semantic answerability.

The adapter may not:

- alter query text;
- add semantic labels or gold information;
- inspect evaluator-only state during retrieval;
- rerank, tune, repair, or supplement production BM25 results;
- claim production chunking behavior from frozen passage adaptation;
- convert the mounted aperture into a native EB completeness receipt;
- convert retrieval nomination into semantic answerability.

## Exposure and stopping rule

The **sealed exposure point** is the first invocation of the production SUT adapter on `runtime/sealed_cases.jsonl`.

Before that point, the workflow must verify the exact SUT and frozen apparatus identities and reproduce the recorded first sealed-control hash. A development-split adapter smoke may be used only for transport/shape correctness; no retrieval tuning or apparatus change is allowed from its outcome.

After sealed exposure:

1. preserve the first legitimate raw SUT output unchanged;
2. evaluate it once with the exact frozen evaluator/thresholds;
3. rerun the exact same SUT/config only for deterministic replay;
4. run the preregistered source-order control without changing the evaluator or gate;
5. preserve technical deviations instead of repairing the apparatus and pretending the rerun was the first decisive experiment;
6. stop after those frozen controls and epistemic compression.

A SUT qualification failure is a scientific result, not a workflow failure. Workflow failure is reserved for technical inability to produce/verify the measurement.

## Decision rule

Use the exact frozen RC2 evaluator qualification result. Do not add or remove gates after exposure.

The terminal research disposition must be exactly one of:

- `SUPPORTED FOR PROMOTION`
- `FALSIFIED`
- `INCONCLUSIVE`
- `SUPERSEDED`

If the real SUT qualifies and the frozen controls complete without a decision-relevant adapter ambiguity, `SUPPORTED FOR PROMOTION` is bounded to the demonstrated presegmented retrieval capability only.

If the SUT fails the frozen retrieval gate on a legitimate measurement, preserve that failure and use `FALSIFIED` for the tested capability claim.

If a post-exposure adapter/apparatus ambiguity prevents the result from discriminating the intended SUT property, use `INCONCLUSIVE` rather than changing the apparatus.
