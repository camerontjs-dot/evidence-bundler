# Deviation 14a — duplicate workflow trigger after sealed exposure

## What happened

The RC2 real-measurement workflow was initially configured for both the research-branch `push` event and the PR `pull_request` event. The first workflow-file commit therefore scheduled two executions against the same frozen branch state.

The canonical decisive run is:

- run: `33208065906`
- branch/head: `846ff956dfb5875b6df16a30ed3fb06bb9b96c8d`
- first raw output SHA256: `05d141abf11eddf90e6f3e1cbbb6f341a9dd495150d0a9f515784fb36722b5ae`
- first frozen evaluation SHA256: `8d7c7b22216126510989c4fb084968de8b67f83451e22ed9461c570e6ba28916`

The automatically scheduled PR-event duplicate `33208068641` also completed. Its SUT raw output and frozen evaluation were byte-identical to the canonical decisive run:

- raw SHA256: `05d141abf11eddf90e6f3e1cbbb6f341a9dd495150d0a9f515784fb36722b5ae`
- evaluation SHA256: `8d7c7b22216126510989c4fb084968de8b67f83451e22ed9461c570e6ba28916`

Later evidence-preservation commits to the still-open PR caused additional PR-event executions because the workflow path remained part of the cumulative PR diff. PR #14 was then closed before further result-record commits to prevent additional synchronization-triggered executions.

## Timing and contamination assessment

The first duplicate was scheduled before the canonical run's result was available. No apparatus, adapter, query construction, SUT, threshold, schema, benchmark, or success definition changed between the executions. No result was used to tune or repair the SUT or apparatus.

Therefore the duplicate executions violate the intended one-shot stop discipline operationally, but they do not replace, average, or retrospectively modify the first legitimate decisive measurement. The canonical disposition is based only on run `33208065906`.

## Scientific effect

**No decision-relevant effect observed.** The first duplicate reproduced the exact raw/evaluated bytes. The deviation is preserved because the workflow trigger design permitted unnecessary post-exposure repeats.

Any future sealed one-shot workflow should use one triggering surface or an explicit concurrency/cancellation guard before exposure.
