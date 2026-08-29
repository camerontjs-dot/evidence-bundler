# RC4 apparatus assurance terminal result

## Disposition

**FALSIFIED**

The exact frozen `eb-retrieval-low-overlap-rc4-v1` apparatus is not authorized for Hybrid or Semantic-only target exposure in PR #17.

This is an apparatus result. It is not evidence about Evidence Bundler Hybrid or Semantic-only performance.

RC4 is the final attempt in this exact synthetic sealed-challenge construction program. Do not create RC5 in this program.

## Exact frozen identity

- apparatus branch terminal evidence run head: `73e8cb1fee9cc6a77c64fba5a9e3a49af8fc487a`
- production source SHA: `c8189c31adbab11729c31430c2070126224a2d42`
- production BM25 Git blob: `f8d7dd7e56710453edbca7c51aeea6da949ff903`
- benchmark: `eb-retrieval-low-overlap-rc4-v1`
- generator seed: `173205`
- benchmark tree SHA-256: `f2b2c31614a78d30c424eb6646f6143a496fe916b446d801a9463cc4184a9457`
- corrected freeze manifest SHA-256: `625fdef0a2f3e972e28c4e021b1e2fadc0a44ceb6f793013d603133d1a7e4aaa`
- target config SHA-256: `65c671e25dfd998350cfdb6d2a84c4a46d4db7e867827dd99fd4e57a8003f60e`
- target PR head pinned by the freeze: `27be0c85fdaae9e56a7622e007ca062575e9c433`
- original control-plan Git blob: `43478f173c0bf08bd9636ffe78b6b0da31d109ae`
- generator-config Git blob: `d7ee1093fa3d517ad4b529eb62f9320ed3524045`
- metamorphic-plan Git blob: `afc60a698efdc5a60b40fee158639b8f0a59298c`
- thresholds Git blob: `88e3ad4a976acc36e54cc2c064664240d4050b87`

Scientific source SHA-256 identities include:

- generator: `6d6be86f69efe79fd81db82a4426a98d85202943564af7eec437c15310a6e800`
- validator: `f05587b3e29eb383ada2a501fb1f2d89395c96bacfdfbf812eaf070d69e62b06`
- evaluator: `6e0d109d1cc7d9579ed6060ae5c18dd362dd57c8093dfd4ad029f5d4b317c334`
- result schema: `d28eb645c0e21af798a4771c318e6cf80c4b4d1b2d1367583976b0b8403c313f`
- control runner: `3d44e21b11ef28315b72d81fff8c277ce522203b66ae89b5c712432ccfa85524`
- anti-gaming runner: `8affd36507aa9bf0f98a14479a668bdbfc600b3106def853199e2cc17ecf6d31`
- evaluator-assurance runner: `f82aa905ff376e68cfba77b31d131af724c08c9c528c637367096215fa2b1a19`
- control gate: `f9987abab5f75c0c6a9b975a2690e16f5022d093fa927efa98175ff267f4fa62`
- BM25 adapter: `c0b7a2ee4dfa4edcb04a6fdd6fdbe9ccb9088e088848b7fe583dd5b12324e81b`
- additional pre-exposure control plan: `38c3e57942d84ce2db5ae7f41c0c5c5b94cdf3e33afe702d7187417aaab65211`

## Hosted execution

Decisive hosted run: GitHub Actions `33226828617`.

Artifact:

- ID: `9707144626`
- ZIP SHA-256: `695bb5306d41124e2cf0dd24ce4f4b358adedd7e49ad3e2cf0e20c56f91c5389`

Frozen result hashes:

- validator result: `0686908839ddee93d786a3d8bb012d67d5ef262e8512a6013d612440365ffa5d`
- first sealed oracle control: `74bd5cef071470868d27e6b30e0f4587e0bc9e96fba4195b555ce6e1c5d8ff32`
- evaluator assurance: `20b80ebe3be822f21b316ab8a6829eab3fe481dc7010fa117618049f8deb53d1`
- exact BM25 raw result: `01edc992ce612a4248de49ef0c12031cae330fc1ce048ce4b944f5f48b66871e`
- exact BM25 evaluation: `6a93fff5026c090c506282e652cbf22dc949071609b94c1473bf41b9a078378e`
- BM25 gate: `42dddcba6a7d06ba3bf7997c7be98e7b4b9be230c9092f310afc9eae49999c3f`
- terminal decision: `d1a69d2bd91ceb24da1e7a13d6176b3f8d8e8cd17b0de148b56392727071f402`
- compact terminal evidence summary: `0f2285987515f1cb2d28785194b1c531114b3dcf82842b7740b1d524632a8067`

The exact BM25 raw/evaluation outputs reproduced byte-for-byte across the two hosted replays.

## OBSERVED evidence

The benchmark/freshness/cue-independence validator completed successfully before the sealed result. The first sealed oracle was preserved separately. Evaluator assurance passed all encoded checks:

- oracle positive ceiling;
- decisive-ID mutation sensitivity;
- hard-negative-ID mutation sensitivity;
- family-label / aggregation mutation sensitivity;
- broken-provenance failure;
- result-coverage mismatch failure;
- K/budget enforcement;
- result-schema shape failure;
- deterministic replay;
- source-order enumeration invariance;
- exact result/hash reproducibility.

Exact production BM25 satisfied the strong fresh C01 prerequisite:

- C01 case hit@5: `1.0` against minimum `0.90`;
- C01 counterevidence recall@5: `1.0` against minimum `0.90`;
- first-counterevidence MRR: `0.75` against minimum `0.75`;
- technical violations: zero.

Exact production BM25 did **not** demonstrate the preregistered material L01-L04 weakness:

- combined L01-L04 case hit@5: `0.859375`, required `<= 0.70`;
- combined L01-L04 decisive recall@5: `0.859375`, required `<= 0.65`;
- family L01 hit/recall: `0.8125 / 0.8125`;
- family L02 hit/recall: `1.0 / 1.0`;
- family L03 hit/recall: `0.6875 / 0.6875`;
- family L04 hit/recall: `0.9375 / 0.9375`.

Only one of four low-overlap families failed the target family floor. The preregistration required at least three.

Because that prerequisite failed, the workflow stopped before the sealed ordinary lexical controls, runtime-only gamers, anti-gaming gate, and metamorphic expected-direction suite. Their preregistered bytes remain frozen, but there is no sealed RC4 result for those systems.

## INFERENCES

RC4 repaired one important RC3 failure mode: the exact production BM25 C01 counterevidence baseline is strong on the fresh object.

That is insufficient for apparatus handoff because the same object does not create the required low-overlap weakness. The object therefore cannot discriminate the intended Hybrid-generalization claim through the preregistered BM25 contrast.

The correct apparatus disposition is `FALSIFIED`, not a harder post-hoc benchmark and not an authorization to expose Hybrid.

## HYPOTHESES

The synthetic construction method may be unable to simultaneously manufacture all required properties without leaving lexical structure that makes the low-overlap families too easy for production BM25.

Externally sourced or independently authored heterogeneous material may provide a stronger next evidence design because its retrieval difficulty is less directly authored around the evaluator.

These are successor hypotheses, not conclusions established by RC4.

## UNKNOWNS

Because the BM25 stop fired first, RC4 does not establish whether the frozen runtime construction/style gamer, cue-swap gamer, additional runtime-only gamers, ordinary lexical controls, or sealed metamorphic transformations would have passed or failed.

RC4 does not establish Hybrid or Semantic-only performance.

RC4 does not establish that every synthetic benchmark approach is invalid. It establishes failure of this exact preregistered synthetic sealed-challenge construction program after its final authorized attempt.

## FALSIFIED alternatives

Falsified for the exact RC4 object:

- the proposition that exact production BM25 would be materially weak enough on L01-L04 while remaining strong on fresh C01;
- the proposition that RC4 satisfies all prerequisites needed to authorize target exposure;
- the proposition that this exact synthetic RC4 object can be repaired after the sealed BM25 result without invalidating the preregistered program.

## Deviations

- `18a`: seed `271828` was found to collide with prior benchmark lineage and was corrected to `173205` before implementation/exposure.
- `18b`: two additional runtime-only gaming falsifiers were added before freeze/exposure. No gate was relaxed.
- `18c`: first hosted run `33226673867` stopped before any sealed control because the freeze manifest contained a mistyped Git-blob binding for the unchanged original control plan. Only the manifest binding was corrected.
- `18d`: run `33226760159` crossed the sealed oracle/evaluator boundary but exact BM25 could not import because the hosted environment omitted the production-declared PyYAML dependency. No BM25 output existed. The workflow alone was repaired to install the already-declared dependency; scientific bytes and decision semantics remained unchanged.

All failed runs remain preserved.

## Exposure / contamination state

- `hybrid_sealed_exposed = false`
- `semantic_sealed_exposed = false`
- no candidate output was used to construct, tune, repair, or reinterpret the RC4 scientific object.

## Authorization

**TARGET EXECUTION PROHIBITED.**

Do not run PR #17 against this object.

Do not run Semantic-only against this object.

Do not create RC5 in this exact synthetic sealed-challenge construction program.

The smallest successor question is methodological: evaluate a costly-to-fake benchmark source such as externally sourced heterogeneous corpora, independently authored cases, transformed real documents, independent/cross-repository benchmark construction, or an established third-party retrieval benchmark.
