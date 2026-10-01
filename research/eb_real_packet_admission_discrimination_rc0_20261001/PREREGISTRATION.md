# EB real-packet admission discrimination RC0 — preregistration

## Status

`PREREGISTERED_NOT_EXECUTED`

This cycle asks one smaller question before any retrieval or admission mechanism is changed:

> On the exact retained candidates already produced by Evidence Bundler V1 `0.2.0` for the frozen ERS-free real packet, can a bounded EB-side admission review distinguish at least one positively admissible passage from at least one non-admissible passage without using CAL semantics?

The result is allowed to be negative. Zero accepted candidates is a falsifier, not a reason to tune the review rule or retrieval after exposure.

## Decision

Decide whether the next research step should remain at the admission boundary or move back upstream to retrieval.

A positive RC0 result would establish only that the frozen retained set contains real admission headroom and that the existing explicit V1 admission seam can carry that review reproducibly. It would not qualify automated admission.

A zero-positive result would falsify the admission-only explanation for this packet and make retrieval the next live question.

An unstable review or a weak-control tie would leave the mechanism question `INCONCLUSIVE`.

## Live authority and pinned subject

Live GitHub was re-read on 2026-10-01 before this preregistration.

### Evidence Bundler

- repository: `camerontjs-dot/evidence-bundler`
- PR #120: open Draft, unmerged
- exact local-pipeline subject: `08ca896debd6d16fa21be2f178ed7cbe62395d00`
- package / CLI version: `0.2.0`
- production base recorded by PR #120: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- released Contract B: `1.2.0` at `c314e53bd91c0736aa4370a364673b069aceb43e`

This branch is research-only and is stacked on the exact PR #120 subject. `src/evidence_bundler/v1/**`, the V1 runner, configuration, compatibility carrier, and Contract B are protected from mutation.

### Predecessor research

PR #119 is closed, Draft, unmerged. Its terminal disposition remains:

`SUPPORTED_SUBJECT_ONLY; COMBINED_FORM_INCREMENT_NOT_REPRODUCED`

The supported successor concept was:

```text
semantic top-3
→ child / all_of coverage
→ exact claim-native subject identity
```

It was not frozen for production. This RC0 does not implement it.

Expected-evidence-form routing, specialty/generic form repair, keyword/predicate lists, evidence-derived entities, query rewrites, source/domain routing, support/refute hints, answer values, opaque weighted fusion, and promoted scope remain outside the causal mechanism.

### Frozen real-packet baseline

Apparatus Contracts PR #153 records the ERS-free real-packet baseline.

Scientific authority:

- preregistered execution head: `1cc9efc52fa591846af473ee165a643f9ac41c22`
- evidence head: `ab4e354dda1af73e5ff56b38e87884e8e1180680`
- disposition: `SUPPORTED_FOR_BOUNDED_ERS_FREE_REAL_PACKET_BASELINE`

Publicly bound packet identities:

- frozen Gate input packet SHA-256: `8abd8b98eeec1bdc6cb9f1f0be0870fbf9ecdcfc6c1c3b8de76c2267636a44e2`
- reviewed Contract A file SHA-256: `8a4a42b57020d710b0e68a57fac5d31d8a977e75bde2c7d535a656bacefabb41`
- Contract A handoff identity: `b59ba3b35d2b1d8b0378ac277703cd4a8867ec1e88b8ea34be577df0c3eeb843`
- target-review manifest SHA-256: `df4eb5b84fb9b1f65a9a7f8245397d85a1b2aff6b19c3f5a456d83a6c5fc0903`
- target 1 SHA-256: `416811675261a1f12e2c4c5ebd3d8fdaf769def57a3fea6fe0ca5a26b270a4c4`
- target 2 SHA-256: `22797d998748039a7aa582c997b6727c1d2f11c01a009a82cf508104cd051aaf`
- baseline EB native package identity: `sha256:8240ca5845b883068c1c9ba6a02e415989fb8d5162664024936d02e677bbd791`

Observed baseline:

- 20 candidate relationships
- 6 retained
- 0 accepted
- no admission override supplied
- CAL returned `not_checkable`
- Decision returned `hold`
- required replay identities were byte-identical

The CAL and Decision observations are not optimization targets and do not participate in this RC0 decision gate.

PR #153 also records that no second eligible reviewed real packet was found in the inspected local scopes. RC0 therefore has one packet and six retained candidates. That is a limitation, not hidden sample size.

## Competing explanations

### H1 — admission headroom exists

The frozen six retained candidates contain both candidates that are suitable for downstream semantic assessment and candidates that are not. The zero accepted baseline is primarily the consequence of no explicit admission review being supplied.

### H2 — retrieval is already the bottleneck

None of the six retained candidates is adequate for positive admission. If observed, changing admission behavior would be result-chasing. The next research question must return upstream to retrieval.

### H3 — apparent admission discrimination is a cheap shortcut

A review may appear useful while merely reproducing nomination rank. The preregistered rank-1-per-target weak control is intended to expose this case.

### H4 — the review rule leaks CAL's job upstream

A procedure may obtain positive decisions only by deciding support, refutation, truth, applicability, or source authority. That would violate the EB/CAL boundary and does not count as support for this experiment.

## Admission meaning in this experiment

EB `accepted` means only:

> The candidate passage is materially about the proposition and contains enough local context for a downstream semantic auditor to make a meaningful proposition-specific assessment from the supplied evidence.

It does **not** mean:

- the passage supports the proposition;
- the passage refutes the proposition;
- the proposition is true or false;
- the source is authoritative;
- the source is applicable;
- the evidence set is complete;
- CAL should return a particular conclusion.

Review decisions use the existing V1 vocabulary:

- `accepted` with reason `on_target_adequate`;
- `rejected` with reason `wrong_target` or `insufficient_context`;
- `needs-review` with reason `uncertain`.

No support/refute label is collected.

## Frozen review aperture

Before either primary review:

1. Verify the exact baseline package identity above.
2. Verify exactly 20 candidates, 6 retained, and 0 accepted.
3. Freeze the retained set and a private alias mapping.
4. Produce a private review packet containing only:
   - opaque candidate alias;
   - proposition text;
   - passage text.
5. Hash-bind the private mapping and review packet in a public freeze receipt.

The reviewer packet must not expose:

- nomination rank;
- selection/admission state;
- retrieval score;
- CAL output;
- Decision output;
- PR #119 result labels or expected selector behavior.

Private source, target, and passage bytes remain local. Only hashes and aggregate results may be committed publicly.

## Reviewer separation

Use exactly two primary reviewer artifacts from distinct fresh reviewer sessions.

Each reviewer receives only the frozen rubric and the same frozen review packet. Record reviewer/model/config identity locally where material.

This protocol claims only the separation actually achieved. A different session is not automatically a clean-room independent reproduction. If the stronger context-free requirements are not met, the result must be described as `separate fresh review`, not `independent reproduction`.

There is no post-reveal adjudication in RC0. Any exact decision disagreement is terminal `INCONCLUSIVE` for this cycle.

## Weak controls

Three controls are fixed before review exposure:

1. **No-admission control:** accept zero retained candidates.
2. **Admit-all control:** accept all six retained candidates.
3. **Rank-1-per-target control:** accept only the rank-1 retained candidate for each primary target.

The rank control is intentionally hidden from reviewers.

A positive review set must differ from the rank-1 accepted set. If it does not, the apparatus has not shown that the bounded review adds relationship/admission discrimination beyond a cheap rank shortcut.

## Primary falsifier

The primary falsifier is:

> After two exact-agreement reviews of the frozen six retained candidates, zero candidates are `accepted`.

Disposition: `FALSIFIED`.

Bounded interpretation:

`ADMISSION_ONLY_FALSIFIED_FOR_FROZEN_PACKET`

Do not alter the rubric, add a new reviewer, reroll the packet, enlarge K, or change retrieval after observing this result.

## Support conditions

All of the following are required before the bounded positive result may be assigned:

1. both reviewer artifacts bind to the exact frozen review packet;
2. the two reviewers give exact matching decisions and reasons on all six candidates;
3. at least one candidate is `accepted`;
4. at least one candidate is not `accepted`;
5. the consensus accepted set differs from the rank-1-per-target weak control;
6. an explicit V1 admission sidecar is generated only from the frozen consensus;
7. two exact EB `0.2.0` replays with that sidecar are byte-identical;
8. after normalizing retained `admission_state`, the admitted packages are identical to the no-admission baseline, so nomination, rank, retention, passage bytes, and other V1 state did not change;
9. the emitted Contract B `1.2` artifacts validate under the exact released Contract B authority;
10. CAL and Decision outputs are not used to pass, fail, tune, or adjudicate the experiment.

If all hold, the primary research disposition may be:

`SUPPORTED FOR PROMOTION`

with bounded result:

`BOUNDED_POSITIVE_ADMISSION_DISCRIMINATION`

This means the existing explicit admission seam has bounded positive real-packet evidence. It does not authorize automated admission, selector promotion, a Contract change, a CAL change, a version change, merge, or release.

## Inconclusive conditions

The primary disposition is `INCONCLUSIVE` if any of these occur:

- the two primary reviews disagree on any exact decision/reason;
- all six candidates are accepted, leaving no positive/negative discrimination headroom;
- the consensus accepted set is exactly the rank-1-per-target weak control;
- the review aperture cannot be established as frozen before review;
- the admission replay changes state outside retained `admission_state`;
- the result depends on support/refute/truth/applicability judgments that belong to CAL.

A harness or environment failure that prevents the frozen experiment from running is `BLOCKED`, not a scientific result.

## Attempt budget and stop rule

- one frozen real packet;
- one frozen retained set;
- exactly two primary reviewer artifacts;
- one consensus evaluation;
- if supported, two explicit-admission EB replays;
- no reviewer replacement or adjudication after decisive exposure;
- no retrieval mutation in RC0.

Stop when a support condition, falsifier, inconclusive condition, or authority/environment blocker is observed.

If RC0 supports admission headroom, the next experiment may ask whether an automated admission candidate can reproduce the frozen review under a separately frozen and appropriately isolated protocol.

If RC0 falsifies admission-only, the next experiment may test the smallest retrieval variant justified by PR #119, starting with child coverage plus exact claim-native subject identity and keeping expected-evidence-form machinery out.

## Protected surfaces

This research branch must not modify:

- `src/evidence_bundler/v1/**`;
- `scripts/run_v1_integration_candidate.py`;
- `config/eb_v1_slice/**`;
- Contract B `1.2`;
- PR #120 head or branch;
- CAL semantics;
- Contract C or D;
- release/version/tag state.

Research-only apparatus, tests, receipts, and a Draft research PR are allowed.

## Required terminal record

A terminal result must preserve:

- base and final SHAs;
- public freeze receipt and hashes of private review inputs;
- reviewer-artifact hashes;
- exact aggregate decisions and weak-control outcomes;
- admission sidecar hash if support is reached;
- two replay package identities;
- Contract B validation receipt;
- failures/deviations;
- observed evidence;
- inference;
- remaining hypotheses and unknowns;
- explicit non-claims;
- primary research disposition.

Do not update PR #120 as though RC0 changed the frozen `0.2.0` implementation. If the result is material to its evidence basis, add a bounded evidence pointer only after RC0 reaches a terminal state.
