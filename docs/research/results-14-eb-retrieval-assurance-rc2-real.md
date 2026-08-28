# Results 14 — Evidence Bundler Retrieval Assurance RC2: Real Production Measurement

**Research disposition: `FALSIFIED`**

The frozen production Evidence Bundler BM25 retriever did not clear the preregistered RC2 retrieval gate on the frozen presegmented runtime representation. The result is a bounded retrieval failure, not a claim about production chunking, native aperture receipts, semantic entailment, or production readiness.

## 1. Observed evidence

### Preflight

The canonical run verified before sealed SUT exposure:

- production SUT SHA `c8189c31adbab11729c31430c2070126224a2d42`;
- durable apparatus storage SHA `2643385c998dd3b08af84eb37f3f089fea7d5e73`;
- frozen apparatus commit `82ec006e888e22c5e5cde600546c05cc6e0b5e33`;
- benchmark tree SHA256 `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`;
- evaluator SHA256 `c443a64a2c2dfe8c9b0decd8c0414c1e7bb1069d86d3355dd0202fa9725aff08`;
- thresholds SHA256 `9df75b448ff5090d9bd2821f624e327d47ba5ea9848460cf69518bb6b04ea05a`;
- result schema SHA256 `26a56b08c90277f6d13434d5bb5db4a0f71edc925ff78db6de285b6a4b992dd0`;
- no production `src/` or `pyproject.toml` difference between the locked SUT and the durable RC2 apparatus-storage head;
- #13 assurance record still stated `real_eb_executed=false` and `sealed_runtime_exposed_to_eb=false`;
- rerunning the frozen sealed controls reproduced the exact recorded control SHA256 `d3cdc3ac7c356cc4ec0edc06b6d149bc80082e861b078e8ef94a2df9ad8dfb74`.

The sealed exposure point was GitHub Actions run `33208065906`, workflow/head SHA `846ff956dfb5875b6df16a30ed3fb06bb9b96c8d`, adapter SHA256 `a2b03b9c2a192124e60e355cb673c7fbf6015d6b1ddd681cd594e02fe75021d6`.

### Canonical sealed result

Across 72 sealed cases, 56 answerable:

| Metric | Real EB BM25 | Frozen gate |
|---|---:|---:|
| case hit@K | 0.589286 | >= 0.95 |
| decisive annotation recall@K | 0.465909 | >= 0.90 |
| counterevidence recall@K | 1.000000 | >= 0.90 |
| qualifier/exception recall@K | 0.000000 | >= 0.90 |
| complete joint-group coverage@K | 0.000000 | >= 0.90 |
| first-decisive MRR | 0.303571 | diagnostic |
| budget violations | 0 | 0 required |
| invalid provenance hits | 0 | 0 required |
| out-of-scope hits | 0 | 0 required |
| scope mismatches | 0 | 0 required |
| false completeness claims | 0 | 0 required |
| answerability overclaims | 0 | 0 required |

Family results:

- R01: case hit 0.125; decisive recall 0.125.
- R02: case hit 1.0; decisive recall 1.0; counterevidence recall 1.0.
- R03: case hit 1.0; decisive recall 0.5; qualifier/exception recall 0.0; complete joint coverage 0.0.
- R04: case hit 1.0; decisive recall 0.5; qualifier/exception recall 0.0; complete joint coverage 0.0.
- R05: case hit 1.0; decisive recall 0.666667; complete joint coverage 0.0.
- R06: case hit 0.0; decisive recall 0.0.
- R07: non-answerable aperture-honesty family; no semantic retrieval score is claimed from this run.
- R08: case hit 0.0; decisive recall 0.0.
- R09: non-answerable family; the adapter emitted `answerability_claim.status=not_established` rather than laundering retrieval into a semantic no-answer judgment.

The SUT produced 47 hard-negative hits at K, with 46 hard negatives ranked before a first decisive hit.

### Controls

- Deterministic replay was byte-identical: raw SHA256 `05d141abf11eddf90e6f3e1cbbb6f341a9dd495150d0a9f515784fb36722b5ae` on both runs.
- Reversing source enumeration changed no hit identity or rank in any of 72 cases. Maximum aligned floating-score delta was `1.1102230246251565e-16`; the frozen evaluation summary was unchanged.
- The canonical frozen evaluation SHA256 is `8d7c7b22216126510989c4fb084968de8b67f83451e22ed9461c570e6ba28916`.
- Frozen oracle remained perfect on all scored retrieval dimensions.
- Each frozen lexical weak control remained nonqualifying at case hit 0.571429, decisive recall 0.454545, counterevidence 0.0, qualifier/exception 0.0, and joint coverage 0.0.
- Real EB was only slightly above the weak lexical controls on aggregate case-hit and decisive recall, materially better on counterevidence, but still failed the promotion-critical gate.

## 2. Inference

The exact `c8189c31...` production BM25 retriever does not possess the preregistered RC2 bounded retrieval capability on the frozen presegmented passage representation. The clean provenance, budget, deterministic-replay, and source-order observations make a simple adapter-shape, budget, provenance-corruption, or source-enumeration explanation insufficient for the observed retrieval failures.

The result does not show that every retrieval sub-capability is absent. R02 counterevidence retrieval is strongly supported within this benchmark, and R03-R05 often retrieve at least one decisive passage. The failure is that the retriever does not reliably recover the full evidence set required by the bounded decision.

## 3. Supported with bounds

Observed support is limited to:

- R02 counterevidence retrieval under the frozen presegmented representation: 1.0 recall and 8/8 case hits;
- at-least-one-decisive-passage retrieval for R03, R04, and R05: 8/8 case hits in each family, without joint completeness;
- zero scored budget, provenance, scope, and receipt-overclaim violations in the research adapter output;
- byte-identical deterministic replay;
- hit/rank invariance to the preregistered source-order reversal.

These are research observations, not authorization to promote production behavior.

## 4. Falsified claims / alternatives

Falsified by the canonical sealed run:

- the preregistered claim that this frozen production BM25 retriever clears the full RC2 presegmented retrieval gate;
- adequate low-overlap retrieval across R01 at the required family floor;
- adequate qualifier/exception retrieval in R03/R04;
- adequate complete joint/multi-passage retrieval in R03-R05;
- adequate bounded-K distractor behavior in R06;
- adequate provenance-twin target retrieval in R08.

Also weakened as explanations for the failure:

- source enumeration order, because reverse-order retrieval was identity/rank invariant;
- nondeterministic execution, because exact replay was byte-identical;
- budget overflow, invalid returned provenance, or aperture-scope leakage, because each scored violation count was zero.

## 5. Remaining hypotheses

Still live:

- a different retrieval representation or retrieval method may perform better on low-overlap, multi-passage, qualifier, distractor, and provenance-twin cases;
- production segmentation/chunking may make end-to-end behavior better or worse than this presegmented experiment;
- query representation may be a bottleneck for the failed families;
- the frozen benchmark may still contain shortcuts not represented by the frozen weak controls, although the real SUT did not exploit them well enough to clear the gate.

## 6. Unresolved unknowns

This experiment does not establish:

- production chunking/extraction behavior;
- native Evidence Bundler aperture/completeness receipts;
- semantic relevance or entailment judgment by Evidence Bundler;
- semantic answerability/no-answer judgment;
- Contract-A decomposition behavior;
- performance of any redesigned or tuned retriever;
- broad retrieval quality outside the frozen RC2 decision.

The aperture and answerability honesty observations are adapter-bound: the adapter explicitly emitted `not_established`. They are not native SUT receipts.

## 7. Research disposition

`FALSIFIED`

This applies only to the preregistered claim that the exact frozen production BM25 SUT can satisfy the full RC2 bounded presegmented retrieval gate.

## 8. Exact SHAs, artifacts, and workflow receipts

- PR: #14
- base/main: `2643385c998dd3b08af84eb37f3f089fea7d5e73`
- production SUT: `c8189c31adbab11729c31430c2070126224a2d42`
- decisive workflow/head: `846ff956dfb5875b6df16a30ed3fb06bb9b96c8d`
- decisive Actions run: `33208065906`
- decisive job: `98974129431`
- Actions artifact: `9700464509`
- artifact digest: `sha256:24369b37c225f28d972074dbceb1f96b14f7062ccc3418fba4c42be1bec84b72`
- adapter SHA256: `a2b03b9c2a192124e60e355cb673c7fbf6015d6b1ddd681cd594e02fe75021d6`
- raw first result SHA256: `05d141abf11eddf90e6f3e1cbbb6f341a9dd495150d0a9f515784fb36722b5ae`
- frozen evaluation SHA256: `8d7c7b22216126510989c4fb084968de8b67f83451e22ed9461c570e6ba28916`
- frozen control reproduction SHA256: `d3cdc3ac7c356cc4ec0edc06b6d149bc80082e861b078e8ef94a2df9ad8dfb74`
- durable exact raw/evaluation encodings: `docs/research/artifacts/eb-rc2-real-first/`
- duplicate-trigger deviation: `docs/research/deviation-14a-eb-rc2-real-duplicate-workflow-trigger.md`

## 9. Smallest justified next step

Do not tune the production retriever against the sealed RC2 cases and do not promote retrieval changes from this result.

The smallest next evidence-producing step is a new, separately preregistered research question that chooses one failed capability family and tests a candidate change on a new or still-unexposed discriminator. R01 low-overlap retrieval is the narrowest first target because the failure is severe (1/8 case hits) and does not require conflating retrieval with joint-evidence completeness or native aperture semantics.
