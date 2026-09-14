# Codex Serialization Harness RC0 — Execution 01 Trace-Classifier Deviation

Status: preserved apparatus failure; no Evidence Bundler scientific inference.

## Failed qualification attempt

- execution commit: `54a6e05b10250842d97deb6c77cd5d23aa6fb42a`
- execution ID: `20260914T153828Z-dd52a2d5`
- installed Codex: `codex-cli 0.154.0`
- deterministic self-test: PASS
- completed qualified runs: `0 / 12`
- terminal harness status: `HARNESS_ERROR`
- stopping error: `ValueError: expected exactly one completed agent message, got 2`

The preserved first child trace contains two completed `agent_message` events with different roles in the execution stream:

1. an ordinary status message before the authorized read command: `I’ll read the two authorized files and return the required JSON object.`;
2. one schema-shaped JSON result after the authorized command completed.

The RC0 validator incorrectly classified every completed `agent_message` as a final result and therefore rejected a normal status-plus-result Codex trace before it evaluated the result/final-file identity.

This is an evaluator/apparatus defect. It is not evidence that schema-constrained 96-key serialization passed or failed.

## Correction boundary

The corrected validator does not simply accept the last message. It now requires:

- exactly one authorized completed child command;
- no forbidden trace item types;
- one or more completed agent messages may exist;
- ordinary non-result status messages are allowed;
- any result-shaped message must itself pass the full duplicate-key-aware structural and deterministic-value validator;
- exactly one result-shaped agent message must exist;
- the unique result-shaped message must be the final agent message;
- it must match the `--output-last-message` file exactly;
- a malformed result-shaped message, a second result-shaped message, or status text after the result remains a hard failure.

The synthetic self-test is expanded to cover:

- status message followed by one valid result: PASS control;
- duplicate result-shaped messages: reject;
- result-shaped message not last: reject;
- malformed result-shaped message followed by a valid result: reject;
- all pre-existing duplicate-key, missing/extra ID, invalid/wrong-label, wrong-reviewer, and forbidden-command controls.

## Rerun rule

Execution 01 remains preserved and is not counted toward qualification.

A successor qualification attempt, if operator-authorized, must start a fresh execution ID and run a complete new `12 / 12` cohort. No child from execution 01 may be reused or selectively resumed.

Even a successful harness qualification does not automatically resume Evidence Bundler RC1. PR #74 remains paused pending an explicit post-exposure continuation decision.
