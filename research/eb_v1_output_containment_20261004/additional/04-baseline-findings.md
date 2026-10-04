# Frozen EB 0.2.0 additional path-boundary results

## Finding

The unchanged installed candidate at
`08ca896debd6d16fa21be2f178ed7cbe62395d00` failed seven additional output-safety
cases: five mutated probe-owned paths outside the requested output directory,
and two published partial output for unrepresentable source-directory IDs.
Two of the outside-output cases returned success through the direct projection
API. These results corroborate the original four-case witness without modifying
its script or evidence.

All nine positive compatibility controls passed, and the existing-receipt
refusal control passed. Four additional case/Unicode alias cases failed the
separately declared portable-refusal policy, while preserving distinct IDs and
remaining contained on this host's case-sensitive, normalization-sensitive
filesystem. Those four cases are not observed macOS overwrite witnesses.

The frozen score is **21 cases: 10 pass, 11 fail**, comprising seven observed
output-safety failures and four separately labeled portable-policy failures.

## Exact subject and execution

| Item | Identity |
|---|---|
| Baseline commit | `08ca896debd6d16fa21be2f178ed7cbe62395d00` |
| Baseline tree | `1248dc464c8ac06aa6a5554b9092d1f793a8b2c2` |
| Installed package | `evidence-bundler==0.2.0` |
| Wheel SHA-256 | `76b64db4753594dd62f0c7788507c6c3bf792b27eac63dae08e092bd801f7237` |
| Runtime | Python 3.12.14, Linux x86_64; complete distributions in `00-baseline-runtime.json` |
| Design frozen | 2026-10-04 13:09:24 UTC |
| Run completed | 2026-10-04 13:09:50 UTC |

Installed Python source files and the packaged compatibility carrier matched the
supplied detached checkout exactly. The installed distribution's wheel receipt
matched the preserved wheel bytes. All 21 inputs passed unchanged through the
exact canonical A2 validator blob `42e5f5b3bf38d677445e9d01ea130ba604e53409`
from release `529c92b49a34d5c610618551a8737f019f9fa332`.

No correction-worktree source was read. No model or semantic calls occurred.
Both the main checkout and frozen detached candidate remained clean afterward.

## Observed output effects

| Cases | Exit | Observation |
|---|---:|---|
| Declared malicious root and later child | 1 | Owned claim sentinels outside output overwritten; native package and partial B output already present |
| Unsafe source nominated at rank 4 | 1 | Owned source profile overwritten and an outside passage created; candidate was `not_retained` / `not_applicable` |
| Direct API: empty `contract_b` symlink | 0 | Full B tree written into the owned sibling referent; receipt returned successfully |
| Direct API: broken receipt symlink | 0 | Previously absent owned sibling receipt file created through the dangling link |
| Source IDs `.` and `..` | 1 | Native package and partial B output published before later failure; no outside-output mutation observed |
| Existing receipt symlink | 1 | Recognizable projection refusal; output/link/target snapshots unchanged |

The rank-4 condition was confirmed from the emitted native package: the unsafe
source had `nomination_rank=4`, `selection_state=not_retained`, and
`admission_state=not_applicable`. Its emitted B files establish why checking only
retained or admitted sources would miss this output path.

The snapshots distinguish a preexisting link from a newly published receipt.
For example, `receipt_is_file=true` in the existing-receipt refusal case reflects
the preexisting link's referent; the before/after diff is empty and no receipt was
published by that invocation.

## Compatibility controls

The following all succeeded, preserved literal IDs in native input, filenames,
directory names, YAML records and extension references, and left owned outside
trees unchanged:

- non-ASCII claim/source IDs (`主張-δ`, `資料-λ`);
- ordinary colon-bearing IDs (`claim:root`, `source:item`);
- percent-encoded-looking strings treated literally;
- the identical string `shared-id` reused across claim and source roles;
- claim IDs `.` and `..`, producing `..yaml` and `...yaml`;
- an unused path-like source ID that remains JSON data and produces no B source directory;
- direct projection into an existing empty real B directory;
- direct projection into an existing empty real output directory.

These are compatibility witnesses for actual generated components. Rejecting
them would require an explicit broader producer restriction; it is not necessary
to correct the observed path escape.

## Alias observations and limits

The two sibling pairs `Alpha`/`alpha` and `café`/`cafe\u0301` were independently
created with exclusive creation in a probe-owned directory. Both pairs remained
distinct on this Linux filesystem. The four claim/source alias product cases
likewise returned success and preserved all exact IDs. They pass the recorded
host-local identity/containment property while failing the separately declared
portable-refusal policy.

No macOS filesystem was exercised. A Python normalization/casefold key is not an
exact APFS or HFS+ equivalence implementation. These observations do not establish
normalization preservation, name-length acceptance, or alias safety on HFS+.
Concurrent directory/symlink replacement was also outside this bounded test.

## Frozen files and verification

| File | SHA-256 |
|---|---|
| `03-additional-path-probes.py` | `5d9543552d2ca024a7106e4fec382605339ca4b20ae4ee74241bef07b4942b1f` |
| `01-probe-design.md` | `afd94fd03178294f9d2e1bdffe1d8ec5bdd4e080f1196f5abb2bb7cf50ec7e3f` |
| `02-design-freeze.json` | `33963eaab4a97555b0c7aef5705e2c57f24afdd4052d7b0e165c45db03928f02` |
| `00-baseline-runtime.json` | `86285419d26fb5bb1ef808bbff3d4035c1862c5487d8ac389d50fc76a9703adc` |
| `baseline-08ca896/results.json` | `9f2d71ef6c3b75b8e5a946aa52548c67062a8d8289f666883ef5b5895eee4adf` |
| `baseline-08ca896/summary.json` | `5b5793f06494b7d89d90255d91b927944a845cf1bd5537c2beafe381de615838` |
| `baseline-08ca896/file-manifest.json` | `31f03217117fe20806352d03b70d38f9fdd99992a8a7ec9d5b1d15e9b72545e3` |

Each case retains input, stdout, stderr, process identity, complete output and
owned-target snapshots, and its evaluation record. The run manifest records file
hashes and symlink text without following links; it excludes its own file.

The original four-case script remains SHA-256
`70f18e7c57e3ac6b0e90b358c621a8dd0be44f6fb1ccf69a19d3d6df3eaee52a`;
its original results remain SHA-256
`cc8f78ab9c84ecd47c43fa4934ceaf9d2ec2436f6345a5487ea1a419c0b6cd1a`.

## Replaying a correction

Use the corrected wheel in a separate virtual environment. Keep the script and
design freeze unchanged. Invoke `03-additional-path-probes.py run` with:

- `--freeze`: this `02-design-freeze.json`;
- `--run-dir`: a new descendant of this review directory, never the baseline directory;
- `--sut-repo`: the exact corrected checkout whose code is installed;
- `--contracts-root`: the existing exact-authority apparatus-contracts clone;
- `--label`: an explicit corrected-candidate label.

The script records the new subject and refuses any installed-source mismatch.
Its exit status indicates completion of the harness, not that the tested product
passed. Evaluate `summary.json` and the case-level fields. Preserve any correction
failures under their own run identity; do not overwrite or reinterpret this baseline.
