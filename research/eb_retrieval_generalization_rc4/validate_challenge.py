#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, json, re
from pathlib import Path
from typing import Any

FAMILIES=("L01","L02","L03","L04","C01")
DIMS=("construction_family","length_bin","sentence_position","punctuation","identifier_pattern","metadata_style","realization")
FORBIDDEN_RUNTIME_KEYS={"family","role","decisive","hard_negative","hard_negatives","cue_profile","hidden_passage_annotations","entity_stem"}

def load_jsonl(p:Path)->list[dict[str,Any]]:
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]

def norm(s:str)->str:
    return re.sub(r"\s+"," ",s.strip().lower())

def flatten_strings(obj:Any)->list[str]:
    out=[]
    if isinstance(obj,str): out.append(obj)
    elif isinstance(obj,dict):
        for v in obj.values(): out.extend(flatten_strings(v))
    elif isinstance(obj,list):
        for v in obj: out.extend(flatten_strings(v))
    return out

def validate(root:Path, reuse_roots:list[Path])->dict[str,Any]:
    cases=load_jsonl(root/'runtime/sealed_cases.jsonl')
    passages=load_jsonl(root/'runtime/passages.jsonl')
    gold=load_jsonl(root/'evaluator_only/sealed_gold.jsonl')
    fam=json.loads((root/'evaluator_only/family_membership.json').read_text())
    scopes=json.loads((root/'runtime/scopes.json').read_text())
    errs=[]; checks={}
    checks['case_count']=len(cases)==80
    checks['passage_count']=len(passages)==800
    checks['gold_count']=len(gold)==80
    checks['family_counts']=all(len(fam.get(f,[]))==16 for f in FAMILIES)
    ids=[c['case_id'] for c in cases]
    checks['unique_case_ids']=len(ids)==len(set(ids))
    pids=[p['passage_id'] for p in passages]
    checks['unique_passage_ids']=len(pids)==len(set(pids))
    bycase=collections.defaultdict(list)
    for p in passages: bycase[p['case_id']].append(p)
    checks['ten_passages_each']=all(len(bycase[c['case_id']])==10 for c in cases)
    checks['k_is_five']=all(c['runtime_config']['maximum_passages']==5 for c in cases)
    checks['scope_complete']=all(len(scopes[c['accessible_subset_id']]['passage_ids'])==10 for c in cases)
    # Runtime firewall.
    def badkeys(o:Any)->bool:
        if isinstance(o,dict):
            if FORBIDDEN_RUNTIME_KEYS.intersection(o): return True
            return any(badkeys(v) for v in o.values())
        if isinstance(o,list): return any(badkeys(v) for v in o)
        return False
    checks['runtime_gold_firewall']=not badkeys(cases) and not badkeys(passages) and not badkeys(scopes)
    gby={g['case_id']:g for g in gold}
    # Pair semantics and L04 explicit cue exchange.
    pair_groups=collections.defaultdict(list)
    for c in cases: pair_groups[c['pair_id']].append(c)
    pair_ok=True; l04_ok=True
    for pair, cs in pair_groups.items():
        if len(cs)!=2 or {c['variant'] for c in cs}!={'A','B'}: pair_ok=False; continue
        a,b=sorted(cs,key=lambda x:x['variant'])
        ga,gb=gby[a['case_id']],gby[b['case_id']]
        if a['claim_text']!=b['claim_text'] or ga['entity_stem']!=gb['entity_stem']: pair_ok=False
        if ga['family']=='L04':
            def prof(g:dict[str,Any], role:str)->int:
                return next(v['cue_profile_index'] for v in g['hidden_passage_annotations'].values() if v['role']==role)
            if not (prof(ga,'decisive')==prof(gb,'hard_negative') and prof(ga,'hard_negative')==prof(gb,'decisive')): l04_ok=False
    checks['paired_semantic_identity']=pair_ok
    checks['l04_decisive_hard_cue_exchange']=l04_ok
    # Cue independence by semantic role. "Balanced across roles" means the runtime cue
    # distribution is the same for low-overlap decisive passages, C01 counterevidence,
    # hard negatives, and ordinary distractors. A cue family need not be internally
    # uniform when its finite 8-profile permutation is deliberately 2/3/3; what matters
    # for anti-gaming is that role does not change that distribution.
    role_groups={'decisive':[], 'counterevidence':[], 'hard_negative':[], 'ordinary_distractor':[]}
    for g in gold:
        for ann in g['hidden_passage_annotations'].values():
            role=ann['role']
            if role=='decisive':
                role_groups['counterevidence' if g['family']=='C01' else 'decisive'].append(ann)
            elif role=='hard_negative':
                role_groups['hard_negative'].append(ann)
            elif role.startswith('distractor_'):
                role_groups['ordinary_distractor'].append(ann)
    balance={}
    cue_ok=True
    for d in DIMS:
        values=sorted({a['cue_profile'][d] for anns in role_groups.values() for a in anns})
        expected=None
        for role,anns in role_groups.items():
            cnt=collections.Counter(a['cue_profile'][d] for a in anns)
            frac={val: cnt[val]/len(anns) for val in values}
            balance[f'{role}:{d}']={'counts':dict(sorted(cnt.items())), 'fractions':frac}
            if expected is None:
                expected=frac
            elif any(abs(frac[val]-expected[val])>1e-12 for val in values):
                cue_ok=False; errs.append(f'cue role-distribution mismatch {d}: {role}={frac} expected={expected}')
    checks['cue_balance']=cue_ok
    # Global position/source/passage balance for decisive and hard negative.
    position_balance={}
    for role in ('decisive','hard_negative'):
        anns=[]
        for g in gold: anns += [v for v in g['hidden_passage_annotations'].values() if v['role']==role]
        for d in ('global_position','source_order','passage_order'):
            cnt=collections.Counter(a[d] for a in anns); spread=max(cnt.values())-min(cnt.values())
            position_balance[f'{role}:{d}']={'counts':dict(sorted(cnt.items())), 'spread':spread}
            if spread>1: errs.append(f'position imbalance {role}:{d}: {cnt}')
    checks['position_balance']=not any(e.startswith('position imbalance') for e in errs)
    # Exact freshness/non-reuse against supplied predecessor roots.
    current_text={norm(c['claim_text']) for c in cases}|{norm(p['text']) for p in passages}
    current_entities={norm(g['entity_stem']) for g in gold}
    collisions=[]
    for rr in reuse_roots:
        if not rr.exists(): continue
        predecessor_text=set(); predecessor_entities=set()
        for p in rr.rglob('*.json*'):
            try:
                if p.suffix=='.jsonl': rows=load_jsonl(p); strings=flatten_strings(rows)
                else: strings=flatten_strings(json.loads(p.read_text(encoding='utf-8')))
            except Exception: continue
            predecessor_text.update(norm(s) for s in strings if len(s.split())>=5)
            # entity stem values when named.
            try:
                objs=load_jsonl(p) if p.suffix=='.jsonl' else [json.loads(p.read_text())]
                def visit(o:Any):
                    if isinstance(o,dict):
                        if isinstance(o.get('entity_stem'),str): predecessor_entities.add(norm(o['entity_stem']))
                        for v in o.values(): visit(v)
                    elif isinstance(o,list):
                        for v in o: visit(v)
                visit(objs)
            except Exception: pass
        for t in sorted(current_text & predecessor_text): collisions.append({'root':str(rr),'kind':'exact_text','value':t[:160]})
        for e in sorted(current_entities & predecessor_entities): collisions.append({'root':str(rr),'kind':'entity_stem','value':e})
    checks['mechanical_nonreuse']=not collisions
    if collisions: errs.append(f'nonreuse collisions: {collisions[:10]}')
    # Verify SHA256SUMS.
    import hashlib
    sum_ok=True
    for line in (root/'SHA256SUMS').read_text().splitlines():
        expected, rel=line.split('  ',1); got=hashlib.sha256((root/rel).read_bytes()).hexdigest()
        if expected!=got: sum_ok=False; errs.append(f'hash mismatch {rel}')
    checks['sha256sums']=sum_ok
    for name,val in checks.items():
        if isinstance(val,bool) and not val: errs.append(f'check failed: {name}')
    return {'valid':not errs,'checks':checks,'cue_balance':balance,'position_balance':position_balance,'collisions':collisions,'errors':errs}

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument('--benchmark-root',type=Path,required=True); ap.add_argument('--reuse-root',type=Path,action='append',default=[]); ap.add_argument('--output',type=Path)
    a=ap.parse_args(); result=validate(a.benchmark_root,a.reuse_root)
    text=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if a.output: a.output.write_text(text,encoding='utf-8')
    print(text,end=''); raise SystemExit(0 if result['valid'] else 2)
if __name__=='__main__': main()
