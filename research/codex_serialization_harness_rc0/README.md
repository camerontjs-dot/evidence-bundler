# Codex Serialization Harness RC0

Purpose: qualify the local Codex child-output serialization path that failed during paused Evidence Bundler RC1, using synthetic non-semantic data only.

Start with `PREREGISTRATION.md`.

Primary runner:

```bash
python3 research/codex_serialization_harness_rc0/run_harness.py
```

Local deterministic controls only:

```bash
python3 research/codex_serialization_harness_rc0/run_harness.py --self-test-only
```

The full runner creates a unique directory under `executions/` and never reuses a child output path.

Do not use this harness to resume RC1 automatically. A successful qualification is a prerequisite, not authorization.
