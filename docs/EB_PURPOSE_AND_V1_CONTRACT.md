# Evidence Bundler purpose and V1 contract

Evidence Bundler prepares evidence for review. It turns a bounded source set and upstream-declared claims into a reproducible package of passage nominations, explicit review decisions, provenance and coverage gaps. A useful workflow finds locally adequate material where the supplied sources provide it and makes missing or inadequate material visible.

This document defines the intended supported boundary. It does not declare a candidate qualified or a stable `1.0.0` release ready. [Issue #132](https://github.com/camerontjs-dot/evidence-bundler/issues/132) owns the changing plan, candidate links and outstanding decisions. [Local acceptance](EB_V1_LOCAL_ACCEPTANCE.md) defines the evidence needed to assess that boundary.

## The reviewed text workflow

The V1 product target is the installed `evidence-bundler-v1` command:

1. Consume a valid Contract A 2.0 declaration containing inline UTF-8 plain text or Markdown and an explicit root or declared `all_of` target.
2. Preserve upstream proposition identity and decomposition. EB retrieves for those declarations; it does not author children or certify their semantic equivalence.
3. Use the fixed depth-10/retain-3 lexical profile to nominate passages and preserve candidate history, source text, spans and retrieval identity. This is a bounded policy, not an optimality or recall guarantee.
4. Let an operator review retained candidates in their claim, source and span context and explicitly record `accepted`, `rejected` or `needs-review` decisions.
5. Preserve the reviewed native package and emit the non-semantic Contract B 1.2 projection with its receipt. Only accepted links become downstream claim evidence.

Unknown or failed decomposition declarations supply no normative retrieval target. A valid declaration with no useful evidence must yield an honest gap, not an invented claim, passage or admission. For `all_of`, adequate evidence for one child does not establish coverage of its siblings.

| State | Meaning |
|---|---|
| Nominated | Retrieval found a candidate relationship. A score is not a support verdict. |
| Retained | The fixed selection policy kept the candidate available for review. Retention is not admission. |
| Accepted | The reviewed passage is materially on-target and locally adequate for subsequent assessment. |
| Rejected / needs review | The relationship was rejected or remains unresolved; it is not silently treated as accepted. |
| Coverage gap | Required material is absent, not retained, inadequate or unresolved. Preserve the actual reason; do not convert it into semantic refutation. |

**Admission does not mean support.** A clear passage contradicting a claim can be valuable admitted evidence. Acceptance does not establish truth, source authority, applicability, evidence completeness, CAL correctness or permission to act.

## Identity, review and output boundaries

The existing admission wire addresses a proposition/passage ID pair. It does **not** bind the reviewer’s decision to target text, a query, the Contract A digest or a native-package digest. The supported workflow must therefore retain a separate review record bound to the exact reviewed input and package, then verify those identities before applying the decisions. Record the resulting admitted package separately: changing admission state changes its identity. Reusing IDs after changing claims or sources must not silently reuse old review authority. This requirement does not add fields to the frozen admission wire.

Retain the native package, Contract B tree and projection receipt together. The native package preserves the complete supplied source set; the compatibility tree contains nominated passages and relevant source profiles. Exact text, offsets and hashes support reconstruction. Internal validation of a self-consistent package is not proof that retrieval executed; preserve the original identity and deterministic replay evidence separately.

The current B1.2 carrier remains explicitly scoped to `integration_candidate_only`. Before promising a stable B projection, decide and document its supported compatibility status and the meaning of its legacy placeholder fields. Do not silently turn those placeholders into upstream authority or downstream semantic evidence.

The filesystem projection must reject inputs it cannot safely represent before emitting artifacts, without rewriting source or proposition identities. Contract A permits opaque nonblank identifiers; a narrower EB filesystem profile is an EB representability boundary, not a new Contract A validity rule. Preserve existing files and output custody. Platform-specific checks do not establish protection against every filesystem or hostile concurrent process.

The supported interface includes CLI behavior, input/output formats, defaults, error and no-output behavior, review identity, deterministic artifact behavior and declared platform/consumer compatibility. Changes to those properties require deliberate compatibility assessment. A package-version change also changes recorded producer identity and needs qualification on the resulting exact artifact.

## Three separate interfaces

| Interface | Scope |
|---|---|
| `evidence-bundler` | Legacy scaffold-directory workflow, including its separately maintained ingestion, retrieval, review, refinement and finalization features. |
| `python -m evidence_bundler.v1` | Native-package operator surface with configurable retrieval and diagnostic options. It is not the installed fixed-profile projection workflow. |
| `evidence-bundler-v1` | The dedicated reviewed Contract A 2.0 text/Markdown workflow defined here: fixed 10/3 retrieval, explicit admission, native package and Contract B 1.2 projection. |

Qualifying one surface does not qualify the others. PDF ingestion, semantic/hybrid retrieval, reranking, automatic claim/decomposition/subject generation, Gate-directed selection, query rewriting and adaptive retention are outside this minimum unless separately brought into its contract and qualified. CAL semantic decisions and downstream operational authorization remain owned downstream.

## Evidence basis and limits

- [Frozen native authority #79](https://github.com/camerontjs-dot/evidence-bundler/tree/4e1f6fe00e7c350b28f52bfea14f1f8988847884) and the [exact #120 promotion design](https://github.com/camerontjs-dot/evidence-bundler/blob/08ca896debd6d16fa21be2f178ed7cbe62395d00/docs/promotion/EVIDENCE_BUNDLER_V1_SLICE_1_20260918.md) establish the bounded integration design. The [installed-CLI receipt](https://github.com/camerontjs-dot/evidence-bundler/pull/120#issuecomment-5742200204) qualifies its exact predecessor for local pipeline use, not a stable release or every successor.
- [The #121 terminal result](https://github.com/camerontjs-dot/evidence-bundler/pull/121#issuecomment-5943839272) records two reviews rejecting all six retained rows for insufficient context. It falsifies admission-only recovery on that frozen packet; it neither proves universal failure nor establishes which correction will work.
- [The #131 custody result](https://github.com/camerontjs-dot/evidence-bundler/issues/131#issuecomment-5976059899) supports the exact pinned verified EB → Contract B → CAL path. It does not certify arbitrary caller-supplied provenance or transfer automatically to changed producers.

These results demonstrate useful preparation machinery and material limits. Stable-release readiness additionally requires the corrective artifact’s engineering checks and demonstrated usefulness for a named workload, with manageable review effort and documented limitations.
