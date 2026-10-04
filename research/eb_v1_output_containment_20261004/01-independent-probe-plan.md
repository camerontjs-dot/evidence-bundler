# Independent portable engineering probe plan

Recorded before reading candidate runtime implementation or author tests.

## Subject and authority

- Maintained baseline: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`.
- Exact product/local-pipeline candidate: `08ca896debd6d16fa21be2f178ed7cbe62395d00` (package 0.2.0).
- Detached worktree: `/workspace/scratch/e4a384da02ee/eb-portable-candidate`.
- Repository and ancestor `AGENTS.md` checks found none.
- Requirements read: candidate `README.md`, `docs/promotion/EVIDENCE_BUNDLER_V1_SLICE_1_20260918.md`, its manifest, `config/eb_v1_slice/INTEGRATION_PROFILE.json`, and explicit compatibility carrier. No author tests or runtime implementation have been read at this point.
- This is independent portable engineering verification. Synthetic inputs exercise software properties only; they are not semantic truth, retrieval-recall, corpus-completeness, or source-legitimacy evidence.

## Independent requirements and probes

| ID | Declared or necessary software property | Independent probe / expected result |
|---|---|---|
| P01 | Installed 0.2.0 CLI exposes the exact frozen 10/3 route and packaged carrier outside the repository | Build wheel, install in isolated environment, run `inspect --json` and a synthetic complete run from an unrelated working directory; verify package version/config/authority/carrier identities. |
| P02 | Intake binds the exact Contract A 2.0 source set and bytes before retrieval | Positive bounded sources; wrong source digest; missing source; duplicate/ambiguous identity; unsupported contract version. Invalid intake must fail before a successful package is produced. |
| P03 | A bounded source set cannot silently acquire outside content | Relocate the complete input; remove or change declared source bytes; examine symlink/path traversal behavior where the input contract permits paths. Source bytes and identity in output must correspond to declared sources. |
| P04 | Depth-10 nomination, rank-3 retention, and explicit admission are distinct | Construct enough lexical candidates to exceed depth and retained limits. Inspect complete nominations, stable rank/tie behavior, exact retained count, default admission state, and explicit admitted versus unadmitted outcomes. Reject admission for unknown or unretained IDs. |
| P05 | Identical authorized inputs have deterministic, relocation-safe artifact identity | Run twice, then relocate the complete native artifact/input and validate/project again. Compare canonical identities and file hashes, allowing only fields explicitly declared non-identity-bearing. |
| P06 | Native evidence identity survives exact non-semantic Contract B projection | Compare IDs, excerpts, source hashes, state/provenance and factual-context inventory across native and projected artifacts; inspect compatibility values for clearly separated authority. |
| P07 | Integrity validation fails closed under substitution/tamper | Modify candidate excerpt, source hash/bytes, nomination/admission/retention state, manifest/index/receipt, and carrier independently. Native validation/projection and projection verification must reject inconsistent substitutions; record any unsupported control surfaces. |
| P08 | Output paths cannot corrupt input or produce silently reusable partial artifacts | Exercise existing nonempty output path and failure after output initialization; identify atomicity/refusal behavior. This is a pressure check; distinguish a product defect from an undocumented convenience feature. |
| P09 | Candidate preserves maintained behavior and frozen runtime identity | Verify baseline ancestry and frozen blob/profile/carrier pins; run relevant V1 and maintained portable regression tests without provider/model/corpus-authoring execution. Record skipped/external-only gates. |

## Execution discipline

- Use isolated worktrees/environments; never edit candidate product code, frozen tests, or scientific records.
- Build independent probe inputs from the declared schemas after freezing this plan. Reading schemas and public API implementations for valid input construction is permitted after this record.
- Keep exact commits, source/config hashes, dependency versions, command logs and positive/negative probe outcomes.
- Run the smallest meaningful controls; broaden only to resolve concrete uncertainty.
- Report bounded defects promptly to the root reviewer. Do not change GitHub state.
- Separate portable conclusions from tests still needing the owner's controlled cross-repository/model/source environment.
