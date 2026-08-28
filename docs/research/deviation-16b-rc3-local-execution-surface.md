# RC3 apparatus deviation 16b — local execution surface after Actions trigger failure

## Reason

The GitHub connector's Git-data and Contents API writes did not create an Actions run for the branch-local RC3 workflow. The workflow file itself remained frozen and unchanged, but the configured GitHub-hosted Python 3.12 job could not be started through the available control surface.

A local execution surface was therefore used for the first sealed BM25/lexical apparatus control rather than altering the scientific object or attempting to expose Hybrid/Semantic.

## Frozen-byte verification before sealed execution

Before any local BM25/lexical output was produced, the local mirror verified all source SHA-256 values in `research/eb_retrieval_generalization_rc3/apparatus_freeze_manifest.json` and regenerated the exact expected benchmark bytes.

- pre-control apparatus commit: `36ec382c3cd94b6dd1a6be652e49a80469e6b1a4`
- freeze-manifest SHA-256: `3f8efeaab3e814c146da937f7824ae62ba8506320dd3ddb7149454f9a063bed7`
- generated benchmark tree SHA-256: `f83bdbec6fd89864ee512ff4557ce51eb53164917bec32b03fb5560e01a71c1e`
- exact c818 BM25 Git blob: `f8d7dd7e56710453edbca7c51aeea6da949ff903`
- exact upstream `rank_bm25.py` tag `0.2.2` Git blob: `d1b5ab9fc0d4f301f2ec995789d41051e65cfa9e`

The c818 `_indexable.py`, `hits.py`, and `models/document.py` blobs also matched their pinned Git identities before execution.

## Local environment

- Python `3.13.5`
- Linux `6.18.35` x86_64, glibc `2.41`
- NumPy `2.3.5`
- Pydantic `2.13.4`
- `rank-bm25` version identity `0.2.2`, with `rank_bm25.py` byte-identical to upstream tag `0.2.2`

This differs from the frozen GitHub workflow's Python `3.12` execution environment and must not be presented as the missing GitHub-hosted CI receipt.

## Exposure state

- `hybrid_sealed_exposed = false`
- `semantic_sealed_exposed = false`

## Additional limitation

The local validator could not load the committed RC2 runtime corpus through the isolated execution environment, so its automated exact RC2 text/entity non-reuse check reported `performed=false`. This is retained as an unresolved apparatus-assurance limitation. It is not the reason for the terminal disposition; the apparatus was independently falsified by a runtime-only gaming control.
