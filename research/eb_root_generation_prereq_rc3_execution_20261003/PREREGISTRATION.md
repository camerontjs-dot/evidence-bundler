# Root-generation prerequisite RC3 context-free execution candidate

## Objective

Freeze a context-free execution candidate using the exact qualified RC3 prerequisite apparatus, without invoking the writer during setup.

A later separately authorized execution may spend exactly one writer attempt and one custody/check attempt.

## Authority

Repository: `camerontjs-dot/evidence-bundler`.

Protected main:

`c26fbd4bfc8ba5c2604a784af158594b59fcae37`

Qualified RC3 apparatus:

- PR #129 evidence head: `2990f02c330f1b47b5e1138925f1d7df5bfd1a95`
- disposition: `SUPPORTED_FOR_PREREQUISITE_EXECUTION_CANDIDATE`
- frozen source: `55c2940d6822a6c666441f61900b2cadcfbde046`
- source tree: `0dcee5f8b872d74ca754818c2b0535d1698fd8ae`
- qualified envelope: `9756d3862efaa40a7e2db51adf1d2db2e8a12411`
- envelope tree: `4010ab5c714940937f5cabfefe22d5403d68c6bd`
- closure blob: `5eaea44e5495df6cfd595c5e111ef59d6ea10964`

Historical evidence remains unchanged:

- PR #127: RC2 `BLOCKED_CUSTODY_VERIFICATION`, reason `'output'`
- PR #128: classifier `SUPPORTED_FOR_APPARATUS_SUCCESSOR`
- PR #129: apparatus `SUPPORTED_FOR_PREREQUISITE_EXECUTION_CANDIDATE`

## Exact apparatus reuse

The following files must be byte-identical to RC3 apparatus source `55c2940...`:

- `AUTHORING-RUBRIC.json`
- `PROFILE-SURFACE.json`
- `PROFILE-WRITER-TASK.md`
- `BOOTSTRAP-MANIFEST.json`
- `CUSTODY-SCHEMA.json`
- `WRITER-TRANSPORT.json`
- `LAUNCH-STATUS.json`
- `validate_setup.py`
- `check_execution.py`
- `run_writer.py`

No scientific, semantic, runtime, profile, request, aperture, checker, or launcher change is authorized.

## Runtime authority

Pinned future execution runtime:

- destination: `http://127.0.0.1:11434/api/generate`
- Ollama service: `0.35.1`
- model: `qwen3.5:9b`
- service-reported model digest: `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`

If live authority differs before POST, the future execution must stop `BLOCKED_AUTHORITY` without consuming the writer attempt.

## Context-free aperture

The fresh writer may receive only what frozen `run_writer.py` supplies:

- `BOOTSTRAP-MANIFEST.json`
- `PROFILE-WRITER-TASK.md`
- `AUTHORING-RUBRIC.json`
- `PROFILE-SURFACE.json`
- launcher-observed runtime capability metadata

Do not manually add project history, PR narrative, prior profiles, native outputs, cases, oracle, weak-system outputs, target outcomes, private PR #124 material, corpus, retrieval or passage-review context.

Forbidden exposure before profile freeze stops `CONTAMINATED`.

## Attempt budget for future execution

- profile writer: 1
- external custody/check: 1
- semantic calibration: 0
- target generation: 0
- deterministic weak generators: 0
- decisive review: 0
- tally: 0

Writer attempt consumption begins only when frozen `run_writer.py` sends the POST.

No retry, repair, reroll, model substitution, parameter change or alternative checker is authorized after POST begins.

## Terminal future execution states

Use the frozen RC3 structured result:

- `SUPPORTED_FOR_GENERATION_EXECUTION`
- `BLOCKED_PROFILE_CONFIGURATION`
- `BLOCKED_CUSTODY_VERIFICATION`
- `BLOCKED_AUTHORITY`
- `CONTAMINATED`
- `INCONCLUSIVE`

Stop on the first terminal state.

## Setup acceptance

This setup is ready only if:

1. exact RC3 apparatus authority is live and unchanged;
2. all ten apparatus/contract files are byte-identical to source `55c2940...`;
3. frozen `validate_setup.py` passes unchanged;
4. candidate closure binds every frozen file;
5. dedicated exact-head CI passes on Python 3.11 and 3.12;
6. ordinary repository CI passes;
7. no writer/model/network invocation occurs during setup;
8. protected main and PRs #127-#129 remain unchanged.

## Boundary

This setup task must not run `run_writer.py` as a command and must not call Ollama or `/api/generate`.

A fully qualified setup authorizes only the later one-shot context-free prerequisite execution.

No semantic calibration, generation case, weak generator, private population work, production change, merge, release or promotion is authorized.
