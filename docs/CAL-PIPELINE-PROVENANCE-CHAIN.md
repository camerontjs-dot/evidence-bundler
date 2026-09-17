# CAL Pipeline Provenance Chain

**Status:** cross-repo architecture pointer / local obligation record. No retrieval behavior, Contract B schema, CAL semantics, Decision behavior, Authorization, release, or production default is changed by this document.

## Canonical blueprint

The canonical proposed architecture is maintained in `camerontjs-dot/apparatus-contracts` Draft PR #101:

- `docs/architecture/CAL-PIPELINE-PROVENANCE-CHAIN-BLUEPRINT.md`
- canonical proposal head at this pointer's creation: `d16e5e14cab55ed23bdeee4cdeecf48724c542db`

Apparatus Contracts owns the cross-pipeline blueprint. Evidence Bundler owns its native retrieval/admission record, Contract B production, and conformance to any later-qualified provenance schema.

## Local requirement

Evidence Bundler is the natural origin of the Contract-B provenance commitment. A later qualified EB attestation should make it possible for an independent downstream consumer to reconstruct exactly which upstream claim/source world and exact EB machinery produced one exact Contract B bundle.

### EB must eventually attest

- exact Contract A digest as `causal_input`;
- exact EvidenceGate digest as `observed_context` unless specific fields have separately qualified causal use;
- exact EB implementation identity;
- exact retrieval/runtime profile identity;
- exact behaviorally relevant configuration digest with defaults materialized;
- exact native EB package identity/digest;
- exact query/retrieval/aperture identity represented by the native package;
- exact candidate/selection/admission history identity;
- exact compatibility carrier digest as `compatibility_input` when one is required to construct locked Contract B;
- exact Contract B compatibility/version, bundle ID, and whole-bundle hash;
- exact Contract B tree / `SHA256SUMS` verification result;
- terminal retrieval/admission execution state;
- durable locators for every native or Contract-B artifact required for later reconstruction.

## Contract-B commitment rule

The whole-bundle hash is expected to act as the producer-originated commitment to the exact Contract-B evidence world. Downstream verification must compare presented B bytes against an independently trusted expected commitment. The artifact path/location is a retrieval mechanism, not by itself the trust root.

## Compatibility-carrier rule

Any B-only compatibility state must remain visibly separate from Contract-A authority, native EB retrieval/admission state, and CAL semantic authority. Provenance should show exactly where each material field originated rather than allowing the final B artifact to erase that distinction.

## Audit preservation

The native V1 package remains the system of record for retrieval identity, aperture, candidate history, nomination rank, selection, admission, source/passage identities/hashes, configuration and package identity. A Contract B projection must not destroy that reconstructability.

## Nonclaims

This pointer does not qualify a production attestation schema, change the current integration profile, establish retrieval completeness/recall, change Contract B, or authorize promotion of the current V1 retrieval candidate.
