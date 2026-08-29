# Gate 3 — SciFact immutable reconstruction

## Outcome

`PASS`

The exact archive bytes retrieved from the canonical upstream acquisition URL reproduced the Pilot 0A preregistered object exactly:

- canonical repository: `allenai/scifact`
- pinned repository commit: `68b98a56d93e0f9da0d2aab4e6c3294699a0f72e`
- upstream acquisition script blob: `ddce40f922bc93b8960c8b93405bc7572b094092`
- acquisition URL class: mutable `release/latest`
- expected archive SHA-256: `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`
- observed archive SHA-256: `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`
- expected bytes: `3115079`
- observed bytes: `3115079`
- HTTP ETag: `"cb7da4d8609e30f2c7483b61aa447f7e"`
- HTTP Last-Modified: `Tue, 26 Jan 2021 02:28:59 GMT`

The content hash therefore supplies an immutable identity even though the canonical retrieval URL is mutable.

## Frozen physical claims

All five frozen physical `claims_dev.jsonl` indices reconstructed, and every externally authored `cited_doc_ids` reference resolved in `corpus.jsonl`:

| physical line | claim ID | cited doc ID |
|---:|---:|---:|
| 199 | 911 | 11254556 |
| 66 | 295 | 20310709 |
| 278 | 1298 | 11718220 |
| 114 | 536 | 16056514 |
| 123 | 569 | 23460562 |

Missing cited documents: `0`.

Archive-contained source hashes include:

- `claims_dev.jsonl`: `86f0435d08fdb65d1aa41d1472684f57e6e71930626497bdf4d7a9ec1a632217` (65,007 bytes)
- `corpus.jsonl`: `b8d6c89624cb2ed74dee8938effc4f5d8bd2086887880af8110d64be4ceade62` (8,307,875 bytes)

The source-only acquisition persisted no SciFact `evidence` labels or rationale sentence IDs.

## Licensing

Authoritative `LICENSE.md` at the pinned upstream commit states:

- claims and evidence annotations: CC BY 4.0;
- abstracts/corpus via S2ORC: ODC-By 1.0;
- code: Apache-2.0.

This is adequate for this bounded research-methodology use, with attribution/licence obligations preserved. The mutable URL remains an acquisition-risk note, not an identity ambiguity, because the frozen archive hash reproduced exactly.
