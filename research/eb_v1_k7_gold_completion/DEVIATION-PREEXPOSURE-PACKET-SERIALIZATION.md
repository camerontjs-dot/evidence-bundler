# Pre-exposure deviation — packet serialization identity

Before any reviewer received the blind adjudication packet, the GitHub connector normalized the packet's file serialization such that the raw-byte SHA-256 preregistered for the local generated file did not reproduce exactly in the repository object.

No adjudication had occurred. No reviewer output existed. The 27 scientific items, opaque IDs, proposition texts, passage texts, excluded metadata, rubric, burden threshold, terminal dispositions, and predecessor evidence were unchanged.

To avoid treating whitespace/serialization transport as scientific content, packet identity is now frozen on canonical JSON rather than repository file formatting.

Canonicalization:

- UTF-8 JSON values;
- recursively sorted object keys;
- compact separators `,` and `:`;
- `ensure_ascii=false`;
- SHA-256 over the resulting bytes.

Frozen canonical packet SHA-256:

`4f50b1e385c48b6b15fc223f4700f0c104ce1633742887ced388fe6342420e9c`

This correction is pre-exposure and transport-only. It does not authorize any scientific-object, threshold, label, or reviewer-aperture change.
