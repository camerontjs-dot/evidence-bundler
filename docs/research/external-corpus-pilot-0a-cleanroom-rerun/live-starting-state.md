# Pilot 0A clean-room rerun - live starting state

Date: 2026-08-29

## Authority posture

Durable CAL Pipeline governance was re-read from the project library. Live GitHub and immutable repository artifacts were treated as authoritative for mutable state.

## Production state

- repository: `camerontjs-dot/evidence-bundler`
- default branch: `main`
- production `main` SHA: `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`
- main commit message: `Maintenance: cancel superseded provenance CI (#19)`
- main observed protected: `true`

## Required predecessor state

### PR #20 - `Research Infrastructure: external corpus methodology pilot 0A`

- state: `closed`
- merged: `false`
- draft: `true`
- base: `main`
- base SHA: `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`
- head branch: `research-infra/external-corpus-methodology-pilot-0a`
- head SHA: `357fe735067dbbd3d54f8872ffc8391dac724950`
- terminal disposition recorded in PR: `INCONCLUSIVE`
- preregistration commit recorded in PR: `bf6a347704d8711628e044f46c0c3fb9fa4557df`
- evidence-record commit recorded in PR: `dad4c9bc77b5740c619c57854dbc36a787d7228c`
- comment present: handoff from PR #21 states dummy P2/P3 infrastructure is `INCONCLUSIVE` because evaluator-B independence remains unestablished.

### PR #21 - `Research Infrastructure: external corpus evaluator independence and blind handoff`

- state: `open`
- merged: `false`
- draft: `true`
- base: `main`
- base SHA: `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`
- head branch: `research-infra/external-corpus-evaluator-independence-v1`
- head SHA: `764144f3da77140a8e542158948b4e88d40a7421`
- terminal disposition recorded in PR: `INCONCLUSIVE`
- evaluator/fixture evidence freeze recorded at: `185e169eea11e01cab39b9d658d78a9f2159a270`
- authorized pre-reveal snapshot: `9123eec2ec0da48f61bd063f634f1e20b1fc5f68`
- hosted dummy assurance comment: Actions run `33232876329` succeeded on Python 3.11 and 3.12, but does not establish genuine fresh-context evaluator-B independence.

### PR #22 - contaminated completion attempt

- state: `closed`
- merged: `false`
- draft: `true`
- base: `main`
- base SHA: `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`
- head branch: `research-infra/external-corpus-pilot-0a-completion`
- head SHA: `4d91e7a3de78981e4f73489aab179767c58c1914`
- terminal disposition recorded in PR: `FALSIFIED`
- use in this rerun: contamination record and procedural lesson only; not scientific gold and not evidence that Pilot 0A itself is invalid.

### PR #18 - RC4 apparatus

- state: `closed`
- merged: `false`
- terminal disposition: `FALSIFIED`
- head SHA: `f0331faa6f97b655de5b22dc419e21f3c0205df3`
- target exposure recorded as not authorized.

### PR #17 - RC4 target

- state: `closed`
- merged: `false`
- terminal disposition: `SUPERSEDED WITHOUT TARGET EXECUTION`
- head SHA: `27be0c85fdaae9e56a7622e007ca062575e9c433`
- Hybrid/Semantic target exposure recorded as `false`.

## Frozen Pilot 0A identities re-established from PR #20 preregistration

- FreshStack query dataset: `freshstack/queries-oct-2024-unfiltered`
- FreshStack query revision: `00150066ff2959688ad03ce7148ffb652f2fee38`
- FreshStack corpus dataset: `freshstack/corpus-oct-2024`
- FreshStack corpus revision: `069f66dc323e163b48b10d08408d282733d4393b`
- FreshStack framework source commit: `f1c4ec96477f5100f10c83798d33b3101db727fa`
- FreshStack frozen indices: langchain 271; yolo 42; laravel 121; angular 248; godot 36
- SciFact canonical upstream: `allenai/scifact`
- SciFact pinned repository commit recorded by preregistration: `68b98a56d93e0f9da0d2aab4e6c3294699a0f72e`
- SciFact recorded archive SHA-256: `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`
- SciFact recorded archive size: `3,115,079` bytes
- SciFact frozen physical `claims_dev.jsonl` indices: 199, 66, 278, 114, 123

## Successor work observed at start

The recent PR list contained no newer Evidence Bundler pull request after #22. PR #21 remained the only open PR among the required predecessor set.

No production or research branch was modified during live-state inspection.