# Evidence Bundler RC0 A2 → B1.2 handoff preflight

## Result

**NEGATIVE INTERFACE COUNTEREXAMPLE.**

The requested retrieval apparatus was stopped before retrieval execution. The frozen Contract A 2.0 and Contract B 1.2 authorities do not currently provide a lawful exact projection for a declared A2 child into the canonical B core claim shape.

## Observed

- Evidence Bundler `main` was verified at `c26fbd4bfc8ba5c2604a784af158594b59fcae37` before branching.
- Contract A `contract-a-v2.0.0` resolves to `529c92b49a34d5c610618551a8737f019f9fa332`. Its production wrapper says unknown Contract-A-owned fields fail closed and explicitly excludes upstream support labels, claim strength, extraction fidelity, and related legacy semantic-looking state from A2 authority.
- Contract B `contract-b-v1.2.0` resolves to the requested production lock `c314e53bd91c0736aa4370a364673b069aceb43e`.
- Contract B 1.2 says the factual-context extension is additive, does not rewrite the v1.0 core, and leaves existing claim/source/passage records canonical.
- The locked Contract B core claim shape requires scaffold-assigned fields described by the core specification as “from C-A; immutable in C-B”, including `scaffold_support_status`, `scaffold_claim_strength`, and `scaffold_extraction_fidelity`.
- The current Evidence Bundler producer model also requires those legacy fields for `ClaimAuditUnit`.

## Why this stops RC0

A valid Contract A 2.0 object cannot supply those legacy B-core fields. Adding them to Contract A is rejected by the canonical A2 validator. Filling them inside Evidence Bundler would invent upstream semantic state and violate this RC0’s authority boundary. The 1.2 extension cannot solve that mismatch because it may only reference existing canonical B claims.

This triggers the preregistered stop condition:

> Contract B cannot preserve required root/child identity without semantic misuse.

No placeholder values were chosen. Retrieval metadata was not converted into semantic authority. Validation was not weakened. Contract B was not widened. CAL was not called.

## Executable falsifier and CI evidence

`research/eb_rc0_a2_b12_handoff/contract_boundary_preflight.py` reproduces the boundary on the pinned authorities. It:

1. validates the released A2 declared fixture with the exact released validator;
2. mutates it with a legacy semantic-looking field and requires the A2 validator to reject it;
3. checks the canonical EB Contract B producer model still requires the legacy B-core fields;
4. attempts the smallest B child claim using only A2 child identity plus mechanical B fields and requires it to fail missing those fields;
5. checks that the frozen B1.2 extension remains additive rather than a core rewrite.

Dedicated workflow run `34080648916`, job `101615145174`, completed successfully on tested research head `7ab5607071d16089dae3a86783e62ebe60cb19e6` and GitHub PR merge SHA `6ff7048d65f5bc8c4156506901ef69f4791c8ff2`.

Observed workflow receipts:

- counterexample: `COUNTEREXAMPLE_CONFIRMED`;
- ordinary Evidence Bundler regression: `199 passed, 5 skipped in 10.40s`;
- CAL dependency gate: `NO_CAL_DEPENDENCY`;
- uploaded receipt artifact: ID `10003599509`;
- uploaded artifact ZIP SHA-256: `609916bd4be1d5a59e3a45a93683959581c384e30b7fd335056cd12da1e12bf3`.

## Not produced

Because the stop condition occurs before retrieval execution, the following outputs are intentionally **not** fabricated: `A2_INTAKE_RECEIPT.json`, `PROPOSITION_MANIFEST.json`, `QUERY_MANIFEST.json`, `CORPUS_CHUNK_RECEIPT.json`, `CANDIDATE_POOL.jsonl`, `SELECTION_RECEIPT.json`, `ADMISSION_RECEIPT.json`, `APERTURE_RECEIPT.json`, Contract B output tree, and `BASELINE_BM25_TOP5.json`.

`RESEARCH_EB_PROFILE.json` records the intended frozen profile and the pre-execution stop without pretending that a corpus, query set, rankings, admissions, or Contract B output hashes were materialized.

## Downstream disposition

Track B is **not ready** for a future CAL integration smoke. There is no lawful canonical Contract B 1.2 artifact to hand to CAL under the frozen A2/B1.2 authorities. Resolving that interface boundary is outside this RC0 and requires a new bounded contract/interface decision before this handoff build can resume.

## Bounded inference

This is a contract/interface authority mismatch. It is not evidence about BM25, BGE, retrieval quality, candidate recall, evidence sufficiency, CAL correctness, or production readiness.

No fresh naturalistic cohort was exposed. No CAL semantic engine was called. No production source, default, release, tag, merge, or promotion was changed.
