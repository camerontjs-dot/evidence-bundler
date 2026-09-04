from __future__ import annotations

import inspect
import json
from pathlib import Path

from research.counterevidence_aperture_localization_dev_rc1.analyzer import analyze
from research.counterevidence_aperture_localization_dev_rc1.runtime_runner import (
    FROZEN_PREFIXES,
    run_split,
)


class FakeEmbedder:
    def encode(self, texts: list[str], **_kwargs: object) -> list[list[float]]:
        return [
            [
                float("fails" in text.lower() or "against" in text.lower()),
                float("claim" in text.lower()),
                0.5,
            ]
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
            "text": "The study fails to demonstrate the claimed effect.",
        },
        {
            "source_id": "s2",
            "passage_id": "p2",
            "source_order": 2,
            "passage_order": 1,
            "text": "The claim appears supported.",
        },
        {
            "source_id": "s3",
            "passage_id": "p3",
            "source_order": 3,
            "passage_order": 1,
            "text": "Background information with no direct relation.",
        },
        {
            "source_id": "s4",
            "passage_id": "p4",
            "source_order": 4,
            "passage_order": 1,
            "text": "Another unrelated background record.",
        },
    ]
    case = {
        "case_id": "c1",
        "claim_text": "The treatment improves outcomes",
        "family": "R02",
        "accessible_subset_id": "subset-1",
        "runtime_config": {"maximum_passages": 1},
    }
    apertures = {
        "subsets": [
            {"subset_id": "subset-1", "source_ids": ["s1", "s2", "s3", "s4"]}
        ]
    }
    gold = [
        {
            "case_id": "c1",
            "source_id": "s1",
            "passage_id": "p1",
            "decisive": True,
            "relevance_class": "decisive_counterevidence",
        },
        {
            "case_id": "c1",
            "source_id": "s2",
            "passage_id": "p2",
            "decisive": False,
            "relevance_class": "hard_negative",
        },
    ]
    (runtime / "passages.jsonl").write_text(
        "\n".join(json.dumps(row) for row in passages) + "\n",
        encoding="utf-8",
    )
    (runtime / "dev_cases.jsonl").write_text(
        json.dumps(case) + "\n", encoding="utf-8"
    )
    (runtime / "apertures.json").write_text(
        json.dumps(apertures) + "\n", encoding="utf-8"
    )
    gold_path = gold_dir / "dev_gold.jsonl"
    gold_path.write_text(
        "\n".join(json.dumps(row) for row in gold) + "\n",
        encoding="utf-8",
    )
    return runtime, gold_path


def test_runner_keeps_frozen_prefixes_and_is_gold_blind() -> None:
    source = inspect.getsource(run_split)
    assert FROZEN_PREFIXES == (
        "evidence against",
        "limitations of",
        "contradicts the claim that",
        "does not support",
        "fails to demonstrate",
    )
    assert "dev_gold" not in source
    assert "evaluator_only" not in source
    assert "sealed_gold" not in source


def test_runner_freezes_k_2k_4k_before_posthoc_gold(tmp_path: Path) -> None:
    runtime, gold_path = _write_fixture(tmp_path)
    raw_path = tmp_path / "raw.json"
    analysis_path = tmp_path / "analysis.json"

    receipt = run_split(
        runtime_root=runtime,
        apparatus_sha="a" * 40,
        output=raw_path,
        embedder=FakeEmbedder(),
    )
    assert receipt["case_count"] == 1
    assert receipt["depth_multipliers"] == [1, 2, 4]

    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    case = raw["cases"][0]
    assert [row["child_depth"] for row in case["depths"]] == [1, 2, 4]
    assert all(len(row["prefix_rankings"]) == 5 for row in case["depths"])
    assert all("fused_rrf_order" in row for row in case["depths"])
    assert all("parent_candidate_order" in row for row in case["depths"])

    summary = analyze(
        raw_path=raw_path,
        gold_path=gold_path,
        expected_raw_sha256=receipt["output_sha256"],
        output=analysis_path,
    )
    assert summary["raw_sha256_verified"] == receipt["output_sha256"]
    assert summary["decisive_counterevidence_count"] == 1
    assert summary["r02"][0]["passage_id"] == "p1"
