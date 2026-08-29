#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json, shutil, tempfile
from pathlib import Path
from evaluator import evaluate, load_apparatus
from control_runner import generate

def canonical(o): return json.dumps(o,sort_keys=True,separators=(',',':')).encode()
def load_json(p:Path): return json.loads(p.read_text(encoding='utf-8'))

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--benchmark-root',type=Path,required=True)
    ap.add_argument('--oracle-raw',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    cases,passages,gold,scopes=load_apparatus(a.benchmark_root)
    oracle=load_json(a.oracle_raw); base=evaluate(a.benchmark_root,oracle)
    checks={}
    checks['oracle_positive_ceiling']=(
        base['aggregate']['combined_l01_l04_case_hit_at_5']==1.0 and
        base['aggregate']['combined_l01_l04_decisive_recall_at_5']==1.0 and
        base['families']['C01']['counterevidence_recall_at_5']==1.0 and
        base['technical']=={k:0 for k in base['technical']})

    def temp_eval(mutator):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)/'b'; shutil.copytree(a.benchmark_root,r)
            gs=[copy.deepcopy(x) for x in gold]; mutator(gs)
            (r/'evaluator_only/sealed_gold.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in gs),encoding='utf-8')
            return evaluate(r,oracle)

    decmut=temp_eval(lambda gs: gs[0].__setitem__('decisive',[gs[0]['hard_negatives'][0]]))
    checks['decisive_id_mutation_sensitivity']=canonical(decmut)!=canonical(base) and decmut['per_case'][0]['case_hit_at_5'] is False
    def mutate_hard(gs): gs[0]['hard_negatives']=[gs[0]['decisive'][0]]
    hardmut=temp_eval(mutate_hard)
    checks['hard_negative_id_mutation_sensitivity']=hardmut['aggregate']['hard_negative_hits_at_5']!=base['aggregate']['hard_negative_hits_at_5']
    def mutate_family(gs): gs[0]['family']='C01'
    fammut=temp_eval(mutate_family)
    checks['family_label_aggregation_sensitivity']=canonical(fammut)!=canonical(base) and fammut['families']['L01']['cases']!=base['families']['L01']['cases']

    prov=evaluate(a.benchmark_root,generate(a.benchmark_root,'provenance_corrupt'))
    checks['broken_provenance_failure']=prov['technical']['invalid_provenance_hits']>0
    missing=oracle[:-1]; cov=evaluate(a.benchmark_root,missing)
    checks['result_coverage_mismatch_failure']=cov['technical']['coverage_errors']>0
    retall=evaluate(a.benchmark_root,generate(a.benchmark_root,'return_all'))
    checks['k_budget_enforcement']=retall['technical']['budget_violations']==80
    malformed=copy.deepcopy(oracle); malformed[0]['unsupported_field']='should_fail_closed'
    shape=evaluate(a.benchmark_root,malformed)
    checks['result_schema_shape_failure']=shape['technical']['shape_errors']>0
    replay=evaluate(a.benchmark_root,copy.deepcopy(oracle))
    checks['deterministic_replay']=canonical(replay)==canonical(base)

    with tempfile.TemporaryDirectory() as td:
        r=Path(td)/'b'; shutil.copytree(a.benchmark_root,r)
        ps=list(reversed(passages))
        (r/'runtime/passages.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in ps),encoding='utf-8')
        inv=evaluate(r,oracle)
    checks['source_order_enumeration_invariance']=canonical(inv)==canonical(base)
    checks['exact_result_hash_reproducibility']=hashlib.sha256(canonical(base)).hexdigest()==hashlib.sha256(canonical(replay)).hexdigest()
    out={
        'record':'eb-rc4-evaluator-assurance',
        'checks':checks,
        'all_pass':all(checks.values()),
        'base_oracle_evaluation_sha256':hashlib.sha256(canonical(base)).hexdigest(),
        'hybrid_sealed_exposed':False,
        'semantic_sealed_exposed':False,
    }
    a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,sort_keys=True,indent=2))
    raise SystemExit(0 if out['all_pass'] else 5)
if __name__=='__main__': main()
