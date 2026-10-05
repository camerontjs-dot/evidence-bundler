# Fresh prerequisite profile-writing task

Create exactly five files:

- PRIMARY-PROMPT.txt
- PRIMARY-CONFIG.json
- EVALUATOR-PROMPT.txt
- EVALUATOR-CONFIG.json
- REVIEW-SCHEMA.json

Use only BOOTSTRAP-MANIFEST.json, AUTHORING-RUBRIC.json, PROFILE-SURFACE.json, this task, and actual runtime/destination capability facts supplied without semantic cases or prior outputs.

Do not execute the primary or evaluator.

The primary must accept only the root-only proposal-null capsule described by PROFILE-SURFACE.json. It may declare exactly two materially distinct required obligations only when the inherited rubric is conserved; otherwise it returns an allowed ineligible result. It must preserve modality, negation, quantifiers, values, dates, attribution, scope and references. Subject spans are exact UTF-8 half-open byte spans. It performs no truth, source, evidence-adequacy, retrieval, or repair work.

The evaluator must have two explicitly named modes under one frozen semantic instruction surface:

1. calibration: judge a supplied proposal and return root_alias plus accept, reject, or uncertain;
2. decisive: judge a supplied root/proposal pair and return row_alias, root_status, decision, and exactly the five Boolean checks named in PROFILE-SURFACE.json.

Both root_status and decision must explicitly support uncertain where defined by PROFILE-SURFACE.json. The evaluator must never edit the proposal.

## Exact machine surface

The three machine-readable files below must match the frozen PROFILE-SURFACE.json contract literally. Do not redesign them.

### PRIMARY-CONFIG.json

Return exactly this object shape and values, with no aliases and no embedded mode definitions:

{
  "role": "primary",
  "input_mode": "root_only_proposal_null",
  "output_mode": "json_only",
  "extra_context": false,
  "proposal_required_null": true
}

### EVALUATOR-CONFIG.json

Return exactly this object shape and values:

{
  "role": "semantic_evaluator",
  "modes": ["calibration", "decisive"],
  "shared_semantic_instructions": true,
  "proposal_editing": false,
  "review_schema_file": "REVIEW-SCHEMA.json"
}

The `modes` value must be exactly the two-string array above.

Do not put mode objects inside EVALUATOR-CONFIG.json.
Do not omit `shared_semantic_instructions`, `proposal_editing`, or `review_schema_file`.

### REVIEW-SCHEMA.json

Use top-level `modes`.

Under `modes.calibration`, copy exactly these keys and arrays from PROFILE-SURFACE.json:

- `input`
- `output`
- `decision`

Under `modes.decisive`, copy exactly:

- `input`
- `output`
- `root_status`
- `decision`
- `checks`

Do not rename any key.

Forbidden aliases include:

- `input_fields`
- `output_fields`
- `decision_enum`
- `root_status_enum`
- `check_fields`

Do not substitute those aliases anywhere in the machine-readable profile files.

## Prompt files

PRIMARY-PROMPT.txt must be a substantive instruction surface longer than 40 characters and consistent with the frozen primary contract.

EVALUATOR-PROMPT.txt must be a substantive instruction surface longer than 40 characters and must literally contain the words:

- `calibration`
- `decisive`
- `uncertain`

Do not include worked examples, case aliases/text, expected answers, oracle material, metamorphic pair identities, weak-system output, previous generated profiles, or scientific outcomes.

Return only the five requested file bodies through the transport-enforced files object. Do not return a custody report, narrative explanation, hashes, or extra files. An external frozen launcher/custodian will hash and record the native request/response and extracted bytes.

One writing attempt. No candidate sweep, repair, reroll, replacement writer, semantic execution, or third role. If you cannot produce the literal machine surface above, return the closest schema-valid five-file bundle without inventing semantic case information; the frozen checker determines the result.

Unknown runtime facts remain UNKNOWN. Do not claim capabilities that are not observable.
