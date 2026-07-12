# Lexical vs hybrid fixture comparison report

status: recorded
last_updated: 2026-05-12

Candidate passages are retrieval nominations, not support determinations. Fixture expectation matches are local nomination checks only; review is required before audit use.
Negative or null fixture results are valid outcomes.

## Metadata

- Fixture: `tests/fixtures/scaffold-run-mixed-formats`
- Generated at: `2026-05-12T18:57:08Z`
- Comparison scope: `lexical_bm25` vs `hybrid_rerank_only` vs `hybrid_rerank_contradiction`
- C-A/C-B contract status: `v1.0.0 unchanged`
- Contradiction activation: `config-only via RetrievalConfig / --config`

## Metric Definitions

- Supporting source recall: expected supporting source IDs retrieved at least once / total expected supporting source IDs.
- Supporting precision proxy: macro-average by claim of matched expected supporting source IDs / unique retrieved supporting source IDs; claims with expected support and no retrieved supporting source score `0.0`.
- Counter-candidate recall: expected counter-candidate needles found in `counterevidence_passages` / total expected counter-candidate needles; `n/a` when contradiction retrieval is disabled.
- False-positive counter-candidate count: counter-candidate passages without an expected needle for that claim, plus all counter-candidates for claims with no expected counter-candidate; `n/a` when contradiction retrieval is disabled.

## Run Summary

| Run | Status | Config hash | Method | Rerank | Contradiction | Supporting source recall | Supporting precision proxy | Counter-candidate recall | False-positive counter candidates |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `lexical_bm25` | completed | `sha256:d413e323cfcd4fce7efb5fff980d3953723cc5150481e6b8f3a191e57c431fe5` | `bm25` | `False` | `False` | 3/3 | 0.556 | n/a | n/a |
| `hybrid_rerank_only` | completed | `sha256:759398ab10e1024e146d1ea7e26f67f81cbec1f29718a0927fb143f24dd80ee4` | `hybrid` | `True` | `False` | 3/3 | 0.556 | n/a | n/a |
| `hybrid_rerank_contradiction` | completed | `sha256:165cf05ff8bcebc161a7980b819ebdd308a6800cfa1d984125ba42aaab1bc89f` | `hybrid` | `True` | `True` | 1/3 | 0.333 | 2/2 | 3 |

## Per-Claim Candidate Nominations

### lexical_bm25

| Claim | Expected support | Retrieved supporting sources | Matched support | Expected counter needles | Matched counter needles | False-positive counter candidates | Supporting candidates | Counter candidates |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `clm-md` | `src-md` | `src-md` | `src-md` | `no significant effect` | n/a | n/a | `supporting:src-md:03bca114b38b`, `supporting:src-md:146e0f58f1e6`, `supporting:src-md:2f47759502a4`, `supporting:src-md:4a3907b3d301`, `supporting:src-md:7d8968f45e47` | none |
| `clm-txt` | `src-txt` | `src-md`, `src-pdf`, `src-txt` | `src-txt` | `only when` | n/a | n/a | `supporting:src-md:2f47759502a4`, `supporting:src-md:4a3907b3d301`, `supporting:src-md:7d8968f45e47`, `supporting:src-pdf:3f567eff5988`, `supporting:src-txt:0823b6706c53` | none |
| `clm-pdf` | `src-pdf` | `src-md`, `src-pdf`, `src-txt` | `src-pdf` | none | n/a | n/a | `supporting:src-md:146e0f58f1e6`, `supporting:src-md:2f47759502a4`, `supporting:src-md:4a3907b3d301`, `supporting:src-pdf:3f567eff5988`, `supporting:src-txt:0823b6706c53` | none |

### hybrid_rerank_only

| Claim | Expected support | Retrieved supporting sources | Matched support | Expected counter needles | Matched counter needles | False-positive counter candidates | Supporting candidates | Counter candidates |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `clm-md` | `src-md` | `src-md` | `src-md` | `no significant effect` | n/a | n/a | `supporting:src-md:03bca114b38b`, `supporting:src-md:146e0f58f1e6`, `supporting:src-md:2f47759502a4`, `supporting:src-md:4a3907b3d301`, `supporting:src-md:7d8968f45e47` | none |
| `clm-txt` | `src-txt` | `src-md`, `src-pdf`, `src-txt` | `src-txt` | `only when` | n/a | n/a | `supporting:src-md:146e0f58f1e6`, `supporting:src-md:2f47759502a4`, `supporting:src-md:4a3907b3d301`, `supporting:src-pdf:3f567eff5988`, `supporting:src-txt:0823b6706c53` | none |
| `clm-pdf` | `src-pdf` | `src-md`, `src-pdf`, `src-txt` | `src-pdf` | none | n/a | n/a | `supporting:src-md:146e0f58f1e6`, `supporting:src-md:2f47759502a4`, `supporting:src-md:4a3907b3d301`, `supporting:src-pdf:3f567eff5988`, `supporting:src-txt:0823b6706c53` | none |

### hybrid_rerank_contradiction

| Claim | Expected support | Retrieved supporting sources | Matched support | Expected counter needles | Matched counter needles | False-positive counter candidates | Supporting candidates | Counter candidates |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `clm-md` | `src-md` | `src-md` | `src-md` | `no significant effect` | `no significant effect` | 0 | `supporting:src-md:03bca114b38b`, `supporting:src-md:146e0f58f1e6`, `supporting:src-md:2f47759502a4`, `supporting:src-md:4a3907b3d301` | `counter:src-md:7d8968f45e47` |
| `clm-txt` | `src-txt` | `src-md` | none | `only when` | `only when` | 1 | `supporting:src-md:146e0f58f1e6`, `supporting:src-md:2f47759502a4`, `supporting:src-md:4a3907b3d301` | `counter:src-pdf:3f567eff5988`, `counter:src-txt:0823b6706c53` |
| `clm-pdf` | `src-pdf` | `src-md` | none | none | none | 2 | `supporting:src-md:146e0f58f1e6`, `supporting:src-md:2f47759502a4`, `supporting:src-md:4a3907b3d301` | `counter:src-pdf:3f567eff5988`, `counter:src-txt:0823b6706c53` |

## Candidate Deltas

### Hybrid rerank-only vs BM25

Baseline: `lexical_bm25`. Comparison: `hybrid_rerank_only`.

| Claim | Added candidates | Removed candidates |
| --- | --- | --- |
| `clm-md` | none | none |
| `clm-pdf` | none | none |
| `clm-txt` | `supporting:src-md:146e0f58f1e6` | `supporting:src-md:7d8968f45e47` |

### Contradiction-aware hybrid vs hybrid rerank-only

Baseline: `hybrid_rerank_only`. Comparison: `hybrid_rerank_contradiction`.

| Claim | Added candidates | Removed candidates |
| --- | --- | --- |
| `clm-md` | `counter:src-md:7d8968f45e47` | `supporting:src-md:7d8968f45e47` |
| `clm-pdf` | `counter:src-pdf:3f567eff5988`, `counter:src-txt:0823b6706c53` | `supporting:src-pdf:3f567eff5988`, `supporting:src-txt:0823b6706c53` |
| `clm-txt` | `counter:src-pdf:3f567eff5988`, `counter:src-txt:0823b6706c53` | `supporting:src-pdf:3f567eff5988`, `supporting:src-txt:0823b6706c53` |

## Reproduction checklist

- Committed fixture used: `tests/fixtures/scaffold-run-mixed-formats`.
- All three configs completed or explicitly failed: `True`.
- Config hashes recorded for completed runs: `True`.
- Metric formulas applied exactly as listed in this report.
- C-A/C-B v1.0.0 unchanged; expectations live outside contract fixtures.
- Calibrated nomination language used; candidates are not support verdicts.
- Verification commands recorded with this artifact: `ruff check .`, `python -m pytest`, `python -m compileall src`, comparison script, BM25 smoke, hybrid smoke.

Finding: this fixture comparison records candidate-nomination behavior only. No default, schema, or vocabulary change is justified by this artifact alone.
