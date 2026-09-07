from __future__ import annotations

from pathlib import Path

from evidence_bundler.contracts.factual_context import ContractBFactualContext, SourceContext

from research.cal_rc0_contract_b_handoff.qualified_handoff import dedupe_source_contexts


def test_dedupe_source_contexts_only_collapses_duplicate_source_identity(tmp_path: Path) -> None:
    extension = ContractBFactualContext(
        history_complete=True,
        sources=[
            SourceContext(source_id="src-a"),
            SourceContext(source_id="src-a"),
            SourceContext(source_id="src-b"),
        ],
    )
    normalized = dedupe_source_contexts(extension)
    assert [row.source_id for row in normalized.sources] == ["src-a", "src-b"]
    assert normalized.history == extension.history
    assert normalized.passages == extension.passages
    assert normalized.claims == extension.claims
