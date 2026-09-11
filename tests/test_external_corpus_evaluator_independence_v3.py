from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
V1 = ROOT / "research" / "external_corpus_evaluator_independence_v1"
V2 = ROOT / "research" / "external_corpus_evaluator_independence_v2"
V3 = ROOT / "research" / "external_corpus_evaluator_independence_v3"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"v3_{name}", V3 / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"v3_{name}"] = module
    spec.loader.exec_module(module)
    return module


A = _load("evaluator_a")
B = _load("evaluator_b")
C = _load("canonical")

MANIFEST = json.loads((V1 / "dummy_manifest.json").read_text())
RUN = json.loads((V1 / "dummy_run.json").read_text())
GOLD = json.loads((V1 / "revealed_dummy_gold.json").read_text())
SCOPE_MANIFEST = json.loads((V2 / "ndcg_scope_manifest.json").read_text())
SCOPE_GOLD = json.loads((V2 / "ndcg_scope_gold.json").read_text())
SCOPE_RUN = json.loads((V2 / "ndcg_scope_run.json").read_text())


def both(manifest=None, gold=None, run=None):
    m = copy.deepcopy(MANIFEST if manifest is None else manifest)
    g = copy.deepcopy(GOLD if gold is None else gold)
    r = copy.deepcopy(RUN if run is None else run)
    return A.evaluate(m, g, r), B.evaluate(copy.deepcopy(m), copy.deepcopy(g), copy.deepcopy(r))


def rejects(manifest=None, gold=None, run=None):
    m = copy.deepcopy(MANIFEST if manifest is None else manifest)
    g = copy.deepcopy(GOLD if gold is None else gold)
    r = copy.deepcopy(RUN if run is None else run)
    for evaluator in (A, B):
        with pytest.raises((evaluator.ContractError, ValueError)):
            evaluator.evaluate(copy.deepcopy(m), copy.deepcopy(g), copy.deepcopy(r))


def test_reference_implementations_agree_on_original_dummy_and_exact_shape():
    ra, rb = both()
    assert ra == rb
    assert set(ra) == {
        "status",
        "k",
        "qrels_mode",
        "metric_interpretation",
        "ndcg_eligible",
        "ndcg_eligible_by_query",
        "aggregate",
        "per_query",
    }
    assert ra["status"] == "ok"
    assert ra["metric_interpretation"] == "point_estimate"
    expected_metrics = {
        "hit_at_k",
        "evidence_recall_at_k",
        "counterevidence_recall_at_k",
        "ndcg_at_k",
        "joint_group_coverage_at_k",
        "judgment_coverage_at_k",
        "resolved_judgment_coverage_at_k",
    }
    assert set(ra["aggregate"]) == expected_metrics
    assert all(set(row) == expected_metrics for row in ra["per_query"].values())
    assert ra["aggregate"]["hit_at_k"] == 1.0
    assert ra["aggregate"]["evidence_recall_at_k"] == 1.0
    assert ra["aggregate"]["counterevidence_recall_at_k"] == 0.5


def test_query_local_ndcg_scope_is_preserved():
    ra, rb = both()
    assert ra == rb
    assert ra["ndcg_eligible_by_query"] == {"q1": True, "q2": False}
    assert ra["per_query"]["q1"]["ndcg_at_k"] == pytest.approx(0.938506417451168)
    assert ra["per_query"]["q2"]["ndcg_at_k"] is None
    assert ra["aggregate"]["ndcg_at_k"] == pytest.approx(0.938506417451168)


def test_minimal_ndcg_scope_discriminator():
    ra = A.evaluate(copy.deepcopy(SCOPE_MANIFEST), copy.deepcopy(SCOPE_GOLD), copy.deepcopy(SCOPE_RUN))
    rb = B.evaluate(copy.deepcopy(SCOPE_MANIFEST), copy.deepcopy(SCOPE_GOLD), copy.deepcopy(SCOPE_RUN))
    assert ra == rb
    assert ra["ndcg_eligible_by_query"] == {"q_clean": True, "q_unknown": False}
    assert ra["per_query"]["q_clean"]["ndcg_at_k"] == pytest.approx(0.7098097413968655)
    assert ra["per_query"]["q_unknown"]["ndcg_at_k"] is None


def test_partial_qrels_disable_ndcg_and_mark_lower_bound():
    gold = copy.deepcopy(GOLD)
    gold["qrels_mode"] = "partial"
    ra, rb = both(gold=gold)
    assert ra == rb
    assert ra["metric_interpretation"] == "lower_bound"
    assert ra["ndcg_eligible_by_query"] == {"q1": False, "q2": False}
    assert ra["aggregate"]["ndcg_at_k"] is None


def test_role_mutation_changes_role_metrics():
    before, _ = both()
    gold = copy.deepcopy(GOLD)
    gold["queries"][0]["judgments"][2]["role"] = "SUPPORT"
    after, rb = both(gold=gold)
    assert after == rb
    assert (
        before["per_query"]["q1"]["evidence_recall_at_k"],
        before["per_query"]["q1"]["counterevidence_recall_at_k"],
    ) != (
        after["per_query"]["q1"]["evidence_recall_at_k"],
        after["per_query"]["q1"]["counterevidence_recall_at_k"],
    )


def test_joint_group_loss_changes_coverage():
    before, _ = both()
    run = copy.deepcopy(RUN)
    run["queries"][1]["hits"] = [
        {"rank": 1, "passage_id": "p4"},
        {"rank": 2, "passage_id": "p3"},
        {"rank": 3, "passage_id": "p6"},
    ]
    after, rb = both(run=run)
    assert after == rb
    assert after["per_query"]["q2"]["joint_group_coverage_at_k"] < before["per_query"]["q2"]["joint_group_coverage_at_k"]


@pytest.mark.parametrize("key", ["corpus_version", "corpus_sha256", "benchmark_sha256"])
def test_required_identity_must_be_present_even_when_all_three_omit_it(key):
    manifest = copy.deepcopy(MANIFEST)
    gold = copy.deepcopy(GOLD)
    run = copy.deepcopy(RUN)
    manifest.pop(key)
    gold.pop(key)
    run.pop(key)
    rejects(manifest=manifest, gold=gold, run=run)


def test_representation_identity_is_the_normative_alternate_locator():
    manifest = copy.deepcopy(MANIFEST)
    manifest["passages"][0].pop("locator")
    manifest["passages"][0]["representation_identity"] = "dummy-representation:p1"
    ra, rb = both(manifest=manifest)
    assert ra == rb


@pytest.mark.parametrize("alias", ["representation_id", "representation_sha256", "representation"])
def test_representation_aliases_do_not_satisfy_locator_requirement(alias):
    manifest = copy.deepcopy(MANIFEST)
    manifest["passages"][0].pop("locator")
    manifest["passages"][0][alias] = "dummy-representation:p1"
    rejects(manifest=manifest)


def test_unknown_relevance_requires_unknown_role():
    gold = copy.deepcopy(GOLD)
    row = gold["queries"][1]["judgments"][3]
    assert row["relevance_degree"] == "UNKNOWN"
    row["role"] = "SUPPORT"
    rejects(gold=gold)


def test_resolved_relevance_may_retain_unknown_role():
    gold = copy.deepcopy(GOLD)
    row = gold["queries"][0]["judgments"][1]
    row["role"] = "UNKNOWN"
    ra, rb = both(gold=gold)
    assert ra == rb


def test_group_identity_is_query_local():
    gold = copy.deepcopy(GOLD)
    gold["queries"][1]["groups"][0]["group_id"] = "g1"
    ra, rb = both(gold=gold)
    assert ra == rb


def test_duplicate_group_identity_within_query_fails_closed():
    gold = copy.deepcopy(GOLD)
    gold["queries"][0]["groups"][1]["group_id"] = gold["queries"][0]["groups"][0]["group_id"]
    rejects(gold=gold)


@pytest.mark.parametrize("field", ["judgments", "groups"])
def test_gold_collections_must_be_explicit(field):
    gold = copy.deepcopy(GOLD)
    gold["queries"][0].pop(field)
    rejects(gold=gold)


def test_explicit_empty_gold_collections_are_valid():
    gold = copy.deepcopy(GOLD)
    gold["queries"][1]["judgments"] = []
    gold["queries"][1]["groups"] = []
    ra, rb = both(gold=gold)
    assert ra == rb
    assert ra["per_query"]["q2"]["hit_at_k"] is None
    assert ra["per_query"]["q2"]["joint_group_coverage_at_k"] is None


@pytest.mark.parametrize("which", ["unknown_id", "duplicate_id", "rank_gap", "version", "corpus_hash", "benchmark_hash"])
def test_fail_closed_run_defects(which):
    run = copy.deepcopy(RUN)
    if which == "unknown_id":
        run["queries"][0]["hits"][0]["passage_id"] = "not-in-corpus"
    elif which == "duplicate_id":
        run["queries"][0]["hits"][1]["passage_id"] = run["queries"][0]["hits"][0]["passage_id"]
    elif which == "rank_gap":
        run["queries"][0]["hits"][1]["rank"] = 3
    elif which == "version":
        run["corpus_version"] = "wrong"
    elif which == "corpus_hash":
        run["corpus_sha256"] = "0" * 64
    elif which == "benchmark_hash":
        run["benchmark_sha256"] = "0" * 64
    rejects(run=run)


@pytest.mark.parametrize("which", ["duplicate_query", "duplicate_source", "unknown_source", "missing_locator"])
def test_fail_closed_manifest_defects(which):
    manifest = copy.deepcopy(MANIFEST)
    if which == "duplicate_query":
        manifest["queries"].append(copy.deepcopy(manifest["queries"][0]))
    elif which == "duplicate_source":
        manifest["sources"].append(copy.deepcopy(manifest["sources"][0]))
    elif which == "unknown_source":
        manifest["passages"][0]["source_id"] = "missing-source"
    elif which == "missing_locator":
        manifest["passages"][0].pop("locator", None)
    rejects(manifest=manifest)


def test_unknown_remains_distinct_from_irrelevant_and_unjudged():
    baseline, _ = both()
    run = copy.deepcopy(RUN)
    run["queries"][1]["hits"][2]["passage_id"] = "p6"
    changed, rb = both(run=run)
    assert changed == rb
    assert changed["per_query"]["q2"]["judgment_coverage_at_k"] == 1.0
    assert changed["per_query"]["q2"]["resolved_judgment_coverage_at_k"] == pytest.approx(2 / 3)
    assert changed["per_query"]["q2"]["hit_at_k"] == baseline["per_query"]["q2"]["hit_at_k"]


def test_reordered_gold_serialization_preserves_commitment_and_metrics():
    reordered = copy.deepcopy(GOLD)
    reordered["queries"].reverse()
    for query in reordered["queries"]:
        query["judgments"].reverse()
        query["groups"].reverse()
        for group in query["groups"]:
            group["passage_ids"].reverse()
    assert C.commitment_sha256(GOLD) == C.commitment_sha256(reordered)
    ra, rb = both(gold=reordered)
    baseline, _ = both()
    assert ra == rb
    assert ra["aggregate"] == baseline["aggregate"]


def test_existing_dummy_commitment_is_unchanged():
    assert C.commitment_sha256(GOLD) == "2d0e0d99d23295b91c838e01a4e1a6274e2a77af45cd52ab834ed78fd5b6131f"
