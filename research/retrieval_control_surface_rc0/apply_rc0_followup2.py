"""Lint-only cleanup identified by hosted run 33275378236.

The full behavioral suite was already green (207 passed, 5 skipped). These
asserted replacements address only Ruff import/line-length findings and remove
the import made obsolete by replacing the semantic rejection test.
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
    "src/evidence_bundler/models/retrieval.py",
    "from pathlib import Path\nimport re\nfrom typing import Literal, Self\n",
    "import re\nfrom pathlib import Path\nfrom typing import Literal, Self\n",
)
replace_once(
    "src/evidence_bundler/models/retrieval.py",
    '        if self.require_immutable_model_revisions and self.retrieval_method in {"semantic", "hybrid"}:\n',
    '        if (\n            self.require_immutable_model_revisions\n            and self.retrieval_method in {"semantic", "hybrid"}\n        ):\n',
)
replace_once(
    "src/evidence_bundler/contracts/writer.py",
    '        f"- Semantic model revision: `{report.retrieval_config.embedding_model_revision or \'unpinned\'}`",\n',
    '        (\n            "- Semantic model revision: "\n            f"`{report.retrieval_config.embedding_model_revision or \'unpinned\'}`"\n        ),\n',
)
replace_once(
    "tests/test_bundle_writer.py",
    "    BundleWriterError,\n",
    "",
)
replace_once(
    "tests/test_retrieval_control_surface_rc0.py",
    "    assert [chunk.chunk_id for chunk in default_chunks] != [chunk.chunk_id for chunk in mutated_chunks]\n",
    "    assert [chunk.chunk_id for chunk in default_chunks] != [\n        chunk.chunk_id for chunk in mutated_chunks\n    ]\n",
)

print("RC0 lint-only follow-up patch staged successfully")
