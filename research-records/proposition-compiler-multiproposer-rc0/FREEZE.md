# Proposition Compiler Multi-Proposer Convergence RC0 — Pre-Fresh Freeze

## Scientific freeze boundary

No decisive fresh roots existed when this freeze was declared.

Frozen proposal/resolution source commit:

- commit: `89d3917d4a4fb65851858e3d79711ac391988fd4`
- tree: `12ee0e3ccce18de9cd04fa057ceabfce55b284d6`

Exact Git blob identities at that commit:

- `research/proposition_compiler_multiproposer_rc0/proposers.py`: `b2684f1752a1eb841dd6ee85b1e81ae523b03810`
- `research/proposition_compiler_multiproposer_rc0/resolver.py`: `ca2fbf63855f21551c2e1ebb46019768753746e4`
- `research/proposition_compiler_multiproposer_rc0/score.py`: `c7ee9d99cccb96d2b713b22d6f29f06feca54212`

Fixed semantic authority:

- RC1 authority commit: `26539c53781148543e980fe1f07b25f1ad9c2005`
- RC1 evaluator SHA-256: `1091169da8e960cdf93242ee4c629c7a1a814009c8f80554f4a190f5b3fe989d`

The RC1 evaluator is fetched from that exact commit at execution time and must pass the SHA-256 check before use.

## Development evidence before freeze

Latest hosted development run:

- workflow run: `34649319509`
- job: `103427506326`
- result: `success`
- exact development replay hash, both runs: `8b55083ff30212afdfc0fa97601b577ad6c9b79a6c586442ee541bf6a160e3d6`
- artifact ID: `10282659175`
- artifact ZIP SHA-256: `12544c486515415c397f8479a0e8dce6971d52c7fcd51ad34093e103229c3cff`

Observed development behavior:

- P1 resolved shared-subject, shared-scope, and shared-subject negation cases.
- P2 resolved explicit independent clauses, directional relations, local scope, and comparison cases.
- P3 uniquely resolved the contextual-pronoun development case using a reference-preserving surface realization.
- P3's explicit-reference rewrite for that case was rejected by the frozen RC1 evaluator.
- P3's deliberately unsafe left-only and right-only shared-scope variants were rejected by the frozen RC1 evaluator.
- ambiguous pronoun and `or` roots remained unresolved.
- the known RC1 modal/shared-coordination and matrix-attribution root-parser bottlenecks remained unresolved.

These are development observations only and do not qualify the architecture.

## No-repair rule

After this record, `proposers.py`, `resolver.py`, `score.py`, and the frozen RC1 evaluator identity are immutable for the decisive RC0 experiment.

Any semantic change to those objects after fresh-case exposure requires a successor experiment. Infrastructure-only repairs must be recorded as deviations and must not change scientific object identities.
