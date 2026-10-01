# EB real-packet admission apparatus A1

Research Infrastructure successor of [PR #121](https://github.com/camerontjs-dot/evidence-bundler/pull/121), stacked on exact blocked head `aad7206f49c94714f4664dccf4b32daa6039cb50`. A1 repairs only the baseline hash-domain check. The original [scientific preregistration](../eb_real_packet_admission_discrimination_rc0_20261001/PREREGISTRATION.md) remains unchanged and authoritative.

## Preserved failure

The [first freeze failure](https://github.com/camerontjs-dot/evidence-bundler/pull/121#issuecomment-5939968146) ran this command at the predecessor head:

```bash
python research/eb_real_packet_admission_discrimination_rc0_20261001/admission_discrimination.py \
  freeze --package <exact-pr153-native-eb-package.json> --out-dir <fresh-private-rc0-dir>
```

It exited 1 with:

```text
ApparatusError: baseline package identity mismatch: expected sha256:8240ca5845b883068c1c9ba6a02e415989fb8d5162664024936d02e677bbd791, got 'sha256:b9ddf8ecb735a31ba50011832bc462a4bd9c97ebc9105d537c9bfad8bfea16ba'
```

The predecessor compared a raw-file digest with a valid intrinsic payload digest. That blocked result, its command/stderr receipts, and all earlier apparatus deviations remain preserved. A1 does not turn that attempt into a successful run.

## Identity domains

| Binding | Frozen expected identity |
| --- | --- |
| Raw native package file | `sha256:8240ca5845b883068c1c9ba6a02e415989fb8d5162664024936d02e677bbd791` |
| Intrinsic payload / embedded `package_sha256` | `sha256:b9ddf8ecb735a31ba50011832bc462a4bd9c97ebc9105d537c9bfad8bfea16ba` |
| Contract A handoff | `sha256:b59ba3b35d2b1d8b0378ac277703cd4a8867ec1e88b8ea34be577df0c3eeb843` |
| Frozen EB subject, version `0.2.0` | `08ca896debd6d16fa21be2f178ed7cbe62395d00` |

A1 binds the exact raw file, requires canonical V1 serialization, checks the embedded intrinsic identity, and recomputes the intrinsic digest with `package_sha256` omitted under the unchanged V1 definition. It preserves 20 candidates, six retained, and zero accepted. No private input is rewritten or resealed.

The apparatus stays at its original research path. A1 receipts and mappings use distinct `rc0-a1-v1` schemas and carry both `baseline_raw_file_sha256` and `baseline_intrinsic_package_sha256`. Evaluation and replay require both bindings. Replay receipts separately name the admitted raw and intrinsic identities. The review packet schema, rubric, alias ordering, candidate fields, and admission sidecar schema remain unchanged.

## Qualification boundary

Before the exact private freeze, commit the apparatus, tests, and controls, then freeze the branch, commit/tree, apparatus/tests blobs, all expected identities, predecessor head, scientific preregistration blob, and relevant CI receipts. `CANDIDATE.json` identifies the source commit; the external pre-execution freeze record binds the final manifest commit and CI.

The committed synthetic tests cover:

- positive preserved-shaped input with independent raw and intrinsic hash oracles;
- a serialization substitution that preserves decoded semantics but fails the raw binding;
- a changed and consistently resealed payload rejected by the frozen raw and intrinsic bindings;
- a forged embedded digest rejected by intrinsic recomputation;
- raw-to-intrinsic, intrinsic-to-raw, and swapped expected-value cross-wiring;
- an intentionally conflated predecessor validator that fails the same positive freeze gate the corrected validator passes;
- canonical serialization, each evaluator identity binding, rank leakage, retained-set tampering, stale outputs, exact reviewer rows, zero-positive/disagreement/admit-all/rank-1 gates, admission-only replay invariance, and raw-byte replay inequality.

Synthetic tests bind synthetic expected identities before mutation. The forged-digest and noncanonical controls additionally isolate inner gates by rebinding only the synthetic outer raw expectation. The decisive private invocation uses the committed real-packet constants without overrides.

Only after this freeze, run the committed CLI once against the exact preserved baseline in a fresh private directory. Verify the public receipt and the private mapping/review packet mechanically without displaying their contents. Record all three raw artifact hashes, counts, both native identities, intrinsic recomputation, Contract A identity, canonical serialization, field aperture, and unchanged protected bytes.

> **Binds:** A1 apparatus qualification and its evidence record.
> **Tier:** T0 for the one-run/no-edit procedure; identity and artifact checks are detected by the committed apparatus and tests.
> **Check:** frozen synthetic CI, one exact private `freeze`, and hash-bound execution receipts; no generic enforcement of reviewer nonexecution is claimed.
> **Escape:** preserve the first qualification failure and stop; any repair requires a separately identified successor. Do not edit frozen A1 after private qualification exposure.

## Disposition and continuation

`SUPPORTED FOR RC0 EXECUTION` is eligible only if the corrected implementation passes, the conflated control fails for the intended domain reason, all required controls pass, the preserved package reaches the original review boundary, and no private content leaks or scientific/protected surface changes occur. If both implementations pass, the apparatus result is `INCONCLUSIVE`.

This task stops at that boundary. It starts no scientific reviewer, consumes no reviewer judgment, and emits no scientific admission result or sidecar. Original RC0 execution may use a supported frozen A1 only under explicit continuation authority for the unchanged preregistration. The blocked #121 record remains intact; a bounded successor pointer may be appended after qualification.

This establishes apparatus executability only. It does not establish EB promotion, admission headroom, retrieval quality, CAL/Decision correctness, automated admission, production readiness, or permission to merge, tag, release, or change version/Contract behavior.
