# EB real-packet admission discrimination RC0

This directory is research-only apparatus for the preregistered admission question in [PREREGISTRATION.md](PREREGISTRATION.md).

It does not modify Evidence Bundler V1 runtime behavior. The scientific subject remains PR #120 at `08ca896debd6d16fa21be2f178ed7cbe62395d00`.

## Private/local execution sequence

The decisive packet, target, passage, mapping, and reviewer bytes stay local.

### 1. Freeze the no-admission baseline

```bash
python research/eb_real_packet_admission_discrimination_rc0_20261001/admission_discrimination.py \
  freeze \
  --package <exact-pr153-eb-native-package.json> \
  --out-dir <private-rc0-dir>
```

The command fails closed unless the package reproduces the preregistered V1 package identity, Contract A handoff, 20 candidates, 6 retained candidates, and 0 accepted candidates.

It writes:

- `FREEZE-RECEIPT.PUBLIC.json`, safe to consider for publication after path/content review;
- `PRIVATE-MAPPING.json`, local only;
- `PRIVATE-REVIEW-PACKET.json`, local only.

Do not commit the private mapping or review packet.

### 2. Obtain exactly two separate primary reviews

Each reviewer receives only the frozen rubric and `PRIVATE-REVIEW-PACKET.json`.

Each review artifact has this shape:

```json
{
  "schema": "eb-real-packet-admission-review-rc0-v1",
  "review_packet_sha256": "sha256:<exact packet hash>",
  "reviewer": "<distinct local reviewer identity>",
  "decisions": [
    {
      "candidate_alias": "candidate-01",
      "decision": "accepted",
      "reason": "on_target_adequate"
    }
  ]
}
```

Every frozen alias must appear exactly once.

Allowed decision/reason pairs:

- `accepted / on_target_adequate`
- `rejected / wrong_target`
- `rejected / insufficient_context`
- `needs-review / uncertain`

Do not add support, refutation, truth, source-authority, applicability, CAL, or Decision labels.

### 3. Evaluate the frozen reviews

```bash
python research/eb_real_packet_admission_discrimination_rc0_20261001/admission_discrimination.py \
  evaluate \
  --freeze <private-rc0-dir>/FREEZE-RECEIPT.PUBLIC.json \
  --mapping <private-rc0-dir>/PRIVATE-MAPPING.json \
  --packet <private-rc0-dir>/PRIVATE-REVIEW-PACKET.json \
  --review <review-one.json> \
  --review <review-two.json> \
  --summary-out <private-rc0-dir>/RESULT-SUMMARY.PUBLIC.json \
  --admission-out <private-rc0-dir>/admission.json
```

The evaluator enforces the preregistered falsifier and weak controls. A positive review gate records `CONTINUE_TO_REPLAY` and emits the existing admission sidecar, but it is not a terminal `SUPPORTED FOR PROMOTION` result.

### 4. Replay the exact V1 subject twice

If and only if the review gate supports the bounded result, run the existing exact PR #120 V1 path twice with the generated admission sidecar.

Then verify the native packages:

```bash
python research/eb_real_packet_admission_discrimination_rc0_20261001/admission_discrimination.py \
  verify-replay \
  --baseline <exact-pr153-eb-native-package.json> \
  --run-one <admitted-run-one-native-package.json> \
  --run-two <admitted-run-two-native-package.json> \
  --admission <private-rc0-dir>/admission.json \
  --receipt-out <private-rc0-dir>/REPLAY-RECEIPT.PUBLIC.json
```

The replay verifier requires byte-identical admitted packages and proves that, after normalizing retained `admission_state`, no other native V1 state changed.

### 5. Validate Contract B 1.2 externally

Terminal support still requires both emitted Contract B artifacts to validate under the exact released Contract B `1.2` authority at `c314e53bd91c0736aa4370a364673b069aceb43e`.

That cross-repository validation is deliberately not simulated by this local research script.

CAL and Decision outputs are not part of the RC0 gate.

## Public apparatus controls

The committed synthetic tests exercise:

- rank-blinded freeze construction and hash binding;
- positive mixed admission with a rank-1 weak-control miss;
- the zero-positive falsifier;
- the rank-1-equivalence inconclusive case;
- reviewer-disagreement inconclusive behavior;
- admission-only replay invariance.

These tests validate the apparatus logic. They are not evidence about the private real packet.
