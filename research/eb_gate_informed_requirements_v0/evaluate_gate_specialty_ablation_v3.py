from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

CAPS=("0.005","0.010","0.020")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_eval(path: str | Path) -> ModuleType:
    spec=importlib.util.spec_from_file_location("frozen_eval_v3",path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen evaluator")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sel(rows: list[dict[str,Any]]) -> dict[str,list[str]]:
    return {str(r["lane_id"]):[str(x) for x in r["selected_candidate_ids"]] for r in rows}


def compact(m: dict[str,Any]) -> dict[str,Any]:
    return {
        "coverage":m["required_lane_coverage"]["covered_positive_lanes"],
        "coverage_total":m["required_lane_coverage"]["eligible_positive_lanes"],
        "useful_retained":m["useful_item_recall_at_3"]["useful_groups_retained"],
        "useful_available":m["useful_item_recall_at_3"]["useful_groups_available"],
        "useful_recall":m["useful_item_recall_at_3"]["rate"],
        "unsafe":m["unsafe_misleading_retention"]["total"],
        "nonuseful":m["nonuseful_burden"]["total"],
        "deep_useful_rescue":m["deep_useful_rescue_count"],
    }


def delta(a: dict[str,Any], b: dict[str,Any]) -> dict[str,float|int]:
    return {
        "coverage":a["required_lane_coverage"]["covered_positive_lanes"]-b["required_lane_coverage"]["covered_positive_lanes"],
        "useful_recall":a["useful_item_recall_at_3"]["rate"]-b["useful_item_recall_at_3"]["rate"],
        "unsafe":a["unsafe_misleading_retention"]["total"]-b["unsafe_misleading_retention"]["total"],
        "nonuseful":a["nonuseful_burden"]["total"]-b["nonuseful_burden"]["total"],
        "deep_useful_rescue":a["deep_useful_rescue_count"]-b["deep_useful_rescue_count"],
    }


def subset(
    evaluator: ModuleType,
    arm: str,
    selections: dict[str, list[str]],
    lanes: dict[str, Any],
    ids: list[str],
) -> dict[str, Any]:
    return evaluator._arm_metrics(
        arm,
        {i:selections[i] for i in ids},
        {i:lanes[i] for i in ids},
    )


def changed(a: dict[str,list[str]], b: dict[str,list[str]], ids: list[str]) -> list[str]:
    return [i for i in ids if a[i]!=b[i]]


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--selections",required=True)
    p.add_argument("--gold",required=True)
    p.add_argument("--frozen-evaluator",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()

    source=load_json(args.selections)
    gold=load_json(args.gold)
    evaluator=load_eval(args.frozen_evaluator)
    lane_by_id,_=evaluator._gold_index(gold)
    arms={name:sel(rows) for name,rows in source["selections"].items()}
    exceptional=list(source["exceptional_lanes"])
    baseline_name="control_semantic_top3_no_gates"
    baseline_all=evaluator._arm_metrics(baseline_name,arms[baseline_name],lane_by_id)
    baseline_exc=subset(evaluator,baseline_name,arms[baseline_name],lane_by_id,exceptional)

    results=[]
    for label in CAPS:
        names={
            "full":f"true_full_gate_cap_{label}",
            "specialty_fraction":f"true_specialty_fraction_cap_{label}",
            "specialty_anyof":f"true_specialty_anyof_cap_{label}",
            "shuffled":f"rare_shuffled_specialty_fraction_cap_{label}",
            "generic_any":f"generic_any_specialty_cap_{label}",
            "generic_union":f"generic_union_specialty_fraction_cap_{label}",
            "ablate_authoritative":f"ablate_authoritative_declaration_cap_{label}",
            "ablate_event":f"ablate_event_record_cap_{label}",
            "ablate_registry":f"ablate_registry_entry_cap_{label}",
        }
        all_metrics={k:evaluator._arm_metrics(v,arms[v],lane_by_id) for k,v in names.items()}
        exc_metrics={k:subset(evaluator,v,arms[v],lane_by_id,exceptional) for k,v in names.items()}
        full_map=arms[names["full"]]
        row={
            "loss_cap":float(label),
            "overall":{k:compact(v) for k,v in all_metrics.items()},
            "exceptional_8":{k:compact(v) for k,v in exc_metrics.items()},
            "exceptional_deltas_vs_full":{
                k:delta(v,exc_metrics["full"]) for k,v in exc_metrics.items() if k!="full"
            },
            "exceptional_deltas_vs_semantic":{
                k:delta(v,baseline_exc) for k,v in exc_metrics.items()
            },
            "changed_lanes_vs_full":{
                k:changed(arms[v],full_map,exceptional) for k,v in names.items() if k!="full"
            },
            "full_vs_semantic":delta(all_metrics["full"],baseline_all),
        }
        results.append(row)

    output={
        "schema":"eb-gate-specialty-ablation-v3-evaluation",
        "classification":"EXPOSED_DEVELOPMENT_SPECIALTY_ABLATION_DIAGNOSTIC",
        "selection_sha256":sha(args.selections),
        "gold_sha256":sha(args.gold),
        "frozen_evaluator_sha256":sha(args.frozen_evaluator),
        "specialty_by_lane":source["specialty_by_lane"],
        "union_specialty":source["union_specialty"],
        "exceptional_lanes":exceptional,
        "baseline_exceptional":compact(baseline_exc),
        "results":results,
        "nonclaims":[
            "exposed development ablation only",
            "no Gate field or EB behavior qualified",
            "no model or Gate runtime rerun",
            "fresh independent reproduction remains required",
        ],
    }
    output["evaluation_sha256"]=hashlib.sha256(
        json.dumps(output,sort_keys=True,separators=(",",":")).encode()
    ).hexdigest()
    Path(args.out).write_text(json.dumps(output,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "specialty_by_lane":output["specialty_by_lane"],
        "union_specialty":output["union_specialty"],
        "baseline_exceptional":output["baseline_exceptional"],
        "results":results,
    },indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
