from __future__ import annotations

import copy
import unittest

from selector import SelectorInputError, candidate_forms, select


def payload() -> dict:
    return {
        "parent_id": "p1",
        "children": [
            {
                "child_id": "a",
                "subject": "Valve 2",
                "expected_evidence_forms": ["event_record"],
            },
            {
                "child_id": "b",
                "subject": "Valve 2",
                "expected_evidence_forms": ["registry_entry"],
            },
        ],
        "candidates": [
            {
                "candidate_id": "c1",
                "text": "Policy requires Valve 2 closure verification.",
                "semantic_scores": {"a": 0.99, "b": 0.20},
            },
            {
                "candidate_id": "c2",
                "text": "Event log recorded Valve 2 closure.",
                "semantic_scores": {"a": 0.985, "b": 0.18},
            },
            {
                "candidate_id": "c3",
                "text": "Registry entry lists Valve 3 as active.",
                "semantic_scores": {"a": 0.10, "b": 0.98},
            },
            {
                "candidate_id": "c4",
                "text": "Registry entry lists Valve 2 as active.",
                "semantic_scores": {"a": 0.11, "b": 0.975},
            },
            {
                "candidate_id": "c5",
                "text": "General narrative about Valve 2.",
                "semantic_scores": {"a": 0.97, "b": 0.30},
            },
        ],
    }


class SelectorTests(unittest.TestCase):
    def test_candidate_forms(self) -> None:
        self.assertIn(
            "event_record",
            candidate_forms("Event log recorded the inspection."),
        )
        self.assertIn(
            "registry_entry",
            candidate_forms("Registry entry lists the unit."),
        )
        self.assertIn(
            "authoritative_declaration",
            candidate_forms("Policy requires dual sign-off."),
        )
        self.assertIn(
            "measurement",
            candidate_forms("Gauge reading measured 3.1 bar."),
        )

    def test_form_then_subject_recovers_correct_rows(self) -> None:
        result = select(payload())
        self.assertEqual(
            set(result["selected_candidate_ids"]),
            {"c2", "c4", "c5"},
        )

    def test_exact_replay(self) -> None:
        first = select(copy.deepcopy(payload()))
        second = select(copy.deepcopy(payload()))
        self.assertEqual(first, second)

    def test_candidate_input_permutation_invariant(self) -> None:
        original = payload()
        reversed_payload = copy.deepcopy(original)
        reversed_payload["candidates"] = list(
            reversed(reversed_payload["candidates"])
        )
        self.assertEqual(
            select(original)["selected_candidate_ids"],
            select(reversed_payload)["selected_candidate_ids"],
        )

    def test_subject_missing_is_safe_noop_for_subject_stage(self) -> None:
        value = payload()
        for child in value["children"]:
            child["subject"] = None
        result = select(value)
        self.assertTrue(
            all(
                row["action"] in {
                    "NO_ELIGIBLE_SWAP",
                    "NO_MATCH_IMPROVEMENT",
                }
                for row in result["subject_receipt"]
            )
        )

    def test_unknown_expected_form_is_ignored(self) -> None:
        value = payload()
        value["children"][0]["expected_evidence_forms"] = [
            "document_text"
        ]
        result = select(value)
        self.assertEqual(
            result["stage_order"][-2],
            "expected_evidence_form",
        )

    def test_duplicate_candidate_rejected(self) -> None:
        value = payload()
        value["candidates"][1]["candidate_id"] = "c1"
        with self.assertRaises(SelectorInputError):
            select(value)


if __name__ == "__main__":
    unittest.main()
