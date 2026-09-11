# Evidence Bundler V1 Convergence Decision — 2026-09-11

**Disposition:** `NOT_READY`

**PR:** #60 — `Convergence: Evidence Bundler V1 candidate`

This record closes the bounded convergence pass. It is not release, merge, tag, or promotion authorization.

## Exact implementation freeze

The maintained V1 implementation was frozen for qualification at:

- commit: `c4e3f97ec8f0bd36180954c3aa382418925bf947`
- released Contract A commit: `529c92b49a34d5c610618551a8737f019f9fa332`
- canonical Contract A validator blob: `42e5f5b3bf38d677445e9d01ea130ba604e53409`

Subsequent documentation commits do not widen the tested V1 implementation surface.

## Architecture retained

The convergence candidate keeps the smallest architecture supported by the prior research record:

1. released Contract A 2.0 is the authoritative proposition/decomposition/source input;
2. a declared `all_of` decomposition yields one normative retrieval lane per exact declared child;
3. positive `not_decomposed` yields one root lane;
4. `unknown` and `failed` are not reinterpreted as `not_decomposed`;
5. root retrieval on a declared decomposition is disabled by default and, if explicitly requested, is isolated as a non-normative diagnostic lane;
6. the maintained lexical retriever is deterministic in-repository Okapi BM25 with `k1=1.5`, `b=0.75`, and the pinned lowercase-word tokenizer;
7. candidate nomination, deterministic retention, and explicit admission remain separate durable states;
8. pre-retention candidate history is preserved through the configured candidate depth;
9. source, passage, query, retrieval, configuration, Contract A, and whole-package identities are content-bound;
10. the V1 package is an Evidence Bundler-owned immutable evidence-world package, not a CAL semantic result.

Contract B remains a separately governed inter-apparatus projection/conformance boundary. The V1 package does not make the research Contract B successor a production dependency and does not carry the old Contract B 1.2 compatibility carrier as native architecture.

## Maintained CI

Initial PR-triggered CI run `34607670835` exposed one Python 3.11 strict-mypy annotation omission in `src/evidence_bundler/v1/package.py`. Python 3.12 was fully green. Commit `f8f452eb995c79757b5d67da0d35f002a501bc30` added the missing tuple annotation only; V1 behavior was unchanged.

Exact frozen implementation/qualification head run `34608721697`: **PASS**.

- Python 3.11: install, Ruff, strict mypy, pytest, compileall, pip-check — PASS.
- Python 3.12: install, Ruff, pytest, compileall, pip-check — PASS.

## Contract A conformance

The convergence qualifier independently compared the maintained V1 Contract A consumer with the canonical released validator over the frozen valid qualification inputs and bounded invalid mutations.

Observed canonical agreement: **PASS**.

Covered invalid mutations included stale proposition text/hash, noncontiguous child sequence, duplicate source identity, unknown top-level field, stale source-content hash, and stale whole-object hash.

## Bounded retrieval-default discriminator

No retrieval grid or broad architecture search was run. The preregistered sequence was exactly:

`5/3 -> 10/3 -> 10/6 if needed`

where the first number is candidate depth and the second is retained K.

The cohort was the existing eight-case qualification set plus the exact preserved lexical-decoy aperture counterexample from CAL PR #91.

### Preserved evaluator deviation

Qualifier run `34608317231` is retained as apparatus-invalid for the decoy successor comparison.

- artifact: `10266029533`
- digest: `sha256:0800c7d5d618ac0142094c6839f1f1a0f4fb80533f1978e140b88d55e37ffc18`

The receipt showed the true S6 source at rank 7 under `10/3`, but the cross-era evaluator attempted to recover the old passage ID by full-passage equality even though V1 deterministically chunks the long source. No EB behavior was changed. The evaluator bridge was narrowed to the exact frozen source ID plus exact decisive sentence.

### Decisive retrieval result

Corrected run `34608721684`:

- artifact: `10267561504`
- digest: `sha256:86283d446726f4c5d430d87bfec642427a099575b9f7e1de9835f74b2060b4f9`
- terminal discriminator state: `UNRESOLVED_AT_AUTHORIZED_BOUND`

Observed:

| Profile | Preserved true evidence `RET-AP-P6` | Result |
|---|---|---|
| `5/3` | outside candidate pool | candidate-aperture loss reproduced |
| `10/3` | rank 7 | candidate aperture widened successfully, but evidence lost at retention |
| `10/6` | rank 7 | evidence still lost at retention |

The frozen eight-case qualification set showed no required-evidence regression under the widened profiles. The known `C03-P2`, `C06-P1`, and `C08-P2` candidate/retention/admission localization controls remained reconstructible.

Per preregistration, the experiment stopped at `10/6`. No `10/7`, larger grid, reranker change, or other retrieval tuning was performed.

### Retrieval disposition

No tested successor profile closes the demonstrated aperture defect within the authorized bound. Therefore no new retrieval default is qualified by this convergence pass.

The candidate retains its existing `5/3` configuration as an implementation default only. It is **not** promoted here as an evidence-backed V1 production default.

## Score-recording decision

The V1 package records deterministic nomination rank and stage transitions but intentionally omits raw BM25 score.

That omission survived the bounded convergence pass because:

- the retriever identity, tokenizer, parameters, and configuration are pinned;
- package reconstruction depends on durable rank/stage/provenance state rather than scalar relevance interpretation;
- raw BM25 scores were preserved in the qualification receipt and were sufficient to diagnose the rank-7 counterexample;
- no concrete package-level audit or reconstruction loss attributable to score omission was observed.

This does not make BM25 score semantically authoritative. A future change should add score to the package only if a concrete reproduction/audit requirement demonstrates that rank plus pinned retriever identity is insufficient.

## Independent CAL structural consumption

A separate CAL research/integration consumer was built on Draft PR #102. It pins the exact EB implementation freeze and imports neither Evidence Bundler implementation code nor CAL semantic machinery in the consumer.

Decisive PR-event run `34609582180`: **PASS**.

- CAL research head: `75caf92e017470c879207ea31970fbf63fe8e6fc`
- artifact: `10267173191`
- artifact digest: `sha256:58cddddac7648970cffabea20023bf77516ec4fa635b9804f4aee7cf97da799f`
- produced EB package: `sha256:f3633a34a21f739731d617ca9acf9b6bd65e68e02af29431d667621d1bcd5858`

The independent consumer reconstructed:

- exact proposition IDs, texts, and text hashes;
- normative `declared_child` lanes;
- accepted evidence only;
- exact source IDs and content hashes;
- exact passage IDs, bytes, hashes, and character coordinates;
- aperture state;
- admission state.

It consumed no EB-authored support/refutation/verdict semantics.

All seven resealed adversarial mutations were refused:

1. proposition-text substitution;
2. normative-lane substitution;
3. passage-byte substitution;
4. query-identity substitution;
5. non-retained admission laundering;
6. aperture-state substitution;
7. injected verdict authority.

Two earlier CAL apparatus/evaluator deviations are preserved on PR #102: a missing producer-side `rank_bm25` dependency before package production, and an ineffective aperture mutation that wrote the already-observed aperture state. Neither required a change to the frozen EB implementation.

## What the evidence supports

The convergence pass supports the narrower claim that the frozen EB V1 package architecture is coherent, maintained-CI clean, Contract-A-conformant within the tested aperture, content-bound, and independently structurally consumable by CAL without semantic-authority leakage.

## What the evidence does not support

This pass does not establish:

- a qualified production retrieval default that closes the known lexical-decoy counterexample;
- universal or perfect recall;
- source truthworthiness or corpus completeness;
- CAL semantic correctness;
- authoritative automatic decomposition;
- root `all_of` semantic composition;
- Contract B successor promotion;
- Contract E / Authorization;
- operational execution;
- universal minimality of the package or retrieval architecture.

## Readiness decision

**`NOT_READY`**

The blocker is specific: the only authorized retrieval-default discriminator did not close the preserved retrieval failure. Structural package qualification passed; retrieval-default qualification did not.

This is not a reason to reopen broad Evidence Bundler architecture research. It is a bounded unresolved V1 limitation. Any successor work on retrieval requires a separately justified operator decision rather than automatic continuation from this PR.

No merge, release, tag, or promotion is authorized by this record.
