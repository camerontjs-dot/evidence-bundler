# Evidence Bundler Obligation-Selection Convergence Record — 2026-09-18

## Status

**Research cycle stopped by operator after the final fresh post-reveal qualification.**

No additional selector experiment, candidate freeze, merge, release, default change, or production promotion is authorized by this record.

Terminal fresh disposition:

`SUPPORTED_SUBJECT_ONLY; COMBINED_FORM_INCREMENT_NOT_REPRODUCED`

The smallest architecture justified for the **next research cycle** is:

```text
semantic top-K
→ explicit child / all_of coverage
→ exact claim-native subject binding
```

The expected-evidence-form repair stage is **not retained as causal selection machinery** for the converged candidate.

Expected evidence forms may remain available as descriptive/shadow metadata. This cycle does not justify giving them causal retention authority.

## Final fresh qualification

Frozen subjects:

- semantic/candidate world: fresh input commit `1bd4b14172d5201ec8687fba621fce4b6637a147`
- fresh-input SHA-256: `da553e3081afdd403dfb4cab24e3a37399baced017b14576b1605714b676307a`
- sealed gold commit: `4814144caf6d5fdb3e8038bf5f77c46d6ef46964`
- sealed-gold SHA-256: `9e521d0010836ec66dc76c5fa21abd1d7fc343e271b2d18029300021f217d801`
- exact combined RC1 selector commit: `df6e0af3732fc08e9db330741b9b99113247a40c`
- selector SHA-256: `31cd6680111147412b766a832c7de4d8ffa8a6adc9c2c234b223111a79cf0a8f`
- post-reveal execution PR: #118
- valid workflow run: `35361473380`
- pre-gold selection commit: `c21de9878327d4a0db3211eeeb008a9e09a30a00`
- selection SHA-256: `a51eef43bf50a84788a6680eb55babe9ace879624291520eab98552c54b60fcb`
- terminal result commit: `e36a786ececc8f9f54607813b2212bdbc3581836`
- terminal result tree: `5a9a53676720a63835ad51504bdcd6c4f79b055d`
- evaluation SHA-256: `e4f1b27b90461da43af29b3e8cef304d2c2c922f6ff74e129d014256b1b0fedd`
- disposition SHA-256: `1bdb9237de35f4cf9af3ad31fa18d27bae21d2546e67ba9684c72cf0e8be9139`
- artifact ID: `10553579903`
- artifact digest: `sha256:4f1cb8a2d67616b7ea752e46143cb82bc62b8c84b904849eb0929b805166573c`

Selections replayed exactly and froze before sealed gold was checked out.

### Aggregate result

| Arm | complete parents | required children | unsafe | non-useful |
| --- | ---: | ---: | ---: | ---: |
| no-Gate semantic top-3 | 15/24 | 39/48 | 13 | 20 |
| child coverage | 19/24 | 43/48 | 12 | 18 |
| **composition + subject** | **22/24** | **46/48** | **3** | **9** |
| form only | 16/24 | 40/48 | 14 | 21 |
| combined form → subject RC1 | 20/24 | 44/48 | 2 | 9 |
| reverse subject → form | 19/24 | 43/48 | 4 | 11 |
| wrong form + correct subject | 20/24 | 44/48 | 2 | 10 |
| wrong subject + correct form | 7/24 | 27/48 | 31 | 36 |
| wrong subject + wrong form | 6/24 | 27/48 | 30 | 36 |

### What reproduced

**Composition / child coverage reproduced.**

Relative to semantic top-3:

- complete parents: 15 → 19;
- required children: 39 → 43;
- unsafe: 13 → 12.

On the dedicated C1 starvation controls, child coverage moved from 5/8 required children to 8/8.

The earlier exposed result that child coverage alone can sometimes rescue starvation therefore survives, while the earlier targeted result correctly warned that semantic child attribution is not sufficient evidence quality by itself.

**Exact subject identity reproduced strongly.**

Composition + subject relative to semantic:

- complete parents: 15 → 22;
- required children: 39 → 46;
- unsafe: 13 → 3;
- non-useful: 20 → 9.

On explicit/inherited subject conflicts C2+C3:

- correct composition + subject: 15/16 required children, 1 unsafe;
- frozen combined candidate: 15/16, 0 unsafe;
- wrong-subject control: 5/16, 15 unsafe.

Separately:

- inherited-subject C3 reached 8/8 required children with subject-only;
- explicit-subject C2 retained 7/8 while reducing unsafe to zero.

This is fresh evidence that the subject binding itself matters, not merely generic lexical movement.

### What did not reproduce

**Expected evidence form did not earn causal retention authority.**

Form only was nearly the semantic baseline and slightly less safe:

- semantic: 39/48 required, 13 unsafe;
- form only: 40/48 required, 14 unsafe.

The exact combined RC1 candidate was **worse on coverage than subject-only**:

- subject-only: 46/48 required, 22/24 complete, 3 unsafe;
- form → subject: 44/48 required, 20/24 complete, 2 unsafe.

The one-unit safety improvement does not compensate for two lost required children and two lost complete parents under the preregistered support contract.

Most importantly, **wrong form reproduced the combined candidate's aggregate coverage and safety**:

- correct form → subject: 44/48 required, 2 unsafe;
- wrong form → subject: 44/48 required, 2 unsafe.

On the intended C4+C5 form population:

- combined correct form: 14/16 required;
- subject-only: 15/16 required;
- wrong-form control: 13/16 required.

The preregistered form-increment and correct-vs-wrong-form thresholds both failed.

Therefore the earlier exposed specialty-form signal is preserved as real development evidence, but it does not survive as a justified causal stage for the current prototype decision.

## Evidence lineage

### 1. Broad search surface

PR #92 widened the research surface deliberately rather than guessing a narrow Gate-to-EB interface.

PRs #93/#94 built and pressure-tested a **92-entry noncausal shadow carrier**. The apparatus result was supported, with 1,177 boundary assertions, but it qualified only the ability to transport/mask/mutate/bind research observations. It granted no semantic or causal authority.

This broad carrier was useful because it let the research cycle prune aggressively without prematurely encoding one explanation into production machinery.

### 2. Actual Gate-field pressure

PRs #95/#96 compared actual Gate-derived fields to the true no-Gate semantic control.

The exposed no-Gate semantic baseline was 21/27 required-lane coverage, 24/41 useful recall, 62 unsafe.

Initial apparent gains came from evidence shape, negation, and staged structure.

PRs #97/#98 corrected metric semantics and showed only 18/92 registered fields were nontrivial on that cohort; 67 were unmaterialized/unknown.

### 3. Generic-form confounder

PRs #99/#100 falsified the broad claim that the observed evidence-shape improvement was uniquely caused by correct Gate requirements. Generic loose form diversity/richness reproduced the aggregate gain.

This preserved a residual individualized signal but forced the mechanism to become smaller.

### 4. Specialty-form narrowing

PRs #101/#102 showed the dominant constant `document_text + measurement` prior did **not** explain the exceptional-lane movement. All movement occurred on eight exceptional lanes.

PRs #103/#104 narrowed the signal to specialty-form structure. Exact specialty and a generic union could reproduce the aggregate result, so exact mapping was not yet necessary.

PRs #105/#106 supplied the stronger exposed falsifier: removing the true specialty collapsed the improvement to semantic baseline, while true specialty retained the development gain.

PRs #107/#108 froze a minimal specialty-form RC0 candidate for fresh qualification. That candidate remains a valid evidence record, but no fresh result in this cycle justifies carrying specialty form into the converged causal selector.

### 5. Composite obligations

PRs #109/#110 tested richer evidence-obligation structure over the historical composite/decomposition corpus.

The rich descriptor did not beat a simpler child-coverage mechanism there. Child coverage rescued the known F10 joint-evidence failure.

That result established a useful structural hypothesis but not general sufficiency.

### 6. Targeted adversarial stress

PRs #112/#113 deliberately introduced child starvation, wrong-entity, inherited-subject, wrong-scope, and wrong-form conflicts.

The result revised the earlier child-coverage interpretation:

- semantic representation of both children did not guarantee required evidence;
- subject identity produced the strongest effect;
- inherited subject was especially important;
- form showed a smaller positive exposed signal;
- scope was behaviorally active but lacked positive rescue headroom.

### 7. Subject × form interaction

PRs #114/#115 pressured subject and form separately and jointly.

On the exposed 24-parent stress world:

- child coverage: 36/48 required, 20 unsafe;
- subject only: 47/48, 13 unsafe;
- form only: 40/48, 25 unsafe;
- form → subject: 48/48, 12 unsafe.

The exposed interaction therefore justified freezing a combined candidate for a fresh falsifier, but not promotion.

### 8. Frozen combined RC1

PRs #116/#117 froze:

```text
semantic top-3
→ child coverage
→ expected evidence form
→ exact subject identity
```

with K=3 and semantic-loss cap 0.01.

The selector itself passed unit/static/replay gates. This was a target freeze, not evidence of generalization.

### 9. Context-free fresh cohort

PR #111 was narrowed before authoring to the surviving factors only.

The prereveal process produced:

- 24 parents / 48 children;
- 240 candidate passages;
- four cases each across C1-C6;
- 24/24 parents with unsafe candidates;
- 15 parents with required evidence at semantic rank 4-10;
- three C1 starvation opportunities;
- all eight C4/C5 cases with actionable expected forms.

Claims froze before corpus authoring; descriptors froze before corpus authoring; corpus froze before semantic scoring; semantic scores replayed exactly; fresh input froze before gold; gold was independently adjudicated from sanitized inputs; cohort eligibility passed without post-gold repair.

One validator error rejected `the console` against `The console`. This was preserved and repaired by aligning the validator with the frozen selector's case-insensitive subject semantics. The exact authored corpus was reused rather than regenerated.

### 10. Final post-reveal qualification

PR #118 executed the preregistered arms against sealed fresh gold.

Terminal disposition:

`SUPPORTED_SUBJECT_ONLY; COMBINED_FORM_INCREMENT_NOT_REPRODUCED`

No falsifier for subject identity fired.

The combined form stage did not pass its fresh support requirements.

## Converged interpretation

### Retain for the next research candidate

1. **Explicit child/composition identity**
   - preserves separate `all_of` obligations;
   - enables a bounded anti-starvation repair;
   - reproduced fresh benefit.

2. **Exact claim-native subject identity**
   - may come from the child or be inherited from the parent when decomposition is elliptical;
   - must originate from the declared claim, never from evidence;
   - reproduced strongly against realistic wrong-subject controls.

### Do not retain as causal selector machinery

- expected evidence form;
- generic/specialty-form repair;
- expected keywords/predicate lists;
- broad lexical descriptors;
- evidence-derived entities;
- query strings or rewrites;
- source/domain routing;
- support/refute hints;
- answer values;
- opaque weighted fusion;
- scope as a promoted selector signal.

Scope remains a research/safety identity observation only. This cycle did not qualify it as positive causal machinery.

### Important upstream limitation

The fresh selector study consumed **explicit frozen subject anchors**.

It did **not** qualify a current ClaimGate subject extractor.

Earlier Proposition Authoring pressure found entity/relation characterization failures on some constructions. Therefore a future pipeline prototype must not silently assume current Gate extraction is already qualified to supply this field.

Subject production needs its own bounded contract/qualification or an explicit trusted upstream source.

## Candidate state at stop

No new subject-only selector has been frozen because the operator requested that research stop after this terminal result.

The combined RC1 at `df6e0af...` remains a preserved **failed-for-combined-promotion** target artifact.

The evidence-supported next candidate, if work resumes, is conceptually:

```text
semantic top-3
→ child coverage
→ exact claim-native subject identity
```

It must be implemented/frozen as the smallest successor and should not inherit the expected-form stage.

## Relationship to EB V1 baseline

The frozen EB V1 integration baseline in PR #79 remains untouched.

This research cycle does not change the production-profile/default selector, first-stage retrieval, Contract B, admission, CAL semantics, or Decision Engine.

Any later prototype integration must be a separate bounded change from that baseline.

## Tree consolidation policy

All research PRs in this cycle are evidence records.

Their branches and exact commits are retained.

The superseded/open Draft PRs should be closed with a pointer to this convergence record rather than merged into `main`.

Closing them means **research thread complete/superseded**, not “evidence discarded.”

This convergence record is the sole open navigation point for this research cycle.
