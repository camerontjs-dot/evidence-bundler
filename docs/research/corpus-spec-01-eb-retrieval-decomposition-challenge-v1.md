# EB Retrieval + Contract-A Decomposition Challenge Corpus v1

**Status:** preregistered corpus requirements
**Purpose:** shared frozen input for EB retrieval/aperture assurance and Contract-A decomposition-sensitivity research
**Runtime-label rule:** gold relevance/decomposition-quality annotations must never be supplied to Evidence Bundler as runtime input.

## 1. Design goal

Build a controlled but realistic local corpus that lets us measure whether Evidence Bundler:

1. retrieves known relevant evidence and counterevidence;
2. resists lexical distractors and duplicated evidence;
3. preserves exact source/passage provenance;
4. exposes search/aperture limitations rather than laundering partial search into completeness;
5. changes appropriately when proposition meaning changes;
6. remains appropriately invariant to irrelevant formatting/order changes;
7. is sensitive to different claim decompositions without hiding which decomposition produced the search target.

The benchmark is not intended to prove real-world corpus completeness, source legitimacy, regulatory applicability, or CAL semantic correctness.

## 2. Preferred corpus style

Use a **fictional synthetic technical/regulatory micro-world** so every material fact, contradiction, version change and exception is intentionally controllable and no external truth claim is required.

Documents should feel realistic enough to stress retrieval:

- guidance-like documents;
- SOP/policy records;
- validation reports;
- incident/deviation records;
- supplier bulletins;
- change-control notices;
- technical specifications;
- FAQs/knowledge-base articles;
- meeting/decision records;
- superseded and current versions;
- background narrative documents.

Do not use real company names, real patient data, secrets, or claims presented as actual regulatory requirements.

## 3. Minimum size

Target at least:

- **60 source documents**;
- **600-1,200 paragraphs/passages** total;
- **48 base audit claims/questions**;
- **12 challenge families**, at least 4 base claims per family;
- **24 decomposition-sensitive base claims** with A0-A4 variants;
- at least **1 hard negative per base claim**;
- at least **1 decisive counterevidence/qualifier/exception passage** for 50% or more of answerable base claims;
- at least **8 deliberately unanswerable claims**;
- at least **8 aperture-boundary cases** where relevant evidence exists in the full frozen corpus but is intentionally excluded from a declared searchable subset.

Larger is fine if the distribution remains controlled and the generator produces a complete manifest.

## 4. Split policy

Create two immutable splits before EB evaluation:

### Development split

Approximately 25% of base claims.

May be used to debug loaders, metric code, passage-offset validation and benchmark plumbing. Do not use it to justify the final capability claim.

### Sealed test split

Approximately 75% of base claims.

Freeze before implementation tuning. The decisive research result should be based on this split.

The generator may know the test gold. EB runtime must not receive it. Any post-freeze test-label correction requires a deviation record.

## 5. Required challenge families

Include at least these 12 families.

### F01 — Lexically obvious relevance
Positive-control cases with direct term overlap.

### F02 — Synonym / paraphrase drift
Relevant evidence uses different terminology while preserving meaning.

### F03 — Negation / polarity
Near-identical wording changes whether evidence supports, contradicts, or is irrelevant.

### F04 — Numeric / threshold sensitivity
Percentages, counts, durations, limits, tolerances, dates or versions differ by small but material amounts.

### F05 — Temporal / supersession
Older document states one rule/fact; newer version changes or supersedes it. Both remain in corpus.

### F06 — Conditional / exception logic
Relevant evidence turns on `if`, `unless`, `except`, scope restrictions, prerequisites or exemptions.

### F07 — Hard lexical distractors
Irrelevant passages share most claim vocabulary while decisive evidence uses less obvious wording.

### F08 — Duplicate / paraphrased evidence
Multiple documents repeat the same underlying fact. Retrieval must not mistake repetition for independent coverage.

### F09 — Long-document buried evidence
Relevant passage occurs deep inside a long document surrounded by semantically similar material.

### F10 — Multi-passage / compositional evidence
No single passage fully answers the claim; two or more identified passages are jointly necessary.

### F11 — No-answer / insufficient-evidence
Corpus genuinely lacks material evidence required to answer. Retrieval should not hallucinate completeness.

### F12 — Aperture-boundary / inaccessible relevant source
Relevant evidence exists in the full corpus but is absent from the declared searchable subset for that run. The evaluation should distinguish retrieval failure from deliberately bounded aperture.

## 6. Decomposition-sensitive claim families

At least 24 base claims should receive all of the following frozen variants:

- **A0 original:** original claim only;
- **A1 reference decomposition:** legitimate decomposition preserving the intended overall meaning;
- **A2 alternative legitimate decomposition:** different grouping/splitting but defensibly same parent claim;
- **A3 meaning-drifting negative control:** deliberately drops/adds/strengthens/weakens a material condition, quantifier, timeframe, threshold or scope;
- **A4 over-decomposition control:** unnecessarily granular children that may fragment evidence requiring composition.

Prefer parent claims that expose real decomposition hazards:

- conjunctions (`A and B`);
- scoped conditions;
- universal/quantified statements;
- temporal claims;
- numeric thresholds;
- comparative claims;
- claims containing exceptions;
- claims whose evidence spans multiple sources/passages.

For every variant preserve explicit parent/child lineage and exact text. Do not provide the decomposer with gold passage IDs.

## 7. Source construction requirements

Every source must have:

- stable `source_id` independent of file order;
- title;
- fictional document type;
- version/revision where applicable;
- publication/effective date where applicable;
- status where applicable (`current`, `superseded`, `draft`, etc.) as a source fact only;
- exact UTF-8 content bytes or deterministic local representation;
- SHA-256 content hash;
- paragraph/passage boundaries that can be reconstructed exactly.

For PDF-like testing, a deterministic text representation is acceptable for v1. If actual PDFs are generated, also retain the exact generated PDF bytes and a deterministic extracted-text representation so extraction failure can be separated from retrieval failure.

## 8. Gold annotation requirements

Gold annotations live outside the EB runtime corpus.

For each base claim/variant, record:

- `case_id`;
- `split`;
- `challenge_family`;
- original claim ID/text;
- variant/decomposition ID;
- accessible corpus subset ID;
- gold source IDs;
- exact gold passage/span IDs;
- start/end offsets against frozen source representation;
- relevance class;
- whether the passage is **decisive** for the case;
- whether multiple passages are jointly required;
- a short adjudication rationale;
- adjudicator/generator identity;
- gold-record version.

Suggested evaluator-only relevance classes:

- `decisive_support`;
- `decisive_contradiction`;
- `decisive_qualifier`;
- `decisive_exception`;
- `material_context`;
- `hard_negative`;
- `irrelevant`.

These are benchmark labels only. They must not enter Contract A, EB retrieval metadata, Contract B, or CAL as authoritative upstream semantic judgments.

## 9. Aperture subsets

Create named immutable search subsets, for example:

- `full` — all corpus sources;
- `primary_window` — selected subset containing the answer in ordinary cases;
- `bounded_missing_decisive` — same style of search surface but deliberately omits one decisive source;
- `stale_only` — contains an obsolete version but not the superseding source for designated temporal cases;
- `distractor_heavy` — includes many near-match distractors.

The subset definition itself is evaluator/input configuration, not a hidden corpus mutation after the run.

## 10. Order and representation metamorphics

Produce deterministic alternate manifests for at least:

- source enumeration permutation;
- paragraph enumeration permutation where semantic coordinates remain valid;
- harmless metadata-order changes;
- duplicate-document insertion;
- paraphrased duplicate insertion.

Do not overwrite the canonical source bytes. Treat each transformed corpus view as a separately identified fixture derived from the same frozen base.

## 11. Required output layout

Preferred layout:

```text
eb-challenge-corpus-v1/
  README.md
  corpus_manifest.json
  SHA256SUMS
  sources/
    src-0001/
      content.txt
      metadata.json
    ...
  cases/
    dev_cases.jsonl
    test_cases.jsonl
  decompositions/
    dev_decompositions.jsonl
    test_decompositions.jsonl
  aperture/
    subsets.json
  gold/
    dev_relevance.jsonl
    test_relevance.jsonl
    gold_manifest.json
  transforms/
    transform_manifest.json
  validation/
    corpus_validation_report.json
```

Equivalent machine-readable layouts are acceptable if all identities and hashes remain explicit.

## 12. Manifest requirements

`corpus_manifest.json` should include:

- corpus name/version;
- generator name/version/commit if available;
- random seed(s);
- generation timestamp;
- counts by split/challenge family/document type;
- source IDs and content hashes;
- case/decomposition IDs;
- aperture subset identities;
- transform identities;
- hash of each gold file;
- overall deterministic corpus tree hash.

Record the generator prompt/config hash if an LLM participates in corpus generation.

## 13. Validation before handoff

The local build should fail if:

- IDs are duplicated;
- referenced source/passage IDs do not exist;
- span offsets do not recover the intended text;
- SHA-256 values do not match bytes;
- a case assigned `no-answer` has a gold decisive passage;
- a required answerable case has no gold material passage;
- A1/A2/A3/A4 lineage references a missing parent;
- an aperture subset references missing files;
- test cases or source files contain gold IDs/labels as hidden hints;
- source ordering affects IDs/hashes;
- required challenge-family minimums are not met.

Emit a machine-readable validation report with pass/fail counts.

## 14. Evaluator contamination guard

The EB process under test may receive:

- source corpus bytes and allowed source metadata;
- the claim/audit proposition or decomposition variant being tested;
- the declared aperture/search subset;
- ordinary EB configuration.

It must **not** receive:

- gold relevance labels;
- gold source/passage IDs;
- challenge-family labels if they would reveal the expected behavior;
- expected rank/order;
- adjudication rationale;
- generated query terms chosen to point directly at the gold evidence.

## 15. Freeze receipt

Before the first decisive test run, record:

- corpus tree hash;
- generator version/commit;
- generator prompt/config hash where applicable;
- random seed(s);
- validation-report hash;
- dev/test case counts;
- exact EB SHA/config to be tested.

Any corpus change after that point requires a new corpus version or an explicit deviation record.
