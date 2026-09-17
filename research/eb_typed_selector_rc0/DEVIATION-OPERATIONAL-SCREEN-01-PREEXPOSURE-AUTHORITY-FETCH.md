# Deviation — Operational Pool Screen 01 Pre-Exposure Authority Fetch

Classification: **apparatus / authority-staging failure before scientific execution**.

Workflow run: `35186045197`

Failed job: `105088262582`

Tested head: `cda8a2e6c511e15041bc4a4d77502ac60bc5e6b2`

Failed-job artifact: `10481757857`

Failed-job artifact ZIP SHA-256: `f0de185898807a64f2d68ca4ac43ba4b2b89743761df9420d74a30e1471518a5`

## Observed failure

The exact predecessor candidate artifact downloaded and verified successfully to:

`sha256:3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`

The job then attempted to stage:

`research/eb_v1_operational_burden_rc1/SUPERVISOR_RELATION_MAP.json`

from PR #77 terminal commit:

`eb72be8f936d68cf2cfcb316e401626ea9de5839`

Git failed because that path is not present at that commit.

The relation map belongs to the PR #74 terminal authority:

`e84cfd84826eacb9751ecf4b54ff9c369547df58`

The operational label binding remains a PR #77 object at:

`eb72be8f936d68cf2cfcb316e401626ea9de5839:research/eb_v1_selector_bakeoff_rc0/OPERATIONAL_LABEL_BINDING.json`

## Exposure boundary

The failure occurred during authority staging.

The following steps did **not** run:

- semantic scoring of the 96 relationships;
- selector execution over the operational pool;
- operational-label reveal;
- operational evaluation.

Therefore this failed run contains no selector result and no scientific observation about the typed selector.

## Correction

Change only the relation-map fetch identity to PR #74 terminal commit `e84cfd84826eacb9751ecf4b54ff9c369547df58`.

Do not change:

- selector source or weights;
- semantic model or revision;
- generic development profile;
- candidate artifact;
- operational label binding;
- evaluation logic;
- K=3 budget;
- first-stage retrieval.

The corrected run is a successor apparatus execution, not a reinterpretation of this failure.
