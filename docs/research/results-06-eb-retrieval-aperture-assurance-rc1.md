# Results 06 — EB Retrieval + Aperture Assurance RC1

**PR:** #6  
**Research disposition:** **INCONCLUSIVE**  
**Production impact:** none  
**First decisive sealed run:** GitHub Actions `33174250908`  
**First decisive harness head:** `5eff2b9ade67629a323bd3c9cd679ee0b1e266eb`

## Decision

The first frozen sealed-test run does **not** justify `SUPPORTED FOR PROMOTION` for the
broad retrieval/aperture claim.

Evidence Bundler's pinned c818 BM25 retrieval primitive performed extremely well on the
sealed benchmark, including complete joint-group and counterevidence coverage. However, the
frozen weak lexical control C3 is indistinguishable from EB on every promotion-critical
sealed gate. The decisive 111-case holdout therefore does not discriminate the capability
that the experiment was intended to establish.

This is not a finding that EB retrieval failed. It is a finding that the decisive evidence is
insufficiently discriminating to support promotion. The appropriate primary research
disposition is therefore **INCONCLUSIVE**, not `FALSIFIED` and not
`SUPPORTED FOR PROMOTION`.

## Frozen identities

| Object | Frozen identity |
| --- | --- |
| Production SUT | `c8189c31adbab11729c31430c2070126224a2d42` |
| Benchmark commit | `22b227ec2c34a085efc79267bc007ff78607aeed` |
| Corpus tree SHA-256 | `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8` |
| Validation report SHA-256 | `1c3db5529f14b18035c11aae0d3454c28914bcd822b41ec3bc6b85fd1deeec2a` |
| Evaluator commit | `acfa232c0a6d1708f249b71606cbdc96755bc4d9` |
| Evaluator composite SHA-256 | `48ccebbd81f43ddd951e83c2a2c4b9c1fae7a6a24ec7c3bf3fdea47b1b936f14` |
| Result schema SHA-256 | `2cfb4dc6cd746f55b690300aafe9a0d19678fcb09bd8e01b0dd5d15043fbf40b` |
| Threshold config SHA-256 | `066e99719168a366f03476fa779398f790cce7653bc3928470486d6bbb805461` |

The workflow reverified these identities and all committed benchmark bytes before any real EB
retrieval output was generated.

## Exact SUT/configuration exercised

The SUT was the unmodified c818 production `BM25Retriever` with:

- frozen case `claim_text` verbatim as query;
- BM25 retrieval only;
- score floor `0.0`;
- frozen per-case `maximum_passages` as K;
- only the frozen named aperture's sources searchable;
- semantic retrieval, reranking, and contradiction query expansion off.

The research adapter provided one flat production `DocumentChunk` per frozen permitted
benchmark passage. This preserves exact passage/anchor identity for the frozen evaluator.
It bounds the result to the **retrieval nomination primitive over frozen passage units**.

The runtime mount contained only `sources/`, `cases/`, and `aperture/subsets.json`. Gold,
decompositions, challenge-family labels, expected rankings, evaluator source, and expected
outcomes were outside EB runtime context.

Search-scope receipts and `completeness_claim.status = not_established` were mechanically
serialized by the research harness. They must not be attributed to native c818 output.

## First decisive sealed result

The frozen evaluator's promotion-critical gates all passed on the 111 sealed cases.

| Metric | EB sealed result | Frozen requirement |
| --- | ---: | ---: |
| Case hit@K | `1.000000` | `>= 0.95` |
| Decisive annotation recall@K | `1.000000` | `>= 0.90` |
| Counterevidence recall@K | `1.000000` | `>= 0.90` |
| Qualifier/exception recall@K | `1.000000` | `>= 0.90` |
| Complete joint-group coverage@K | `1.000000` (`12/12`) | `>= 0.90` |
| First-decisive MRR | `0.992958` | reported, no frozen threshold |
| Scored-gold passage recall@K | `1.000000` (`94/94`) | auxiliary |
| Scored-gold source recall@K | `1.000000` (`94/94`) | auxiliary |
| Hard-negative-before-first-decisive | `36` | diagnostic |
| Hard-negative proportion@K | `0.066066` | diagnostic |
| Budget violations | `0` | `0` |
| Shape errors | `0` | `0` |
| Invalid provenance hits | `0` | `0` |
| Out-of-scope hits | `0` | `0` |
| False completeness claims | `0` | `0` |
| Configured-scope mismatches | `0` | `0` |
| Scope-fact mismatches | `0` | `0` |

There were no frozen evaluator qualification failures.

### By challenge family

| Family | Name | Cases | Case hit@K | Decisive recall@K | Counter recall | Qualifier recall | Joint coverage | MRR | Hard-neg proportion |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| F01 | LEXICALLY_OBVIOUS | 3 | 1.000 | 1.000 | n/a | n/a | n/a | 1.000 | 0.0833 |
| F02 | SYNONYM_PARAPHRASE | 3 | 1.000 | 1.000 | n/a | n/a | n/a | 1.000 | 0.0833 |
| F03 | NEGATION_POLARITY | 15 | 1.000 | 1.000 | 1.000 | 1.000 | n/a | 1.000 | 0.0833 |
| F04 | NUMERIC_THRESHOLD | 15 | 1.000 | 1.000 | n/a | 1.000 | n/a | 1.000 | 0.0833 |
| F05 | TEMPORAL_SUPERSESSION | 15 | 1.000 | 1.000 | n/a | 1.000 | n/a | 1.000 | 0.0556 |
| F06 | CONDITION_EXCEPTION | 15 | 1.000 | 1.000 | n/a | 1.000 | n/a | 1.000 | 0.0222 |
| F07 | HARD_LEXICAL_DISTRACTOR | 3 | 1.000 | 1.000 | 1.000 | 1.000 | n/a | 1.000 | 0.0556 |
| F08 | DUPLICATE_PARAPHRASE | 3 | 1.000 | 1.000 | n/a | 1.000 | n/a | 0.8333 | 0.0556 |
| F09 | LONG_DOCUMENT_BURIED | 3 | 1.000 | 1.000 | 1.000 | 1.000 | n/a | 1.000 | 0.0833 |
| F10 | MULTI_PASSAGE_COMPOSITION | 15 | 1.000 | 1.000 | n/a | 1.000 | 1.000 | 1.000 | 0.0556 |
| F11 | NO_ANSWER | 6 | n/a | n/a | n/a | n/a | n/a | n/a | 0.0833 |
| F12 | APERTURE_BOUNDARY | 15 | n/a | n/a | n/a | n/a | n/a | n/a | 0.0833 |

No challenge family crossed a frozen failure floor.

### Named apertures

| Aperture | Cases | Decisive cases | Decisive recall@K | Joint coverage | Mean scored-passage recall | Mean source recall | False completeness |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full` | 42 | 35 | 1.000 | 1.000 | 1.000 | 1.000 | 0 |
| `ordinary_window` | 16 | 9 | 1.000 | n/a | 1.000 | 1.000 | 0 |
| `distractor_heavy` | 33 | 27 | 1.000 | n/a | 1.000 | 1.000 | 0 |
| `bounded_missing_decisive` | 15 | 0 | n/a | n/a | n/a | n/a | 0 |
| `stale_only` | 5 | 0 | n/a | n/a | 1.000 material-context behavior | 1.000 | 0 |

The SUT produced no out-of-scope hits. The aperture identity and `not_established`
completeness state are harness-observed facts, not native c818 aperture receipts.

## No-answer behavior

F11 contains 6 sealed no-answer cases. EB returned the full budget of 12 retrieval nominees
for every case (`72` total), with `6` hard-negative nominations at K in aggregate.

No false completeness claim was emitted because the research harness serialized
`not_established` for all six cases. c818 BM25 itself does not turn those nominations into a
proposition-level relevance claim and does not provide an explicit no-answer abstention.

**Bounded inference:** raw lexical retrieval can nominate candidates in no-answer settings,
but a semantic/admission layer or downstream consumer is still required to decide that no
answer is supported.

## Weak-control result: decisive promotion blocker

The intentionally weak frozen lexical-overlap control C3 also passed **every sealed frozen
gate**:

- case hit@K: `1.000000`;
- decisive recall@K: `1.000000`;
- counterevidence recall@K: `1.000000`;
- qualifier/exception recall@K: `1.000000`;
- complete joint-group coverage@K: `1.000000` (`12/12`);
- first-decisive MRR: `1.000000`;
- qualification failures: none.

EB is therefore not distinguished from this weak lexical strategy on the decision-relevant
sealed gates. EB is actually slightly worse on first-decisive MRR (`0.992958` vs `1.000000`)
and has one additional hard negative before first decisive evidence (`36` vs `35`), although
those are not frozen failure gates.

This exposes a split-level evaluator/benchmark limitation that the aggregate E3 assurance
record concealed for the intended sealed-only decision:

- development C3 joint coverage: `0/4 = 0.000000`;
- sealed C3 joint coverage: `12/12 = 1.000000`;
- combined C3 joint coverage: `12/16 = 0.750000`.

Development C3 also fails decisive recall (`0.882353`), qualifier/exception recall
(`0.809524`), and the F10 family decisive-recall floor. The sealed split contains none of
those C3 failures.

The prior aggregate weak-control result was therefore real, but its discriminating failures
were concentrated in the development split. Because development cases cannot rescue a
sealed promotion decision, this experiment cannot attribute the sealed pass to a capability
stronger than weak lexical retrieval.

The source-order control initially reported `99/111` changed cases because the harness
compared floating scores for exact equality. Post-sealed diagnosis of the preserved raw
artifacts found:

- identity/rank sequence changes: `0/111`;
- text changes: `0/111`;
- score-bit changes: `99/111`;
- maximum absolute score delta: `1.4210854715202004e-14`;
- maximum relative score delta: `4.132847672500785e-16`.

Thus the preregistered **substantive** source-order falsifier did not fire. The original
wrapper flag remains preserved in the artifact; see deviation 06b.

## Production chunking diagnostic

Before sealed retrieval, the unmodified c818 production chunker was run over the frozen 60
sources solely as an apparatus/extraction diagnostic:

- frozen passage units: `946`;
- c818 production chunks: `95`;
- c818 chunks exactly equal to one frozen passage: `0`;
- c818 chunks not exactly equal to one frozen passage: `95`.

This validates why the research passage-unit adapter was necessary for exact frozen-passage
scoring. It also means this experiment does **not** establish end-to-end production chunking
or `build-bundle` retrieval behavior. Treating the presegmented result as if it covered that
surface would overstate the evidence.

## Reproducibility and provenance

The decisive raw output reproduced byte-for-byte:

- first decisive raw SHA-256:
  `7d3beace9e7ea507e204eee4bcfb22d84f7fb86978532197c78d40e1097da02d`;
- deterministic replay SHA-256:
  `7d3beace9e7ea507e204eee4bcfb22d84f7fb86978532197c78d40e1097da02d`;
- byte-identical replay: `true`.

Other preserved hashes:

- frozen evaluation SHA-256:
  `55b6bee60e9d2d9b947e60bc18952bc553d834c0d3d039257a76d2f2f9c4c35d`;
- reversed-source-order raw SHA-256:
  `4b5414d449dbbcb19bf41e3e1d84e464229b40b9488ed43c253b702bc3e215a7`;
- chunker diagnostic SHA-256:
  `e47f30178dc2dc15c52a77dd93dd1a63623874c07a9a3a8bf29c4028f87195b8`;
- dev raw SHA-256:
  `08c36bc589f783903955721b18ce09bdb14ad0b957dc54d2f2244c4f463ca2ef`;
- dev evaluation SHA-256:
  `baec51ff09fd573c79c8b8e821a0846e11ca136546e7bf30228880962fcba220`;
- run artifact ID: `9686891938`;
- GitHub-reported artifact ZIP SHA-256:
  `93380a76bb20db419ed62051d7601233a7cb46593942c8e0305c97706f07adc7`.

## Preserved failed apparatus run and deviations

### Deviation 06a — pre-sealed dependency omission

Run `33174045876` failed before development or sealed retrieval because the research
workflow omitted the c818-declared PyYAML dependency needed by the production chunker
diagnostic. The failure was preserved, the workflow environment alone was corrected, and no
SUT/benchmark/evaluator/query/threshold/configuration changed.

No decisive output existed in that failed run.

### Deviation 06b — post-sealed source-order comparator precision

The source-order comparator's exact-float equality produced an over-sensitive `invariant =
false` flag. No apparatus was changed after sealed output; the diagnosis above is based only
on comparison of preserved raw artifacts.

## Exact execution commands

The successful decisive workflow executed the following research commands after verifying
all frozen identities and creating the clean runtime mount:

```bash
PYTHONPATH=sut/src python research/eb_retrieval_aperture_rc1/chunk_alignment_diagnostic.py \
  --runtime-root work/runtime \
  --output artifacts/eb-retrieval-aperture-rc1/chunker-alignment.json

PYTHONPATH=sut/src python research/eb_retrieval_aperture_rc1/runtime_runner.py \
  --runtime-root work/runtime --split dev \
  --output artifacts/eb-retrieval-aperture-rc1/dev-results.jsonl

python research/eb_retrieval_aperture_rc1/evaluate_split.py \
  --benchmark-root apparatus/benchmarks/eb-challenge-corpus-v1 \
  --evaluator-root apparatus/research/eb_retrieval_evaluator_rc1 \
  --split dev \
  --results artifacts/eb-retrieval-aperture-rc1/dev-results.jsonl \
  --output artifacts/eb-retrieval-aperture-rc1/dev-evaluation.json

PYTHONPATH=sut/src python research/eb_retrieval_aperture_rc1/runtime_runner.py \
  --runtime-root work/runtime --split test \
  --output artifacts/eb-retrieval-aperture-rc1/test-results-FIRST-DECISIVE.jsonl

PYTHONPATH=sut/src python research/eb_retrieval_aperture_rc1/runtime_runner.py \
  --runtime-root work/runtime --split test \
  --output artifacts/eb-retrieval-aperture-rc1/test-results-replay.jsonl

PYTHONPATH=sut/src python research/eb_retrieval_aperture_rc1/runtime_runner.py \
  --runtime-root work/runtime --split test --reverse-source-order \
  --output artifacts/eb-retrieval-aperture-rc1/test-results-reverse-source-order.jsonl

python research/eb_retrieval_aperture_rc1/evaluate_split.py \
  --benchmark-root apparatus/benchmarks/eb-challenge-corpus-v1 \
  --evaluator-root apparatus/research/eb_retrieval_evaluator_rc1 \
  --split test \
  --results artifacts/eb-retrieval-aperture-rc1/test-results-FIRST-DECISIVE.jsonl \
  --replay-results artifacts/eb-retrieval-aperture-rc1/test-results-replay.jsonl \
  --reverse-results artifacts/eb-retrieval-aperture-rc1/test-results-reverse-source-order.jsonl \
  --output artifacts/eb-retrieval-aperture-rc1/test-evaluation-FIRST-DECISIVE.json
```

The full identity verification and byte-check commands remain in
`.github/workflows/research-eb-retrieval-aperture-rc1.yml` at the first decisive harness
head.

## Epistemic compression

### Observed evidence

1. c818 BM25 over the permitted frozen passage units retrieved every accessible decisive,
   counterevidence, qualifier/exception, material-context, and jointly required target within
   the frozen K budgets on the 111 sealed cases.
2. Exact provenance, budgets, and mounted subset boundaries survived the research adapter
   without evaluator violations.
3. The raw decisive output is deterministic byte-for-byte under exact replay.
4. Source enumeration reversal leaves passage identities, ranks, and text unchanged, while
   inducing sub-`1.5e-14` score rounding differences.
5. Weak lexical control C3 also passes every sealed promotion-critical gate, including
   complete joint coverage `12/12`.
6. C3's joint-group failures are concentrated in development (`0/4`) rather than sealed
   (`12/12`), producing the previously observed aggregate `12/16 = 0.75`.
7. The general c818 production chunker does not reproduce the frozen passage units (`0/95`
   chunks exactly equal a frozen passage).
8. No-answer cases receive full-budget nominations; c818 does not itself emit a semantic
   no-answer decision.

### Inference

The evidence supports a narrow behavioral statement:

> At c818, the real EB BM25 retriever, when supplied the frozen benchmark's permitted
> presegmented passage units and named source aperture, can recover the benchmark's accessible
> scored evidence under the tested budgets with exact reconstructable passage identity.

It does **not** support promotion of the broader retrieval/aperture claim because the sealed
holdout cannot distinguish that result from the frozen weak lexical strategy and because
native c818 aperture output plus production chunking are not exercised by the scored path.

### Remaining hypotheses

- The sealed benchmark split is lexically too easy even though the full 148-case corpus has
  useful weak-control discrimination.
- A genuinely independent sealed set containing lexically nontrivial multi-passage,
  counterevidence, synonym, and distractor cases may distinguish EB from trivial overlap.
- Production chunking may materially change recall/provenance relative to the presegmented
  retrieval primitive and needs its own evaluator-compatible experiment.
- Explicit aperture/search-scope state may need to become a named upstream/runtime input or
  EB-produced receipt before H3 can be claimed natively.

### Unknowns

- end-to-end c818 `build-bundle` recall using production chunking;
- native EB aperture-honesty behavior without research-harness serialization;
- whether semantic/hybrid retrieval adds decision-relevant value over lexical retrieval;
- calibrated no-answer behavior after semantic/admission review;
- behavior on real external corpora.

### Falsified alternatives

- `The sealed set itself preserves the weak-control joint-group discriminator seen in the
  aggregate E3 assurance result.` **Falsified:** sealed C3 is `12/12`; all four incomplete C3
  joint groups are in development.
- `Source enumeration changes substantive ranked identities on this run.` **Falsified:**
  identity/rank/text changes are `0/111`; only negligible floating-score bits change.
- `The c818 production chunker naturally yields the frozen evaluator's passage units.`
  **Falsified:** `0/95` production chunks exactly equal one frozen passage.

## What this establishes

Supported with bounds:

- deterministic c818 BM25 passage nomination on the frozen presegmented benchmark surface;
- 100% accessible scored-passage/source coverage under these sealed K budgets;
- 100% decisive counterevidence and joint-group coverage under these sealed K budgets;
- exact evaluator-reconstructable passage provenance through the research adapter;
- mechanical respect for the mounted source aperture with no out-of-scope retrieval.

## What this does not establish

- superiority over, or decision-relevant differentiation from, weak lexical retrieval;
- a promotion-worthy general retrieval capability;
- end-to-end production extraction/chunking behavior;
- native EB aperture/completeness receipts;
- semantic relevance, support, contradiction, or no-answer judgments;
- Contract A, Contract B, CAL, or production-promotion changes;
- real-world corpus completeness or external validity.

## Smallest discriminating follow-up

Do not optimize EB from this result.

Run a new preregistered RC2 with a **new independent sealed challenge extension/split frozen
before any real EB output**. Before authorizing EB exposure, require the weak lexical C3
control to fail at least one decision-relevant sealed gate, especially complete joint-group
coverage and one or more synonym/distractor/counterevidence family floors, while the oracle
still passes. Preserve c818 as a comparison SUT if the question remains architectural.

Separately, if end-to-end EB production behavior matters, create a small extraction/chunking
assurance experiment whose evaluator can score c818's real 95-chunk representation without
post-hoc overlap credit.

Neither follow-up is implemented in this PR.
