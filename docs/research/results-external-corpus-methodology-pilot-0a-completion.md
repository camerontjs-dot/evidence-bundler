# Evidence Bundler External Corpus Methodology Pilot 0A Completion

## Class

Research Infrastructure / benchmark-methodology completion.

This record resumes the exact frozen Pilot 0A scientific object from PR #20 and the evaluator contract lineage from PR #21. It does not create a benchmark, run a retriever, or authorize BM25, Hybrid, Semantic-only, dense retrieval, lexical retrieval, or any candidate target execution.

## Terminal disposition

# `FALSIFIED`

The completion run cannot support clean pre-retrieval methodology because prohibited external retrieval-output exposure occurred while inspecting the FreshStack construction paper. A page opened to verify construction semantics exposed published aggregate BM25 and dense/fusion pooling results. Those values were not used to select cases, define relevance, or choose a source aperture, and no FreshStack retrieval-produced candidate list was inspected. Nevertheless the Pilot 0A firewall prohibits inspecting or consuming retrieval output, and the frozen preregistration treats prohibited exposure as an isolation falsifier.

This is a falsification of this completion run's clean-isolation claim. It is not evidence that the frozen ten-case scientific object is intrinsically invalid. No scientific gold was created and no Evidence Bundler target output was exposed, so the frozen object remains reusable only in a genuinely fresh, uncontaminated completion context.

## Live starting state

Observed at task start:

- production `main`: `b9917f371d00a8dfaad20ab63e1daebc8c3c5f37`;
- PR #20 `Research Infrastructure: external corpus methodology pilot 0A`: closed, unmerged, terminal `INCONCLUSIVE`, head `357fe735067dbbd3d54f8872ffc8391dac724950`;
- PR #21 `Research Infrastructure: external corpus evaluator independence and blind handoff`: open draft, terminal `INCONCLUSIVE`, head `764144f3da77140a8e542158948b4e88d40a7421`;
- PR #18: terminal `FALSIFIED`;
- PR #17: terminal `SUPERSEDED WITHOUT TARGET EXECUTION`;
- PR #19 was the only newer merged change and changed CI notification hygiene, not the scientific object.

### Governance access deviation

The task requested the durable CAL Pipeline governance documents before material work. The exact project-state documents were not available through the public GitHub surfaces inspected in this runtime. The private MainFrame path directs agents to use the intended MainFrame/Conduit access surface, but the Conduit session/adapter request returned HTTP 404 in this run. The required governance contents therefore could not be re-read through the sanctioned path. This record does not claim that they were read. Live GitHub state and the frozen predecessor records were re-established before scientific conclusions.

## Exact frozen Pilot 0A identities

The frozen object is unchanged.

### FreshStack

- query dataset: `freshstack/queries-oct-2024-unfiltered`;
- query revision: `00150066ff2959688ad03ce7148ffb652f2fee38`;
- corpus dataset: `freshstack/corpus-oct-2024`;
- corpus revision: `069f66dc323e163b48b10d08408d282733d4393b`;
- framework commit: `fresh-stack/freshstack@f1c4ec96477f5100f10c83798d33b3101db727fa`;
- selected topic rows: `langchain:271/318`, `yolo:42/94`, `laravel:121/230`, `angular:248/310`, `godot:36/197`.

### SciFact

- canonical repository snapshot: `allenai/scifact@68b98a56d93e0f9da0d2aab4e6c3294699a0f72e`;
- frozen physical `claims_dev.jsonl` line indices: `199, 66, 278, 114, 123`;
- previously recorded archive SHA-256: `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`;
- previously recorded archive size: `3115079` bytes.

The passage rules, relevance degrees, support/counterevidence semantics, evidence-group semantics, inclusion rules, and ten selected cases were not changed.

# OBSERVED

## 1. FreshStack source-provenance result

### Canonical dataset and transformation path

The official FreshStack corpus is a finite October 2024 topic collection containing 271,842 chunks across five topic partitions. The official dataset card identifies the original GitHub repository set for every topic and the pinned corpus revision is immutable at the dataset-repository level.

The frozen framework code establishes this construction path:

1. query GitHub for each repository's current default branch;
2. shallow-clone that single branch with `depth=1`;
3. build file URLs with the mutable default-branch name;
4. after cloning, resolve local `HEAD` using `git rev-parse HEAD`;
5. write that commit SHA into each constructed chunk as `metadata.commit_id`.

The released official corpus schema currently exposes `_id`, exact chunk `text`, and metadata `url`, `start_byte`, `end_byte`, but omits `commit_id`.

A historical `nthakur/corpus-oct-2024` representation is publicly visible with the same style of chunk identities and an additional `commit_id` field. For example, its Angular CLI rows expose a short commit identity while the corresponding official representation omits it.

### Provenance join decision

`UNRESOLVED`

A deterministic join is plausible using topic + `_id` + exact text + URL + byte offsets, followed by expansion/verification of the historical commit SHA against GitHub. However, this run did not materialize and compare the complete pinned official and historical bytes, so it did not prove a one-to-one join for the exact frozen source world. Guessing source revisions or substituting current repository HEAD is prohibited and was not done.

### FreshStack licensing

The FreshStack dataset is declared CC-BY-SA-4.0. The dataset card explicitly warns that underlying GitHub repositories may have different or non-permissive licenses. Therefore the methodology may preserve dataset artifacts, hashes, immutable locators, and permitted excerpts under their applicable terms, but any later plan to redistribute full upstream repository bytes must be checked repository by repository rather than inferred from the FreshStack dataset license.

## 2. FreshStack source-aperture result

### Structural classification

For each frozen FreshStack topic, the full topic corpus snapshot is a finite externally published ecosystem corpus established independently of the later per-query relevance pool:

- langchain: 49,514 chunks from 10 declared repositories;
- yolo: 27,207 chunks from 5 declared repositories;
- laravel: 52,351 chunks from 9 declared repositories;
- angular: 117,288 chunks from 4 declared repositories;
- godot: 25,482 chunks from 6 declared repositories.

For the frozen selected query in each topic, the qrel-independent source aperture can therefore be defined as that topic's entire pinned corpus partition.

Per-case aperture classification:

| Frozen case | Aperture classification | Boundary |
|---|---|---|
| FreshStack langchain index 271 | `EXTERNALLY FIXED` | entire pinned langchain topic corpus |
| FreshStack yolo index 42 | `EXTERNALLY FIXED` | entire pinned yolo topic corpus |
| FreshStack laravel index 121 | `EXTERNALLY FIXED` | entire pinned laravel topic corpus |
| FreshStack angular index 248 | `EXTERNALLY FIXED` | entire pinned angular topic corpus |
| FreshStack godot index 36 | `EXTERNALLY FIXED` | entire pinned godot topic corpus |

FreshStack's published judged-document pools are separately retrieval-conditioned and are not an admissible source aperture for Pilot 0A. No such candidate list was used here.

Because this completion context later saw prohibited aggregate retrieval-output results, this structural aperture finding is preserved as an observation but cannot be used by this run to establish the required clean support claim.

## 3. SciFact reconstruction and licensing result

### Source aperture

SciFact's canonical schema defines `cited_doc_ids` as the documents cited by the source citation sentence from which a claim was generated, while the separate `evidence` field records documents/rationales later judged evidential. The frozen Pilot 0A use of `cited_doc_ids` is therefore a qrel-independent source boundary.

Classification for all five frozen SciFact claims: `DETERMINISTICALLY DERIVED WITHOUT RETRIEVAL`.

### Immutable acquisition

The pinned upstream repository's official download path is `release/latest/data.tar.gz`. That path is mutable and the download script does not bind a release version or checksum. Pilot 0A preserves a previously observed archive SHA-256 and byte count, but this runtime did not independently reacquire the archive bytes and bind them to an immutable upstream object/version.

Result: `INCONCLUSIVE` for exact immutable byte reconstruction. The failure mode is missing immutable acquisition proof, not evidence that the bytes are unrecoverable.

### Licensing

Authoritative upstream `LICENSE.md` states:

- claims and evidence annotations: CC BY 4.0;
- corpus abstracts: ODC-By 1.0 through S2ORC;
- code: Apache-2.0.

A Hugging Face mirror advertises an aggregate CC-BY-NC-2.0 label. That is a mirror-level discrepancy and does not override the canonical upstream split-license statement for the upstream files. Any future preserved artifact must retain the upstream attribution/license split and avoid claiming a single license over all SciFact components.

## 4. Fresh-context evaluator B

Frozen evaluator contract identity inspected from PR #21:

- branch head: `764144f3da77140a8e542158948b4e88d40a7421`;
- contract path: `research/external_corpus_evaluator_independence_v1/contract.md`;
- contract blob SHA: `61ad95dab08c89c34e3416c2a3b9b0f35dabb7f0`;
- contract title: `External Corpus Retrieval Evaluator Contract v0.2-draft`.

PR #21 already establishes dummy commitment/reveal mechanics, fail-closed behavior, and numerical agreement between two non-importing implementations, while explicitly rejecting E4 independence because both implementations were authored in the same supervisory context.

This task attempted to reach a genuinely fresh implementation context through the available MainFrame/Conduit surface. The surface returned HTTP 404. No same-context replacement was created.

Gate B outcome: `INDEPENDENCE NOT ESTABLISHED`.

No fresh evaluator-B source hash, implementation receipt, or A/B comparison exists from this completion task. That absence is deliberate rather than a false independence claim.

## 5. Scientific adjudication result

`NOT_EXECUTED`

Two genuinely isolated adjudication contexts were unavailable, FreshStack exact upstream source-version reconstruction remained unresolved, SciFact immutable archive binding remained unresolved, and the completion context became contaminated by prohibited published retrieval-output exposure.

Accordingly:

- adjudicator A frozen record: `NOT_EXECUTED`;
- adjudicator B frozen record: `NOT_EXECUTED`;
- adjudication comparison: `NOT_EXECUTED`;
- published-qrel comparison: `NOT_EXECUTED`;
- disagreement taxonomy: no scientific disagreements exist because no scientific labels were created.

Published FreshStack qrels/nuggets and SciFact evidence/rationale annotations were not used to create scientific gold.

## 6. Passage correspondence and segmentation stability

`NOT_EXECUTED`

The two frozen passage representations remain unchanged. Exact parent-source bytes were not fully materialized, and no clean independent gold exists. Therefore this run does not claim:

- passage correspondence;
- semantic evidence preservation across representations;
- benign split/merge behavior;
- material instability;
- segmentation-induced evidence manufacture.

The absence of observed instability is not evidence of stability.

## 7. Gold/evaluator stability

Scientific gold invariance checks were `NOT_EXECUTED` because no scientific gold was created.

The existing PR #21 dummy-only evaluator evidence remains exactly what that PR claims: serialization reorder, source-order permutation, stable-ID correspondence, malformed input, and related dummy invariance/sensitivity checks. It is not promoted here into scientific Pilot 0A evidence.

## 8. Evaluator-contract defects

No new contract defect was established because the required fresh independent implementation was not created. The missing discriminator remains whether a reasonable independent implementer, given only the frozen contract and allowed dummy interface, reaches the same semantics and error classifications.

Gate B must not be upgraded from `INDEPENDENCE NOT ESTABLISHED` on numerical agreement alone.

## 9. Project-control analysis

| Variable | FreshStack | SciFact |
|---|---|---|
| query | `EXTERNALLY FIXED` plus deterministic frozen sampling | `EXTERNALLY_FIXED` plus deterministic frozen sampling |
| corpus | `EXTERNALLY_FIXED` | `EXTERNALLY_FIXED` |
| source aperture | `EXTERNALLY_FIXED` as full pinned topic partition | `DETERMINISTICALLY_DERIVED` from `cited_doc_ids` |
| source version | dataset revision externally fixed; upstream repo-commit join `UNKNOWN` | repo snapshot externally fixed; data archive identity `UNKNOWN` |
| passage segmentation | `DETERMINISTICALLY_DERIVED` by frozen rules | `DETERMINISTICALLY_DERIVED` by frozen rules |
| relevance | `UNKNOWN`, not adjudicated | `UNKNOWN`, not adjudicated |
| evidence role | `UNKNOWN`, not adjudicated | `UNKNOWN`, not adjudicated |
| evidence grouping | `UNKNOWN`, not adjudicated | `UNKNOWN`, not adjudicated |
| metadata | external dataset metadata; official FreshStack commit field loss observed | external corpus/claim metadata |
| hard negatives | none created | none created |

The decisive semantic variables, relevance, role, grouping, and segmentation stability, remain untested rather than project-discretionary by observation.

## 10. Contamination and exposure record

### Evidence Bundler target exposure

- production BM25 exposed = `false`;
- Hybrid exposed = `false`;
- Semantic-only exposed = `false`.

### Other protected exposure

- Evidence Bundler dense/lexical/candidate retrieval output exposed = `false`;
- FreshStack retrieval-produced candidate lists exposed = `false`;
- FreshStack published qrels used for gold = `false`;
- SciFact published evidence/rationales used for gold = `false`;
- scientific gold created = `false`;
- FreshStack published aggregate retrieval-pooling output accidentally exposed = `true`.

### Contamination event

During source-construction verification, an authoritative FreshStack paper page opened around corpus/pooling methodology also displayed aggregate performance rows for BM25, dense retrievers, and fusion. The values were not used for source-aperture choice or case selection. Because the task firewall prohibits inspection of retrieval output, the exposure is preserved as contamination rather than rationalized away.

Affected claim stopped: this run cannot establish a clean pre-retrieval `SUPPORTED FOR EXTERNAL-CORPUS PILOT` disposition.

## 11. Explicit alternative explanations

1. **Source aperture is retrieval-conditioned.** Partially falsified structurally for the full FreshStack topic corpus and SciFact `cited_doc_ids`; still true of FreshStack's published judged-document pools, which remain inadmissible.
2. **Source-version reconstruction is ambiguous.** Not falsified. FreshStack upstream commit restoration and SciFact immutable archive binding remain unresolved.
3. **Passage segmentation manufactures decisive evidence.** `UNKNOWN`, not tested.
4. **Independent judges use the same superficial cue.** `UNKNOWN`, no independent scientific judges executed.
5. **Published qrels influenced supposedly independent gold.** No gold was created. This run is nevertheless unsuitable for future same-context gold because retrieval-output contamination occurred.
6. **Source/query metadata leaks relevance.** `UNKNOWN`, not tested.
7. **Evaluator contract permits multiple reasonable interpretations.** `UNKNOWN`, fresh independent implementation unavailable.
8. **Independent evaluator reproduction is contaminated by implementation knowledge.** The prior same-context implementation is explicitly not accepted as independent; no new reproduction was substituted.
9. **Gold stability depends on one corpus-specific convention.** `UNKNOWN`, not tested.

## 12. Strongest remaining alternative explanation

Ignoring the contamination event, the strongest scientific alternative remains that exact source-version reconstruction and segmentation could materially change the evidence world. FreshStack has a recoverable-looking but unproven official-to-historical commit join, while SciFact's canonical convenience URL is mutable. Until exact bytes are frozen, any later apparent adjudication stability could partly reflect source-version choices rather than stable semantics.

# INFERENCE

1. FreshStack does not appear to require a retrieval-conditioned source aperture if the frozen aperture is the entire externally published topic partition rather than the judged-document pool.
2. That aperture improvement does not solve FreshStack provenance. A finite source world and an immutable parent-source version are separate requirements.
3. SciFact retains the stronger qrel-independent aperture, but its canonical acquisition procedure is not itself immutable.
4. PR #21's evaluator contract is ready for the missing fresh-context discriminator but E4 independence remains unestablished.
5. This completion run is terminally unusable as clean promotion evidence because the firewall was breached before support could be established.

# HYPOTHESIS

1. A full bytewise join between `freshstack/corpus-oct-2024@069f66d...` and the historical `nthakur` representation may restore per-repository construction commits without relevance knowledge.
2. The previously recorded SciFact archive hash may identify a stable historical object that can be mirrored or content-addressed without relying on `release/latest`.
3. Once exact bytes and genuine isolation are available, the ten-case object may still be capable of producing stable independent gold. No claim is made either way.

# UNKNOWN

- exact selected FreshStack query bytes/IDs in a newly materialized clean packet;
- complete official-to-historical FreshStack one-to-one provenance join;
- full immutable Git commit identity for every FreshStack upstream repository represented in the frozen source world;
- independently reacquired SciFact archive bytes bound to a non-mutable origin;
- scientific passage correspondence;
- independent adjudication agreement/disagreement structure;
- published-qrel comparison after frozen gold;
- segmentation stability;
- scientific gold invariance;
- fresh-context evaluator-B agreement and contract adequacy.

## 13. Falsified alternatives and terminal decision

### Terminal decision

`FALSIFIED`

Promotion-critical condition falsified: **clean pre-retrieval isolation for this completion run**.

The result must not be repaired by ignoring the exposed aggregate retrieval results, swapping cases, changing source boundaries, weakening the firewall, or creating a new benchmark.

The frozen 10-case object itself remains reusable because no scientific gold, case replacement, passage-rule change, or Evidence Bundler target exposure occurred. Reuse requires a fresh context that has not seen the prohibited retrieval output.

## 14. Smallest next authorized task

### `Pilot 0A clean-room reconstruction and isolation rerun`

Use the exact frozen ten cases, passage rules, and relevance contract unchanged. Do not construct the 24-30 case apparatus.

The smallest successor adds one procedural control rather than changing the scientific object:

1. create an explicit source-only allow-list that permits the frozen dataset cards, pinned dataset objects, source repositories/commits, license files, SciFact schema, and evaluator contract, while excluding FreshStack paper retrieval-result/pooling-result sections, published qrels, leaderboards, and all Evidence Bundler retrieval output;
2. in a genuinely fresh supervisory/agent context, materialize the pinned FreshStack official and historical corpus bytes and prove or fail the deterministic provenance join without relevance information;
3. independently reacquire the SciFact archive, bind it to an immutable/content-addressed identity, and verify the preserved SHA-256;
4. restore a genuinely isolated evaluator-B runner, implement from the frozen contract only, freeze its source/runtime/fixture receipt, then compare against evaluator A on dummy fixtures only;
5. only if those pre-adjudication gates pass, create two isolated scientific adjudications and execute the already frozen passage/gold stability checks.

No production BM25, Hybrid, Semantic-only, dense, lexical, or substitute retrieval is authorized by this result.

## Durable-record coverage

This file plus the machine-readable receipt records:

1. live starting state;
2. exact frozen Pilot 0A identities;
3. FreshStack provenance join status;
4. FreshStack source-aperture decision;
5. SciFact immutable acquisition/licence decision;
6. source-hash status;
7. passage correspondence status;
8. adjudicator A status;
9. adjudicator B status;
10. disagreement taxonomy status;
11. published-qrel comparison status;
12. segmentation/gold stability status;
13. fresh-context evaluator-B identity status;
14. evaluator A/B comparison status;
15. independence/access audit;
16. failures/deviations;
17. contamination/exposure record;
18. terminal methodology decision;
19. machine-readable receipt.
