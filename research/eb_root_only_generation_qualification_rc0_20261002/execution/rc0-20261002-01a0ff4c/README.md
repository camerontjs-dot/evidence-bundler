# Public root-only generation RC0: BLOCKED

This execution stopped before semantic calibration. The one profile-writing invocation returned frozen artifacts that exclude the required `uncertain` review decision and omit the decisive row/root-status wire. The one independent custody invocation exhausted its 8,192-token output allowance and returned incomplete JSON. Its checker was not executed. Generation capability remains **UNKNOWN**.

The [public receipt](PUBLIC-RECEIPT.json), [profile prerequisite check](PROFILE-PREREQUISITES.PUBLIC.json), [custody terminal receipt](CUSTODY-TERMINAL.PUBLIC.json), and [final attempt ledger](ATTEMPT-LEDGER.FINAL.PUBLIC.json) record the bounded result. All [twelve case statuses](CASE-STATUS.PUBLIC.json) are `NOT_RUN`. No target failure, target abstention or semantic pass was observed.

## Exact authority

- Starting PR #125 envelope: `0988ee8756ce595477695d0cd451fb8d82002e88`.
- Authoritative `CANDIDATE.R1.json` source: `1c94cb82262d6346cf4aef35ff50d8d70c4aacb3`; tree `fb629ae75b9924ebfa5968f1862648a788f33639`.
- Profile and transport checkpoint: `d66a95a9507ecaf2d51a6041b9e3a14b1c205017`; tree `255adb87b8cdfafcf7d23685a4c98eaa57adaf97`.
- Protected main: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`; protected EB subject: `08ca896debd6d16fa21be2f178ed7cbe62395d00`.
- PR #124 envelope: `bc3d887f27991c215e251875b964f205e478df21`; inherited source: `af9cebf187cc5e1f96683bfa1366c6641ea0139c`.

[Identity closure](IDENTITY-CLOSURE.PUBLIC.json) reproduces all 17 R1 source/history/workflow blob and raw hashes and all three inherited blob identities. The original setup closure, original candidate and original receipt remain intact. This directory adds execution artifacts; it does not replace setup history.

## What physically ran

| Budgeted operation | Consumed | Result |
| --- | ---: | --- |
| Profile writing | 1/1 | Six returned files extracted verbatim and frozen; prerequisites incomplete |
| Evaluator calibration | 0/2 | NOT_RUN |
| Root-only generation | 0/12 | NOT_RUN |
| Deterministic weak generators | 0/3 | NOT_RUN; zero of 36 planned weak records produced |
| Decisive reviews | 0/2 | NOT_RUN; no 48-row packet produced |
| Consensus/scoring tally | 0/1 | NOT_RUN |
| Independent custody session | 1/1 | Partial output at length limit; verification unavailable |

The writer and custody session used the local raw API at `http://127.0.0.1:11434/api/generate`, service version `0.34.4`, reported model `qwen3.5:9b`, reported digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`. Requested input and output allowances were 32,768 and 8,192 tokens. The reported digest remained unchanged after writing and during custody. The primary/evaluator runtime and research qualification adapter remain unbound.

The [writer route freeze](WRITER-ROUTE-FREEZE.PUBLIC.json) binds the four bootstrap sources, raw request and transport code. The observable request contains those sources and runtime facts, with no history, tools, cases, controls or oracle supplied. Raw mode's documented behavior is described in the [Ollama API documentation](https://docs.ollama.com/api/generate). That interface evidence does not establish an independently verified effective internal token sequence or exact backend weights; those remain `UNKNOWN`. Operational isolation remains `UNVERIFIED` after the incomplete custody attempt.

## Native evidence and failures

Writer native response SHA-256: `472f07a0ddb27c4b184aa9da5a7a41259ad086638b877f8c5224fe64bf513917`. [Request](writer/REQUEST.native.json), [response](writer/RESPONSE.native.json), [verbatim output](writer/OUTPUT.raw.txt), [byte freeze](PROFILE-FREEZE.PUBLIC.json), and [unchanged profile files](profiles/) are preserved.

Custody native response SHA-256: `2c7f1477c75f5a14e22e7d64edf79a9dd1ff6f9202d89a921567c186c67a1a46`. Its [allowlist](CUSTODY-SCOPE.PUBLIC.json), [request](custody/REQUEST.native.json), [response](custody/RESPONSE.native.json), and [partial output](custody/OUTPUT.raw.txt) are preserved. The response reports `done_reason: length`, 17,379 prompt tokens and 8,192 generated tokens. Its JSON decoder found an unterminated string. No repaired output or replacement role was used.

The first upstream filename lookup failure, corrected hand-entered receipt time, archived-PR-body formatting rejection, and temporary-file storage failure remain separately recorded. The latter interrupted a metadata-only probe; existing native receipts survived. No unrelated files were removed. Original archived body bytes remain reconstructable from the JSON history record. These packaging observations do not qualify semantic generation or custody.

The structural prerequisite checker is a preparation check. Its mode/field detection is an implementation choice; it is not a new general schema contract. The explicit omission of `uncertain` from both returned decision constraints conflicts directly with the frozen profile-writing task. No profile was edited to satisfy the check.

## Limits and next boundary

Weak-system discrimination and all four metamorphic relations remain `NOT_RUN`. There are zero observed valid explicit or inherited subject outputs because generation never began. Inherited-subject generation is `INHERITANCE_NOT_EXERCISED` and unqualified.

Only a separately authorized public successor may resolve the incomplete profile configuration and custody envelope. It requires a fresh allowlisted writer and complete frozen review/configuration artifacts before case/control exposure. This execution's writing and custody attempts cannot be repaired or rerolled. Its remaining scientific budgets are not permission to bypass the failed prerequisites.

PR #124 remains separately blocked. Its original gates and attempt budgets are unchanged and unconsumed. Private root transmission, population construction, corpus access, retrieval, passage review, production changes, merge, release and promotion remain outside this result.
