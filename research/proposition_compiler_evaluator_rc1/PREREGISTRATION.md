# Proposition Compiler Evaluator RC1 — Preregistration

## Class
Research / bounded evaluator successor. No production behavior, Contract A/B/C, retrieval, CAL, Decision Engine, decomposer, or standalone repository change is authorized.

## Exact authority
- Evidence Bundler base: `c26fbd4bfc8ba5c2604a784af158594b59fcae37`
- RC0 predecessor PR: `#61`
- RC0 immutable head: `7e4cfef6551c18ae63082b83c2cb6b0877edf9b9`
- RC0 frozen evaluator SHA-256: `d6dcda3c053e4cb68a65aa8bcb01404e72e084cdd735068c6e6935cf8cb71643`
- RC0 disposition: `FALSIFIED`

## Research question
Within the bounded explicit-conjunction `all_of` fragment, can a different evaluator architecture discriminate safe from unsafe decompositions by conserving semantic bindings: predicate/relation, argument roles, child-local operators, qualifier attachment, reference bindings, connective membership, and ambiguity state?

## Candidate architectural hypothesis
RC1 uses a bounded proposition-frame extractor plus a constrained root-frame ↔ child-frame correspondence check. It does not infer universal semantics. Unsupported or multiply compatible parses fail closed.

A proposition frame contains only corpus-required fields:
- predicate/relation;
- ordered semantic arguments/roles;
- local negation/modality/quantifier operators;
- attached qualifiers (unit, time, population, location, condition, exception, attribution);
- explicit reference binding state;
- connective membership / composition identity.

No single lexical overlap score or learned-model confidence can authorize acceptance.

## Acceptance logic
A `DECLARED/all_of` candidate is `ACCEPTABLE_WITHIN_PROFILE` only when:
1. root parsing produces one unique supported frame set;
2. each child produces one unique supported proposition frame;
3. root and child frame sets admit a one-to-one correspondence for authoritative assertions;
4. every matched pair preserves predicate/relation, argument roles, local operators, qualifiers, and reference binding;
5. there is no extra, missing, or duplicated authoritative frame;
6. the connective remains compatible with `all_of`;
7. each child is independently auditable within the declared bounded scope.

If more than one materially distinct binding remains and the alternatives would change authoritative children, result is `INDETERMINATE`.

## Result vocabulary
- `ACCEPTABLE_WITHIN_PROFILE`
- `REJECT_UNSAFE`
- `INDETERMINATE`
- `INVALID_INPUT`

## Promotion-critical fresh gates
A positive RC1 disposition requires all of:
1. zero unsafe acceptances for fresh predicate/argument-role mutations;
2. zero unsafe acceptances for fresh cross-child argument reassignments;
3. zero unsafe acceptances for fresh required operator/qualifier relocation cases;
4. zero unsafe acceptances for connective corruption;
5. every materially ambiguous fresh case fails closed;
6. unambiguous reference controls are not rejected solely because a pronoun occurs;
7. every preregistered safe positive is accepted unless a limitation is frozen before decisive execution;
8. RC0 unsafe regression acceptances no longer pass as safe;
9. RC0 safe false-negative cases are accepted or prospectively declared outside profile before decisive execution;
10. exact replay is byte-identical;
11. harmless child-order/canonicalization transformations preserve normalized conclusion;
12. C0-C4 each fail at least one fresh promotion-critical gate for the intended reason;
13. target materially discriminates better than frozen RC0 on the fresh binding surface;
14. no retrieval/CAL/Decision output participates in scoring or evaluator choice;
15. exact scientific identities and receipts are preserved.

## Falsifiers
RC1 is `FALSIFIED` on the first fresh promotion-critical observation of any of:
- subject/object or semantic-role reversal accepted as safe;
- cross-predicate argument reassignment accepted as safe;
- required child-local qualifier/operator relocation accepted as safe;
- connective semantic change accepted as safe;
- materially ambiguous binding silently resolved into acceptance;
- unsafe reference resolution accepted;
- exact replay changes;
- evaluator consumes gold before raw-output freeze;
- post-result semantic repair is required.

One decisive unsafe acceptance is sufficient. Aggregate accuracy cannot override it.

## Inconclusive conditions
Use `INCONCLUSIVE` instead of positive support when:
- gold/adjudication cannot establish the binding;
- target and weak controls all clear the fresh discriminator;
- fresh corpus fails to exercise the intended distinction;
- required candidate architecture cannot actually execute because instrumentation is unavailable;
- positive evidence cannot be reproduced on the required hosted/maintained boundary.

A weaker local boundary may still falsify RC1 if it directly exhibits a preregistered unsafe acceptance.

## Weak controls
Freeze before fresh case construction:
- C0 accept-all;
- C1 shape-only;
- C2 lexical/token conservation;
- C3 bag-of-words/similarity;
- C4 exact frozen RC0 evaluator, unchanged;
- C5 gold oracle, scoring ceiling only.

## Freeze order
1. preregistration / architecture;
2. target evaluator implementation;
3. weak controls;
4. freeze target/controls and record hashes/commit;
5. construct fresh cases and gold after that freeze;
6. freeze fresh corpus/gold;
7. run target and controls without gold exposure;
8. freeze/hash raw outputs;
9. score against gold;
10. replay and metamorphic checks;
11. reconcile terminal disposition.

## Evidence surfaces
- RC0 regression surface: predecessor failures and safe false negatives, used only as regression requirements.
- Fresh RC1 surface: new semantic-binding minimal pairs constructed only after the target/controls freeze. This is the promotion-relevant surface.

## Hosted execution burden
Positive support requires hosted CI if GitHub Actions is available: maintained EB tests, research tests, static checks, target/controls, raw-before-gold scoring, replay, metamorphic checks, Contract A validation, artifacts and SHA256SUMS. If hosted execution is unavailable, positive disposition is not justified.

## Human adjudication
Independent human adjudication is preferred for fresh promotion-critical cases. If unavailable, record that as a limitation. Material adjudicator disagreement converts the case to ambiguity/inconclusive evidence rather than forced gold.

## Allowed terminal dispositions
- `SUPPORTED_FOR_FRESHER_QUALIFICATION`
- `FALSIFIED`
- `INCONCLUSIVE`
- `SUPERSEDED`
