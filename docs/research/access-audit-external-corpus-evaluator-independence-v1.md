# Access-boundary audit

## Observed

- Final pre-reveal dummy handoff: `9123eec2ec0da48f61bd063f634f1e20b1fc5f68`.
- `revealed_dummy_gold.json` is absent at that ref; GitHub returns 404 for the exact path.
- The pre-reveal module directory exposes the public contract, manifest, run, commitment, canonicalizer, evaluators, and access policy only.
- Dummy hidden-gold commitment at that ref: `2d0e0d99d23295b91c838e01a4e1a6274e2a77af45cd52ab834ed78fd5b6131f`.
- After reveal, canonical hashing of the exact dummy gold returns the same commitment.
- Existing historical synthetic benchmark gold already present on main is unrelated to this dummy external-corpus handoff and was not opened or used.
- No scientific Pilot 0A qrels, relevance judgments, adjudicator outputs, or target retrieval outputs were inspected.
- No Evidence Bundler production retriever was run.

## Repository-separation finding

**Directory separation alone is rejected.** If hidden gold is committed anywhere in history reachable by the target execution identity, normal Git/GitHub operations can retrieve it even when runtime code does not import it.

The dummy protocol instead uses a pre-reveal commit that does not contain the new gold, followed by a later reveal commit. This is materially stronger than storing public and hidden artifacts in sibling directories.

## Principal-separation limitation

The rehearsal does not prove that two separately authorized principals were isolated. The same authenticated project owner/supervisory context could create both commits. The MainFrame/Conduit bridge was unavailable when a clean second agent was attempted.

The infrastructure therefore has an auditable object-separation mechanism, but clean scientific execution still requires a separate access principal/workspace whose normal credentials cannot reach construction-only gold before reveal.

## Scientific-pilot allow-list

Before a scientific target run, freeze an execution allow-list. At minimum it may read only the frozen public corpus/query/source/passage manifest, permitted reconstructable source material, evaluator contract/run schema, K/target configuration, and public hidden-gold commitment.

It must not be able to read hidden qrels/adjudicator records, construction notes, expected per-query results, gold-derived nonpublic labels/IDs, or any repository/ref/artifact store/cache/workflow artifact/issue attachment that contains those objects.

A normal allowed credential reaching one of those surfaces before reveal is a terminal isolation failure for that scientific run.
