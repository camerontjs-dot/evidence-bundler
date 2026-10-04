# Root-generation prerequisite RC3 apparatus successor

This is a research-infrastructure successor to the frozen RC2 prerequisite apparatus.

RC2 remains preserved at PR #127 with terminal disposition BLOCKED_CUSTODY_VERIFICATION and raw checker reason `'output'`. PR #128 subsequently qualified a structured failure-classification boundary on 18 frozen synthetic mutations.

RC3 apparatus changes only the diagnostic/control path needed to consume that evidence:

- the checker returns structured `result/category/code/detail/disposition` records instead of allowing raw structural exceptions to escape;
- profile-surface failures map explicitly to `BLOCKED_PROFILE_CONFIGURATION`;
- custody failures map explicitly to `BLOCKED_CUSTODY_VERIFICATION`;
- forbidden-source exposure maps to `CONTAMINATED`;
- unexpected apparatus exceptions map to `INCONCLUSIVE`;
- the launcher consumes the structured checker result directly and no longer guesses from exception-message substrings.

The RC2 profile contract, writer task, runtime authority, endpoint, model digest, request options, response schema, aperture and attempt budgets are unchanged.

This task qualifies the corrected apparatus offline. It does not authorize a writer/model invocation.
