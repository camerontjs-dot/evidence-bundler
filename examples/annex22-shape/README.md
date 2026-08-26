# Annex 22 shape stress packet

This directory is an **exploratory schema fixture**, not a validated evidence bundle and not an interpretation of binding GMP.

It uses the European Commission's 2025 consultation draft of proposed GMP Annex 22 (Artificial Intelligence) to pressure-test the Evidence Bundler's persisted shape. The draft is useful because it contains numbered requirements, applicability limits, conditions, exceptions, multi-clause obligations, lifecycle requirements, and source-status ambiguity that a simple `claim -> supporting passages` representation tends to flatten.

The fixture deliberately uses short **paraphrases** rather than reproducing the draft text. Its purpose is to test representation, not requirement extraction fidelity.

## Questions this fixture must answer

For every claim, can a downstream auditor determine without hidden state:

1. Where the claim came from?
2. Which source version/status is in scope?
3. Which exact source locations are relevant?
4. Why each passage is linked to the claim?
5. Whether that relationship was produced by retrieval or accepted by review?
6. Whether the evidence set is empty because nothing was found, everything was rejected, or review is incomplete?
7. Whether a claim is composite and has been decomposed?
8. Which bytes/representation an offset refers to?

If a required answer lives only in free-text notes, treat that as evidence that the shape is underspecified.

## Files

- `prototype-bundle.yaml` — one-file prototype of the proposed entities and links. Keeping it in one file is intentional: this tests semantics before committing to a directory layout or Pydantic API.
- `../../docs/annex22-bundle-shape-spike.md` — rationale, current C-B diagnosis, proposed v2 boundary, and acceptance gates.

## Stress cases

| ID | Pressure |
|---|---|
| A | Draft source status + scope limitation |
| B | Composite intended-use obligation |
| C | Qualification by subgroup/baseline criteria |
| D | One conclusion requiring several source locations |
| E | General rule with procedural fallback |
| F | Distinct requirement and review requirement |
| G | Conditional applicability + explicit undecided outcome |
| H | Lifecycle obligation spanning multiple controls |
| N1 | No candidates retrieved |
| N2 | Candidates retrieved but all rejected |
| N3 | Partial review |
| N4 | Evidence admitted, but draft source status limits what can be concluded |

A-H test representational richness. N1-N4 are negative controls for coverage semantics.

## Decision rule for the next iteration

Do **not** implement this as C-B v2 merely because the fixture is expressible.

First compare it against the smallest backward-compatible extension of C-B v1.x. Prefer the smaller extension if it can represent every stress case without:

- putting CAL run state inside evidence identity,
- treating retrieval scores as evidentiary relations,
- using notes for structurally essential state,
- losing claim origin or source status,
- conflating the four negative-control outcomes.

If v1.x cannot pass those gates cleanly, that is evidence for a versioned C-B redesign rather than aesthetic preference.
