# CAL-Specific Learned Reranker RC0 — Pre-Fresh Freeze

Issue: #69  
Draft PR: #71

This record freezes the learned ranking signal before any shared successor fresh case is authored.

## Exact scientific objects

- `cal_ranker.py` Git blob: `f0440ca67189bedd1f898bed46dfc8a80ac6c12e`
- `evaluate.py` Git blob: `cd3f2cb75e3ebfd51d16be480b64d9adcde35585`
- `FROZEN_MODEL.json` Git blob: `0e9e10d998c2641ea90a19c079125394d735ff0c`
- frozen model content SHA-256: `a4e6aecbb02af4cb1cdd4bd6116a955ca4cc05480ad93daf00ca28323de91e7b`
- frozen base semantic scorer: PR #67 `runner.py` blob `c717d5c066305c3f612ef82c5314974a3777f1e3`
- frozen R2 model: `cross-encoder/nli-deberta-v3-small@fa2804872c3b4bd748f38c0185cc85775361e735`
- frozen R1 model: `cross-encoder/ms-marco-MiniLM-L6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a`

No feature, weight, standardization statistic, training/calibration split, optimizer parameter, runtime scorer, or learned model byte may change after shared fresh cases are authored.

## Training and calibration boundary

Training roots: `D01-D12`, `F01-F16`.  
Held-out predecessor calibration roots: `F17-F24`.

The frozen model is deterministic. Two independent executions in the same hosted run produced byte-identical model SHA-256 `a4e6aecbb02af4cb1cdd4bd6116a955ca4cc05480ad93daf00ca28323de91e7b`.

### Preserved calibration failure

`NO_ZERO_UNSAFE_CALIBRATION`

Best observed preregistered grid point:
- floor: `2.0`
- margin: `2.0`
- safe selections: `3`
- unsafe selections: `1`
- correct abstains: `3`
- false abstains: `1`

No wider threshold search or post-hoc repair was performed. Therefore T1 has **not** earned a calibrated `SELECT` function in RC0. Fresh testing may assess ranking generalization but cannot silently convert T1 into authority.

## Revealed predecessor characterization

Training/reporting workflow run: `34678574247`  
Job: `103512769044`  
Artifact: `10293710552`  
Artifact digest: `sha256:0c657e75b753cdcbb669776c78687e4a2b1b61c3879341e7f31a014478e040fb`

- reproduced base raw SHA-256: `5903c674c4234ad8d8b7c483a3eed8502679326c1814481b4b24f35dad4b69ed`
- learned-score raw SHA-256: `651e7c6805322589726f691621e1529b74b6f48dd354f015fbd945c6aa3224f5`
- evaluation SHA-256: `e240a21e695a3ac9212aa076a6306e98ccb431b3fa84ad9b7b765d50b0f13bba`

Across all already-revealed predecessor SELECT roots:

### Frozen R2
- top-1 safe preference: `0.774194`
- pairwise safe-over-unsafe: `0.886598`
- critical pairwise: `0.865854`

### T1 CAL linear ranking signal
- top-1 safe preference: `0.967742`
- pairwise safe-over-unsafe: `0.979381`
- critical pairwise: `0.975610`
- selection unavailable because no zero-unsafe calibration exists.

This is evidence of a stronger ranking signal on already-revealed data, not evidence of fresh generalization or authority.

## Preserved development deviation

The initial evaluator suppressed pairwise metrics whenever a learned model lacked a zero-unsafe calibration. Before any shared fresh case existed, `evaluate.py` was changed only to report ranking metrics while leaving selection unavailable. Training code, feature vector, weights, model bytes, calibration grid, calibration result, and base scorer were not changed. This reporting repair is frozen in blob `cd3f2cb75e3ebfd51d16be480b64d9adcde35585`.
