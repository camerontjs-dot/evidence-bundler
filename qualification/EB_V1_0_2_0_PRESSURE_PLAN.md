# Evidence Bundler V1 0.2.0 pre-local pressure plan

**Subject under test:** `08ca896debd6d16fa21be2f178ed7cbe62395d00`  
**Frozen ref:** `freeze/eb-v1-slice-1-0.2.0-cli-20260919`  
**Purpose:** adversarial qualification before local CAL Pipeline use. This branch is a test harness only and must not redefine the frozen subject.

## Highest-weight assumptions

1. The installed wheel behaves like the source-qualified slice when executed outside the repository.
2. Version `0.2.0` propagates through native package and Contract B provenance, not only CLI display.
3. Fail-closed behavior survives the installed CLI wrapper for malformed Contract A, admission and compatibility-carrier inputs.
4. Repeated execution is artifact-byte deterministic and independent of input/output path location.
5. Contract B 1.2 and current CAL V1 reject materially malformed boundary state rather than silently normalizing it.

## Discriminating tests

- build a wheel from the exact frozen commit and install it non-editably;
- run `evidence-bundler-v1` from an unrelated working directory;
- exact `--version` and deterministic `inspect --json`;
- two-run artifact-byte replay and input-path relocation replay;
- verify native producer and Contract B evidence-builder provenance both say `0.2.0`;
- verify explicit admission changes only the addressed retained candidate;
- reject stale Contract A hashes, malformed admission JSON, wrong admission schema, admission targeting a non-retained candidate, malformed carrier JSON, and a carrier that attempts semantic authorization;
- refuse a non-empty output directory without touching its sentinel;
- verify a failed invocation leaves no partial artifacts;
- validate a clean emitted B1.2 bundle with canonical Apparatus and current CAL intake;
- mutate the extension shape and Contract version and require downstream rejection.

## Stop rule

Any unexpected success on a negative control, artifact-byte replay mismatch, wrong installed provenance/version, partial artifact leakage after a rejected run, or downstream acceptance of a malformed Contract B subject blocks the local-pipeline disposition until explained.

Harness trigger receipt: this commit exists only to execute the pressure workflow after the workflow file was present on the branch.
