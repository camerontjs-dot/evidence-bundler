from __future__ import annotations

import copy
import unittest

from selector import (
    SelectorInputError,
    candidate_specialty_forms,
    select,
)


def candidate(
    candidate_id: str,
    rank: int,
    score: float,
    text: str,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "rank": rank,
        "text": text,
        "semantic_score": score,
    }


class GateSpecialtySelectorRC0Tests(unittest.TestCase):
    def test_no_specialty_is_exact_semantic_noop(self) -> None:
        payload = {
            "claim_id": "c1",
            "expected_evidence_forms": ["document_text", "measurement"],
            "candidates": [
                candidate("a", 1, 0.99, "plain report"),
                candidate("b", 2, 0.98, "audit event record"),
                candidate("c", 3, 0.97, "registry certificate"),
                candidate("d", 4, 0.96, "policy declaration"),
            ],
        }
        result = select(payload)
        self.assertEqual(result["action"], "NO_SPECIALTY_NOOP")
        self.assertEqual(result["selected_candidate_ids"], ["a", "b", "c"])

    def test_correct_specialty_can_rescue_bounded_candidate(self) -> None:
        payload = {
            "claim_id": "c2",
            "expected_evidence_forms": ["document_text", "event_record"],
            "candidates": [
                candidate("a", 1, 0.99, "plain narrative"),
                candidate("b", 2, 0.98, "plain narrative"),
                candidate("c", 3, 0.97, "plain narrative"),
                candidate("d", 4, 0.965, "incident event record"),
            ],
        }
        result = select(payload)
        self.assertEqual(result["action"], "SPECIALTY_REPAIR")
        self.assertEqual(set(result["selected_candidate_ids"]), {"a", "b", "d"})
        self.assertEqual(result["challenger_candidate_id"], "d")
        self.assertEqual(result["victim_candidate_id"], "c")

    def test_wrong_specialty_does_not_match(self) -> None:
        payload = {
            "claim_id": "c3",
            "expected_evidence_forms": ["authoritative_declaration"],
            "candidates": [
                candidate("a", 1, 0.99, "plain narrative"),
                candidate("b", 2, 0.98, "plain narrative"),
                candidate("c", 3, 0.97, "plain narrative"),
                candidate("d", 4, 0.965, "incident event record"),
            ],
        }
        result = select(payload)
        self.assertEqual(result["action"], "SPECIALTY_NO_CHANGE")
        self.assertEqual(result["selected_candidate_ids"], ["a", "b", "c"])

    def test_semantic_loss_cap_blocks_large_drop(self) -> None:
        payload = {
            "claim_id": "c4",
            "expected_evidence_forms": ["registry_entry"],
            "candidates": [
                candidate("a", 1, 0.99, "plain narrative"),
                candidate("b", 2, 0.98, "plain narrative"),
                candidate("c", 3, 0.97, "plain narrative"),
                candidate("d", 4, 0.80, "registry certificate"),
            ],
        }
        result = select(payload)
        self.assertEqual(result["action"], "SPECIALTY_NO_CHANGE")
        self.assertEqual(result["selected_candidate_ids"], ["a", "b", "c"])

    def test_input_order_permutation_is_invariant(self) -> None:
        candidates = [
            candidate("a", 1, 0.99, "plain narrative"),
            candidate("b", 2, 0.98, "plain narrative"),
            candidate("c", 3, 0.97, "plain narrative"),
            candidate("d", 4, 0.965, "policy declaration"),
        ]
        first = select(
            {
                "claim_id": "c5",
                "expected_evidence_forms": ["authoritative_declaration"],
                "candidates": candidates,
            }
        )
        second = select(
            {
                "claim_id": "c5",
                "expected_evidence_forms": ["authoritative_declaration"],
                "candidates": list(reversed(candidates)),
            }
        )
        self.assertEqual(
            first["selected_candidate_ids"],
            second["selected_candidate_ids"],
        )

    def test_replay_is_exact(self) -> None:
        payload = {
            "claim_id": "c6",
            "expected_evidence_forms": ["registry_entry"],
            "candidates": [
                candidate("a", 1, 0.99, "plain narrative"),
                candidate("b", 2, 0.98, "plain narrative"),
                candidate("c", 3, 0.97, "plain narrative"),
                candidate("d", 4, 0.965, "registry certificate"),
            ],
        }
        self.assertEqual(select(copy.deepcopy(payload)), select(copy.deepcopy(payload)))

    def test_classifier_exposes_only_supported_specialties(self) -> None:
        self.assertEqual(
            candidate_specialty_forms(
                "The policy report states that the registry recorded an incident event."
            ),
            frozenset(
                {
                    "authoritative_declaration",
                    "registry_entry",
                    "event_record",
                }
            ),
        )

    def test_duplicate_candidate_ids_are_rejected(self) -> None:
        payload = {
            "claim_id": "c7",
            "expected_evidence_forms": ["event_record"],
            "candidates": [
                candidate("a", 1, 0.99, "plain"),
                candidate("a", 2, 0.98, "plain"),
                candidate("c", 3, 0.97, "plain"),
            ],
        }
        with self.assertRaises(SelectorInputError):
            select(payload)


if __name__ == "__main__":
    unittest.main()
