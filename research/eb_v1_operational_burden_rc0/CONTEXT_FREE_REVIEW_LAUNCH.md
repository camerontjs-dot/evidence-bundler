# Context-Free Review Launch

Classification: **CONTEXT-FREE REQUIRED**

The semantic review is valid only if each execution is isolated from CAL Pipeline history, prior Evidence Bundler results, the other review set, and other reviewer outputs.

Run four fresh semantic-review contexts total:

1. Amber reviewer A: `eb-v1-operational-review-amber.zip`
2. Amber reviewer B: the same Amber ZIP in a different fresh context
3. Cobalt reviewer A: `eb-v1-operational-review-cobalt.zip`
4. Cobalt reviewer B: the same Cobalt ZIP in a different fresh context

Do not tell reviewers that there are two arms, which profile their packet represents, or that one packet is larger because of K=7.

For each fresh context, attach only the relevant ZIP and send:

> CONTEXT-FREE REQUIRED. Use only the attached files. Read `REVIEWER_RUBRIC.md` and `BLIND_REVIEW_PACKET.json` completely, follow the rubric exactly, and return only the required JSON object. Do not inspect GitHub, search the web, use prior project context, or ask for additional project information. If prohibited context is exposed, return `CONTEXT_CONTAMINATED` instead of judgments.

Preserve each returned JSON exactly. Do not show any reviewer another reviewer's output.
