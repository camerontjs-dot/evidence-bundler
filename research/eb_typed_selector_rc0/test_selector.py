from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("selector.py")
spec = importlib.util.spec_from_file_location("eb_typed_selector_rc0_selector", MODULE_PATH)
assert spec and spec.loader
selector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = selector
spec.loader.exec_module(selector)


def candidate(evidence_id, text, rank, bm25, semantic, metadata=None):
    return {
        "evidence_id": evidence_id,
        "text": text,
        "rank": rank,
        "bm25_score": bm25,
        "semantic_score": semantic,
        "metadata": metadata or {},
    }


def hard_negative_lane():
    return {
        "proposition_id": "DEV_HARD_NEG",
        "proposition_text": "Lumen Filter removal in the 5 micron test was 93 percent.",
        "claim_profile": {
            "concepts": [
                {
                    "name": "measured_result",
                    "terms": ["measured", "result", "efficiency"],
                    "weight": 3.0,
                },
                {"name": "target", "terms": ["lumen filter"], "weight": 1.0},
            ]
        },
        "candidates": [
            candidate(
                "D1",
                "Lumen Filter 5 micron protocol revision used 93 percent humidity.",
                1,
                10.0,
                0.97,
            ),
            candidate(
                "D2",
                "Lumen Filter 5 micron setup fixture was checked at 93 percent.",
                2,
                9.5,
                0.96,
            ),
            candidate(
                "D3",
                "Lumen Filter protocol notes list 93 percent for setup use.",
                3,
                9.0,
                0.95,
            ),
            candidate(
                "KEEP",
                "Lumen Filter measured efficiency result was 93 percent.",
                4,
                8.0,
                0.90,
            ),
        ],
    }


def long_context_lane():
    prefix = " ".join(["Calibration context"] * 80)
    return {
        "proposition_id": "DEV_LONG_CONTEXT",
        "proposition_text": "Alpha exceeded Beta by 4 units.",
        "claim_profile": {
            "concepts": [
                {
                    "name": "comparison",
                    "terms": ["alpha", "beta", "4 units"],
                    "weight": 2.0,
                }
            ]
        },
        "candidates": [
            candidate("D1", "Alpha and Beta calibration context was reviewed.", 1, 10.0, 0.91),
            candidate("D2", "Alpha calibration exceeded a prior setup threshold.", 2, 9.0, 0.90),
            candidate("D3", "Beta calibration context differed by four setup units.", 3, 8.5, 0.89),
            candidate("KEEP", prefix + " Alpha exceeded Beta by 4 units.", 7, 4.0, 0.82),
        ],
    }


def evidence_posture_lane():
    return {
        "proposition_id": "DEV_POSTURE",
        "proposition_text": "Alpha exceeded Beta by 4 units.",
        "claim_profile": {
            "requires_direct_evidence": True,
            "concepts": [
                {
                    "name": "comparison",
                    "terms": ["alpha", "beta", "4 units"],
                    "weight": 2.0,
                }
            ],
        },
        "candidates": [
            candidate("D1", '"Alpha exceeded Beta by 4 units" was a rejected hypothesis.', 1, 10.0, 0.99),
            candidate("D2", 'The draft claim "Alpha exceeded Beta by 4 units" was unverified.', 2, 9.8, 0.99),
            candidate("D3", "Alpha exceeded Beta by 4 units appeared in a hypothetical scenario.", 3, 9.5, 0.98),
            candidate("KEEP", "Alpha exceeded Beta by 4 units.", 7, 4.0, 0.90),
        ],
    }


def test_typed_selector_can_rescue_hard_negative_when_semantic_only_does_not():
    result = selector.run_lane(hard_negative_lane())
    assert "KEEP" not in result["arms"]["semantic_top3"]
    assert "KEEP" in result["arms"]["typed_top3"]


def test_local_span_signal_can_rescue_long_context_candidate():
    result = selector.run_lane(long_context_lane())
    keep = next(row for row in result["characterization"] if row["evidence_id"] == "KEEP")
    assert keep["signals"]["local_span_recall"] == 1.0
    assert "KEEP" in result["arms"]["typed_top3"]


def test_evidence_posture_is_inspectable_and_discriminating():
    result = selector.run_lane(evidence_posture_lane())
    by_id = {row["evidence_id"]: row for row in result["characterization"]}
    assert by_id["D1"]["signals"]["evidence_posture"] == "non_direct:rejected"
    assert by_id["D2"]["signals"]["evidence_posture"] == "non_direct:unverified"
    assert by_id["D3"]["signals"]["evidence_posture"] == "non_direct:hypothetical"
    assert by_id["KEEP"]["signals"]["evidence_posture"] == "direct_or_unmarked_assertion"
    assert "KEEP" in result["arms"]["typed_top3"]
    assert "KEEP" not in result["arms"]["typed_without_evidence_posture"]


def test_explicit_non_result_is_not_treated_as_direct_evidence():
    label, value = selector.evidence_posture(
        "The 93 percent mark was not removal efficiency."
    )
    assert label == "non_direct:explicit_non_result"
    assert value == 0.0


def test_unknown_is_preserved_not_silently_zeroed():
    lane = hard_negative_lane()
    lane["claim_profile"] = {}
    lane["candidates"][0]["semantic_score"] = None
    result = selector.run_lane(lane)
    row = result["characterization"][0]
    assert row["signals"]["semantic_relevance"] is None
    assert row["signals"]["profile_compatibility"] is None
    assert row["signals"]["direct_evidence_match"] is None
    assert "semantic_score" in row["unknowns"]
    assert "profile_compatibility" in row["unknowns"]


def test_input_order_permutation_does_not_change_selection():
    lane = hard_negative_lane()
    result_a = selector.run_lane(lane)
    lane_b = copy.deepcopy(lane)
    lane_b["candidates"] = list(reversed(lane_b["candidates"]))
    result_b = selector.run_lane(lane_b)
    assert result_a["arms"] == result_b["arms"]


def test_selector_never_exceeds_budget_or_duplicates():
    result = selector.run_lane(evidence_posture_lane())
    for selected in result["arms"].values():
        assert len(selected) <= 3
        assert len(selected) == len(set(selected))


def test_profile_signal_has_decision_discrimination_on_hard_negative_control():
    result = selector.run_lane(hard_negative_lane())
    assert "KEEP" in result["arms"]["typed_top3"]
    assert "KEEP" not in result["arms"]["typed_without_profile"]
