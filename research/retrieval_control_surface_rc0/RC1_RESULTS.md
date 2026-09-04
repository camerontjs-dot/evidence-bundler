# Retrieval Arm Receipt and Observability Hardening RC1 — Results

Status date: 2026-08-29

Terminal apparatus disposition: **RC1_REPAIRS_VERIFIED**

Characterization disposition: **NOT YET AUTHORIZED**

This is Research Infrastructure evidence only. No Pilot 0A scientific judgments, qrels, hidden gold, or target-system performance were used.

## OBSERVED — authority

- RC0 frozen source: `a02a9d313816ad8302efbcbb24bca265c31473e7`
- RC0 reconciliation PR: #37
- RC1 PR: #38
- exact tested RC1 commit: `5dde0df3dbea8de476de240f2f48d2b9c0c5b715`
- exact tested tree: `1cd3189f1cf2f278a2d936f10e0af9fe519426ca`
- exact-head push workflow run: `33281719546`
- apparatus job: `99177883484`
- workflow artifact: `9723197074`
- artifact archive digest: `sha256:744f2a01df076495f4e0be188c10ed90a376d13678f38451f587ddaead0f254c`

## OBSERVED — repairs

### Machine-readable arm receipt

`src/evidence_bundler/retrieval/research_receipt.py` now records:

- repository, exact apparatus commit SHA, and exact apparatus tree SHA;
- source run identity and source corpus hash;
- complete serialized `RetrievalConfig`;
- normalized identity config;
- explicit non-identity config fields for cache/index filesystem paths;
- retrieval config hash;
- explicit chunk geometry;
- ordered materialized chunk-set hash even for transient runs;
- canonical embedding/reranker identifiers and immutable revisions;
- Python and material runtime package versions;
- platform/device context;
- bundle and optional report hashes;
- execution timestamp;
- replay-oriented `arm_identity`;
- SHA-256 sidecar for the written receipt.

The legacy MiniLM alias remains unchanged in `RetrievalConfig` so production defaults are not modified. The research receipt canonicalizes that alias to `cross-encoder/ms-marco-MiniLM-L6-v2`.

### Research-only independent controls

Added with default `None`, preserving prior default behavior:

- `parent_candidate_top_k`;
- `counterevidence_lexical_child_top_k`;
- `counterevidence_semantic_child_top_k`.

When unset, normal retrieval preserves the RC0 behavior. Counterevidence child budgets fall back to the existing `rrf_candidate_pool`.

### Truthful durable Markdown report

The report now includes:

- parent candidate top-k;
- semantic query prefix;
- independent counterevidence lexical child top-k;
- independent counterevidence semantic child top-k.

### Stale transport cleanup

The obsolete `.github/workflows/research-retrieval-control-surface-rc0-bootstrap.yml` was removed only on the successor line. Historical failed and successful RC0 runs remain preserved.

## OBSERVED — observability/replay tests

The successor suite directly demonstrates:

- receipt reconstruction and same-arm replay from the serialized config;
- same normalized `arm_identity` under replay;
- same ordered chunk-set hash under replay;
- same deterministic claim summaries under replay;
- cache-path changes are recorded but do not alter arm identity;
- semantic-query-prefix mutation changes the text actually encoded;
- parent candidate budget mutation changes the actual aggregation limit while final `top_k` is held fixed;
- counterevidence lexical and semantic child budgets independently change their respective retrieval calls;
- RRF `k` mutation changes fusion computation with rankings held fixed;
- contradiction prefix mutation changes generated contradiction queries;
- contradiction text-gate mutation changes role classification with passage text held fixed;
- new research-only controls default to disabled/legacy behavior.

See `OBSERVABILITY_MATRIX_RC1.md`.

## OBSERVED — false-green counterexample preserved

An earlier run on commit `61676caeb0ffd4602ab66663b6e918698eabf29c` was reported green by GitHub even though the test output contained:

- `1 failed, 215 passed, 5 skipped`;
- explicit successor suite: `1 failed, 7 passed`.

Cause: commands such as `pytest | tee` were executed without shell `pipefail`, so `tee` masked the failing producer exit code.

This was an evaluator/apparatus failure, not retrieval behavior evidence.

The workflow was repaired to use `set -o pipefail`. Run `33281626643` then correctly failed on the same test instead of masquerading as green.

The failing assertion itself expected a trailing space on a `NonBlankStr`. Pydantic normalizes the stored value by stripping that trailing whitespace, while semantic encoding restores a separator when needed. The test was corrected to assert the normalized stored configuration rather than an input-formatting artifact.

## OBSERVED — final exact-head tests

Workflow run `33281719546` tested commit `5dde0df3dbea8de476de240f2f48d2b9c0c5b715` and tree `1cd3189f1cf2f278a2d936f10e0af9fe519426ca` without mutating the tested object.

Results:

- full deterministic suite: **216 passed, 5 skipped**;
- explicit successor observability/replay suite: **8 passed**;
- Ruff: **clean**;
- scoped mypy: **clean, 4 source files**;
- CLI truthfulness checks: **pass**;
- artifact upload: **pass**.

## OBSERVED — exact pinned real-model execution

The exact tested head executed:

- `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`;
- `cross-encoder/ms-marco-MiniLM-L6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a`.

Observed receipt:

- embedding dimension: `384`;
- reranker score: finite;
- real-model receipt SHA-256: `fce78a368c75f57b8450f763d69e4ce83b77a34ec899d28eead24a6c855de3af`.

Runtime receipt:

- Python `3.11.16`;
- sentence-transformers `5.7.0`;
- faiss-cpu `1.15.0`;
- rank-bm25 `0.2.2`;
- pydantic `2.13.5`.

This is apparatus execution evidence only and makes no model-quality claim.

## INFERENCE — prerequisite status after RC1

| Prerequisite | State |
| --- | --- |
| Truthful independent variables needed for planned Blocks A/E | **CLEARED for the repaired controls** |
| Machine-readable reconstructable arm identity | **CLEARED** |
| Immutable model identity plus exact-head execution | **CLEARED** |
| Reproducible chunk identity | **CLEARED at apparatus level** |
| BM25 / semantic / hybrid executable semantics | **CLEARED from RC0 + RC1** |
| Deterministic non-Pilot diagnostic evaluator/corpus | **NOT CLEARED** |
| Pilot scientific-gold independence | **CLEARED for this apparatus work** |

Therefore characterization is still **not authorized**. The remaining blocking prerequisite is a separately frozen, deterministic, non-Pilot diagnostic corpus/evaluator with intentionally weak controls.

## HYPOTHESIS

Once that diagnostic object is independently frozen and shown to reject at least one plausible weak strategy for the intended reason, the characterization design can be converted into a preregistration without reopening RC1 apparatus semantics.

## UNKNOWN

No claim is made yet that the proposed diagnostic corpus will discriminate retrieval families adequately. That must be tested as an evaluator-system question before configuration comparison.

## Production impact

None authorized. The new controls are research-only optional configuration values with defaults that preserve prior behavior. No retrieval model, retrieval family, threshold, or production default is promoted by RC1.
