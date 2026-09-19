# Evidence Bundler V1 Slice 1 Promotion Design

**Status:** Draft production-promotion / local-pipeline candidate design  
**Production base:** `c26fbd4bfc8ba5c2604a784af158594b59fcae37`  
**Frozen research authority:** `4e1f6fe00e7c350b28f52bfea14f1f8988847884`

## Decision

Promote the smallest already-qualified Evidence Bundler V1 route needed for staged CAL Pipeline runs, without promoting unfinished Gate-informed selection research or changing Contract A / Contract B authority.

The slice is:

```text
released Contract A 2.0
        ↓
frozen Evidence Bundler V1 10/3 machinery
        + explicit retained-candidate admission
        ↓
native immutable EB V1 package
        ↓
exact non-semantic Contract B 1.2 compatibility projection
        ↓
released Contract B 1.2 bundle + projection receipt
```

The production-shaped operator surface is a dedicated installed CLI, leaving the legacy `evidence-bundler` command unchanged:

```bash
evidence-bundler-v1 inspect --json

evidence-bundler-v1 run \
  CONTRACT_A.json \
  --admission ADMISSION.json \
  --out-dir RUN_DIR/eb
```

The `run` command defaults to a packaged byte-identical copy of the frozen Contract B compatibility carrier. An explicit `--compatibility-carrier` override remains available for controlled reproduction. The historical `scripts/run_v1_integration_candidate.py` runner remains byte-identical to the frozen research authority and is retained as provenance/control surface rather than the primary installed interface.

## Why this subject

The exact frozen authority is Evidence Bundler PR #79 at `4e1f6fe00e7c350b28f52bfea14f1f8988847884`.

Its qualification established the bounded route `EB V1 -> Contract B 1.2 -> CAL intake` with:
- deterministic 10/3 V1 configuration;
- exact Contract A 2.0 intake;
- complete depth-10 nomination history;
- explicit retained-candidate admission state;
- released Contract B 1.2 projection;
- provenance and replay checks;
- fail-closed substitution/tamper controls;
- CAL consumer intake.

The frozen head is 22 commits ahead of maintained `main`, and the diff is additive only. No pre-existing production file differs. That makes a main-based minimal slice mechanically separable from the research record.

## Included

Only the qualified runtime/configuration closure is copied from the frozen subject:

- `src/evidence_bundler/v1/**`;
- `scripts/run_v1_integration_candidate.py`;
- exact frozen integration profile;
- exact Contract B compatibility carrier;
- dedicated `evidence-bundler-v1` installed CLI wrapper around the exact frozen V1 runtime;
- a packaged byte-identical compatibility carrier for repository-independent CLI execution;
- the direct V1 regression/conformance and production-CLI test surfaces.

The V1 runtime files and operator runner remain byte-identical to their frozen research blobs.

The compatibility carrier is moved to `config/eb_v1_slice/` without changing its bytes. Its internal scope remains `integration_candidate_only`; this PR does not relabel that frozen authority after the fact.

## Explicitly deferred

The slice does **not** include:

- typed-selector RC1, which was terminally falsified;
- Gate-informed obligation selection from PR #119;
- subject extraction/production for the Gate-informed selector;
- expected-evidence-form routing;
- semantic reranking or any selector not frozen in PR #79;
- query rewrite, adaptive K, or mid-run tuning;
- new admission semantics;
- proof of corpus or retrieval completeness;
- CAL semantics;
- Contract C / Decision / Authorization behavior.

PR #119's terminal fresh result was `SUPPORTED_SUBJECT_ONLY; COMBINED_FORM_INCREMENT_NOT_REPRODUCED`. Its conceptual successor was not frozen, and upstream subject production remains unqualified. Under the minimal-production-slice convention, that capability stays outside this slice.

## Contract authorities

Input:
- Contract A `2.0.0`;
- release commit `529c92b49a34d5c610618551a8737f019f9fa332`;
- validator blob `42e5f5b3bf38d677445e9d01ea130ba604e53409`.

Output:
- Contract B `1.2.0`;
- canonical production lock `c314e53bd91c0736aa4370a364673b069aceb43e`;
- immutable tag `contract-b-v1.2.0`.

Next consumer for qualification:
- CAL V1 local-pipeline candidate `61cab64149cb6119e4dbe1fe18496f3ccf89002f`;
- CAL PR #181;
- current disposition `QUALIFIED_FOR_LOCAL_PIPELINE_RUNS`.

The CAL candidate already re-executed the original frozen EB `4e1f6fe...` route through Contract B 1.2 into a clean-installed CAL wheel, including support and reversed-evidence/refutation controls. This PR still rechecks the new main-based slice against that consumer because production-slice identity is distinct from research identity.

## Qualification gate

Before this slice is called ready for local pipeline runs, one exact head must establish:

1. maintained `main` is an ancestor;
2. the allowed diff is limited to this production slice, its config, tests, promotion record, and qualification workflow;
3. all seven V1 runtime files and the runner are exact frozen blobs;
4. integration profile and compatibility carrier bytes match the frozen authority;
5. dedicated V1 package/projection tests pass;
6. full Evidence Bundler regression passes on Python 3.11 and 3.12;
7. Ruff, strict mypy on the maintained Python 3.11 lane, compileall, and dependency checks pass;
8. the historical runner remains invocable and the installed `evidence-bundler-v1` entry point exposes deterministic authority via `inspect --json`;
9. a built wheel installed into a fresh environment exposes `evidence-bundler-v1` and can execute the qualified V1 route;
10. exact Contract B 1.2 authority is present and its factual-context validator accepts the CLI-emitted extension;
11. exact current CAL V1 Slice 1 candidate accepts the CLI-emitted Contract B bundle;
12. known fail-closed controls remain green.

A repository-local green check alone is not the disposition.

## Version posture

This promotion introduces a new public installed CLI capability, `evidence-bundler-v1`. Under the project's strict pre-1.0 policy, that is a **MINOR** compatibility change.

The versioned promotion candidate is therefore `0.2.0`.

The native V1 package records `evidence_bundler.__version__` inside its producer identity, so this version assignment intentionally creates a new exact subject. Qualification must therefore run on the exact `0.2.0` tree, including built-wheel CLI smoke and cross-repository Contract B / CAL conformance, before any tag or GitHub Release is authorized.

The version change does not authorize broader retrieval, selector, Contract, CAL, Decision, or Authorization behavior.

## Preserved limitations and nonclaims

This slice preserves the known 10/3 limitations, including rank-4/rank-7 retention misses observed in the research programme. It does not reinterpret the historical legacy convergence non-pass `UNRESOLVED_AT_AUTHORIZED_BOUND`.

This PR does not establish:
- universal retrieval recall;
- evidence completeness;
- source legitimacy;
- a universally optimal retrieval default;
- semantic correctness of CAL;
- production release readiness;
- merge authorization;
- operational authorization.

## Stop rule

Stop rather than widen the slice if qualification requires:
- changing V1 retrieval or admission semantics;
- changing Contract A or Contract B;
- introducing Gate-informed selector authority;
- inventing compatibility state not already frozen;
- weakening a negative/tamper control;
- changing the output-version identity without fresh qualification.

Research evidence remains in its original PRs. This promotion slice points to it rather than importing the research history.
