# Evidence Bundler Retrieval Assurance RC2 — Terminal Apparatus Result

## Decision

**SUPPORTED FOR PROMOTION**

This disposition is bounded to one claim only:

> The exact frozen RC2 retrieval-assurance apparatus identified below is sufficiently discriminating for handoff unchanged to a later, separate real-Evidence-Bundler RC2 experiment.

It does **not** establish Evidence Bundler retrieval quality, production readiness, superiority to a weak baseline, corpus completeness, Contract-A decomposition quality, or any production release claim.

`REAL EB RC2 EXPERIMENT AUTHORIZED AGAINST THIS EXACT FROZEN APPARATUS`

No real Evidence Bundler output was executed or inspected in this assurance task.

## Exact frozen identity

First decision-relevant hosted sealed run:

- GitHub Actions run: `33183653897`
- apparatus commit: `82ec006e888e22c5e5cde600546c05cc6e0b5e33`
- apparatus composite SHA256: `9d3599e34c5ff6eda05e91370c77010ca2f28c9294a69f76972098ad0838673d`
- first sealed control output SHA256: `d3cdc3ac7c356cc4ec0edc06b6d149bc80082e861b078e8ef94a2df9ad8dfb74`

Frozen apparatus components:

- generator SHA256: `eccb586d8366ba6f878ffb323315b81251017153a5ef892d407594818cba7086`
- validator SHA256: `6b73492b724ed4d7bf76114d1f71c26fb66e8ac00f8dfd5d0b3f55cf2109e1fd`
- evaluator SHA256: `c443a64a2c2dfe8c9b0decd8c0414c1e7bb1069d86d3355dd0202fa9725aff08`
- control runner SHA256: `7735fd74dc46dc0ddb46f031cfb2fa9a24578e3c47b406243811be1cdfbe709d`
- thresholds SHA256: `9df75b448ff5090d9bd2821f624e327d47ba5ea9848460cf69518bb6b04ea05a`
- result schema SHA256: `26a56b08c90277f6d13434d5bb5db4a0f71edc925ff78db6de285b6a4b992dd0`
- preregistration SHA256: `aa864c77294d0158b98537170e5262e4369c2e15e420cb1f57199d5a2759ae4a`

Frozen benchmark:

- name/version: `eb-retrieval-assurance-rc2-v1` / `1.0.0`
- deterministic seed: `161803`
- benchmark tree / `SHA256SUMS` SHA256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`
- manifest SHA256: `10b71aeca95e62792f499d9f54db253db4162556d414e8d51da353bd38066fa1`
- freeze receipt SHA256: `527799e8f2914bd290d23e90eedc18e5eccf9f30cadd7a1906a2a05d3143ec18`
- runtime passages SHA256: `352ce375a9b2e987f5a7fc686c4560d018646e56a13743027b0b06602cf66dbd`
- runtime apertures SHA256: `9f11111aee7bc9b0b0c798184b09efb0d2502c8463d63fef3ed2d08d598ad236`
- runtime dev cases SHA256: `cb8018d950b785910937375d6936073405d754f3c7616b7d8cd9d1bebc22d57a`
- runtime sealed cases SHA256: `b5f15e7ec52e34846d26e15f530daf242264862ccf56950f5151735c55ce8120`
- evaluator-only dev gold SHA256: `a0498b6704036a876ffd4c354a7284b8478a76c8b11f89475b674bc3e2ddde28`
- evaluator-only sealed gold SHA256: `4c114dd2f00e70f26581f0287058ce68ad40ef5b8d28fcaae582a6b4e719915c`

The exact candidate is stored under `benchmarks/eb-retrieval-assurance-rc2-v1/`. Post-sealed durability reconciliation run `33192256527` regenerated the candidate from the frozen apparatus, verified every recorded file identity, reproduced the exact first sealed-control hash, and then committed the exact candidate bytes. Deviation 13b remains preserved as the record of the earlier work-directory-only freeze failure.

## Observed evidence

### Positive ceiling

The oracle qualified and scored `1.0` on every promotion-critical retrieval measure: case hit@K, decisive-annotation recall, counterevidence recall, qualifier/exception recall, complete joint-group coverage, and every applicable family floor. It produced zero budget, provenance, scope, false-completeness, answerability, shape, or parser violations.

### Preregistered lexical shortcuts

All three intentionally weak lexical controls failed qualification without parser, provenance, shape, scope, or other incidental technical defects:

| Control | case hit@K | decisive recall | counterevidence | qualifier/exception | complete joint group | Qualified |
|---|---:|---:|---:|---:|---:|---|
| token overlap | 0.5714 | 0.4545 | 0.0 | 0.0 | 0.0 | no |
| bag-of-words TF-IDF cosine | 0.5714 | 0.4545 | 0.0 | 0.0 | 0.0 | no |
| character-trigram Jaccard | 0.5714 | 0.4545 | 0.0 | 0.0 | 0.0 | no |

For all three lexical controls, family-level failures included low-overlap relevance and distractor-heavy bounded retrieval, with zero counterevidence recall in R02 and zero qualifier/exception and joint-group success in R03/R04. R05 complete joint-group coverage was also zero. Each lexical control hit many hard negatives before decisive evidence.

The simpler `first_n` and `hard_negative_biased` controls also failed, with case hit@K `0.4286`, decisive recall `0.3636`, and zero counterevidence, qualifier/exception, and joint-group success.

### Gaming controls

- `null`: failed with zero retrieval capability.
- `return_all`: failed with 56 budget violations and weak bounded retrieval metrics; this rejects the unbounded-return shortcut on the intended budget surface.
- `provenance_corrupt`: failed with 88 invalid-provenance hits; this rejects identity/provenance corruption on the intended provenance surface.
- `aperture_liar`: retained perfect retrieval metrics but failed with 8 false-completeness claims; this isolates aperture honesty from retrieval quality.
- `answerability_liar`: retained perfect retrieval metrics but failed with 72 answerability overclaims; this isolates answerability honesty from retrieval quality.

### Metamorphic and mutation assurance

The preregistered checks all succeeded:

- deterministic replay produced byte-identical sealed-control output;
- oracle source/passage enumeration permutation was evaluator-invariant;
- aperture completeness mutation changed false-completeness detection from 0 to 1;
- decisive-gold identity mutation changed the relevant found count from 1 to 0;
- joint-group membership mutation changed the relevant partial-group count from 1 to 0;
- provenance text mutation changed invalid-provenance detection from 0 to 1.

### Contamination and goalpost checks

- `real_eb_executed=false` in the first sealed receipt.
- `sealed_runtime_exposed_to_eb=false` in the first sealed receipt.
- No production `src/` or dependency changes are part of PR #13.
- Evaluator, control runner, thresholds, result schema, preregistration, and generator identities remained byte-identical after first sealed exposure.
- No threshold, family floor, sealed case, gold, control implementation, or success criterion was altered in response to the first sealed result.
- Deviation 13a was a generator-seed correction before any sealed control existed.
- Deviation 13b was a post-sealed durability-workflow defect: the shell redirected to `work/` before the directory existed. The later correction only created that directory; it did not change the scientific apparatus or first result.

## Interpretation

RC1 was inconclusive because both the real c818 BM25 system and an intentionally weak lexical control cleared every promotion-critical sealed gate. RC2 directly addresses that decision-level defect: the positive oracle retains a clean ceiling while every preregistered weak lexical shortcut is rejected across multiple semantic retrieval categories, and the adversarial controls are rejected on the specific surfaces they are intended to challenge.

The discrimination is therefore materially harder for weak systems to fake than RC1's decision rule. The result supports handing this exact apparatus, unchanged, to a later real-EB RC2 experiment.

## Evaluator-assurance level

**E3 — Adversarially challenged**, bounded to the decision: whether this exact RC2 apparatus is sufficiently discriminating to expose a real EB system in a later separate experiment.

The record supports E1-E3 through positive/negative controls, mutation/invariance checks, and explicit gaming controls. It does not support E4 or E5 because no genuinely independent evaluator implementation, independent gold adjudication, or external cross-check has been demonstrated for this configuration.

## Remaining gaming surfaces and unknowns

- The adversarial/control set is finite and hand-designed; it does not prove exhaustive gaming resistance.
- The three lexical strategies produce the same aggregate promotion-critical scores on this challenge. Their algorithmic diversity is real, but this challenge has not demonstrated broad behavioral diversity among them beyond their shared failure signature.
- Provenance corruption challenges malformed identity/provenance; it does not exhaust self-consistent forged provenance or every duplicate-identity strategy.
- Aperture-liar and answerability-liar controls test explicit overclaiming, not every strategically incomplete but internally self-consistent declaration.
- Source-order invariance is preregistered and demonstrated for the oracle, not exhaustively for every possible implementation.
- Mutation checks cover named decision-relevant state, not a fuzzed or property-complete mutation space.
- Gold labels and evaluator logic have no independent E4 cross-check.
- Benchmark representativeness for all real corpora is not established.
- Real EB RC2 performance remains completely unknown until the later authorized experiment runs.

## Terminal handoff

A later real-EB thread must pin the exact frozen identities above. Any change to benchmark bytes, evaluator, control runner, thresholds, result schema, success criteria, or gold creates a different apparatus and requires a new assurance decision.

`REAL EB RC2 EXPERIMENT AUTHORIZED AGAINST THIS EXACT FROZEN APPARATUS`
