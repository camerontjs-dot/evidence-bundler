# Proposition Compiler Competing-Hypothesis Reranker RC0

Status: development calibration authorized under issue #66.

Class: Research Infrastructure / bounded evaluator-measurement experiment.

This experiment does not authorize a Proposition Compiler, production decomposition, Contract A/B/C changes, production Evidence Bundler behavior, retrieval/CAL/Decision changes, merge, release, or promotion.

## Exact base and predecessor

- Evidence Bundler protected `main`: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- predecessor multi-proposer decisive head: `b25fa4743e16f40186d29bec3757c378733b7791`
- predecessor disposition: `SUPPORTED_FOR_FRESHER_QUALIFICATION`

## Question

Can a reproducible cross-encoder ranking lane order semantically faithful same-root decompositions above adversarial near-misses, with a calibrated abstention rule that fails closed on ambiguity, strongly enough to serve as a proposal-triage lane before independent semantic authority?

The experiment does not ask whether a reranker is semantic authority.

## Systems

- `B0_lexical`: root/candidate token Jaccard.
- `R1_generic`: `cross-encoder/ms-marco-MiniLM-L6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a`.
- `R2_bidirectional_nli`: `cross-encoder/nli-deberta-v3-small@fa2804872c3b4bd748f38c0185cc85775361e735`, scored by the minimum of root→candidate and candidate→root entailment probabilities.

The prior Semantic-4K evidence-retrieval experiment falsified R1's usefulness as a passage-compression reranker. RC0 deliberately tests a distinct task: same-root decomposition-candidate ordering.

## Candidate representation

A candidate decomposition is rendered as the conjunction of its children:

`(child 1) AND (child 2) ...`

When explicit context is supplied it is included symmetrically with the root and candidate representation. Gold labels are never consumed by the scorer.

## Development surface

Twelve visible roots, four candidate decompositions each. Families include scope, polarity, modality, quantification, directional binding, comparison, attribution, reference binding, completeness/duplication, multiple legitimate realizations and intrinsic ambiguity.

Development gold is used only after raw model scores freeze.

## Calibration

Each system receives a deterministic `SELECT` / `ABSTAIN` rule defined by:

- score floor from `{0.0, 0.25, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9}`;
- top1-vs-top2 margin from `{0.0, 0.01, 0.025, 0.05, 0.1, 0.15, 0.2}`.

For each system, choose among zero-unsafe development rules by:

1. maximum safe selections;
2. maximum correct ambiguity abstentions;
3. higher score floor;
4. larger margin.

If no zero-unsafe development rule exists, record `NO_ZERO_UNSAFE_CALIBRATION`; do not repair the model or grid after observing the result.

## Development stop / freeze

After a valid hosted development run:

1. preserve raw scores and exact replay hash;
2. freeze scorer source, calibration source, evaluation source and model revisions;
3. freeze the calibration output;
4. only then author the fresh decisive root/candidate corpus and fresh gold.

No scientific code/model/threshold repair is permitted after fresh corpus construction begins. A successor experiment is required instead.

## Fresh decisive surface

After freeze construct 24 roots with at least 96 candidate decompositions. Include:

- at least 12 critical scope/operator/direction/binding mutants;
- at least 2 roots with multiple legitimate decompositions;
- at least 4 intrinsic-ambiguity roots that must abstain;
- no exact root wording reused from the development or predecessor decisive cohorts.

## Fresh metrics

Per system preserve:

- top1 safe preference rate on selectable roots;
- pairwise safe-over-unsafe ordering rate;
- pairwise safe-over-critical-unsafe ordering rate;
- calibrated safe selections;
- unsafe selections;
- correct ambiguity abstentions;
- false abstentions;
- per-root top score and margin;
- raw/replay/calibration/evaluation hashes.

## Terminal rules

`FALSIFIED_AS_JUDGE_REPLACEMENT` if R2:

- selects any unsafe fresh candidate;
- selects any candidate on an intrinsic-ambiguity root;
- fails any critical safe-over-unsafe pairwise ordering;
- cannot obtain a zero-unsafe development calibration;
- requires post-result repair;
- or exact replay changes.

`SUPPORTED_AS_TRIAGE_LANE` requires all of:

- zero unsafe R2 fresh selections;
- all fresh ambiguity roots abstain;
- critical pairwise safe-over-unsafe rate = 1.00;
- overall pairwise safe-over-unsafe rate >= 0.95;
- R2 safe selections > lexical baseline safe selections;
- exact replay byte-identical;
- exact identities and receipts preserved;
- maintained hosted CI success.

Otherwise use `INCONCLUSIVE` unless superseded by an apparatus-validity failure.

A positive result supports only a reranker as a bounded triage/ordering lane. It does not confer semantic authority and does not establish that an LLM/checklist reader is unnecessary outside the tested profile.
