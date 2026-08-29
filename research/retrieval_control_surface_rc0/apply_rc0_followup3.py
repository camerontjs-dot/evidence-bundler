"""Close the remaining RC0 falsifier and keep workflow mutation out of the freeze.

Hosted run 33276331342 established 207 passed / 5 skipped, clean touched-file
Ruff, clean RC0-touched mypy, truthful CLI help, and a final push rejection only
because the Actions-authored freeze still contained a generated workflow file.

This asserted follow-up preserves the unrelated repo-wide mypy boundary, adds
the preregistered lexical-budget mutation check, and removes the generated
permanent workflow before the Actions-authored freeze commit. The bootstrap
workflow remains historical transport machinery and is not changed by the
freeze commit.
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


# Preserve the known unrelated repo-wide mypy failure boundary in the generated
# permanent workflow, even though that workflow is removed before this freeze.
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

# The preregistration explicitly requires an independent lexical-budget
# mutation check. Add a spy that demonstrates rrf_candidate_pool controls the
# lexical pre-fusion call while semantic_child_top_k remains fixed.
replace_once(
    "tests/test_retrieval_control_surface_rc0.py",
    "from evidence_bundler.retrieval.embedding_retriever import (\n",
    "from evidence_bundler.retrieval.bm25_retriever import BM25Retriever\n"
    "from evidence_bundler.retrieval.embedding_retriever import (\n",
)
replace_once(
    "tests/test_retrieval_control_surface_rc0.py",
    "\ndef test_default_control_surface_preserves_live_pre_rc0_machinery_defaults() -> None:\n",
    '''
def test_lexical_budget_mutation_changes_pre_fusion_bm25_budget_without_semantic_change(
    mixed_scaffold_run_tmp: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "evidence_bundler.contracts.writer.load_embedding_model",
        lambda *_args, **_kwargs: FakeEmbedder(),
    )
    observed_top_k: list[int] = []
    original_query = BM25Retriever.query

    def spy_query(
        self: BM25Retriever,
        query_text: str,
        *,
        top_k: int = 20,
        score_floor: float = 0.0,
    ) -> list[object]:
        observed_top_k.append(top_k)
        return original_query(self, query_text, top_k=top_k, score_floor=score_floor)

    monkeypatch.setattr(BM25Retriever, "query", spy_query)
    for lexical_budget in (1, 4):
        build_retrieval_bundle(
            mixed_scaffold_run_tmp,
            tmp_path / f"hybrid-lexical-{lexical_budget}",
            config=RetrievalConfig(
                retrieval_method="hybrid",
                top_k=10,
                rrf_candidate_pool=lexical_budget,
                semantic_child_top_k=3,
                embedding_model="fake-semantic",
            ),
        )

    claim_count = len(observed_top_k) // 2
    assert claim_count > 0
    assert observed_top_k[:claim_count] == [1] * claim_count
    assert observed_top_k[claim_count:] == [4] * claim_count


def test_default_control_surface_preserves_live_pre_rc0_machinery_defaults() -> None:
''',
)

# The Actions token has contents:write but not workflow scope. Leaving this
# generated file in the freeze diff makes GitHub reject an otherwise valid
# source/test commit. Remove it before the freeze so transport does not masquerade
# as retrieval-machinery failure.
(ROOT / ".github/workflows/research-retrieval-control-surface-rc0.yml").unlink()

print("RC0 lexical-budget and workflow-transport follow-up staged successfully")
