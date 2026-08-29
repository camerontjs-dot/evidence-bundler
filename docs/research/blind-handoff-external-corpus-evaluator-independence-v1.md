# Dummy blind-handoff protocol and rehearsal

## Purpose

Test whether external-corpus target execution can be separated from hidden-gold construction by an auditable object boundary rather than a directory naming convention.

## Frozen sequence

1. Construction freezes the public query/source/passage manifest and evaluator contract.
2. Construction creates dummy hidden gold outside the target-execution Git snapshot.
3. Construction publishes only the canonical SHA-256 commitment to that hidden gold.
4. Target execution receives only the public manifest, permitted source material, contract/run shape, K, and commitment.
5. The exact pre-reveal Git snapshot is inspected for absence of dummy gold and construction notes.
6. A dummy ranked run is frozen without using hidden gold.
7. Gold and dummy construction notes are revealed in a later Git commit.
8. Canonical revealed gold is hashed and compared with the earlier commitment.
9. Evaluator A and B score the same frozen manifest/run/revealed-gold tuple.
10. Adversarial, mutation, fail-closed, and invariance fixtures challenge both implementations.

## Decisive pre-reveal identity

- base main: `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`
- first pre-reveal draft: `496f5bed508fb00673d77c00621036e4eefc3dd5`
- authorized pre-reveal snapshot: `9123eec2ec0da48f61bd063f634f1e20b1fc5f68`
- hidden-gold commitment at that snapshot: `2d0e0d99d23295b91c838e01a4e1a6274e2a77af45cd52ab834ed78fd5b6131f`

The exact `revealed_dummy_gold.json` path returns 404 at the authorized pre-reveal snapshot. The module directory at that commit contains the public contract, manifest, run, commitment, canonicalizer, evaluator implementations, and access policy, but not revealed gold or construction notes.

## Role access

Construction could access dummy hidden gold and construction notes plus the public contract/manifest. It was forbidden from using any Evidence Bundler retriever or scientific Pilot 0A qrels.

Target execution at `9123eec2...` could access only public manifest/source identities, contract/run shape, K, commitment, and ordinary public repository content. The new dummy gold, construction notes, and gold-derived expected results were absent.

Post-reveal evaluation could access the exact run, revealed dummy gold, pre-reveal commitment, public manifest, contract, and evaluators.

## Bound

The rehearsal establishes Git-object separation for the dummy gold. It does not establish separately credentialed principal isolation because the same authenticated owner/supervisory context assembled both sides. A future scientific execution identity must be unable to reach construction-only storage or refs through normal credentials.
