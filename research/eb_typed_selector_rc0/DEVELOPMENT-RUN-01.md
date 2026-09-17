# Development Run 01 — Preserved Negative Result

Classification: **development observation only / not a research disposition**

Hosted run: `35185340754`

Tested head: `b32f4c2a38bc47005b5ad004f05ae4bdc2c2410c`

Tree: `94afa7c609c5239f98ef2e6bdc147a0f85fad9b6`

Known-case selection SHA-256: `01a1c45bee51b6af389f6c1b4c8b44e3065f77907b21aa3045f2507f88718456`

Known-case evaluation SHA-256: `9e445d5039992491fa055ab847d63e35628b1cd4bb045a1ce8619be4a63cd99b`

Selector SHA-256: `978759aec5a2bed531297a1fbd87edc2e450afacbf5e67fcbaca1b93fa238f5f`

Development-profile SHA-256: `ce8361811c0bc81fff0131e58b1695b5e9ecab82a49a18ad16ab6412b07e9a1b`

Hosted artifact: `10481564156`

## Systems observations

- apparatus controls: PASS;
- six unit/weak-control tests: PASS;
- synthetic replay: byte-identical;
- exact predecessor artifact digest: PASS;
- pinned generic semantic scorer execution: PASS;
- known-case selector replay: byte-identical;
- answer-bearing evaluation occurred only after selection bytes were frozen for the run.

## Known-case observations

### C06 hard negative

Expected exposed development KEEP: `C06-P1`, original BM25 rank 4.

- BM25 top-3: miss;
- semantic top-3: miss;
- full typed top-3: miss;
- typed without profile: miss;
- typed without semantic: miss;
- **typed without local-span: rescue**.

The characterization exposed why. The three lexical hard negatives all had `local_span_recall = 1.0`; `C06-P1` had only about `0.364`, even though its profile compatibility was highest (`0.9`). The local-span feature therefore rewarded proposition-token copying inside explicit non-result statements and suppressed the short measured-result passage.

### Retrieval-aperture long-context case

Expected exposed development KEEP: `RET-AP-P6`, original BM25 rank 7.

Every arm missed it.

`RET-AP-P6` had strong available signals: semantic relevance about `0.969`, local-span recall `1.0`, profile compatibility `1.0`. But ranks 1–5 also appeared nearly perfect to those same measurements because they repeat the exact proposition in different discourse roles:

- rejected hypothesis;
- unverified draft claim;
- unanswered question / no conclusion;
- hypothetical scenario;
- template/example.

## Development inference

The first selector is not ready to freeze.

The result weakens the idea that whole-passage semantic relevance plus lexical local-span coverage and concept compatibility are sufficient for the known retention failures. Both exposed cases require distinguishing **an evidentiary assertion/result from a mention, rejection, hypothetical, unresolved question, or explicit non-result use of the same proposition vocabulary**.

This is candidate-side evidence/discourse-form characterization, not a SUPPORTS/REFUTES verdict. It is within issue #80's stated evidence-form hypothesis.

## Authorized next development change

Before scientific freeze, add one explicit inspectable evidence-posture signal that can distinguish direct/assertive evidence from clearly marked non-assertive/disclaimed forms. Keep it separable from semantic relevance and add an ablation so its contribution is testable.

Do not change first-stage retrieval, the semantic model, K=3, the candidate pool, CAL, Contract B, or the frozen integration candidate.
