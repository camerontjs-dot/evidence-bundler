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


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"v2_{name}", V2 / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"v2_{name}"] = module
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


def test_reference_implementations_agree_on_original_dummy():
    ra, rb = both()
    assert ra == rb
    assert ra["aggregate"]["hit_at_k"] == 1.0
    assert ra["aggregate"]["evidence_recall_at_k"] == 1.0
    assert ra["aggregate"]["counterevidence_recall_at_k"] == 0.5


def test_original_dummy_exercises_query_local_ndcg_scope():
    ra, rb = both()
    assert ra == rb
    assert ra["ndcg_eligible_by_query"] == {"q1": True, "q2": False}
    assert ra["per_query"]["q1"]["ndcg_at_k"] == pytest.approx(0.938506417451168)
    assert ra["per_query"]["q2"]["ndcg_at_k"] is None
    assert ra["aggregate"]["ndcg_at_k"] == pytest.approx(ra["per_query"]["q1"]["ndcg_at_k"])


def test_minimal_ndcg_scope_discriminator():
    ra = A.evaluate(copy.deepcopy(SCOPE_MANIFEST), copy.deepcopy(SCOPE_GOLD), copy.deepcopy(SCOPE_RUN))
    rb = B.evaluate(copy.deepcopy(SCOPE_MANIFEST), copy.deepcopy(SCOPE_GOLD), copy.deepcopy(SCOPE_RUN))
    assert ra == rb
    assert ra["ndcg_eligible_by_query"] == {"q_clean": True, "q_unknown": False}
    assert ra["per_query"]["q_clean"]["ndcg_at_k"] == pytest.approx(0.7098097413968655)
    assert ra["per_query"]["q_unknown"]["ndcg_at_k"] is None
    assert ra["aggregate"]["ndcg_at_k"] == pytest.approx(0.7098097413968655)


def test_resolving_unknown_enables_second_query_without_changing_first():
    before, _ = both()
    gold = copy.deepcopy(GOLD)
    gold["queries"][1]["judgments"][3].update(
        {
            "relevance_degree": "IRRELEVANT",
            "binary_relevant": False,
            "gain": 0,
            "role": "NEUTRAL_OR_NOT_APPLICABLE",
        }
    )
    after, rb = both(gold=gold)
    assert after == rb
    assert after["per_query"]["q1"]["ndcg_at_k"] == pytest.approx(before["per_query"]["q1"]["ndcg_at_k"])
    assert after["ndcg_eligible_by_query"] == {"q1": True, "q2": True}
    assert after["per_query"]["q2"]["ndcg_at_k"] is not None


def test_partial_qrels_disable_ndcg_for_every_query_and_mark_lower_bound():
    gold = copy.deepcopy(GOLD)
    gold["qrels_mode"] = "partial"
    ra, rb = both(gold=gold)
    assert ra == rb
    assert ra["metric_interpretation"] == "lower_bound"
    assert ra["ndcg_eligible_by_query"] == {"q1": False, "q2": False}
    assert ra["aggregate"]["ndcg_at_k"] is None


def test_top_level_ndcg_switch_disables_every_query():
    gold = copy.deepcopy(GOLD)
    gold["ndcg_eligible"] = False
    ra, rb = both(gold=gold)
    assert ra == rb
    assert ra["ndcg_eligible_by_query"] == {"q1": False, "q2": False}
    assert ra["aggregate"]["ndcg_at_k"] is None


def test_support_counterevidence_mutation_changes_role_metrics():
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
    for evaluator in (A, B):
        with pytest.raises((evaluator.ContractError, ValueError)):
            evaluator.evaluate(copy.deepcopy(MANIFEST), copy.deepcopy(GOLD), copy.deepcopy(run))


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
    for evaluator in (A, B):
        with pytest.raises((evaluator.ContractError, ValueError)):
            evaluator.evaluate(copy.deepcopy(manifest), copy.deepcopy(GOLD), copy.deepcopy(RUN))


def test_gold_query_set_must_match_manifest():
    gold = copy.deepcopy(GOLD)
    gold["queries"][0]["query_id"] = "not-in-manifest"
    for evaluator in (A, B):
        with pytest.raises((evaluator.ContractError, ValueError)):
            evaluator.evaluate(copy.deepcopy(MANIFEST), copy.deepcopy(gold), copy.deepcopy(RUN))


def test_run_query_set_must_match_manifest():
    run = copy.deepcopy(RUN)
    run["queries"][0]["query_id"] = "not-in-manifest"
    for evaluator in (A, B):
        with pytest.raises((evaluator.ContractError, ValueError)):
            evaluator.evaluate(copy.deepcopy(MANIFEST), copy.deepcopy(GOLD), copy.deepcopy(run))


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
    assert ra["ndcg_eligible_by_query"] == baseline["ndcg_eligible_by_query"]


def test_existing_dummy_commitment_is_unchanged():
    assert C.commitment_sha256(GOLD) == "2d0e0d99d23295b91c838e01a4e1a6274e2a77af45cd52ab834ed78fd5b6131f"


def _rename(obj, mapping):
    if isinstance(obj, dict):
        return {key: _rename(value, mapping) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_rename(value, mapping) for value in obj]
    if isinstance(obj, str):
        return mapping.get(obj, obj)
    return obj


def test_stable_id_renaming_preserves_metric_values():
    mapping = {f"p{i}": f"x{i}" for i in range(1, 7)} | {"q1": "z1", "q2": "z2", "s1": "t1", "s2": "t2"}
    m2 = _rename(copy.deepcopy(MANIFEST), mapping)
    g2 = _rename(copy.deepcopy(GOLD), mapping)
    r2 = _rename(copy.deepcopy(RUN), mapping)
    ra = A.evaluate(m2, g2, r2)
    rb = B.evaluate(copy.deepcopy(m2), copy.deepcopy(g2), copy.deepcopy(r2))
    baseline, _ = both()
    assert ra == rb
    assert ra["aggregate"] == baseline["aggregate"]
    assert sorted(ra["per_query"].values(), key=str) == sorted(baseline["per_query"].values(), key=str)
    assert C.commitment_sha256(g2) != C.commitment_sha256(GOLD)
