# RC0 Regression Surface Lineage

This surface is development/regression evidence only. It is not fresh RC1 qualification evidence.

Source: terminal RC0 bundle corresponding to Evidence Bundler PR #61, immutable head `7e4cfef6551c18ae63082b83c2cb6b0877edf9b9`.

Included are all 15 RC0 target/gold disposition mismatches from the decisive development run:
- 10 unsafe candidates accepted by RC0;
- 2 intrinsic-ambiguity candidates accepted by RC0;
- 3 safe candidates rejected by RC0.

Candidate semantics and expected dispositions are unchanged. Only `profile_id` is adapted from RC0 to `pc-evaluator-rc1-binding-v1` so the RC1 target can consume the predecessor fixtures. The exact RC0 evaluator is invoked unchanged through a profile adapter in `controls.py`; hosted execution must fetch it from immutable RC0 head `7e4cfef6551c18ae63082b83c2cb6b0877edf9b9` and verify SHA-256 `d6dcda3c053e4cb68a65aa8bcb01404e72e084cdd735068c6e6935cf8cb71643` before use.

Passing this regression surface cannot establish RC1 generalization because RC1 was designed after observing these failures.
