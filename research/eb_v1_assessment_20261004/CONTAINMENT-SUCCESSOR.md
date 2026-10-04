# Corrective EB V1 path-boundary replay

**All 21 unchanged probes passed** on corrective commit `0f5e7d9df2d4fe223b737bea27281c90cdfe0ebb`
(PR #133), using the separately installed `0.2.1.dev0` wheel.
All twelve refusal cases left output and owned target trees unchanged.
All nine acceptance controls succeeded and preserved exact IDs.

## Tested identity

| Item | Value |
|---|---|
| Commit | `0f5e7d9df2d4fe223b737bea27281c90cdfe0ebb` |
| Tree | `ffaa4e14b14f1863bdc482453e9830d3bc1b0273` |
| Wheel SHA-256 | `63a1d6a3c89f2fb4daef6825773c024f6dc0f392a889e07d0adf3779f6b90a14` |
| Script SHA-256 | `5d9543552d2ca024a7106e4fec382605339ca4b20ae4ee74241bef07b4942b1f` |
| Design SHA-256 | `afd94fd03178294f9d2e1bdffe1d8ec5bdd4e080f1196f5abb2bb7cf50ec7e3f` |
| Completion | 2026-10-04T13:19:10.072554+00:00 |

The installed Python source and packaged carrier matched the clean corrective
checkout. The preserved wheel bytes matched the installed wheel receipt.
All 21 synthetic inputs passed the exact canonical A2 engine unchanged.
The original script, design, baseline results, and original four-case probe
were not modified.

## Complete case matrix

| Case | Entry | Baseline | Correction | Corrective output effect |
|---|---|---|---|---|
| `declared_root_traversal` | cli | FAIL | PASS | Refused; zero mutation |
| `declared_later_child_traversal` | cli | FAIL | PASS | Refused; zero mutation |
| `claim_case_alias` | cli | POLICY FAIL | PASS | Refused; zero mutation |
| `claim_nfc_alias` | cli | POLICY FAIL | PASS | Refused; zero mutation |
| `source_case_alias` | cli | POLICY FAIL | PASS | Refused; zero mutation |
| `source_nfc_alias` | cli | POLICY FAIL | PASS | Refused; zero mutation |
| `safe_unicode` | cli | PASS | PASS | Literal output preserved |
| `safe_ordinary_colons` | cli | PASS | PASS | Literal output preserved |
| `safe_percent_literals` | cli | PASS | PASS | Literal output preserved |
| `same_id_across_roles` | cli | PASS | PASS | Literal output preserved |
| `claim_dot` | cli | PASS | PASS | Literal output preserved |
| `claim_dotdot` | cli | PASS | PASS | Literal output preserved |
| `source_dot` | cli | FAIL | PASS | Refused; zero mutation |
| `source_dotdot` | cli | FAIL | PASS | Refused; zero mutation |
| `unprojected_path_source` | cli | PASS | PASS | Literal output preserved |
| `unsafe_nonretained_source` | cli | FAIL | PASS | Refused; zero mutation |
| `direct_empty_bundle_symlink` | api | FAIL | PASS | Refused; zero mutation |
| `direct_broken_receipt_symlink` | api | FAIL | PASS | Refused; zero mutation |
| `direct_existing_receipt_symlink` | api | PASS | PASS | Refused; zero mutation |
| `direct_empty_bundle_directory` | api | PASS | PASS | Literal output preserved |
| `direct_empty_output_directory` | api | PASS | PASS | Literal output preserved |

The predecessor had five outside-output mutations and two additional
partial-output failures. The corrected run reproduced none of them.
The earlier case/Unicode pairs stayed distinct on Linux and passed local
identity/containment; their four predecessor failures concerned the explicitly
declared portable-refusal policy. They were not observed macOS overwrite cases.

## Compatibility and scope

The positive controls preserved non-ASCII IDs, ordinary colon-bearing IDs,
literal percent strings, the same ID across claim/source roles, dot-valued
claim filenames, and unused path-like sources carried only as JSON.
Both supported empty real-directory direct-API controls also remained usable.

This supports the bounded output-publication correction at the exact installed
candidate. It does not establish retrieval usefulness, a general security review,
exhaustive APFS/HFS+ compatibility, resistance to concurrent link swaps,
or release readiness. No models or semantic calls were made. Probe implementation
was separated from corrective implementation; task context and model family were
shared. The earlier failures remain preserved.

## Evidence bindings

- Full public matrix: [CONTAINMENT-SUCCESSOR.json](CONTAINMENT-SUCCESSOR.json).
- Raw successor results SHA-256: `5c811844a5ff3eedaaa591b5bb596896978d640b72388b48719d61701e332335`.
- Successor run manifest SHA-256: `3996f0436f4dfd0fb50bdff00adaafe94df605f7ff6389be163469aaf27ac0fe`.
- Frozen design receipt SHA-256: `33963eaab4a97555b0c7aef5705e2c57f24afdd4052d7b0e165c45db03928f02`.

The raw case records retain exact input hashes, stdout/stderr, process metadata,
output snapshots, owned target snapshots, symlink state, and refusal attribution.
The public summary removes local absolute paths while retaining source and
artifact identity bindings.
