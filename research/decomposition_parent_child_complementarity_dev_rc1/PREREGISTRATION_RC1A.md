# Decomposition + Parent/Child Complementarity Dev RC1A — Successor Preregistration

Status: preregistered successor before any RC1A generation, retrieval, faithfulness evaluation, or gold analysis.

## Why RC1A exists

RC1 produced two preserved pre-gold failures:

1. run `33869504444` stopped on Ruff before generation;
2. run `33869743401` reached generation and Contract A validation, but both frozen model generators received the complete 357-source body-text aperture in every prompt and exceeded their model context limits. FLAN produced 0/12 declared outputs with an observed 26,548-token prompt against a 512-token limit; Smol produced 0/12 declared outputs with an observed 27,838-token prompt against an 8,192-token limit. All 42 resulting Contract A fixtures printed `VALID`, then the workflow failed because the validation counter was incremented inside a piped subshell.

Run `33869743401` stopped before faithfulness analysis, R0/R1/R2/R3 retrieval, raw-retrieval freeze, or dev relevance analysis. No retrieval gold was opened and no retrieval result was observed.

The immutable RC1 failure record is `research-records/decomposition-parent-child-complementarity-dev-rc1/FAILED_RUNS.md` at ancestor commit `035674a72413e1528720bfd2ed6b97f70e7e2f5b`.

RC1A is a successor, not a rewrite of RC1.

## Decision questions

Unchanged from RC1:

1. Which bounded decomposition strategies produce useful evidence worlds without material semantic-faithfulness instrument failures?
2. For a valid Contract A `declared/all_of` root, does retrieving the exact root in addition to mandatory exact-child retrieval add material information?
3. Does preserving proposition/retrieval roles outperform flattening the same available root/child evidence into an anonymous union?

No CAL aggregation rule is decided here. Generated semantics acquire authority only inside each separately resealed research Contract A fixture.

## Frozen research identities

Unchanged:

- predecessor research PR: #43
- predecessor terminal head: `0e4bed62553ebb6aef6a1b485664fb80cc78c802`
- predecessor decisive implementation: `55d158f829f4aad1ed8ad69b19d9e39d445c953d`
- predecessor decisive run: `33286415682`
- frozen challenge corpus tree SHA256: `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8`
- frozen dev decomposition file SHA256: `2120228c81466471214ca8b56a6eba2fa5bc498cd0b0243ff3b8fe24c9da2144`
- retrieval embedding model: `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- split: dev only; sealed/test data prohibited
- cases: claim-009/F03, claim-013/F04, claim-017/F05, claim-021/F06, claim-037/F10, claim-049/F12

Canonical Contract A authority remains:

- `camerontjs-dot/apparatus-contracts@c3563cff66d2c85dcbf575c693056e2d8e4563d4`
- validator blob `42e5f5b3bf38d677445e9d01ea130ba604e53409`
- wire token `contract-a-wire-candidate-rc2`

## The only scientific-apparatus change: generator source exposure

RC1 proved that injecting all source bodies into the decomposition prompt is incompatible with the frozen model contexts. RC1A therefore separates **frozen source aperture identity** from **decomposition semantic input**.

For D3, D4, D5a, and D5b:

- the full exact source representation array remains present in the frozen generation-input artifact;
- the full exact source representation array remains byte-identical across all Contract A treatment fixtures;
- retrieval later runs over those exact source bytes;
- the decomposition generator receives only the exact authoritative root proposition plus its frozen strategy instruction;
- no source body, source snippet, retrieval result, gold annotation, expected downstream verdict, predecessor result, or other generator output is included in the model prompt.

This is intentionally a **root-semantic decomposition aperture**. It is stricter than RC1 and avoids source-derived proposition additions. It does not claim that source-aware decomposition is useless; it only tests whether the bounded strategy families can produce faithful candidate children from the authoritative proposition itself.

The full generation-input SHA remains recorded so every generated treatment is still linked to the exact common root/source research world.

This change is fixed before RC1A generation. It may not be changed again after generator outputs are observed.

## Frozen decomposition treatments

D1 — predecessor A1 minimal conjunctive child texts exactly.

D2 — predecessor A2 scope-preserving child texts exactly.

D3 — retrieval-oriented, meaning-preservation constrained, root-only prompt:

`google/flan-t5-small@14fd6edcfdd71f2ef5b67d4e735fee8bc6d9fd31`

D4 — typed-semantic bounded-concept, meaning-preservation constrained, root-only prompt:

`HuggingFaceTB/SmolLM2-360M-Instruct@a10cc1512eabd3dde888204e902eca88bddb4951`

D5a / D5b — the same neutral root-only decomposition instruction, executed independently by the two frozen models above. Neither model sees the other's output before both are frozen.

D6 — predecessor A4 deliberate over-decomposition negative control exactly.

A model output that cannot parse to 2–4 unique child strings remains `decomposition.state=failed`. No regeneration or manual repair is allowed after observing RC1A outputs.

## Contract A fixture rules

Unchanged except successor identity strings use `rc1a`:

- one exact root per case;
- identical ordered source representation bytes across all seven treatments for that case;
- each declared alternative has its own decomposition identity, exact child IDs/text/hashes/order, and whole-object reseal;
- failed generators become valid `decomposition.state=failed` objects;
- every fixture must validate under the pinned canonical Contract A validator before retrieval begins.

The workflow validation-count implementation may be corrected mechanically so that successful validator invocations are counted outside a shell pipeline subshell. This is not a treatment change.

## Retrieval arms and budgets

Exactly unchanged from RC1.

For each declared treatment, retriever (`semantic` primary; `bm25` secondary control), and budget mode:

- R0 root only;
- R1 exact children only;
- R2 root + exact children with every proposition/role/lane relationship retained;
- R3 exact R2 physical passage set with proposition/retrieval attribution removed.

Equal-total budget:
- R0: K to root;
- R1: K divided deterministically across N children;
- R2/R3: K divided deterministically across root + N children.

Equal-per-query capacity:
- K for every active query lane.

The two budget questions remain separate.

## Faithfulness instruments

Unchanged:

- bidirectional NLI using `cross-encoder/nli-deberta-v3-small@fa2804872c3b4bd748f38c0185cc85775361e735`;
- exact critical-feature retention for numbers, dates/temporal markers, negation, modality, conditions/exceptions, and named/alphanumeric scope/entity tokens;
- auditability/redundancy measures;
- pairwise generator disagreement.

These are measurements under test, not proposition authority.

## Gold firewall

Required execution order:

1. verify RC1A apparatus is a descendant of this preregistration;
2. run deterministic tests and static checks;
3. build and hash the complete six-case generation input containing exact roots and full source arrays;
4. execute both frozen model generators with root-only prompts;
5. freeze/hash both raw generator outputs;
6. build and validate every Contract A treatment;
7. freeze/hash the entire Contract A fixture directory;
8. run and freeze semantic-faithfulness instruments;
9. run gold-blind R0/R1/R2/R3 retrieval;
10. freeze/hash raw retrieval;
11. only then open frozen dev relevance annotations in the posthoc analyzer.

No sealed/test data may be read.

## Falsifiers and legitimate negative outcomes

- If either frozen model still cannot produce valid decompositions, retain that abstention. Do not repair it.
- If D3/D4 retrieve better but fail material faithfulness instruments, they are not semantically safe successes.
- If R2 adds no equal-total information over R1 or primarily adds noise, the parent lane does not earn default production status.
- If R2 helps only under increased per-query capacity, that is a capacity result, not a representation result.
- If R2 and R3 have identical passage sets but role removal destroys proposition-attribution facts, role preservation is supported even without recall differences.
- If over-decomposition does not hurt this cohort, preserve that negative result.
- If the CAL-facing probe cannot carry root/child distinction under current Contract B/CAL authority, record the boundary rather than inventing a schema or composition rule.

## Stop rule

After RC1A generation is frozen, do not change model pins, prompts, parsing rules, historical treatment texts, retrieval models, retrieval budgets, faithfulness instruments, or analysis criteria in response to observed outcomes.

Stop after frozen generation, Contract A validation, faithfulness, both retrieval budget comparisons, posthoc analysis, bounded CAL-facing probe if representable, exact receipts, issue/PR reconciliation, and synthesis input.

Do not merge this research PR, modify Contract A/B, touch sealed data, tune production defaults, or implement the final production A→EB→B architecture here.
