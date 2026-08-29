# External Corpus Source-Access Isolation Assurance — Results

## Terminal disposition

**SOURCE ACCESS ASSURED**

Bounded authorization only: a new genuinely fresh Pilot 0A completion may begin at Gate 1 using the assured reader. This does not authorize retrieval execution, reuse of a contaminated Pilot context, or construction/execution of a 24–30-case apparatus.

## OBSERVED

- Live production `main` at task start was `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`.
- PR #25 was opened as a draft Research Infrastructure PR from that exact base.
- The preserved PR #24 acquisition implementation called `ParquetFile.iter_batches()` without `columns=...` and then converted full batches to Python rows. Output-only key filtering therefore occurred after row deserialization.
- The new reader accepts only explicit logical requests resolved through `field_registry.json` and never accepts wildcard or `columns=None` access.
- Before the first row batch is read, every supplied Parquet file is schema-preflighted and its exact safe physical leaf projection is resolved.
- Row materialization has one audited surface: `ParquetFile.iter_batches(..., columns=<resolved leaves>, use_pandas_metadata=False)`.
- Parent-struct projection is rejected when it would select nested descendants beyond an exact allowed leaf.
- Successful receipts record the actual call arguments and returned batch field paths. In the normal synthetic receipt, the physical schema contained nine forbidden tripwire fields while the physical read call requested only `query_id`, `query_title`, and `query_text`; returned batches contained only those three fields and `forbidden_columns_deserialized` was `false`.
- The nested fixture contained `metadata.evidence`; the receipt identified it as forbidden while returned batches still contained only the three allowed query fields and `forbidden_columns_deserialized` remained `false`.
- Explicit forbidden request, wildcard request, `columns=None`, missing required field, empty allow-list, corrupt Parquet, malformed schema, unsafe parent projection, projected-API failure, and multi-file schema drift all fail closed in the behavioral suite.
- Multi-file schema preflight completes before the first file is materialized, so a later drifted file cannot trigger partial earlier row exposure.
- The projected-API failure control records the actual keyword arguments supplied to `iter_batches` and verifies no unprojected fallback occurs.
- Static controls reject unprojected `iter_batches()`, unprojected `read_table()`, `read_pandas()`, `to_pylist()` in the audited access path, high-level dataset loading, and direct Parquet imports/calls outside the safe reader. The final static scope is `research/**/*.py`.
- Final workflow run `33255140441` at head `0a1f0579a77b0430df6d6b06f4bbb7e55b3cd1e8` completed successfully. The JUnit result was 30 tests, 0 errors, 0 failures, 0 skipped. The deterministic dummy runner was 14/14. Static assurance reported zero findings across `research/**/*.py`.
- The final pinned runtime was Python `3.11.16`, PyArrow `17.0.0`; reader SHA-256 was `88f12f5998b729aa3ecee808925849837f98a8dd202f6fa2e419e90c091a1ed2`.
- Official Apache Arrow documentation states that `ParquetFile.iter_batches(columns=[...])` reads only the listed columns, and warns that a parent name is a prefix selecting nested descendants. `pyarrow.parquet.read_schema` is documented as reading the effective Arrow schema from Parquet file metadata.
- Run 1 (`33255026317`) failed at pytest collection because the script entry point did not make the repository namespace importable. Zero behavioral tests executed. That failed run is preserved. The only correction was invoking the same frozen test module with `python -m pytest`; no reader or field-contract criterion was changed for that deviation.
- A later hardening step widened the static guard from its local module to all research Python callers and added two direct-bypass controls. The reader and field registry did not change.
- The optional real-artifact probe was not executed. No real scientific rows were read.
- A genuinely separate MainFrame/Conduit reviewer could not be established because the available surface returned HTTP 429. `INDEPENDENT ACCESS REVIEW NOT ESTABLISHED`.
- The branch diff through the assured code head adds only a research workflow, research records, and `research/source_access_firewall/`; production `src/`, production dependency declarations, retrievers, and frozen Pilot 0A case files are unchanged.

## INFERENCE

The audited reader enforces the relevant row-deserialization firewall for the bounded PyArrow 17 path: the only row-materialization API receives an explicit safe physical leaf projection, the Arrow API contract says only those columns are read, returned batch schemas are checked against the resolved projection, unsafe/fallback paths fail closed, and a repository-wide research guard makes casual direct Parquet bypass visible.

The successful result therefore supports the narrow gate that was actually asked: a future fresh Pilot 0A can acquire permitted query/source fields through this reader without first hydrating qrel/relevance/answer/evidence/candidate/retrieval fields as row values.

This does not establish scientific benchmark validity, source provenance, gold stability, passage stability, evaluator independence, retrieval quality, or any production retrieval capability.

## HYPOTHESIS

A fresh Pilot 0A using this reader will reach scientific Gate 1 without reproducing PR #24's full-row deserialization contamination mechanism, provided all external Parquet access remains behind this interface and any new physical field authorization is preregistered before exposure.

## UNKNOWN

The strongest remaining technical alternative is narrower than the row-materialization claim: `pyarrow.parquet.read_schema` is documented as deriving schema from Parquet metadata, and the synthetic assurance fixtures disable Parquet statistics, but this task does not establish a low-level theorem that PyArrow's internal footer parser can never transiently parse value-bearing statistics or custom key-value metadata in an arbitrary future real artifact. The optional real-artifact structural probe was deliberately not used to chase that question because doing so was not necessary to validate the row projection boundary and could enlarge exposure.

Independent access review is also not established. That limits the review-independence claim, not the observed local mechanical gate.

## Alternative-explanation audit

1. **Projection occurs only after row materialization — FALSIFIED for the audited path.** The projection is an argument to the physical `iter_batches` read call, and Arrow documents that only specified columns are read.
2. **A high-level library silently reads all columns — FALSIFIED for the audited path.** No high-level dataset loader is used; static controls reject it.
3. **Schema inspection itself materializes row values — NOT OBSERVED; bounded residual UNKNOWN at metadata-parser internals.** `read_schema` returns schema from metadata and the synthetic fixtures carry no statistics. Arbitrary real footer internals were not independently instrumented.
4. **Nested forbidden fields bypass top-level checks — FALSIFIED by controls.** Recursive field paths identify `metadata.evidence`; exact leaf projection succeeds without it; unsafe parent projection fails before reading.
5. **Aliases/renames bypass the deny-list — FALSIFIED for registered aliases and undeclared names.** Registered `rel_ids` is forbidden; an unknown renamed field is reported but unread because it is not allow-listed.
6. **Multi-file schema drift introduces exposure after partial reading — FALSIFIED by preflight control.** All files are schema-resolved before any `physical_read_calls` entry is emitted.
7. **Exception/fallback switches to unprojected reading — FALSIFIED by projected-API failure control.** Failure terminates with no fallback.
8. **Debug/output logging exposes forbidden values — FALSIFIED for the reader surface and synthetic run.** The reader has no row logging surface; tripwire values were absent from captured output and successful returned objects.
9. **Receipts describe intended columns rather than the physical call — FALSIFIED within the audited Python boundary.** The receipt is created at the same call site that passes `columns=...`; an adversarial fake `ParquetFile` independently captured those actual keyword arguments.
10. **Later callers can casually bypass the safe reader — materially reduced and currently FALSIFIED across the research tree.** Static assurance scans `research/**/*.py` and rejects direct Parquet imports/calls outside the audited reader; final scan had zero findings.

## Exposure state

No prohibited scientific value was intentionally inspected, printed, persisted, compared, or used. No FreshStack qrel/nugget/relevance/candidate/retrieval result, SciFact evidence/rationale annotation, prior scientific gold, or frozen ten-case content was materialized. No BM25, Hybrid, Semantic-only, dense, lexical, reranking, or substitute retriever was run.

## Deviations

### D-001 — local runtime unavailable
The local analysis runtime lacked PyArrow and could not resolve packages externally. Decisive behavior testing moved to a pinned GitHub Actions runtime. Contract, reader, fixtures, and criteria were unchanged.

### D-002 — workflow run 1 collection failure
Run `33255026317` executed zero behavioral tests because the `pytest` script invocation could not import the repository namespace. The run is preserved. The correction changed only invocation to `python -m pytest` and allowed later assurance stages to run even if an earlier step failed.

### D-003 — static scope hardening
After run 2 passed, alternative #10 showed that guarding only the reader module was weaker than the task required. The static guard was widened to `research/**/*.py` and direct caller-bypass tests were added. The source reader and access registry remained unchanged. Runs 3 and 4 passed the widened control.

## Optional real-artifact structural probe

**NOT EXECUTED.** The local assurance does not rely on inspecting the real FreshStack Parquet schema or any real scientific row. A future fresh Pilot may perform only the bounded schema/file-identity work allowed by its Gate 1 protocol through this reader; any need to deserialize prohibited values remains a fail-closed stop.

## Independent review

**INDEPENDENT ACCESS REVIEW NOT ESTABLISHED.** A separate Conduit launch surface was unavailable due HTTP 429. No simulated independence claim is made.

## Exact authorization

The only authorization from this result is:

> Begin a new genuinely fresh Pilot 0A completion from Gate 1 using the assured source-access reader and frozen field registry.

Not authorized:

- retrieval execution of any kind;
- reuse of prior contaminated Pilot contexts;
- modification/materialization of the frozen ten cases outside the future Pilot's authorized gates;
- a 24–30-case apparatus;
- production promotion of retrieval behavior.

## Smallest next task

Start a genuinely fresh Pilot 0A thread/context, pin the merged/accepted source-access reader identity, begin at Gate 1, and require every external Parquet access to produce a successful access receipt before any scientific case reconstruction. Stop immediately if an external access path cannot stay behind the reader or a prohibited scientific value is exposed.
