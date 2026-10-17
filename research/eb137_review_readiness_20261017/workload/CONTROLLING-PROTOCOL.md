## Prospective representative-workload gate for stable V1

This is separate from #137's eight-case display-context qualification. It is the first workload-usefulness gate for a stable V1 claim.

### Intended workload
Operator-reviewed evidence preparation for bounded biotech / pharmaceutical quality or regulatory questions where:
- the claim/question is declared upstream rather than authored by EB;
- the source set is explicitly bounded before EB runs;
- source bytes are UTF-8 plain text or Markdown at the V1 boundary;
- the task is to identify locally adequate material for later assessment, not to decide truth/compliance.

The synthetic Biotech RAG corpus and the fictional FDA memo are useful controls but **do not count as the representative cohort**.

### Population selection
Use a pre-existing owner-local work queue, packet list or research backlog. Before any EB execution:
1. freeze its ordering/identity;
2. take the first **20 eligible targets** in that pre-existing order, across at least **3 distinct source packets**;
3. do not select or replace targets based on expected EB difficulty or observed output.

If fewer than 20 eligible targets exist, use all available only when there are at least **12**; otherwise disposition is `WORKLOAD_GATE_UNESTABLISHED`.

Eligibility and exclusion must be frozen before outcomes. Conversion to the V1 text boundary must be completed and hashed before target selection; do not change source text after witness work begins.

### Hidden witness pass
Before EB execution, a context isolated from EB output labels each target:
- `ADEQUATE_WITNESS_PRESENT`, with one or more exact locally adequate source spans; or
- `NO_ADEQUATE_WITNESS_IN_BOUNDED_SOURCES`.

For `all_of` declarations, label witnesses per required child. The later EB reviewer must not see these labels/spans.

Contradictory evidence is eligible as an adequate witness. Witnessing is about suitability for downstream assessment, not whether the passage supports the claim.

### Reviewer aperture
The EB reviewer sees only the candidate-generated claim/context/review surface required by the supported workflow. They do not see witness labels, expected yield, earlier EB runs or the evaluator result.

Record elapsed review time per target and every direct raw-source lookup outside the generated review context.

### Frozen stable-V1 thresholds
For this named cohort:

- **Witness-bearing retrieval usefulness:** at least **90%** of targets/required children labelled `ADEQUATE_WITNESS_PRESENT` must expose at least one retained passage that the blinded reviewer can validly accept as locally adequate.
- **Gap honesty:** **100%** of targets/children labelled `NO_ADEQUATE_WITNESS_IN_BOUNDED_SOURCES` must finish with zero accepted passages.
- **No display-context authority smuggling:** **100%** of accepted passages must be locally adequate from the admitted passage text itself. Display-only text cannot supply a missing fact/qualifier/scope.
- **Compound coverage:** **100%** of `all_of` parents may be counted complete only when every required child has accepted adequate evidence.
- **Review burden:** median reviewer time must be **≤ 120 seconds per target** and no more than **25%** of targets may require opening raw source material beyond the generated review surface.
- **Workflow integrity:** zero stale-review reuse, silent ID remapping, manual passage-span editing or manual admission-wire repair. Any required correction must become a new identified candidate/run.

Always-accept/always-reject controls and mechanical binding/consumer checks remain separate controls and do not count toward the representative denominator.

### Disposition
- `SUPPORTED_FOR_NAMED_WORKLOAD_V1`: every threshold passes.
- `NOT_SUPPORTED_FOR_NAMED_WORKLOAD_V1`: valid execution misses one or more frozen thresholds.
- `APPARATUS_INVALID`: witness/reviewer isolation, selection, bindings or measurement are invalid.
- `WORKLOAD_GATE_UNESTABLISHED`: insufficient eligible real workload exists to execute prospectively.

Passing supports only this named workload and tested boundary. It does not establish universal retrieval recall, human-review performance outside this cohort, semantic correctness, source authority, or general RAG quality.
