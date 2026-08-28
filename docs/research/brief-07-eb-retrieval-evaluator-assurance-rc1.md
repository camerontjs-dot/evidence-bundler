# EB Retrieval Evaluator Assurance RC1

## PR class

Research Infrastructure. Production Evidence Bundler behavior is out of scope and must remain unchanged.

## Decision

Determine whether the evaluator used to measure retrieval/aperture behavior on `eb-challenge-corpus-v1` is sufficiently validated to authorize a later, separate Evidence Bundler retrieval experiment.

This RC does **not** evaluate real Evidence Bundler retrieval output.

## Frozen apparatus

- benchmark commit: `22b227ec2c34a085efc79267bc007ff78607aeed`
- corpus tree SHA-256: `eee87cff5e86a3d0a3cdaaa762837ca90ae60f62939309c1dc335a19884c78a8`
- corpus: 60 sources / 946 passages / 52 base claims / 148 runtime cases
- dev/test split: 37 / 111 cases
- decomposition records: 120 over 24 base claims
- challenge families: F01-F12

A hash mismatch is a stop condition. Corrections require a new benchmark version or an explicit deviation record.

## Pre-existing evaluator debt

1. `validation/freeze_receipt.json` pins `generator_source_sha256` but records `generator_source_commit: null`. Artifact identity is strong; independent regeneration from committed generator source is not established.
2. Relevance rows contain both row-level `source_id` / `passage_id` and repeated case-level `gold_source_ids` / `gold_passage_ids`. Their scoring roles must be explicit before evaluation.

## Gold interpretation decision

The evaluator shall treat each relevance JSONL row as one annotation whose exact identity is the row-level source plus passage/anchor fields:

`(source_id, passage_id, exact_start_offset, exact_end_offset, offset_unit)`.

Rows with `decisive: true` are the authoritative decisive annotations for scoring. `relevance_class` determines whether the annotation contributes to support/counterevidence/qualifier/exception/material-context diagnostics. `joint_group_id` plus `jointly_required: true` defines all-of evidence groups.

The case-level `gold_source_ids` and `gold_passage_ids` are **case summary/integrity fields**, not row identity. They are repeated even on hard-negative rows. The evaluator must derive the decisive passage/source sets from row-level decisive annotations and verify that every row's case-level summaries agree with those derived sets. A mismatch is an evaluator input error and stops scoring for that case. This avoids silently choosing one representation over the other.

## Generic retrieval-result boundary

The evaluator accepts a retriever-neutral result containing:

- `case_id`
- ordered `hits`
- each hit's `source_id`
- each hit's `passage_id` **or** exact anchor (`start_offset`, `end_offset`, `offset_unit`)
- rank
- optional retriever score
- optional returned text, which is diagnostic only and never rescues provenance
- actual searchable subset identity
- observed search-scope facts
- completeness claim, including explicit `unknown` / `not_established`
- configuration/run identity

No field is required merely because production EB currently emits it.

## Provenance rule

Gold credit requires an exact frozen identity match. Text similarity, copied span text, or a near-correct passage with corrupted source/passage identity receives no gold credit.

For paragraph-order metamorphic views, anchor-based hits must first be mapped through the transform's supplied anchor mapping before comparison with canonical gold. Stale canonical offsets against transformed text are invalid.

## Budget rule

`K` is the case's `runtime_config.maximum_passages`. Coverage metrics are computed only over ranks `<= K`. Returning more than K hits is a budget violation even when unbounded recall is high. Budget violations are critical-gate failures.

## Metrics

### Retrieval coverage

For cases with accessible decisive annotations:

- case-level accessible decisive-evidence hit@K
- decisive annotation recall@K
- first-decisive reciprocal rank plus rank distribution
- decisive counterevidence/refutation recall where such annotations exist
- decisive qualifier/exception recall where such annotations exist
- material-context recall where such annotations exist

Cases with no accessible decisive annotation are reported as not-applicable for positive coverage, not forced to zero.

### Multi-passage composition

For each `joint_group_id`:

- complete joint-group coverage@K: all required distinct member identities retrieved
- partial joint-group coverage@K: at least one but not all required members retrieved

Duplicate retrieval of one member never creates complete-group credit.

### Hard negatives

Report:

- hard negatives ranked before first decisive evidence
- hard-negative proportion in the bounded top-K result
- F01-F12 family breakdown

Hard-negative retrieval is not itself a semantic verdict error.

### Aperture

Report separately:

- actual searchable subset
- observed search-scope facts
- completeness claim
- aperture-assurance violations

A bounded search claiming `unknown` / `not_established` completeness is not failed merely because completeness is unavailable. A bounded search claiming full/comprehensive corpus coverage is a critical false-completeness failure.

### Family reporting

F01-F12 remain separate. Aggregate summaries are convenience views only.

## Preregistered later-EB thresholds

These thresholds are defined before any real EB retrieval output is inspected. They are risk-oriented engineering gates for a **bounded useful retrieval/aperture assurance claim**, not empirically calibrated estimates of real-world error.

### Critical gates: all required

1. zero result-schema errors on evaluated cases;
2. zero retrieval-budget violations;
3. zero false full/comprehensive aperture claims;
4. exact provenance matching only; no text-similarity rescue path;
5. deterministic evaluation output reproducible under canonical serialization;
6. no family may be omitted from reporting.

### Coverage gates

Among cases where decisive evidence is accessible within the named aperture:

- case-level decisive hit@K >= **0.95** overall;
- decisive annotation recall@K >= **0.90** overall;
- decisive counterevidence/refutation recall >= **0.90** when applicable;
- decisive qualifier/exception recall >= **0.90** when applicable;
- complete joint-group coverage >= **0.90** when applicable;
- each applicable answerable family must have case-level hit@K >= **0.75** and decisive annotation recall@K >= **0.70**.

Rationale: the bounded claim is meant to support assurance, so average recall below nine-in-ten decisive annotations is too weak; the per-family floor prevents an easy-family average from hiding catastrophic family-specific failure. The 0.95 case-hit gate is stricter than annotation recall because a case with no decisive evidence retrieved is a qualitatively larger failure than missing one member of a multi-annotation case. These numbers are preregistered design tolerances, not claims that 90/95% is universally safe.

First-decisive rank and hard-negative metrics are authoritative diagnostics but are not independent pass gates in RC1; their primary failure mode is already captured when distractors crowd decisive evidence beyond K.

### Support / weaken / inconclusive for the later EB experiment

**Supports the bounded EB claim:** every critical gate passes and every applicable coverage gate meets threshold on the frozen evaluator/corpus.

**Materially weakens/falsifies the bounded claim:** any critical gate fails, an overall coverage gate misses threshold, or any applicable family falls below its floor.

**Inconclusive:** required evaluator state is missing/ambiguous, a corpus/evaluator identity cannot be verified, an evaluator defect affects acceptance logic, or execution is not reproducible.

These criteria must not be changed after inspecting EB output without an explicit deviation/new RC.

## Evaluator-assurance controls

Before any real EB run, execute synthetic retrievers C0-C8:

- C0 Null
- C1 Gold oracle
- C2 First-N/source-order
- C3 lexical-overlap-only weak retriever
- C4 return-everything gamer
- C5 provenance-corrupt retriever
- C6 aperture liar
- C7 honest bounded retriever
- C8 hard-negative-biased retriever

Expected qualitative behavior follows the experiment prompt. Unexpected control behavior is evidence about the benchmark/evaluator and must be preserved.

## Metamorphic / mutation controls

Validate at minimum:

- source-enumeration permutation invariance;
- harmless metadata-order invariance;
- exact duplicate insertion cannot create independent-evidence credit;
- paraphrased duplicate insertion cannot create independent-evidence credit without frozen gold identity;
- paragraph-order transforms use supplied anchor mapping;
- isolated mutation of one required gold identity changes/fails the affected evaluation.

Canonical benchmark files must not be mutated.

## Determinism

Run deterministic controls at least twice. Canonically serialized result bytes must be identical. Record SHA-256 of evaluator configuration and result artifact, plus material runtime/tool versions.

## Stop conditions

Stop before evaluating EB if:

- corpus tree hash mismatches the frozen receipt;
- gold interpretation cannot be validated;
- C4 or C6 can obtain an unqualified pass;
- C5 corrupted provenance scores as valid decisive evidence;
- deterministic output cannot be reproduced;
- a material evaluator bug requires changing acceptance criteria after controls run.

A corrected evaluator may be rerun only with an explicit deviation record.

## Assurance-level ceiling

RC1 can establish at most E3 from its own synthetic, mutation, metamorphic and gaming controls. E4 requires an actually independent cross-check. E5 requires sufficient evidence for the named bounded decision and should not be inferred merely from green local controls.

## Explicit non-claims

This work does not establish:

- real Evidence Bundler retrieval quality;
- corpus completeness or real-world representativeness;
- correctness of the synthetic gold as regulatory truth;
- source legitimacy/authority;
- claim-decomposition correctness;
- CAL semantic-evaluator correctness;
- independent generator regeneration from a committed generator source;
- production readiness of any EB retrieval change.
