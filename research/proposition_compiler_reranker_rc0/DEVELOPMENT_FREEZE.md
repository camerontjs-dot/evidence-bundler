# Proposition Compiler Reranker RC0 — Development Freeze

Status: scientific scorer/calibration freeze complete. Fresh decisive corpus authoring may begin after this record.

## Scientific freeze identity

- freeze commit: `fe992639abc7e2624fe783627277fe9c6e846601`
- hosted development head: `fafe4847b2b10e57d5df2e9d8409e9299e4c8f4f`
- hosted development tree: `508ac2fc4d5f0d0d825f66253499752c859e224c`
- scorer blob `runner.py`: `c717d5c066305c3f612ef82c5314974a3777f1e3`
- calibrator blob `calibrate.py`: `1250868ac59278006eddf8a2f6ea22860e7782b8`
- fresh evaluator blob `evaluate.py`: `310a31d6f846a07c1eb9d2e1df4728aa2a1c9260`
- development corpus blob: `8909a1e4cbc2caa496b6eb95a2b536739fa29ad1`
- development gold blob: `04ed7a5d0ba369cf9c779a84039120d73b7269dc`
- frozen calibration blob: `d3476286fc01655ca1f379e8f4b4f2e5b50d5c0b`
- frozen calibration content SHA-256: `2099d086de75f05030bc6cbf0ba51ae4c2882e71c11e4c106860b634299bfcd5`

## Frozen model identities

- generic reranker: `cross-encoder/ms-marco-MiniLM-L6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a`
- bidirectional NLI: `cross-encoder/nli-deberta-v3-small@fa2804872c3b4bd748f38c0185cc85775361e735`

Observed hosted runtime for the development run:
- Python `3.11.16`
- torch `2.14.0`
- transformers `5.17.0`
- tokenizers `0.23.2`
- huggingface-hub `1.31.0`
- sentence-transformers `5.7.0`

The decisive workflow must pin or verify this runtime rather than silently accepting later dependency drift.

## Hosted development receipt

- run: `34675149853`
- job: `103503570031`
- conclusion: success
- artifact: `10292291086`
- artifact digest: `sha256:aa00bc44b3ecb290725dc0a5a0cedf153cee92e923649a0857e7785a65f0a610`
- raw A/B SHA-256: `ef0624e892f5c9073f57f4315bffa1c9b284ff9f5adb5865a56200c5cfef85fb`
- exact replay: byte-identical

The preceding failed workflow run `34675004898` is preserved separately in PR #67. It failed before scientific execution because of an over-broad source-firewall regex; no score or calibration was produced.

## Frozen development calibration

### B0 lexical
- floor `0.9`
- margin `0.2`
- safe selections `0/11`
- unsafe selections `0`
- ambiguity abstentions `1/1`
- false abstentions `11`

### R1 generic relevance reranker
- floor `0.9`
- margin `0.2`
- safe selections `0/11`
- unsafe selections `0`
- ambiguity abstentions `1/1`
- false abstentions `11`
- critical unsafe top-1 cases `3`

### R2 bidirectional NLI
- floor `0.9`
- margin `0.01`
- safe selections `7/11`
- unsafe selections `0`
- ambiguity abstentions `1/1`
- false abstentions `4`
- critical unsafe top-1 cases `2`

The two R2 critical top-1 errors are development cases D01 and D02, both shared-scope relocation. Their top1-vs-safe score gaps are below the frozen `0.01` selection margin, so the calibrated rule abstains rather than selecting the unsafe candidate.

This is a preserved weakness, not a repaired one. Fresh scope-attachment cases are required to discriminate whether the margin-based abstention generalizes.

## Freeze rule

From this point onward, no change to scorer code, calibration code, evaluator code, model identity, calibration grid, chosen calibration thresholds, candidate rendering or semantic terminal gates is permitted inside RC0. Any such change requires a successor experiment.
