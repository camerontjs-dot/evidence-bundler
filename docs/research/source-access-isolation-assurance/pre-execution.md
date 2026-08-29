# External Corpus Source-Access Isolation Assurance — Pre-Execution Record

## Task class
Research Infrastructure / information-isolation assurance.

## Decision
Determine whether the external-source reader can enforce the scientific firewall at the physical Parquet deserialization boundary, rather than merely redacting output after full-row loading.

## Live starting state

- repository: `camerontjs-dot/evidence-bundler`
- production `main`: `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`
- assurance branch: `research-infra/source-access-firewall-assurance`
- PR #20: closed / unmerged; head `357fe735067dbbd3d54f8872ffc8391dac724950`
- PR #21: open / draft / unmerged; head `764144f3da77140a8e542158948b4e88d40a7421`
- PR #22: closed / unmerged; head `4d91e7a3de78981e4f73489aab179767c58c1914`
- PR #23: closed / unmerged; head `a24542a32acb4f3c04da2dd5bfd8aeaa63123769`
- PR #24: closed / unmerged; head `412f4cfa2e01e92072d6eafdd6c8cfbaa4603507`

## Authority identities

Durable CAL Pipeline governance defines procedure and evidence boundaries. GitHub live state and exact commits define mutable repository/experiment state.

PR #24 is used only for its preserved procedural falsifier: its FreshStack query path invoked `ParquetFile.iter_batches()` without a `columns` projection and then converted those full batches into Python rows. Output-key filtering therefore occurred after the firewall boundary had already been crossed.

No post-exposure corpus row-count, revision diagnostic, scientific content, qrel value, or relevance judgment from #24 is imported into this assurance.

## Source-access contract

### FreshStack query Parquet
Required and allowed logical fields:

- `query_id`
- `query_title`
- `query_text`

No wildcard exists. Any additional field requires an explicit registry change in a separately inspectable commit.

### Source/corpus Parquet
The separate registry permits only source reconstruction/provenance fields:

- source identifier;
- source text;
- source URL;
- start/end byte offsets;
- source commit identity.

Allowed physical aliases are explicit. Parent-struct projection is forbidden when it would select nested descendants beyond the requested leaf.

### Forbidden before scientific gold freeze
The registry denies qrel/relevance, nugget, answer, accepted-answer, evidence/rationale, candidate-list, retrieval score/rank/result, and leaderboard/result-metadata surfaces, including explicitly registered aliases.

## Mechanical boundary

The audited reader must:

1. obtain schema metadata before row materialization;
2. resolve requested logical fields only through the frozen allow-list;
3. reject missing, ambiguous, undeclared, wildcard, forbidden, and parent-struct requests;
4. preflight all files before the first row batch is read;
5. call `ParquetFile.iter_batches(..., columns=<explicit leaf projection>, use_pandas_metadata=False)` with no unprojected fallback;
6. verify returned batch field paths exactly match the resolved projection;
7. emit a deterministic receipt for success and fail-closed outcomes.

## Synthetic fixture policy

Behavioral assurance uses synthetic Parquet only. Forbidden tripwire fields contain an obvious sentinel beginning `FORBIDDEN_TRIPWIRE_DO_NOT_DESERIALIZE`. Synthetic fixture generation disables Parquet statistics so the schema-only preflight is not tested against value-bearing column statistics.

## Preregistered adversarial controls

At minimum:

- normal projected read;
- physical-column reorder;
- extra unknown column;
- missing required allowed column;
- forbidden present but not requested;
- forbidden explicitly requested;
- wildcard request;
- `columns=None`;
- empty allow-list;
- nested forbidden field;
- exact nested leaf projection with forbidden sibling;
- unsafe parent-struct projection;
- dictionary/serialization variation;
- multiple row groups;
- multiple files;
- multi-file schema drift before first materialization;
- registered forbidden alias;
- unknown renamed field;
- malformed schema;
- corrupt Parquet;
- projected API failure with no fallback;
- static rejection of unprojected `iter_batches()`;
- static rejection of unprojected `read_table()`;
- static rejection of `read_pandas()` / full-row `to_pylist()` in the access module;
- static rejection of a high-level dataset loader.

## Acceptance

`SOURCE ACCESS ASSURED` requires observed physical projection before row materialization, complete synthetic/adversarial pass, fail-closed unsafe paths, static bypass detection, successful receipts with `forbidden_columns_deserialized = false`, and zero prohibited scientific exposure.

## Falsifiers

`FALSIFIED` if any forbidden field can enter a materialized returned batch, any fallback becomes unprojected, the physical call lacks explicit columns, library behavior contradicts the projection claim, or prohibited scientific content is exposed.

`INCONCLUSIVE` only if the relevant projection/isolation property cannot be verified in the available runtime.

## Alternative explanations under test

1. projection occurs only after row materialization;
2. a high-level library silently reads all columns;
3. schema inspection itself crosses the prohibited row-value boundary;
4. nested fields bypass top-level controls;
5. aliases/renames bypass the deny-list;
6. multi-file drift introduces a forbidden or missing field after partial execution;
7. exceptions trigger an unprojected fallback;
8. debug/output surfaces leak tripwire values;
9. receipts describe intended rather than actual projected calls;
10. later code can casually bypass the narrow reader.

## Independent review state before execution

A separate MainFrame/Conduit surface was attempted and returned HTTP 429 before an isolated reviewer session could be established.

`INDEPENDENT ACCESS REVIEW NOT ESTABLISHED`

No independence claim will be simulated.

## Exposure log at freeze

- FreshStack qrel values exposed in this assurance: `false`
- FreshStack nuggets exposed in this assurance: `false`
- FreshStack relevance/non-relevance IDs exposed in this assurance: `false`
- FreshStack candidate/retrieval-result values exposed: `false`
- SciFact evidence/rationale annotations exposed: `false`
- prior scientific gold exposed: `false`
- production BM25 executed: `false`
- Hybrid executed: `false`
- Semantic-only executed: `false`
- dense/lexical/reranking/substitute retrieval executed: `false`
- frozen Pilot 0A ten cases materialized: `false`

## Deviation before execution

The current local analysis runtime does not have PyArrow available and cannot install packages because outbound package resolution is unavailable. The decisive synthetic behavior check is therefore assigned to a pinned GitHub Actions runtime. This changes the execution venue, not the frozen contract, fixtures, or acceptance criteria.

## Production impact

None intended. All code is under `research/source_access_firewall/` plus a research-only workflow and research records. No production dependency, `src/` behavior, retriever, canonical contract, or frozen Pilot 0A object is changed.
