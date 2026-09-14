# RC1 Context-Free Execution Boundary

All semantic judgments in RC1 are information-isolation dependent and therefore context-free required.

The supervising Codex context may orchestrate mechanics but is contaminated for semantic judgment by prior project/result knowledge. It must never substitute its own labels.

Each child semantic execution must:

1. be a new `codex exec --ephemeral` context;
2. run in a fresh temporary directory containing only `BLIND_REVIEW_PACKET.json` and `OPERATIONAL_REVIEW_RUBRIC.md`;
3. use `--ignore-user-config`, `--ignore-rules`, `--skip-git-repo-check`, and read-only sandboxing;
4. be explicitly prohibited from GitHub, web, parent directories, other sets, prior references, prior results, or reviewer outputs;
5. return only the rubric JSON object;
6. preserve a JSONL trace;
7. fail closed if the trace shows any shell command other than the exact authorized `cat` of the two files.

Stage 1 and Stage 2 child contexts must be distinct. Stage 1 reference outputs must be committed and pushed before any Stage 2 child is launched.
