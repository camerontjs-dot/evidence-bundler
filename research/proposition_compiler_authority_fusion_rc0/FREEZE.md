# Authority-Preserving Fusion RC0 — Pre-Fresh Freeze

Issue: #68  
Draft PR: #70

This record freezes the scientific resolver before any shared successor fresh case is authored.

## Exact scientific objects

- `fusion.py` Git blob: `dbf978216fb94b821c7f50fa1c5a11b702699618`
- `score.py` Git blob: `eaf7e6fbb78c71806362ef92f295abab1dd7f932`
- frozen RC1 semantic authority commit: `26539c53781148543e980fe1f07b25f1ad9c2005`
- frozen RC1 evaluator SHA-256: `1091169da8e960cdf93242ee4c629c7a1a814009c8f80554f4a190f5b3fe989d`
- frozen R2 model: `cross-encoder/nli-deberta-v3-small@fa2804872c3b4bd748f38c0185cc85775361e735`
- NLI floor: `0.90`
- inter-cluster NLI margin: `0.05`

No scientific code, hazard rule, authority precedence, model identity, score floor, or cluster margin may change after shared fresh cases are authored.

## Visible predecessor regression

Development workflow run: `34678303993`  
Job: `103512041964`  
Artifact: `10293790083`  
Artifact digest: `sha256:395d17111081de544f06c6e56242b751cfeb23b94bd50e581d584a30da154b25`

Historical corpus: PR #67 D01-D12 + F01-F24, all already revealed before this experiment.

- raw A/B SHA-256: `e478b6e4098d7ac2a6b13d0f031132750068c81012833baf27ec23ae6522232c`
- exact replay: byte-identical
- score SHA-256: `b0ba07fc35faf96a242babe61d0462f3941cb3e71d241f0731f2c8887e7218f4`

### A0 authority-only
- safe selections: 16
- unsafe selections: 0
- correct abstains: 5
- false abstains: 15

### A1 fusion
- safe selections: 16
- unsafe selections: 0
- correct abstains: 5
- false abstains: 15
- decision/representative path changes vs A0: 1

This regression supports proceeding to a fresh discriminating cohort only. It is not a positive result because A1 showed no root-level resolution gain on visible predecessor evidence.
