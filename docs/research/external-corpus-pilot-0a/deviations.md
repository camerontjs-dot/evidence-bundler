# Pilot 0A deviations and execution limitations

## D-0A-01 — Independent adjudicator surface unavailable

**Observed:** the first Conduit project-list probe returned HTTP 429; a later retry returned HTTP 404.

**Effect:** two genuinely isolated adjudicators were not available. No scientific labels were generated from duplicated same-context reasoning.

**Validity impact:** promotion-critical independent-gold evidence is missing. This supports `INCONCLUSIVE`, not a fabricated independence claim.

## D-0A-02 — Pinned binary acquisition unavailable in this runtime

**Observed:** web metadata/revisions/checksums were accessible, but the local execution environment could not resolve Hugging Face binary-host DNS and the SciFact archive was not materialized.

**Effect:** selected query/claim/source bytes, normalized bytes, passage bytes, correspondence offsets, and content hashes were not created.

**Validity impact:** the core passage-mapping and gold-stability experiment was not executed.

## D-0A-03 — FreshStack official provenance field loss

**Observed:** FreshStack construction code writes `metadata.commit_id`; the historical `nthakur/corpus-oct-2024` viewer exposes it; the current official `freshstack/corpus-oct-2024` schema exposes URL/start/end but not commit ID.

**Effect:** official current corpus rows do not alone identify the frozen Git source commit.

**Validity impact:** reconstruction remains incomplete until an external deterministic provenance-restoration join is byte-verified or another authoritative frozen source identity is established.

## D-0A-04 — FreshStack query-specific source aperture unresolved

**Observed:** FreshStack generated nugget relevance over a document list produced during its retrieval-oriented benchmark construction. No qrel-independent query-to-document source mapping was established.

**Effect:** using those document lists would violate Pilot 0A's no-retrieval source-selection rule; whole-topic manual adjudication is not a bounded alternative.

**Validity impact:** FreshStack is not yet eligible for the core bounded adjudication lane.

## D-0A-05 — Initial P2 role mutation was non-discriminating

**Observed:** flipping the role of already-retrieved `p1` to counterevidence left counterevidence recall at 1.0 because both counterevidence passages were retrieved.

**Action:** preserved the failed control; changed the dummy-only stimulus to flip unretrieved `p2`, which changed recall from 1.0 to 0.5 in both implementations.

**Validity impact:** none on scientific evidence. This occurred only in dummy P2 infrastructure before scientific gold existed.
