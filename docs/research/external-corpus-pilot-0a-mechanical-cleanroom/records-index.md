# Pilot 0A mechanically isolated clean-room record index

Terminal disposition: `FALSIFIED`.

| Required durable record | Durable artifact |
|---|---|
| 1. live starting state | `01-live-starting-state.json` |
| 2. frozen Pilot 0A identities | `02-frozen-identities.json` |
| 3. clean-room access allow-list | `00-pre-execution-access-receipt.json` |
| 4. forbidden-surface list | `00-pre-execution-access-receipt.json` |
| 5. initial exposure receipt | `00-pre-execution-access-receipt.json` |
| 6. contamination/exposure log | `03-contamination-exposure-log.json` |
| 7. FreshStack official/historical provenance join | `04-freshstack-provenance.md`, `05-freshstack-failed-ambiguous-joins.json` |
| 8. failed/ambiguous FreshStack joins | `05-freshstack-failed-ambiguous-joins.json` |
| 9. FreshStack source-aperture decision | `06-freshstack-source-aperture.md` |
| 10. SciFact immutable acquisition record | `07-scifact-immutable-acquisition.md` |
| 11. licensing decision | `08-licensing-decision.md` |
| 12. source hashes | `09-source-hashes.json` |
| 13. passage correspondence | `10-downstream-gate-status.json` (`NOT_EXECUTED`) |
| 14. evaluator-B access audit | `11-evaluator-b-access-audit.md` |
| 15. evaluator-B implementation identity | `11-evaluator-b-access-audit.md` (`NOT_CREATED`) |
| 16. evaluator A/B cross-check | `10-downstream-gate-status.json` (`NOT_EXECUTED`) |
| 17. evaluator disagreement record | `10-downstream-gate-status.json` (`NOT_EXECUTED`) |
| 18. adjudicator A frozen record | `10-downstream-gate-status.json` (`NOT_CREATED`) |
| 19. adjudicator B frozen record | `10-downstream-gate-status.json` (`NOT_CREATED`) |
| 20. adjudication comparison | `10-downstream-gate-status.json` (`NOT_EXECUTED`) |
| 21. published-qrel comparison | `10-downstream-gate-status.json` (`NOT_EXECUTED`) |
| 22. segmentation/gold stability | `10-downstream-gate-status.json` (`NOT_EXECUTED`) |
| 23. corpus-authoring influence audit | `10-downstream-gate-status.json` (scientific audit `NOT_EXECUTED`; partial structural state preserved) |
| 24. deviations | `22-deviations.md` |
| 25. terminal methodology decision | `23-terminal-methodology-decision.md` |
| 26. machine-readable receipt | `24-receipt.json` |

Additional explicit-alternative record: `21-alternative-explanations.md`.

Research-only acquisition harnesses:

- `research/external_corpus_pilot0a_mechanical_cleanroom/acquire_sources.py`
- `research/external_corpus_pilot0a_mechanical_cleanroom/freshstack_failsoft.py`
- `.github/workflows/external-corpus-pilot0a-source-only-acquisition.yml`

No scientific gold, evaluator-B implementation, adjudicator judgment artifact, qrel comparison, passage stability result, retrieval output, or candidate-retriever execution is present in this record set.
