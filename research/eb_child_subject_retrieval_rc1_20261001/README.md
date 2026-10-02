# Child coverage and exact-subject retrieval RC1

Admission RC0 is terminally falsified. This separate experiment tests upstream
retrieval, preserving the exact EB 0.2.0 BM25 baseline and adding a matched
semantic reference plus independent child/subject ablations.

Read [PREREGISTRATION.md](PREREGISTRATION.md), then `SPEC.json`. Only mechanical
research apparatus is tested in Phase 1. Fresh population, execution runtime and
semantic reviewer qualification remain unbound; decisive execution is BLOCKED.

`retrieval.py` implements the fixed research arms without changing V1.
`study.py` checks independent input binding, builds an arm/rank-blinded packet,
checks reviewer controls and computes the preregistered counts from supplied
judgments. It does not generate semantic judgments or launch reviewers.
All synthetic fixtures are exposed development controls, never real qualification.

Run apparatus tests from the repository root:

```bash
python -m pytest -q research/eb_child_subject_retrieval_rc1_20261001/test_apparatus.py
python -m ruff check research/eb_child_subject_retrieval_rc1_20261001
```

The CLI writes only to fresh private output directories and refuses unbound inputs.
See [NEXT-RUN.md](NEXT-RUN.md) for the preparation boundary. No decisive result is
claimed, and no frozen predecessor is reopened, overwritten or retuned.
