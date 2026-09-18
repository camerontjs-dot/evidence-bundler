# RC1 Fresh Post-Reveal Execution — Arm Binding

## Frozen subjects

- RC1 selector commit: `df6e0af3732fc08e9db330741b9b99113247a40c`
- selector SHA-256: `31cd6680111147412b766a832c7de4d8ffa8a6adc9c2c234b223111a79cf0a8f`
- fresh-input commit: `1bd4b14172d5201ec8687fba621fce4b6637a147`
- fresh-input SHA-256: `da553e3081afdd403dfb4cab24e3a37399baced017b14576b1605714b676307a`
- sealed-gold commit: `4814144caf6d5fdb3e8038bf5f77c46d6ef46964`
- sealed-gold SHA-256: `9e521d0010836ec66dc76c5fa21abd1d7fc343e271b2d18029300021f217d801`

Gold is not read until all arm selections replay exactly and freeze.

## Arms

- `semantic_top3`: no obligation metadata.
- `child_coverage`: semantic top-3 plus frozen composition repair only.
- `subject_only`: child coverage then exact claim-native subject repair.
- `form_only`: child coverage then expected-form repair.
- `rc1_candidate`: exact frozen selector, form then subject.
- `reverse_order`: child coverage, subject then form.
- `wrong_subject`: child coverage, correct expected form, then deterministic wrong-subject repair.
- `wrong_form`: child coverage, deterministic wrong-form repair, then correct subject.
- `wrong_both`: child coverage, deterministic wrong-form repair, then deterministic wrong-subject repair.

K and semantic-loss cap are inherited unchanged from the frozen selector.

## Wrong-subject binding

Use only prereveal corpus construction metadata and candidate text, never gold.

For each child:

1. collect candidates whose frozen `design_role` begins `other_subject`;
2. for each candidate, tokenize the target subject and candidate text;
3. scan same-length token windows in the candidate text;
4. choose the non-identical window with highest case-insensitive SequenceMatcher similarity to the target subject;
5. ties break by candidate ID then window position;
6. if no valid window exists, choose the lexicographically first different subject extracted for another child in the same case; otherwise use a deterministic sentinel that matches no candidate.

This produces an intentionally wrong entity string without inspecting usefulness labels.

## Wrong-form binding

For each child:

1. among candidates semantically attributed to that child, inspect prereveal `design_role=target_subject_other_form`;
2. choose the highest-semantic candidate whose `intended_form` is one of the frozen selector's supported form vocabulary and is absent from the child's actionable expected-form set;
3. use that intended form as the wrong form;
4. ties break by candidate ID;
5. deterministic fallback rotates among `authoritative_declaration → event_record → registry_entry → measurement → authoritative_declaration` to the first form absent from the expected actionable set.

No gold or evaluator output is used.

## Evaluation

Use the evaluator frozen in the fresh-input lineage and the thresholds in `EVALUATION-CONTRACT.md`.

No arm, threshold, or binding change is permitted after the first valid selection run.

## Terminal scientific disposition

Exactly one:

- `SUPPORTED_COMBINED_RC1_FOR_FROZEN_RESEARCH_PROTOTYPE`
- `SUPPORTED_SUBJECT_ONLY; COMBINED_FORM_INCREMENT_NOT_REPRODUCED`
- `FALSIFIED`
- `INCONCLUSIVE`
- `BLOCKED_APPARATUS`

No production promotion is authorized by any outcome.
