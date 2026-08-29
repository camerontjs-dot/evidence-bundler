# CAL Pipeline Writing Style Guidance

## Purpose

Use this guidance for public and semi-public CAL Pipeline writing: READMEs, project pages, findings, ADRs, research summaries, release notes, technical explanations, and other prose that represents the work.

The goal is not to make AI-assisted writing “look human” or to imitate casual chat. The goal is to preserve Cameron’s actual judgment, priorities, uncertainty, and way of explaining technical work after a clean register shift.

Write like the person doing the work, not like a narrator describing it from outside.

Style is downstream of truth. Evidence, scope, uncertainty, and project governance determine what can be said. This file only helps determine how to say it.

---

## Core voice

The default voice is:

- specific;
- evidence-led;
- plainspoken;
- decision-seeking;
- comfortable naming uncertainty;
- willing to state a point of view;
- more interested in the hard part than in making the work sound impressive.

Use first person when the sentence represents an actual judgment, decision, preference, or limitation.

Prefer:

> I kept the benchmark frozen because changing it after seeing the evaluator failure would make the next result harder to trust.

over:

> The benchmark was kept frozen in order to preserve methodological integrity.

Both may be true. The first makes ownership and reasoning visible.

Do not force first person into every paragraph. Technical facts can remain direct facts.

---

## Land the real point early

Start with the thing that actually matters.

Skip generic setup, industry framing, and ceremonial introductions unless the reader genuinely needs them.

Prefer:

> Contract B 1.2.0 is locked. The remaining question is whether Contract C can preserve CAL’s result without inventing downstream state.

over:

> As AI systems continue to become increasingly complex, robust interoperability between pipeline components is becoming more important.

The opening should usually establish one of:

- the decision;
- the tension;
- the failure;
- the boundary;
- the thing that changed;
- the question still unresolved.

---

## Use concrete named objects

Do not dissolve the work into abstractions.

Use the actual names of:

- systems;
- repositories;
- contracts;
- tests;
- artifacts;
- versions;
- failure modes;
- workflows;
- decisions.

Prefer:

> The return-all control hit perfect unbounded recall and still failed because it violated the retrieval budget on every case.

over:

> A permissive baseline demonstrated limitations in the evaluation framework.

Concrete objects make the reasoning easier to inspect and make the writing sound like it came from someone who was actually there.

Do not synonym-swap important terms merely to avoid repetition. If the subject is Contract B, keep calling it Contract B.

---

## Name the hard part

A useful piece of writing usually contains the uncomfortable seam.

Examples:

- what the current evidence does not establish;
- where the evaluator may still be weak;
- what failed;
- what remains a judgment rather than a measurement;
- what assumption carries the most weight;
- what would change the conclusion.

Do not bury these in a limitations appendix if they are central to understanding the work.

Prefer:

> The hard part is not producing a result package. It is preserving enough CAL state that a downstream policy can make a different decision without reopening the audit.

That kind of sentence is usually more useful than another paragraph describing the architecture.

---

## Uncertainty should still move

Use uncertainty when it is real, but pair it with what follows from it.

Useful shape:

> I am not confident enough in X yet, so the next test is Y.

Avoid both extremes:

- pretending uncertainty is gone;
- hedging until no position remains.

Prefer specific uncertainty:

> The weak point is evaluator independence. We have code-isolated reproduction, but not a fully supervisory-context-isolated consumer.

over:

> More testing may be required.

If the evidence supports a bounded conclusion, say it plainly.

---

## Limits are part of the work

State boundaries without apology.

A limitation is useful when it tells the reader what not to infer.

Prefer:

> This establishes deterministic cross-language reproduction on the frozen evidence world. It does not establish universal interoperability.

Do not add self-deprecating filler or defensive language around an honest boundary.

A smaller supported claim is stronger than a bigger claim wrapped in caveats.

---

## Prefer a better route over a bigger plan

When the work points toward narrowing scope, let the writing show that.

Useful phrases when they are genuinely true:

- for now;
- the smaller change;
- the better route;
- the remaining question;
- the next discriminating test;
- not enough evidence yet;
- worth separating;
- keep this out of scope.

Avoid turning every finding into a roadmap.

Sometimes the right ending is:

> For now, I would leave the contract alone and test the consumer assumption directly.

That is enough.

---

## Evidence before polish

Every substantive public claim should be traceable to something real:

- an observed behavior;
- a test result;
- a frozen artifact;
- a decision record;
- a source;
- an exact version;
- a known constraint.

Use the right epistemic word.

Prefer distinctions such as:

- observation rather than finding when interpretation is incomplete;
- measurement rather than proof;
- nomination rather than support when retrieval only proposes candidates;
- exercises rather than validates when a test covers only a bounded path;
- supported with bounds rather than solved.

Do not make the prose more confident than the evidence.

---

## Observations and conclusions are different things

When both matter, make the separation visible.

Example:

**Observed:** the lexical-only control recovered nearly all decisive passages.

**Inference:** aggregate recall alone will not discriminate sophisticated retrieval from a cheap lexical baseline on this corpus.

This distinction should feel natural, not bureaucratic. Use explicit labels when the distinction matters to the argument. Otherwise preserve it through sentence structure.

---

## Rhythm

Use short and medium sentences most of the time.

Longer sentences are fine when they carry a real chain of reasoning, but do not let technical prose become one continuous block.

Most paragraphs should be two to four sentences.

A one-sentence paragraph is useful when it carries the turn.

Use contractions when they sound natural.

Prefer plain verbs:

- want;
- think;
- check;
- test;
- keep;
- fix;
- fail;
- prove;
- hold;
- ship;
- change.

Do not manufacture “human” rhythm with random fragments, slang, or abrupt sentence-length variation.

Read the prose aloud. If it sounds like a press release, consulting deck, or generic assistant answer, rewrite it.

---

## Avoid generic professional filler

Cut phrases that add polish without information.

Usually avoid:

- “in today’s rapidly evolving landscape”;
- “it is important to note”;
- “this enables stakeholders to”;
- “robust” when it is not naming a tested property;
- “comprehensive” when the scope is actually bounded;
- “leverage” when “use” works;
- “pivotal,” “crucial,” “synergy,” “delve,” and similar filler;
- repeated “not just X, but Y” constructions;
- conclusions that merely restate the previous paragraph.

Do not replace these mechanically with different fancy words. Replace them with the actual consequence, object, or failure mode.

---

## Do not dump raw chat into public prose

Cameron’s spoken and typed prompts are source material for stance and reasoning, not a transcription style.

Strip:

- “um”;
- “uh”;
- “you know”;
- repeated starts;
- dictation loops;
- filler hedges that do not change meaning.

Keep the underlying move:

- the agenda;
- the preference;
- the uncertainty;
- the hard question;
- the next step.

Public writing should feel like the same person after editing, not a transcript and not a corporate rewrite.

---

## Public project writing

For READMEs, findings, ADRs, project pages, and technical research summaries:

1. State the actual purpose or decision.
2. Name the boundary.
3. Show the mechanism, evidence, or important observation.
4. State what failed or remains uncertain when it matters.
5. End with the consequence, next test, or current limit.

Do not write as though someone is grading the project.

The costly signaling should come from the artifacts themselves:

- frozen evidence;
- preserved failures;
- explicit falsifiers;
- reproducible tests;
- independent consumers;
- narrow claims;
- visible decisions.

The prose should simply make that machinery legible.

Avoid sentences that sound like they were written to impress an evaluator:

> This demonstrates rigorous engineering discipline and provides strong evidence of technical maturity.

Prefer the underlying fact:

> The failed run is still in the record, and the corrected workflow now fails closed on the same condition.

Let the reader draw some conclusions for themselves.

---

## Register

### README / project page
Clear, owned, practical. Explain what the system does, where its boundary is, and where the evidence is.

### Research finding
More explicit about observations, competing explanations, uncertainty, and falsifiers.

### ADR / EDR
Direct and compact. Decision, evidence, alternatives, consequence.

### Technical explanation
Result first, then reason, evidence or constraint, then verification path.

### Public essay or article
More conversational and reflective, but still anchored in concrete systems and examples. Keep the hard part visible.

The voice can shift by surface. The underlying judgment should stay recognizable.

---

## Final pass

Before publishing, check:

1. Does the opening reach the real point quickly?
2. Are the important systems, artifacts, versions, or failure modes named?
3. Does the writing distinguish what was observed from what is being inferred?
4. Is uncertainty specific?
5. Are limits stated without apology or inflation?
6. Is there a clear consequence, boundary, or next move where one is needed?
7. Did any generic professional filler replace a concrete fact?
8. Does the prose sound like the person doing the work?
9. Is the evidence carrying the credibility, rather than the prose asking the reader to be impressed?
10. Would this still read naturally if nobody were explicitly evaluating the project?

If the draft is polished but ownerless, restore judgment.

If it sounds defensive, state the boundary more simply.

If it sounds like a portfolio pitch, remove the pitch and expose the evidence.
