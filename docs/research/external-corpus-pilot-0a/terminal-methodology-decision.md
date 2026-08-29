# Pilot 0A terminal methodology decision

## Decision

`INCONCLUSIVE`

## Why

The pilot froze a clean 10-case pre-retrieval methodology object and found material upstream risks, but it did not execute the scientific passage/gold experiment. Exact selected source bytes were not materialized in this runtime, and two genuinely independent adjudicators were unavailable.

FreshStack also has a specific unresolved source-aperture problem: its published candidate document lists are entangled with retrieval-oriented benchmark construction, and using them to choose passages would violate this pilot's firewall. SciFact has a cleaner source aperture through `cited_doc_ids`, but the selected frozen bytes and independent labels were not executed.

The evidence therefore does not support `SUPPORTED FOR EXTERNAL-CORPUS PILOT`. It also does not justify declaring the entire external-corpus methodology `FALSIFIED`, because the decisive passage-stability and independent-gold tests were not run.

## Exact missing evidence

- frozen selected FreshStack and SciFact source bytes + hashes;
- FreshStack deterministic provenance restoration and a qrel-independent bounded source aperture, or a preserved ineligibility result;
- two frozen independent adjudication records;
- disagreement taxonomy;
- two-representation passage correspondence;
- scientific gold invariance/sensitivity results.

## Next authorized task

Execute Pilot 0A again **only as completion of this already frozen scientific object**:

- same 10 selected indices;
- same source-aperture rules;
- same two passage representations;
- same relevance contract;
- same falsifiers;
- no production BM25, Hybrid, Semantic-only, or candidate-retriever exposure.

Do not expand to 24–30 cases yet.
