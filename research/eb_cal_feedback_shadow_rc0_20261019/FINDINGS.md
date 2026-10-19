# CAL → EB evidence-need feedback: RC0 shadow findings

**Research disposition: INCONCLUSIVE for an actual CAL-triggered feedback loop.**
**Supported with bounds:** the existing EB native retriever can construct a single contiguous on-target source passage for the deliberately split p07 fixture when the chunk size is enlarged. This does not establish the adequacy of a general retrieval policy, automated CAL feedback, or canonical Contract B/CAL compatibility.

## Identities and sequence

- Owner: Evidence Bundler issue #132; CAL issue #205 remains owner of semantic assessment and any typed evidence-need producer. Portfolio route: apparatus-contracts #137.
- Public synthetic controls: frozen EB #134 acceptance kit at a622fd70c5c48e826b5f2ec9907754e3a35f2d67, closure sha256:01cac06293afdb4fd145c3f7b64464799620eac2fcce80ffc2d5bc677553878c.
- Installed EB V1 0.3.0.dev0: source b09d25828d269a226a7d57a9c3b6d3b11a597b24, wheel sha256:cf22a25c74dce2b46e6562caeb67df69168fa026ab085a0d234198e501876405. Native V1Config is a separate configurable surface; it is not the fixed installed CLI projection route.
- Pinned Contract A 2.0.0: 529c92b49a34d5c610618551a8737f019f9fa332; Contract B 1.2.0: c314e53bd91c0736aa4370a364673b069aceb43e; CAL consumer: 64b6c7702696c851057c1cf0b2c105b1c81db543.
- Preregistration commit cd9395fba0a552bf952150eb191252706131b6e2; frozen code/controls commit 47a6427639508e92a80824f99cc4f80e74942ab3, runner SHA-256 20ac0391adbf441d2433ae708b14993aef5bb1d83d8f24f93d4c74851544af16.
- One first exploratory run generated RESULT.json sha256:a829cf3ebfd1a423faa03643aa6009fa9e9d8c7b41c8b643b6544d613c5ed145. A separate *supplemental interface conformance* check generated SEAM-CHECK.json sha256:82f455e333269167f0f9a924e0b13de681a7773988274f79980efb43954a8ce1.
- Experiment is informed: author/supervisor already knew the #134 opportunities and p07/p06; no blind CAL judgement, independent reviewer, new source acquisition, or representative denominator.

## Actual EB native retrieval comparison

Every frozen source, upstream claim, source hash and target ID remained fixed. Engine and tokenizer remained deterministic Okapi BM25 with depth 10, retention 3 and overlap 80. Only research-native chunk_max_chars changed (1800, 2400, 8000); no packaged release/default changed.

| Case/property | Current 1800 | 2400 | Research-native 8000 |
|---|---:|---:|---:|
| p07 nominated chunks | 6 | 5 | 1 |
| p07 retained chunks | 3 | 3 | 1 |
| p07 total retained chars | 2,286 | 2,862 | 6,706 |
| p07 same-span subject + value + unit marker | No | No | Yes |
| p06 second child: 24-month-retention witness | No | No | No |
| p08 no-source candidates | 0 | 0 | 0 |

p07's retained current spans are 0:305 (Ilex-9/unit but no number), 6484:6706 (value, defers subject/unit), and 307:2066 (administrative entries). 2400-character windows preserve this separation. With 8000 allowed, the existing chunker retained one contiguous 0:6706 span from its unchanged 6707-character source. It includes the explicit header/table cross-reference and all required claim elements. The single contiguous span avoids needing to import an absent fact from a *different* admitted passage. This is an informed contextual reading, **not proof of automated semantic sufficiency**.

The recovered retained text is about 2.93 times the 1800 baseline retained-character total. Whole-source rescue may be expensive on realistic material. p01/p02 positive and contradiction cases, p03 both declared children, p04 wrong-subject, p05 missing relation, p06 partial compound and p08 empty-source controls did not magically acquire their missing evidence when the chunk limit increased. The broad always-widen strategy gives no improvement on already adequate and no-witness cases; no reliable trigger-selection policy was established.

Baseline B0 package objects regenerated from the installed EB wheel matched all eight earlier frozen unreviewed product packages byte-for-byte. The generated native candidates preserved original source bytes, contiguous spans, text hashes, source identities, upstream propositions, nomination and retained states, and explicit needs-review status. Synthetic CAL-shaped evidence-need descriptors passed binding/shape checks; forged target IDs, package hashes, source-routing fields and verdict-directed requests were refused. **Those descriptors are authored by this experiment; they are not emitted by CAL or used to cause the comparison-arm runs.**

## Actual CAL / Contract B boundary

The pinned CAL code contains failure types UPSTREAM_APERTURE_INSUFFICIENT and EVIDENCE_NOT_ADMITTED, but inspection found **no implemented typed evidence-need→EB retriever request** on the pinned interface. The legacy CAL v1 intake also exposes a full bundle passage set for certain auditable claims, but the narrower pinned factual-context semantic view filters to accepted links. These paths are not interchangeable and do not automatically establish a no-operator workflow.

A real pinned CAL Contract B intake inspection of all eight **unreviewed** package bundles found nomination/history entries, but exactly **zero admitted links** in its semantic context for every case, including p01 and p07. Thus absence of admitted evidence at that interface cannot distinguish a truly absent witness from a perfectly adequate nominated passage awaiting review. An automated loop would need CAL-owned assessment of permitted candidates before any acceptance gate, or another explicitly authorized route.

A separate actual B carrier conformance check shows:
- exact current 1800 V1 package passes the frozen integration-profile validator;
- the 8000 research-native recovered package is **rejected**, correctly, with 'native package config is not the frozen eb-v1-integration-10x3-rc0 profile'.

This is not a generic Contract B insufficiency finding and not authorization to weaken the locked carrier. It is evidence that the present installed product path does not transport this alternative configuration as a qualified successor.

**Evaluator control:** the string-marker proxy also accepted a fabricated text describing 0.08 as an obsolete *rejected* value. It is therefore explicitly incapable of judging semantic adequacy on its own. No promotion or general accuracy conclusion is based on it.

## Where the earlier ideas stand

EB #91 previously proposed *upstream* Gate-provided evidence-shape hints, with an EB authority firewall; it is design-only, and it does not implement feedback from downstream CAL. EB #50 and #80 preserve parent/child and post-retrieval selection research, not a deployed CAL→EB retry path. CAL #3 and #205 specify the CAL intake/assessment boundary and independent process results. No live current V1 CAL-produced bounded retry request or qualified EB consumer of such a request was identified in the inspected owners.

## Inference, alternatives, and next discriminating check

- **Observed:** source-coherent rewindowing is possible using already-maintained EB native machinery on the split-context p07 fixture; the smaller fixed 2400 window did not recover it. CAL intake's unreviewed semantic context has no admitted evidence. The fixed projection refuses changed V1Config.
- **Inference:** retrieval/chunk boundaries can cause the p07 local-adequacy gap, but these observations do not determine the best recovery policy or whether a CAL judge can accurately detect/describe it.
- **Alternative explanations/limits:** a better chunker, a grouped evidence representation, neighboring-section recovery, or a qualified CAL audit over original candidate evidence could be better than whole-source widening. The proxy can be fooled by juxtaposed tokens, and no representative workload has been measured.
- **Smallest separate successor:** under CAL #205, check whether an existing qualified measurement output can distinguish 'missing relation within retrieved context' from 'unsupported semantics', 'not admitted', and 'no witness in bounded sources' on p07/p06/p01 controls. Test an **adapter over existing verified B nomination ledger** before introducing any new contract; only then let EB own a bounded, replayable local recovery and return fresh evidence to CAL for a separate assessment. Preserve pass counts, source span hashes, budget and failure state.
- **Product/policy decision remains open:** dropping mandatory pre-CAL admission or allowing candidate evidence into CAL must be explicitly owned; a shadow test cannot redefine the current 'accepted' semantics, CAL's independent first-pass rules, or the public B carrier.

No product/contract change, release, integration or representative workload occurred. The historical #141 local-model review remains a separate valid failure for its exact reviewer; it was not rerun or repaired. Current EB #137 and CAL candidates remain untouched.
