# eb-challenge-corpus-v1

This package is a frozen, fully fictional technical/regulatory micro-world for
two separate experiments:

1. retrieval evaluation for an Evidence Bundler-like system; and
2. claim-decomposition evaluation using independently generated A0-A4
   variants.

It is not a regulatory requirement set, compliance opinion, software
qualification, validation record, or evidence about a real organization. All
organizations, systems, products, dates, thresholds, procedures, incidents,
and document histories are synthetic.

## Runtime and evaluator boundary

The retrieval runtime may receive only:

- source bytes and permitted source metadata under sources/;
- a case from cases/;
- the named source subset from aperture/subsets.json; and
- ordinary runtime configuration in the case.

The evaluator-only files under gold/ and the decomposition metadata under
decompositions/ must remain outside the runtime corpus. The runtime must not
be given challenge-family labels, relevance labels, gold source or passage
identifiers, adjudication rationales, expected rankings, or expected outputs.

corpus_manifest.json, SHA256SUMS, and validation/ are control and verification
artifacts, not retrieval hints. A clean runtime mount should explicitly
allowlist the runtime directories above.

## Frozen layout

sources/ contains 60 exact UTF-8 source representations with stable source
identity keys, SHA-256 content hashes, and deterministic paragraph spans.
cases/ contains 148 runtime cases: 37 development cases and 111 sealed-test
cases. The 52 base claims cover the twelve required challenge families; eight
are full-corpus no-answer controls. Twenty-four base claims have A0 through A4
decomposition variants.

The five immutable named apertures are full, ordinary_window,
bounded_missing_decisive, stale_only, and distractor_heavy.
transforms/ contains separately identified non-canonical metamorphic views.

## Reproduction

The generator is deterministic from the recorded seed, as-of date, fixed
generation timestamp, configuration hash, and generator source commit. The
canonical build command used for this version is:

    python3 scripts/generate_eb_challenge_corpus.py --output eb-challenge-corpus-v1 --seed 271828 --as-of 2026-08-27

The generator refuses to write into a non-empty directory unless --force is
explicitly supplied. Do not regenerate this frozen directory after the freeze
receipt; create a new corpus version for corrections.

## Interpretation boundary

Gold annotations are evaluator judgments about this synthetic package only.
They are not independent regulatory truth, and a passing construction check
does not establish retrieval accuracy, decomposition quality, or CAL
validation.
