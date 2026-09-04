# NEXT — Retrieval Arm Receipt and Observability Hardening

Status: **CHARACTERIZATION NOT AUTHORIZED**

RC0 source freeze: `a02a9d313816ad8302efbcbb24bca265c31473e7`

Terminal RC0 class: `RC0_APPARATUS_FAILURE`

The next task is not retrieval tuning. It is the smallest apparatus repair needed to make a retrieval arm independently reconstructable and its advertised variables observable.

## Required repair

1. **Write a machine-readable research-arm receipt for every characterization run.**

   The receipt must bind at least:

   - repository and apparatus commit SHA/tree;
   - source corpus/run identity and corpus hash;
   - complete normalized `RetrievalConfig`, including `semantic_query_prefix`;
   - retrieval configuration hash;
   - chunk geometry;
   - materialized ordered chunk-set hash, including transient semantic runs;
   - canonical embedding model ID and immutable revision when active;
   - canonical reranker model ID and immutable revision when active;
   - relevant runtime package versions and Python version;
   - output bundle/report hashes;
   - execution timestamp and compute/device identity needed to interpret latency/cost receipts.

   Cache directories and output paths may remain non-identity fields if their exclusion is explicit and tested.

2. **Add an advertised-variable observability matrix.**

   For every field admitted as an experimental independent variable, a mutation/metamorphic test must demonstrate one of:

   - the intended downstream computation changes and the receipt identity changes; or
   - the field is a documented invariant/non-experimental value and is not presented as a tunable arm dimension.

   A changed configuration hash alone is not sufficient proof of downstream observability.

3. **Execute the exact pinned real-model smoke on the final repaired apparatus SHA.**

   Use the preregistered model revisions unless a separate evidence record changes them:

   - `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
   - `cross-encoder/ms-marco-MiniLM-L6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a`

   Persist the smoke receipt and its hash. This is an apparatus execution test, not a model-quality result.

4. **Expose only the additional research-only controls required by the planned blocks.**

   Before Block A, establish a truthful parent-candidate budget distinct from final `top_k` if the experiment intends to vary parent pool size independently.

   Before Block E, establish an independent counterevidence child candidate budget. The current contradiction pass uses `rrf_candidate_pool` for both lexical and semantic child retrieval, so it cannot support the requested independent counterevidence-budget experiment as written.

   Do not change production defaults.

5. **Retire stale bootstrap transport on the successor line.**

   `.github/workflows/research-retrieval-control-surface-rc0-bootstrap.yml` is no longer a truthful ongoing validation workflow because its patch scripts were deleted at freeze. Remove or replace it only on the successor apparatus line. Preserve the historical workflow runs.

6. **Freeze a separate non-Pilot diagnostic evaluator and corpus after items 1–5 pass.**

   Do not reuse Pilot scientific qrels or infer validity from the external-corpus evaluator record. The diagnostic evaluator must be deterministic, fixture-bound, and tested against intentionally weak controls before retrieval characterization begins.

## Repair falsifiers

The successor apparatus is not ready if any of the following occurs:

- two materially different experimental configurations can produce the same research-arm receipt identity;
- a receipt cannot reconstruct every computation-relevant arm field;
- a declared independent variable cannot be shown to affect the intended computation or be explicitly classified as invariant;
- an exact pinned model revision cannot be loaded/executed from the repaired frozen SHA;
- a semantic index can alias a different model revision or chunk set;
- the diagnostic evaluator cannot reject at least one intentionally weak but plausible retrieval strategy for the intended reason;
- any repair requires Pilot scientific gold to determine whether the apparatus works.

## Stop condition

When the repair is frozen, independently replay one synthetic arm from only its corpus plus receipt. If the replay reproduces the same normalized arm identity and expected retrieval mechanics, the characterization authorization gate can be reconsidered.

Until then, do not run the characterization sweep and do not promote retrieval defaults.