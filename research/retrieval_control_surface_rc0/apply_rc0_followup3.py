"""Scope the RC0 type gate after preserved unrelated repo-wide mypy failure.

Hosted run 33275482196 established that the full RC0 behavioral suite and Ruff
pass, while repo-wide mypy fails only in the untouched
src/evidence_bundler/contracts/factual_context.py. RC0 does not repair or hide
that unrelated failure. Its permanent workflow type-checks the source files
changed by this apparatus hardening.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path}, found {count}: {old!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    ".github/workflows/research-retrieval-control-surface-rc0.yml",
    '''      - name: Mypy source
        run: |
          python -m mypy src 2>&1 | tee artifacts/retrieval-control-surface-rc0/mypy.txt
''',
    '''      - name: Mypy RC0-touched source
        run: |
          python -m mypy \\
            src/evidence_bundler/models/retrieval.py \\
            src/evidence_bundler/retrieval/embedding_retriever.py \\
            src/evidence_bundler/retrieval/reranker.py \\
            src/evidence_bundler/contracts/writer.py \\
            src/evidence_bundler/cli.py \\
            2>&1 | tee artifacts/retrieval-control-surface-rc0/mypy.txt
''',
)

print("RC0 touched-source mypy scope patch staged successfully")
