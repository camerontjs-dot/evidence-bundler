from __future__ import annotations

import json
from pathlib import Path

from research.retrieval_candidate_pool_aperture_dev_rc1.pool_analyzer import analyze
from research.retrieval_candidate_pool_aperture_dev_rc1.pool_runner import (
    run_candidate_pools,
)


class FakeEmbedder:
    def encode(self, texts: list[str], **_kwargs: object) -> list[list[float]]:
        return [
            [float("alpha" in text.lower()), float("beta" in text.lower()), 0.5]
            for text in texts
        ]


def _write_fixture(root: Path) -> tuple[Path, Path]:
    runtime = root / "runtime"
    gold_dir = root / "evaluator_only"
    runtime.mkdir(parents=True)
    gold_dir.mkdir(parents=True)
    passages = [
        {
            "source_id": "s1",
            "passage_id": "p1",
            "source_order": 1,
            "passage_order": 1,
            "text": "alpha decisive passage",
        },
        {
            "source_id": "s1",
            "passage_id": "p2",
            "source_order": 1,
            "passage_order": 2,
            "text": "hard negative beta",
        },
        {
            "source_id": "s2",
            "passage_id": "p3",
            "source_order": 2,
            "passage_order": 1,
            "text": "semantic alpha support",
        },
    ]
    case = {
        "case_id": "c1",
        "claim_text": "alpha claim",
        "family": "R01",
        "accessible_subset_id": "subset-1",
        "runtime_config": {"maximum_passages": 1},
    }
    aperture = {"subsets": [{"subset_id": "subset-1", "source_ids": ["s1", "s2"]}]}
    gold = [
        {
            "case_id": "c1",
            "source_id": "s2",
            "passage_id": "p3",
            "decisive": True,
            "relevance_class": "decisive_support",
            "joint_group_id": None,
        },
        {
            "case_id": "c1",
            "source_id": "s1",
            "passage_id": "p2",
            "decisive": False,
            "relevance_class": "hard_negative",
            "joint_group_id": None,
        },
    ]
    (runtime / "passages.jsonl").write_text(
        "\n".join(json.dumps(row) for row in passages) + "\n",
        encoding="utf-8",
    )
    (runtime / "dev_cases.jsonl").write_text(json.dumps(case) + "\n", encoding="utf-8")
    (runtime / "apertures.json").write_text(json.dumps(aperture) + "\n", encoding="utf-8")
    gold_path = gold_dir / "dev_gold.jsonl"
    gold_path.write_text(
        "\n".join(json.dumps(row) for row in gold) + "\n",
        encoding="utf-8",
    )
    return runtime, gold_path


def test_candidate_runner_is_gold_blind_and_analyzer_is_posthoc(tmp_path: Path) -> None:
    runtime, gold_path = _write_fixture(tmp_path)
    candidates = tmp_path / "candidates.json"

    receipt = run_candidate_pools(
        runtime_root=runtime,
        apparatus_sha="a" * 40,
        output=candidates,
        embedder=FakeEmbedder(),
    )

    assert receipt["case_count"] == 1
    assert candidates.exists()

    result = analyze(
        runtime_root=runtime,
        gold_path=gold_path,
        candidate_path=candidates,
    )
    assert set(result["multipliers"]) == {"1", "2", "4"}
    assert "lexical" in result["multipliers"]["1"]["aggregate"]["pools"]
    assert "semantic" in result["multipliers"]["1"]["aggregate"]["pools"]
    assert "union" in result["multipliers"]["1"]["aggregate"]["pools"]
