#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

def load(p): return json.loads(p.read_text()) if p and p.exists() else None
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p and p.exists() else None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--artifacts',type=Path,required=True); ap.add_argument('--target-identity',type=Path,required=True); ap.add_argument('--freeze-manifest',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    A=a.artifacts; assurance=load(A/'evaluator-assurance.json'); bm=load(A/'bm25-gate.json'); cg=load(A/'control-gate.json'); meta=load(A/'metamorphic-result.json'); target=load(a.target_identity)
    exposure=(target['exposure']['hybrid_sealed_exposed'] is False and target['exposure']['semantic_sealed_exposed'] is False)
    stages={'evaluator_assurance':bool(assurance and assurance.get('all_pass')),'bm25_prerequisite':bool(bm and bm.get('all_pass')),'weak_gaming_controls':bool(cg and cg.get('all_pass')),'metamorphic_assurance':bool(meta and meta.get('all_expected_directions_pass')),'target_unexposed':exposure}
    if assurance is not None and not assurance.get('all_pass'): disposition='FALSIFIED'; reason='evaluator assurance failed a preregistered promotion-critical check'
    elif assurance is None: disposition='INCONCLUSIVE'; reason='evaluator assurance did not complete'
    elif bm is not None and not bm.get('all_pass'): disposition='FALSIFIED'; reason='exact production BM25 did not satisfy the RC4 apparatus prerequisite'
    elif bm is None: disposition='INCONCLUSIVE'; reason='exact production BM25 prerequisite was not completed'
    elif cg is not None and not cg.get('all_pass'): disposition='FALSIFIED'; reason='a promotion-critical weak/gaming control gate failed'
    elif cg is None: disposition='INCONCLUSIVE'; reason='weak/gaming control suite did not complete'
    elif meta is not None and not meta.get('all_expected_directions_pass'): disposition='FALSIFIED'; reason='preregistered metamorphic expected-direction assurance failed'
    elif meta is None: disposition='INCONCLUSIVE'; reason='metamorphic assurance did not complete'
    elif not exposure: disposition='FALSIFIED'; reason='target exposure state is contaminated'
    elif all(stages.values()): disposition='SUPPORTED FOR PROMOTION'; reason='all frozen apparatus promotion-critical gates passed'
    else: disposition='INCONCLUSIVE'; reason='apparatus evidence is incomplete'
    out={'record':'eb-rc4-terminal-apparatus-decision','disposition':disposition,'reason':reason,'stages':stages,'authorization':'UNCHANGED_APPARATUS_HANDOFF_TO_SEPARATE_PR17_TARGET_EXECUTION' if disposition=='SUPPORTED FOR PROMOTION' else 'TARGET_EXECUTION_PROHIBITED','synthetic_program_termination_required':disposition!='SUPPORTED FOR PROMOTION','no_rc5':disposition!='SUPPORTED FOR PROMOTION','hybrid_sealed_exposed':False,'semantic_sealed_exposed':False,'hashes':{'freeze_manifest_sha256':h(a.freeze_manifest),'first_sealed_control_sha256':h(A/'first-sealed-control.json'),'bm25_raw_sha256':h(A/'bm25-raw.json'),'bm25_evaluation_sha256':h(A/'bm25-evaluation.json'),'controls_sha256':h(A/'sealed-controls.json'),'metamorphic_sha256':h(A/'metamorphic-result.json')}}
    a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n'); print(json.dumps(out,sort_keys=True,indent=2))
if __name__=='__main__': main()
