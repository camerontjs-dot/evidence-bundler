# Child coverage and claim-native subject retrieval RC1

## Authority and phase boundary

This is a new Draft Research experiment following admission RC0. This protocol
is frozen before implementing its research arms or opening fresh retrieval
outcomes. Phase 1 qualifies mechanical apparatus only. Fresh population binding,
retrieval execution and semantic evaluator qualification remain separate gates.

Owner: Evidence Bundler research. Structural type: experiment protocol;
workbench scope; public-safe; immutable after freeze. `SPEC.json` contains the
numeric policy. `study.py`, `retrieval.py` and their tests enforce its mechanical
parts. Source freshness, declaration authority and reviewer information boundaries
also require direct custody evidence; JSON assertions alone do not prove them.

No change to #120, V1 source, runner/config, EB 0.2.0, Contract B 1.2, CAL,
Contract C, Decision, Contract D, merge/tag/version/release state is authorized.
Private claim, source, passage, mapping and reviewer bytes stay local. Prior RC0
destination permission applies only to RC0; it does not authorize these reviews.

## Observed predecessors

Live GitHub was inspected before design:

| Record | Exact head | State / bounded evidence |
| --- | --- | --- |
| [#120](https://github.com/camerontjs-dot/evidence-bundler/pull/120) | `08ca896debd6d16fa21be2f178ed7cbe62395d00` | Open Draft; protected EB 0.2.0 |
| [#119](https://github.com/camerontjs-dot/evidence-bundler/pull/119) | `b40a36e82821f7206243a1c675e2462a20ca0b76` | Closed/unmerged; `SUPPORTED_SUBJECT_ONLY; COMBINED_FORM_INCREMENT_NOT_REPRODUCED` |
| [#121](https://github.com/camerontjs-dot/evidence-bundler/pull/121) | `aad7206f49c94714f4664dccf4b32daa6039cb50` | Open Draft; terminal `FALSIFIED / ADMISSION_ONLY_FALSIFIED_FOR_FROZEN_PACKET` |
| [#122](https://github.com/camerontjs-dot/evidence-bundler/pull/122) | `cf55ba0128a5cbfc696f4740f9807a2d334c1bff` | Open Draft; `SUPPORTED FOR RC0 EXECUTION`, apparatus only |

#119's exact terminal result commit is
`e36a786ececc8f9f54607813b2212bdbc3581836`, tree
`5a9a53676720a63835ad51504bdcd6c4f79b055d`. Its child-coverage arm moved required
children from 39/48 to 43/48 and complete parents from 15/24 to 19/24.
Composition + subject reached 46/48, 22/24, 3 unsafe; wrong subject reached
27/48, 7/24, 31 unsafe. Correct and wrong form both reached 44/48 with 2 unsafe.
The old arm called `subject_only` already ran **coverage then subject**. It is
not evidence for a factorial arm that omits coverage. Subject production itself
was not qualified. See the immutable convergence record and execution receipts
in `PREDECESSOR-EVIDENCE.json`; no old selector code is imported here.

#121's exact retained set was 20 candidates / 6 retained / 0 accepted. Two fresh
Codex sessions agreed on six `rejected / insufficient_context` judgments. One
frozen evaluation applied the zero-positive falsifier. Sidecar was not produced;
admitted replay and Contract B terminal validation were NOT_RUN. CAL and Decision
were not decision inputs. This falsifies admission rescue for that retained set,
not generalized retrieval. Its [terminal record](https://github.com/camerontjs-dot/evidence-bundler/pull/121#issuecomment-5943839272)
preserves failures, reviewer limitations and exact artifact identities.

#122 informs custody design: distinguish raw file hashes from intrinsic payload
hashes; reject stale locations and leaked fields; bind mappings and exact bytes.
Its scientific decision function is not reused. Earlier failures remain intact:
Conduit task capacity, premature positive review disposition, stale-output/field
leak/replay hardening, stale-test CI failure, identity-domain conflation, approval
block and native reviewer warnings. None becomes successor support.

## Question and hypotheses

Does explicit child/all_of coverage plus exact claim-native subject binding
retrieve more locally adequate passages than exact EB 0.2.0 on fresh real
packets, with component increments distinguishable from semantic or generic
lexical movement?

H1: structural and subject headroom exists beyond baseline retention.
H2: subject identity explains useful movement; child increment is absent.
H3: child coverage explains movement; subject increment is absent.
H4: more lexical/query text explains the apparent improvement.
H5: exposed historical improvement fails to reproduce on fresh real packets.
H6: no locally adequate material occurs in the frozen reachable depth.

H6 is valid negative evidence, not permission to widen the search. No outcome
about evidence outside the depth/corpus is inferred.

## Baseline distinction and fixed budgets

The exact frozen V1 baseline is **BM25**, `evidence_bundler_okapi_bm25_v1`,
lowercase-word tokenizer, k1=1.5, b=0.75. It already queries each declared child
separately. Candidate depth is 10 and retained K is 3 **per child**. Chunking is
1800 characters with overlap 80, root diagnostic disabled, all Contract A sources,
exact primary-target text. Config identity is
`sha256:5b10d0c29794e80d6876a99e26bcf6ec6a27a4c5165aee78054a6bc32759f4bc`.

A separate S0 semantic-only reference makes the semantic-stage change visible.
A1/A2/A3 factorial comparisons share S0's model, nominations and budgets. A3
must improve over **both A0 and S0**; beating BM25 alone cannot establish the
structural/subject interpretation. All arms retain at most 3 passages per child
and at most 6 child/passage slots per two-child parent. A passage may occur in
both lanes; measure those as two distinct assessment opportunities and report
unique passage count separately. No hidden parent-budget contraction or larger K.

Semantic model: sentence-transformers/all-MiniLM-L6-v2, exact revision and file
digests in `MODEL.json`; CPU, float32, normalized embeddings, cosine similarity,
batch 32, maximum sequence length 256, one Torch thread, seed 0, deterministic
algorithms, scores rounded to 9 decimals. No reranker, fusion or score floor.
Exact runtime package versions and executable hashes must be bound **before**
retrieval in the execution freeze. They are currently unqualified/unbound.
This model is a research arm, not an assertion that it is EB's baseline.

## Fresh population

The fixed design is **3 independent real source packets**, each with **4 declared
all_of parents of exactly 2 required children**: 12 parents / 24 children.
Packet independence here means distinct origin/source sets, not statistical or
model independence. All 12 Contract A handoffs and 24 child identities are frozen.
There is no automatic fallback to one packet or a smaller denominator. A smaller
population requires a separate preregistration before outcomes.

Eligible packets are existing real claim declarations and real source packets,
not a corpus written to make this mechanism succeed. Select by a frozen inventory
order (creation time, then raw file hash); take the first three that meet only
structural/provenance criteria. Record every exclusion before retrieval. No
eligibility rule may inspect candidate adequacy, baseline scores, ranks, outcome
labels, source subject mentions, or the presence of rescue material. Source/claim
fidelity must already have trusted declaration authority; this experiment does
not qualify an extractor or manufacture child claims from source outcomes.

Each packet includes at least one elliptical child with deterministic declared
parent-subject inheritance, and at least two distinct explicitly declared subject
identities of the same entity class for credible wrong-subject swaps. Wrong
subjects are frozen rotations of these claim-native declarations, never strings
derived from evidence. Both children must express different obligations; coverage
is not earned by duplicate claims. These are input-design criteria, not adequacy
criteria. Missing eligible input yields BLOCKED.

Exclude every #119 authored/scored/gold cohort and all RC0 source/claim bytes.
The RC0 raw native identity is
`sha256:8240ca5845b883068c1c9ba6a02e415989fb8d5162664024936d02e677bbd791`;
intrinsic identity is
`sha256:b9ddf8ecb735a31ba50011832bc462a4bd9c97ebc9105d537c9bfad8bfea16ba`;
handoff is
`sha256:b59ba3b35d2b1d8b0378ac277703cd4a8867ec1e88b8ea34be577df0c3eeb843`.
The known failure can be development/mutation material only. Its review data is
not imported or retuned. No fresh population was located in Phase 1's scoped EB
and Apparatus input inventory; exact fresh identities remain **UNBOUND**.

## Freeze order and information boundaries

Use append-only, hash-linked stage receipts, with one fresh directory and no
overwrite. Freeze in this order:

1. Exact claim/parent/child strings and declared all_of mapping, with provenance.
2. Exact subject declarations, origin text hashes and byte spans; wrong-subject
   rotations; wrong-child permutation. Subject declaration precedes corpus access.
3. Exact real source bytes and corpus identity; then exact Contract A handoffs.
4. Depth/K/chunking, model files, supported Python/runtime/executable identities.
5. This candidate's exact code, arms and deterministic tie/swap rules.
6. Rubric, evaluator controls, reviewer profiles/session adapter and schemas.
7. Numeric falsifiers, weak controls, provenance exclusions and attempt budget.
8. All arm outputs from two deterministic executions, raw-byte identical, before
   any decisive review/gold assessment.
9. Only then separate fresh assessment of the union of reachable candidate pairs.

Claims/subjects are supplied by a trusted declarer and mechanically checked
against exact child or parent spans. No LLM subject extraction is implemented.
Inheritance copies the frozen parent anchor; it does not synthesize an entity.
No evidence-derived aliases or post-retrieval declaration repair is permitted.

The binding gate requires separate raw-file hashes for claims, subjects and
corpus; their prior stage receipt chain; excluded specimen checks; exact source
overlap exclusions; and a direct freshness/custody attestation. A self-reported
`fresh=true` field alone is insufficient authority. The preparation operator
must preserve inspection/access receipts for claim-before-corpus ordering.

## Arms and exact interventions

| Arm | Retrieval and selection |
| --- | --- |
| A0 | Exact frozen V1 build, BM25 10/3 for each primary child; no new logic |
| S0 | Same chunks/corpus/query/depth/K; semantic top-3 per exact child |
| A1 | S0 + one bounded child-ownership repair per child; no subject increment |
| A2 | S0 + one bounded exact-subject repair per child; no ownership repair or protection |
| A3 | S0 → child-ownership repair → exact-subject repair preserving represented child ownership |
| WS3 | A3 with frozen incorrect claim-native subject rotation |
| WC3 | A3 with child ownership score columns swapped within each parent; correct subject stays bound |
| L0 | Semantic top-3 using exact child + newline + exact parent text; no coverage/subject machinery |
| WS2 | A2 with the same frozen incorrect subjects; isolates any subject-only survival |
| WC1 | A1 with the same swapped ownership columns; isolates child-only survival |

No new corpus search is triggered by a repair. For S0/A1/A2/A3/WS3/WC3/WS2,
each child's same top-10 semantic pool is immutable. Candidate ownership is the
argmax score over the two exact declared child texts, ties by ascending child ID.
Ownership is a nomination heuristic, not a semantic adequacy label. Coverage is
an increment over S0's possible **semantic ownership starvation**, not over an
imaginary absence of child retrieval in A0.

Coverage repair: if none of the lane's retained passages is owned by that child,
choose the highest lane-score unretained owned challenger; replace the lowest
lane-score retained victim only when score loss <=0.01. At most one swap.
Ties use passage ID ascending. If no challenger or loss exceeds cap, retain the
negative/no-swap result. The loss cap is inherited as a fixed development bound
from #119, not tuned from the RC0 judgments.

Subject repair: exact case-insensitive whole-anchor matching after whitespace
normalization; no fuzzy aliases, entity detector, keyword/predicate/form scoring.
Choose the highest lane-score unretained exact-match challenger and the lowest
lane-score nonmatching retained victim, loss <=0.01, at most one swap. In A3,
never remove the last correctly owned retained passage for that child unless the
challenger preserves it. A2 has no such ownership rule. Match presence does not
mean the subject is the passage's semantic target; the reviewer measures that.

WC3 swaps the two ownership score-column labels, retaining all scores, query
strings, candidate pools, passage bytes, K and subject declarations. It breaks
the declared child-to-score association without deleting text richness. This
control can legitimately reproduce A3 and thereby falsify the interpretation.
L0 is a frozen negative-control query expansion, never an outcome-selected rewrite.

Expected form, keywords, predicate lists, answer values, support/refute hints,
evidence-derived entities, adaptive queries, source/domain routing, promoted
scope signals, opaque weighted fusion, CAL and Decision labels are excluded.

## Assessment and evaluator qualification

For each child/passage pair, assess only whether it is materially about the
proposition and contains enough **local** context for meaningful downstream
proposition-specific assessment. Accepted does not mean support, refutation,
truth, authority, applicability or completeness. A locally adequate passage may
describe a contrary observation or lack a determinate answer.

Use this experiment's separately bound rubric, not RC0's evaluator machinery.
Permitted exact pairs: `accepted/on_target_adequate`,
`rejected/wrong_subject`, `rejected/wrong_target`,
`rejected/insufficient_context`, `needs-review/uncertain`.

The mechanically built review packet contains only randomized opaque aliases,
exact declared child text with its parent context and exact passage text. Review
the union of **all** reachable top-10 child/passage pairs across A0, semantic and
L0 pools, not only selected passages. Deduplicate the same pair across arms;
different children remain separate. This provides a bounded recall denominator
independent of selected K. Do not show arm, rank, score, selection/admission,
mapping, subject-control assignment, CAL/Decision or predecessor results.

Two distinct fresh task contexts use the same frozen model/profile, each once.
The intended provider is authenticated OpenAI Codex; an exact supported named
model, adapter/config/executable, destination permission and session metadata
must be frozen before launch. No reviewer runs in this setup phase. No inherited
conversation, memory, project/rules/skills, tools or other review. Raw outputs stay
local. No clean-room reproduction or cross-model independence claim is automatic.

Before decisive assessment, the exact reviewer/profile must pass a separately
sealed calibration: both fresh calibration sessions must score **8/8** exact
decision/reason controls correctly. Cases include topical insufficient context,
wrong subject, wrong target, an uncertain fragment, adequate contrary evidence,
adequate unresolved evidence and a partial all_of pair. The partial pair must
cover one child and leave the parent incomplete. Intentionally accept-all and
topical-only control implementations must fail. Actual semantic calibration is
NOT_RUN in Phase 1; development tests of the gate do not qualify the model.
Failed calibration yields INCONCLUSIVE and no fresh scientific reviews.

Decisive reviews must agree on every exact decision/reason pair, with exact
packet binding, complete aliases, distinct fresh sessions and valid minimum
schema. Any disagreement, uncertain label, missing/malformed row or aperture
violation yields INCONCLUSIVE. No adjudicator, third reviewer, replacement,
repair, rescore or post-reveal rubric edit. Gold is the frozen consensus of these
bounded judgments; it does not establish downstream semantic correctness.

## Metrics and numeric gates

For arm X, preserve raw counts per parent, packet and aggregate:

- C(X): required children with at least one accepted retained pair (out of 24).
- P(X): complete all_of parents with both children covered (out of 12).
- R(X): accepted retained pairs / accepted reachable pairs; aggregate micro recall
  and child recall. Zero denominator is reported as undefined, never perfect.
- U(X): retained pairs judged wrong_subject.
- N(X): retained nonaccepted pairs, including wrong subject and insufficient context.
- selected slots, unique passages, accepted pairs and all rejection reason counts.

Do not equate semantic ownership or anchor presence with C or P.

Primary combined support requires **all**:

1. C(A3)-C(A0) >=3 AND C(A3)-C(S0) >=3 (12.5 percentage points of 24).
2. P(A3)-P(A0) >=1 AND P(A3)-P(S0) >=1.
3. Positive child-count gain against both references in at least 2 of 3 packets.
4. C(A3)-C(WS3) >=2; C(A3)-C(WC3) >=2; C(A3)-C(L0) >=2.
5. U(A3)<=U(A0), U(A3)<=U(S0), N(A3)<=N(A0), N(A3)<=N(S0).

If any primary gate fails after valid frozen evaluation, primary result is
**FALSIFIED**. In particular, a wrong/lexical control within one child of A3
reproduces the gain and fails causal discrimination even if A3 beats A0.
These are fixed small-sample practical thresholds, not a significance test or
an estimate of universal performance. They follow the prospective 24-child
design; they are not derived from the RC0 six rejected passages.

Child increment requires C(A3)-C(A2)>=2 and U(A3)<=U(A2), N(A3)<=N(A2).
Failure: `CHILD_COVERAGE_INCREMENT_NOT_REPRODUCED`.

Subject increment requires C(A3)-C(A1)>=2 and C(A3)-C(WS3)>=2 and
U(A3)<=U(A1), N(A3)<=N(A1).
Failure: `SUBJECT_IDENTITY_INCREMENT_NOT_REPRODUCED`.

Primary support with both increments is `SUPPORTED / SUPPORTED_CHILD_AND_SUBJECT`.
Primary support with a missing increment remains **INCONCLUSIVE for the combined
architecture**, preserving the primary threshold result and missing-increment
label separately. Do not promote the combination because one component survives.

Subject-only survival is recorded independently when A2 gains >=3 children and
>=1 complete parent over both A0/S0, gains in >=2 packets, beats WS2 and L0 by
>=2 children, and does not increase U/N versus either reference. Label:
`SUPPORTED_SUBJECT_ONLY`; it does not upgrade a FALSIFIED combined result.
Child-only survival analogously compares A1 with both references and WC1/L0,
with label `SUPPORTED_CHILD_ONLY`. Keep mixed evidence separate.

If zero adequate pairs exist in the complete frozen reachable union, preserve
H6 as `NO_LOCAL_ADEQUACY_OBSERVED_WITHIN_FROZEN_DEPTH` alongside FALSIFIED; do not
claim nothing adequate exists elsewhere. A full-adequacy ceiling also cannot
pass the prospective improvement threshold.

## Attempt budget and stops

One population, one frozen candidate, one execution cohort. Exactly two full
retrieval executions for determinism, same inputs and all arms, separate fresh
directories. Any raw-byte difference or protected-input drift stops INCONCLUSIVE.
No third deterministic run to rescue a mismatch. Exactly two calibration sessions
and, only after they pass, exactly two new decisive reviewer sessions. One result
per session and one consensus tally. No tuning, new K/model/depth/population,
retrieval reroll, annotation repair or successor editing after outcome exposure.
Preflight failure starts no science and remains BLOCKED; an exposed apparatus
defect is preserved and requires a separately identified successor.

All retrieval outputs freeze before decisive judgments; all review bytes freeze
before arm unblinding. Preserve first failures with event, private exposure,
possible conclusion effect, invalidated evidence and legal continuation.

## Phase 1 state and nonclaims

Current scientific state: **BLOCKED before fresh population binding**. Freeze the
protocol, research code, tests, controls and numeric policy as a candidate. This
does not freeze nonexistent packet/runtime/reviewer authority or imply execution
readiness. `CANDIDATE.json` and an external exact commit/tree/blob receipt distinguish
the source freeze from the eventual execution/input freeze.

Next authorized work is input preparation and exact binding, preserving this
policy, then separately qualifying the retrieval/runtime and reviewer aperture
before requesting any necessary destination-specific decisive authorization.
If those steps require changing this policy, use a new preregistration.

No result here establishes automatic subject extraction, universal retrieval,
completeness, authority/applicability, support/refutation correctness, CAL,
automated admission, production readiness, merge/release or promotion.
