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

Both root_status and decision must explicitly support uncertain where defined by PROFILE-SURFACE.json. The evaluator must never edit the proposal. REVIEW-SCHEMA.json must make these modes and enums mechanically explicit.

Do not include worked examples, case aliases/text, expected answers, oracle material, metamorphic pair identities, weak-system output, previous generated profiles, or scientific outcomes.

Return only the five requested file bodies through the transport-enforced files object. Do not return a custody report, narrative explanation, hashes, or extra files. An external frozen launcher/custodian will hash and record the native request/response and extracted bytes.

One writing attempt. No candidate sweep, repair, reroll, replacement writer, semantic execution, or third role. If the required surface cannot be produced from the allowed inputs, return the closest schema-valid five-file bundle you can produce without inventing semantic case information; the frozen checker determines whether the prerequisite passes.

Unknown runtime facts remain UNKNOWN. Do not claim capabilities that are not observable.
