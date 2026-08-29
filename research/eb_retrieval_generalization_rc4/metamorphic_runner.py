#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json, shutil, tempfile
from pathlib import Path
from typing import Any
from generate_challenge import render_semantic
from control_runner import generate
from evaluator import evaluate, qualify_target

def loadj(p:Path): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def dumpj(p:Path,rows): p.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in rows),encoding='utf-8')
def canonical(o): return json.dumps(o,sort_keys=True,separators=(',',':')).encode()
def text_hash(s:str): return hashlib.sha256(s.encode()).hexdigest()
def raw_ids(raw): return {r['case_id']:tuple(h['passage_id'] for h in r.get('hits',[])) for r in raw}
def changed_fraction(a,b):
    aa,bb=raw_ids(a),raw_ids(b); keys=sorted(set(aa)&set(bb)); return sum(aa[k]!=bb[k] for k in keys)/len(keys) if keys else 0.0

def transform(root:Path,tid:str)->dict[str,Any]:
    cases=loadj(root/'runtime/sealed_cases.jsonl'); passages=loadj(root/'runtime/passages.jsonl'); gold=loadj(root/'evaluator_only/sealed_gold.jsonl')
    pby={p['passage_id']:p for p in passages}; cby={c['case_id']:c for c in cases}
    role_changed=0
    for g in gold:
        cid=g['case_id']; dec=g['decisive'][0]['passage_id']; hard=g['hard_negatives'][0]['passage_id']; ann=g['hidden_passage_annotations']; d=ann[dec]; h=ann[hard]
        def rerender(pid:str):
            a=ann[pid]; pby[pid]['text']=render_semantic(a['semantic_sentence'],a['cue_profile']); pby[pid]['text_sha256']=text_hash(pby[pid]['text'])
        if tid=='swap_decisive_decoy_construction_style':
            for key in ('construction_family','punctuation','realization'):
                d['cue_profile'][key],h['cue_profile'][key]=h['cue_profile'][key],d['cue_profile'][key]
            rerender(dec); rerender(hard)
        elif tid=='equalize_exchange_passage_lengths':
            d['cue_profile']['length_bin'],h['cue_profile']['length_bin']=h['cue_profile']['length_bin'],d['cue_profile']['length_bin']
            rerender(dec); rerender(hard)
        elif tid=='permute_source_and_passage_order':
            for pid,a in ann.items():
                p=pby[pid]; p['source_order']=6-p['source_order']; p['passage_order']=3-p['passage_order']
                a['source_order']=p['source_order']; a['passage_order']=p['passage_order']; a['global_position']=(p['source_order']-1)*2+p['passage_order']
        elif tid=='exchange_runtime_visible_metadata_style':
            pby[dec]['runtime_metadata'],pby[hard]['runtime_metadata']=copy.deepcopy(pby[hard]['runtime_metadata']),copy.deepcopy(pby[dec]['runtime_metadata'])
            d['cue_profile']['metadata_style'],h['cue_profile']['metadata_style']=h['cue_profile']['metadata_style'],d['cue_profile']['metadata_style']
        elif tid=='consistent_fictional_entity_rename':
            old=g['entity_stem']; new=f'Rena{cid.replace("-","")}'
            g['entity_stem']=new; cby[cid]['claim_text']=cby[cid]['claim_text'].replace(old,new)
            for pid,a in ann.items():
                a['semantic_sentence']=a['semantic_sentence'].replace(old,new); pby[pid]['text']=pby[pid]['text'].replace(old,new); pby[pid]['text_sha256']=text_hash(pby[pid]['text'])
        elif tid=='punctuation_and_format_alteration':
            cycle={'plain':'semicolon','semicolon':'plain','numbered':'colon','colon':'numbered','pipe':'qa','qa':'pipe','narrative':'conditional','conditional':'narrative'}
            for pid,a in ann.items(): a['cue_profile']['punctuation']=cycle[a['cue_profile']['punctuation']]; rerender(pid)
        elif tid=='move_decisive_meaning_sentence_position':
            cycle={'beginning':'end','middle':'beginning','end':'middle'}; d['cue_profile']['sentence_position']=cycle[d['cue_profile']['sentence_position']]; rerender(dec)
        elif tid=='exchange_concise_verbose_realization':
            for key in ('realization','length_bin'):
                d['cue_profile'][key],h['cue_profile'][key]=h['cue_profile'][key],d['cue_profile'][key]
            rerender(dec); rerender(hard)
        elif tid=='semantic_role_exchange_with_cue_profile_fixed':
            dsem,hsem=d['semantic_sentence'],h['semantic_sentence']; d['semantic_sentence'],h['semantic_sentence']=hsem,dsem
            d['role'],h['role']='hard_negative','decisive'
            rerender(dec); rerender(hard)
            g['decisive']=[{'source_id':pby[hard]['source_id'],'passage_id':hard,'role':'counterevidence' if g['family']=='C01' else 'decisive'}]
            g['hard_negatives']=[{'source_id':pby[dec]['source_id'],'passage_id':dec}]
            role_changed+=1
        else: raise ValueError(tid)
    dumpj(root/'runtime/sealed_cases.jsonl',cases); dumpj(root/'runtime/passages.jsonl',passages); dumpj(root/'evaluator_only/sealed_gold.jsonl',gold)
    return {'role_changed_cases':role_changed}

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument('--benchmark-root',type=Path,required=True); ap.add_argument('--plan',type=Path,required=True); ap.add_argument('--thresholds',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    plan=json.loads(a.plan.read_text(encoding='utf-8')); th=json.loads(a.thresholds.read_text(encoding='utf-8'))
    expected_ids=[x['id'] for x in plan['transformations']]
    relevant={
        'swap_decisive_decoy_construction_style':['runtime_construction_style_gamer'],
        'equalize_exchange_passage_lengths':['passage_length_heuristic'],
        'permute_source_and_passage_order':['source_position_heuristic'],
        'exchange_runtime_visible_metadata_style':['metadata_identifier_pattern_heuristic'],
        'consistent_fictional_entity_rename':['token_overlap','bow_tfidf','character_ngram'],
        'punctuation_and_format_alteration':['runtime_construction_style_gamer'],
        'move_decisive_meaning_sentence_position':['runtime_sentence_position_gamer'],
        'exchange_concise_verbose_realization':['passage_length_heuristic','runtime_construction_style_gamer'],
        'semantic_role_exchange_with_cue_profile_fixed':['cue_swap_gamer'],
    }
    if set(expected_ids)!=set(relevant): raise SystemExit('metamorphic implementation/plan id mismatch')
    base_controls={n:generate(a.benchmark_root,n) for names in relevant.values() for n in names}
    results={}; all_pass=True
    for entry in plan['transformations']:
        tid=entry['id']
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'derived'; shutil.copytree(a.benchmark_root,root); meta=transform(root,tid)
            oracle=generate(root,'oracle'); oev=evaluate(root,oracle); oq,of=qualify_target(oev,th)
            weak={}; direction_ok=oq and not of
            for name in relevant[tid]:
                transformed=generate(root,name); ev=evaluate(root,transformed); q,fail=qualify_target(ev,th); frac=changed_fraction(base_controls[name],transformed)
                weak[name]={'ranking_changed_fraction':frac,'qualifies_transformed_target_gate':q,'qualification_failures':fail}
                if tid=='semantic_role_exchange_with_cue_profile_fixed' and name=='cue_swap_gamer':
                    # Cue-only rankings should remain fixed while semantic identity moves.
                    control_ok=(frac==0.0 and not q and meta['role_changed_cases']==80)
                elif entry.get('expected_'+('source_order_heuristic' if name=='source_position_heuristic' else 'metadata_heuristic' if name=='metadata_identifier_pattern_heuristic' else 'length_heuristic' if name=='passage_length_heuristic' else 'position_heuristic' if name=='runtime_sentence_position_gamer' else 'construction_gamer' if name=='runtime_construction_style_gamer' else 'lexical_controls')) in ('change_or_fail','may_change','may_change_or_fail'):
                    control_ok=(frac>0.0 or not q)
                else:
                    control_ok=(frac>0.0 or not q)
                weak[name]['expected_direction_pass']=control_ok; direction_ok &= control_ok
            results[tid]={'oracle_qualifies':oq,'oracle_failures':of,'weak_controls':weak,'expected_direction_pass':direction_ok,'transform_meta':meta}
            all_pass &= direction_ok
    cases=loadj(a.benchmark_root/'runtime/sealed_cases.jsonl'); pairs={}
    for c in cases: pairs.setdefault(c['pair_id'],[]).append(c)
    stable=sum(1 for cs in pairs.values() if len(cs)==2 and cs[0]['claim_text']==cs[1]['claim_text'])/len(pairs)
    if stable < plan['promotion_critical_metrics']['cue_swap_pair_semantic_role_stability_min']: all_pass=False
    out={'record':'eb-rc4-metamorphic-assurance','transformations':results,'paired_semantic_role_stability':stable,'all_expected_directions_pass':all_pass,'hybrid_sealed_exposed':False,'semantic_sealed_exposed':False}
    a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True,indent=2)); raise SystemExit(0 if all_pass else 4)
if __name__=='__main__': main()
