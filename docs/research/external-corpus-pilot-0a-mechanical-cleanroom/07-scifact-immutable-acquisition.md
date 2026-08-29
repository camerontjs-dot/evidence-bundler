# Gate 3 — SciFact immutable reconstruction

## Scientific outcome

`NOT EXECUTED AS A CLEAN GATE`

The first source-acquisition workflow crossed the FreshStack pre-gold qrel firewall before it proceeded to SciFact acquisition. The task contract requires the affected clean scientific execution to stop at exposure, so the subsequent SciFact reconstruction cannot be characterized as a clean Gate 3 `PASS` in this execution.

## Preserved post-exposure mechanical observation

The workflow nevertheless observed that the bytes then served from the canonical SciFact acquisition URL matched the Pilot 0A preregistered archive identity exactly:

- canonical repository: `allenai/scifact`
- pinned repository commit: `68b98a56d93e0f9da0d2aab4e6c3294699a0f72e`
- upstream acquisition script blob: `ddce40f922bc93b8960c8b93405bc7572b094092`
- expected archive SHA-256: `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`
- observed archive SHA-256: same
- expected/observed bytes: `3115079`
- five requested physical claims were located and their `cited_doc_ids` resolved
- published SciFact `evidence` labels/rationale sentence IDs were not persisted or rendered

These observations may guide a later fresh clean execution but are not promotion-supporting evidence from this run.

## Pre-exposure licensing observation

Before the contaminated Actions acquisition, authoritative `LICENSE.md` at the pinned upstream commit was inspected through a source-only GitHub file surface. It states:

- claims/evidence annotations: CC BY 4.0;
- abstracts/corpus via S2ORC: ODC-By 1.0;
- code: Apache-2.0.

That source-only licensing observation preceded the qrel exposure, but the full Gate 3 reconstruction still remains unexecuted as a clean scientific gate.
