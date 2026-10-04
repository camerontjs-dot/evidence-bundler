> Public presentation copy: local scratch paths are replaced with descriptive placeholders. The original report SHA-256 is `81dfbeb52362d0e7314ee9f05885d7476fa4063a6c0a9cfd69b6a57fa7f6048b`. Named raw logs/manifests remain local; only the selected scripts and summarized results listed in this directory are committed.

# Evidence Bundler V1: independent portable engineering review

## Disposition

**The frozen product candidate has strong bounded engineering behavior, but fails output-path containment. A correction and a fresh exact-subject replay are required before relying on its installed V1 command for arbitrary valid Contract A inputs.** Four independent probes overwrote probe-owned sentinel files outside the requested output directory before the command failed. Green author regressions did not expose these cases.

The remaining independent behavior exercise produced **34 asserted-property passes and two boundary observations**, all matching their stated expectations. This does not establish retrieval recall, evidence completeness, source legitimacy, semantic correctness, or release readiness. No provider, model, or corpus-authoring experiment was run.

## Exact subject and environment

| Item | Identity |
|---|---|
| Maintained baseline | `c26fbd4bfc8ba5c2604a784af158594b59fcae37` |
| Product/local-pipeline candidate | `08ca896debd6d16fa21be2f178ed7cbe62395d00` |
| Candidate tree | `1248dc464c8ac06aa6a5554b9092d1f793a8b2c2` |
| Frozen research authority named by candidate | `4e1f6fe00e7c350b28f52bfea14f1f8988847884` |
| Installed package | `evidence-bundler==0.2.0`, built wheel installed outside the repository |
| Wheel SHA-256 | `76b64db4753594dd62f0c7788507c6c3bf792b27eac63dae08e092bd801f7237` |
| Python | 3.12.14, Linux x86_64 |
| Isolated environment | `<baseline-venv>` |
| Profile | `eb-v1-integration-10x3-rc0` |
| Config identity | `sha256:5b10d0c29794e80d6876a99e26bcf6ec6a27a4c5165aee78054a6bc32759f4bc` |
| Contract A authority checked | Release `529c92b49a34d5c610618551a8737f019f9fa332` |
| Contract B authority checked | Lock `c314e53bd91c0736aa4370a364673b069aceb43e` |

`identity-record.json` records Git blob and SHA-256 identities for 120 source, test, configuration and workflow files, every installed distribution, the clean candidate worktree, and all ten frozen runtime/configuration pins. All ten pins match. Maintained main is an ancestor; the only modified pre-existing files are `pyproject.toml` and the package version in `src/evidence_bundler/__init__.py`. The legacy implementation and its existing tests are otherwise unchanged.

The wheel was installed with `--no-deps` into a fresh environment, with the exercised lightweight runtime dependencies installed explicitly. It imports from the environment's `site-packages`, and the independent CLI runs used unrelated working directories. This is **not a complete dependency-install qualification**; see the dependency result below. The candidate source, frozen tests and installed wheel environment were not changed after verification.

## Independence and evidence order

No repository or ancestor `AGENTS.md` was present. The reviewer first read the public README, promotion design and manifest, integration profile and compatibility carrier. `01-independent-probe-plan.md` was written and hashed before reading the runtime or author tests. Its SHA-256 is `289cdde8f3600f4f76d7fe2d7a20e0c17c234f0904e865fbff17ec8e562a6ebe`.

`02-path-containment-probe.py` and `03-behavior-probes.py` construct their own synthetic wire objects and compute hashes independently. They do not import author test fixtures. The later maintained tests are supplementary regression evidence. Exact canonical validators were subsequently run on the independently constructed inputs and outputs.

## Blocking finding: valid wire identifiers escape the output directory

Contract A validates proposition and source IDs as nonblank strings. The projection writes claim files using `claims / f"{claim_id}.yaml"` and source files using `evidence / source_id / ...`. Absolute IDs or `../../../` components therefore become output paths. In each case below, all attempted writes were confined to the review's own disposable scratch area.

| Independent case | Outside sentinel overwritten | Native package written | Receipt written | CLI exit |
|---|---:|---:|---:|---:|
| Claim ID with `../../../` | Yes | Yes | No | 1 |
| Source ID with `../../../` | Yes | Yes | No | 1 |
| Absolute claim ID | Yes | Yes | No | 1 |
| Absolute source ID | Yes | Yes | No | 1 |

The command eventually raises an uncaught factual-context error about unknown canonical references. That rejection occurs after the escaped writes, so the nonzero exit is not fail-closed output behavior. Source locations are the candidate's [Contract A identifier validation](https://github.com/camerontjs-dot/evidence-bundler/blob/08ca896debd6d16fa21be2f178ed7cbe62395d00/src/evidence_bundler/v1/contract_a.py), [`_write_base_bundle` projection](https://github.com/camerontjs-dot/evidence-bundler/blob/08ca896debd6d16fa21be2f178ed7cbe62395d00/src/evidence_bundler/v1/contract_b.py), and [production execution wrapper](https://github.com/camerontjs-dot/evidence-bundler/blob/08ca896debd6d16fa21be2f178ed7cbe62395d00/src/evidence_bundler/production_v1/execution.py).

The bounded repair should enforce safe destination construction before any artifact write, with a clearly stated representability boundary for identifiers. Preserve the frozen research blobs and distinguish the corrected product subject. Do not change retrieval or admission semantics to repair this defect.

The decisive record is `path-probe/results.json`, SHA-256 `cc8f78ab9c84ecd47c43fa4934ceaf9d2ec2436f6345a5487ea1a419c0b6cd1a`. `02-path-probe-freeze.json` seals 52 files and the original wheel; its SHA-256 is `e856145910539267892e4446db0a2fb6d5c47ad13f3672389f69c590d902a884`. The unchanged path probe itself hashes to `70f18e7c57e3ac6b0e90b358c621a8dd0be44f6fb1ccf69a19d3d6df3eaee52a`.

Replay the frozen script with the successor's Python and a new, nonexistent probe-output directory. The script locates `evidence-bundler-v1` beside `sys.executable`:

```bash
/absolute/successor-venv/bin/python \
  <portable-review-root>/02-path-containment-probe.py \
  <portable-review-root>/successor-path-probe
```

For a safe successor, all four original sentinels must remain unchanged and rejection must precede artifact emission. An intentional, contract-compatible identifier-to-path mapping would require separately verified positive mapping behavior.

## Independent positive and negative results

`behavior-probe/results.json` contains all 36 records, SHA-256 `87aa17d30bba5b4cc56c60b64c5ad9e3b34f9bf961c94d8f7f86dda6c2f30496`. The script hashes to `ee993b2ddffdf36835906509a2586c402bc5a4b23629cc99c4bc46a4d8165dce`.

The core synthetic input contains fourteen inline sources, including twelve equal-scoring lexical matches. All fourteen sources and their exact UTF-8 content hashes remain in the native package. Ten candidates are nominated in deterministic source-ID tie order; three are retained. The remaining seven retain explicit `not_retained` / `not_applicable` states. Without an admission file, none is exposed in the claim's accepted evidence list. Supplying one accepted, one rejected and one needs-review decision preserves the same nominations and exposes exactly the accepted passage.

Two complete CLI runs in different directories produced identical hashes for all 29 output files. Copying the complete artifact elsewhere preserved package, bundle and receipt validation. A Unicode, emoji, Markdown-table and CRLF source retained exact character spans. Offsets are Python Unicode character positions; hashes separately bind UTF-8 bytes.

Source-content mismatch, claim-text mismatch, duplicate source identity, unsupported schema/media, forbidden source-path fields, unknown/failed decomposition states and invalid admission bindings were rejected before durable artifact emission. Unknown/failed decomposition states remain valid Contract A states but supply no normative V1 retrieval target. A completed zero-hit retrieval remained distinct from an explicitly not-run retrieval. Native API checks also preserved declared-child targeting and partial execution; those options are not exposed by the fixed production CLI.

Raw admission-state and receipt modifications failed hash validation. Independently rehashed excerpt, source hash, nonretained acceptance, retention, rank-gap, searched-scope and authority inconsistencies were rejected. A modified projected passage failed bundle and file checksums. A carrier claiming semantic authority was rejected. A permitted compatibility-title change preserved the native package and all mapping identities while changing the downstream bundle identity.

The exact Contract A validator accepted thirteen and rejected six independently constructed wire objects, all as expected. The exact Contract B validator accepted six distinct projected/relocated extension artifacts, including the zero-hit and explicit-admission cases. Candidate vocabulary also matched the exact B1.2 canonical copy.

## Two boundaries that must not be overstated

1. **Admission is bound to an identifier pair.** Reusing the same admission file after changing target text, retaining `proposition_id`, and keeping the same retained passages still admitted the passage. The query identity changed. The admission wire contains no target-text, query, handoff or review-record digest. Callers must manage revision identity and retain the exact admission/input pair. This observation does not silently redefine the frozen admission contract.
2. **Internal validation is not retrieval-execution attestation.** A structurally consistent rank permutation, resealed with a new package hash, validated and projected. The validator checks internal shape, content/source bindings and the supplied digest; it does not rerun BM25. A trusted original identity and independent deterministic replay are separate controls. “Immutable” here is content-addressed artifact identity, not protection from an actor creating a different internally consistent artifact.

The native package preserves the complete source set. The Contract B compatibility tree contains nominated passages and their relevant source profiles. Retain the native package, projection receipt and Contract B tree together when claiming full input-to-output custody.

## Maintained regressions and quality gates

| Check | Result | Evidence |
|---|---|---|
| Author V1/package/projection/CLI tests | 29 passed, 1 CAL-import skip | `author-v1-tests.log` |
| Author complete portable candidate suite | 228 passed, 6 skipped | `author-full-portable-tests.log` |
| Baseline complete portable suite | 199 passed, 5 skipped | `baseline-replay-tests.log`, execution JSON and JUnit XML |
| Exact B1.2 vocabulary comparison | 1 passed | `exact-b12-vocabulary-test.log` |
| Ruff | Passed | `ruff.log` |
| Compileall | Passed | `compileall.log` |
| Strict mypy | Not qualified in this lane | `mypy.log` |
| Full dependency consistency | Not qualified | `pip-check-lightweight.log` |

The candidate suite's six skips were canonical vocabulary discovery, three legacy CAL demo tests, opt-in real reranker smoke, and exact CAL V1 intake import. The vocabulary check was subsequently closed against the pinned authority. CAL and model-dependent checks remain unexecuted. The first baseline log ended without a test summary; it is retained as an incomplete receipt. A separate rerun with explicit subprocess exit capture and JUnit output completed successfully, so the baseline result above uses that second record.

Mypy could not qualify the maintained Python 3.11 gate from this Python 3.12 environment: `sentence_transformers` is absent, and installed NumPy 2.5.3 type stubs use Python 3.12 syntax while the project targets 3.11. This is a lane/dependency limitation, not an asserted product-source type regression. `pip check` reports the omitted required `sentence-transformers` dependency.

## Installation burden and remaining qualification

The ordinary Linux dependency resolver selected 53 additional distributions for the mandatory sentence-transformers closure, including torch 2.14.1, transformers 5.18.0 and CUDA 13 libraries. The recorded `pip --dry-run` unexpectedly downloaded full wheels while resolving: approximately **3,079.7 MB** in its displayed download sizes. This is wheel-transfer size, not installed disk size or model weights. No ML closure was installed and no model weights or inference calls were requested. `full-install-dry-run.json` and its log preserve the exact resolution.

The successor still needs its own exact wheel/environment identity, the frozen path-control replay, full dependency installation plus `pip check`, the required Python 3.11/3.12 maintained lanes, strict mypy on the designated 3.11 lane, and exact CAL consumer intake qualification. Real model smoke is a separate legacy-feature gate when those features are promised; it is not evidence for the deterministic lexical V1 route. Practical retrieval adequacy requires the owner's separately controlled corpus and semantic evaluation programme.

## The CLI surfaces are distinct

| Surface | Actual bounded capability |
|---|---|
| `evidence-bundler` | Existing scaffold-directory path; Markdown/text/PDF ingest, BM25/hybrid and optional reranking/contradiction, review sidecars, refinement, finalization and coverage tooling. |
| `evidence-bundler-v1` | Self-contained Contract A 2.0 JSON with plain text/Markdown sources; fixed lexical 10/3 profile; explicit admission JSON; native package plus Contract B 1.2 projection and receipt. |
| `python -m evidence_bundler.v1` | Separate native package operator surface; configurable depth/retention, default 5/3, explicit not-run and diagnostic options. It is not the fixed installed 10/3 projection route. |

The installed commands reject each other's input shape. The V1 qualification therefore does not inherit the legacy PDF, semantic retrieval, human review workflow or finalization features. Conversely, the existing command does not acquire V1's package/replay guarantees merely because it ships in the same 0.2.0 wheel. `cli-surface-check.json` records the observed surfaces.

All evidence is under `evidence/eb-v1/portable-review/`; no GitHub mutation or product fix was made by this reviewer.
