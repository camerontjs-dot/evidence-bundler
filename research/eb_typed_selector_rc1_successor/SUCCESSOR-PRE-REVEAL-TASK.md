# EB Typed Selector RC1 Successor — Context-Free Prereveal Task

Act as the independent fresh-corpus author, adjudicator, evaluator author, and prereveal qualification executor.

This is the successor to one `BLOCKED_APPARATUS` attempt. The hidden selector was not revealed. The predecessor failure was execution-only: it could not run the exact frozen Evidence Bundler first stage.

## Information boundary

Read `SUCCESSOR-MANIFEST.json` first and obey its allowlist/denylist.

Do not inspect selector-development material, PR #82, issue #80, prior selector-result artifacts, or the blocked predecessor's corpus/pools/gold/evaluator.

The only scientific object carried forward is:

`research/eb_typed_selector_rc1_successor/FROZEN_CLAIMS_PROFILES.json`

Its provenance is frozen in `SUCCESSOR-MANIFEST.json`.

## Objective

Produce a valid `READY_FOR_REVEAL` prereveal freeze for the same bounded question: selection of at most 3 candidates from exact frozen depth-10 Evidence Bundler nominations.

## Work

1. Create a dedicated successor authoring branch from this exact bootstrap branch.
2. Record exact sources opened before freeze.
3. Keep the 30 frozen claims/profiles unchanged unless a complete replacement lane is required by the existing fresh-cohort rules.
4. Author **new source corpora from scratch** for all lanes. Do not reuse or paraphrase predecessor source fixtures.
5. Save them as `research/eb_typed_selector_rc1_successor/SOURCE_FIXTURES_V2.json` using this shape:

```json
{
  "schema": "eb-typed-selector-rc1-successor-source-fixtures-v1",
  "claims_profiles_sha256": "sha256:0e142d3bace270f9c7d45c7c35f3b1e17ab06156ed936681c98ccdaf39f6e15d",
  "lanes": [
    {
      "lane_id": "L001",
      "sources": [
        {
          "source_id": "L001-S01",
          "media_type": "text/plain; charset=utf-8",
          "content": "fresh passage text"
        }
      ]
    }
  ]
}
```

Use 12-20 fresh sources per lane. Keep each source at or below 1700 characters. Use opaque IDs with no gold meaning.

6. Commit the fresh source fixtures. The repository workflow `Research - EB Typed Selector RC1 Authoritative First Stage` will then:
   - check out exact EB commit `4e1f6fe00e7c350b28f52bfea14f1f8988847884`;
   - install that exact package;
   - execute its pinned V1 `build_package` machinery with exact 10/3 config identity;
   - run every lane twice;
   - require exact depth-10, unique-candidate, deterministic output;
   - upload a non-gold authoritative first-stage artifact.
7. Do not substitute local retrieval. If that workflow does not succeed, stop `BLOCKED_APPARATUS`.
8. Open only the successful first-stage artifact for your own authoring commit. Verify the exact pinned commit/config/hash receipt, then freeze its authoritative candidate pools on the successor input lineage.
9. Adjudicate **new gold from those authoritative pools**, not from predecessor pools.
10. Rebuild the target-agnostic evaluator and controls from the frozen `EVALUATION-CONTRACT.md`. Do not reuse the predecessor draft evaluator bytes.
11. Apply the existing 30-lane cohort/eligibility rules. If a lane fails, preserve it and follow the preregistered replacement rule. Never repair an exposed corpus in place.
12. Freeze non-gold inputs/evaluator separately from sealed gold, with exact hashes, source-access log, deviations, workflow run/artifact identity, and denylist declaration.
13. Stop at exactly one terminal state:
   - `READY_FOR_REVEAL`
   - `BLOCKED_APPARATUS`
   - `CONTAMINATED_PRE_FREEZE`

Do not reveal or execute the hidden target in this lane.

## Completion

For `READY_FOR_REVEAL`, return the same structure required by `RETURN-HANDOFF-TEMPLATE.md`, plus:

- authoritative first-stage workflow run ID;
- artifact ID/digest;
- pinned EB head/tree recorded by the workflow;
- confirmation that predecessor source/pool/gold/evaluator bytes were not reused.

No selector research disposition or production recommendation is authorized here.
