# Release and Version Governance

**Purpose:** Define when CAL Pipeline components receive versions, what those versions mean, and what evidence is required before a version becomes an official release.

This is a durable convention. Current component versions, release candidates, and release status belong in GitHub.

## 1. Version each public artifact independently

Do not assign one version number to the entire CAL Pipeline unless a future integrated distribution genuinely has one public compatibility surface.

Current version streams may include:

- Claim Audit Lab application/package;
- Evidence Bundler application/package;
- Apparatus Contract B;
- Apparatus Contract C;
- Decision Engine application/package;
- any future separately consumable SDK/API.

A CAL release does not automatically imply a Contract-B release. A Contract-B release does not automatically imply a Decision Engine release.

Cross-component compatibility should be recorded explicitly through conformance evidence and, if needed later, a compatibility manifest/BOM rather than synchronized version numbers.

## 2. Semantic Versioning basis

Use Semantic Versioning `MAJOR.MINOR.PATCH`.

For normal versions after `1.0.0`:

- **MAJOR**: backward-incompatible public API, contract, CLI, artifact, or semantic behavior change.
- **MINOR**: backward-compatible public capability or interface addition.
- **PATCH**: backward-compatible correction that does not intentionally expand or break the public interface.

A version number is a compatibility claim, not a measure of effort or importance.

A huge internal refactor may be PATCH if externally observable behavior is intentionally unchanged and verified. A one-line schema change may be MAJOR if it breaks consumers.

## 3. Strict pre-1.0 policy

Semantic Versioning permits instability during `0.y.z`. This project uses a stricter convention so pre-1.0 numbers remain informative.

### `0.Y.0` — development capability / semantic release

Increment the MINOR number when a release intentionally changes any consequential public behavior, including:

- public CLI/API behavior;
- audit/verdict semantics;
- schema/contract surface;
- output artifact meaning or shape;
- new public capability;
- removed capability;
- backward-incompatible behavior;
- a material model/rules/policy change that can change legitimate outputs.

Examples:

- `0.4.0 -> 0.5.0`: new audit-result semantics, new public workflow, new contract consumption behavior.
- `0.5.0 -> 0.6.0`: breaking CLI/schema change while CAL remains pre-1.0.

Before 1.0, do **not** use the first digit as a routine breaking-change counter. `0.Y.0` is the development-series release boundary.

### `0.Y.Z` — bounded corrective release

Increment PATCH only when the change is compatible with the current `0.Y` public/semantic surface and does not intentionally add a new public capability.

Suitable examples:

- packaging correction;
- documentation correction tied to the same behavior;
- backward-compatible defect fix whose expected semantics were already specified;
- security/reliability correction that preserves the advertised interface;
- release metadata correction requiring new immutable artifacts.

If a “bug fix” changes what CAL legitimately concludes for a class of claims because the prior semantics were under-specified, prefer a MINOR bump. The version should communicate semantic change, not excuse it as implementation repair.

## 4. When CAL becomes 1.0.0

`1.0.0` does **not** mean perfect, finished, universally accurate, or feature-complete.

Release `1.0.0` when the project is prepared to make and maintain a stable public compatibility promise.

For CAL, the 1.0 gate should require evidence that:

1. the intended public API/CLI/artifact surfaces are explicitly declared;
2. core audit-result semantics are named and stable enough to support downstream consumers;
3. Contract-B consumption is canonical and conformance-tested if Contract B is part of the supported public workflow;
4. output/provenance behavior required for reconstruction is stable;
5. missing/unknown/not-checkable behavior is part of the declared contract rather than incidental implementation behavior;
6. release packaging has reproducible acceptance tests;
7. known evaluator limitations are documented and do not contradict the claims made by the release;
8. backward-compatibility obligations are understood well enough that future breaking changes will intentionally require `2.0.0`;
9. there is at least one realistic supported use path that the project is willing to call production-capable within stated bounds.

A high benchmark score is neither necessary nor sufficient for 1.0. The decisive property is a defensible stable public contract.

## 5. Post-1.0 rules

After `1.0.0`, follow standard Semantic Versioning strictly.

### MAJOR

Increment for any backward-incompatible change to a declared public surface.

Examples:

- remove/rename required API or CLI behavior;
- require a previously optional contract field;
- reinterpret a public field incompatibly;
- change artifact semantics such that existing legitimate consumers can no longer rely on prior meaning;
- remove a supported workflow.

### MINOR

Increment for backward-compatible public functionality.

Examples:

- new optional API;
- new output field that old consumers can ignore safely;
- new CLI feature;
- new supported audit capability preserving existing behavior;
- deprecation of public functionality.

### PATCH

Increment for backward-compatible fixes only.

Examples:

- correct implementation to match already-declared behavior;
- packaging/security/reliability fix with no compatibility expansion;
- documentation correction accompanying unchanged public behavior.

## 6. Semantic compatibility outranks syntactic compatibility

A parser accepting an artifact does not prove compatibility.

Version classification must consider:

- syntax/shape compatibility;
- semantic meaning;
- legitimate consumer behavior;
- failure/unknown behavior;
- provenance and identity behavior;
- downstream decision effects where the interface promises them.

A syntactically optional field may still require a breaking version if its presence changes the meaning of existing state for legitimate consumers.

For contract changes, determine version class from producer -> contract -> consumer conformance evidence rather than preference.

## 7. Research versions are not release versions

Do not bump official versions merely because a research branch or experiment exists.

Research artifacts may use identifiers such as:

- `rc0`;
- experiment IDs;
- branch names;
- fixture versions;
- candidate profile names.

An official version is assigned only when a bounded change is being promoted.

This prevents unused version numbers from becoming accidental claims.

## 8. Pre-release versions

Use Semantic Versioning pre-release identifiers only when an artifact is genuinely approaching a specific release:

- `0.5.0-alpha.1` — early externally testable candidate;
- `0.5.0-beta.1` — feature/semantic shape mostly established, broader validation ongoing;
- `0.5.0-rc.1` — intended release content is frozen except release-blocking fixes;
- `1.0.0-rc.1` — candidate for the exact 1.0 compatibility promise.

Do not call ordinary research branches release candidates.

If an RC changes materially, issue `rc.2`; do not move or rewrite `rc.1`.

## 9. One version identifies one immutable tree

Once a version is released:

- do not move its tag;
- do not rewrite the released artifact;
- do not reuse the version number;
- corrections require a new version.

Use:

- package/version metadata: `0.5.0`;
- Git tag: `v0.5.0`.

Prefer an immutable annotated Git tag pointing to the exact release commit.

This is a costly signal: a published version permanently binds the project's claim to inspectable code and evidence.

## 10. What counts as an official release

A normal release is official only when all required release artifacts agree on the same version and commit.

Minimum release identity:

1. version declared in package/schema metadata;
2. changelog entry;
3. immutable Git tag;
4. exact release commit;
5. required CI/release acceptance evidence.

For public repositories, also create a GitHub Release object from the immutable tag unless there is a documented reason not to. The GitHub Release should summarize:

- what changed;
- compatibility classification;
- known limitations/non-claims;
- evidence or promotion lineage;
- install/use notes where relevant.

If a distributable package is later published to PyPI or another registry, that publication is an additional release artifact and must correspond to the same versioned source tree.

## 11. Release PR

Normal releases should use a dedicated release/promotion PR when the repository has meaningful production behavior.

The PR should contain or verify:

- exact proposed version;
- why that version class is justified;
- evidence/EDR supporting consequential semantic changes;
- changelog;
- version metadata;
- compatibility/migration notes;
- known limitations;
- release acceptance checks;
- rollback/recovery posture where applicable.

The version number should be derived from the change/evidence, not chosen first and rationalized afterward.

## 12. Release gates

The exact gate varies by component, but a public release should normally require:

### Common

- clean production CI;
- leak/secret/private-path checks;
- changelog updated;
- version metadata consistent;
- build/package reproducibility checks where applicable;
- installation/smoke test from the built artifact rather than only the source tree;
- no unresolved release-blocking deviations;
- known defects that remain open stated honestly.

### CAL / applications

Also consider:

- frozen regression suite;
- representative end-to-end acceptance fixture;
- evaluator/model/config identity where behavior depends on them;
- deterministic rerun check where determinism is claimed;
- public artifact/report sanity check.

### Apparatus contracts

Also require:

- schema/spec/validator agreement;
- producer conformance;
- consumer conformance;
- compatibility matrix;
- missing-state/fail-closed controls;
- version classification from observed behavior;
- migration/adapter notes if needed.

## 13. Release decision and EDR

A routine PATCH release does not require a new EDR unless it changes a material architectural or assurance decision.

Create/link an EDR when a release:

- promotes a researched contract or architecture;
- establishes a new compatibility promise;
- crosses `1.0.0`;
- makes a consequential semantic change;
- establishes or removes a major assurance gate.

The EDR answers **why this is now justified**. The release record answers **what exact artifact was published**.

## 14. Release channels

Use these concepts distinctly:

- **Research:** evidence-generation surface; not a release.
- **Pre-release:** named candidate for a specific upcoming release.
- **Normal release:** supported version under its stated compatibility/quality bounds.
- **Deprecated release:** still identifiable but no longer recommended.
- **Yanked/withdrawn release:** serious problem; preserve the record and publish the reason. Never erase history to make the release disappear.

## 15. Pipeline compatibility

Because CAL Pipeline components can evolve independently, maintain compatibility explicitly.

Eventually, if integration complexity warrants it, add a machine-readable compatibility manifest, for example:

```yaml
cal: 1.2.0
contract_b: 1.3.0
contract_c: 1.0.0
decision_engine: 0.8.0
evidence_bundler: 0.9.0
validated_by:
  conformance_run: ...
```

Do not add this until independent component versions create a real coordination problem.

## 16. Release-status source of truth

Current version/release status belongs in GitHub, not in static project attachments.

For each component, GitHub should make it possible to determine:

- latest normal release;
- latest pre-release, if any;
- exact tag and commit;
- release date;
- compatibility class;
- current supported/deprecated status;
- linked EDR/promotion evidence for consequential releases.

## Decision rule summary

### Before 1.0

- same public/semantic capability, compatible correction -> `0.Y.(Z+1)`
- new or materially changed public/semantic capability, including breaking development change -> `0.(Y+1).0`
- stable compatibility promise is now justified -> `1.0.0`

### After 1.0

- compatible fix -> PATCH
- compatible capability -> MINOR
- incompatible public change -> MAJOR

When uncertain, ask what legitimate existing consumers would observe. If that question has not been tested and the distinction matters, run the compatibility experiment before assigning the version.
