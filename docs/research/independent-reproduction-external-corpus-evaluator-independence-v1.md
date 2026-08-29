# Independent reproduction record

## Frozen contract surface

Evaluator A and evaluator B consume the same manifest, hidden-gold object, ranked run, and frozen contract semantics. Neither imports the other implementation or a shared evaluator/metric helper. The canonical commitment helper is separate and neither evaluator imports it.

The implementations use different internal validation, indexing, and aggregation structures. On the frozen dummy tuple they return exactly equal result objects.

## Dummy result

At K=3:

- hit@K macro: `1.0`
- evidence/support recall@K macro: `1.0`
- counterevidence recall@K macro: `0.5`
- joint/group coverage@K macro: `0.75`
- nDCG@K: `null` because an explicit `UNKNOWN` judgment makes the frozen graded metric ineligible
- judgment coverage@K macro: `1.0`
- resolved-judgment coverage@K macro: `1.0`

These are dummy fixture expectations, not Evidence Bundler performance.

## Adversarial suite

The suite covers oracle behavior; missing decisive/support evidence; rank movement across K; jointly-required versus alternative-sufficient groups; SUPPORT/COUNTEREVIDENCE mutation; unknown/duplicate ranked IDs; malformed ranks; corpus-version, corpus-hash, and benchmark-hash mismatch; partial qrels; UNKNOWN versus irrelevant/unjudged; nDCG eligibility; serialization reorder; source/passages order permutation; stable-ID renaming; commitment verification; semantic mutation; and evaluator implementation separation.

Local frozen result after dummy reveal: `20 passed`.

## Independence classification

**Observed:** two non-importing implementations agree over the frozen dummy and adversarial suite.

**Not established:** evaluator B was not authored in a genuinely isolated context blind to evaluator A. The same supervisory context produced both implementations, and the attempted Conduit clean-agent launch was unavailable.

This therefore supports **separate implementation / cross-check**, not the stronger CAL Pipeline claim of a genuinely independent Consumer-B-style reproduction.
