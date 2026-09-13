#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

LABELS={'MATERIAL_FOR_PROPOSITION','NONMATERIAL_FOR_PROPOSITION','UNRESOLVED'}

def load(p:Path)->Any: return json.loads(p.read_text(encoding='utf-8'))
def canon_hash(o:Any)->str:
    return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def parse_review(path:Path, expected_hash:str, allowed:set[str])->dict[str,str]:
    o=load(path)
    if o.get('schema')!='eb-v1-operational-review-result-v1': raise ValueError(f'{path}: schema')
    r=o.get('reviewer',{})
    if r.get('packet_canonical_sha256')!=expected_hash: raise ValueError(f'{path}: packet hash')
    if r.get('independent_of_other_reviewers') is not True: raise ValueError(f'{path}: independence')
    if r.get('saw_other_review_set') is not False: raise ValueError(f'{path}: other set exposure')
    out={}
    for j in o.get('judgments',[]):
        rid=j.get('relation_id'); lab=j.get('label')
        if rid in out: raise ValueError(f'{path}: duplicate {rid}')
        if rid not in allowed: raise ValueError(f'{path}: unknown {rid}')
        if lab not in LABELS: raise ValueError(f'{path}: label {lab}')
        out[rid]=lab
    if set(out)!=allowed: raise ValueError(f'{path}: relation set mismatch')
    return out

def counts_for(review:dict[str,str], rels:list[dict[str,Any]], id_field:str):
    fm=fn=un=0
    for x in rels:
        rid=x[id_field]; gold=x['gold_label']; got=review[rid]
        if got=='UNRESOLVED': un+=1
        elif gold=='NONMATERIAL_FOR_PROPOSITION' and got=='MATERIAL_FOR_PROPOSITION': fm+=1
        elif gold=='MATERIAL_FOR_PROPOSITION' and got=='NONMATERIAL_FOR_PROPOSITION': fn+=1
    return {'false_material':fm,'false_nonmaterial':fn,'unresolved':un,'total_error':fm+fn}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--answer-key',required=True,type=Path)
    ap.add_argument('--amber-a',required=True,type=Path); ap.add_argument('--amber-b',required=True,type=Path)
    ap.add_argument('--cobalt-a',required=True,type=Path); ap.add_argument('--cobalt-b',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args(); key=load(a.answer_key)
    if key.get('schema')!='eb-v1-operational-burden-answer-key-v1': raise ValueError('answer key schema')
    files={'amber':[a.amber_a,a.amber_b],'cobalt':[a.cobalt_a,a.cobalt_b]}
    reviews={}
    for arm in ['amber','cobalt']:
        armkey=key['arms'][arm]; allowed=set(armkey['relations'])
        reviews[arm]=[parse_review(p,armkey['packet_canonical_sha256'],allowed) for p in files[arm]]
    shared=key['matched_relationships']
    arm_fields={'amber':'amber_relation_id','cobalt':'cobalt_relation_id'}
    primary={}
    for arm in ['amber','cobalt']:
        f=arm_fields[arm]
        per=[counts_for(r,shared,f) for r in reviews[arm]]
        pooled={k:sum(x[k] for x in per) for k in per[0]}
        disagree=sum(1 for x in shared if reviews[arm][0][x[f]]!=reviews[arm][1][x[f]])
        primary[arm]={'per_reviewer':per,'pooled':pooled,'inter_reviewer_disagreement':disagree}
    larger=next(k for k,v in key['arm_mapping'].items() if v=='10/7')
    smaller=next(k for k,v in key['arm_mapping'].items() if v=='5/3')
    metrics=['false_material','false_nonmaterial','unresolved']
    worse={m: primary[larger]['pooled'][m] > primary[smaller]['pooled'][m] for m in metrics}
    worse['inter_reviewer_disagreement']=primary[larger]['inter_reviewer_disagreement']>primary[smaller]['inter_reviewer_disagreement']
    if any(worse.values()):
        primary_conclusion='DECISION_QUALITY_HARM_OBSERVED'; disposition='FALSIFIED'
    else:
        primary_conclusion='NO_OBSERVED_DECISION_QUALITY_HARM'; disposition='SUPPORTED FOR PROMOTION'
    extra=key['larger_arm_only_relationships']; lf='relation_id'
    secondary=[]
    for r in reviews[larger]: secondary.append(counts_for(r,extra,lf))
    material=[x for x in extra if x['gold_label']=='MATERIAL_FOR_PROPOSITION']
    nonmat=[x for x in extra if x['gold_label']=='NONMATERIAL_FOR_PROPOSITION']
    sec={
        'relationship_count':len(extra),'gold_material_count':len(material),'gold_nonmaterial_count':len(nonmat),
        'per_reviewer':secondary,
        'material_correct_by_reviewer':[sum(rev[x[lf]]=='MATERIAL_FOR_PROPOSITION' for x in material) for rev in reviews[larger]],
        'nonmaterial_correct_by_reviewer':[sum(rev[x[lf]]=='NONMATERIAL_FOR_PROPOSITION' for x in nonmat) for rev in reviews[larger]],
        'inter_reviewer_disagreement':sum(1 for x in extra if reviews[larger][0][x[lf]]!=reviews[larger][1][x[lf]])
    }
    out={
        'schema':'eb-v1-operational-burden-result-v1',
        'arm_mapping':key['arm_mapping'],
        'shared_relationship_count':len(shared),
        'primary':primary,
        'larger_arm':larger,'smaller_arm':smaller,'larger_worse_flags':worse,
        'primary_conclusion':primary_conclusion,
        'secondary_larger_only':sec,
        'primary_disposition':disposition,
        'experiment_specific_conclusion':'NO_OBSERVED_DECISION_QUALITY_HARM_IN_MATCHED_BLIND_REVIEW' if disposition=='SUPPORTED FOR PROMOTION' else 'FIXED_K_REVIEW_CONTEXT_DEGRADES_MATCHED_ADMISSION_DECISIONS',
        'stop_boundary':True,
    }
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'primary_disposition':disposition,'primary_conclusion':primary_conclusion,'worse_flags':worse},indent=2))

if __name__=='__main__': main()
