# Research EB Profile RC0 Contract B Handoff

The hard boundary in this build is between evidence-world state and semantic state.

This research infrastructure takes exact Contract A 2.0.0 declared `all_of` propositions, retrieves each declared child independently, preserves proposition/lane provenance, applies explicit research review state, and prepares Contract B 1.2 material for the parallel CAL RC0 consumer.

It does not run Claim Audit Lab and it does not assign support, refutation, entailment, semantic warrant, proposition truth, or a CAL conclusion.

## Authority pins

- Evidence Bundler base: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- Contract A release: `contract-a-v2.0.0`
- Contract A release commit: `529c92b49a34d5c610618551a8737f019f9fa332`
- Contract A promotion merge: `b59c2fbe38bae78a3a35699362c0e67d17152e4b`
- Contract A frozen validator blob: `42e5f5b3bf38d677445e9d01ea130ba604e53409`
- Contract B release: `contract-b-v1.2.0`
- Contract B production lock: `c314e53bd91c0736aa4370a364673b069aceb43e`
- Contract B factual-context validator blob: `f5ad1a0db70d2f36d06c04ab0c9c2050f41bd8e7`
- Evidence Bundler factual-context producer ancestor: `c8189c31adbab11729c31430c2070126224a2d42`
- CAL supervisor synthesis: `dff189bd58cd1f1817564b18ff53a355787e8338`

The frozen `RESEARCH_EB_PROFILE.json` continues to govern retrieval/admission apparatus. The later compatibility carrier is deliberately separate because it was added after the A2/B1.2 interface counterexample was observed.

## Evidence-world stages

For each case:

1. validate the supplied Contract A wire invariants;
2. query every declared child independently using the pinned research-only BM25 qualification retriever;
3. retain the first `K` candidates per child without root union;
4. apply explicit `accepted`, `rejected`, or `needs-review` research review state;
5. preserve candidate, retention, admission, proposition, lane, source, and aperture receipts;
6. keep evaluator gold outside the runtime path;
7. localize required-evidence loss to candidate-pool, retention, or admission.

The default RC0 handoff never flattens parent and child provenance. An optional root diagnostic is available only as the separately named `diagnostic_root_rescue` lane and is disabled in the frozen profile.

## Qualification retriever

This first build uses a small, deterministic, research-only Okapi BM25 implementation:

- lowercase word tokenizer;
- `k1 = 1.5`;
- `b = 0.75`;
- per-query candidate depth = 5;
- retained K = 3;
- no learned model;
- no reranker;
- no semantic retrieval;
- no context truncation;
- no diversity selector.

These settings qualify the handoff machinery. They are not a production retrieval recommendation and are not tuned against downstream CAL outcomes.

## Contract A 2.0 -> Contract B 1.2 compatibility seam

The initial adapter attempted to make a valid Contract B 1.2 core object by filling legacy C-A-derived fields with fixed values. Live boundary review showed that was too strong.

Contract A 2.0 deliberately does not carry the legacy fields Contract B 1.2 still requires, including scaffold support/strength/fidelity state, workflow condition, trust/bibliographic state, and other legacy provenance surfaces. Contract A 2.0 also says a separate compatibility carrier may be used where a legacy consumer still requires one, but that carrier is not Contract A 2.0 authority.

Qualification now follows that narrower route.

`fixtures/contract_b_compatibility_carrier.json` is a separate, qualification-only input. It explicitly declares:

- actual upstream authority is `contract-a-v2.0.0`;
- the carrier supplies no Contract A authority;
- the carrier supplies no CAL semantic authority;
- semantic use of carrier values is not authorized;
- legacy B-only scalar/boolean/source metadata are compatibility payload, not recovered A2 unknown state.

The qualification runtime fails closed if that carrier is missing, malformed, weakened, or changes its authority declaration.

The carrier is not an amendment to Contract A or Contract B. It is research-only compatibility apparatus for exercising the locked B1.2 wire while preserving the mismatch as an explicit limitation.

## Final B rewrite and reseal

`qualified_handoff.py` is the authorized qualification B-emission path. After the frozen retrieval/admission build creates the initial tree, the wrapper:

1. deduplicates repeated factual-context source references;
2. rewrites legacy B-only fields from the explicit compatibility carrier;
3. binds source `content_hash` and passage provenance back to exact Contract A 2.0 source content hashes;
4. requires each emitted passage to have exactly one exact occurrence in its Contract A source representation and derives exact character offsets from that occurrence;
5. preserves all CAL audit fields as null;
6. reseals `audit_config.yaml`, `bundle_manifest.yaml`, the bundle-tree hash, and `SHA256SUMS`;
7. runs exact Contract B tree/factual-context validation again.

The earlier direct `build_handoff.build_all_contract_b` function remains in the research record because it was part of the pre-counterexample implementation. It is not the qualification entrypoint and must not be treated as proof that A2 alone supplies canonical B1.2 legacy state.

## Causal separation

The compatibility carrier is not an input to `build_runtime_receipt`. Mutating compatibility-only support/trust values therefore cannot change candidate retrieval, retained K, or research admission state. Tests enforce that separation.

The factual-context extension carries the actual EB nomination/review history. Its review decision means only research admission state. It does not mean semantic support or refutation.

## Files

- `fixtures/cases/*.json`: source material and exact Contract A objects, one immutable file per case.
- `fixture_loader.py`: deterministic fixed-order assembly of the 8-case runtime cohort.
- `fixtures/admission.json`: explicit research review decisions. The runtime may consume this.
- `fixtures/contract_b_compatibility_carrier.json`: explicit qualification-only legacy B compatibility state. The B adapter may consume this; retrieval/admission may not.
- `fixtures/evaluator_gold.json`: independent evaluation authority. The runtime must not consume this.
- `build_handoff.py`: frozen retrieval, retention, admission, and pre-counterexample B-emission implementation.
- `qualified_handoff.py`: post-counterexample explicit-carrier B adapter, normalization, reseal, and validation path.
- `evaluate_receipt.py`: post-runtime localization against evaluator gold.
- `RESEARCH_EB_PROFILE.json`: frozen machine-readable retrieval/admission profile.
- `qualification/`: deterministic runtime/evaluator receipts from the earlier profile freeze; successor carrier qualification must produce a new receipt before any stronger claim.

## Non-claims

A passing carrier qualification would not establish:

- that Contract A 2.0 can natively populate Contract B 1.2 core legacy fields;
- production retrieval quality;
- an optimal K;
- a better reranker;
- root-plus-child retrieval as a default;
- autonomous evidence admission;
- semantic evidence sufficiency;
- source trustworthiness;
- CAL semantic correctness;
- Contract A or Contract B changes;
- production authorization.

The purpose is narrower: build enough truthful apparatus to expose evidence-world failures and exercise the downstream boundary without laundering missing state into A2 authority.
