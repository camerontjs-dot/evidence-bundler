# Proposition Compiler Evaluator RC0 — Terminal Results

Disposition: `FALSIFIED`

This is the terminal result for the exact frozen RC0 development evaluator. Per issue #59, no semantic repair is permitted in this experiment after the decisive raw target output.

## Frozen base and apparatus

- Evidence Bundler base: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- evaluator.py SHA-256: `d6dcda3c053e4cb68a65aa8bcb01404e72e084cdd735068c6e6935cf8cb71643`
- controls.py SHA-256: `0ada71aed251a298434dba847e075616363eafd2a3383718dc21d3541dcf8445`
- scorer.py SHA-256: `e0f279426c9f1687d9058d06091a659dbdec71dbee5d661e425b10206f946d8b`
- annotation spec SHA-256: `e52bb01dc8a44fa2a354a66af6e4853e33f5c1495e13d14eaa014b8046bceb06`
- core candidates SHA-256: `1e1c2977573ae559ea72849109635dbe24acb804006f4585d053052ef2701846`
- metamorphic candidates SHA-256: `eaea3c6771ba169bd0d1d3363e0b4b5690ad70042f70ecbfcd0d1d84eadf97ab`
- gold SHA-256: `9c481d0215c7ea3531dc4ca28ab802cb543f8aeddd0d39f6e990909c17e7965d`
- metamorphic relation gold SHA-256: `b3f9d83533f53705042bf1bad0f3a145de6a895c0fb0db56478745dc23d39f0f`

## Raw-before-gold receipt

- target raw SHA-256: `06afbef245722355c728de43ff9aa60878814927be4dfec8281d737458924311`
- exact replay byte-identical: `true`
- core candidates: `150`
- metamorphic follow-ups: `40`

The decisive runner wrote and hashed target/control raw outputs before opening gold for scoring.

## Decisive falsifiers

The target accepted **10** preregistered critical unsafe candidates as `ACCEPTABLE_WITHIN_PROFILE`:

- `R04-swap-object`
- `R04-fragment`
- `R06-or-change`
- `R14-scope-loss`
- `R15-drop-unit`
- `R19-partial-strip`
- `R21-swap`
- `R21-cross`
- `R23-cross`
- `R25-wrong-ref`

It also accepted **2** cases that were preregistered `INDETERMINATE` ambiguity probes:

- `R29-router`
- `R29-controller`

Those outcomes independently satisfy the issue #59 `FALSIFIED` stop rule.

## Aggregate observations

- Exact core disposition agreement: `135/150`
- Metamorphic relations satisfied: `34/40`
- Deterministic replay: PASS

Aggregate accuracy is not a promotion gate and does not offset the unsafe accepts.

## Counterexample clusters

The falsifiers concentrate around the exact research risk identified before implementation:

1. **Argument / referent binding** — object swaps, acquisition-role swaps, cross-bound relation arguments, and wrong contextual referents passed because aggregate lexical coverage did not preserve predicate-to-argument binding.
2. **Child-local operator attachment** — assertion-type stripping and unit/scope loss passed when the operator or unit remained somewhere else in the child set. Global retention was insufficient.
3. **Propositionhood / auditability heuristic weakness** — subjectless fragments could still look proposition-like under the simple verb/token heuristic.
4. **Connective semantics** — an `or` mutation inside a child was not robustly rejected as a connective change.
5. **Ambiguity recognition** — competing coreference readings were accepted rather than failed closed.

There were also conservative false rejects on safe condition, negation, and hedge cases, showing that the propositionhood/verb heuristic is too brittle even while the evaluator remains unsafe in other directions.

## Metamorphic failures

- `MI08A` (child_order_permutation): expected `ACCEPTABLE_WITHIN_PROFILE`, observed `REJECT_UNSAFE`
- `MI08B` (insignificant_whitespace_punctuation): expected `ACCEPTABLE_WITHIN_PROFILE`, observed `REJECT_UNSAFE`
- `MR06A` (subject_object_swap): expected `REJECT_UNSAFE`, observed `ACCEPTABLE_WITHIN_PROFILE`
- `MR06B` (subject_object_swap): expected `REJECT_UNSAFE`, observed `ACCEPTABLE_WITHIN_PROFILE`
- `MD03A` (introduce_coreference_ambiguity): expected `INDETERMINATE`, observed `REJECT_UNSAFE`
- `MD03B` (introduce_coreference_ambiguity): expected `INDETERMINATE`, observed `REJECT_UNSAFE`

## Weak-control interpretation

All locally available weak controls failed substantial decision expectations, so the corpus has discriminatory value against those controls. Several planned external-model/parser controls were unavailable and were explicitly recorded as unavailable rather than simulated. This does not rescue the target evaluator; its own critical unsafe accepts are decisive.

## Epistemic disposition

**OBSERVED:** the exact frozen evaluator is deterministic but does not reliably preserve semantic binding/attachment under the RC0 corpus.

**SUPPORTED:** the adversarial corpus successfully exposed failure modes that the six-root smoke pilot did not. This supports the research decision to use minimal semantic mutations rather than relying on pilot accuracy.

**NOT SUPPORTED:** promotion of this evaluator to fresh qualification; any claim that aggregate lexical/operator retention is sufficient for Proposition Compiler semantic conservation.

**UNKNOWN:** the smallest successor architecture that will safely capture argument binding, local operator scope, and ambiguity without becoming an unrestricted semantic parser.

## Smallest successor

Do not expand the compiler. The next experiment should isolate the three strongest failure classes with a smaller discriminating target: (1) predicate/argument binding, (2) child-local operator/qualifier attachment, and (3) ambiguity/profile gating. Reuse the frozen counterexamples as regression evidence but create fresh minimal pairs for the successor's decisive gate.
