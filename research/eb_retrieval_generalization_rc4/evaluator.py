#!/usr/bin/env python3
from __future__ import annotations
import json, math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

K=5
LOW=("L01","L02","L03","L04")
RESULT_KEYS={"case_id","hits"}
HIT_KEYS={"passage_id","rank","score"}

def load_jsonl(p:Path)->list[dict[str,Any]]:
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]

def load_apparatus(root:Path):
    cases=load_jsonl(root/'runtime/sealed_cases.jsonl')
    passages=load_jsonl(root/'runtime/passages.jsonl')
    gold=load_jsonl(root/'evaluator_only/sealed_gold.jsonl')
    scopes=json.loads((root/'runtime/scopes.json').read_text(encoding='utf-8'))
    return cases,passages,gold,scopes

def evaluate(root:Path, results:list[dict[str,Any]])->dict[str,Any]:
    cases,passages,gold,scopes=load_apparatus(root)
    cby={c['case_id']:c for c in cases}; gby={g['case_id']:g for g in gold}; pby={p['passage_id']:p for p in passages}
    case_result_counts=Counter(r.get('case_id') for r in results if isinstance(r,dict) and isinstance(r.get('case_id'),str))
    rby={r.get('case_id'):r for r in results if isinstance(r,dict) and isinstance(r.get('case_id'),str)}
    missing=set(cby)-set(rby); extra=set(rby)-set(cby)
    duplicate_rows=sum(v-1 for k,v in case_result_counts.items() if k in cby and v>1)
    coverage_errors=len(missing)+len(extra)+duplicate_rows
    budget=invalid=outscope=scope_mismatch=shape=false_complete=answerability=0
    family_stats=defaultdict(lambda:{'n':0,'hits':0,'dec_total':0,'dec_found':0,'rr':0.0,'counter_total':0,'counter_found':0,'counter_rr':0.0})
    hard_hits=0; per_case=[]
    for cid,c in cby.items():
        g=gby[cid]; fam=g['family']; s=family_stats[fam]; s['n']+=1
        r=rby.get(cid,{"case_id":cid,"hits":[]})
        if not isinstance(r,dict): r={"case_id":cid,"hits":[]}; shape+=1
        else:
            extras=set(r)-RESULT_KEYS
            if extras:
                shape += len(extras)
                if r.get('complete') is True or r.get('completeness_claim') is True: false_complete += 1
                if r.get('answerable') is True or r.get('answerable_claim') is True: answerability += 1
        hits=r.get('hits',[]) if isinstance(r,dict) else []
        if not isinstance(hits,list): hits=[]; shape+=1
        if len(hits)>c['runtime_config']['maximum_passages']: budget+=1
        valid_scope=set(scopes[c['accessible_subset_id']]['passage_ids']); ids=[]; seen=set()
        for i,h in enumerate(hits):
            if not isinstance(h,dict): shape+=1; continue
            if set(h)!=HIT_KEYS: shape+=len(set(h)^HIT_KEYS) or 1
            pid=h.get('passage_id'); rank=h.get('rank'); score=h.get('score')
            if not isinstance(pid,str) or not pid: shape+=1; continue
            if not isinstance(rank,int) or isinstance(rank,bool) or rank!=i+1: shape+=1
            if not isinstance(score,(int,float)) or isinstance(score,bool) or not math.isfinite(float(score)): shape+=1
            if pid in seen: shape+=1
            seen.add(pid); ids.append(pid)
            if pid not in pby: invalid+=1
            else:
                if pby[pid]['case_id']!=cid: scope_mismatch+=1
                if pid not in valid_scope: outscope+=1
        ids=ids[:K]
        decisive=[d['passage_id'] for d in g['decisive']]; hard=[d['passage_id'] for d in g['hard_negatives']]
        found=[x for x in decisive if x in ids]
        s['dec_total']+=len(decisive); s['dec_found']+=len(found)
        case_hit=bool(found); s['hits']+=int(case_hit)
        rr=1.0/(min(ids.index(x) for x in found)+1) if found else 0.0; s['rr']+=rr
        hh=sum(1 for x in hard if x in ids); hard_hits+=hh
        if fam=='C01':
            s['counter_total']+=len(decisive); s['counter_found']+=len(found); s['counter_rr']+=rr
        per_case.append({'case_id':cid,'family':fam,'case_hit_at_5':case_hit,'decisive_recall_at_5':len(found)/len(decisive),'first_decisive_rr':rr,'hard_negative_hits':hh})
    famout={}
    for fam in ("L01","L02","L03","L04","C01"):
        s=family_stats[fam]
        famout[fam]={
            'cases':s['n'],
            'case_hit_at_5':s['hits']/s['n'] if s['n'] else 0.0,
            'decisive_recall_at_5':s['dec_found']/s['dec_total'] if s['dec_total'] else 0.0,
            'first_decisive_mrr':s['rr']/s['n'] if s['n'] else 0.0,
            'counterevidence_case_hit_at_5':s['hits']/s['n'] if fam=='C01' and s['n'] else None,
            'counterevidence_recall_at_5':s['counter_found']/s['counter_total'] if fam=='C01' and s['counter_total'] else None,
            'first_counterevidence_mrr':s['counter_rr']/s['n'] if fam=='C01' and s['n'] else None,
        }
    lowcases=sum(family_stats[f]['n'] for f in LOW); lowhits=sum(family_stats[f]['hits'] for f in LOW)
    lowdec=sum(family_stats[f]['dec_total'] for f in LOW); lowfound=sum(family_stats[f]['dec_found'] for f in LOW); lowrr=sum(family_stats[f]['rr'] for f in LOW)
    aggregate={
        'combined_l01_l04_case_hit_at_5':lowhits/lowcases if lowcases else 0.0,
        'combined_l01_l04_decisive_recall_at_5':lowfound/lowdec if lowdec else 0.0,
        'combined_l01_l04_first_decisive_mrr':lowrr/lowcases if lowcases else 0.0,
        'hard_negative_hits_at_5':hard_hits,
    }
    technical={
        'coverage_errors':coverage_errors,
        'budget_violations':budget,
        'invalid_provenance_hits':invalid,
        'out_of_scope_hits':outscope,
        'scope_mismatches':scope_mismatch,
        'false_completeness_claims':false_complete,
        'answerability_overclaims':answerability,
        'shape_errors':shape,
    }
    return {'aggregate':aggregate,'families':famout,'technical':technical,'per_case':per_case}

def qualify_target(ev:dict[str,Any], thresholds:dict[str,Any])->tuple[bool,list[str]]:
    t=thresholds['target_gates']; a=ev['aggregate']; f=ev['families']; tech=ev['technical']; fails=[]
    checks=[
        ('combined_l01_l04_case_hit_at_5',a['combined_l01_l04_case_hit_at_5'],t['combined_l01_l04_case_hit_at_5_min']),
        ('combined_l01_l04_decisive_recall_at_5',a['combined_l01_l04_decisive_recall_at_5'],t['combined_l01_l04_decisive_recall_at_5_min']),
        ('combined_l01_l04_first_decisive_mrr',a['combined_l01_l04_first_decisive_mrr'],t['combined_l01_l04_first_decisive_mrr_min'])]
    for n,v,m in checks:
        if v<m: fails.append(f'{n}={v:.6f} < {m}')
    for fam in LOW:
        if f[fam]['case_hit_at_5']<t['per_low_overlap_family_case_hit_at_5_min']: fails.append(f'{fam}.case_hit_at_5')
        if f[fam]['decisive_recall_at_5']<t['per_low_overlap_family_decisive_recall_at_5_min']: fails.append(f'{fam}.decisive_recall_at_5')
    c=f['C01']
    if c['counterevidence_case_hit_at_5']<t['c01_counterevidence_case_hit_at_5_min']: fails.append('C01.case_hit')
    if c['counterevidence_recall_at_5']<t['c01_counterevidence_recall_at_5_min']: fails.append('C01.recall')
    if c['first_counterevidence_mrr']<t['c01_counterevidence_first_mrr_min']: fails.append('C01.mrr')
    for key in ('budget_violations','invalid_provenance_hits','out_of_scope_hits','scope_mismatches','false_completeness_claims','answerability_overclaims','shape_errors','coverage_errors'):
        maxkey='max_'+key
        if maxkey in t and tech[key]>t[maxkey]: fails.append(key)
    return not fails,fails
