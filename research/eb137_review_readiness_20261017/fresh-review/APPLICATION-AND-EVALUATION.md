# Frozen application and evaluation instructions (supervisor only)

This is not reviewer input. Controlling authority is EB PR #137 comment 5982684493, reproduced without modification in GOVERNING-FRESH-REVIEW-PROTOCOL.md. Preserve the original #134 kit, oracle and helper bytes.

## Preconditions
The content manifest freezes the candidate wheel, full installed runtime, exact eight A2 inputs, generated reviewer-only surfaces, evaluator sources and rubric. It is NOT an execution admission. Before launch, a separately attributable reviewer and its actual model/version, permitted effective tools, prior-context aperture and launch/access receipt must be admitted. No qualified reviewer mechanism has been identified here. An ordinary source-filled development container, fresh session ID or self-attestation is insufficient. Never give the reviewer this folder's supervisor files or the owning issue/PR.

Only the 17 files in reviewer-only/ may enter the reviewer context. A custodian must enforce and record this allowlist, retain first decisions and actual actions/timing, and stop for contamination. Synthetic raw lookups are not allowed by this gate. Freeze the returned records and receipt before opening the evaluator to the reviewer or evaluating the results.

## Bound application
For every p01..p08, verify the original input, wheel, configuration, unreviewed-package and review-record bindings against CONTENT-FREEZE.json. Verify every retained pair appears exactly once, no other pair appears, all reasons are nonblank, and no field except decision/reason has changed. Preserve rejected and needs-review alongside accepted decisions.

Run the installed CLI outside every checkout, with a fresh output directory per case:

```sh
"$EB_CANDIDATE_VENV/bin/evidence-bundler-v1" run   "$EB_FRESH_PACKET/inputs/p01.contract-a.json"   --review "$EB_REVIEW_RETURN/p01/review_record.json"   --out-dir "$EB_REPLAY_OUTPUT/p01"
```

Repeat in frozen p01..p08 order. Do NOT run the old acceptance helper's replay subcommand: it invokes unbound --admission and does not establish this gate. Do not convert returned records into admission-wire files.

Verify exact applied_review_record.json preservation and compare native before/after using the unchanged #134 helper check_replay function with the returned decision map. Require review-accepted pair identity == native accepted pairs == actual pinned CAL admitted pairs. The unchanged check_v1_workflow_consumers.py check_case function performs the native-to-canonical-B/CAL leg; the reviewer-to-native equality is a separate required check, not inferred from B validation. Preserve all native, projection, review, integrity and consumer bytes and before/after hashes. Repeat the pre-existing stale-review no-output and tamper controls separately from the reviewer decisions.

## Adequacy and unchanged numerical gates
The unchanged #134 helper gate function covers its five mandatory positive opportunities and four mandatory gaps. Its always-accept and always-reject fabricated controls must fail. This numerical gate does not itself enforce p07 or determine passage adequacy. The recorded fabricated p07-positive control shows that transfer limit; it does not invalidate the older #134 result.

Apply the already-required #137 overlay: p07 must have zero accepted passages when no single admitted span is locally adequate. Do not combine the subject/unit from its opening span with the value from a separate span or display context to confer individual passage adequacy. Inspect all accepted passages from admitted text alone under the frozen rubric. Compare sufficient source opportunities without requiring one arbitrary witness span where a legitimate alternative exists. Record unresolved disagreement as INCONCLUSIVE rather than changing an expectation. For p03, both required children must have adequate evidence; p06 must remain incomplete when its missing child lacks evidence.

These are the existing #137 conditions, not changed thresholds or a repaired #134 evaluator. The full guide and exact helper/evaluator identities are pinned in CONTENT-FREEZE.json. Do not count source inspection by this informed supervisor as the fresh blinded review.

## Terminal states
Use SUPPORTED_FOR_REVIEWED_WORKFLOW_PROMOTION only after every required semantic, information-boundary and consumer condition passes. Use FALSIFIED_REVIEW_CONTEXT_BOUNDARY for a valid exposed semantic-boundary failure, APPARATUS_INVALID for an invalid aperture/binding/evaluator, and INCONCLUSIVE for a genuinely unresolved result. A valid frozen failure ends that candidate attempt. A repair requires a distinct successor and applicable review protocol. None of these results establishes workload usefulness, authenticated human review, human speed, carrier stability, release approval or general CAL correctness.
