import copy
import unittest

import evaluator


def make_gold():
    lanes = []
    n = 1
    for category in range(1, 11):
        for _ in range(3):
            lane_id = f"L{n:03d}"
            candidates = []
            for rank in range(1, 11):
                cid = f"{lane_id}-C{rank:02d}"
                if rank == 1 and category != 10:
                    cls = "REQUIRED"
                    req = ["core"]
                else:
                    cls = "DISTRACTOR"
                    req = []
                candidates.append({
                    "candidate_id": cid,
                    "source_id": f"{lane_id}-S{rank:02d}",
                    "rank": rank,
                    "gold_class": cls,
                    "required_group_ids": req,
                    "redundancy_group_id": None,
                    "reason_code": "SYNTHETIC",
                    "justification": "Synthetic control.",
                    "reviewer_confidence": "high",
                })
            lanes.append({
                "lane_id": lane_id,
                "category": category,
                "lane_type": "no_clear_suitable" if category == 10 else "positive",
                "claim": "Synthetic claim.",
                "candidates": candidates,
            })
            n += 1
    return {
        "schema": "synthetic",
        "candidate_pools_raw_sha256": "abc123",
        "lanes": lanes,
    }


def selections(gold, covered_count):
    positive = [l for l in gold["lanes"] if l["lane_type"] == "positive"]
    covered = {l["lane_id"] for l in positive[:covered_count]}
    rows = []
    for lane in gold["lanes"]:
        chosen = [lane["candidates"][0]["candidate_id"]] if lane["lane_id"] in covered else []
        rows.append({"lane_id": lane["lane_id"], "selected_candidate_ids": chosen})
    return rows


def replay(gold, counts):
    return {
        "schema": "synthetic-replay",
        "candidate_pools_raw_sha256": "abc123",
        "arms": {arm: selections(gold, counts[arm]) for arm in evaluator.ARM_KEYS},
    }


def all_gates():
    return {key: True for key in evaluator.REQUIRED_EXTERNAL_GATES}


BINDING = {
    "rank_only": "ARM_A",
    "semantic": "ARM_B",
    "candidate": "ARM_C",
    "weak": "ARM_D",
}


class EvaluatorTests(unittest.TestCase):
    def test_support_gate(self):
        gold = make_gold()
        r = replay(gold, {"ARM_A": 27, "ARM_B": 24, "ARM_C": 27, "ARM_D": 24})
        ev = evaluator.evaluate_replays(gold, r, copy.deepcopy(r))
        d = evaluator.assign_disposition(ev, BINDING, all_gates())
        self.assertEqual("SUPPORTED FOR PROMOTION", d["disposition"])

    def test_falsification_gate(self):
        gold = make_gold()
        r = replay(gold, {"ARM_A": 27, "ARM_B": 27, "ARM_C": 24, "ARM_D": 24})
        ev = evaluator.evaluate_replays(gold, r, copy.deepcopy(r))
        d = evaluator.assign_disposition(ev, BINDING, all_gates())
        self.assertEqual("FALSIFIED", d["disposition"])

    def test_inconclusive_gate(self):
        gold = make_gold()
        r = replay(gold, {"ARM_A": 26, "ARM_B": 25, "ARM_C": 26, "ARM_D": 24})
        ev = evaluator.evaluate_replays(gold, r, copy.deepcopy(r))
        d = evaluator.assign_disposition(ev, BINDING, all_gates())
        self.assertEqual("INCONCLUSIVE", d["disposition"])

    def test_weak_control_discrimination_blocks_support(self):
        gold = make_gold()
        r = replay(gold, {"ARM_A": 27, "ARM_B": 24, "ARM_C": 27, "ARM_D": 27})
        ev = evaluator.evaluate_replays(gold, r, copy.deepcopy(r))
        d = evaluator.assign_disposition(ev, BINDING, all_gates())
        self.assertEqual("INCONCLUSIVE", d["disposition"])
        self.assertFalse(d["support_checks"]["weak_discrimination"])

    def test_duplicate_selection_rejected(self):
        gold = make_gold()
        r = replay(gold, {a: 27 for a in evaluator.ARM_KEYS})
        cid = r["arms"]["ARM_A"][0]["selected_candidate_ids"][0]
        r["arms"]["ARM_A"][0]["selected_candidate_ids"] = [cid, cid]
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.evaluate_replays(gold, r, copy.deepcopy(r))

    def test_out_of_pool_selection_rejected(self):
        gold = make_gold()
        r = replay(gold, {a: 27 for a in evaluator.ARM_KEYS})
        r["arms"]["ARM_A"][0]["selected_candidate_ids"] = ["not-in-pool"]
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.evaluate_replays(gold, r, copy.deepcopy(r))

    def test_more_than_k_rejected(self):
        gold = make_gold()
        r = replay(gold, {a: 27 for a in evaluator.ARM_KEYS})
        lane = gold["lanes"][0]
        r["arms"]["ARM_A"][0]["selected_candidate_ids"] = [
            c["candidate_id"] for c in lane["candidates"][:4]
        ]
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.evaluate_replays(gold, r, copy.deepcopy(r))

    def test_gold_like_extra_output_fields_rejected(self):
        gold = make_gold()
        r = replay(gold, {a: 27 for a in evaluator.ARM_KEYS})
        r["arms"]["ARM_A"][0]["gold_class"] = "REQUIRED"
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.evaluate_replays(gold, r, copy.deepcopy(r))

    def test_candidate_replay_mismatch_is_blocked_without_target_owned_failure(self):
        gold = make_gold()
        r1 = replay(gold, {a: 27 for a in evaluator.ARM_KEYS})
        r2 = copy.deepcopy(r1)
        r2["arms"]["ARM_C"][0]["selected_candidate_ids"] = []
        ev = evaluator.evaluate_replays(gold, r1, r2)
        d = evaluator.assign_disposition(ev, BINDING, all_gates())
        self.assertEqual("BLOCKED_APPARATUS", d["disposition"])

    def test_target_owned_failure_can_falsify(self):
        gold = make_gold()
        r1 = replay(gold, {a: 27 for a in evaluator.ARM_KEYS})
        r2 = copy.deepcopy(r1)
        r2["arms"]["ARM_C"][0]["selected_candidate_ids"] = []
        ev = evaluator.evaluate_replays(gold, r1, r2)
        gates = all_gates()
        gates["target_owned_deterministic_system_property_pass"] = False
        d = evaluator.assign_disposition(ev, BINDING, gates)
        self.assertEqual("FALSIFIED", d["disposition"])

    def test_complementary_group_coverage_requires_all_groups(self):
        gold = make_gold()
        lane = gold["lanes"][21]  # category 8
        lane["candidates"][1]["gold_class"] = "REQUIRED"
        lane["candidates"][1]["required_group_ids"] = ["second"]
        r = replay(gold, {a: 27 for a in evaluator.ARM_KEYS})
        ev = evaluator.evaluate_replays(gold, r, copy.deepcopy(r))
        self.assertEqual(
            26,
            ev["arm_metrics"]["ARM_A"]["required_lane_coverage"]["covered_positive_lanes"],
        )

    def test_pool_hash_mismatch_rejected(self):
        gold = make_gold()
        r = replay(gold, {a: 27 for a in evaluator.ARM_KEYS})
        r["candidate_pools_raw_sha256"] = "different"
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.evaluate_replays(gold, r, copy.deepcopy(r))


if __name__ == "__main__":
    unittest.main()
