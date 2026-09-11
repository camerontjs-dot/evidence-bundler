from __future__ import annotations

import copy
import json
import math
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from evaluator import (
    EvaluationError,
    METRIC_NAMES,
    RESULT_KEYS,
    canonical_hidden_gold_bytes,
    evaluate,
    hidden_gold_sha256,
    verify_hidden_gold_commitment,
)


DEFAULT_REPO_ROOT = HERE.parents[1]
REPO_ROOT = Path(os.environ.get("EVALUATOR_FIXTURE_ROOT", DEFAULT_REPO_ROOT))
V1 = REPO_ROOT / "research" / "external_corpus_evaluator_independence_v1"
V2 = REPO_ROOT / "research" / "external_corpus_evaluator_independence_v2"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def baseline():
    return (
        load_json(V1 / "dummy_manifest.json"),
        load_json(V1 / "revealed_dummy_gold.json"),
        load_json(V1 / "dummy_run.json"),
    )


def scope_fixture():
    return (
        load_json(V2 / "ndcg_scope_manifest.json"),
        load_json(V2 / "ndcg_scope_gold.json"),
        load_json(V2 / "ndcg_scope_run.json"),
    )


def assert_invalid(testcase: unittest.TestCase, manifest, gold, run):
    with testcase.assertRaises(EvaluationError):
        evaluate(manifest, gold, run)


def consistently_rename(manifest, gold, run):
    manifest = copy.deepcopy(manifest)
    gold = copy.deepcopy(gold)
    run = copy.deepcopy(run)
    qmap = {row["query_id"]: f"query::{index}" for index, row in enumerate(manifest["queries"], start=1)}
    smap = {row["source_id"]: f"source::{index}" for index, row in enumerate(manifest["sources"], start=1)}
    pmap = {row["passage_id"]: f"passage::{index}" for index, row in enumerate(manifest["passages"], start=1)}

    for row in manifest["queries"]:
        row["query_id"] = qmap[row["query_id"]]
    for row in manifest["sources"]:
        row["source_id"] = smap[row["source_id"]]
    for row in manifest["passages"]:
        row["passage_id"] = pmap[row["passage_id"]]
        row["source_id"] = smap[row["source_id"]]

    for query in gold["queries"]:
        query["query_id"] = qmap[query["query_id"]]
        for judgment in query["judgments"]:
            judgment["passage_id"] = pmap[judgment["passage_id"]]
        for group_index, group in enumerate(query["groups"], start=1):
            group["group_id"] = f"group::{query['query_id']}::{group_index}"
            group["passage_ids"] = [pmap[pid] for pid in group["passage_ids"]]

    for query in run["queries"]:
        query["query_id"] = qmap[query["query_id"]]
        for hit in query["hits"]:
            hit["passage_id"] = pmap[hit["passage_id"]]
    return manifest, gold, run, qmap


class ExternalCorpusEvaluatorV04FreshTests(unittest.TestCase):
    def test_valid_baseline_dummy_evaluation(self):
        manifest, gold, run = baseline()
        result = evaluate(manifest, gold, run)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["k"], 3)
        self.assertEqual(result["metric_interpretation"], "point_estimate")
        self.assertEqual(result["per_query"]["q1"]["hit_at_k"], 1)
        self.assertEqual(result["per_query"]["q1"]["evidence_recall_at_k"], 1.0)
        self.assertEqual(result["per_query"]["q1"]["counterevidence_recall_at_k"], 0.0)
        self.assertEqual(result["per_query"]["q1"]["joint_group_coverage_at_k"], 0.5)
        self.assertEqual(result["per_query"]["q2"]["joint_group_coverage_at_k"], 1.0)
        expected_q1_ndcg = (
            7.0 + 1.0 / math.log2(3)
        ) / (
            7.0 + 1.0 / math.log2(3) + 1.0 / math.log2(4)
        )
        self.assertAlmostEqual(result["per_query"]["q1"]["ndcg_at_k"], expected_q1_ndcg)
        self.assertIsNone(result["per_query"]["q2"]["ndcg_at_k"])
        self.assertAlmostEqual(result["aggregate"]["ndcg_at_k"], expected_q1_ndcg)

    def test_query_local_ndcg_discriminator(self):
        manifest, gold, run = scope_fixture()
        result = evaluate(manifest, gold, run)
        self.assertTrue(result["ndcg_eligible_by_query"]["q_clean"])
        self.assertFalse(result["ndcg_eligible_by_query"]["q_unknown"])
        self.assertIsNotNone(result["per_query"]["q_clean"]["ndcg_at_k"])
        self.assertIsNone(result["per_query"]["q_unknown"]["ndcg_at_k"])
        self.assertEqual(result["aggregate"]["ndcg_at_k"], result["per_query"]["q_clean"]["ndcg_at_k"])

    def test_missing_required_identity_when_all_three_omit_it(self):
        manifest, gold, run = baseline()
        for artifact in (manifest, gold, run):
            del artifact["benchmark_sha256"]
        assert_invalid(self, manifest, gold, run)

    def test_identity_mismatch(self):
        manifest, gold, run = baseline()
        run["corpus_sha256"] = "not-the-same"
        assert_invalid(self, manifest, gold, run)

    def test_valid_representation_identity_without_locator(self):
        manifest, gold, run = baseline()
        passage = manifest["passages"][0]
        del passage["locator"]
        passage["representation_identity"] = "dummy-representation-v1"
        result = evaluate(manifest, gold, run)
        self.assertEqual(result["status"], "ok")

    def test_representation_aliases_do_not_satisfy_contract(self):
        aliases = ("representation_id", "representation_sha256", "representation")
        for alias in aliases:
            with self.subTest(alias=alias):
                manifest, gold, run = baseline()
                passage = manifest["passages"][0]
                del passage["locator"]
                passage[alias] = "alias-value"
                assert_invalid(self, manifest, gold, run)

    def test_unknown_degree_with_resolved_semantic_role_rejected(self):
        manifest, gold, run = baseline()
        unknown = next(row for row in gold["queries"][1]["judgments"] if row["relevance_degree"] == "UNKNOWN")
        unknown["role"] = "SUPPORT"
        assert_invalid(self, manifest, gold, run)

    def test_resolved_relevance_with_unknown_role_accepted(self):
        manifest, gold, run = baseline()
        resolved = gold["queries"][0]["judgments"][0]
        resolved["role"] = "UNKNOWN"
        self.assertEqual(evaluate(manifest, gold, run)["status"], "ok")

    def test_group_id_may_repeat_across_queries(self):
        manifest, gold, run = baseline()
        gold["queries"][1]["groups"][0]["group_id"] = gold["queries"][0]["groups"][0]["group_id"]
        self.assertEqual(evaluate(manifest, gold, run)["status"], "ok")

    def test_duplicate_group_id_within_query_rejected(self):
        manifest, gold, run = baseline()
        duplicate = copy.deepcopy(gold["queries"][0]["groups"][0])
        gold["queries"][0]["groups"].append(duplicate)
        assert_invalid(self, manifest, gold, run)

    def test_missing_judgments_rejected(self):
        manifest, gold, run = baseline()
        del gold["queries"][0]["judgments"]
        assert_invalid(self, manifest, gold, run)

    def test_missing_groups_rejected(self):
        manifest, gold, run = baseline()
        del gold["queries"][0]["groups"]
        assert_invalid(self, manifest, gold, run)

    def test_explicit_empty_judgments_and_groups_are_valid(self):
        manifest, gold, run = baseline()
        gold["queries"][0]["judgments"] = []
        gold["queries"][0]["groups"] = []
        result = evaluate(manifest, gold, run)
        self.assertIsNone(result["per_query"]["q1"]["hit_at_k"])
        self.assertIsNone(result["per_query"]["q1"]["evidence_recall_at_k"])
        self.assertIsNone(result["per_query"]["q1"]["counterevidence_recall_at_k"])
        self.assertIsNone(result["per_query"]["q1"]["joint_group_coverage_at_k"])
        self.assertEqual(result["per_query"]["q1"]["judgment_coverage_at_k"], 0.0)
        self.assertEqual(result["per_query"]["q1"]["resolved_judgment_coverage_at_k"], 0.0)

    def test_malformed_ranks_rejected(self):
        mutations = []
        manifest, gold, run = baseline()
        run["queries"][0]["hits"][0]["rank"] = 0
        mutations.append((manifest, gold, run))
        manifest, gold, run = baseline()
        run["queries"][0]["hits"][1]["rank"] = 3
        mutations.append((manifest, gold, run))
        manifest, gold, run = baseline()
        run["queries"][0]["hits"][1]["rank"] = 1
        mutations.append((manifest, gold, run))
        manifest, gold, run = baseline()
        run["queries"][0]["hits"][1]["rank"] = 2.0
        mutations.append((manifest, gold, run))
        for case in mutations:
            with self.subTest():
                assert_invalid(self, *case)

    def test_duplicate_ranked_passage_ids_rejected(self):
        manifest, gold, run = baseline()
        run["queries"][0]["hits"][1]["passage_id"] = run["queries"][0]["hits"][0]["passage_id"]
        assert_invalid(self, manifest, gold, run)

    def test_unknown_passage_and_source_identities_rejected(self):
        manifest, gold, run = baseline()
        run["queries"][0]["hits"][0]["passage_id"] = "missing-passage"
        assert_invalid(self, manifest, gold, run)

        manifest, gold, run = baseline()
        manifest["passages"][0]["source_id"] = "missing-source"
        assert_invalid(self, manifest, gold, run)

    def test_k_overflow_rejected(self):
        manifest, gold, run = baseline()
        run["k"] = 2
        assert_invalid(self, manifest, gold, run)

    def test_support_counterevidence_role_sensitivity(self):
        manifest, gold, run = baseline()
        before = evaluate(manifest, gold, run)
        p3 = next(row for row in gold["queries"][0]["judgments"] if row["passage_id"] == "p3")
        p3["role"] = "SUPPORT"
        after = evaluate(manifest, gold, run)
        self.assertNotEqual(
            before["per_query"]["q1"]["evidence_recall_at_k"],
            after["per_query"]["q1"]["evidence_recall_at_k"],
        )
        self.assertNotEqual(
            before["per_query"]["q1"]["counterevidence_recall_at_k"],
            after["per_query"]["q1"]["counterevidence_recall_at_k"],
        )

    def test_missing_decisive_support_evidence_changes_metrics(self):
        manifest, gold, run = baseline()
        before = evaluate(manifest, gold, run)
        run["queries"][0]["hits"] = [
            {"rank": 1, "passage_id": "p4"},
            {"rank": 2, "passage_id": "p2"},
            {"rank": 3, "passage_id": "p6"},
        ]
        after = evaluate(manifest, gold, run)
        self.assertNotEqual(
            before["per_query"]["q1"]["evidence_recall_at_k"],
            after["per_query"]["q1"]["evidence_recall_at_k"],
        )
        self.assertNotEqual(
            before["per_query"]["q1"]["ndcg_at_k"],
            after["per_query"]["q1"]["ndcg_at_k"],
        )

    def test_counterevidence_presence_sensitivity(self):
        manifest, gold, run = baseline()
        before = evaluate(manifest, gold, run)
        run["queries"][1]["hits"] = [
            {"rank": 1, "passage_id": "p1"},
            {"rank": 2, "passage_id": "p5"},
            {"rank": 3, "passage_id": "p3"},
        ]
        after = evaluate(manifest, gold, run)
        self.assertNotEqual(
            before["per_query"]["q2"]["counterevidence_recall_at_k"],
            after["per_query"]["q2"]["counterevidence_recall_at_k"],
        )

    def test_jointly_required_group_member_sensitivity(self):
        manifest, gold, run = baseline()
        before = evaluate(manifest, gold, run)
        run["queries"][1]["hits"] = [
            {"rank": 1, "passage_id": "p4"},
            {"rank": 2, "passage_id": "p6"},
            {"rank": 3, "passage_id": "p3"},
        ]
        after = evaluate(manifest, gold, run)
        self.assertEqual(before["per_query"]["q2"]["joint_group_coverage_at_k"], 1.0)
        self.assertEqual(after["per_query"]["q2"]["joint_group_coverage_at_k"], 0.0)

    def test_relevant_item_crossing_cutoff_changes_metrics(self):
        manifest, gold, run = baseline()
        run["k"] = 2
        for query in run["queries"]:
            query["hits"] = query["hits"][:2]
        without_p3 = evaluate(manifest, gold, run)
        run["queries"][0]["hits"] = [
            {"rank": 1, "passage_id": "p1"},
            {"rank": 2, "passage_id": "p3"},
        ]
        with_p3 = evaluate(manifest, gold, run)
        self.assertNotEqual(
            without_p3["per_query"]["q1"]["counterevidence_recall_at_k"],
            with_p3["per_query"]["q1"]["counterevidence_recall_at_k"],
        )
        self.assertNotEqual(
            without_p3["per_query"]["q1"]["joint_group_coverage_at_k"],
            with_p3["per_query"]["q1"]["joint_group_coverage_at_k"],
        )

    def test_serialization_order_invariance(self):
        manifest, gold, run = baseline()
        before = evaluate(manifest, gold, run)
        commitment_before = hidden_gold_sha256(gold)

        manifest["queries"].reverse()
        manifest["sources"].reverse()
        manifest["passages"].reverse()
        gold["queries"].reverse()
        for query in gold["queries"]:
            query["judgments"].reverse()
            query["groups"].reverse()
            for group in query["groups"]:
                group["passage_ids"].reverse()
        run["queries"].reverse()
        for query in run["queries"]:
            query["hits"].reverse()

        after = evaluate(manifest, gold, run)
        self.assertEqual(before, after)
        self.assertEqual(commitment_before, hidden_gold_sha256(gold))

    def test_stable_id_renaming_metric_invariance(self):
        manifest, gold, run = baseline()
        before = evaluate(manifest, gold, run)
        commitment_before = hidden_gold_sha256(gold)
        renamed_manifest, renamed_gold, renamed_run, qmap = consistently_rename(manifest, gold, run)
        after = evaluate(renamed_manifest, renamed_gold, renamed_run)
        self.assertEqual(before["aggregate"], after["aggregate"])
        for old_qid, new_qid in qmap.items():
            self.assertEqual(before["per_query"][old_qid], after["per_query"][new_qid])
            self.assertEqual(
                before["ndcg_eligible_by_query"][old_qid],
                after["ndcg_eligible_by_query"][new_qid],
            )
        self.assertNotEqual(commitment_before, hidden_gold_sha256(renamed_gold))

    def test_hidden_gold_commitment_determinism_and_semantic_sensitivity(self):
        _, gold, _ = baseline()
        first_bytes = canonical_hidden_gold_bytes(gold)
        first = hidden_gold_sha256(gold)
        second = hidden_gold_sha256(copy.deepcopy(gold))
        self.assertEqual(first, second)
        self.assertTrue(verify_hidden_gold_commitment(gold, first))
        self.assertEqual(first_bytes, canonical_hidden_gold_bytes(copy.deepcopy(gold)))

        mutated = copy.deepcopy(gold)
        mutated["queries"][0]["judgments"][0]["gain"] = 4
        self.assertNotEqual(first, hidden_gold_sha256(mutated))
        self.assertFalse(verify_hidden_gold_commitment(mutated, first))

    def test_exact_successful_result_keys_and_metric_names(self):
        manifest, gold, run = baseline()
        result = evaluate(manifest, gold, run)
        self.assertEqual(tuple(result.keys()), RESULT_KEYS)
        self.assertEqual(tuple(result["aggregate"].keys()), METRIC_NAMES)
        for metrics in result["per_query"].values():
            self.assertEqual(tuple(metrics.keys()), METRIC_NAMES)
        self.assertEqual(set(result["ndcg_eligible_by_query"]), {"q1", "q2"})

    def test_partial_qrels_uses_lower_bound_and_disables_ndcg(self):
        manifest, gold, run = baseline()
        gold["qrels_mode"] = "partial"
        result = evaluate(manifest, gold, run)
        self.assertEqual(result["metric_interpretation"], "lower_bound")
        self.assertFalse(result["ndcg_eligible"])
        self.assertTrue(all(not value for value in result["ndcg_eligible_by_query"].values()))
        self.assertIsNone(result["aggregate"]["ndcg_at_k"])

    def test_empty_ranked_results_have_full_diagnostic_coverage(self):
        manifest, gold, run = baseline()
        for query in run["queries"]:
            query["hits"] = []
        result = evaluate(manifest, gold, run)
        for metrics in result["per_query"].values():
            self.assertEqual(metrics["judgment_coverage_at_k"], 1.0)
            self.assertEqual(metrics["resolved_judgment_coverage_at_k"], 1.0)

    def test_duplicate_judgment_rejected(self):
        manifest, gold, run = baseline()
        gold["queries"][0]["judgments"].append(copy.deepcopy(gold["queries"][0]["judgments"][0]))
        assert_invalid(self, manifest, gold, run)

    def test_unknown_judgment_is_judged_but_not_resolved(self):
        manifest, gold, run = baseline()
        run["queries"][1]["hits"] = [{"rank": 1, "passage_id": "p6"}]
        result = evaluate(manifest, gold, run)
        self.assertEqual(result["per_query"]["q2"]["judgment_coverage_at_k"], 1.0)
        self.assertEqual(result["per_query"]["q2"]["resolved_judgment_coverage_at_k"], 0.0)


if __name__ == "__main__":
    unittest.main()
