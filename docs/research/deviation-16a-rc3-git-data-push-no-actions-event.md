# RC3 apparatus deviation 16a — Git-data ref update did not emit Actions push event

## Discovery

After the exact pre-control apparatus tree was frozen at commit `36ec382c3cd94b6dd1a6be652e49a80469e6b1a4`, the branch ref was advanced through the GitHub Git-data API. GitHub recorded the branch at that exact commit, but no Actions workflow run was created for the configured `push` trigger.

## Exposure state at discovery

- `hybrid_sealed_exposed = false`
- `semantic_sealed_exposed = false`
- no sealed BM25 output had been produced;
- no sealed lexical weak-control output had been produced.

## Classification

Infrastructure-only execution deviation discovered before the first sealed apparatus control.

The correction must not change the frozen scientific object. In particular, the following remain byte-identical to the pre-control freeze at `36ec382c3cd94b6dd1a6be652e49a80469e6b1a4`:

- generator and generator configuration;
- exact expected generated benchmark bytes/tree hash;
- validator;
- evaluator;
- thresholds;
- result schema;
- control runner;
- exact production BM25 adapter/identity pins;
- target preregistration identity.

## Correction

Create one inert marker under `research/eb_retrieval_generalization_rc3/` using the repository Contents API so GitHub emits a normal branch push event matching the already-frozen workflow path filter. The marker has no imports, runtime use, benchmark content, evaluator role, threshold role, or control behavior.

The workflow itself verifies the frozen source hashes and generated benchmark hashes before any sealed control executes. Any scientific-byte drift therefore fails before BM25/lexical exposure.

## Scientific consequence

None expected. This deviation changes only how the already-frozen workflow is scheduled. The first legitimate sealed control remains the first control output produced after all frozen-byte checks succeed.
