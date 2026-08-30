# Counterevidence Pass Dev RC1 — Preregistration

Status: **AUTHORIZED BOUNDED DIAGNOSTIC EXECUTION**

Class: Research Infrastructure / counterevidence retrieval characterization.

This experiment does not use Pilot scientific gold, does not use the RC2 sealed split, does not change production defaults, and does not authorize production promotion.

## Starting evidence

Prior RC2 dev characterization established:

- raw semantic K counterevidence recall: 0.0;
- semantic 2K and 4K candidate pools contain 100% R02 counterevidence;
- generic MiniLM reranking over semantic 4K still returns 0.0 R02 counterevidence recall.

Therefore the next question is whether the existing explicit contradiction/counterevidence pass recovers counterevidence through query expansion and role-aware admission.

## Frozen authority

- RC2 benchmark tree SHA256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`
- dev split only;
- embedding model: `BAAI/bge-small-en-v1.5`;
- embedding revision: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`;
- semantic query prefix: `Represent this sentence for searching relevant passages:`;
- contradiction query prefixes: current frozen `DEFAULT_CONTRADICTION_QUERY_PREFIXES`;
- RRF k: 60;
- contradiction reranking: disabled.

## Supporting channel

Hold supporting retrieval fixed at raw semantic K using the same representation and model identity as Block B.

Supporting and counterevidence channels remain separate in the raw artifact.

## Arms

For every dev case with benchmark budget `K`:

### E0 — counter pass disabled

- supporting semantic K only;
- counterevidence channel empty.

### E1 — counter pass enabled, text-role gate ON

- five current fixed contradiction-query prefixes;
- lexical child budget per contradiction query: K;
- semantic child budget per contradiction query: K;
- RRF k=60 over all contradiction-query lexical/semantic rankings;
- counterevidence output budget: K;
- current text-pattern role gate enabled;
- contradiction reranking disabled.

### E2 — counter pass enabled, text-role gate OFF

Same as E1 except all contradiction-pass candidates are admitted as `contradicting`.

E2 is a mechanism probe, not a proposed production setting.

## Gold boundary

The retrieval runner is gold-blind and may read only runtime passages, dev cases, and apertures.

A separate analyzer may read evaluator-only dev gold only after raw E0/E1/E2 artifacts are written.

## Measurements

Preserve separately by arm:

- R02 decisive counterevidence recall;
- all-family decisive counterevidence recall where applicable;
- counter-channel case hit;
- role-gate rejection count;
- role-gate false rejection of decisive counterevidence;
- admitted conditional count;
- admitted contradicting count;
- duplicate identities shared with supporting channel;
- counter-channel hard-negative burden;
- spillover counter-channel admissions on non-counterevidence families;
- provenance/scope/budget integrity;
- exact per-query lexical/semantic candidate budgets;
- total lexical and semantic query-call counts;
- exact model revision and contradiction prefixes.

Do not collapse to a scalar score.

## Falsifiers

### Counterevidence-pass usefulness

Weakened if E1 does not materially improve R02 counterevidence recall over E0.

### Role-gate usefulness

Supported only if E1 rejects non-decisive spillover while retaining decisive counterevidence.

Falsified if decisive R02 counterevidence is retrieved before the gate but rejected by the gate.

### Query-expansion usefulness

Supported if E2 recovers decisive R02 counterevidence into the counter channel. If E2 also fails, the failure is upstream of the text-role gate.

### Overbreadth

A large increase in non-counterevidence-family admissions or hard negatives weakens the case for the pass even if R02 improves.

## Stop conditions

Stop without interpreting behavior if:

- benchmark identity changes;
- exact pinned embedding revision cannot execute;
- retrieval runner reads dev gold;
- counter budgets differ from K;
- contradiction prefixes or RRF constant change after preregistration;
- output identities cannot round-trip exactly.

## Non-claims

This experiment does not establish:

- production counterevidence settings;
- optimal contradiction prefixes;
- optimal counterevidence budget;
- semantic contradiction classification;
- NLI correctness;
- Pilot performance;
- sealed generalization;
- production promotion.
