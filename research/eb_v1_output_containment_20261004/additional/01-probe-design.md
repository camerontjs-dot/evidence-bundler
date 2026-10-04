# EB V1 additional path-boundary probe design

This is an engineering regression design for the installed EB V1 Slice 1
candidate, not a scientific retrieval evaluation or a release decision.

## Frozen baseline and authority

- Baseline source: Evidence Bundler
  `08ca896debd6d16fa21be2f178ed7cbe62395d00`.
- Baseline package: installed wheel version `0.2.0`; exact source payload,
  wheel digest, runtime, and dependency identities are recorded before execution.
- Contract A: released `2.0.0` at
  `529c92b49a34d5c610618551a8737f019f9fa332`, exact validation-engine blob
  `42e5f5b3bf38d677445e9d01ea130ba604e53409`.
- Contract B: `1.2.0`, lock
  `c314e53bd91c0736aa4370a364673b069aceb43e`.

All synthetic inputs must pass the exact canonical A2 engine before the product
is invoked. A projection refusal must not be reported as an A2 schema rejection.

## Scope and independence

The probe author inspected the frozen contracts, writer, loader, and original
failure receipts. The author did not inspect the correction worktree or its
implementation. Expectations come from the literal Contract B layout and the
stated output-safety properties. Separate agents have shared task context and a
model family; this is implementation separation, not a broad clean-room claim.

No models, semantic judgments, scientific corpora, network retrieval, GitHub
mutations, or release operations occur. The original four-case probe and its
results remain unchanged. These cases are synthetic filesystem controls.

## Required output properties

1. Refuse an unrepresentable projected component before publishing any native
   package, Contract B file, or projection receipt. Preserve an existing empty
   destination, existing links, link targets, and absent target paths.
2. Preserve accepted IDs literally in native input, generated filenames,
   source directories, canonical YAML records, and extension references.
3. Claim and source namespaces are disjoint; matching IDs across roles are legal.
4. Validate actual output names. A claim ID `.` produces `..yaml`, and `..`
   produces `...yaml`; those are ordinary filenames. Source IDs `.` and `..`
   occupy directory components directly and are unrepresentable in B's layout.
5. Sources that have no nominated candidate receive no B source directory.
   Their IDs remain opaque JSON data. All nominated sources, including those
   occurring only at rank 4 / non-retained, receive B records in the frozen writer.
6. Existing empty real directories remain supported by the direct projection
   API. Empty or dangling symlinks must not act as permission to redirect output.

## Portable alias policy and host limits

The alias cases separately evaluate a declared conservative projection policy:
distinct sibling IDs that collide under case or canonical Unicode equivalence
must refuse before publication. The probe also records whether this host actually
aliases each tested name pair, and whether successful output preserves both
literal identities. Successful distinct-name output on a case-sensitive Linux
filesystem is not evidence of an observed macOS overwrite. It can pass host-local
identity/containment while failing the separately labeled portable-refusal policy.

These observations do not establish exhaustive APFS or HFS+ compatibility.
Python Unicode folding differs from filesystem comparison tables; HFS+ can
change stored normalization even for a single name. The probe does not simulate
macOS and does not present normalization-key checks as an exact filesystem model.

## Preregistered cases

| Case | Entry | Required behavior |
|---|---|---|
| declared_root_traversal | CLI | Refuse before output; preserve owned root sentinel |
| declared_later_child_traversal | CLI | Refuse before output; preserve owned child sentinel |
| claim_case_alias | CLI | Portable sibling-alias refusal, claims only |
| claim_nfc_alias | CLI | Portable sibling-alias refusal, claims only |
| source_case_alias | CLI | Portable sibling-alias refusal, sources only |
| source_nfc_alias | CLI | Portable sibling-alias refusal, sources only |
| safe_unicode | CLI | Succeed with exact non-ASCII IDs |
| safe_ordinary_colons | CLI | Succeed with literal multi-character colon prefixes |
| safe_percent_literals | CLI | Succeed without percent decoding |
| same_id_across_roles | CLI | Succeed without a global-namespace collision |
| claim_dot | CLI | Succeed with the literal `..yaml` filename |
| claim_dotdot | CLI | Succeed with the literal `...yaml` filename |
| source_dot | CLI | Refuse before output |
| source_dotdot | CLI | Refuse before output |
| unprojected_path_source | CLI | Succeed; unused path-like ID remains JSON data |
| unsafe_nonretained_source | CLI | Refuse before output; preserve owned source sentinel |
| direct_empty_bundle_symlink | Direct API | Refuse before output; owned empty sibling stays empty |
| direct_broken_receipt_symlink | Direct API | Refuse before output; absent owned receipt stays absent |
| direct_existing_receipt_symlink | Direct API | Refuse before output; preserve owned receipt sentinel |
| direct_empty_bundle_directory | Direct API | Succeed using the supported empty real directory |
| direct_empty_output_directory | Direct API | Succeed using the supported empty real directory |

## Safety and observation procedure

The script creates a new exclusive run directory beneath the directory holding
the frozen design. It checks the supplied leaf before resolving it, including
dangling links. Every case has its own output
directory and owned sibling target area. Traversal strings resolve only to that
case's owned sibling area. Before invocation, the script checks each anticipated
dangerous target is inside the run root. It never points a probe at repository,
user, or system files. No existing run directory can be reused or overwritten.

Snapshots use `lstat` and do not follow symlinks. They record relative names,
entry kinds, symlink text, and file hashes; access-time equality is not required.
The complete output tree and owned sibling tree are compared before and after.
CLI invocations execute the installed console script from an unrelated case
directory. Direct calls execute in a fresh subprocess through this same script.
Both run with user-site and model/network download paths disabled.

Refusal attribution requires a recognizable projection error. The direct API
worker records the actual exception class. The real CLI exposes Click's error
message instead; the runner records that limitation and requires path/output
wording, rather than accepting an arbitrary nonzero exit. Raw process evidence
is saved before output inspection. Timeouts and launch failures retain their
partial evidence and stop the run.

The script and this design are hashed into `02-design-freeze.json` before the
first case execution. The runner refuses a mismatched script, design, case list,
or canonical validator. It verifies installed Python source files and packaged
carrier match the supplied checkout, writes raw stdout/stderr and case records, and retains every
failed outcome. A later corrected candidate can replay the identical frozen
script/design in a new run directory with its own supplied checkout and label.

## Interpretation and stop rule

The decisive security property is no unrequested output mutation. A nonzero exit
code after overwriting an owned sibling or publishing partial output fails that
property. Portable-alias policy failures are reported separately from observed
host containment failures. Positive controls must preserve exact identities.

Stop if an anticipated target falls outside the newly owned run tree, installed
source does not match the specified checkout, a synthetic object fails exact A2
validation, or a harness error prevents reliable observation. Do not repair or
rerun a consequential product failure under the same run directory. Apparatus
corrections, if needed, require a new script/design freeze and retained failed run.
