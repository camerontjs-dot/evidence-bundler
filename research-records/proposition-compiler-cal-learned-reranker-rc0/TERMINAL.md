# Proposition Compiler CAL-Specific Learned Reranker RC0 — Terminal Record

## Governance disposition

`INCONCLUSIVE`

Experimental classification: `INCONCLUSIVE_STRONG_RANKING_SIGNAL_NO_SAFE_CALIBRATION`

This is a research evidence record. It does not authorize learned-score semantic authority, production selection, merge, Proposition Compiler promotion, Contract change, release, or production Evidence Bundler mutation.

## Exact frozen learned object

- frozen model SHA-256: `a4e6aecbb02af4cb1cdd4bd6116a955ca4cc05480ad93daf00ca28323de91e7b`
- frozen model blob: `0e9e10d998c2641ea90a19c079125394d735ff0c`
- training replay: byte-identical
- held-out predecessor calibration status: `NO_ZERO_UNSAFE_CALIBRATION`

The calibration failure is preserved. No post-hoc threshold was substituted.

## Preserved pre-score harness failure

The first decisive attempt, run `34679031164`, job `103514041469`, stopped before fresh scoring because the gold-firewall grep also scanned training/calibration functions in `cal_ranker.py` that legitimately name gold fields. No fresh model scores were produced in that attempt. Its partial artifact is `10293316009`.

The repair at commit `4fd2b52e31ed6b217a711d4ad01d17c3993bf70d` narrowed only the firewall check. Frozen model bytes, learned weights/features, scorer, evaluator, shared fresh cases, and gold were unchanged.

## Exact decisive execution

- decisive head: `4fd2b52e31ed6b217a711d4ad01d17c3993bf70d`
- GitHub Actions run: `34679133071`
- job: `103514329736`
- artifact: `10293891228`
- artifact digest: `sha256:caac0450b20b3179a01573d67545a83f748132909a3f9f0531ec297ea6c5da0e`
- shared fresh cohort SHA-256: `480c2e876fefd66c3315152cefdb531b739e83e42a1c29a9371b2507a21c0319`
- frozen base raw SHA-256, run A and exact replay: `0d2f772681f35fe2472ed8fbaf14e8d706b21f197cdb55232d6118161488b458`
- learned raw SHA-256, run A and exact replay: `decc1f1160f283ac3b782c40093f1664ce19ce1a9b5eb6712efc47ebf0e74dec`
- evaluation SHA-256: `b978659af6aff8ef5a52b6ef8f23c2811772ae17ebe0404579de533b42f82bab`
- terminal SHA-256: `61a41efdea3db7af9514f4d926e13c8de8229d06d2ade5d58f2885ef1d831076`
- replay: byte-identical
- maintained CI at decisive head: PASS

## Fresh result

Shared fresh surface: 24 roots / 96 competing candidate decompositions, including 4 intrinsic-ambiguity roots.

### R2_bidirectional_nli

- pairwise safe-over-unsafe: `0.8571428571428571` (54/63)
- critical pairwise safe-over-unsafe: `0.8333333333333334` (45/54)
- top-1 safe preference rate: `0.70`
- calibrated safe selections: 10
- calibrated unsafe selections: 3
- correct abstentions: 1
- false abstentions: 10

### T1_CAL_LINEAR

- pairwise safe-over-unsafe: `0.9682539682539683` (61/63)
- critical pairwise safe-over-unsafe: `0.9629629629629629` (52/54)
- top-1 safe preference rate: `0.95`
- fresh overall pairwise gain over R2: `+0.11111111111111116`
- fresh critical pairwise gain over R2: `+0.12962962962962954`
- selection calibration: `NO_ZERO_UNSAFE_CALIBRATION`
- authority-bearing selection: unavailable / not established

## Interpretation

The learned CAL-specific signal generalized strongly as a ranking measurement on genuinely fresh cases. It exceeded frozen generic bidirectional NLI both overall and on critical unsafe mutations, and crossed the preregistered 0.95 ranking thresholds.

It did not satisfy the positive gate because the frozen predecessor calibration could not produce a zero-unsafe selection rule. That limitation is not erased by the strong fresh ordering result.

The supported claim is therefore narrow but useful: CAL-specific weighting over frozen semantic measurements and explicit hazard features contains substantial proposition-failure information that generic NLI does not capture. It is evidence for retaining a learned reranking lane as a subordinate measurement, not for treating that lane as semantic authority or allowing it to select by itself.

## Competing explanation / next discriminating question

The largest remaining uncertainty is whether the calibration failure reflects:

1. an intrinsically non-authoritative ranking signal whose best role is only ordering candidates inside an authority-approved set; or
2. an inadequate calibration/decision geometry that could safely exploit the strong ranking signal if the decision boundary were separately learned and evaluated.

This RC0 cannot answer that because any threshold repair against the revealed cohort would be post-result tuning. A successor must be a new experiment with a fresh calibration/decision design and fresh decisive evidence.
