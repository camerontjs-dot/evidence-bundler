# Gate 1 — FreshStack exact provenance reconstruction

## Scientific outcome

`NOT VALIDLY COMPLETED — EXECUTION ALREADY FALSIFIED BY PRE-GOLD QREL ACCESS`

The acquisition harness intended to be source-only read full FreshStack query Parquet rows into process memory. Pinned FreshStack loader code establishes that those query rows contain the `nuggets` field used to construct qrels. Because the harness did not project away that field before deserialization, published qrel-bearing data crossed the clean-room boundary before scientific gold freeze.

Under the frozen task contract, exposure/access itself is the falsifier. Therefore the later FreshStack reconstruction observations below are preserved only as **contaminated diagnostic evidence** and must not be cited as a clean Gate 1 result.

## Contaminated diagnostic observations

At frozen query dataset `freshstack/queries-oct-2024-unfiltered@00150066ff2959688ad03ce7148ffb652f2fee38`, the fail-soft diagnostic later observed:

| topic | frozen row count | frozen selected index | observed test rows | selected row present |
|---|---:|---:|---:|---|
| langchain | 318 | 271 | 318 | yes |
| yolo | 94 | 42 | 94 | yes |
| laravel | 230 | 121 | 310 | yes |
| angular | 310 | 248 | 230 | no |
| godot | 197 | 36 | 0 | no |

The exact pinned file tree diagnostic contained no `godot` test parquet and only 230 angular rows, so the recorded angular/godot frozen indices were not reconstructed. This is a potentially important preregistration-integrity defect, but this execution cannot elevate it to a clean scientific discriminator because the qrel firewall had already been crossed.

The exact official corpus revision `freshstack/corpus-oct-2024@069f66dc323e163b48b10d08408d282733d4393b` was also mechanically acquired and hashed after exposure. Same-dataset history inspection did not find a usable commit-bearing representation, so immutable upstream source-byte binding remained unexecuted.

## What may be reused

Only the procedural lesson is authoritative from this contaminated Gate 1 attempt:

1. Parquet readers must use an explicit allow-listed column projection **before deserialization**.
2. Merely suppressing forbidden fields at output/persistence is insufficient isolation.
3. Query-row identity verification and qrel-bearing scientific fields must be mechanically separated into different artifacts or read paths.
4. A future fresh execution may independently test the observed revision/row mismatch, but this run does not cleanly establish it.

No repair to Pilot 0A is authorized.
