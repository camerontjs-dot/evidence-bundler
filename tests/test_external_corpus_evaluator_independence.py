from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
MOD = ROOT / "research" / "external_corpus_evaluator_independence_v1"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, MOD / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


A = _load("evaluator_a")
B = _load("evaluator_b")
C = _load("canonical")
MANIFEST = json.loads((MOD / "dummy_manifest.json").read_text())
RUN = json.loads((MOD / "dummy_run.json").read_text())
GOLD_PATH = MOD / "revealed_dummy_gold.json"


def gold() -> dict:
    return json.loads(GOLD_PATH.read_text())


def both(manifest=None, qrels=None, run=None):
    manifest = copy.deepcopy(MANIFEST if manifest is None else manifest)
    qrels = copy.deepcopy(gold() if qrels is None else qrels)
    run = copy.deepcopy(RUN if run is None else run)
    return A.evaluate(manifest, qrels, run), B.evaluate(manifest, qrels, run)


def metric_view(result):
    return result["aggregate"], result["ndcg_eligible"], result["metric_interpretation"]


def test_independent_implementations_agree_on_dummy_run():
    ra, rb = both()
    assert ra == rb
    assert ra["aggregate"]["hit_at_k"] == 1.0
    assert ra["aggregate"]["evidence_recall_at_k"] == 1.0
    assert ra["aggregate"]["counterevidence_recall_at_k"] == 0.5
    assert ra["ndcg_eligible"] is False


def test_oracle_result():
    oracle = copy.deepcopy(RUN)
    oracle["queries"][0]["hits"] = [
        {"rank": 1, "passage_id": "p1"},
        {"rank": 2, "passage_id": "p2"},
        {"rank": 3, "passage_id": "p3"},
    ]
    oracle["queries"][1]["hits"] = [
        {"rank": 1, "passage_id": "p4"},
        {"rank": 2, "passage_id": "p5"},
        {"rank": 3, "passage_id": "p3"},
    ]
    ra, rb = both(run=oracle)
    assert ra == rb
    assert ra["aggregate"]["hit_at_k"] == 1.0
    assert ra["aggregate"]["evidence_recall_at_k"] == 1.0
    assert ra["aggregate"]["counterevidence_recall_at_k"] == 1.0
    assert ra["aggregate"]["joint_group_coverage_at_k"] == 1.0


def test_missing_decisive_evidence_changes_recall():
    before, _ = both()
    run = copy.deepcopy(RUN)
    run["queries"][0]["hits"] = [
        {"rank": 1, "passage_id": "p6"},
        {"rank": 2, "passage_id": "p2"},
        {"rank": 3, "passage_id": "p3"},
    ]
    ra, rb = both(run=run)
    assert ra == rb
    assert ra["per_query"]["q1"]["evidence_recall_at_k"] < before["per_query"]["q1"]["evidence_recall_at_k"]


def test_rank_movement_across_k_changes_recall():
    k2 = copy.deepcopy(RUN)
    k2["k"] = 2
    for row in k2["queries"]:
        row["hits"] = row["hits"][:2]
    before, _ = both(run=k2)
    moved = copy.deepcopy(k2)
    moved["queries"][0]["hits"] = [
        {"rank": 1, "passage_id": "p6"},
        {"rank": 2, "passage_id": "p1"},
    ]
    ra, rb = both(run=moved)
    assert ra == rb
    assert ra["per_query"]["q1"]["evidence_recall_at_k"] < before["per_query"]["q1"]["evidence_recall_at_k"]


def test_partial_joint_group_and_alternative_group_semantics():
    ra, rb = both()
    assert ra == rb
    assert ra["per_query"]["q1"]["joint_group_coverage_at_k"] == 0.5


def test_support_counterevidence_mutation_changes_role_metrics():
    qrels = gold()
    before, _ = both(qrels=qrels)
    qrels["queries"][0]["judgments"][2]["role"] = "SUPPORT"
    after, rb = both(qrels=qrels)
    assert after == rb
    before_pair = (
        before["per_query"]["q1"]["evidence_recall_at_k"],
        before["per_query"]["q1"]["counterevidence_recall_at_k"],
    )
    after_pair = (
        after["per_query"]["q1"]["evidence_recall_at_k"],
        after["per_query"]["q1"]["counterevidence_recall_at_k"],
    )
    assert before_pair != after_pair


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
    with pytest.raises((A.ContractError, ValueError)):
        A.evaluate(copy.deepcopy(MANIFEST), gold(), run)
    with pytest.raises((B.ContractError, ValueError)):
        B.evaluate(copy.deepcopy(MANIFEST), gold(), run)


def test_unknown_is_distinct_from_irrelevant_and_unjudged():
    ra, rb = both()
    assert ra == rb
    assert ra["per_query"]["q2"]["judgment_coverage_at_k"] == 1.0
    assert ra["per_query"]["q2"]["resolved_judgment_coverage_at_k"] == 1.0
    run = copy.deepcopy(RUN)
    run["queries"][1]["hits"][2]["passage_id"] = "p6"
    changed, rb2 = both(run=run)
    assert changed == rb2
    assert changed["per_query"]["q2"]["judgment_coverage_at_k"] == 1.0
    assert changed["per_query"]["q2"]["resolved_judgment_coverage_at_k"] == pytest.approx(2 / 3)
    assert changed["per_query"]["q2"]["hit_at_k"] == ra["per_query"]["q2"]["hit_at_k"]


def test_partial_qrels_are_lower_bounds_and_ndcg_disabled():
    qrels = gold()
    qrels["qrels_mode"] = "partial"
    ra, rb = both(qrels=qrels)
    assert ra == rb
    assert ra["metric_interpretation"] == "lower_bound"
    assert ra["ndcg_eligible"] is False
    assert ra["aggregate"]["ndcg_at_k"] is None


def test_ndcg_only_when_graded_complete_and_no_unknowns():
    qrels = gold()
    j = qrels["queries"][1]["judgments"][3]
    j.update({"relevance_degree": "IRRELEVANT", "binary_relevant": False, "gain": 0, "role": "NEUTRAL_OR_NOT_APPLICABLE"})
    ra, rb = both(qrels=qrels)
    assert ra == rb
    assert ra["ndcg_eligible"] is True
    assert ra["aggregate"]["ndcg_at_k"] is not None


def test_reordered_serialization_does_not_change_commitment_or_metrics():
    qrels = gold()
    reordered = copy.deepcopy(qrels)
    reordered["queries"].reverse()
    for q in reordered["queries"]:
        q["judgments"].reverse()
        q["groups"].reverse()
        for g in q["groups"]:
            g["passage_ids"].reverse()
    assert C.commitment_sha256(qrels) == C.commitment_sha256(reordered)
    ra, rb = both(qrels=reordered)
    baseline, _ = both(qrels=qrels)
    assert ra == rb
    assert metric_view(ra) == metric_view(baseline)


def test_source_order_permutation_is_metric_invariant():
    manifest = copy.deepcopy(MANIFEST)
    manifest["sources"].reverse()
    manifest["passages"].reverse()
    ra, rb = both(manifest=manifest)
    baseline, _ = both()
    assert ra == rb
    assert metric_view(ra) == metric_view(baseline)


def _rename(obj, mapping):
    if isinstance(obj, dict):
        return {k: _rename(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rename(v, mapping) for v in obj]
    if isinstance(obj, str):
        return mapping.get(obj, obj)
    return obj


def test_consistent_stable_id_renaming_preserves_metric_values():
    mapping = {f"p{i}": f"x{i}" for i in range(1, 7)} | {"q1": "z1", "q2": "z2", "s1": "t1", "s2": "t2"}
    m2 = _rename(copy.deepcopy(MANIFEST), mapping)
    g2 = _rename(gold(), mapping)
    r2 = _rename(copy.deepcopy(RUN), mapping)
    ra = A.evaluate(m2, g2, r2)
    rb = B.evaluate(m2, g2, r2)
    baseline, _ = both()
    assert ra == rb
    assert ra["aggregate"] == baseline["aggregate"]
    assert sorted(ra["per_query"].values(), key=str) == sorted(baseline["per_query"].values(), key=str)
    assert C.commitment_sha256(g2) != C.commitment_sha256(gold())


def test_commitment_reveal_verifies_and_semantic_mutation_fails():
    qrels = gold()
    committed = (MOD / "dummy_gold_commitment.sha256").read_text().strip()
    assert C.commitment_sha256(qrels) == committed
    changed = copy.deepcopy(qrels)
    changed["queries"][0]["judgments"][0]["gain"] = 4
    assert C.commitment_sha256(changed) != committed


def test_evaluators_share_contract_data_not_implementation_helpers():
    a = (MOD / "evaluator_a.py").read_text()
    b = (MOD / "evaluator_b.py").read_text()
    assert "evaluator_b" not in a
    assert "evaluator_a" not in b
    assert "canonical" not in a
    assert "canonical" not in b
