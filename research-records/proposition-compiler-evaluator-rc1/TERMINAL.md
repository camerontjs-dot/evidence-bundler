# Proposition Compiler Evaluator RC1 — Terminal Record

## Disposition

`INCONCLUSIVE`

## Exact research head before terminal record

- branch: `research-infra/proposition-compiler-evaluator-rc1-binding-20260911`
- scientific/workflow head before this terminal record: `d5701727e3f30c037a253923c811eda0325374de`
- base `main`: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- frozen target commit: `26539c53781148543e980fe1f07b25f1ad9c2005`
- frozen target tree: `6d8cd9d376ce759b66652dc3c60623722d14a3b4`

## Supported local observations

The frozen RC1 binding-conservation evaluator produced no observed preregistered unsafe authoritative acceptance on the fresh local surface. It also returned fail-closed results for the fresh ambiguity cases and reproduced byte-identically on exact replay.

The fresh local result nevertheless failed the positive gate because three preregistered safe controls were rejected:

1. modal/shared-coordination case: lexical-category ambiguity around `Process` caused a valid second subject to be parsed as inherited predicate structure;
2. uniquely resolvable reference case: the resolver treated reference-resolution provenance (`uniquely_resolved`) as semantically different from an explicit child referent despite referent identity;
3. local-attribution case: matrix-predicate scope detection overextended a reporting construction and collapsed two root frames into one.

These are conservative false negatives, not observed unsafe accepts.

## Hosted execution

- maintained CI run `34613403697`: `success`
- RC1 research run `34613403673`: `failure`
- research job `103309260762`

The research workflow stopped at frozen-byte verification before fresh execution because two workflow checksum expectations were stale:

- `research/proposition_compiler_evaluator_rc1/score.py`
- `research/proposition_compiler_evaluator_rc1/metamorphic_fixture_materializer.py`

All earlier checked frozen scientific objects in that step that were reported individually as OK remained consistent, including the target evaluator, controls, raw runner, regression cases/gold, and fresh fixture materializer. The hosted failure is an execution-harness/manifest failure, not a hosted semantic result.

## Why `INCONCLUSIVE`

RC1 did not hit a semantic falsifier on the local decisive surface, so `FALSIFIED` would overstate the evidence. Positive support is also unavailable because:

- three preregistered safe positive controls failed locally;
- the hosted positive-evidence workflow did not reach semantic execution;
- fresh promotion-critical gold did not have independent human adjudication.

The correct terminal disposition is therefore `INCONCLUSIVE`.

## Successor boundary

A successor should not patch the monolithic parser one construction at a time. The next bounded research question is whether heterogeneous proposal mechanisms can increase safe recoverability while preserving a fixed fail-closed semantic-binding authority layer.

No compiler, production behavior, Contract A/B/C, retrieval, CAL, or Decision Engine change is authorized by this record.
