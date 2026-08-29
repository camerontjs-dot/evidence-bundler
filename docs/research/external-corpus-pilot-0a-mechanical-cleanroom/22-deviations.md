# Deviations

## D1 — governance record lookup unavailable

The task required six named CAL Pipeline governance records to be read first. Exact-name/path searches through the available GitHub connector did not locate them. No local/MindGraph or prior-chat copy was substituted because this execution was required to be fresh and repository-authoritative.

**Handling:** the exact PR #20 preregistration plus the stricter current clean-room contract governed the run. This limitation is preserved and no claim is made that the named governance corpus was re-read.

## D2 — overbroad PR-search surface before exclusion

An early GitHub pull-request search intended to find PR #20 also rendered bodies for PR #20, #21, #22, #23 and an unrelated PR #5.

**Exposure assessment:** no historical retrieval metric value, FreshStack result table, FreshStack candidate list, FreshStack qrel value, or SciFact published evidence label was rendered. PR #22/#23 contributed procedural contamination descriptions only. The surface was excluded from later predecessor inspection.

**Scientific effect:** non-terminal deviation by itself.

## D3 — evaluator isolation unavailable

MainFrame/Conduit returned an MCP SSE HTTP 404 before an independent evaluator session could be created.

**Handling:** evaluator B was not simulated and predecessor same-context evaluator B was not relabeled independent. `INDEPENDENCE NOT ESTABLISHED`.

## D4 — terminal source-acquisition firewall violation

The intended source-only FreshStack query reader used `ParquetFile.iter_batches()` without a column projection, then converted complete rows to Python objects. The pinned FreshStack `DataLoader` source shows that the query dataset contains the `nuggets` field from which qrels/relevant corpus IDs are constructed.

The harness did block forbidden keys from output/persistence, but **output filtering is not access isolation**. Qrel-bearing data had already entered process memory before the filter.

**First affected execution:** Actions run `33253126024`, head `2b1cbb7e00a67138384e15ce547b9be87630380a`.

**Scientific effect:** terminal `FALSIFIED` under the absolute firewall. Published FreshStack qrel exposure before gold freeze = `true` at the acquisition-process level. Qrel values were not rendered to the model/user and were not intentionally used, but the contract makes access itself sufficient.

## D5 — execution continued before D4 was recognized

Because the harness printed/persisted only allow-listed fields, the machine-level access was initially mistaken for clean isolation. A second fail-soft source run and subsequent source diagnostics were performed before the violation was caught in final audit.

**Handling after detection:** all material produced after the first qrel-bearing deserialization is marked contaminated/post-exposure diagnostic only. FreshStack revision/row-count discrepancies and SciFact archive reproduction from those runs are not characterized as clean scientific gate evidence.

## D6 — correct post-falsifier boundary

After D4 was recognized, no further corpus investigation, historical-revision search, passage materialization, adjudication, qrel comparison, or retrieval execution was performed. Only durable-record correction and PR metadata updates were allowed.

## Successor control implied by D4

A future source-access harness must enforce allow-listed column projection **before deserialization**, fail closed if that projection cannot be proven, and include an access-level test demonstrating that forbidden qrel/answer/evidence/result fields never enter process memory. A fresh scientific execution is required after that assurance.
