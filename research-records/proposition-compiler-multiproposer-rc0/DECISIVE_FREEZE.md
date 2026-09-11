# Multi-Proposer Convergence RC0 — Decisive Freeze

## Freeze order satisfied

The proposal/resolver apparatus was frozen before any decisive fresh root was authored. Fresh roots were then committed, followed by adjudication gold, before any decisive target execution.

## Frozen scientific apparatus

Source commit: `89d3917d4a4fb65851858e3d79711ac391988fd4`

- proposer blob: `b2684f1752a1eb841dd6ee85b1e81ae523b03810`
- resolver blob: `ca2fbf63855f21551c2e1ebb46019768753746e4`
- scorer blob: `c7ee9d99cccb96d2b713b22d6f29f06feca54212`
- fixed RC1 authority commit: `26539c53781148543e980fe1f07b25f1ad9c2005`
- fixed RC1 evaluator SHA-256: `1091169da8e960cdf93242ee4c629c7a1a814009c8f80554f4a190f5b3fe989d`

## Frozen decisive evidence surface

Scientific state after fresh roots and gold: `2f87e9fecc20dd1c8ee498fec73928d46fb98dca`

- `fresh_roots.jsonl` Git blob: `e51ec542898a0f40489e0140bbd0455e1429e0bb`
- `GOLD/fresh_gold.jsonl` Git blob: `da169fcc9b0efc096cbb3c68a744da9d7beaa03d`
- root count: 24
- family count: 6
- roots per family: 4
- gold `RESOLVED`: 22
- gold `FAIL_CLOSED`: 2

The ellipsis case F19 and local-attribution case F20 are adjudicated `RESOLVED` despite known predecessor parser limitations. They are retained to expose, not conceal, a fixed-authority bottleneck.

## Runtime/gold boundary

The decisive workflow must:
1. verify these exact Git blob identities;
2. fetch and verify exact frozen RC1 evaluator bytes;
3. move gold outside the runtime research path before target execution;
4. execute the resolver and freeze/hash raw output;
5. perform an exact replay and byte comparison;
6. only then score against sealed gold;
7. preserve artifacts and checksums.

No scientific object above may change after decisive output. A change requires a successor experiment.
