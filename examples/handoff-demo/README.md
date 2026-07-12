# Handoff demo

This folder contains a fictional BM25 handoff exercise for Evidence Bundler. It is synthetic by design. The input note is marked `FICTIONAL DEMO CONTENT` so the demo boundary is still visible when the file is read outside this README.

The exercise checks whether Evidence Bundler can carry source identity, passage anchors, review state, and final bundle structure through an adapter-ready handoff path. It does not measure retrieval quality, claim truth, or real-world support.

Run from the repository root:

```bash
.venv/bin/python scripts/run_phase_4_unit1_handoff_demo.py --force
```

The runner writes generated artifacts under `build/phase-4-unit1-handoff-demo/`. Those outputs are ignored because they are reproducible from the tracked fixture and runner.
