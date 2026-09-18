from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from shadow_carrier import (
    FORBIDDEN_INSTRUCTION_KEYS,
    ShadowCarrierError,
    build_shadow_carrier,
    registry_field_ids,
    rotated_wrong_substitutions,
    sha256_json,
    validate_registry,
    verify_shadow_carrier,
)

ROOT = Path(__file__).resolve().parent
REGISTRY_PATH = ROOT / "SHADOW-FIELD-REGISTRY.json"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def record(value: object, *, state: str = "known") -> dict:
    return {
        "state": state,
        "value": value,
        "basis": {"kind": "unit_test", "source": "frozen_fixture"},
    }


def packet(case_id: str, fields: dict[str, dict]) -> dict:
    return {
        "schema": "eb-gate-shadow-observation-packet-v0",
        "case_id": case_id,
        "upstream_identity": {
            "producer": "unit-test",
            "artifact_sha256": "sha256:" + ("a" * 64),
        },
        "fields": fields,
    }


class ShadowCarrierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry()
        self.field_ids = registry_field_ids(self.registry)
        self.assertEqual(len(self.field_ids), 92)
        self.sample_fields = self.field_ids[:6]
        self.packet = packet(
            "CASE-001",
            {
                field_id: record({"field_id": field_id, "case": "CASE-001"})
                for field_id in self.sample_fields
            },
        )

    def test_registry_is_noncausal_and_unique(self) -> None:
        normalized = validate_registry(self.registry)
        ids = [row["field_id"] for row in normalized["entries"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 92)
        self.assertTrue(
            all(
                row["eb_consumption_state"]
                in {"VISIBLE_SHADOW", "PRESSURE_TEST_ELIGIBLE"}
                for row in normalized["entries"]
            )
        )

    def test_exact_replay(self) -> None:
        first = build_shadow_carrier(
            registry=self.registry,
            packet=self.packet,
            requested_fields=self.sample_fields,
        )
        second = build_shadow_carrier(
            registry=self.registry,
            packet=self.packet,
            requested_fields=list(reversed(self.sample_fields)),
        )
        self.assertEqual(first, second)
        verify_shadow_carrier(first)

    def test_packet_field_order_is_irrelevant(self) -> None:
        reordered = copy.deepcopy(self.packet)
        reordered["fields"] = dict(reversed(list(reordered["fields"].items())))
        first = build_shadow_carrier(
            registry=self.registry,
            packet=self.packet,
            requested_fields=self.sample_fields,
        )
        second = build_shadow_carrier(
            registry=self.registry,
            packet=reordered,
            requested_fields=self.sample_fields,
        )
        self.assertEqual(first, second)

    def test_masked_field_change_does_not_change_observations(self) -> None:
        requested = self.sample_fields[:2]
        changed = copy.deepcopy(self.packet)
        masked_field = self.sample_fields[-1]
        changed["fields"][masked_field]["value"] = {"changed": True}

        first = build_shadow_carrier(
            registry=self.registry,
            packet=self.packet,
            requested_fields=requested,
        )
        second = build_shadow_carrier(
            registry=self.registry,
            packet=changed,
            requested_fields=requested,
        )
        self.assertEqual(first["observations"], second["observations"])
        self.assertEqual(first["observations_sha256"], second["observations_sha256"])
        self.assertNotEqual(first["input_packet_sha256"], second["input_packet_sha256"])
        self.assertNotEqual(first["output_sha256"], second["output_sha256"])

    def test_unknown_is_preserved_without_invention(self) -> None:
        field_id = self.sample_fields[0]
        unknown_packet = packet(
            "CASE-UNKNOWN",
            {
                field_id: {
                    "state": "unknown",
                    "value": None,
                    "basis": {"kind": "unit_test", "reason": "not_observed"},
                }
            },
        )
        result = build_shadow_carrier(
            registry=self.registry,
            packet=unknown_packet,
            requested_fields=[field_id, self.sample_fields[1]],
        )
        self.assertEqual(result["observations"][field_id]["state"], "unknown")
        self.assertIsNone(result["observations"][field_id]["value"])
        self.assertEqual(
            result["mask"]["missing_requested_fields"],
            [self.sample_fields[1]],
        )

    def test_duplicate_mask_is_rejected(self) -> None:
        field_id = self.sample_fields[0]
        with self.assertRaisesRegex(ShadowCarrierError, "duplicates"):
            build_shadow_carrier(
                registry=self.registry,
                packet=self.packet,
                requested_fields=[field_id, field_id],
            )

    def test_unregistered_field_is_rejected(self) -> None:
        bad = copy.deepcopy(self.packet)
        bad["fields"]["claim.not_registered"] = record("x")
        with self.assertRaisesRegex(ShadowCarrierError, "unregistered field"):
            build_shadow_carrier(
                registry=self.registry,
                packet=bad,
                requested_fields=self.sample_fields,
            )

    def test_causal_registry_state_is_rejected(self) -> None:
        bad = copy.deepcopy(self.registry)
        bad["entries"][0]["eb_consumption_state"] = "QUALIFIED_EB_HINT"
        with self.assertRaisesRegex(ShadowCarrierError, "causal or unsupported"):
            validate_registry(bad)

    def test_every_forbidden_instruction_key_is_rejected(self) -> None:
        field_id = self.sample_fields[0]
        for forbidden_key in sorted(FORBIDDEN_INSTRUCTION_KEYS):
            with self.subTest(forbidden_key=forbidden_key):
                bad = packet(
                    "CASE-BAD",
                    {
                        field_id: record(
                            {
                                "descriptive": "still-shadow",
                                forbidden_key: "instruction",
                            }
                        )
                    },
                )
                with self.assertRaisesRegex(ShadowCarrierError, "forbidden causal instruction"):
                    build_shadow_carrier(
                        registry=self.registry,
                        packet=bad,
                        requested_fields=[field_id],
                    )

    def test_rotated_wrong_hint_control_is_deterministic_and_explicit(self) -> None:
        field_id = self.sample_fields[0]
        packets = [
            packet("CASE-A", {field_id: record("A")}),
            packet("CASE-B", {field_id: record("B")}),
            packet("CASE-C", {field_id: record("C")}),
        ]
        first = rotated_wrong_substitutions(
            registry=self.registry,
            packets=packets,
            field_ids=[field_id],
        )
        second = rotated_wrong_substitutions(
            registry=self.registry,
            packets=list(reversed(packets)),
            field_ids=[field_id],
        )
        self.assertEqual(first, second)
        self.assertEqual(first["CASE-A"][0]["source_case_id"], "CASE-B")
        self.assertEqual(first["CASE-B"][0]["source_case_id"], "CASE-C")
        self.assertEqual(first["CASE-C"][0]["source_case_id"], "CASE-A")

        result = build_shadow_carrier(
            registry=self.registry,
            packet=packets[0],
            requested_fields=[field_id],
            substitutions=first["CASE-A"],
        )
        self.assertEqual(result["observations"][field_id]["value"], "B")
        self.assertEqual(result["substitutions"][0]["source_case_id"], "CASE-B")
        self.assertEqual(
            result["substitutions"][0]["record_sha256"],
            sha256_json(record("B")),
        )

    def test_substitution_for_masked_field_is_rejected(self) -> None:
        field_id = self.sample_fields[0]
        with self.assertRaisesRegex(ShadowCarrierError, "non-requested field"):
            build_shadow_carrier(
                registry=self.registry,
                packet=self.packet,
                requested_fields=[],
                substitutions=[
                    {
                        "field_id": field_id,
                        "source_case_id": "OTHER",
                        "record": record("wrong"),
                    }
                ],
            )

    def test_bound_hash_detects_tampering(self) -> None:
        result = build_shadow_carrier(
            registry=self.registry,
            packet=self.packet,
            requested_fields=self.sample_fields,
        )
        verify_shadow_carrier(result)
        tampered = copy.deepcopy(result)
        tampered["causal_effects_authorized"] = True
        with self.assertRaisesRegex(ShadowCarrierError, "hash mismatch"):
            verify_shadow_carrier(tampered)

    def test_all_boundary_flags_are_false(self) -> None:
        result = build_shadow_carrier(
            registry=self.registry,
            packet=self.packet,
            requested_fields=self.sample_fields,
        )
        self.assertFalse(result["causal_effects_authorized"])
        self.assertFalse(result["retrieval_behavior_changed"])
        self.assertFalse(result["selection_behavior_changed"])
        self.assertFalse(result["admission_behavior_changed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
