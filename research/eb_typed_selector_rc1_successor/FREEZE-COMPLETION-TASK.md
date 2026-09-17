# EB Typed Selector RC1 — Context-Free Freeze Completion

## Objective

Complete only the prereveal scientific freeze that remained unfinished after the successor authoring execution.

The claims/profiles, fresh source fixtures, and exact authoritative depth-10 first-stage candidate pools are already immutable and must not be changed or regenerated.

Your job is to independently author fresh gold and a target-agnostic evaluator from those fixed prereveal inputs, validate cohort eligibility, create the required separated Git refs, and stop at `READY_FOR_REVEAL` if and only if every prereveal condition is satisfied.

Do not inspect or execute the hidden selector.

## Authority and aperture

Start with `FREEZE_COMPLETION_MANIFEST.json` on this branch and obey its allowlist/denylist literally.

Use immutable non-gold parent:

`03528f8ac137007ade205ab0d1d78424df6c388f`

Verify its tree and hashes before scientific work.

Do not rerun Evidence Bundler retrieval. `AUTHORITATIVE_CANDIDATE_POOLS.json` on that parent is the frozen authoritative candidate world.

Do not use any gold, evaluator, eligibility report, gold hash/statistic, or scientific output from either earlier blocked execution.

## Required work

1. Verify immutable parent identity and the claims/source/pool hashes from the manifest.
2. Read the fixed cohort, evaluation, and freeze/reveal contracts listed in the manifest.
3. Independently adjudicate all candidates in the frozen authoritative pools into the existing gold classes and group fields. Do not tailor adjudication to any target implementation.
4. Compute cohort eligibility under the already-fixed cohort contract. Do not repair claims, corpora, or pools to make a gate pass. If eligibility fails, preserve the result and stop `BLOCKED_APPARATUS` or the contract-appropriate prereveal terminal state.
5. Independently implement the target-agnostic evaluator and its synthetic/unit controls from the frozen evaluation contract. Do not change thresholds or invent new success criteria.
6. Run evaluator self-tests before any target reveal. Preserve failures and fixes in the source-access/deviation record.
7. Create the sealed-gold ref exactly named in the manifest, directly from parent `03528f8ac137007ade205ab0d1d78424df6c388f`. Add only `GOLD.json` and a sealed-gold receipt recording raw/canonical hashes and the parent identity. Do not add evaluator files to this ref.
8. Create the fresh-input ref exactly named in the manifest, independently and directly from the same parent `03528f8ac137007ade205ab0d1d78424df6c388f`. Add the evaluator, evaluator tests, eligibility report, source-access/deviation log, and prereveal freeze receipt. Do not add `GOLD.json`, and do not base this ref on the sealed-gold commit.
9. In the prereveal receipt, record the exact sealed-gold ref/commit/tree and gold hash without copying gold content into the fresh-input ref.
10. Verify mechanically that the fresh-input tree contains no `GOLD.json` and that its ancestry does not include the sealed-gold commit.

## READY_FOR_REVEAL gate

Return `READY_FOR_REVEAL` only if all of the following are true:

- immutable parent hashes match;
- no forbidden source was opened;
- no predecessor gold/evaluator scientific bytes were reused;
- fresh gold is complete under the fixed schema;
- cohort eligibility gates pass without changing frozen inputs;
- evaluator/tests are frozen and pass their prereveal controls;
- sealed-gold ref exists at the exact required name and records exact gold hashes;
- fresh-input ref exists at the exact required name and contains no gold;
- both refs descend directly from the same immutable non-gold parent, not from each other;
- prereveal receipt records both exact ref identities/hashes;
- hidden selector remains unopened and unexecuted.

Otherwise stop at `BLOCKED_APPARATUS` or `CONTAMINATED_PRE_FREEZE`, whichever is accurate.

## Return

Return a compact handoff with:

- terminal state;
- immutable parent commit/tree;
- final fresh-input ref/commit/tree;
- final sealed-gold ref/commit/tree;
- claims/source/pool hashes;
- gold raw and canonical hashes;
- evaluator and evaluator-test hashes;
- eligibility counts/gates;
- source aperture and deviations;
- exact confirmation that fresh-input contains no gold and is not descended from sealed-gold;
- exact confirmation that the hidden selector was not opened or executed;
- what remains unestablished;
- next authorized step.

The strongest claim available in this task is `READY_FOR_REVEAL`. Do not issue a selector research disposition or production recommendation.
