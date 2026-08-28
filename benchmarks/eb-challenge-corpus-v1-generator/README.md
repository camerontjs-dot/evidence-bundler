# `eb-challenge-corpus-v1` generator provenance

This directory is an adjacent provenance companion to the frozen
[`eb-challenge-corpus-v1`](../eb-challenge-corpus-v1/) package. It is kept
outside that directory so adding tooling cannot change the frozen corpus tree
hash or its `SHA256SUMS` receipt.

## Exact source files

- `scripts/generate_eb_challenge_corpus.py` — SHA-256
  `8f957bfa9aaa4ee95b108b36ab1659b45c495c96445f909a2ab7c3ec8c30edca`;
- `scripts/validate_eb_challenge_corpus.py` — SHA-256
  `873972bae79034792bfd1931fa4e69fb9393de2c50996161c1fa344cf6e1beb9`.

The generator file is an exact-byte copy of the source named by the historical
freeze receipt. The validator is its required local companion: the generator
imports it after writing the candidate package, while the validator imports
generator constants and hashing helpers.

## Observed dependency closure

The pair uses only Python standard-library modules. The generator also makes
an optional `git` subprocess call to populate source-commit metadata; failure
of that lookup is handled by recording no source commit. It reads no
templates, static files, configuration files, environment variables, network
resources, model weights, or external packages. Its data tables and generation
rules are embedded in the generator source.

The historical source lived under an ignored MainFrame project directory, so
the freeze receipt records `generator_source_commit: null`. The tracked copy
here is provenance tooling, not a new frozen identity.

## Safe invocation

Use an explicitly new output directory and never point the generator at the
frozen package:

```text
python3 -B benchmarks/eb-challenge-corpus-v1-generator/scripts/generate_eb_challenge_corpus.py \
  --output /tmp/eb-challenge-corpus-v1-regeneration \
  --seed 271828 \
  --as-of 2026-08-27
```

The `-B` flag only prevents bytecode side effects. One provenance regeneration
was observed on Python 3.14.4 in a new temporary directory; it produced 60
sources, 946 passages, passed all 16 validation groups, and matched the
historical tree, validation, and freeze hashes. That observation is not a
general reproducibility or regulatory-validation claim.
