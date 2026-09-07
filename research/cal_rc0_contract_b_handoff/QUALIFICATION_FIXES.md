# Qualification wrapper note

The initial RC0 implementation exposed two narrow representation issues before profile freeze:

1. repeated factual-context `SourceContext` rows could be produced when multiple retained evidence IDs share one source ID;
2. the returned per-case `bundle_hash` was captured before `attach_factual_context` re-sealed the Contract B tree.

The first qualification wrapper corrected those two surfaces without changing retrieval/admission semantics.

## Post-freeze A2/B1.2 boundary counterexample

A later live boundary review exposed a more important issue: the initial B writer internally filled legacy Contract B core fields that Contract A 2.0 does not carry or authorize. The tree could validate while the adapter still overstated the upstream source of those values.

That observation is preserved as a counterexample. The frozen retrieval/admission profile is not rewritten to hide it.

Contract A 2.0 explicitly permits a separate compatibility carrier where a legacy consumer still requires one, while stating that such a carrier is not Contract A 2.0 authority. The successor qualification wrapper therefore adds one additional, bounded responsibility:

3. require `fixtures/contract_b_compatibility_carrier.json`, verify its non-authority declarations, rewrite only legacy B compatibility surfaces from that explicit carrier, bind source hashes/passages back to exact A2 source representations, and reseal/revalidate the resulting B tree.

The compatibility carrier is not an input to retrieval, retention, or admission. It cannot alter candidate ranking, retained K, review decisions, Contract A proposition identity, root-union policy, or aperture history.

The direct pre-counterexample B writer remains in the research record as a failed/superseded compatibility attempt. `qualified_handoff.py` is the qualification entrypoint after this counterexample.
