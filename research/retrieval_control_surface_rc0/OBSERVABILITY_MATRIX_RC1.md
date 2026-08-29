# Retrieval Arm Observability Matrix RC1

Status: Research Infrastructure. Characterization remains unauthorized until this branch passes its full workflow and exact pinned-model smoke.

| Field / mechanism | Classification | Discriminating evidence |
| --- | --- | --- |
| `retrieval_method` | experimental | Existing BM25/semantic/hybrid execution tests exercise distinct paths. |
| `top_k` | experimental final-output budget | Existing retrieval tests and writer behavior bind final parent selection. |
| `parent_candidate_top_k` | research-only experimental intermediate budget | `test_parent_candidate_budget_mutation_changes_parent_aggregation_limit` spies the actual parent aggregation limit while final `top_k` is fixed. |
| `child_top_k` | BM25-only experimental child budget | Existing BM25 tests exercise the child query budget. |
| `lexical_score_floor` | experimental | Existing retrieval tests use score-floor changes to suppress lexical candidates. |
| `chunk_max_chars`, `chunk_overlap_chars` | experimental geometry | RC0 geometry mutation changes chunk ids and ordered chunk-set hash. |
| embedding model + revision | experimental identity | RC0 loader propagation, immutable revision validation, manifest mismatch tests, and exact real-model smoke. |
| `semantic_child_top_k` | experimental | RC0 semantic-budget mutation changes semantic pre-fusion candidates. |
| `semantic_query_prefix` | experimental | RC1 test observes different text actually passed to the embedder and different config identity. |
| `rrf_candidate_pool` | experimental hybrid lexical budget | RC0 lexical-budget spy observes the actual BM25 pre-fusion `top_k`. |
| `rrf_k_constant` | experimental | RC1 metamorphic test holds rankings fixed and observes changed fusion scores. |
| `parent_aggregation` | invariant | Type is currently `Literal["max"]`; it is not a multi-valued arm dimension. |
| `rerank_enabled` | experimental block switch | Existing hybrid tests exercise enabled/disabled paths. |
| reranker model + revision | experimental identity | RC0 loader propagation and exact real-model smoke. |
| `rerank_top_n` | experimental rerank scope | Existing writer path slices the parent pool before model scoring; successor characterization must record this value in the arm receipt. |
| `contradiction_enabled` | experimental block switch | Existing contradiction tests exercise enabled/disabled paths. |
| `contradiction_top_k` | experimental final counterevidence budget | Existing contradiction path truncates after classification/rerank. |
| `counterevidence_lexical_child_top_k` | research-only experimental | RC1 spy observes the actual contradiction BM25 child budget. |
| `counterevidence_semantic_child_top_k` | research-only experimental | RC1 spy observes the actual contradiction semantic child budget independently. |
| `contradiction_query_prefixes` | experimental | RC1 metamorphic test observes changed generated contradiction queries. |
| `contradiction_rerank_enabled` | experimental block switch | Existing dependency validation and contradiction rerank path establish the separate switch. |
| `contradiction_text_gate_enabled` | experimental | RC1 test holds passage text fixed and observes the role decision change. |
| cache/index filesystem paths | non-identity operational fields | Full receipt records them; normalized arm identity explicitly excludes them and RC1 proves path-only changes do not change `arm_identity`. |

## Receipt rule

A characterization arm must use `build_research_arm_receipt` and persist the JSON receipt plus its SHA-256 sidecar. The receipt contains the complete serialized `RetrievalConfig`, a normalized identity config, apparatus commit/tree, source run/corpus identity, ordered chunk-set hash, canonical model identities/revisions, runtime package versions, platform/device context, and output hashes.

A configuration-hash change is not accepted as the sole observability proof for an experimental variable.

## Validation authority

The successor workflow records the exact commit SHA and tree SHA before running deterministic tests and the pinned real-model smoke. Its artifact is evidence for that exact tested object; it does not mutate the tested tree.
