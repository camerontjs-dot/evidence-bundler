from __future__ import annotations

import json
from pathlib import Path

from research.retrieval_characterization_block_b_dev_rc1.runtime_runner import (
    EMBEDDING_REVISION,
    run_split,
)


class FakeEmbedder:
    def encode(self, texts: list[str], **_kwargs: object) -> list[list[float]]:
        return [[float("alpha" in text.lower()), float("beta" in text.lower()), 0.5] for text in texts]


def _write_runtime(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    passages = [
        {"source_id":"s1","passage_id":"p1","source_order":1,"passage_order":1,"text":"alpha decisive passage"},
        {"source_id":"s1","passage_id":"p2","source_order":1,"passage_order":2,"text":"hard negative beta"},
        {"source_id":"s2","passage_id":"p3","source_order":2,"passage_order":1,"text":"semantic alpha support"},
    ]
    cases = [
        {
            "case_id":"c1",
            "claim_text":"alpha claim",
            "accessible_subset_id":"subset-1",
            "runtime_config":{"maximum_passages":2},
        }
    ]
    apertures = {"subsets":[{"subset_id":"subset-1","source_ids":["s1","s2"]}]}
    (root/"passages.jsonl").write_text(
        "\n".join(json.dumps(row) for row in passages)+"\n",
        encoding="utf-8",
    )
    (root/"dev_cases.jsonl").write_text(
        "\n".join(json.dumps(row) for row in cases)+"\n",
        encoding="utf-8",
    )
    (root/"apertures.json").write_text(json.dumps(apertures)+"\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_bm25_adapter_runs_without_any_gold_directory(tmp_path: Path) -> None:
    runtime = tmp_path/"runtime"
    _write_runtime(runtime)
    output = tmp_path/"bm25.jsonl"

    receipt = run_split(
        runtime_root=runtime,
        split="dev",
        arm="bm25",
        apparatus_sha="a"*40,
        output=output,
    )

    assert output.exists()
    assert not (tmp_path/"evaluator_only").exists()
    rows = _read_jsonl(output)
    assert len(rows)==1
    assert len(rows[0]["hits"]) <= 2
    assert receipt["arm"]=="bm25"
    assert receipt["embedding_revision"] is None
    assert receipt["source_candidate_positions_budgeted"]==2


def test_semantic_and_hybrid_use_fixed_pinned_identity_and_budgets(tmp_path: Path) -> None:
    runtime = tmp_path/"runtime"
    _write_runtime(runtime)
    embedder = FakeEmbedder()

    semantic = run_split(
        runtime_root=runtime,
        split="dev",
        arm="semantic",
        apparatus_sha="b"*40,
        output=tmp_path/"semantic.jsonl",
        embedder=embedder,
    )
    hybrid = run_split(
        runtime_root=runtime,
        split="dev",
        arm="hybrid",
        apparatus_sha="b"*40,
        output=tmp_path/"hybrid.jsonl",
        embedder=embedder,
    )

    assert semantic["embedding_revision"]==EMBEDDING_REVISION
    assert hybrid["embedding_revision"]==EMBEDDING_REVISION
    assert semantic["source_candidate_positions_budgeted"]==2
    assert hybrid["source_candidate_positions_budgeted"]==4
    assert semantic["semantic_query_encodes"]==1
    assert hybrid["semantic_query_encodes"]==1


def test_bm25_source_order_reversal_preserves_ranked_identities(tmp_path: Path) -> None:
    runtime = tmp_path/"runtime"
    _write_runtime(runtime)
    canonical=tmp_path/"canonical.jsonl"
    reversed_path=tmp_path/"reversed.jsonl"

    run_split(
        runtime_root=runtime,
        split="dev",
        arm="bm25",
        apparatus_sha="c"*40,
        output=canonical,
    )
    run_split(
        runtime_root=runtime,
        split="dev",
        arm="bm25",
        apparatus_sha="c"*40,
        output=reversed_path,
        reverse_source_order=True,
    )

    a=_read_jsonl(canonical)[0]["hits"]
    b=_read_jsonl(reversed_path)[0]["hits"]
    assert [(hit["source_id"],hit["passage_id"]) for hit in a] == [
        (hit["source_id"],hit["passage_id"]) for hit in b
    ]
