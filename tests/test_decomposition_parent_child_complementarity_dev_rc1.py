from __future__ import annotations

import inspect

from research.decomposition_parent_child_complementarity_dev_rc1.fixture_builder import (
    _contract_a_object,
    compute_handoff_hash,
)
from research.decomposition_parent_child_complementarity_dev_rc1.model_generator import (
    _case_prompt,
    _parse_children,
)
from research.decomposition_parent_child_complementarity_dev_rc1.runtime_runner import (
    _alloc,
    _flatten_r2,
    run,
)


def test_equal_total_budget_allocation_is_deterministic() -> None:
    assert _alloc(12, 1) == [12]
    assert _alloc(12, 2) == [6, 6]
    assert _alloc(12, 3) == [4, 4, 4]
    assert _alloc(12, 5) == [3, 3, 2, 2, 2]
    assert sum(_alloc(12, 7)) == 12


def test_model_output_parser_abstains_instead_of_inventing_children() -> None:
    children, error = _parse_children('["Alpha is required.", "Beta is prohibited."]')
    assert children == ["Alpha is required.", "Beta is prohibited."]
    assert error is None

    children, error = _parse_children("Alpha. Beta.")
    assert children == []
    assert error == "NON_JSON_OUTPUT"

    children, error = _parse_children('["Only one child."]')
    assert children == []
    assert error == "CHILD_COUNT_OUT_OF_RANGE"


def test_rc1a_generator_prompt_is_root_semantic_and_source_blind() -> None:
    case = {
        "original_claim_id": "claim-test",
        "root_proposition": {
            "proposition_id": "claim-test",
            "text": "Alpha is required and beta is prohibited.",
            "text_sha256": "sha256:" + "4" * 64,
        },
        "source_aperture_sha256": "1" * 64,
        "sources": [
            {
                "source_id": "SECRET-SOURCE-ID",
                "media_type": "text/plain; charset=utf-8",
                "content": "SOURCE-BODY-MUST-NOT-ENTER-GENERATOR-PROMPT",
                "content_sha256": "sha256:" + "5" * 64,
            }
        ],
    }
    prompt = _case_prompt(case, "D3")
    assert case["root_proposition"]["text"] in prompt
    assert "SOURCE-BODY-MUST-NOT-ENTER-GENERATOR-PROMPT" not in prompt
    assert "SECRET-SOURCE-ID" not in prompt
    assert "source bodies are intentionally not available" in prompt


def test_contract_a_treatments_preserve_root_and_source_bytes() -> None:
    case = {
        "original_claim_id": "claim-test",
        "root_proposition": {
            "proposition_id": "claim-test",
            "text": "Alpha is required and beta is prohibited.",
            "text_sha256": "sha256:" + "4" * 64,
        },
        "sources": [
            {
                "source_id": "src-1",
                "media_type": "text/plain; charset=utf-8",
                "content": "Source bytes.",
                "content_sha256": "sha256:" + "5" * 64,
            }
        ],
    }
    left = _contract_a_object(
        case=case,
        strategy="D1",
        state="declared",
        children=["Alpha is required.", "Beta is prohibited."],
    )
    right = _contract_a_object(
        case=case,
        strategy="D2",
        state="declared",
        children=[
            "Within scope, alpha is required.",
            "Within scope, beta is prohibited.",
        ],
    )
    assert left["root_proposition"] == right["root_proposition"]
    assert left["sources"] == right["sources"]
    assert left["decomposition"] != right["decomposition"]
    assert left["handoff_sha256"] == compute_handoff_hash(left)
    assert right["handoff_sha256"] == compute_handoff_hash(right)
    assert left["decomposition"]["decomposition_id"].endswith("-rc1a")
    assert right["decomposition"]["decomposition_id"].endswith("-rc1a")


def test_flattened_control_preserves_physical_set_and_removes_attribution() -> None:
    r2 = {
        "requested_candidate_positions": 12,
        "returned_before_dedupe": 4,
        "unique_candidates": 2,
        "duplicate_burden": 2,
        "source_diversity": 2,
        "hits": [
            {
                "paragraph_id": "p1",
                "source_id": "s1",
                "paragraph_index": 0,
                "text": "one",
                "best_rank": 1,
                "best_score": 0.9,
                "relationships": [
                    {
                        "proposition_id": "root",
                        "proposition_role": "root",
                        "retrieval_lane": "root_lane",
                    }
                ],
            },
            {
                "paragraph_id": "p2",
                "source_id": "s2",
                "paragraph_index": 0,
                "text": "two",
                "best_rank": 1,
                "best_score": 0.8,
                "relationships": [
                    {
                        "proposition_id": "child",
                        "proposition_role": "child",
                        "retrieval_lane": "child_lane",
                    }
                ],
            },
        ],
    }
    flat = _flatten_r2(r2)
    assert flat["same_physical_passage_ids"] == ["p1", "p2"]
    assert [hit["paragraph_id"] for hit in flat["hits"]] == ["p1", "p2"]
    assert all("relationships" not in hit for hit in flat["hits"])
    assert flat["proposition_and_lane_attribution_removed"] is True


def test_retrieval_runner_is_gold_blind() -> None:
    source = inspect.getsource(run)
    assert "dev_relevance" not in source
    assert "gold" not in source.lower()
    assert "sealed" not in source.lower()
