from __future__ import annotations

import json
from pathlib import Path

from research.retrieval_rerank_semantic4k_dev_rc1.runtime_runner import (
    CANDIDATE_MULTIPLIER,
    EMBEDDING_REVISION,
    RERANK_REVISION,
    run_split,
)


class FakeEmbedder:
    def encode(self, texts: list[str], **_kwargs: object) -> list[list[float]]:
        return [
            [
                float("decisive" in text.lower()),
                float("negative" in text.lower()),
                0.5,
            ]
            for text in texts
        ]


class FakeReranker:
    def predict(
        self,
        sentence_pairs: list[tuple[str, str]],
        **_kwargs: object,
    ) -> list[float]:
        return [
            10.0 if "decisive" in passage.lower() else -1.0
            for _claim, passage in sentence_pairs
        ]


def _write_runtime(root: Path) -> None:
    root.mkdir(parents=True)
    passages = [
        {
            "source_id": "s1",
            "passage_id": "p1",
            "source_order": 1,
            "passage_order": 1,
            "text": "irrelevant negative one",
        },
        {
            "source_id": "s1",
            "passage_id": "p2",
            "source_order": 1,
            "passage_order": 2,
            "text": "decisive evidence",
        },
        {
            "source_id": "s2",
            "passage_id": "p3",
            "source_order": 2,
            "passage_order": 1,
            "text": "irrelevant negative two",
        },
    ]
    case = {
        "case_id": "c1",
        "claim_text": "claim",
        "family": "R06",
        "accessible_subset_id": "subset-1",
        "runtime_config": {"maximum_passages": 1},
    }
    apertures = {
        "subsets": [
            {
                "subset_id": "subset-1",
                "source_ids": ["s1", "s2"],
            }
        ]
    }
    (root / "passages.jsonl").write_text(
        "\n".join(json.dumps(row) for row in passages) + "\n",
        encoding="utf-8",
    )
    (root / "dev_cases.jsonl").write_text(
        json.dumps(case) + "\n",
        encoding="utf-8",
    )
    (root / "apertures.json").write_text(
        json.dumps(apertures) + "\n",
        encoding="utf-8",
    )


def test_semantic_4k_rerank_is_gold_blind_and_compresses_to_k(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    output = tmp_path / "results.jsonl"
    _write_runtime(runtime)

    receipt = run_split(
        runtime_root=runtime,
        apparatus_sha="a" * 40,
        output=output,
        embedder=FakeEmbedder(),
        rerank_model=FakeReranker(),
    )

    row = json.loads(output.read_text(encoding="utf-8").strip())
    assert row["hits"][0]["passage_id"] == "p2"
    assert len(row["hits"]) == 1
    assert row["diagnostic_receipt"]["semantic_candidate_multiplier"] == 4
    assert row["diagnostic_receipt"]["semantic_candidate_requested"] == 4
    assert row["diagnostic_receipt"]["semantic_candidate_actual"] == 3
    assert row["diagnostic_receipt"]["rerank_pair_count"] == 3
    assert receipt["rerank_pair_count"] == 3
    assert receipt["embedding_revision"] == EMBEDDING_REVISION
    assert receipt["rerank_revision"] == RERANK_REVISION
    assert CANDIDATE_MULTIPLIER == 4
