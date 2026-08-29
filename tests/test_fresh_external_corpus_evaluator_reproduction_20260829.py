from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "research" / "external_corpus_evaluator_independence_v1"
FRESH_PATH = ROOT / "research" / "external_corpus_evaluator_independence_fresh_reproduction_20260829" / "fresh_external_corpus_evaluator.py"


def _load_file(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


A = _load_file("revealed_evaluator_a", SOURCE / "evaluator_a.py")
B = _load_file("revealed_evaluator_b", SOURCE / "evaluator_b.py")
C = _load_file("revealed_canonical", SOURCE / "canonical.py")
F = _load_file("frozen_fresh_evaluator", FRESH_PATH)
MANIFEST = json.loads((SOURCE / "dummy_manifest.json").read_text())
RUN = json.loads((SOURCE / "dummy_run.json").read_text())
GOLD = json.loads((SOURCE / "revealed_dummy_gold.json").read_text())

KEYS = {
    "hit_at_k": "hit@K",
    "evidence_recall_at_k": "evidence_recall@K",
    "counterevidence_recall_at_k": "counterevidence_recall@K",
    "ndcg_at_k": "nDCG@K",
    "joint_group_coverage_at_k": "joint_group_coverage@K",
    "judgment_coverage_at_k": "judgment_coverage@K",
    "resolved_judgment_coverage_at_k": "resolved_judgment_coverage@K",
}


def results(manifest=None, gold=None, run=None):
    m = copy.deepcopy(MANIFEST if manifest is None else manifest)
    g = copy.deepcopy(GOLD if gold is None else gold)
    r = copy.deepcopy(RUN if run is None else run)
    return A.evaluate(copy.deepcopy(m), copy.deepcopy(g), copy.deepcopy(r)), B.evaluate(copy.deepcopy(m), copy.deepcopy(g), copy.deepcopy(r)), F.evaluate(copy.deepcopy(m), copy.deepcopy(g), copy.deepcopy(r))


def assert_shared_metrics(legacy, fresh, *, include_ndcg: bool):
    for qid, old_row in legacy["per_query"].items():
        new_row = fresh["per_query"][qid]
        for old_key, new_key in KEYS.items():
            if old_key == "ndcg_at_k" and not include_ndcg:
                continue
            old_value = old_row[old_key]
            new_value = new_row[new_key]
            if old_value is None or new_value is None:
                assert old_value is None and new_value is None, (qid, old_key, old_value, new_value)
            else:
                assert new_value == pytest.approx(old_value), (qid, old_key, old_value, new_value)


def test_baseline_revealed_evaluators_agree_and_fresh_agrees_except_global_ndcg_gate():
    a, b, fresh = results()
    assert a == b
    assert_shared_metrics(a, fresh, include_ndcg=False)
    assert a["ndcg_eligible"] is False
    assert a["aggregate"]["ndcg_at_k"] is None
    assert fresh["per_query"]["q1"]["nDCG@K"] is not None
    assert fresh["per_query"]["q2"]["nDCG@K"] is None


def test_when_unknown_is_resolved_ndcg_values_agree():
    gold = copy.deepcopy(GOLD)
    gold["queries"][1]["judgments"][3].update({
        "relevance_degree": "IRRELEVANT",
        "binary_relevant": False,
        "gain": 0,
        "role": "NEUTRAL_OR_NOT_APPLICABLE",
    })
    a, b, fresh = results(gold=gold)
    assert a == b
    assert a["ndcg_eligible"] is True
    assert_shared_metrics(a, fresh, include_ndcg=True)


def test_oracle_and_sensitivity_fixtures_agree_on_non_ndcg_metrics():
    variants = []

    oracle = copy.deepcopy(RUN)
    oracle["queries"][0]["hits"] = [
        {"rank": 1, "passage_id": "p1"},
        {"rank": 2, "passage_id": "p2"},
        {"rank": 3, "passage_id": "p3"},
    ]
    variants.append((GOLD, oracle))

    missing = copy.deepcopy(RUN)
    missing["queries"][0]["hits"] = [
        {"rank": 1, "passage_id": "p6"},
        {"rank": 2, "passage_id": "p2"},
        {"rank": 3, "passage_id": "p3"},
    ]
    variants.append((GOLD, missing))

    k2 = copy.deepcopy(RUN)
    k2["k"] = 2
    for row in k2["queries"]:
        row["hits"] = row["hits"][:2]
    moved = copy.deepcopy(k2)
    moved["queries"][0]["hits"] = [
        {"rank": 1, "passage_id": "p6"},
        {"rank": 2, "passage_id": "p1"},
    ]
    variants.extend([(GOLD, k2), (GOLD, moved)])

    role_mutation = copy.deepcopy(GOLD)
    role_mutation["queries"][0]["judgments"][2]["role"] = "SUPPORT"
    variants.append((role_mutation, RUN))

    unknown_retrieved = copy.deepcopy(RUN)
    unknown_retrieved["queries"][1]["hits"][2]["passage_id"] = "p6"
    variants.append((GOLD, unknown_retrieved))

    for gold, run in variants:
        a, b, fresh = results(gold=gold, run=run)
        assert a == b
        assert_shared_metrics(a, fresh, include_ndcg=False)


def test_partial_qrels_agree_and_report_lower_bound():
    gold = copy.deepcopy(GOLD)
    gold["qrels_mode"] = "partial"
    a, b, fresh = results(gold=gold)
    assert a == b
    assert a["metric_interpretation"] == fresh["metric_interpretation"] == "lower_bound"
    assert a["aggregate"]["ndcg_at_k"] is None
    assert fresh["macro_average"]["nDCG@K"] is None
    assert_shared_metrics(a, fresh, include_ndcg=True)


@pytest.mark.parametrize("which", ["unknown_id", "duplicate_id", "rank_gap", "version", "corpus_hash", "benchmark_hash"])
def test_revealed_fail_closed_run_fixtures_are_also_rejected_by_fresh(which):
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

    with pytest.raises(Exception):
        A.evaluate(copy.deepcopy(MANIFEST), copy.deepcopy(GOLD), copy.deepcopy(run))
    with pytest.raises(Exception):
        B.evaluate(copy.deepcopy(MANIFEST), copy.deepcopy(GOLD), copy.deepcopy(run))
    with pytest.raises(F.EvalContractError):
        F.evaluate(copy.deepcopy(MANIFEST), copy.deepcopy(GOLD), copy.deepcopy(run))


def test_canonical_commitment_agrees_with_revealed_canonicalizer():
    assert F.commitment_sha256(copy.deepcopy(GOLD)) == C.commitment_sha256(copy.deepcopy(GOLD))
    assert F.commitment_sha256(copy.deepcopy(GOLD)) == "2d0e0d99d23295b91c838e01a4e1a6274e2a77af45cd52ab834ed78fd5b6131f"

    reordered = copy.deepcopy(GOLD)
    reordered["queries"].reverse()
    for q in reordered["queries"]:
        q["judgments"].reverse()
        q["groups"].reverse()
        for group in q["groups"]:
            group["passage_ids"].reverse()
    assert F.commitment_sha256(reordered) == C.commitment_sha256(reordered) == C.commitment_sha256(GOLD)

    changed = copy.deepcopy(GOLD)
    changed["queries"][0]["judgments"][0]["gain"] = 4
    assert F.commitment_sha256(changed) == C.commitment_sha256(changed)
    assert F.commitment_sha256(changed) != C.commitment_sha256(GOLD)


def _rename(obj, mapping):
    if isinstance(obj, dict):
        return {k: _rename(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rename(v, mapping) for v in obj]
    if isinstance(obj, str):
        return mapping.get(obj, obj)
    return obj


def test_permutation_and_stable_id_rename_invariances_match_revealed_suite():
    manifest = copy.deepcopy(MANIFEST)
    manifest["sources"].reverse()
    manifest["passages"].reverse()
    a, b, fresh = results(manifest=manifest)
    assert a == b
    assert_shared_metrics(a, fresh, include_ndcg=False)

    mapping = {f"p{i}": f"x{i}" for i in range(1, 7)} | {"q1": "z1", "q2": "z2", "s1": "t1", "s2": "t2"}
    m2 = _rename(copy.deepcopy(MANIFEST), mapping)
    g2 = _rename(copy.deepcopy(GOLD), mapping)
    r2 = _rename(copy.deepcopy(RUN), mapping)
    a2, b2, f2 = results(manifest=m2, gold=g2, run=r2)
    assert a2 == b2
    assert a2["aggregate"] == a["aggregate"]
    for old_row in a2["per_query"].values():
        assert old_row in a["per_query"].values()
    for new_row in f2["per_query"].values():
        comparable = {k: v for k, v in new_row.items() if k != "metric_interpretation" and k != "nDCG@K"}
        assert any(
            all(comparable[KEYS[old_key]] == pytest.approx(old_value) if old_value is not None else comparable[KEYS[old_key]] is None for old_key, old_value in old_row.items() if old_key != "ndcg_at_k")
            for old_row in a["per_query"].values()
        )
    assert F.commitment_sha256(g2) != F.commitment_sha256(GOLD)


def test_complete_mode_interpretation_label_is_a_non_metric_representation_difference():
    a, b, fresh = results()
    assert a == b
    assert a["metric_interpretation"] == "point_estimate"
    assert fresh["metric_interpretation"] == "complete_relevant_set"
