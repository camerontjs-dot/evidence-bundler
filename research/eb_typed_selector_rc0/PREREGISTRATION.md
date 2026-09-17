# Evidence Bundler Typed Candidate Selector RC0

Status: **development preregistration / research only**.

Tracking issue: #80.

This experiment does not change the frozen Evidence Bundler 10/3 integration candidate, production retrieval, admission semantics, Contract B projection, CAL behavior, or any release/default.

## Decision

Determine whether a post-retrieval selector informed by explicit typed claim/evidence characterization contains useful selection information **beyond both BM25 rank and a semantic-only reranker** at the same maximum three-passage budget.

A positive development result does not authorize production promotion. It authorizes freezing the scientific object and launching a separate fresh decisive experiment.

## Live and frozen authority at start

- protected `main`: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- frozen maintained V1 implementation: `c4e3f97ec8f0bd36180954c3aa382418925bf947`
- frozen integration candidate PR: #79
- frozen integration candidate head: `4e1f6fe00e7c350b28f52bfea14f1f8988847884`
- integration profile: `eb-v1-integration-10x3-rc0`
- candidate depth: 10
- retained budget: 3
- predecessor selector screen: PR #77, terminal `SETWISE_NOT_JUSTIFIED_ON_FROZEN_POOL`
- predecessor candidate-world artifact: `10282804289`
- artifact ZIP SHA-256: `3424e70988a2ca878e97f6eeaf855cd5ebbd449413536841872bd485de74819d`

The previous selector result remains negative evidence. This RC0 does not reinterpret it.

## Frozen question

With first-stage retrieval held fixed, can explicit candidate characterization improve the choice of three passages by measuring properties that ordinary relevance rank misses?

The specific hypothesis is:

> Typed characterization adds decision-useful selection signal beyond semantic relevance alone, especially for lexical hard negatives and long-context/local-span dilution.

Competing explanations remain live:

- **H0 — ranking is enough:** semantic-only reranking closes the useful gap; typing adds no material information.
- **H1 — local-span problem:** most remaining failures are long-context dilution and can be fixed without broader typing.
- **H2 — typed representation adds signal:** evidence-form/concept/profile compatibility contributes beyond semantic and local-span relevance.
- **H3 — selection is not the bottleneck:** even a richer selector cannot reliably retain the useful evidence at K=3.

## Protected boundary

The experiment holds fixed:

`same claim -> same corpus -> same query -> same depth-10 BM25 candidate pool`

No first-stage retrieval rerun, query rewrite, adaptive candidate depth, source routing change, admission repair, CAL call, Contract change, or production mutation is permitted inside this RC0.

The selector must not emit or consume:

- SUPPORTS / REFUTES;
- factual truth labels;
- CAL conclusions;
- downstream verdicts;
- decisive gold during selection;
- answer-bearing evaluator state.

Complete native candidate history remains the system of record.

## Characterization record

Each candidate receives inspectable signals rather than one opaque final score.

RC0 apparatus supports:

- normalized original BM25 score;
- whole-claim lexical overlap;
- best local-span claim-token recall;
- semantic relevance from a separately identified scorer;
- weighted compatibility with explicit profile concepts;
- optional evidence-form compatibility when supplied;
- optional source-role compatibility when supplied;
- explicit unknown fields.

Missing values remain `null`/unknown and are omitted from weighted means. They are not coerced to zero.

The current development profile interface is intentionally explicit because no canonical Claim Profile schema is present on Evidence Bundler `main` at experiment start. A later frozen ClaimGate/EvidenceGate output may replace the development profile adapter only in a separately recorded pre-freeze apparatus change.

## Arms

Every primary arm retains at most three candidates per lane.

### A — BM25 top 3

Current rank control.

### B — semantic top 3

A semantic-only reranker control. Development uses the previously exercised generic reranker identity:

- model: `cross-encoder/ms-marco-MiniLM-L6-v2`
- revision: `233902d25c440f23af6f7d6e94d2946bac0bee0a`

This arm answers whether ordinary semantic relevance is sufficient without typed characterization.

### C — typed set selector

Greedy deterministic set selection using:

- semantic relevance;
- local-span relevance;
- typed/profile compatibility;
- normalized BM25;
- concept-set coverage;
- redundancy penalty.

Tie break: better original rank, then stable evidence identity.

The exact weights in `selector.py` are development parameters until scientific freeze. They may change during development only with the change recorded before fresh-case authoring.

### Ablations / weak controls

- typed without profile signal;
- typed without local-span signal;
- typed without semantic signal.

At least one weak/ablated control must fail a meaningful development discriminator for the feature family to count as demonstrated machinery rather than decorative complexity.

## Development-only known cases

Two already-exposed failures may be used to debug mechanism, never as decisive evidence:

- `C06_HARD_NEG:child:1|C06-P1` — rank-4 measured-result passage behind lexical setup/protocol hard negatives;
- `RETRIEVAL_APERTURE:child:1|RET-AP-P6` — rank-7 passage containing the exact proposition inside long repeated context.

The development profiles for these lanes are answer-aware by design and are explicitly prohibited from decisive reuse.

Known-case evaluation must occur only after selector output is frozen for that run.

## Development acceptance

Before scientific freeze, require:

1. unit controls pass;
2. exact replay on synthetic development input;
3. candidate input-order permutation does not change selection;
4. no duplicate or out-of-budget selection;
5. unknown signals remain explicit;
6. no support/refutation/verdict fields appear;
7. at least one weak/ablated control demonstrates decision discrimination on a synthetic control;
8. frozen predecessor artifact digest verifies before known-case execution;
9. semantic model identity is exact and recorded;
10. known-case output and answer-bearing evaluation are separated in execution order.

Failure of a known exposed case is a development observation, not an automatic falsifier. The apparatus may still be revised before scientific freeze.

## Scientific freeze boundary

After the development machinery is accepted, freeze:

- selector source bytes;
- candidate characterization schema;
- semantic scorer model/revision/runtime;
- weights and set objective;
- profile input schema/adapter;
- evaluator and decisive gates;
- budget of three;
- all development observations.

After this point, fresh decisive outcomes may not be used to tune the frozen object. Any material scientific change requires a successor identity and a new freeze.

## Fresh decisive experiment

**CONTEXT-FREE REQUIRED** for fresh case/gold construction or independent adjudication because prior failures and development behavior are now answer-bearing.

The separate launch packet must expose only the frozen scientific object and the minimum authorized case-construction/evaluation contract. It must not copy this thread's implementation reasoning or known answers into the fresh authoring context.

Fresh cases should cover, at minimum:

- lexical hard negatives;
- long-context buried relevant spans;
- duplicate/redundant passages;
- competing measurement/evidence forms;
- temporal mismatch;
- provenance/source-role variation;
- qualifier/scope traps;
- complementary multi-passage coverage;
- ordinary easy cases;
- cases where required state is unknown or no candidate is clearly suitable.

## Decisive evaluation

Compare A, B, C and frozen weak/ablation controls on the exact same candidate pools.

Primary evidence should include:

- useful/required evidence retained@3;
- lane/claim coverage;
- distractor retention;
- unsafe/misleading retention;
- duplicate/redundancy burden;
- reviewer burden/disagreement where applicable;
- hard-negative discrimination;
- local-span rescue behavior;
- deterministic replay;
- mutation sensitivity for signals that should matter;
- invariance to irrelevant metadata/order changes;
- unknown/abstention behavior;
- complete native candidate-history preservation.

The decisive comparison of interest is **typed selector versus semantic-only**, not only typed selector versus BM25.

## Allowed terminal research dispositions

- `SUPPORTED FOR PROMOTION`
- `FALSIFIED`
- `INCONCLUSIVE`
- `SUPERSEDED`

A typed-selector pass requires preregistered improvement beyond semantic-only without violating burden/safety/system gates, plus evidence that weak/ablated controls do not clear the same decision gate for incidental reasons.

If semantic-only is equivalent within the frozen gate, the additional typed architecture is not justified by this experiment.

## Stop rules

Stop rather than repair the sealed experiment when:

- decisive gold or expected answers are exposed before scientific freeze;
- the frozen artifact or scorer identity does not match;
- the selector would need CAL semantics to proceed;
- a material scientific change is needed after fresh decisive exposure;
- the evaluator cannot discriminate the target from the weak control;
- the next change would alter first-stage retrieval rather than post-retrieval selection.
