# Pre-evaluation deviation — selection archive serialization

Classification: archival serialization deviation. Selector semantics unchanged.

## What happened

The gold-blind selector runner produced a local selection object before evaluator freezing. When that JSON was archived through the GitHub connector at commit `3b062f49e72cbeef3d3c083dc03704084cd62c19`, the same parsed selection object was written with different whitespace/line formatting than the local runner output.

This made a raw file-byte hash unsuitable as the cross-transport identity even though the selector decisions themselves were unchanged.

## Correction

Before any evaluator artifact was committed, `run_selection.py` was changed only to serialize its already-determined selection object using canonical JSON:

`json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"`

Correction commit:

`f578ddf3e67532f0a226941d1793a318515c0ad1`

The selector algorithm, fixed budget, TF-IDF representation, objective, alpha values, tie-breaks, input candidate world, and selected proposition/evidence identities were not changed.

A fresh local rerun after the serialization-only correction reproduced the same parsed selection sets for every arm and produced canonical selection digest:

`sha256:d925877bfdb7410f2088a159fd3d23ae7204cce2aff98e22f18497980b6f8b81`

Final evaluation uses the canonicalized parsed JSON object for selection identity, not archival whitespace.

## Exposure note

This experiment is explicitly retrospective frozen-pool screening, not an independent clean-room qualification. The supervisor already knew the Phase-0 qualification results before this bake-off. A local evaluator probe was performed after the selection decisions were fixed but before this archival-format correction was documented. No selector algorithm, alpha, selected identity, or scientific decision rule was changed in response.

## Boundary

No retrieval rerun, semantic reviewer, production behavior change, or post-gold selector tuning occurred.
