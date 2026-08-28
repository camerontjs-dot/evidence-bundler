# EB Retrieval Low-Overlap RC3 — Fresh Apparatus Assurance

**PR class:** Research Infrastructure / Draft

**Dependent target experiment:** Evidence Bundler PR #15.

**Current state:** apparatus design only. No semantic or hybrid retrieval may be run on the fresh sealed split in this apparatus PR.

## Objective / decision

Construct, freeze, and adversarially assure a fresh retrieval challenge that can discriminate the bounded PR #15 decision:

> Does the exact existing hybrid retrieval candidate materially improve meaning-preserving low-lexical-overlap retrieval over the exact frozen production BM25 baseline without materially degrading counterevidence retrieval?

This task evaluates the apparatus, not the hybrid candidate.

Allowed terminal apparatus handoff decision:

- `SUPPORTED FOR PROMOTION` — exact frozen apparatus may be handed unchanged to PR #15;
- `FALSIFIED` — the apparatus cannot satisfy its preregistered validity/discrimination requirements;
- `INCONCLUSIVE` — evidence cannot establish a valid discriminator;
- `SUPERSEDED` — replaced before target exposure by an explicitly versioned successor.

## Authority / frozen predecessor state

- target preregistration: PR #15;
- terminal predecessor measurement: PR #14 (`FALSIFIED`);
- production-source comparison identity: `c8189c31adbab11729c31430c2070126224a2d42`;
- current Research-Infrastructure `main` base: `2643385c998dd3b08af84eb37f3f089fea7d5e73`.

Do not reuse RC2 sealed text as RC3 challenge material. RC2 may be inspected only as predecessor evidence motivating the family definitions.

## Fresh benchmark identity to create

Name: `eb-retrieval-low-overlap-rc3-v1`

Generator seed: `141421`

Sealed split: exactly 64 answerable cases:

- L01 terminology substitution: 16;
- L02 compositional paraphrase: 16;
- L03 lexical-decoy low-overlap: 16;
- C01 counterevidence retention: 16.

All cases use `maximum_passages = 5`.

No RC2 case text, decisive passage, hard negative, or fictional entity stem may be copied into RC3.

## Case construction invariants

Every L01-L03 case must contain:

1. a query/claim and at least one decisive passage preserving the same intended proposition while reducing lexical overlap;
2. at least one hard negative with **greater surface lexical overlap** to the query than the decisive passage;
3. enough additional distractors that return-all/first-N is not a qualified strategy at K=5;
4. exact source/passage identity and reconstructable text provenance;
5. evaluator-only gold and family labels physically separated from runtime material.

Family intent:

- **L01:** terminology/alias substitution, where decisive evidence uses alternate domain terms rather than claim wording;
- **L02:** compositional paraphrase, where the decisive meaning is expressed through a materially different construction rather than word replacement alone;
- **L03:** lexical decoy, where a wrong passage is deliberately more lexically similar than the decisive passage;
- **C01:** fresh counterevidence cases to detect semantic/hybrid gains purchased by losing the RC2-supported counterevidence capability.

The generator may use deterministic concept/alias dictionaries and templates, but the final sealed object must be frozen by exact bytes and hashes. Do not choose or discard cases after observing hybrid/semantic retrieval.

## Runtime / evaluator firewall

Runtime retriever-visible material may include only:

- case id;
- query/claim text;
- permitted passage text/identity;
- accessible subset/scope identity;
- K/runtime configuration needed for retrieval.

Evaluator-only material contains decisive identities, hard negatives, family labels, counterevidence labels, and any construction diagnostics not needed by the retriever.

## Controls

The apparatus must implement and freeze at minimum:

- oracle;
- exact frozen `c8189c31...` BM25 baseline;
- null;
- first-N/source-order;
- token overlap;
- bag-of-words TF-IDF cosine;
- character-trigram similarity;
- return-all;
- provenance-corrupt;
- hard-negative-biased;
- false completeness/aperture claimant where the schema supports it;
- semantic answerability liar where the schema supports it.

**Forbidden in this apparatus PR:** running PR #15 Hybrid or Semantic-only candidate on sealed RC3 cases.

## Apparatus acceptance / discrimination gate

The exact frozen sealed apparatus is eligible for handoff only if:

### Positive ceiling

- oracle low-overlap case hit@5 = 1.0;
- oracle decisive recall@5 = 1.0;
- oracle counterevidence recall@5 = 1.0;
- zero oracle technical/provenance/scope/receipt violations.

### Required weak-system rejection

- exact BM25 fails at least one PR #15 primary low-overlap gate;
- token-overlap, TF-IDF, and char-trigram controls each fail qualification;
- at least two distinct substantive failure categories are represented across lexical weak controls;
- null and first-N do not qualify;
- return-all is rejected by budget;
- provenance corruption is rejected by provenance integrity;
- hard-negative-biased control materially underperforms oracle;
- completeness/answerability liar controls are rejected on their intended surfaces where applicable.

If exact BM25 clears every low-overlap target gate, the benchmark is not a useful discriminator for PR #15. Stop before hybrid/semantic exposure and return `INCONCLUSIVE` or `FALSIFIED` according to the observed defect. Do not move thresholds around the result.

## Required evaluator sensitivity / invariance checks

Freeze named checks for:

- decisive-identity mutation sensitivity;
- hard-negative identity mutation sensitivity;
- exact text/provenance corruption sensitivity;
- family-label/aggregation sensitivity where family floors are used;
- deterministic replay;
- source enumeration reversal invariance for oracle/control behavior;
- result-coverage mismatch fail-closed behavior;
- K/budget enforcement.

## Frozen target thresholds

The apparatus must encode PR #15 thresholds exactly, including:

- combined L01-L03 case hit@5 >= 0.85;
- combined L01-L03 decisive recall@5 >= 0.80;
- combined first-decisive MRR >= 0.60;
- each L01-L03 case hit@5 >= 0.75;
- each L01-L03 decisive recall@5 >= 0.70;
- Hybrid minus BM25 case hit >= 0.25 absolute;
- Hybrid minus BM25 decisive recall >= 0.25 absolute;
- C01 counterevidence case hit@5 >= 0.90;
- C01 counterevidence recall@5 >= 0.90;
- C01 Hybrid regression versus BM25 <= 0.05 absolute;
- zero budget/provenance/scope/shape/completeness-overclaim/answerability-overclaim violations;
- score invariance tolerance `1e-12` with exact hit identity/rank invariance.

Thresholds may not be changed after the first sealed apparatus control run.

## Freeze receipt

Before terminal handoff, record exact hashes/identities for:

- generator and generator configuration;
- validator;
- runtime passages/scope/cases;
- evaluator-only gold;
- evaluator source;
- thresholds;
- result schema;
- control runner;
- preregistration;
- full benchmark tree;
- first sealed control output.

The terminal receipt must explicitly state:

- `hybrid_sealed_exposed = false`;
- `semantic_sealed_exposed = false`;
- whether exact BM25 was run as the preregistered weak/production baseline;
- whether all required lexical controls failed qualification;
- whether oracle qualified;
- whether evaluator mutation/invariance checks passed.

## Stop rule

Stop once the exact fresh object is frozen and its control/evaluator evidence establishes one terminal apparatus disposition.

Do not proceed to the hybrid/semantic target run in this PR.

If supported, the only authorized next action is to hand the **unchanged exact frozen apparatus** to PR #15 for its first legitimate target exposure.
