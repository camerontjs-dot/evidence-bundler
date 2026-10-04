# Evidence Bundler V1 local acceptance

Use this ordinary engineering and operator-workflow acceptance route to assess the [reviewed text contract](EB_PURPOSE_AND_V1_CONTRACT.md). [Issue #132](https://github.com/camerontjs-dot/evidence-bundler/issues/132) owns current status and candidate links. Passing this route supplies evidence for a promotion/release decision; it is not itself a `1.0.0` declaration.

## Bind the candidate before execution

The initial corrective subject is [PR #133](https://github.com/camerontjs-dot/evidence-bundler/pull/133), commit `6be9ab4809440365f9fcdf4aafa6b264cdfdf02c`, tree `f9ac8a58457a558205cb06cdcdf7b968784a301a`, version `0.2.1.dev0`. Record the exact wheel hash and acceptance-kit commit before execution. If #132 explicitly selects a later correction, preserve this observation and bind the later subject separately. A branch name or version string alone is insufficient.

Use the public eight-packet kit at [`research/eb_v1_workflow_acceptance_20261004`](../research/eb_v1_workflow_acceptance_20261004), pinned by its manifest. Use `scripts/qualification/run_v1_workflow_acceptance.py` from the acceptance-kit checkout. The kit and runtime are separate checkouts; install the candidate wheel from #133, then run the helper with that installed CLI. Preserve its first result and frozen expectations; do not modify fixtures after seeing the candidate outcome and report the repaired run as the same attempt.

| Boundary | Exact authority |
|---|---|
| Contract A 2.0.0 | [`529c92b49a34d5c610618551a8737f019f9fa332`](https://github.com/camerontjs-dot/apparatus-contracts/commit/529c92b49a34d5c610618551a8737f019f9fa332) |
| Contract B 1.2.0 | [`c314e53bd91c0736aa4370a364673b069aceb43e`](https://github.com/camerontjs-dot/apparatus-contracts/commit/c314e53bd91c0736aa4370a364673b069aceb43e) |
| CAL consumer | [`64b6c7702696c851057c1cf0b2c105b1c81db543`](https://github.com/camerontjs-dot/claim-audit-lab/commit/64b6c7702696c851057c1cf0b2c105b1c81db543) |

Reconcile live ownership before launch, but do not silently replace these subjects. The earlier [#120 receipt](https://github.com/camerontjs-dot/evidence-bundler/pull/120#issuecomment-5742200204) exercised an earlier CAL subject; it does not substitute for this candidate’s consumer check.

## Engineering and installed-artifact checks

Build and install the exact wheel in clean supported Python environments, then run from outside the repository checkout on the owner Mac. Record macOS version, architecture, filesystem characteristics, Python, complete installed dependencies, wheel/source identities and commands. Hosted Linux results and Mac results are separate observations.

Required evidence includes:

- Full dependency installation and a passing dependency-consistency check. A lightweight `--no-deps` environment is useful diagnostic evidence, not complete installation qualification. Measure download/install time, transfer or disk size when available, and unexpected model downloads or inference. Decide separately whether legacy ML dependencies belong in the text-only distribution surface.
- Maintained Python 3.11/3.12 regression and quality checks, with strict typing on the designated 3.11 lane; the installed command’s version, help, error handling and deterministic machine-readable output. Record every skipped test and the claim it leaves unverified.
- The unchanged frozen containment probes and maintained behavior regressions supplied with the corrective candidate. The archived original behavior script pins version `0.2.0` and is a predecessor reproducer, not a drop-in successor gate. Rejections must precede artifact emission and preserve existing files. Check output-directory custody and the documented identifier/alias restrictions on the tested platform without silently changing Contract A or remapping identities.
- Repeated and relocated complete runs with matching expected artifact identities; text/span/hash preservation; honest empty and unresolved results; and tampered/invalid-input rejection. Package validation alone does not attest that retrieval ran.
- Native emitted Contract B validation against the pinned canonical authority and actual pinned CAL intake, including rejected/tampered controls. Retain the native package, projected tree and receipt together. Do not infer CAL semantic correctness from intake acceptance.

## Run the prepared harness

Set `EB_KIT_CHECKOUT` to the exact acceptance-kit checkout, `EB_CANDIDATE_VENV` to the isolated environment containing the exact corrective wheel, and `EB_ACCEPTANCE_RUN` to a fresh absolute directory outside both checkouts. Substitute the measured wheel hash in the subject record. The helper is standard-library test apparatus; its SHA and kit closure are recorded at preparation.

```bash
python3 "$EB_KIT_CHECKOUT/scripts/qualification/run_v1_workflow_acceptance.py" prepare \
  --cli "$EB_CANDIDATE_VENV/bin/evidence-bundler-v1" \
  --subject "commit=6be9ab4809440365f9fcdf4aafa6b264cdfdf02c;wheel=sha256:MEASURED_WHEEL_HASH" \
  --run-dir "$EB_ACCEPTANCE_RUN"
```

Use a fresh reviewer context that has not read this assessment, the saved reviews or evaluation materials. The supervising agent can read prior evidence and prepare the run; do not call that supervisor's own later review cold. Give the reviewer only the kit's `REVIEWER-GUIDE.md`/`OPERATOR-RUN.md`, generated `review-packets/`, and editable `reviews/` files. Corresponding copied input sources are available for documented source inspection; record when they are needed. Keep evaluation materials outside that initial reviewer context. Complete every review, coverage note and measured timing/friction field, then freeze and replay:

```bash
python3 "$EB_KIT_CHECKOUT/scripts/qualification/run_v1_workflow_acceptance.py" replay \
  --run-dir "$EB_ACCEPTANCE_RUN"
python3 "$EB_KIT_CHECKOUT/scripts/qualification/run_v1_workflow_acceptance.py" evaluate \
  --run-dir "$EB_ACCEPTANCE_RUN"
```

Each phase refuses an existing destination. Evaluation exits 0 for a passing synthetic gate, 2 for an acceptance failure with its result preserved, and 1 for an apparatus error. Preserve failures and use a separately identified run after an ordinary repair. Inspect `replay/COVERAGE.json` and `evaluate/RESULT.json`; their coverage summaries are helper-created counts and manual notes, not new EB product features. The separate canonical B/CAL check remains necessary for actual accepted-link semantics.

Install the B/CAL wheels from the exact pinned commits in the candidate environment. Save `INSTALLED-IDENTITY.json` in the run directory with the source commits, wheel hashes, installation receipts and imported payload identities. Then run the separate checker with that environment's Python:

```bash
"$EB_CANDIDATE_VENV/bin/python" -I \
  "$EB_KIT_CHECKOUT/scripts/qualification/check_v1_workflow_consumers.py" \
  --run-dir "$EB_ACCEPTANCE_RUN" \
  --output "${EB_ACCEPTANCE_RUN}-consumers" \
  --installed-identity "$EB_ACCEPTANCE_RUN/INSTALLED-IDENTITY.json"
```

It verifies the frozen output hashes before and after actual consumer intake and requires exact admitted-pair equality for all eight cases. The fresh consumer directory preserves `RESULT.json` and any CAL deviations. Its recorded module versions and expected pins do not by themselves attest which commits are installed; that is why the separate installed-artifact receipt is required.

## Cold reviewed workflow and useful positives

Before the first kit outcome, freeze the candidate, kit, review rubric, permitted operator actions and pass/fail rules. A reviewer sees the declared claim/decomposition and retained passage/source/span context, but not expected decisions or prior candidate results. Freeze the review record before comparing it with the kit’s expectations. This is a cold workflow check, not a claim of context-free scientific independence.

The eight-packet kit must discriminate a useful evidence-preparation workflow from one that rejects everything:

- Every named must-pass positive target must have an adequate retained candidate, including targets whose adequate evidence **contradicts** the claim. Review admission concerns relevance and local adequacy, not support direction.
- Each must-pass `all_of` parent needs adequate evidence for every required child. Wrong-subject and wrong-child passages cannot satisfy that obligation.
- Insufficient qualifiers/context, a missing child, empty sources or sources without adequate on-target evidence, and split-context limitations must remain visible as the expected rejection, uncertainty or gap. Successful packaging is not a positive evidence result.

Review `accepted`, `rejected` and `needs-review` decisions with brief reasons. Bind the record to exact Contract A bytes, target/source identities, configuration, candidate/package identity and admission-file hash. Before applying it, verify that the reviewed input and package are unchanged. The admission JSON itself binds only proposition/passage ID pairs; an external launch/review record must supply the missing snapshot binding. Test stale-review reuse explicitly at the supported workflow boundary: refuse it or require a new review, rather than trusting reused IDs.

Replay reviewed admissions through the installed command. Verify that only addressed retained pairs become accepted, candidate history and gaps survive, and the emitted B links correspond to the exact reviewed evidence. Preserve disagreement or uncertainty under the frozen rule; do not resolve it by changing the desired result.

## Representative workload and burden

The synthetic kit is development acceptance evidence, not a population recall estimate. Before inspecting outcomes on representative material, record a **named first supported workload**: intended operator, source/claim types, packet-selection rule, adequate source witnesses, required `all_of` coverage and permitted manual actions. Freeze packet identities and numerical thresholds for adequate-target yield, complete-parent coverage, mistaken admissions/unresolved cases and review burden, with a rationale tied to that workload. Do not invent a general usefulness threshold after seeing results.

Measure installation, first run, review, admission editing and rerun/handoff time; manual lookups, copying, re-entry, clarification and recovery; and per-packet adequate targets, complete parents, rejects, uncertainty and gaps. Report every case and the first failure. If no suitable representative population or pre-outcome thresholds are available, mark workload usefulness unestablished and finish the available engineering/kit checks. Private packets and review content remain local unless their publication to a specific destination is separately authorized.

## Continue within the product boundary

Ordinary implementation repairs, tests, CI fixes and workflow improvements may continue on a separately identified reversible candidate. Preserve the original failure and use new source/wheel/run identities after changes. Keep source/claim identity, shared contracts and downstream semantics intact; do not weaken frozen probes to obtain a pass. When related reversible workflow improvements need evaluation together, build the bounded integrated candidate, then prune and harden what proves useful.

Preserve [#121](https://github.com/camerontjs-dot/evidence-bundler/pull/121), [#123](https://github.com/camerontjs-dot/evidence-bundler/pull/123), [#124](https://github.com/camerontjs-dot/evidence-bundler/pull/124) and [#130](https://github.com/camerontjs-dot/evidence-bundler/pull/130) under their own frozen protocols, populations, budgets and terminal rules. This kit is not their replacement or a rerun under their names. Automatic root/child/subject production is outside the minimum product contract; #130 remains optional research, not a prerequisite for consuming legitimate upstream declarations.

Finish with exact tested identities, checks and skips, fixture/workload results, timings and friction, original failures, limitations and the smallest concrete remaining blocker. Stop the affected lane for a real protected-boundary change, terminal research result or unresolved product/authority decision; continue unrelated authorized work. Do not insert routine human approval between ordinary steps. Product merge and public release remain separate decisions.

## Paste-ready local task

> Continue the Evidence Bundler work owned by issue #132. Inspect the corrective PR and pin its exact source, wheel and acceptance-kit identities. Using this acceptance contract, qualify the installed reviewed-text workflow on the owner Mac outside the checkout, with complete dependencies, the preserved regression controls and exact Contract B/CAL consumer boundary. Run the cold eight-packet review and prospectively defined representative workload; require adequate positive and counterevidence opportunities, honest gaps and practical review effort. Bind decisions to the exact input/package; the admission wire alone is insufficient. Preserve first failures, private data and the separate research protocols. Continue ordinary in-scope repairs on a new exact candidate without changing shared contracts or downstream semantics. Report observed results, skipped/blocked checks, burden and the next concrete decision; do not claim fixture success alone establishes 1.0 readiness.
