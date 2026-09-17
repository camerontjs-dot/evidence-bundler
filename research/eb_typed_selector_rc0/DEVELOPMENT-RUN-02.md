# Development Run 02 — Evidence-Posture Successor

Classification: **development observation only / not a research disposition**

Hosted run: `35185668550`

Tested head: `58fe2af351c0925c3a4a561eb285095d7e31d97c`

Tree: `fb872171e1ac422c5ae8b97f625893dd2c650580`

Known-case selection SHA-256: `45143716f7321583fe2d7159065e4a12c2d7e0159f9eb74a02baa53c5d3ffa79`

Known-case evaluation SHA-256: `2be8335c58bb01b791fe69655337d5ff61edfb4d636ddfa1a3f4ebcedddb8bed`

Selector SHA-256: `e83e6305008a0f7a264cde2167bff80ce6399f03d34ebce10376f106c52cec6c`

Development-profile SHA-256: `cfd629145e46fd5d10daf818bff66396fb413232c14306e96ba191c0aae2c08f`

Hosted known-case artifact: `10482301685`

Hosted known-case artifact ZIP SHA-256: `a49f44e0d609684b3d7ab072327d2deb216f83b0b177909905e178a0494b2aaf`

Hosted apparatus artifact: `10482485897`

Synthetic replay SHA-256: `7308cbaeff2ede8db4014c4a5b823f5c085c56569d86ab9bc8909218040015ed`

## Systems observations

- compile: PASS;
- `8` apparatus / weak-control tests: PASS;
- synthetic replay: byte-identical;
- exact predecessor artifact digest: PASS;
- pinned semantic scorer execution: PASS;
- known-case selector replay: byte-identical;
- answer-bearing evaluation occurred only after selection bytes were frozen for the run.

## Known-case observations

### C06 hard negative

Exposed development KEEP: `C06-P1`, original BM25 rank 4.

- BM25 top-3: miss;
- semantic top-3: miss;
- full typed top-3: **rescue**;
- typed without evidence-posture: rescue;
- typed without local-span: rescue;
- typed without profile: rescue;
- typed without semantic: rescue.

The full typed selected set was `C06-P1`, `C06-P2`, `C06-P4`.

This establishes development recovery of the target but does **not** isolate evidence posture as the causal basis of the C06 recovery. The successor also rebalanced the other signal weights. The selected set still contains passages that may create burden, so this case alone is not enough to freeze the selector.

### Retrieval-aperture long-context case

Exposed development KEEP: `RET-AP-P6`, original BM25 rank 7.

- BM25 top-3: miss;
- semantic top-3: miss;
- full typed top-3: **rescue**;
- typed without evidence-posture: **miss**;
- typed without local-span: rescue;
- typed without profile: rescue;
- typed without semantic: rescue.

The full typed selected set was `RET-AP-P6`, `RET-AP-P7`, `RET-AP-P4`.

On this exposed case, evidence posture is decision-discriminating: removing it returns to the miss while removing the other individual signal families does not.

## Development inference

The successor is materially more promising than Run 01, but it is **not ready for scientific freeze yet**.

Observed support is narrow:

- full typed selection recovers both known deep misses;
- ordinary semantic-only recovers neither;
- evidence posture has explicit weak-control discrimination on the retrieval-aperture case.

Remaining concern:

- recovering a known KEEP does not establish acceptable set composition or reviewer/distractor burden;
- C06 recovery is not uniquely attributable to evidence posture;
- the answer-aware two-case development profiles cannot support a general selection claim.

## Next discriminating development check

Before freezing the selector, run one broader retrospective screen over all 18 frozen normative lanes using the existing 96-relationship operational label authority.

Use a deliberately non-answer-aware generic profile (`requires_direct_evidence=true`, no case-specific concepts) so the screen tests selector burden and broad operational KEEP survival rather than tuning per-lane profiles.

Compare at least BM25 top-3, semantic top-3, full typed top-3, and the evidence-posture ablation on the exact same frozen candidate pool.

Do not alter the selector based on individual full-pool labels before recording that screen.
