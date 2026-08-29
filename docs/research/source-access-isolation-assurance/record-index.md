# Source-Access Isolation Assurance — Durable Record Index

This index maps the task's required records to their durable artifact surfaces.

| Required record | Durable surface |
|---|---|
| 1. live starting state | `pre-execution.md` → Live starting state |
| 2. authority identities | `pre-execution.md` → Authority identities |
| 3. source-access contract | `pre-execution.md` + `research/source_access_firewall/field_registry.json` |
| 4. allowed-field registries | `research/source_access_firewall/field_registry.json` |
| 5. forbidden-field registry | `research/source_access_firewall/field_registry.json` |
| 6. reader implementation identity | `terminal-receipt.json`, `runtime.json`, reader source SHA-256 |
| 7. dummy fixture manifest | `fixture-manifest.json` |
| 8. adversarial test results | `adversarial-results.json` + workflow run 33255140441 |
| 9. static assurance results | `static-assurance.json` |
| 10. runtime access-receipt schema | `research/source_access_firewall/access_receipt.schema.json` |
| 11. actual dummy execution receipts | `dummy-receipts.json` |
| 12. optional real-artifact schema-only probe | `results.md` → Optional real-artifact structural probe (`NOT EXECUTED`) |
| 13. independent review state | `results.md` → Independent review |
| 14. deviations | `results.md` → Deviations |
| 15. exposure log | `pre-execution.md` + `results.md` → Exposure state + `terminal-receipt.json` |
| 16. alternative-explanation audit | `results.md` → Alternative-explanation audit |
| 17. terminal decision | `results.md` → Terminal disposition |
| 18. machine-readable terminal receipt | `terminal-receipt.json` |

## Preserved CI lineage

- Run 1 — `33255026317`: preserved collection failure; zero behavioral tests executed.
- Run 2 — `33255061873`: first full green synthetic assurance.
- Run 3 — `33255130554`: widened research-tree static guard green.
- Run 4 — `33255140441`: final assured-code head with direct caller-bypass controls; 30/30 pytest, 14/14 dummy runner, zero static findings.

Primary machine artifact for run 4: GitHub Actions artifact `9715573013`, SHA-256 `4442034b25894a96a5c18f5626ba9f5cebb744fc9c959271db0c73b6fcdb0744`.
