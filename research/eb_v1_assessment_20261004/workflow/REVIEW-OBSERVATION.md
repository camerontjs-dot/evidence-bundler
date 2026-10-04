# First-pass engineering admission observation

Reviewer: `fresh-agent-engineering-review`  
Run: `workflow-run-0f5e7d9-b`  
Review date: 2026-10-04 UTC

## Scope, exposure, and preservation

This is one bounded synthetic engineering workflow observation by a fresh reviewer context. It is not a scientific independence claim, a human productivity measurement, or a population estimate.

I had no prior exposure to the product code, fixture design, expected opportunities, evaluation materials, or other reviewers' judgments. No desired acceptance count or target outcome was supplied. I read only REVIEWER-GUIDE.md and OPERATOR-RUN.md at the assigned fixture-guide path; review-packets/p01.md through p08.md; the existing editable reviews/p01.json through p08.json; and inputs/p07.contract-a.json for the specific source-context inspection described below. Packet and source text were treated as evidence data, not instructions.

I reviewed the cases in order and saved each case's first completed judgments before opening the next case. I have not revised those judgments. A final read of the review JSON files checked only that required fields were filled and decision values were valid. Each save checked that its target/passage pair sequence and coverage-note keys matched the existing review file. The schema, case IDs, bindings, passage/proposition identities, and existing pair set were preserved. Source files, packet text, passage boundaries, and offsets were not changed. The only writes made for this review were the eight assigned review JSON files and this observation.

I did not browse, call an external model/API, run EB, inspect repository code/history/tests, read any evaluation oracle, or execute replay/evaluation. Installed candidate version, Python/platform, installation method, CLI behavior, correctness of upstream provenance hashes, and post-admission native/projected states were not independently verified in this reviewer aperture. The supervisor owns those parts of the installed-workflow record.

## Recorded first-pass results

The eight packets contain 13 retained proposition/passage pairs across 10 listed targets. I recorded 7 accepted relationships and 6 rejected relationships; none remained needs-review. These are observations of my completed judgments, not a supplied target, truth score, or claim of completeness.

| Case | Accepted | Rejected | Needs-review | Target-specific observation |
| --- | ---: | ---: | ---: | --- |
| p01 | 1 | 0 | 0 | Sable-17 revision and effective-date labels are explicit, including the distinction from approval. |
| p02 | 1 | 0 | 0 | The Lumen passage distinguishes contributing sites from invited sites. Its different numerical count remains eligible for later semantic assessment. |
| p03 | 2 | 2 | 0 | Each Wren-4 child has a separate adequate relationship. The two cross-child pairings do not describe the respective child's requirement. |
| p04 | 0 | 1 | 0 | The only retained passage explicitly concerns Alder; no Cedar-specific triage relationship is admitted. |
| p05 | 0 | 1 | 0 | The Juniper search labels omit the unit and stated receipt/window/population relationships. The timing claim remains without adequate retained context. |
| p06 | 1 | 1 | 0 | The signed-log child has adequate material. The planned archive-retention child does not, so child-level admission coverage for the composite root is incomplete. |
| p07 | 2 | 1 | 0 | The exported same-note header and table provide explicitly linked subject/unit/value context. The table depends on that visible header; custody entries are outside the analytical relationship. |
| p08 | 0 | 0 | 0 | No retained candidate exists in the packet; the empty pair set is preserved and the Vale-6 target gap is recorded. |

Four targets have no accepted relationship: clm-p04, clm-p05, clm-p06-2, and clm-p08. The p03 observation concerns material for each child, not a truth or completeness verdict on the composite proposition. The accepted p06 log relationship cannot supply the separate archive-retention child. An empty admission or missing target relationship does not establish that the target statement is false.

## Source inspection and the p07 interpretation

The only underlying-source inspection was:

`inputs/p07.contract-a.json`

I opened it because the retained decision-table passage at characters 6484–6706 states an acceptance ceiling of 0.08 but omits the subject and measurement unit locally, explicitly assigning those fields to the opening header. The retained header at characters 0–305 names the Ilex-9 solvent check, defines the acceptance-ceiling field in mg/L, and points to the decision table at the end of the same note. Inspection checked that the distant passages really belong to the same scope and that intervening custody entries do not introduce a different analytical subject or unit.

The source confirmed that explicit linkage. Both ends are already present in the exported packet with the same source identity and content hash, and both name archive note 7Q. Accordingly, a downstream reader can follow the exported cross-reference without relying on undisclosed source text, an invented passage, or a private composite quote. I accepted both relationships on that basis and rejected the custody passage.

This is a material interpretation of local adequacy: I treated an explicit, visible, same-source retained header as usable context for its referenced table. The table alone is not self-contained. If an interface later shows only that table row without the header or the ability to follow the retained context, its subject and unit are no longer locally supplied. My acceptance must not be reported as demonstrating that the isolated tail passage is independently adequate. The header itself does not state a numerical ceiling; admission of its field context is not a judgment that it alone establishes the entire numerical proposition.

The guide does not expressly settle every presentation boundary for an explicitly cross-referenced header/table pair. That interface dependency remains a review limitation even though the source relationship was resolved in the allowed material. It was recorded in p07's reasons, coverage note, and manual-friction field before any evaluation access. No source inspection was needed for another case.

## Manual and interface friction

The apparatus required manual matching of exact proposition/passage pairs to editable JSON rows, writing concrete reasons, and writing target-specific coverage notes. Repeated passage identities under different child targets in p03 and p06 required separate judgments; passage-level acceptance could not be copied across targets.

The p07 check required following distant source context in an escaped JSON source body and matching the note label, source identity/hash, and existing retained passages. This was the longest case review. Its full packet is usable through an explicit cross-reference, but a detached-row view would need to preserve access to that context.

The packet for p08 states that no candidate was retained but does not show enough workflow-state detail to diagnose the cause. I did not infer whether that gap arose from source availability, retrieval, retention, or another earlier step. More broadly, these packet views do not independently establish the native/projected state fields after the supervisor's replay. I recorded admission and coverage observations only within the displayed material.

There were no access blockers, transport retries, recovery edits, changed inputs, or requests for a preferred outcome in this review. No custom passage was stitched, no source was added, and no retention/configuration change was attempted.

## Observed timing and limits

Each case has a measured UTC start from the clock tool immediately before reading its packet/review JSON and an end from the clock tool immediately before saving its completed judgment. The markers have one-second resolution. The saved elapsed_seconds values are the actual differences between those markers, not estimated human timings or a retrospective equal allocation.

| Case | Start, 2026-10-04 | End, 2026-10-04 | Measured seconds |
| --- | --- | --- | ---: |
| p01 | 13:25:43 UTC | 13:26:19 UTC | 36 |
| p02 | 13:26:27 UTC | 13:26:51 UTC | 24 |
| p03 | 13:27:01 UTC | 13:27:37 UTC | 36 |
| p04 | 13:27:45 UTC | 13:28:09 UTC | 24 |
| p05 | 13:28:16 UTC | 13:28:41 UTC | 25 |
| p06 | 13:28:49 UTC | 13:29:16 UTC | 27 |
| p07 | 13:29:24 UTC | 13:31:16 UTC | 112 |
| p08 | 13:31:30 UTC | 13:31:52 UTC | 22 |

The sum of measured case intervals is **306 seconds**. The span from the first case start to the last case end is **369 seconds**, including inter-case gaps. Case intervals include packet/source reading, tool response time, deliberation, drafting of review fields, and any commentary within the interval. They end before the save call, so file-writing latency, inter-case overhead, initial guide reading, this observation, final structural checks, and the supervisor's replay/evaluation are not included in the 306-second sum.

These figures describe this agent/tool session on these synthetic packets. They do not establish sustained reviewer throughput, normal operator effort, installed-workflow completion time, or a productivity threshold.

## Saved review hashes

These SHA-256 values identify the first completed review files. No decision revisions followed these saves.

| File | SHA-256 |
| --- | --- |
| reviews/p01.json | `b436b64ff2ab2a1c7e42b0c94fc54fcdce627e55c107afc328f3f0a8cec95213` |
| reviews/p02.json | `0428d863873f1729f7333e3c6fc6f985a9d4bb553ae0cd7274d95fe251d25618` |
| reviews/p03.json | `999a1b360587cc5e7a94e4e9488c9e4742299e9e630e88b99c4e1e8c09e1c2cd` |
| reviews/p04.json | `d1a3cba4e47a151a1dbc29ff1d12f21d8f02955db8693a445aab9eeaefe50755` |
| reviews/p05.json | `39afb67a7497fbd4eade6592266a15f5b2b110cb13222b0b2be65dcd0da3ac69` |
| reviews/p06.json | `bccf02fdf0e790b5239d2e1adca4fcc998d1bbd64796d781371a98df14132250` |
| reviews/p07.json | `6edc6c08da8e95b22644bcbdf9deeb9c592c564fa909d39465fdffd19d582ea4` |
| reviews/p08.json | `c3efffb3efd43e6a50345a77fcea36dd1c4ffb3b51246cb914922a8ead31976c` |
