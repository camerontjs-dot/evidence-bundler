# RC4 deviation 18d: post-sealed BM25 runtime dependency repair

## Observation

The corrected hosted RC4 apparatus run `33226760159` successfully completed:

- frozen-source / target / production-BM25 identity verification;
- exact benchmark regeneration, freshness, non-reuse and cue-independence validation;
- first sealed oracle generation;
- evaluator assurance.

The first exact production BM25 execution then stopped before producing any retrieval output.

The traceback was:

`ModuleNotFoundError: No module named 'yaml'`

Importing `evidence_bundler.retrieval.bm25_retriever` traverses the production package initializer into modules that import `evidence_bundler.contracts.yaml_io`. The pinned production `pyproject.toml` at `c8189c31adbab11729c31430c2070126224a2d42` declares `PyYAML>=6.0,<7`; the RC4 workflow had installed only Pydantic and rank-bm25.

## Exposure state at diagnosis

The first sealed oracle and evaluator-assurance outputs already existed, so the scientific object was frozen.

No BM25 raw/evaluation output existed. The workflow therefore skipped:

- BM25 replay/gating;
- all sealed weak/gaming controls;
- anti-gaming gate;
- metamorphic sealed assurance.

Hybrid and Semantic-only remained unexposed.

## Classification

This is an infrastructure/runtime-environment defect.

The repair does not alter:

- generator source or seed;
- generated benchmark bytes or benchmark-tree identity;
- runtime cases, passages, scopes, evaluator-only gold, or family membership;
- evaluator source;
- result schema;
- thresholds;
- original or additional weak/gaming controls;
- metamorphic definitions or expected directions;
- exact production source SHA or BM25 source blob;
- target identity or target configuration.

It only installs a dependency already declared by the exact pinned production source so that the already-frozen BM25 adapter can import and execute that source.

## Repair

Add `PyYAML>=6.0,<7` to the hosted workflow's exact BM25 runtime dependency installation and update only the freeze manifest's infrastructure-workflow SHA-256 binding.

The repaired workflow SHA-256 is:

`028995c2e63730c15d8e5751ab471a2505f88c83bb7e04486892b265b56133f0`

No scientific byte or decision criterion is changed.

## Preserved negative evidence

Run `33226760159` remains the first post-freeze hosted execution. Its first sealed control SHA-256 is:

`74bd5cef071470868d27e6b30e0f4587e0bc9e96fba4195b555ce6e1c5d8ff32`

Its evaluator-assurance SHA-256 is:

`20b80ebe3be822f21b316ab8a6829eab3fe481dc7010fa117618049f8deb53d1`

The run's terminal classifier reported `INCONCLUSIVE` solely because the exact production BM25 prerequisite was not completed. That provisional classifier output is preserved and does not substitute for the repaired unchanged-object run.
