# Counterevidence Aperture Localization Dev RC1 — Preregistration

Status: preregistered before diagnostic execution.

## Decision question

Why does the frozen RC1 contradiction/counterevidence path fail to recover decisive R02 counterevidence at the preregistered final K even though ordinary unprefixed semantic retrieval previously showed that the evidence exists at wider depth?

The purpose is localization only. No retrieval semantic or production default may change in this experiment.

## Frozen predecessor authority

- terminal predecessor PR: #42
- predecessor final research head / apparatus lineage: `d02b7c61dc0d2779f35a8fa9eb534d9c301abdd8`
- predecessor decisive implementation: `755a1877cb321b8e9a24e6a770ce7dd40e19433f`
- predecessor decisive run: `33284797206`
- frozen RC2 benchmark tree SHA256: `0a9da82e3e28fd3650936fc715904e39c91f34a944ac7c3bfe40277953870dad`
- embedding model: `BAAI/bge-small-en-v1.5`
- immutable embedding revision: `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- contradiction prefixes, in order:
  1. `evidence against`
  2. `limitations of`
  3. `contradicts the claim that`
  4. `does not support`
  5. `fails to demonstrate`
- RRF k constant: `60`
- contradiction reranking: disabled
- contradiction text-role gate: disabled
- split: RC2 dev only
- sealed split: prohibited

## Fixed arms

For every dev case and every exact contradiction prefix, execute lexical and semantic child retrieval at:

- K
- 2K
- 4K

where K is the case's frozen `runtime_config.maximum_passages`.

At every depth the gold-blind runner must preserve:

1. lexical ranking per prefix;
2. semantic ranking per prefix;
3. per-prefix lexical/semantic candidate unions;
4. complete cross-prefix fused RRF order before final output truncation;
5. complete parent-candidate order after the predecessor max-parent aggregation with no text-role filtering;
6. the exact parent passage identities retained by final output K;
7. duplicate burden against the ordinary unprefixed semantic support channel at K.

No posthoc relevance/counterevidence annotation may be read by the runner.

## Gold boundary

The runner may read only the frozen RC2 runtime passages, dev cases, apertures and the fixed retrieval apparatus. It must write the raw artifact before a separate analyzer opens `evaluator_only/dev_gold.jsonl`.

The workflow must hash the raw artifact before invoking the analyzer. The analyzer may verify and record that pre-analysis digest but may not alter the raw artifact.

## Primary discriminator

For every frozen dev passage annotated `decisive_counterevidence`, and especially each R02 passage, report:

- first lexical prefix/depth where found, else absent through 4K;
- first semantic prefix/depth where found, else absent through 4K;
- best lexical rank by depth;
- best semantic rank by depth;
- fused rank at K, 2K and 4K;
- parent-candidate rank at K, 2K and 4K;
- whether final K retains it at each child depth.

Classify the observed failure surface exactly as follows:

- `PREFIX_QUERY_SUPPRESSION`: absent from every semantic contradiction child ranking through 4K;
- `CROSS_PREFIX_RRF_GEOMETRY`: present in at least one child ranking but poor/absent after fusion or parent aggregation;
- `OUTPUT_TRUNCATION`: useful parent/fused rank exists but the item is removed only by final K;
- `WIDE_NOISY_RECOVERY`: recovered only at wide depth and accompanied by severe hard-negative/non-counterevidence/duplicate burden, so widening is not yet production-quality evidence;
- `MIXED_OR_OTHER`: observations do not support one of the above exclusively.

The analyzer may report more than one mechanism across decisive passages; it must not force a single global cause if the passages differ.

## Controls and invariants

- exact predecessor prefixes only;
- exact pinned BGE only;
- RRF k=60 only;
- no contradiction reranking;
- text-role gate disabled;
- ordinary support channel unchanged and used only for duplicate-burden comparison;
- at least one no-decisive-counterevidence family retained to measure spillover;
- no parameter tuning after results;
- no sealed data;
- no production code/default change.

## Falsifiers / legitimate negative outcomes

A negative result is preserved if widening through 4K still does not recover decisive R02 counterevidence. Such a result supports prefix/query suppression rather than a wider-aperture repair.

If recovery occurs only at 4K with substantial noise/duplicates, that does not support production widening by itself.

## Stop rule

Stop after the raw diagnostic, posthoc analyzer, exact receipts, terminal classification and issue/PR reconciliation. Do not change prefixes, add a reranker, change the text-role gate, touch sealed data, tune after observation, or alter production defaults.
