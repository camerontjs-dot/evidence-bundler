from __future__ import annotations

import json
from pathlib import Path

from research.retrieval_counterevidence_pass_dev_rc1.analyzer import analyze
from research.retrieval_counterevidence_pass_dev_rc1.runtime_runner import run_split


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
    ]
    case = {
        "case_id": "c1",
        "claim_text": "The treatment improves outcomes",
        "family": "R02",
        "accessible_subset_id": "subset-1",
        "runtime_config": {"maximum_passages": 1},
    }
    apertures = {
        "subsets": [{"subset_id": "subset-1", "source_ids": ["s1", "s2"]}]
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
    (runtime / "dev_cases.jsonl").write_text(json.dumps(case) + "\n", encoding="utf-8")
    (runtime / "apertures.json").write_text(json.dumps(apertures) + "\n", encoding="utf-8")
    gold_path = gold_dir / "dev_gold.jsonl"
    gold_path.write_text(
        "\n".join(json.dumps(row) for row in gold) + "\n",
        encoding="utf-8",
    )
    return runtime, gold_path


def test_counter_runner_is_gold_blind_and_role_gate_is_observable(tmp_path: Path) -> None:
    runtime, gold_path = _write_fixture(tmp_path)
    raw_path = tmp_path / "raw.json"

    receipt = run_split(
        runtime_root=runtime,
        apparatus_sha="a" * 40,
        output=raw_path,
        embedder=FakeEmbedder(),
    )

    assert receipt["case_count"] == 1
    assert raw_path.exists()
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    row = raw["cases"][0]
    assert row["arms"]["E0_disabled"] == []
    assert row["receipt"]["counter_lexical_child_top_k"] == 1
    assert row["receipt"]["counter_semantic_child_top_k"] == 1

    result = analyze(
        runtime_root=runtime,
        gold_path=gold_path,
        raw_path=raw_path,
    )
    assert set(result["summary"]) == {"E0_disabled", "E1_gate_on", "E2_gate_off"}
    assert result["summary"]["E0_disabled"]["counterevidence_recall"] == 0.0
