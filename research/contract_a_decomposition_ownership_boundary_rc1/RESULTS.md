# Contract A Decomposition Ownership Boundary RC1 — Results

Status date: 2026-08-29 / 2026-08-30 UTC

Research disposition: **OWNERSHIP_BOUNDARY_IDENTIFIED**

Production disposition: **NO PROMOTION**

## OBSERVED — authority

- Evidence Bundler main at campaign start: `6011789957f3294f97bff260069cfb5bb1c5772f`
- Claim Audit Lab pin: `53f0885b111676794d1bd20e10b91aa58b07e9d4`
- fixed F10 A1 retrieval snapshot SHA256: `8dbedd537c024c4a624f21abd5fa11536ddfe558000f3a9366584c30c045e31c`
- exact decisive boundary implementation: `6f442224450b7607480226daea7736f833dd4ecd`
- exact decisive tree: `85fe05aec4ce9efe768582c6580d6262a096be31`
- workflow run: `33289470312`
- job: `99198428088`
- artifact: `9725515416`
- artifact digest: `sha256:739842f9fa6c0ece1e2059b00794e1893d7a52e05d5d9d70c30fd9c263621ce4`
- result SHA256: `52a9b34a1f9d4bc3ec5cb0d524050fb29820c552e436b0e06fce802ff84beb10`
- summary SHA256: `f0cceed47721f76c0e2e2517d6389793ffb8241b9d5fe567d78e3b61d0839be7`

No retrieval was rerun.

## OBSERVED — decisive validation

On exact head `6f442224...`:

- full EB deterministic suite: **224 passed, 5 skipped**;
- Ruff: **clean**;
- pinned CAL v1 consumer installed from exact SHA;
- ownership-boundary conformance: **PASS**;
- artifact hashing/upload: **PASS**.

Preserved pre-execution deviations included two import-order Ruff stops and a missing CAL v1 optional dependency (`spacy`). These occurred before the boundary assertions. The final workflow installed CAL's declared `[v1]` dependencies and changed no treatment or falsifier.

## OBSERVED — Contract A is currently too small

The current strict EB `ScaffoldClaim` model rejects ad-hoc:

- `parent_claim_id`;
- `decomposition_id`;
- `sequence`.

Observed:

`current_contract_a_rejects_lineage_fields = true`.

Therefore current Contract A does not yet provide the proposition-lineage semantics established as necessary by the preceding experiments.

## OBSERVED — CAL does not claim decomposition authority

CAL's current explicit-claim seam states that it does not decompose claim text; the caller supplies stable provenance-bound atoms.

Its `AtomProvenance.origin` authority vocabulary is:

- `source_contract`;
- `operator_declared`.

The boundary test attempted an `evidence_bundler_generated` semantic provenance origin.

Observed:

`cal_rejects_evidence_bundler_generated_provenance = true`.

This does not prove that CAL could never accept another governed producer in a future contract. It establishes that the current governed consumer does not assign semantic authority to EB-generated atoms.

## OBSERVED — upstream semantic declaration crosses into CAL losslessly

A minimal research shadow Contract-A packet was built from the frozen F10 A1 decomposition, containing:

- parent claim identity/text;
- decomposition identity;
- operator `all_of`;
- exact child claim identities/text;
- parent-child lineage;
- sequence;
- immutable child reference hashes.

It was adapted to CAL's existing `ExplicitClaimRequest` using `source_contract` provenance.

Observed:

`source_contract_packet_adapts_losslessly_to_cal = true`.

The adapter preserved:

- parent identity/text;
- child identities/text;
- `all_of` operator;
- source-contract reference identities/hashes.

No model inference was needed to establish the boundary.

## OBSERVED — EB cannot truthfully mint upstream semantic authority by itself

The boundary apparatus requires any child represented as `source_contract` provenance to be a member of the frozen upstream proposition packet.

An invented `eb-synthesized-child` was rejected.

Observed:

`source_contract_membership_rejects_eb_synthesized_child = true`.

This is a conformance firewall: EB may derive arbitrary retrieval queries internally, but an internal query cannot silently become a new authoritative semantic proposition.

## OBSERVED — EB can consume declared propositions without semantic reinterpretation

For each declared child, EB's retrieval execution identity used:

- the existing upstream child `claim_id`;
- the exact upstream child text;
- the retrieval method.

Observed:

`eb_query_execution_preserves_declared_child_text = true`.

Nothing in retrieval requires EB to rewrite or reinterpret the child proposition merely to search for evidence.

## INFERENCE — ownership boundary

The smallest architecture consistent with all observed evidence is:

### Contract A / upstream semantic boundary

Owns the **authoritative semantic declaration**:

- original parent proposition identity/text;
- whether decomposition is declared;
- decomposition artifact identity;
- child proposition identities/text;
- parent-child lineage;
- logical composition operator when declared;
- transformation/producer provenance and immutable identity.

The physical decomposition algorithm does not necessarily have to live in the component that serializes Contract A. An operator, model, or upstream decomposition service may produce candidate children. They become authoritative for the pipeline only when frozen into the Contract-A semantic object.

### Evidence Bundler

Owns **evidence construction**:

- retrieval/query planning;
- retrieval-family choice;
- derivative search queries;
- candidate budgets;
- chunking;
- fusion/reranking/counterevidence search;
- source/passage evidence construction;
- faithful attribution of evidence to the declared proposition identity.

EB may derive search queries from a child proposition, including contradiction/paraphrase/query-expansion forms. Those are retrieval artifacts, not new semantic propositions unless a separately governed upstream semantic transition creates them.

### Claim Audit Lab

Owns **semantic audit of declared propositions**:

- evidence interpretation/measurement;
- eligibility/semantic-validity/aperture machinery;
- child-level epistemic state;
- deterministic parent composition only where an explicit upstream operator is supplied and the composition rule is governed.

CAL does not need to infer decomposition to perform this role; its existing explicit-claim API already demonstrates the caller-declared shape.

## INFERENCE — why the boundary is now supported

The ownership conclusion is not based on code organization alone. It follows from the experiment chain:

1. **Retrieval sensitivity:** legitimate decomposition can materially change the retrieved evidence world and complete joint coverage.
2. **Attribution collision:** child identity held only in EB query/nomination metadata is lost before CAL semantic measurement.
3. **Consumer authority:** CAL already accepts caller/source-contract-declared atoms and does not claim decomposition generation.
4. **EB intake behavior:** EB starts from a verified, hash-sealed upstream claims registry and can retrieve directly for declared child text.
5. **Authority falsifier:** an EB-invented semantic child has no current truthful `source_contract` authority identity.
6. **Cross-repo conformance:** a minimal upstream proposition-lineage packet adapts losslessly into CAL while EB can remain a retrieval/evidence constructor.

Together these make the Contract-A boundary the smallest supported place for authoritative semantic decomposition identity.

## FALSIFIED

The following candidate boundaries are falsified or unsupported:

### Decomposition only inside EB retrieval metadata

Falsified by the `(6,6)` vs `(12,0)` CAL semantic-context collision.

### CAL owns decomposition generation

Unsupported by the current governed API and unnecessary for the observed consumer behavior. CAL consumes caller-declared atoms without decomposing.

### EB may silently promote an internal retrieval query to an authoritative child proposition

Falsified by the authority-membership conformance check for the current source-contract semantics.

## UNKNOWN / not yet authorized

The ownership boundary does **not** yet establish the final Contract-A wire schema.

Still open:

- exact schema/version name;
- optional vs required decomposition object;
- producer vocabulary;
- operator vocabulary beyond demonstrated `all_of`;
- whether decomposition is attached to the parent or stored as a sibling artifact;
- how Contract B should transport child proposition identity without treating retrieval metadata as semantics;
- how Contract C exposes parent/child outputs and composition;
- promotion/migration behavior for undecomposed existing Contract-A objects.

## Smallest justified successor

Design and independently test a **minimal Contract-A decomposition-lineage extension** with cross-repository conformance:

1. preserve current undecomposed objects byte/semantically where possible;
2. add only the lineage fields justified above;
3. make EB consume declared children without semantic mutation;
4. make EB carry proposition identity through the evidence bundle via a governed semantic field/seam, not nomination metadata;
5. make CAL consume the resulting child identities through its explicit-claim pathway;
6. prove an undeclared EB query cannot become a proposition;
7. test parent/child cardinality and Contract-C consequences separately before promotion.

No production contract change is authorized by RC1 itself.
