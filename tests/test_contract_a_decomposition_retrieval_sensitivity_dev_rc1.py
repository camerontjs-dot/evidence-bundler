from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.contract_a_decomposition_retrieval_sensitivity_dev_rc1 import (
    analyzer,
    runtime_runner,
)


class FakeEmbedder:
    def encode(self, texts: list[str], **_kwargs: object) -> list[list[float]]:
        return [
            [
                float("alpha" in text.lower()),
                float("beta" in text.lower()),
                float("gamma" in text.lower()),
            ]
            for text in texts
        ]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


def _fixture(root: Path) -> tuple[Path, Path]:
    benchmark = root / "benchmark"
    source = benchmark / "sources" / "s1"
    source.mkdir(parents=True)
    (source / "content.txt").write_text(
        "alpha evidence paragraph.\n\nbeta evidence paragraph.\n\ngamma distractor.",
        encoding="utf-8",
    )
    (benchmark / "aperture").mkdir(parents=True)
    (benchmark / "aperture" / "subsets.json").write_text(
        json.dumps(
            {
                "subsets": [
                    {
                        "subset_id": "full",
                        "source_ids": ["s1"],
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    cases = []
    decompositions = []
    variants = {
        "A0": [],
        "A1": [
            {"child_id": "c-a1-1", "sequence": 1, "text": "alpha"},
            {"child_id": "c-a1-2", "sequence": 2, "text": "beta"},
        ],
        "A2": [
            {"child_id": "c-a2-1", "sequence": 1, "text": "alpha evidence"},
            {"child_id": "c-a2-2", "sequence": 2, "text": "beta evidence"},
        ],
        "A3": [{"child_id": "c-a3-1", "sequence": 1, "text": "gamma"}],
        "A4": [
            {"child_id": "c-a4-1", "sequence": 1, "text": "alpha"},
            {"child_id": "c-a4-2", "sequence": 2, "text": "evidence"},
            {"child_id": "c-a4-3", "sequence": 3, "text": "beta"},
        ],
    }
    for variant_id, children in variants.items():
        case_id = f"case-{variant_id.lower()}"
        cases.append(
            {
                "case_id": case_id,
                "original_claim_id": "claim-1",
                "original_claim_text": "alpha and beta",
                "claim_text": "alpha and beta",
                "variant_id": variant_id,
                "accessible_subset_id": "full",
                "runtime_config": {"maximum_passages": 2},
            }
        )
        decompositions.append(
            {
                "decomposition_id": f"dec-{variant_id.lower()}",
                "original_claim_id": "claim-1",
                "original_claim_text": "alpha and beta",
                "variant_id": variant_id,
                "children": children,
                "preserves_parent_meaning": variant_id != "A3",
                "evaluator_only_negative_control": variant_id == "A3",
                "over_decomposition": variant_id == "A4",
            }
        )

    _write_jsonl(benchmark / "cases" / "dev_cases.jsonl", cases)
    decomposition_path = benchmark / "decompositions" / "dev_decompositions.jsonl"
    _write_jsonl(decomposition_path, decompositions)
    runtime_runner.DEV_DECOMPOSITION_SHA256 = hashlib.sha256(
        decomposition_path.read_bytes()
    ).hexdigest()

    gold = []
    for variant_id in variants:
        gold.append(
            {
                "annotation_id": f"ann-{variant_id}-a",
                "case_id": f"case-{variant_id.lower()}",
                "source_id": "s1",
                "span_text": "alpha evidence paragraph.",
                "decisive": True,
                "in_accessible_subset": True,
                "relevance_class": "decisive_support",
                "joint_group_id": None,
            }
        )
        gold.append(
            {
                "annotation_id": f"ann-{variant_id}-b",
                "case_id": f"case-{variant_id.lower()}",
                "source_id": "s1",
                "span_text": "beta evidence paragraph.",
                "decisive": True,
                "in_accessible_subset": True,
                "relevance_class": "decisive_support",
                "joint_group_id": None,
            }
        )
    gold_path = benchmark / "gold" / "dev_relevance.jsonl"
    _write_jsonl(gold_path, gold)
    analyzer.DEV_GOLD_SHA256 = hashlib.sha256(gold_path.read_bytes()).hexdigest()
    return benchmark, gold_path


def test_equal_total_budget_and_ownership_equivalence(tmp_path: Path) -> None:
    benchmark, gold_path = _fixture(tmp_path)
    raw_path = tmp_path / "raw.json"

    receipt = runtime_runner.run(
        benchmark_root=benchmark,
        apparatus_sha="a" * 40,
        output=raw_path,
        embedder=FakeEmbedder(),
    )

    assert receipt["base_claim_count"] == 1
    assert receipt["ownership_equivalence_invariants"] == 8

    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    for retriever in raw["claims"][0]["retrievers"].values():
        for variant_id in ("A1", "A2"):
            variant = retriever["variants"][variant_id]
            assert variant["equal_total_budget"]["requested_candidate_positions"] == 2
            assert variant["ownership_equivalence"]["identical"] is True

    result = analyzer.analyze(
        benchmark_root=benchmark,
        raw_path=raw_path,
        gold_path=gold_path,
    )
    assert result["ownership_equivalence"]["all_identical"] is True


def test_budget_allocator_never_exceeds_total() -> None:
    children = [
        {"sequence": index + 1, "child_id": f"c{index}", "text": "x"}
        for index in range(6)
    ]
    allocation = runtime_runner.allocate_total_budget(12, children)
    assert allocation == [2, 2, 2, 2, 2, 2]
    assert sum(allocation) == 12
