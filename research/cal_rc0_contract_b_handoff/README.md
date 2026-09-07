# Research EB Profile RC0 Contract B Handoff

The hard boundary in this build is between retrieval state and semantic state.

This research infrastructure takes exact Contract A 2.0.0 declared `all_of` propositions, retrieves each declared child independently, preserves proposition/lane provenance, applies an explicit research review state, and emits Contract B 1.2 material for the parallel CAL RC0 consumer.

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

The machine-readable Research EB Profile records the implementation commit separately from the PR head so the profile does not attempt to hash a commit that contains itself.

## Handoff stages

For each case:

1. validate the supplied Contract A wire invariants;
2. query every declared child independently using the pinned research-only BM25 qualification retriever;
3. retain the first `K` candidates per child without root union;
4. apply explicit `accepted`, `rejected`, or `needs-review` research review state;
5. emit a Contract B 1.2 bundle containing retained physical evidence and proposition/lane history;
6. keep evaluator gold outside the runtime path;
7. evaluate whether required evidence was lost at candidate-pool, retention, or admission.

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

## Contract B compatibility seam

Contract B 1.2 still requires legacy scaffold compatibility fields in each `ClaimAuditUnit`. Contract A 2.0.0 does not supply those fields.

This build therefore uses the released B fields with a fixed compatibility mapping:

- `scaffold_support_status = uncertain`;
- `scaffold_claim_strength = 0.0`;
- `scaffold_extraction_fidelity = 1.0`;
- counterevidence and downgraded flags = false;
- every CAL audit field = null.

These values are not evidence judgments and are not consumed by the research admission receipt. This is a preserved representational limitation of using the current B 1.2 base shape with Contract A 2.0.0, not a Contract B amendment.

The factual-context extension carries the actual research history. Its review decision means only research admission state. It does not mean semantic support or refutation.

## Files

- `fixtures/cases/*.json`: source material and exact Contract A objects, one immutable file per case.
- `fixture_loader.py`: deterministic fixed-order assembly of the 8-case runtime cohort.
- `fixtures/admission.json`: explicit research review decisions. The runtime may consume this.
- `fixtures/evaluator_gold.json`: independent evaluation authority. The runtime must not consume this.
- `build_handoff.py`: retrieval, retention, admission, and Contract B emission.
- `evaluate_receipt.py`: post-runtime localization against evaluator gold.
- `RESEARCH_EB_PROFILE.json`: frozen machine-readable profile, added after the implementation commit is known.
- `qualification/`: deterministic runtime/evaluator receipts after the profile freeze.

## Non-claims

A passing qualification does not establish:

- production retrieval quality;
- an optimal K;
- a better reranker;
- root-plus-child retrieval as a default;
- autonomous evidence admission;
- semantic evidence sufficiency beyond the frozen evaluator facts;
- CAL semantic correctness;
- Contract A or Contract B changes;
- production authorization.

The output exists to make downstream failure localization inspectable before CAL semantics begin.
