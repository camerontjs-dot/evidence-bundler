# RC1A Root/Child CAL-Facing Probe — Preregistration

Status: preregistered before RC1A raw retrieval or dev relevance analysis is observed.

## Purpose

Test whether proposition-specific retrieval lanes carry downstream CAL information that is lost when the same physical passage set is flattened, without inventing a root/child aggregation rule or production admission authority.

This probe is subordinate to Evidence Bundler issue #50. It is not a production Contract B build and does not modify CAL.

## Frozen upstream input

The only authorized retrieval input is the successfully frozen artifact, if produced, from:

- Evidence Bundler RC1A execution head: `6de9d37140bc16301c151a3ca1b148f13df4c3f5`
- workflow run: `33890894890`
- experiment: `decomposition-parent-child-complementarity-dev-rc1a`
- preregistration ancestor: `32434828264ec9613c7f3530ce4ec39f3d5bd1f4`

The probe must consume the exact RC1A `contract-a-fixtures/MANIFEST.json`, fixture files, `raw-retrieval.json`, and their recorded SHA-256 digests from that run. It must not rerun decomposition generation or retrieval.

If run `33890894890` does not freeze raw retrieval successfully, this probe does not execute.

## Frozen downstream consumer authority

- Claim Audit Lab: `camerontjs-dot/claim-audit-lab@32275a239b68af383a56bca843e28cbc1e343976`
- CAL tree: `bd5c6dd6d352f11282899e0b8c07c4f223504c2e`
- CAL Contract-B models blob: `a153787302824d76d67326f17a881899078cb6d6`
- CAL Contract-B adapter blob: `7fde574c4ea9af71b4e2abc8efed61e20bd55e92`
- CAL factual-context consumer blob: `32a4f80ac32cd340d5470abb333a8a1dd98110dd`
- Apparatus Contracts authority: `c3563cff66d2c85dcbf575c693056e2d8e4563d4`
- Contract B factual-context v1.2.0 spec blob: `77645a6adac664892866f3fdf8abf66cd1d0dd10`
- Contract B factual-context validator blob: `f5ad1a0db70d2f36d06c04ab0c9c2050f41bd8e7`

## Authority boundary discovered before the result

Contract B 1.2 can carry canonical claim identities, claim origin/lineage facts, passage identities, claim-specific nomination history, and aperture observations. Its semantic projection admits passages only after `history.review.decision == accepted` and deliberately excludes nomination metadata.

RC1A measures retrieval nominations; it does not perform evidence review/admission. Therefore this probe MUST NOT mark RC1A retrieval nominations as accepted merely to force them through the production Contract-B semantic projection.

The probe has two distinct parts:

1. **Representability check:** mechanically demonstrate that the exact Contract A root and declared children can be represented as distinct strict Contract-B 1.2 canonical claim identities with common factual lineage in the optional extension, while retrieval-lane relationships remain audit-visible nomination metadata. Use `needs-review` for nomination history if a shadow extension is materialized. This part makes no semantic measurement claim.
2. **Research-only direct CAL measurement:** audit frozen RC1A retrieval-nominated passage sets through CAL's explicit-claim API without calling them admitted Contract-B evidence. Results describe CAL behavior over supplied research evidence worlds only.

These two parts must not be collapsed.

## Scope

Primary retriever: semantic.

Budget regimes:
- `equal_total` primary architecture comparison;
- `equal_per_query` secondary capacity comparison.

All six frozen RC1A cases are eligible. All seven strategies are eligible when their Contract A decomposition state is `declared`. Failed/abstained decompositions remain absent from child-based probe arms and are reported, not repaired.

No sealed/test data and no RC1A dev relevance gold are required by this probe.

## Direct CAL measurement arms

For each case, declared strategy, retriever/budget pair:

### C0 — exact root / root-lane world

Audit the exact Contract A root proposition against only physical passages that R2 records with a `root_lane` relationship to the root proposition.

### C1 — exact children / child-specific worlds

Audit every exact declared Contract A child independently. Each child receives only passages that R2 records with a `child_lane` relationship to that exact child proposition ID.

A passage retrieved by multiple children may appear in multiple child-specific supplied evidence worlds; that multiplicity is provenance, not duplication of physical passage identity.

### C2 — distinct root + children with common lineage

Return C0 and all C1 assessments together as distinct proposition units plus factual common lineage:
- root proposition ID;
- decomposition ID;
- child proposition IDs and sequence;
- source RC1A fixture handoff SHA.

Do not compute a parent verdict from children and do not let the root assessment override child assessments.

### C3 — flattened anonymous-union control

For the same root and each child proposition, run CAL against the exact R3 physical passage union for that case/strategy/retriever/budget, with retrieval-lane attribution unavailable to evidence selection.

R3 must have the same physical passage IDs as R2. If not, fail the probe.

## CAL input rule

The probe calls CAL's explicit-claim audit surface with proposition text/identity from frozen Contract A. It constructs research evidence bundles from the selected frozen RC1A passage bytes. It does not provide caller-supplied support/refutation polarity.

No CAL source outside the pinned commit is modified. No CAL aggregation/composition helper is added.

## Measurements

Preserve per proposition and per arm:
- CAL support label;
- support score / match measurements exposed by the pinned CAL result;
- rule flags;
- selected/matched evidence identities where exposed;
- differences between typed lane-specific and flattened supplied evidence worlds.

Report disagreement patterns explicitly, including:
- root and one or more children differ;
- all children agree while root differs;
- flattened union changes a root result;
- flattened union changes a child result;
- typed lane-specific evidence prevents a change observed under flattening;
- no difference.

Do not aggregate child labels into a root label.

## Representability checks

For every probed declared treatment:
- strict Contract-B `CBClaim` accepts root and each child as separate canonical claims;
- inline undeclared `propositions` remain rejected by the strict model;
- a Contract-B 1.2 factual-context `claims[].origin` value can retain factual `{parent_claim_id, decomposition_id, proposition_role, sequence}` lineage without prohibited semantic keys;
- retrieval nominations can retain `{proposition_id, proposition_role, retrieval_lane, rank, score}` inside audit-visible nomination history;
- `needs-review` nomination history does not enter CAL semantic context as admitted evidence.

These establish representational capacity only, not production authorization.

## Falsifiers / interpretations

- If C0/C1 and C3 are identical everywhere, the CAL probe does not establish downstream value from lane-specific evidence partitioning.
- If C3 changes proposition assessments despite identical physical passage availability, flattening has observable semantic-pollution/information-loss consequences under the pinned CAL consumer.
- If strict Contract B cannot represent root/child canonical claims plus common lineage without schema invention, stop and record that boundary.
- If direct CAL measurement requires caller-supplied support/refutation polarity, stop rather than invent it.
- If RC1A raw retrieval is unavailable or its digest cannot be verified, stop.

## Nonclaims

This probe does not establish proposition truth, root/child aggregation semantics, production admission policy, Contract C projection, retrieval completeness, or a production Contract-B schema change.

## Stop rule

Do not redesign CAL, Contract B, or RC1A retrieval. Do not use dev relevance gold to tune the probe. Preserve disagreements and null results. Produce a frozen receipt and return its observations to issue #50 synthesis only.
