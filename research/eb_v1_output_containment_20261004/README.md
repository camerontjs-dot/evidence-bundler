# EB V1 output containment correction

This is a bounded engineering correction and a dated evidence record for [the v1 plan, #132](https://github.com/camerontjs-dot/evidence-bundler/issues/132). The predecessor is frozen [PR #120](https://github.com/camerontjs-dot/evidence-bundler/pull/120), commit `08ca896debd6d16fa21be2f178ed7cbe62395d00`, package `0.2.0`. The correction is an unreleased `0.2.1.dev0` candidate. Its current GitHub checks and disposition belong to its PR.

## Defect and consequence

The installed predecessor uses proposition and source IDs literally in Contract B paths. Four independently constructed controls supplied traversal or absolute IDs through otherwise valid Contract A 2.0. Each overwrote a disposable sentinel outside the requested output directory. EB then failed during factual-context validation, after writing its native package and part of the B tree. No receipt was emitted. A nonzero exit therefore did not establish that the run had no side effects.

The original [independent probe plan](01-independent-probe-plan.md) preceded implementation/test inspection. [The unchanged reproducer](02-path-containment-probe.py) hashes to `70f18e7c57e3ac6b0e90b358c621a8dd0be44f6fb1ccf69a19d3d6df3eaee52a`. It only targets files that it creates in its own disposable directory. [EVIDENCE.json](EVIDENCE.json) records the original and corrected outcomes, wheel identities and tested runtime blobs. The [portable review](BASELINE-PORTABLE-REVIEW.md) is a presentation copy of the original report with local paths replaced; its original hash is preserved. Named raw logs remain local and are not implied to be present in this directory.

A [separate 21-case boundary review](additional/04-baseline-findings.md) also preserves declared-root/child, non-retained-source, symlink, alias and literal-name controls. Its baseline has seven output-safety failures and four separately labeled portable-alias-policy failures. The design/freeze/script are copied unchanged; historical scratch paths in that freeze are evidence identities, not paths a receiving operator should reuse. Raw run logs referenced by the report remain local.

## Correction

Projection validates every actual output-name namespace before writing: the root plus declared claims, every nominated source including non-retained/rejected candidates, and the deduplicated passage names. The installed command runs that preflight before creating an output directory or writing the native package. Direct `project_contract_b` callers receive the same name validation before its first write. The direct API also refuses an existing `contract_b` or `projection_receipt.json` symlink, including broken links.

Accepted IDs are preserved literally. IDs are never trimmed, encoded, normalized, renamed, or decoded. The shared [A2 validator](https://github.com/camerontjs-dot/apparatus-contracts/blob/529c92b49a34d5c610618551a8737f019f9fa332/validators/contract_a_rc2.py) accepts opaque nonblank identities; this correction does not modify it. B's [locked physical layout](https://github.com/camerontjs-dot/apparatus-contracts/blob/c314e53bd91c0736aa4370a364673b069aceb43e/handoff-contract-v1.0.0.md) and identity loaders make filename encoding an incompatible shortcut. A valid A2 object can therefore be refused by the narrower EB filesystem projection profile.

The projection profile refuses:

- Slash/backslash, absolute/rooted/Windows-drive syntax, and actual `.` or `..` output components.
- Surrounding whitespace, control/surrogate/line-separator characters, and generated components exceeding 255 UTF-8 bytes, including their suffix.
- Distinct sibling names that alias after NFC normalization and full case folding, checked separately for claim filenames and source directories.

Ordinary colon-bearing IDs, safe Unicode, literal percent-encoded strings, internal `..`, and the same ID reused across claim/source roles remain possible. Generated `passage:...` IDs remain unchanged. Claim IDs `.` and `..` produce the ordinary filenames `..yaml` and `...yaml`; source IDs `.` and `..` are refused because they are directory components. Unretrieved source IDs are not used as directory names and remain native/aperture metadata.

An operator-supplied output root is resolved intentionally. The change prevents input-ID traversal and pre-existing nested output links; it does not claim protection against a hostile concurrent local process swapping paths between checks and writes. NFC/casefold catches common aliases but is not an exact model of every filesystem's name equivalence. Native macOS observation remains a separate local gate, and Windows is not newly claimed as a supported platform. The command is not a general transactional rollback system for unrelated I/O failures.

## Identity and compatibility

The native builder, A2 consumer, retrieval, package schema, 10/3 profile, carrier, shared contracts, CAL semantics and the old promotion workflow are unchanged. The inherited `frozen_v1_implementation` field identifies that native builder; it does not identify this corrected projection. The wheel/version, source commit and qualification receipts identify the complete successor.

The new development version distinguishes artifacts from the frozen `0.2.0` package. New CLI output includes the producer-version change, so package and dependent bundle/receipt hashes are expected to change. That is not a retrieval improvement or a schema change. Accepted IDs keep their original meaning; newly refused path forms are an explicit safety boundary. No `1.0.0` release is declared.

## Verification and remaining claims

The local installed-wheel replay of the original four controls preserves every sentinel and emits neither native package nor receipt. Author regressions exercise declared-root/child paths, source paths, common aliases, literal compatible names and direct output symlinks. The full lightweight Python 3.12 run reports 281 passed / 6 skipped; after installing the pinned CAL wheel, all 18 projection/CLI tests pass. Ruff and compilation pass. Reprojecting an unchanged baseline native package yields byte-identical contents for all 27 B files and its receipt. The [installed consumer check](CONSUMER-AND-COMPATIBILITY.json) also validates actual successor emission with canonical B and CAL, and both refuse a tampered copy. These numbers describe their recorded environment, not a full dependency/platform release gate.

The new [qualification workflow](../../.github/workflows/eb-v1-output-containment.yml) checks the actual event head, unchanged authorities, maintained Python 3.11/3.12 gates, full dependency installation, an isolated installed wheel outside checkout, the original probe, and canonical B1.2 plus actual CAL intake. It does not weaken or inherit the predecessor's frozen-source qualification. Exact-head run links and terminal results belong in the corrective PR.

For a local probe replay, use the Python interpreter beside the installed candidate CLI and a fresh directory:

```bash
/absolute/candidate-venv/bin/python \
  research/eb_v1_output_containment_20261004/02-path-containment-probe.py \
  /absolute/fresh-probe-output
```

The script reports observations rather than asserting success. Require all four exit codes to be nonzero, `sentinel_overwritten=false`, `native_written=false`, and `receipt_written=false`. The qualification helper additionally verifies the probe hash and unchanged sentinel bytes.

The correction establishes a bounded output property. It does not resolve #121's real retained-context failure, establish representative retrieval usefulness, provide automatic semantic review, or authorize release. Those obligations remain explicit in #132.
