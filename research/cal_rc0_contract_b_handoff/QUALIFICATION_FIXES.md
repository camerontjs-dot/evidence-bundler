# Qualification wrapper note

The initial RC0 implementation commit `dec6c8ded95372878699645f97667f27bc34c31b` exposed two narrow qualification issues that do not alter retrieval/admission semantics:

1. repeated factual-context `SourceContext` rows could be produced when multiple retained evidence IDs share one source ID;
2. the returned per-case `bundle_hash` was captured before `attach_factual_context` re-sealed the Contract B tree.

`qualified_handoff.py` corrects only those two surfaces for qualification. It does not change candidate ranking, retained K, admission decisions, Contract A proposition identity, root-union policy, or any semantic field. The wrapper is single-threaded research infrastructure; it temporarily intercepts the factual-context attachment call only while constructing the qualification bundles.
